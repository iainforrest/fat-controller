#!/usr/bin/env python3
"""
Autonomous Orchestrator for fat-controller.

Drives the PM-PL cycle loop: invokes a PM agent to plan sprints from
OUTCOMES.md/ROADMAP.md, then invokes a PL agent to execute each sprint
on a git branch, collecting results and feeding them back to PM.

Architecture:
    - Python 3 stdlib only (no pip dependencies)
    - Filesystem is truth, sessions are disposable
    - PM plans, PL executes, orchestrator loops
    - Structured signals: YAML between ---ORCHESTRATOR_SIGNAL--- markers
    - VALUES.md is recommended but NOT required (graduated warning, not gate)

Usage:
    python3 orchestrator.py /path/to/project [--max-cycles 50] [--log-level INFO]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import textwrap
import time
from collections import deque
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIGNAL_MARKER = "---ORCHESTRATOR_SIGNAL---"
VALUES_PATH = Path.home() / ".claude" / "VALUES.md"

DEFAULT_MAX_CYCLES = 50
DEFAULT_PM_TIMEOUT = 600      # 10 minutes
DEFAULT_PL_TIMEOUT = 7200     # 2 hours
DEFAULT_LOG_LEVEL = "INFO"
STUCK_THRESHOLD = 3           # same sprint name N times in sequence -> halt
PM_ERROR_MAX_RETRIES = 1
SIGNAL_PARSE_MAX_RETRIES = 1
PARALLEL_LAUNCH_DELAY = 2.0   # seconds between parallel PL launches


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("orchestrator")

# Module-level state for agent I/O logging
_agent_log_dir: Optional[Path] = None
_invocation_counter = 0


def setup_logging(log_dir: Path, log_level: str = DEFAULT_LOG_LEVEL) -> None:
    """Configure dual logging: structured file + human-friendly stderr."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "orchestrator.log"

    # File handler: detailed logs with ISO 8601 timestamps
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))

    # Stderr handler: user-facing messages, no timestamp clutter
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(stderr_handler)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Agent I/O log directory -- captures full context and output per invocation
    global _agent_log_dir
    _agent_log_dir = log_dir / "agent-logs"
    _agent_log_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Agent I/O logs: %s", _agent_log_dir)


def _log_agent_io(
    agent_name: str,
    cycle: int,
    context: str,
    output: Optional[str] = None,
    stderr: Optional[str] = None,
    elapsed: Optional[float] = None,
    exit_code: Optional[int] = None,
    error: Optional[str] = None,
    command: Optional[str] = None,
) -> None:
    """Write full agent context and output to timestamped files.

    Creates per-invocation files in tasks/agent-logs/ for retrospective
    analysis of every prompt sent and response received.
    """
    if _agent_log_dir is None:
        return

    global _invocation_counter
    _invocation_counter += 1
    seq = _invocation_counter

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prefix = f"{seq:03d}-{ts}-cycle{cycle:02d}-{agent_name}"

    # Write the context (prompt) sent to the agent
    ctx_path = _agent_log_dir / f"{prefix}-context.md"
    command_line = command or f"claude --print --agent {agent_name} -p <context>"
    ctx_path.write_text(
        f"# Agent: {agent_name} | Cycle: {cycle} | Invocation: {seq}\n"
        f"# Timestamp: {ts}\n"
        f"# Command: {command_line}\n\n"
        f"{context}\n",
        encoding="utf-8",
    )

    # Write the full output (response) from the agent
    if output is not None:
        out_path = _agent_log_dir / f"{prefix}-output.md"
        meta_lines = [
            f"# Agent: {agent_name} | Cycle: {cycle} | Invocation: {seq}",
            f"# Timestamp: {ts}",
        ]
        if elapsed is not None:
            meta_lines.append(f"# Duration: {elapsed:.1f}s")
        if exit_code is not None:
            meta_lines.append(f"# Exit code: {exit_code}")
        meta_lines.append("")

        out_path.write_text(
            "\n".join(meta_lines) + "\n" + output + "\n",
            encoding="utf-8",
        )

    # Write stderr if non-empty
    if stderr and stderr.strip():
        err_path = _agent_log_dir / f"{prefix}-stderr.txt"
        err_path.write_text(stderr, encoding="utf-8")

    # Write error info if invocation failed
    if error:
        err_path = _agent_log_dir / f"{prefix}-error.txt"
        err_path.write_text(
            f"# Agent: {agent_name} | Cycle: {cycle} | Invocation: {seq}\n"
            f"# Timestamp: {ts}\n\n"
            f"{error}\n",
            encoding="utf-8",
        )


def _capture_session_logs(
    sprint: Dict[str, Any],
    project_dir: Path,
    cycle: int,
) -> None:
    """Copy pl-session.log and execution.log from sprint task dir to agent-logs/.

    These logs are written by the PL and execute agents during their sessions
    via echo-append. Copying them to agent-logs/ provides centralized access
    for post-hoc diagnosis of model selection and fallback behavior.
    """
    if _agent_log_dir is None:
        return

    sprint_name = sprint.get("name", "unknown")
    task_dir = project_dir / "tasks" / sprint_name

    for log_name in ("pl-session.log", "execution.log"):
        src = task_dir / log_name
        if src.is_file():
            dest = _agent_log_dir / f"cycle{cycle:02d}-{sprint_name}-{log_name}"
            try:
                dest.write_bytes(src.read_bytes())
                logger.info("Captured %s -> %s", src, dest)
            except OSError as exc:
                logger.warning("Failed to capture %s: %s", src, exc)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SprintState:
    """State of a single sprint read from ROADMAP.md or PM signal."""
    name: str
    target_outcome: str
    status: str  # backlog, in_progress, done, blocked
    prd_path: Optional[str] = None
    branch: Optional[str] = None
    pl_summary: Optional[str] = None


@dataclass
class SprintTask:
    """A sprint to execute, as received from a PM next_task signal."""
    name: str
    prd: str
    branch: str
    parallel_safe: bool = False


@dataclass
class OrchestratorState:
    """Top-level orchestrator state."""
    project_dir: Path
    roadmap_path: Path
    outcomes_path: Path
    log_dir: Path
    sprints: List[SprintState] = field(default_factory=list)
    cycle_count: int = 0
    max_cycles: int = DEFAULT_MAX_CYCLES
    pm_timeout: int = DEFAULT_PM_TIMEOUT
    pl_timeout: int = DEFAULT_PL_TIMEOUT
    values_loaded: bool = False
    current_graph: Optional["Graph"] = None
    checkpoint_manager: Optional["CheckpointManager"] = None
    run_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Graph engine data models
# ---------------------------------------------------------------------------

class NodeType(Enum):
    """Node role in a graph execution plan."""
    TASK = "task"
    DISCOVERY = "discovery"
    GATE = "gate"
    FAN_OUT = "fan_out"
    FAN_IN = "fan_in"


class NodeStatus(Enum):
    """Execution state for a graph node."""
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class ContextFidelityMode(Enum):
    """How much upstream context to pass to a node."""
    MINIMAL = "minimal"
    PARTIAL = "partial"
    FULL = "full"


class DomainType(Enum):
    """Execution domain for the graph."""
    SOFTWARE = "software"
    CONTENT = "content"
    MIXED = "mixed"


@dataclass
class GraphNode:
    """Single graph node definition."""
    id: str
    name: str
    type: NodeType
    node_class: str
    handler: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    context_fidelity: ContextFidelityMode = ContextFidelityMode.MINIMAL
    complexity_hint: Optional[str] = None
    discovery_tools: List[str] = field(default_factory=list)
    criteria: List[str] = field(default_factory=list)
    retry_target: Optional[str] = None
    max_retries: int = 3
    prd_path: Optional[str] = None
    branch: Optional[str] = None
    output_path: Optional[str] = None
    source_materials: List[str] = field(default_factory=list)


@dataclass
class GraphEdge:
    """Directed edge between graph nodes."""
    source: str
    target: str
    condition: str = "always"


@dataclass
class Graph:
    """Graph definition for orchestrated execution."""
    nodes: Dict[str, GraphNode]
    edges: List[GraphEdge]
    domain: DomainType = DomainType.SOFTWARE


@dataclass
class NodeOutcome:
    """Execution output for a completed node."""
    status: str
    output_summary: str
    artifacts: List[str] = field(default_factory=list)
    duration: float = 0.0
    model_used: str = ""
    error_details: Optional[str] = None
    commit_shas: List[str] = field(default_factory=list)
    merge_success: Optional[bool] = None
    merge_details: Optional[str] = None
    criteria_results: Dict[str, bool] = field(default_factory=dict)


@dataclass
class ModelConfig:
    """Model provider configuration for a graph node class."""
    provider: str
    model: str
    reasoning_effort: str = "medium"
    tool_profile: str = "claude"
    timeout: int = 7200
    fallback: List["ModelConfig"] = field(default_factory=list)


@dataclass
class CheckpointState:
    """Persisted state for an in-flight graph run."""
    run_id: str
    graph_hash: str
    nodes: Dict[str, "NodeCheckpoint"]
    created_at: str
    updated_at: str
    gate_retries: Dict[str, int] = field(default_factory=dict)


@dataclass
class NodeCheckpoint:
    """Persisted state for a single node."""
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_summary: Optional[str] = None
    model_used: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    error_details: Optional[str] = None


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

_shutting_down = False


def _handle_sigint(signum: int, frame: Any) -> None:
    """Handle Ctrl+C gracefully -- log state and exit cleanly."""
    global _shutting_down
    if _shutting_down:
        # Second SIGINT = force quit
        logger.warning("Forced shutdown (second SIGINT)")
        sys.exit(1)
    _shutting_down = True
    logger.info("Received SIGINT -- shutting down gracefully after current operation")


def check_shutdown(state: Optional[OrchestratorState] = None) -> None:
    """Check if a graceful shutdown was requested and exit if so.

    If state is provided, logs the current orchestrator state (cycle count,
    sprint progress) before exiting for debugging and resume purposes.
    """
    if _shutting_down:
        if state is not None:
            logger.info(
                "Graceful shutdown: cycle %d/%d, %d sprints tracked",
                state.cycle_count, state.max_cycles, len(state.sprints),
            )
        logger.info("Graceful shutdown: exiting between operations")
        sys.exit(0)


# ---------------------------------------------------------------------------
# Graph engine
# ---------------------------------------------------------------------------

class GraphEngine:
    """Core graph utilities for validation and traversal readiness."""

    def __init__(self, graph: Graph):
        self.graph = graph
        self.forward_edges: Dict[str, List[GraphEdge]] = {
            node_id: [] for node_id in graph.nodes
        }
        self.reverse_edges: Dict[str, List[GraphEdge]] = {
            node_id: [] for node_id in graph.nodes
        }
        self.in_degree: Dict[str, int] = {
            node_id: 0 for node_id in graph.nodes
        }

        for edge in graph.edges:
            self.forward_edges.setdefault(edge.source, []).append(edge)
            self.reverse_edges.setdefault(edge.target, []).append(edge)
            if edge.target in self.in_degree:
                self.in_degree[edge.target] += 1

        # Ensure all graph nodes are addressable even when no edges exist.
        for node_id in graph.nodes:
            self.forward_edges.setdefault(node_id, [])
            self.reverse_edges.setdefault(node_id, [])

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate node references and DAG acyclicity."""
        errors: List[str] = []
        seen_missing: Set[str] = set()

        for edge in self.graph.edges:
            if edge.source not in self.graph.nodes and edge.source not in seen_missing:
                seen_missing.add(edge.source)
                errors.append(f"Edge references unknown node: '{edge.source}'")
            if edge.target not in self.graph.nodes and edge.target not in seen_missing:
                seen_missing.add(edge.target)
                errors.append(f"Edge references unknown node: '{edge.target}'")

        # Kahn's algorithm for cycle detection (ignores edges to unknown nodes).
        in_degree = {node_id: 0 for node_id in self.graph.nodes}
        for edge in self.graph.edges:
            if edge.source in self.graph.nodes and edge.target in self.graph.nodes:
                in_degree[edge.target] += 1

        queue = deque(
            node_id for node_id, degree in in_degree.items() if degree == 0
        )
        visited_count = 0

        while queue:
            node_id = queue.popleft()
            visited_count += 1

            for edge in self.forward_edges.get(node_id, []):
                target_id = edge.target
                if target_id not in in_degree:
                    continue
                in_degree[target_id] -= 1
                if in_degree[target_id] == 0:
                    queue.append(target_id)

        if visited_count != len(self.graph.nodes):
            cyclic_nodes = {
                node_id for node_id, degree in in_degree.items() if degree > 0
            }
            cycle = self._find_cycle(cyclic_nodes)
            if cycle:
                errors.append(f"Cycle detected: {' -> '.join(cycle)}")
            else:
                # Preserve expected cycle error shape even on fallback.
                anchor = next(iter(cyclic_nodes), "unknown")
                errors.append(f"Cycle detected: {anchor} -> {anchor}")

        return (len(errors) == 0, errors)

    def get_ready_nodes(self, status_map: Dict[str, str]) -> List[str]:
        """Return nodes whose dependencies are complete and edges are active."""
        ready: List[str] = []

        for node_id in self.graph.nodes:
            current_status = self._normalize_status(
                status_map.get(node_id, NodeStatus.PENDING.value)
            )
            if node_id in status_map and current_status != NodeStatus.PENDING.value:
                continue

            incoming = self.reverse_edges.get(node_id, [])
            if not incoming:
                ready.append(node_id)
                continue

            is_ready = True
            for edge in incoming:
                source_status = self._normalize_status(
                    status_map.get(edge.source, "")
                )
                if source_status != NodeStatus.COMPLETED.value:
                    is_ready = False
                    break

                source_outcome = NodeOutcome(
                    status=source_status,
                    output_summary="",
                )
                if not self.evaluate_edge_condition(edge, source_outcome):
                    is_ready = False
                    break

            if is_ready:
                ready.append(node_id)

        return ready

    def evaluate_edge_condition(
        self,
        edge: GraphEdge,
        source_outcome: Optional[NodeOutcome],
    ) -> bool:
        """Evaluate edge activation condition against source node output."""
        condition = (edge.condition or "always").strip()

        if not condition or condition == "always":
            return True

        if source_outcome is None:
            logger.warning(
                "Edge %s -> %s condition '%s' cannot be evaluated without source outcome",
                edge.source, edge.target, condition,
            )
            return False

        status_match = re.fullmatch(
            r'status\s*==\s*["\'](pass|fail)["\']',
            condition,
        )
        if status_match:
            status_check = status_match.group(1)
            actual_status = self._normalize_status(source_outcome.status)
            if status_check == "pass":
                return actual_status == NodeStatus.COMPLETED.value
            return actual_status == NodeStatus.FAILED.value

        output_match = re.fullmatch(
            r'output\.([A-Za-z_][\w]*)\s*(==|!=|>=|<=|>|<)\s*(.+)',
            condition,
        )
        if not output_match:
            logger.warning(
                "Unsupported edge condition '%s' for edge %s -> %s",
                condition, edge.source, edge.target,
            )
            return False

        field_name, operator, raw_value = output_match.groups()
        try:
            if not hasattr(source_outcome, field_name):
                raise AttributeError(
                    f"NodeOutcome has no field '{field_name}'"
                )
            actual_value = getattr(source_outcome, field_name)
            expected_value = _parse_scalar(raw_value.strip())
            return self._compare_values(actual_value, operator, expected_value)
        except Exception as exc:
            logger.warning(
                "Failed to evaluate edge condition '%s' for edge %s -> %s: %s",
                condition, edge.source, edge.target, exc,
            )
            return False

    def get_downstream_nodes(self, node_id: str) -> List[str]:
        """Return all direct downstream node IDs from node_id."""
        return [edge.target for edge in self.forward_edges.get(node_id, [])]

    def get_upstream_nodes(self, node_id: str) -> List[str]:
        """Return all direct upstream node IDs into node_id."""
        return [edge.source for edge in self.reverse_edges.get(node_id, [])]

    def _find_cycle(self, candidates: Set[str]) -> List[str]:
        """Return a concrete cycle path, including repeated start node."""
        visited: Set[str] = set()
        recursion_stack: Set[str] = set()
        parent: Dict[str, str] = {}

        def dfs(node_id: str) -> List[str]:
            visited.add(node_id)
            recursion_stack.add(node_id)

            for edge in self.forward_edges.get(node_id, []):
                target_id = edge.target
                if target_id not in candidates:
                    continue

                if target_id not in visited:
                    parent[target_id] = node_id
                    cycle = dfs(target_id)
                    if cycle:
                        return cycle
                    continue

                if target_id in recursion_stack:
                    cycle = [target_id]
                    cursor = node_id
                    while cursor != target_id:
                        cycle.append(cursor)
                        cursor = parent[cursor]
                    cycle.append(target_id)
                    cycle.reverse()
                    return cycle

            recursion_stack.remove(node_id)
            return []

        for node_id in candidates:
            if node_id in visited:
                continue
            cycle = dfs(node_id)
            if cycle:
                return cycle

        return []

    @staticmethod
    def _normalize_status(status: Any) -> str:
        """Normalize status values to lowercase strings."""
        if isinstance(status, NodeStatus):
            return status.value
        return str(status).strip().lower()

    @staticmethod
    def _compare_values(actual: Any, operator: str, expected: Any) -> bool:
        """Compare values for edge condition evaluation."""
        if operator == "==":
            return actual == expected
        if operator == "!=":
            return actual != expected

        try:
            actual_num = float(actual)
            expected_num = float(expected)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Non-numeric comparison for operator '{operator}'"
            ) from exc

        if operator == ">":
            return actual_num > expected_num
        if operator == "<":
            return actual_num < expected_num
        if operator == ">=":
            return actual_num >= expected_num
        if operator == "<=":
            return actual_num <= expected_num
        raise ValueError(f"Unsupported operator '{operator}'")


# ---------------------------------------------------------------------------
# Domain handlers
# ---------------------------------------------------------------------------

class NodeHandler:
    """Base interface for domain-specific graph node execution."""

    def execute(
        self,
        node: GraphNode,
        context: str,
        config: ModelConfig,
        project_dir: Path,
        cycle: int = 0,
    ) -> NodeOutcome:
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute()")

    @staticmethod
    def _signal_to_outcome_status(signal_payload: Dict[str, Any]) -> str:
        """Map signal payloads to checkpoint-friendly node statuses."""
        signal_type = str(signal_payload.get("signal", "unknown")).strip().lower()
        if signal_type == "done":
            return NodeStatus.COMPLETED.value
        if signal_type == "skipped":
            return NodeStatus.SKIPPED.value
        return NodeStatus.FAILED.value

    @staticmethod
    def _signal_summary(signal_payload: Dict[str, Any], node_id: str) -> str:
        """Extract a concise outcome summary from a signal payload."""
        for key in ("summary", "details", "blocker_description", "reason"):
            value = signal_payload.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        signal_type = str(signal_payload.get("signal", "unknown")).strip().lower()
        return f"Node '{node_id}' finished with signal '{signal_type}'"

    @staticmethod
    def _signal_error(signal_payload: Dict[str, Any], node_id: str) -> Optional[str]:
        """Extract error details when the signal maps to a failed node."""
        if NodeHandler._signal_to_outcome_status(signal_payload) != NodeStatus.FAILED.value:
            return None
        details = (
            signal_payload.get("details")
            or signal_payload.get("blocker_description")
            or signal_payload.get("reason")
        )
        if details is None:
            signal_type = str(signal_payload.get("signal", "unknown")).strip().lower()
            return f"Node '{node_id}' failed with signal '{signal_type}'"
        return str(details).strip()

    @staticmethod
    def _extract_commit_shas(signal_payload: Dict[str, Any]) -> List[str]:
        """Normalize commit SHA fields from signal payloads."""
        raw_commit_shas = signal_payload.get("commit_shas")
        if isinstance(raw_commit_shas, list):
            return [str(sha).strip() for sha in raw_commit_shas if str(sha).strip()]
        if isinstance(raw_commit_shas, str) and raw_commit_shas.strip():
            return [raw_commit_shas.strip()]
        return []

    @staticmethod
    def _relative_path(path: Path, project_dir: Path) -> str:
        """Render a path relative to project root when possible."""
        try:
            return str(path.resolve().relative_to(project_dir.resolve()))
        except ValueError:
            return str(path)


class SoftwareHandler(NodeHandler):
    """Execute software implementation nodes in isolated git worktrees."""

    def execute(
        self,
        node: GraphNode,
        context: str,
        config: ModelConfig,
        project_dir: Path,
        cycle: int = 0,
    ) -> NodeOutcome:
        started_at = time.monotonic()
        branch = (node.branch or f"sprint/{node.id}").strip()
        prd_path = (
            node.prd_path
            or str(node.inputs.get("prd", "")).strip()
        )
        model_used = f"{config.provider}:{config.model}"
        signal_payload: Dict[str, Any] = {
            "signal": "error",
            "error_type": "execution_failed",
            "details": "Software handler did not produce a signal",
        }
        merge_success: Optional[bool] = None
        merge_details: Optional[str] = None
        worktree_path: Optional[Path] = None

        if not prd_path:
            return NodeOutcome(
                status=NodeStatus.FAILED.value,
                output_summary=f"Node '{node.id}' missing required field 'prd_path'",
                duration=time.monotonic() - started_at,
                model_used=model_used,
                error_details=f"Node '{node.id}' missing required field 'prd_path'",
            )

        try:
            worktree_path = self._create_worktree(node.id, branch, project_dir)
            if worktree_path is None:
                return NodeOutcome(
                    status=NodeStatus.FAILED.value,
                    output_summary=(
                        f"Failed to create git worktree for node '{node.id}' (branch '{branch}')"
                    ),
                    duration=time.monotonic() - started_at,
                    model_used=model_used,
                    error_details=(
                        f"Failed to create git worktree for node '{node.id}' (branch '{branch}')"
                    ),
                )

            sprint_payload = {
                "name": node.name or node.id,
                "prd": prd_path,
                "branch": branch,
            }
            pl_context = build_pl_context(sprint_payload, worktree_path)
            if node.criteria:
                pl_context += (
                    "\n\nQUALITY_CRITERIA:\n"
                    + "\n".join(f"- {criterion}" for criterion in node.criteria)
                )
            if node.inputs:
                pl_context += (
                    "\n\nNODE_INPUTS:\n"
                    + json.dumps(node.inputs, indent=2, sort_keys=True, ensure_ascii=True)
                )
            if context:
                pl_context += f"\n\nUPSTREAM_CONTEXT:\n{context}"

            output = invoke_agent(
                "pl",
                pl_context,
                worktree_path,
                timeout=max(1, int(config.timeout or DEFAULT_PL_TIMEOUT)),
                cycle=cycle,
                model_config=config,
            )
            signal_payload = parse_signal(output)
        except subprocess.TimeoutExpired:
            signal_payload = {
                "signal": "error",
                "error_type": "timeout",
                "details": f"PL timed out after {max(1, int(config.timeout or DEFAULT_PL_TIMEOUT))}s",
            }
        except RuntimeError as exc:
            signal_payload = {
                "signal": "error",
                "error_type": "invocation_failed",
                "details": str(exc),
            }
        except Exception as exc:
            signal_payload = {
                "signal": "error",
                "error_type": "execution_failed",
                "details": str(exc),
            }
        else:
            signal_type = str(signal_payload.get("signal", "unknown")).strip().lower()
            if signal_type == "done":
                merge_success, merge_details = self._merge_worktree_branch(branch, project_dir)
                if merge_success:
                    delete_branch(branch, project_dir)
                else:
                    signal_payload = dict(signal_payload)
                    signal_payload["signal"] = "error"
                    signal_payload["error_type"] = "merge_failed"
                    signal_payload["details"] = merge_details or (
                        f"Failed to merge branch '{branch}' into main"
                    )
                    signal_payload["merge_conflict"] = merge_details
        finally:
            if worktree_path is not None:
                self._remove_worktree(node.id, project_dir)

        summary = self._signal_summary(signal_payload, node.id)
        error_details = self._signal_error(signal_payload, node.id)
        if merge_success is False and merge_details:
            error_details = merge_details

        return NodeOutcome(
            status=self._signal_to_outcome_status(signal_payload),
            output_summary=summary,
            duration=time.monotonic() - started_at,
            model_used=model_used,
            error_details=error_details,
            commit_shas=self._extract_commit_shas(signal_payload),
            merge_success=merge_success,
            merge_details=merge_details,
        )

    def _create_worktree(
        self,
        node_id: str,
        branch: str,
        project_dir: Path,
    ) -> Optional[Path]:
        """Create an isolated git worktree for a graph node."""
        if not checkout_main(project_dir):
            logger.error(
                "Cannot create worktree for node '%s': failed to checkout main",
                node_id,
            )
            return None

        safe_node_id = re.sub(r"[^a-zA-Z0-9._-]", "-", node_id).strip("-") or "node"
        worktrees_dir = project_dir / ".worktrees"
        worktrees_dir.mkdir(parents=True, exist_ok=True)
        worktree_path = worktrees_dir / safe_node_id

        if worktree_path.exists():
            git_run(
                ["worktree", "remove", str(worktree_path), "--force"],
                project_dir,
                check=False,
            )
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)

        branch_exists = git_run(
            ["rev-parse", "--verify", branch],
            project_dir,
            check=False,
        ).returncode == 0

        if branch_exists:
            cmd = ["worktree", "add", str(worktree_path), branch]
        else:
            cmd = ["worktree", "add", str(worktree_path), "-b", branch]
        result = git_run(cmd, project_dir, check=False)

        if result.returncode != 0:
            logger.error(
                "Failed to create worktree for node '%s' (%s): %s",
                node_id,
                branch,
                (result.stderr or result.stdout or "unknown error").strip(),
            )
            return None

        logger.info(
            "Created worktree for node '%s': %s (branch: %s)",
            node_id,
            worktree_path,
            branch,
        )
        return worktree_path

    def _remove_worktree(self, node_id: str, project_dir: Path) -> None:
        """Remove node worktree after execution to avoid orphaned checkouts."""
        safe_node_id = re.sub(r"[^a-zA-Z0-9._-]", "-", node_id).strip("-") or "node"
        worktree_path = project_dir / ".worktrees" / safe_node_id
        if not worktree_path.exists():
            return

        result = git_run(
            ["worktree", "remove", str(worktree_path), "--force"],
            project_dir,
            check=False,
        )
        if result.returncode != 0:
            logger.warning(
                "Failed to remove worktree '%s': %s",
                worktree_path,
                (result.stderr or result.stdout or "unknown error").strip(),
            )
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)

        git_run(["worktree", "prune"], project_dir, check=False)

    def _merge_worktree_branch(self, branch: str, project_dir: Path) -> Tuple[bool, str]:
        """Merge worktree branch back to main via existing merge helper."""
        return merge_branch(branch, project_dir)


class ContentHandler(NodeHandler):
    """Execute non-software content-production nodes without git operations."""

    def execute(
        self,
        node: GraphNode,
        context: str,
        config: ModelConfig,
        project_dir: Path,
        cycle: int = 0,
    ) -> NodeOutcome:
        started_at = time.monotonic()
        model_used = f"{config.provider}:{config.model}"
        work_dir = project_dir / "tasks" / node.id
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            content_context = self._build_content_context(node, context)
            output = invoke_agent(
                "pl",
                content_context,
                work_dir,
                timeout=max(1, int(config.timeout or DEFAULT_PL_TIMEOUT)),
                cycle=cycle,
                model_config=config,
            )
            signal_payload = parse_signal(output)
        except subprocess.TimeoutExpired:
            signal_payload = {
                "signal": "error",
                "error_type": "timeout",
                "details": f"Content agent timed out after {max(1, int(config.timeout or DEFAULT_PL_TIMEOUT))}s",
            }
        except RuntimeError as exc:
            signal_payload = {
                "signal": "error",
                "error_type": "invocation_failed",
                "details": str(exc),
            }
        except Exception as exc:
            signal_payload = {
                "signal": "error",
                "error_type": "execution_failed",
                "details": str(exc),
            }

        artifacts, artifact_error = self._collect_content_artifacts(
            node,
            project_dir,
            work_dir,
        )
        if artifact_error:
            signal_payload = {
                "signal": "error",
                "error_type": "missing_output",
                "details": artifact_error,
            }

        return NodeOutcome(
            status=self._signal_to_outcome_status(signal_payload),
            output_summary=self._signal_summary(signal_payload, node.id),
            artifacts=artifacts,
            duration=time.monotonic() - started_at,
            model_used=model_used,
            error_details=self._signal_error(signal_payload, node.id),
            commit_shas=[],
            merge_success=None,
            merge_details=None,
        )

    def _build_content_context(self, node: GraphNode, upstream_context: str) -> str:
        """Build content-focused context for document/report generation nodes."""
        output_path = (
            node.output_path
            or str(node.inputs.get("output_path", "")).strip()
            or f"tasks/{node.id}/output.md"
        )
        topic = str(node.inputs.get("topic", node.name or node.id)).strip()
        style_guide = (
            node.inputs.get("style_guide")
            or node.inputs.get("style_guide_path")
            or node.inputs.get("style")
            or ""
        )

        parts = [
            "CONTENT_TASK: Produce non-code deliverables only (no git operations).",
            f"TASK_NAME: {node.name or node.id}",
            f"TOPIC: {topic}",
            f"OUTPUT_PATH: {output_path}",
            f"WORKING_DIRECTORY: tasks/{node.id}",
        ]
        if node.source_materials:
            parts.append(
                "SOURCE_MATERIALS:\n"
                + "\n".join(f"- {item}" for item in node.source_materials)
            )
        if node.criteria:
            parts.append(
                "QUALITY_CRITERIA:\n"
                + "\n".join(f"- {criterion}" for criterion in node.criteria)
            )
        if style_guide:
            parts.append(f"STYLE_GUIDE: {style_guide}")
        if node.inputs:
            parts.append(
                "NODE_INPUTS:\n"
                + json.dumps(node.inputs, indent=2, sort_keys=True, ensure_ascii=True)
            )
        if upstream_context:
            parts.append(f"UPSTREAM_CONTEXT:\n{upstream_context}")

        return "\n\n".join(parts)

    def _collect_content_artifacts(
        self,
        node: GraphNode,
        project_dir: Path,
        work_dir: Path,
    ) -> Tuple[List[str], Optional[str]]:
        """Validate and collect expected content output artifacts."""
        output_path_text = (
            node.output_path
            or str(node.inputs.get("output_path", "")).strip()
        )

        if output_path_text:
            output_path = Path(output_path_text)
            if not output_path.is_absolute():
                output_path = project_dir / output_path

            if not output_path.exists():
                return (
                    [],
                    f"Expected output path '{output_path_text}' does not exist",
                )

            if output_path.is_file():
                return ([self._relative_path(output_path, project_dir)], None)

            files = sorted(path for path in output_path.rglob("*") if path.is_file())
            if not files:
                return (
                    [],
                    f"Output directory '{output_path_text}' contains no files",
                )
            return ([self._relative_path(path, project_dir) for path in files], None)

        generated_files = sorted(path for path in work_dir.rglob("*") if path.is_file())
        if not generated_files:
            return (
                [],
                f"Node '{node.id}' produced no files in '{work_dir}' and no output_path was provided",
            )
        return ([self._relative_path(path, project_dir) for path in generated_files], None)


class DiscoveryHandler(NodeHandler):
    """Execute discovery nodes and persist approach decisions to CONTEXT.md."""

    def execute(
        self,
        node: GraphNode,
        context: str,
        config: ModelConfig,
        project_dir: Path,
        cycle: int = 0,
    ) -> NodeOutcome:
        started_at = time.monotonic()
        model_used = f"{config.provider}:{config.model}"
        work_dir = project_dir / "tasks" / node.id
        work_dir.mkdir(parents=True, exist_ok=True)
        context_path = work_dir / "CONTEXT.md"

        complexity_hint = str(node.complexity_hint or "").strip().lower()
        if complexity_hint in ("simple", "complex"):
            complexity = complexity_hint
            logger.info(
                "Discovery node '%s' using explicit complexity hint '%s'",
                node.id,
                complexity,
            )
        else:
            outcome_description = self._outcome_description(node)
            constraints = self._extract_constraints(node)
            complexity = self._detect_complexity(outcome_description, constraints)
            logger.info(
                "Discovery node '%s' auto-detected complexity '%s'",
                node.id,
                complexity,
            )

        if complexity == "simple":
            discovery_context = self._build_simple_discovery_context(node)
        else:
            discovery_context = self._build_complex_discovery_context(node)
        if context:
            discovery_context += f"\n\nUPSTREAM_CONTEXT:\n{context}"

        signal_payload: Dict[str, Any]
        try:
            output = invoke_agent(
                "discovery",
                discovery_context,
                work_dir,
                timeout=max(1, int(config.timeout or DEFAULT_PL_TIMEOUT)),
                cycle=cycle,
                model_config=config,
            )
            signal_payload = parse_signal(output)
        except subprocess.TimeoutExpired:
            signal_payload = {
                "signal": "error",
                "error_type": "timeout",
                "details": (
                    "Discovery agent timed out after "
                    f"{max(1, int(config.timeout or DEFAULT_PL_TIMEOUT))}s"
                ),
            }
        except RuntimeError as exc:
            signal_payload = {
                "signal": "error",
                "error_type": "invocation_failed",
                "details": str(exc),
            }
        except Exception as exc:
            signal_payload = {
                "signal": "error",
                "error_type": "execution_failed",
                "details": str(exc),
            }

        summary = self._signal_summary(signal_payload, node.id)
        context_markdown = self._compose_context_markdown(
            node=node,
            complexity=complexity,
            summary=summary,
            signal_payload=signal_payload,
        )
        try:
            context_path.write_text(context_markdown, encoding="utf-8")
        except OSError as exc:
            details = f"Failed to write discovery context file '{context_path}': {exc}"
            return NodeOutcome(
                status=NodeStatus.FAILED.value,
                output_summary=details,
                duration=time.monotonic() - started_at,
                model_used=model_used,
                error_details=details,
                artifacts=[],
            )

        return NodeOutcome(
            status=self._signal_to_outcome_status(signal_payload),
            output_summary=summary,
            artifacts=[self._relative_path(context_path, project_dir)],
            duration=time.monotonic() - started_at,
            model_used=model_used,
            error_details=self._signal_error(signal_payload, node.id),
            commit_shas=[],
            merge_success=None,
            merge_details=None,
        )

    def _detect_complexity(
        self,
        outcome_description: str,
        constraints: List[str],
    ) -> str:
        """Classify discovery complexity using lightweight keyword heuristics."""
        text = " ".join(
            [str(outcome_description or "").strip()]
            + [str(item or "").strip() for item in constraints]
        ).lower()
        simple_reasons: List[str] = []
        complex_reasons: List[str] = []

        simple_keywords = ("report", "presentation", "document", "slides")
        complex_keywords = (
            "build",
            "implement",
            "system",
            "architecture",
            "infrastructure",
        )
        choice_keywords = ("or", "vs", "versus", "choice", "decide")
        integration_keywords = ("integrate", "api", "third-party", "external")
        uncertainty_keywords = ("not sure", "maybe", "could be", "options")

        for keyword in simple_keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                simple_reasons.append(f"simple keyword '{keyword}'")
        for keyword in complex_keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                complex_reasons.append(f"complex keyword '{keyword}'")
        for keyword in choice_keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                complex_reasons.append(f"approach-choice keyword '{keyword}'")
                break
        for keyword in integration_keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                complex_reasons.append(f"integration keyword '{keyword}'")
        for keyword in uncertainty_keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                complex_reasons.append(f"uncertainty keyword '{keyword}'")
                break

        explicit_format_patterns = (
            r"\bpowerpoint\b",
            r"\bslide deck\b",
            r"\bformat\b",
            r"\btemplate\b",
        )
        if any(re.search(pattern, text) for pattern in explicit_format_patterns):
            simple_reasons.append("explicit format constraint detected")
        if re.search(r"\b(single|straightforward|obvious)\b", text):
            simple_reasons.append("single reasonable approach indicated")

        if complex_reasons:
            logger.info(
                "Discovery complexity classified as 'complex': %s",
                ", ".join(complex_reasons),
            )
            return "complex"
        if simple_reasons:
            logger.info(
                "Discovery complexity classified as 'simple': %s",
                ", ".join(simple_reasons),
            )
            return "simple"

        logger.info(
            "Discovery complexity ambiguous; defaulting to 'complex' (description=%r)",
            outcome_description,
        )
        return "complex"

    def _build_simple_discovery_context(self, node: GraphNode) -> str:
        """Build a compact discovery prompt for straightforward outcomes."""
        constraints = self._extract_constraints(node)
        lines = [
            "DISCOVERY_MODE: simple",
            "TOKEN_BUDGET: ~2000",
            f"OUTCOME_NAME: {node.name or node.id}",
            f"OUTCOME_DESCRIPTION: {self._outcome_description(node)}",
            "TASK: Produce a concise approach decision for this outcome.",
            "REQUIRED_SECTIONS:",
            "- ## Approach",
            "- ## Rationale",
            "- ## Constraints",
            "OUTPUT_FILE: tasks/{node-id}/CONTEXT.md",
            "Also emit ORCHESTRATOR_SIGNAL with signal=done, summary, context_path, complexity_used.",
        ]
        if constraints:
            lines.append("CONSTRAINTS:\n" + "\n".join(f"- {item}" for item in constraints))
        return "\n".join(lines)

    def _build_complex_discovery_context(self, node: GraphNode) -> str:
        """Build a deep-investigation discovery prompt for ambiguous outcomes."""
        constraints = self._extract_constraints(node)
        lines = [
            "DISCOVERY_MODE: complex",
            f"OUTCOME_NAME: {node.name or node.id}",
            f"OUTCOME_DESCRIPTION: {self._outcome_description(node)}",
            "TASK: Perform a deeper discovery before implementation.",
            "PROCESS:",
            "1. Use /investigate for technical and delivery options.",
            "2. Optionally use /debate when trade-offs are non-obvious.",
            "3. Synthesize findings into a recommended approach.",
            "REQUIRED_SECTIONS:",
            "- ## Approach",
            "- ## Rationale",
            "- ## Constraints",
            "- ## Investigation Findings",
            "- ## Alternatives Considered",
            "OUTPUT_FILE: tasks/{node-id}/CONTEXT.md",
            "Also emit ORCHESTRATOR_SIGNAL with signal=done, summary, context_path, complexity_used.",
        ]
        if node.discovery_tools:
            lines.append(
                "DISCOVERY_TOOLS:\n"
                + "\n".join(f"- {tool}" for tool in node.discovery_tools)
            )
        if constraints:
            lines.append("CONSTRAINTS:\n" + "\n".join(f"- {item}" for item in constraints))
        return "\n".join(lines)

    def _compose_context_markdown(
        self,
        node: GraphNode,
        complexity: str,
        summary: str,
        signal_payload: Dict[str, Any],
    ) -> str:
        """Create deterministic CONTEXT.md content expected by downstream nodes."""
        constraints = self._extract_constraints(node)
        approach = str(
            signal_payload.get("approach")
            or summary
            or "Use a pragmatic approach aligned to the outcome constraints."
        ).strip()
        rationale = str(
            signal_payload.get("rationale")
            or "This approach balances speed, clarity, and implementation risk."
        ).strip()

        lines = [
            f"# Discovery: {node.name or node.id}",
            "",
            "## Approach",
            approach,
            "",
            "## Rationale",
            rationale,
            "",
            "## Constraints",
        ]
        if constraints:
            lines.extend(f"- {item}" for item in constraints)
        else:
            lines.append("- No explicit constraints were provided.")

        if complexity == "complex":
            findings = str(
                signal_payload.get("investigation_findings")
                or signal_payload.get("findings")
                or "Investigation covered delivery approach, implementation risks, and integration trade-offs."
            ).strip()
            alternatives = str(
                signal_payload.get("alternatives_considered")
                or signal_payload.get("alternatives")
                or "Alternatives were considered and rejected due to higher risk, slower delivery, or weaker fit."
            ).strip()
            lines.extend(
                [
                    "",
                    "## Investigation Findings",
                    findings,
                    "",
                    "## Alternatives Considered",
                    alternatives,
                ]
            )

        return "\n".join(lines).rstrip() + "\n"

    def _outcome_description(self, node: GraphNode) -> str:
        """Extract the best available outcome description from node payload."""
        candidates = [
            node.inputs.get("outcome_description"),
            node.inputs.get("outcome"),
            node.inputs.get("goal"),
            node.inputs.get("description"),
            node.name,
            node.id,
        ]
        for value in candidates:
            text = str(value or "").strip()
            if text:
                return text
        return node.id

    def _extract_constraints(self, node: GraphNode) -> List[str]:
        """Collect and normalize constraints from graph node fields."""
        collected: List[str] = []
        collected.extend(str(item).strip() for item in node.criteria if str(item).strip())

        raw_constraints = node.inputs.get("constraints")
        if isinstance(raw_constraints, list):
            collected.extend(str(item).strip() for item in raw_constraints if str(item).strip())
        elif isinstance(raw_constraints, str) and raw_constraints.strip():
            collected.append(raw_constraints.strip())

        for key in ("constraint", "format", "output_format", "format_constraints"):
            value = node.inputs.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                collected.append(f"{key}: {text}")

        deduped: List[str] = []
        seen: Set[str] = set()
        for item in collected:
            normalized = item.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(normalized)
        return deduped


def detect_domain(outcomes_content: str) -> DomainType:
    """Infer orchestration domain from outcomes text using keyword density."""
    software_keywords = (
        "git", "code", "test", "deploy", "api", "function", "class",
        "module", "build", "compile", "commit", "branch", "merge",
    )
    content_keywords = (
        "write", "draft", "publish", "research", "report", "article",
        "document", "review", "edit", "commentary", "presentation",
    )

    text = str(outcomes_content or "").lower()
    software_hits = sum(
        len(re.findall(rf"\b{re.escape(keyword)}\w*\b", text))
        for keyword in software_keywords
    )
    content_hits = sum(
        len(re.findall(rf"\b{re.escape(keyword)}\w*\b", text))
        for keyword in content_keywords
    )

    if software_hits == 0 and content_hits == 0:
        logger.info(
            "Domain detection found no keywords; defaulting to %s",
            DomainType.SOFTWARE.value,
        )
        return DomainType.SOFTWARE

    if software_hits > content_hits * 2:
        detected = DomainType.SOFTWARE
    elif content_hits > software_hits * 2:
        detected = DomainType.CONTENT
    elif software_hits > 0 and content_hits > 0:
        detected = DomainType.MIXED
    elif software_hits > 0:
        detected = DomainType.SOFTWARE
    else:
        detected = DomainType.CONTENT

    logger.info(
        "Domain detection: software_hits=%d, content_hits=%d, detected=%s",
        software_hits,
        content_hits,
        detected.value,
    )
    return detected


# ---------------------------------------------------------------------------
# Checkpoint manager
# ---------------------------------------------------------------------------

def _compute_graph_hash(graph: Graph) -> str:
    """Compute deterministic SHA256 hash for graph structure."""
    def enum_or_value(value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        return value

    canonical_nodes = []
    for node_id in sorted(graph.nodes):
        node = graph.nodes[node_id]
        canonical_nodes.append(
            {
                "id": node.id,
                "name": node.name,
                "type": enum_or_value(node.type),
                "node_class": node.node_class,
                "handler": node.handler,
                "inputs": node.inputs,
                "context_fidelity": enum_or_value(node.context_fidelity),
                "complexity_hint": node.complexity_hint,
                "discovery_tools": node.discovery_tools,
                "criteria": node.criteria,
                "retry_target": node.retry_target,
                "max_retries": node.max_retries,
                "prd_path": node.prd_path,
                "branch": node.branch,
                "output_path": node.output_path,
                "source_materials": node.source_materials,
            }
        )

    canonical_edges = []
    for edge in sorted(
        graph.edges,
        key=lambda item: (item.source, item.target, item.condition or "always"),
    ):
        canonical_edges.append(
            {
                "source": edge.source,
                "target": edge.target,
                "condition": edge.condition or "always",
            }
        )

    canonical_graph = {
        "domain": enum_or_value(graph.domain),
        "nodes": canonical_nodes,
        "edges": canonical_edges,
    }
    canonical_str = json.dumps(
        canonical_graph,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

class CheckpointManager:
    """Persist and recover per-node graph execution state."""

    def __init__(self, run_dir: str, graph: Graph):
        self.logger = logging.getLogger("orchestrator")
        self.run_dir = Path(run_dir)
        self.graph = graph
        self.graph_engine = GraphEngine(graph)
        self.checkpoint_path = self.run_dir / "checkpoint.json"
        self.temp_checkpoint_path = self.run_dir / "checkpoint.json.tmp"
        self.graph_hash = self._compute_graph_hash(graph)

        generated_run_id = self._generate_run_id()
        existing_state = self._load_checkpoint()

        if existing_state is None:
            self.state = self._new_checkpoint_state(generated_run_id)
            self.run_id = self.state.run_id
            return

        if existing_state.graph_hash != self.graph_hash:
            self.logger.warning(
                "Pipeline definition changed since last run (hash mismatch). Starting fresh."
            )
            self.state = self._new_checkpoint_state(generated_run_id)
            self.run_id = self.state.run_id
            return

        self.state = existing_state
        self.run_id = self.state.run_id or generated_run_id

        changed = False
        if self.state.run_id != self.run_id:
            self.state.run_id = self.run_id
            changed = True

        if self.state.graph_hash != self.graph_hash:
            self.state.graph_hash = self.graph_hash
            changed = True

        # Ensure every graph node has checkpoint state on resume.
        for node_id in self.graph.nodes:
            if node_id not in self.state.nodes:
                self.state.nodes[node_id] = NodeCheckpoint(
                    status=NodeStatus.PENDING.value
                )
                changed = True

        # in_progress indicates the process likely crashed mid-node.
        for node_id, checkpoint in self.state.nodes.items():
            status = self._normalize_status(checkpoint.status)
            checkpoint.status = status
            if status != NodeStatus.IN_PROGRESS.value:
                continue

            self.logger.warning(
                "Resetting in_progress node '%s' to pending (crashed mid-execution)",
                node_id,
            )
            self._reset_node_checkpoint(checkpoint)
            changed = True

        # Missing summaries are a quality signal only; keep completed status.
        for node_id, checkpoint in self.state.nodes.items():
            if self._normalize_status(checkpoint.status) != NodeStatus.COMPLETED.value:
                continue
            summary = checkpoint.output_summary or ""
            if summary.strip():
                continue
            self.logger.warning(
                "Completed node '%s' has missing output_summary in checkpoint; keeping completed status",
                node_id,
            )

        if changed:
            self._write_checkpoint()

    def _compute_graph_hash(self, graph: Graph) -> str:
        """Compute deterministic SHA256 hash for graph structure."""
        return _compute_graph_hash(graph)

    def _write_checkpoint(self) -> None:
        """Write checkpoint state atomically using write-then-rename."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.state.updated_at = self._utc_timestamp()

        payload = {
            "run_id": self.state.run_id,
            "graph_hash": self.state.graph_hash,
            "nodes": {},
            "created_at": self.state.created_at,
            "updated_at": self.state.updated_at,
            "gate_retries": self.state.gate_retries,
        }
        for node_id in sorted(self.state.nodes):
            node_state = self.state.nodes[node_id]
            payload["nodes"][node_id] = {
                "status": self._normalize_status(node_state.status),
                "started_at": node_state.started_at,
                "completed_at": node_state.completed_at,
                "output_summary": node_state.output_summary,
                "model_used": node_state.model_used,
                "artifacts": list(node_state.artifacts),
                "error_details": node_state.error_details,
            }

        with self.temp_checkpoint_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.rename(self.temp_checkpoint_path, self.checkpoint_path)

        completed = sum(
            1
            for node in self.state.nodes.values()
            if self._normalize_status(node.status) == NodeStatus.COMPLETED.value
        )
        total = len(self.state.nodes)
        self.logger.info("Checkpoint written: %d/%d nodes complete", completed, total)

    def record_node_completion(self, node_id: str, outcome: NodeOutcome) -> None:
        """Record node completion data and persist checkpoint immediately."""
        node_checkpoint = self._ensure_node_checkpoint(node_id)
        node_checkpoint.status = self._normalize_status(outcome.status)
        node_checkpoint.completed_at = self._utc_timestamp()
        summary = str(outcome.output_summary or "")
        node_checkpoint.output_summary = summary[:2000]
        node_checkpoint.model_used = str(outcome.model_used or "")
        node_checkpoint.artifacts = list(outcome.artifacts or [])
        node_checkpoint.error_details = (
            None if outcome.error_details is None else str(outcome.error_details)
        )
        self._write_checkpoint()

    def record_node_start(self, node_id: str, model: str) -> None:
        """Record node start and selected model, then persist checkpoint."""
        node_checkpoint = self._ensure_node_checkpoint(node_id)
        node_checkpoint.status = NodeStatus.IN_PROGRESS.value
        node_checkpoint.started_at = self._utc_timestamp()
        node_checkpoint.completed_at = None
        node_checkpoint.model_used = str(model or "")
        node_checkpoint.output_summary = None
        node_checkpoint.artifacts = []
        node_checkpoint.error_details = None
        self._write_checkpoint()

    def get_status_map(self) -> Dict[str, str]:
        """Return node status map from current checkpoint state."""
        return {
            node_id: self._normalize_status(node_state.status)
            for node_id, node_state in self.state.nodes.items()
        }

    def get_output_summary(self, node_id: str) -> Optional[str]:
        """Return node output summary from checkpoint if present."""
        node_state = self.state.nodes.get(node_id)
        if node_state is None:
            return None
        return node_state.output_summary

    def get_artifacts(self, node_id: str) -> List[str]:
        """Return node artifact paths from checkpoint if present."""
        node_state = self.state.nodes.get(node_id)
        if node_state is None:
            return []
        return list(node_state.artifacts)

    def invalidate_nodes(self, node_ids: List[str]) -> None:
        """Reset selected nodes and all downstream nodes to pending."""
        to_reset: Set[str] = set()
        queue: deque[str] = deque(node_ids)

        while queue:
            node_id = queue.popleft()
            if node_id in to_reset:
                continue
            if node_id not in self.graph.nodes:
                self.logger.warning(
                    "Cannot invalidate unknown node '%s'; skipping",
                    node_id,
                )
                continue

            to_reset.add(node_id)
            for downstream_id in self.graph_engine.get_downstream_nodes(node_id):
                if downstream_id not in to_reset:
                    queue.append(downstream_id)

        if not to_reset:
            return

        for node_id in sorted(to_reset):
            node_checkpoint = self._ensure_node_checkpoint(node_id)
            self._reset_node_checkpoint(node_checkpoint)
            self.logger.info("Invalidated node '%s' (reset to pending)", node_id)

        self._write_checkpoint()

    def _load_checkpoint(self) -> Optional[CheckpointState]:
        """Load checkpoint.json from disk if present and parse safely."""
        if not self.checkpoint_path.exists():
            return None

        try:
            with self.checkpoint_path.open("r", encoding="utf-8") as handle:
                raw_data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            self.logger.warning(
                "Failed to load checkpoint '%s': %s. Starting fresh.",
                self.checkpoint_path,
                exc,
            )
            return None

        if not isinstance(raw_data, dict):
            self.logger.warning(
                "Checkpoint '%s' is not a JSON object. Starting fresh.",
                self.checkpoint_path,
            )
            return None

        nodes_raw = raw_data.get("nodes", {})
        if not isinstance(nodes_raw, dict):
            self.logger.warning(
                "Checkpoint '%s' has invalid 'nodes' payload. Starting fresh.",
                self.checkpoint_path,
            )
            return None

        parsed_nodes: Dict[str, NodeCheckpoint] = {}
        for node_id, node_data in nodes_raw.items():
            if not isinstance(node_data, dict):
                self.logger.warning(
                    "Checkpoint node '%s' payload is invalid; resetting to pending",
                    node_id,
                )
                parsed_nodes[str(node_id)] = NodeCheckpoint(
                    status=NodeStatus.PENDING.value
                )
                continue

            artifacts_raw = node_data.get("artifacts", [])
            if isinstance(artifacts_raw, list):
                artifacts = [str(item) for item in artifacts_raw if item is not None]
            else:
                self.logger.warning(
                    "Checkpoint node '%s' has non-list artifacts; defaulting to empty list",
                    node_id,
                )
                artifacts = []

            parsed_nodes[str(node_id)] = NodeCheckpoint(
                status=self._normalize_status(
                    node_data.get("status", NodeStatus.PENDING.value)
                ),
                started_at=self._optional_text(node_data.get("started_at")),
                completed_at=self._optional_text(node_data.get("completed_at")),
                output_summary=self._optional_text(node_data.get("output_summary")),
                model_used=self._optional_text(node_data.get("model_used")),
                artifacts=artifacts,
                error_details=self._optional_text(node_data.get("error_details")),
            )

        gate_retries_raw = raw_data.get("gate_retries", {})
        gate_retries: Dict[str, int] = {}
        if isinstance(gate_retries_raw, dict):
            for node_id, retries in gate_retries_raw.items():
                try:
                    gate_retries[str(node_id)] = int(retries)
                except (TypeError, ValueError):
                    self.logger.warning(
                        "Checkpoint gate_retries for node '%s' is invalid (%r); defaulting to 0",
                        node_id,
                        retries,
                    )
                    gate_retries[str(node_id)] = 0
        else:
            self.logger.warning(
                "Checkpoint has invalid gate_retries payload; defaulting to empty dict"
            )

        created_at = self._optional_text(raw_data.get("created_at"))
        updated_at = self._optional_text(raw_data.get("updated_at"))

        return CheckpointState(
            run_id=self._optional_text(raw_data.get("run_id")) or self._generate_run_id(),
            graph_hash=self._optional_text(raw_data.get("graph_hash")) or "",
            nodes=parsed_nodes,
            created_at=created_at or self._utc_timestamp(),
            updated_at=updated_at or created_at or self._utc_timestamp(),
            gate_retries=gate_retries,
        )

    def _new_checkpoint_state(self, run_id: str) -> CheckpointState:
        """Build a fresh checkpoint state with all nodes marked pending."""
        timestamp = self._utc_timestamp()
        return CheckpointState(
            run_id=run_id,
            graph_hash=self.graph_hash,
            nodes={
                node_id: NodeCheckpoint(status=NodeStatus.PENDING.value)
                for node_id in self.graph.nodes
            },
            created_at=timestamp,
            updated_at=timestamp,
            gate_retries={},
        )

    def _ensure_node_checkpoint(self, node_id: str) -> NodeCheckpoint:
        """Return mutable checkpoint entry for node, creating if needed."""
        if node_id not in self.state.nodes:
            self.logger.warning(
                "Node '%s' not present in checkpoint map; creating pending entry",
                node_id,
            )
            self.state.nodes[node_id] = NodeCheckpoint(status=NodeStatus.PENDING.value)
        return self.state.nodes[node_id]

    @staticmethod
    def _reset_node_checkpoint(node_checkpoint: NodeCheckpoint) -> None:
        """Clear node checkpoint fields and reset status to pending."""
        node_checkpoint.status = NodeStatus.PENDING.value
        node_checkpoint.started_at = None
        node_checkpoint.completed_at = None
        node_checkpoint.output_summary = None
        node_checkpoint.model_used = None
        node_checkpoint.artifacts = []
        node_checkpoint.error_details = None

    @staticmethod
    def _enum_or_value(value: Any) -> Any:
        """Return enum `.value` or the raw value for serialization."""
        if isinstance(value, Enum):
            return value.value
        return value

    @staticmethod
    def _normalize_status(status: Any) -> str:
        """Normalize status-like values into lowercase strings."""
        if isinstance(status, NodeStatus):
            return status.value
        return str(status).strip().lower()

    @staticmethod
    def _optional_text(value: Any) -> Optional[str]:
        """Convert nullable fields to stripped strings."""
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _utc_timestamp() -> str:
        """Return current timestamp in ISO 8601 UTC format."""
        return (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _generate_run_id() -> str:
        """Generate run identifier in UTC."""
        return f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"


# ---------------------------------------------------------------------------
# Model stylesheet loader
# ---------------------------------------------------------------------------

class StylesheetLoader:
    """Load and resolve model configuration classes with fallback chains."""

    def __init__(self, stylesheet_path: Optional[str]):
        self.logger = logging.getLogger("orchestrator")
        self.stylesheet_path = Path(stylesheet_path).expanduser() if stylesheet_path else None
        self._defaults: Dict[str, Any] = {
            "timeout": 7200,
            "context_fidelity": "minimal",
            "max_gate_retries": 3,
        }
        self._classes: Dict[str, ModelConfig] = self._build_default_classes()

        if self.stylesheet_path is None or not self.stylesheet_path.is_file():
            self.logger.info("Using default model stylesheet (no file found)")
            return

        try:
            payload = self._parse_stylesheet_yaml(
                self.stylesheet_path.read_text(encoding="utf-8")
            )
            parsed_defaults = payload.get("defaults")
            if isinstance(parsed_defaults, dict):
                self._defaults = parsed_defaults

            parsed_classes = payload.get("classes")
            if isinstance(parsed_classes, dict) and parsed_classes:
                self._classes = parsed_classes
            else:
                self.logger.warning(
                    "Model stylesheet '%s' did not define any valid classes; using defaults",
                    self.stylesheet_path,
                )
                self._classes = self._build_default_classes()

            self.logger.info(
                "Loaded model stylesheet: %d classes defined", len(self._classes)
            )
        except OSError as exc:
            self.logger.warning(
                "Failed to read model stylesheet '%s': %s. Using defaults.",
                self.stylesheet_path,
                exc,
            )
        except Exception as exc:
            self.logger.warning(
                "Failed to parse model stylesheet '%s': %s. Using defaults.",
                self.stylesheet_path,
                exc,
            )

    def select(self, node_class: str) -> ModelConfig:
        """Resolve model config by node class, then default, then hardcoded fallback."""
        normalized = str(node_class or "").strip()

        config = self._classes.get(normalized)
        if config is None:
            config = self._classes.get("default")
        if config is None:
            return self._hardcoded_fallback()

        return self._clone_model_config(config)

    def get_fallback_chain(self, node_class: str) -> List[ModelConfig]:
        """Return primary model followed by first-order fallback configs."""
        primary = self.select(node_class)
        return [primary] + list(primary.fallback)

    def _parse_stylesheet_yaml(self, text: str) -> Dict[str, Any]:
        """Parse and validate model-stylesheet.yaml payload."""
        parsed = _parse_simple_yaml(text)
        if not isinstance(parsed, dict):
            raise ValueError("Stylesheet payload must be a YAML object")

        defaults = self._parse_defaults(parsed.get("defaults"))
        classes_raw = parsed.get("classes", {})
        if not isinstance(classes_raw, dict):
            raise ValueError("Stylesheet 'classes' must be an object")

        classes: Dict[str, ModelConfig] = {}
        for raw_class_name, raw_entry in classes_raw.items():
            class_name = str(raw_class_name).strip()
            if not class_name:
                self.logger.warning("Skipping stylesheet class with empty name")
                continue
            if not isinstance(raw_entry, dict):
                self.logger.warning(
                    "Stylesheet class '%s' must be an object; got %s",
                    class_name,
                    type(raw_entry).__name__,
                )
                continue

            model_config = self._parse_model_entry(class_name, raw_entry, defaults)
            if model_config is None:
                continue
            classes[class_name] = model_config

        return {
            "version": parsed.get("version", 1),
            "defaults": defaults,
            "classes": classes,
        }

    def _parse_defaults(self, defaults_raw: Any) -> Dict[str, Any]:
        """Parse stylesheet defaults block."""
        if defaults_raw is None:
            self.logger.warning(
                "Stylesheet missing optional top-level 'defaults' block; using built-ins"
            )
            return dict(self._defaults)

        if not isinstance(defaults_raw, dict):
            self.logger.warning(
                "Stylesheet 'defaults' must be an object; got %s. Using built-ins.",
                type(defaults_raw).__name__,
            )
            return dict(self._defaults)

        timeout = self._coerce_timeout(defaults_raw.get("timeout"), 7200, "defaults")
        context_fidelity = str(
            defaults_raw.get("context_fidelity", "minimal")
        ).strip() or "minimal"
        max_gate_retries = self._coerce_int(
            defaults_raw.get("max_gate_retries"), 3, "defaults.max_gate_retries"
        )

        return {
            "timeout": timeout,
            "context_fidelity": context_fidelity,
            "max_gate_retries": max_gate_retries,
        }

    def _parse_model_entry(
        self,
        entry_name: str,
        entry: Dict[str, Any],
        defaults: Dict[str, Any],
    ) -> Optional[ModelConfig]:
        """Parse one model class or fallback entry."""
        provider = str(entry.get("provider", "")).strip()
        model = str(entry.get("model", "")).strip()
        if not provider or not model:
            self.logger.warning(
                "Stylesheet entry '%s' missing required fields 'provider' and/or 'model'; skipping",
                entry_name,
            )
            return None

        if "reasoning_effort" not in entry:
            self.logger.warning(
                "Stylesheet entry '%s' missing optional field 'reasoning_effort'; defaulting to 'medium'",
                entry_name,
            )
        reasoning_effort = (
            str(entry.get("reasoning_effort", "medium")).strip() or "medium"
        )

        if "tool_profile" not in entry:
            self.logger.warning(
                "Stylesheet entry '%s' missing optional field 'tool_profile'; inferring from provider",
                entry_name,
            )
        tool_profile = str(
            entry.get("tool_profile", self._default_tool_profile(provider))
        ).strip() or self._default_tool_profile(provider)

        timeout_default = self._coerce_int(defaults.get("timeout"), 7200, "defaults.timeout")
        if "timeout" not in entry:
            self.logger.warning(
                "Stylesheet entry '%s' missing optional field 'timeout'; defaulting to %d",
                entry_name,
                timeout_default,
            )
        timeout = self._coerce_timeout(
            entry.get("timeout"), timeout_default, f"{entry_name}.timeout"
        )

        fallback_entries = entry.get("fallback", [])
        fallback_models: List[ModelConfig] = []
        if fallback_entries in (None, ""):
            fallback_entries = []
        if isinstance(fallback_entries, list):
            for idx, fallback_entry in enumerate(fallback_entries):
                if not isinstance(fallback_entry, dict):
                    self.logger.warning(
                        "Stylesheet entry '%s' fallback index %d must be an object; got %s",
                        entry_name,
                        idx,
                        type(fallback_entry).__name__,
                    )
                    continue
                fallback_name = f"{entry_name}.fallback[{idx}]"
                fallback_model = self._parse_model_entry(
                    fallback_name,
                    fallback_entry,
                    defaults,
                )
                if fallback_model is not None:
                    # Keep fallback depth shallow in the chain list.
                    fallback_model.fallback = []
                    fallback_models.append(fallback_model)
        elif "fallback" in entry:
            self.logger.warning(
                "Stylesheet entry '%s' field 'fallback' must be a list; got %s",
                entry_name,
                type(fallback_entries).__name__,
            )

        return ModelConfig(
            provider=provider,
            model=model,
            reasoning_effort=reasoning_effort,
            tool_profile=tool_profile,
            timeout=timeout,
            fallback=fallback_models,
        )

    def _build_default_classes(self) -> Dict[str, ModelConfig]:
        """Build hardcoded defaults for environments without stylesheet file."""
        timeout = 7200
        classes: Dict[str, ModelConfig] = {
            "planning": ModelConfig(
                provider="anthropic",
                model="claude-opus-4-6",
                reasoning_effort="xhigh",
                tool_profile="claude",
                timeout=timeout,
                fallback=[
                    ModelConfig(
                        provider="openai",
                        model="gpt-5.3-codex",
                        reasoning_effort="xhigh",
                        tool_profile="codex",
                        timeout=timeout,
                    )
                ],
            ),
            "implementation": ModelConfig(
                provider="openai",
                model="gpt-5.3-codex",
                reasoning_effort="medium",
                tool_profile="codex",
                timeout=timeout,
                fallback=[
                    ModelConfig(
                        provider="anthropic",
                        model="claude-sonnet-4-6",
                        reasoning_effort="medium",
                        tool_profile="claude",
                        timeout=timeout,
                    )
                ],
            ),
            "implementation-complex": ModelConfig(
                provider="openai",
                model="gpt-5.3-codex",
                reasoning_effort="xhigh",
                tool_profile="codex",
                timeout=timeout,
            ),
            "review": ModelConfig(
                provider="anthropic",
                model="claude-opus-4-6",
                reasoning_effort="xhigh",
                tool_profile="claude",
                timeout=timeout,
            ),
            "gate": ModelConfig(
                provider="anthropic",
                model="claude-sonnet-4-6",
                reasoning_effort="medium",
                tool_profile="claude",
                timeout=timeout,
            ),
            "content-draft": ModelConfig(
                provider="anthropic",
                model="claude-opus-4-6",
                reasoning_effort="medium",
                tool_profile="claude",
                timeout=timeout,
            ),
            "discovery": ModelConfig(
                provider="anthropic",
                model="claude-opus-4-6",
                reasoning_effort="xhigh",
                tool_profile="claude",
                timeout=timeout,
            ),
            "discovery-simple": ModelConfig(
                provider="anthropic",
                model="claude-sonnet-4-6",
                reasoning_effort="medium",
                tool_profile="claude",
                timeout=timeout,
            ),
            "research": ModelConfig(
                provider="anthropic",
                model="claude-opus-4-6",
                reasoning_effort="xhigh",
                tool_profile="claude",
                timeout=timeout,
            ),
            "default": self._hardcoded_fallback(),
        }
        return classes

    @staticmethod
    def _default_tool_profile(provider: str) -> str:
        """Infer tool profile from provider when omitted in stylesheet."""
        return "codex" if provider.strip().lower() == "openai" else "claude"

    @staticmethod
    def _coerce_int(raw_value: Any, default: int, label: str) -> int:
        """Parse integer fields with fallback and warning."""
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            logger.warning(
                "Invalid integer for '%s': %r. Defaulting to %d.",
                label,
                raw_value,
                default,
            )
            return default

    def _coerce_timeout(self, raw_value: Any, default: int, label: str) -> int:
        """Parse timeout values ensuring positive integers."""
        if raw_value is None or raw_value == "":
            return default

        timeout = self._coerce_int(raw_value, default, label)
        if timeout <= 0:
            self.logger.warning(
                "Invalid timeout for '%s': %r. Defaulting to %d.",
                label,
                raw_value,
                default,
            )
            return default
        return timeout

    @staticmethod
    def _clone_model_config(config: ModelConfig) -> ModelConfig:
        """Copy model config deeply enough to avoid mutating loader cache."""
        return ModelConfig(
            provider=config.provider,
            model=config.model,
            reasoning_effort=config.reasoning_effort,
            tool_profile=config.tool_profile,
            timeout=config.timeout,
            fallback=[
                StylesheetLoader._clone_model_config(fallback)
                for fallback in config.fallback
            ],
        )

    @staticmethod
    def _hardcoded_fallback() -> ModelConfig:
        """Return built-in fallback when class selection misses."""
        return ModelConfig(
            provider="openai",
            model="gpt-5.3-codex",
            reasoning_effort="medium",
            tool_profile="codex",
            timeout=7200,
            fallback=[],
        )


# ---------------------------------------------------------------------------
# 7.6 -- Structured signal parser
# ---------------------------------------------------------------------------

def parse_signal(output: str) -> Dict[str, Any]:
    """Extract and parse ORCHESTRATOR_SIGNAL from agent output.

    Signals are delimited by ---ORCHESTRATOR_SIGNAL--- markers. The content
    between the markers is a subset of YAML that we parse without PyYAML:
    simple key: value pairs, nested objects (indented keys), and arrays
    (lines starting with - ).

    Returns a dict with at minimum a 'signal' key. On parse failure,
    returns an error signal with diagnostic information.
    """
    parts = output.split(SIGNAL_MARKER)
    if len(parts) < 3:
        # No valid signal found -- return error signal
        truncated = output[-500:] if len(output) > 500 else output
        return {
            "signal": "error",
            "error_type": "no_signal",
            "details": "No ORCHESTRATOR_SIGNAL markers found in agent output",
            "raw_tail": truncated,
        }

    # Take the content between the LAST pair of markers (in case the agent
    # echoed examples or documentation containing markers earlier).
    yaml_text = parts[-2].strip()
    if not yaml_text:
        return {
            "signal": "error",
            "error_type": "empty_signal",
            "details": "Signal markers found but content between them is empty",
        }

    try:
        signal = _parse_simple_yaml(yaml_text)
        signal_type = signal.get("signal", "")

        # Parse graph payloads eagerly so callers can operate on typed models.
        if signal_type == "next_graph":
            signal["graph"] = _parse_graph_signal(signal)
        elif signal_type == "next_task":
            sprints = signal.get("sprints", [])
            if isinstance(sprints, list):
                signal["graph"] = _sprints_to_graph(sprints, signal)
            else:
                logger.warning(
                    "next_task signal contained non-list 'sprints' value: %s",
                    type(sprints).__name__,
                )

        return signal
    except Exception as exc:
        return {
            "signal": "error",
            "error_type": "parse_error",
            "details": f"Failed to parse signal YAML: {exc}",
            "raw_signal": yaml_text[:500],
        }


def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Parse a simple YAML subset without external dependencies.

    Supports:
    - key: value (string, number, boolean)
    - key: "quoted value" or key: 'quoted value'
    - Nested objects via indentation
    - Arrays via "- item" syntax (flat or object arrays)
    - Multi-line quoted strings

    This is intentionally limited to the signal protocol format.
    """
    result: Dict[str, Any] = {}
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip blank lines and comments
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue

        # Determine indentation level
        indent = len(line) - len(line.lstrip())

        # Top-level key: value
        match = re.match(r'^(\s*)([\w_-]+)\s*:\s*(.*)', line)
        if not match:
            if line.strip() and not line.strip().startswith('#'):
                logger.debug("Skipping unparseable YAML line %d: %s", i, line.strip()[:100])
            i += 1
            continue

        key = match.group(2)
        value_part = match.group(3).strip()

        # Check if the next line starts an array or nested object
        next_indent = _next_content_indent(lines, i + 1)

        if value_part == "" and next_indent is not None and next_indent > indent:
            # Could be a nested object or array
            if _is_array_start(lines, i + 1):
                result[key], i = _parse_array(lines, i + 1, indent)
            else:
                result[key], i = _parse_nested(lines, i + 1, indent)
        else:
            result[key] = _parse_scalar(value_part)
            i += 1

    return result


def _next_content_indent(lines: List[str], start: int) -> Optional[int]:
    """Return the indentation of the next non-blank line, or None."""
    for j in range(start, len(lines)):
        stripped = lines[j].strip()
        if stripped and not stripped.startswith("#"):
            return len(lines[j]) - len(lines[j].lstrip())
    return None


def _is_array_start(lines: List[str], start: int) -> bool:
    """Check if the content at start begins with an array item (- prefix)."""
    for j in range(start, len(lines)):
        stripped = lines[j].strip()
        if stripped and not stripped.startswith("#"):
            return stripped.startswith("- ")
    return False


def _parse_array(lines: List[str], start: int, parent_indent: int) -> tuple:
    """Parse a YAML array starting at 'start'. Returns (list, next_index)."""
    result: List[Any] = []
    i = start

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank/comment lines
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        current_indent = len(line) - len(line.lstrip())

        # If we've de-dented back to or beyond parent, array is over
        if current_indent <= parent_indent:
            break

        if not stripped.startswith("- "):
            # Not an array item -- we're done
            break

        item_content = stripped[2:].strip()
        item_indent = current_indent

        # Empty item; parse nested value if present.
        if item_content == "":
            next_indent = _next_content_indent(lines, i + 1)
            if next_indent is not None and next_indent > item_indent:
                if _is_array_start(lines, i + 1):
                    item_value, i = _parse_array(lines, i + 1, item_indent)
                else:
                    item_value, i = _parse_nested(lines, i + 1, item_indent)
                result.append(item_value)
            else:
                result.append("")
                i += 1
            continue

        # Check if this array item starts an object (e.g. "- id: foo")
        item_match = re.match(r'^([\w_-]+)\s*:\s*(.*)', item_content)
        if not item_match:
            # Scalar array item
            result.append(_parse_scalar(item_content))
            i += 1
            continue

        # Object array item -- collect fields at this item indent.
        obj: Dict[str, Any] = {}
        first_key = item_match.group(1)
        first_value_part = item_match.group(2).strip()

        if first_value_part == "":
            # The first key lives on "- key:", so nested content must be
            # indented beyond the virtual key indent (item indent + "- ").
            virtual_key_indent = item_indent + 2
            next_indent = _next_content_indent(lines, i + 1)
            if next_indent is not None and next_indent > virtual_key_indent:
                if _is_array_start(lines, i + 1):
                    obj[first_key], i = _parse_array(
                        lines, i + 1, virtual_key_indent
                    )
                else:
                    obj[first_key], i = _parse_nested(
                        lines, i + 1, virtual_key_indent
                    )
            else:
                obj[first_key] = ""
                i += 1
        else:
            obj[first_key] = _parse_scalar(first_value_part)
            i += 1

        while i < len(lines):
            next_line = lines[i]
            next_stripped = next_line.strip()

            if not next_stripped or next_stripped.startswith("#"):
                i += 1
                continue

            next_indent = len(next_line) - len(next_line.lstrip())
            if next_indent <= item_indent:
                break

            field_match = re.match(r'^\s*([\w_-]+)\s*:\s*(.*)', next_line)
            if not field_match:
                logger.debug(
                    "Skipping unparseable YAML array object line %d: %s",
                    i, next_stripped[:100],
                )
                i += 1
                continue

            field_key = field_match.group(1)
            field_value_part = field_match.group(2).strip()

            if field_value_part == "":
                child_indent = _next_content_indent(lines, i + 1)
                if child_indent is not None and child_indent > next_indent:
                    if _is_array_start(lines, i + 1):
                        obj[field_key], i = _parse_array(
                            lines, i + 1, next_indent
                        )
                    else:
                        obj[field_key], i = _parse_nested(
                            lines, i + 1, next_indent
                        )
                else:
                    obj[field_key] = ""
                    i += 1
            else:
                obj[field_key] = _parse_scalar(field_value_part)
                i += 1

        result.append(obj)

    return result, i


def _parse_nested(lines: List[str], start: int, parent_indent: int) -> tuple:
    """Parse a nested YAML object. Returns (dict, next_index)."""
    result: Dict[str, Any] = {}
    i = start

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        current_indent = len(line) - len(line.lstrip())
        if current_indent <= parent_indent:
            break

        match = re.match(r'^\s*([\w_-]+)\s*:\s*(.*)', line)
        if match:
            key = match.group(1)
            value_part = match.group(2).strip()

            next_indent = _next_content_indent(lines, i + 1)
            if value_part == "" and next_indent is not None and next_indent > current_indent:
                if _is_array_start(lines, i + 1):
                    result[key], i = _parse_array(lines, i + 1, current_indent)
                else:
                    result[key], i = _parse_nested(lines, i + 1, current_indent)
            else:
                result[key] = _parse_scalar(value_part)
                i += 1
        else:
            i += 1

    return result, i


def _parse_scalar(value: str) -> Any:
    """Parse a scalar YAML value into a Python type."""
    if not value:
        return ""

    # Remove surrounding quotes
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    # Booleans
    lower = value.lower()
    if lower in ("true", "yes"):
        return True
    if lower in ("false", "no"):
        return False

    # null
    if lower in ("null", "~"):
        return None

    # Numbers
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    return value


def _parse_graph_signal(signal: Dict[str, Any]) -> Graph:
    """Parse a next_graph signal payload into a typed Graph model."""
    nodes_data = signal.get("nodes", [])
    edges_data = signal.get("edges", [])

    if not isinstance(nodes_data, list):
        logger.warning(
            "next_graph signal field 'nodes' must be a list, got %s",
            type(nodes_data).__name__,
        )
        nodes_data = []
    if not isinstance(edges_data, list):
        logger.warning(
            "next_graph signal field 'edges' must be a list, got %s",
            type(edges_data).__name__,
        )
        edges_data = []

    nodes: Dict[str, GraphNode] = {}
    for idx, node_data in enumerate(nodes_data):
        if not isinstance(node_data, dict):
            logger.warning(
                "Skipping non-dict graph node at index %d: %r",
                idx, node_data,
            )
            continue

        node_id = str(node_data.get("id", "")).strip()
        if not node_id:
            logger.warning("Skipping graph node at index %d: missing required field 'id'", idx)
            continue
        if node_id in nodes:
            logger.warning("Duplicate graph node id '%s' encountered; skipping duplicate", node_id)
            continue

        node_name = str(node_data.get("name", "")).strip()
        if not node_name:
            logger.warning(
                "Graph node '%s' missing required field 'name'; defaulting to node id",
                node_id,
            )
            node_name = node_id

        raw_node_type = node_data.get("type", NodeType.TASK.value)
        node_type = _coerce_enum(
            NodeType,
            raw_node_type,
            NodeType.TASK,
            f"graph node '{node_id}' type",
        )

        node_class = str(node_data.get("class", node_data.get("node_class", ""))).strip()
        if not node_class:
            logger.warning(
                "Skipping graph node '%s': missing required field 'class'/'node_class'",
                node_id,
            )
            continue

        handler = str(node_data.get("handler", "")).strip()
        if not handler:
            logger.warning(
                "Skipping graph node '%s': missing required field 'handler'",
                node_id,
            )
            continue

        if "context_fidelity" not in node_data:
            logger.warning(
                "Graph node '%s' missing optional field 'context_fidelity'; defaulting to '%s'",
                node_id, ContextFidelityMode.MINIMAL.value,
            )
        context_fidelity = _coerce_enum(
            ContextFidelityMode,
            node_data.get("context_fidelity", ContextFidelityMode.MINIMAL.value),
            ContextFidelityMode.MINIMAL,
            f"graph node '{node_id}' context_fidelity",
        )

        inputs_raw = node_data.get("inputs", {})
        if inputs_raw is None:
            inputs: Dict[str, Any] = {}
        elif isinstance(inputs_raw, dict):
            inputs = inputs_raw
        else:
            logger.warning(
                "Graph node '%s' field 'inputs' must be an object; got %s. Using empty object.",
                node_id, type(inputs_raw).__name__,
            )
            inputs = {}

        max_retries_raw = node_data.get("max_retries", 3)
        try:
            max_retries = int(max_retries_raw)
        except (TypeError, ValueError):
            logger.warning(
                "Graph node '%s' has invalid max_retries=%r; defaulting to 3",
                node_id, max_retries_raw,
            )
            max_retries = 3

        prd_path = node_data.get("prd_path", node_data.get("prd"))
        branch = node_data.get("branch")
        output_path = node_data.get("output_path")

        if handler == "software":
            if not prd_path:
                logger.warning(
                    "Graph node '%s' missing optional field 'prd'/'prd_path'",
                    node_id,
                )
            if not branch:
                logger.warning(
                    "Graph node '%s' missing optional field 'branch'",
                    node_id,
                )
        if handler == "content" and not output_path:
            logger.warning(
                "Graph node '%s' missing optional field 'output_path'",
                node_id,
            )

        nodes[node_id] = GraphNode(
            id=node_id,
            name=node_name,
            type=node_type,
            node_class=node_class,
            handler=handler,
            inputs=inputs,
            context_fidelity=context_fidelity,
            complexity_hint=_as_optional_str(node_data.get("complexity_hint")),
            discovery_tools=_as_string_list(
                node_data.get("discovery_tools"),
                f"graph node '{node_id}' discovery_tools",
            ),
            criteria=_as_string_list(
                node_data.get("criteria"),
                f"graph node '{node_id}' criteria",
            ),
            retry_target=_as_optional_str(node_data.get("retry_target")),
            max_retries=max_retries,
            prd_path=_as_optional_str(prd_path),
            branch=_as_optional_str(branch),
            output_path=_as_optional_str(output_path),
            source_materials=_as_string_list(
                node_data.get("source_materials"),
                f"graph node '{node_id}' source_materials",
            ),
        )

    edges: List[GraphEdge] = []
    for idx, edge_data in enumerate(edges_data):
        if not isinstance(edge_data, dict):
            logger.warning(
                "Skipping non-dict graph edge at index %d: %r",
                idx, edge_data,
            )
            continue

        source = str(edge_data.get("source", "")).strip()
        target = str(edge_data.get("target", "")).strip()
        if not source or not target:
            logger.warning(
                "Skipping graph edge at index %d: required fields 'source' and 'target' must be non-empty",
                idx,
            )
            continue

        condition = str(edge_data.get("condition", "always")).strip() or "always"
        edges.append(
            GraphEdge(
                source=source,
                target=target,
                condition=condition,
            )
        )

    domain = _coerce_enum(
        DomainType,
        signal.get("domain", DomainType.SOFTWARE.value),
        DomainType.SOFTWARE,
        "graph domain",
    )

    return Graph(nodes=nodes, edges=edges, domain=domain)


def _coerce_enum(
    enum_type: Any,
    raw_value: Any,
    default: Any,
    label: str,
) -> Any:
    """Coerce a raw value into an enum member, with warning and default."""
    if isinstance(raw_value, enum_type):
        return raw_value

    candidate = str(raw_value).strip().lower()
    if not candidate:
        return default

    try:
        return enum_type(candidate)
    except ValueError:
        logger.warning(
            "Invalid %s value '%s'; defaulting to '%s'",
            label, candidate, default.value,
        )
        return default


def _as_string_list(value: Any, label: str) -> List[str]:
    """Normalize scalar-or-list values into a string list."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if isinstance(value, str):
        return [value]

    logger.warning(
        "Expected %s to be a list or string, got %s; defaulting to empty list",
        label, type(value).__name__,
    )
    return []


def _as_optional_str(value: Any) -> Optional[str]:
    """Normalize optional scalar values to stripped strings."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


# ---------------------------------------------------------------------------
# 7.2 -- VALUES.md graduated warning flow
# ---------------------------------------------------------------------------

def check_values(state: OrchestratorState) -> bool:
    """Check for VALUES.md with graduated warning flow.

    This is NOT a hard gate. The user can proceed without values after
    two explicit confirmations. Returns True if the orchestrator should
    continue, False if the user chose to exit.
    """
    if VALUES_PATH.is_file():
        state.values_loaded = True
        logger.info("Values profile loaded from %s", VALUES_PATH)
        return True

    # VALUES.md not found -- graduated warning
    state.values_loaded = False

    print()
    print("The autonomous orchestrator is designed to work with values-driven agents.")
    print(f"No values profile found at {VALUES_PATH}.")
    print()
    print("Values-driven agents make decisions aligned with your principles.")
    print("Without values, agents operate generically.")
    print()

    # First prompt: offer values-discovery
    response = _prompt(
        "Would you like to run /values-discovery now to set up your values profile? "
        "(recommended) [y/N] "
    )
    if response.lower() in ("y", "yes"):
        print()
        print("Run `/values-discovery` in Claude Code, then restart the orchestrator.")
        return False

    # Second prompt: confirm proceed-without-values
    print()
    print(
        "Operating in autonomous mode without values can produce unexpected outcomes."
    )
    print(
        "The PM and PL agents will make decisions without your personal principles "
        "guiding them."
    )
    print()

    response = _prompt("Would you like to proceed without values? [y/N] ")
    if response.lower() in ("y", "yes"):
        logger.warning(
            "RUNNING WITHOUT VALUES PROFILE -- agents operating in generic mode"
        )
        return True

    print()
    print("Exiting. Run /values-discovery when ready.")
    return False


def _prompt(message: str) -> str:
    """Read user input, handling EOF and interrupts gracefully."""
    try:
        return input(message)
    except (EOFError, KeyboardInterrupt):
        return ""


# ---------------------------------------------------------------------------
# 7.3 -- OUTCOMES.md validation and ROADMAP.md resume
# ---------------------------------------------------------------------------

def validate_outcomes(state: OrchestratorState) -> bool:
    """Validate that OUTCOMES.md exists and is non-empty.

    Returns True if valid, False (with error message) if not.
    """
    outcomes = state.outcomes_path
    if not outcomes.is_file():
        logger.error(
            "OUTCOMES.md not found at %s. Run /outcomes first to define project outcomes.",
            outcomes,
        )
        return False

    try:
        content = outcomes.read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.error("Cannot read OUTCOMES.md: %s", exc)
        return False

    if not content:
        logger.error(
            "OUTCOMES.md is empty at %s. Run /outcomes to add project outcomes.",
            outcomes,
        )
        return False

    logger.info("OUTCOMES.md validated at %s", outcomes)
    return True


def read_roadmap(state: OrchestratorState) -> Optional[str]:
    """Read ROADMAP.md for resume capability.

    Returns the roadmap content if it exists, or None on first run.
    Logs resume information when sprints are found.
    """
    roadmap = state.roadmap_path
    if not roadmap.is_file():
        logger.info("First run -- PM will create ROADMAP.md")
        return None

    try:
        content = roadmap.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("Cannot read ROADMAP.md: %s", exc)
        return None

    # Parse sprint statuses for resume logging
    done_count = content.count("**Status:** done")
    in_progress_count = content.count("**Status:** in_progress")
    blocked_count = content.count("**Status:** blocked")
    backlog_count = content.count("**Status:** backlog")

    total = done_count + in_progress_count + blocked_count + backlog_count
    if total > 0:
        logger.info(
            "Resuming: %d sprints done, %d in progress, %d blocked, %d backlog",
            done_count, in_progress_count, blocked_count, backlog_count,
        )

    return content


# ---------------------------------------------------------------------------
# 7.5 -- Agent invocation via subprocess
# ---------------------------------------------------------------------------

def _agent_env() -> Dict[str, str]:
    """Return a clean environment for spawning agent subprocesses.

    Strips CLAUDECODE so that `claude --print` doesn't refuse to launch
    when the orchestrator is itself running inside a Claude Code session.
    """
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


def _default_tool_profile(provider: str) -> str:
    """Infer tool profile from provider when profile is omitted."""
    return "codex" if provider.strip().lower() == "openai" else "claude"


def _resolve_invocation_config(
    tool_profile: str,
    model_config: Optional[ModelConfig],
) -> Tuple[str, str, str]:
    """Resolve effective tool profile, model, and reasoning effort."""
    resolved_profile = str(tool_profile or "claude").strip().lower() or "claude"
    model_name = ""
    reasoning_effort = "medium"

    if model_config is not None:
        provider = str(model_config.provider or "").strip()
        configured_profile = str(model_config.tool_profile or "").strip().lower()
        if configured_profile:
            resolved_profile = configured_profile
        elif provider:
            resolved_profile = _default_tool_profile(provider)

        model_name = str(model_config.model or "").strip()
        reasoning_effort = (
            str(model_config.reasoning_effort or "medium").strip().lower()
            or "medium"
        )

    return resolved_profile, model_name, reasoning_effort


def _build_invoke_command(
    agent_name: str,
    context: str,
    tool_profile: str,
    model_name: str,
    reasoning_effort: str,
) -> Tuple[List[str], str]:
    """Build a provider-native CLI command for agent invocation."""
    profile = str(tool_profile or "claude").strip().lower() or "claude"
    if profile == "claude":
        return (
            ["claude", "--print", "--agent", agent_name, "-p", context],
            "claude",
        )

    if profile in {"codex", "gpt"}:
        resolved_model = model_name or "gpt-5.3-codex"
        cmd = ["codex", "-m", resolved_model]
        if reasoning_effort != "medium":
            cmd.extend(["-c", f'model_reasoning_effort="{reasoning_effort}"'])
        cmd.extend(["exec", "--full-auto", context])
        return (cmd, "codex")

    logger.warning(
        "Unknown tool_profile '%s' for agent '%s'; defaulting to Claude CLI",
        profile,
        agent_name,
    )
    return (
        ["claude", "--print", "--agent", agent_name, "-p", context],
        "claude",
    )

def invoke_agent(
    agent_name: str,
    context: str,
    project_dir: Path,
    timeout: int = DEFAULT_PM_TIMEOUT,
    cycle: int = 0,
    tool_profile: str = "claude",
    model_config: Optional[ModelConfig] = None,
) -> str:
    """Invoke an agent via provider-native CLI and capture stdout.

    Uses provider-native tools for execution:
    - `claude --print --agent <name> -p <context>` for Claude profile.
    - `codex -m <model> exec --full-auto <context>` for codex/gpt profiles.

    If `model_config` is provided, its `tool_profile`, `model`, and
    `reasoning_effort` determine invocation behavior.

    Args:
        agent_name: Agent to invoke (e.g., "pm", "pl")
        context: Context string to pass to the agent
        project_dir: Working directory for the subprocess
        timeout: Maximum time in seconds before killing the agent
        cycle: Current orchestration cycle number (for log file naming)
        tool_profile: Tool profile override when model_config is omitted
        model_config: Optional model configuration for provider-native routing

    Returns:
        The agent's stdout output as a string.

    Raises:
        subprocess.TimeoutExpired: If the agent exceeds the timeout.
        RuntimeError: If the agent exits with a non-zero return code
                      and produces no stdout.
    """
    (
        resolved_profile,
        resolved_model,
        resolved_reasoning,
    ) = _resolve_invocation_config(tool_profile, model_config)
    cmd, cli_name = _build_invoke_command(
        agent_name,
        context,
        resolved_profile,
        resolved_model,
        resolved_reasoning,
    )
    command_for_logs = " ".join(cmd[:-1] + ["<context>"]) if cmd else "<unknown>"

    logger.info(
        "Invoking agent '%s' with tool_profile='%s' model='%s' reasoning='%s' (timeout: %ds)",
        agent_name,
        resolved_profile,
        resolved_model or "default",
        resolved_reasoning,
        timeout,
    )
    start_time = time.monotonic()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(project_dir),
            env=_agent_env(),
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start_time
        logger.error(
            "Agent '%s' timed out after %.1fs (limit: %ds)",
            agent_name, elapsed, timeout,
        )
        _log_agent_io(
            agent_name, cycle, context,
            elapsed=elapsed,
            error=f"Timed out after {elapsed:.1f}s (limit: {timeout}s)",
            command=command_for_logs,
        )
        raise
    except FileNotFoundError:
        if cli_name == "codex":
            message = (
                "Codex CLI not found. Ensure 'codex' is on your PATH and installed."
            )
        else:
            message = (
                "Claude CLI not found. Ensure 'claude' is on your PATH. "
                "Install via: npm install -g @anthropic-ai/claude-code"
            )
        logger.error(message)
        _log_agent_io(
            agent_name, cycle, context,
            error=message,
            command=command_for_logs,
        )
        raise RuntimeError(message)

    elapsed = time.monotonic() - start_time
    logger.info(
        "Agent '%s' completed in %.1fs (exit code: %d)",
        agent_name, elapsed, result.returncode,
    )

    # Log full agent I/O for retrospective analysis
    _log_agent_io(
        agent_name, cycle, context,
        output=result.stdout,
        stderr=result.stderr,
        elapsed=elapsed,
        exit_code=result.returncode,
        command=command_for_logs,
    )

    if result.returncode != 0:
        logger.warning(
            "Agent '%s' exited with code %d. stderr: %s",
            agent_name, result.returncode, (result.stderr or "")[:500],
        )

    if not result.stdout and result.returncode != 0:
        raise RuntimeError(
            f"Agent '{agent_name}' failed (exit code {result.returncode}) "
            f"with no stdout. stderr: {(result.stderr or '')[:500]}"
        )

    return result.stdout


def invoke_agent_async(
    agent_name: str,
    context: str,
    project_dir: Path,
) -> subprocess.Popen:
    """Launch an agent subprocess asynchronously for parallel execution.

    Returns the Popen object. Caller is responsible for waiting and
    collecting output.
    """
    cmd = ["claude", "--print", "--agent", agent_name, "-p", context]
    logger.info("Launching agent '%s' asynchronously", agent_name)
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(project_dir),
        env=_agent_env(),
    )


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git_run(
    args: List[str], project_dir: Path, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a git command in the project directory."""
    cmd = ["git"] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(project_dir),
        check=check,
    )


def get_current_branch(project_dir: Path) -> str:
    """Return the current git branch name."""
    result = git_run(["branch", "--show-current"], project_dir, check=False)
    return result.stdout.strip()


def _stash_if_dirty(project_dir: Path) -> bool:
    """Stash uncommitted changes if the working tree is dirty.

    Returns True if changes were stashed (caller should pop later).
    """
    status = git_run(["status", "--porcelain"], project_dir, check=False)
    if status.stdout.strip():
        result = git_run(
            ["stash", "push", "-m", "orchestrator-auto-stash"],
            project_dir, check=False,
        )
        if result.returncode == 0:
            logger.info("Stashed dirty working tree before branch switch")
            return True
        logger.warning("Failed to stash: %s", result.stderr)
    return False


def _stash_pop(project_dir: Path) -> None:
    """Pop the most recent stash if it's an orchestrator auto-stash."""
    # Verify top stash is ours before popping
    result = git_run(
        ["stash", "list", "--max-count=1"], project_dir, check=False,
    )
    if "orchestrator-auto-stash" in result.stdout:
        pop = git_run(["stash", "pop"], project_dir, check=False)
        if pop.returncode == 0:
            logger.info("Restored stashed changes")
        else:
            logger.warning("Stash pop failed: %s", pop.stderr)


def create_branch(branch_name: str, project_dir: Path) -> bool:
    """Create and checkout a git branch. Returns True on success."""
    stashed = _stash_if_dirty(project_dir)

    # Check if branch already exists
    result = git_run(
        ["rev-parse", "--verify", branch_name], project_dir, check=False
    )
    if result.returncode == 0:
        # Branch exists -- check it out
        logger.info("Branch '%s' exists, checking out", branch_name)
        checkout = git_run(["checkout", branch_name], project_dir, check=False)
        if checkout.returncode != 0:
            logger.error("Failed to checkout '%s': %s", branch_name, checkout.stderr)
            if stashed:
                _stash_pop(project_dir)
            return False
        if stashed:
            _stash_pop(project_dir)
        return True

    # Create new branch from current HEAD
    logger.info("Creating branch '%s'", branch_name)
    result = git_run(["checkout", "-b", branch_name], project_dir, check=False)
    if result.returncode != 0:
        logger.error("Failed to create branch '%s': %s", branch_name, result.stderr)
        if stashed:
            _stash_pop(project_dir)
        return False
    if stashed:
        _stash_pop(project_dir)
    return True


def checkout_main(project_dir: Path) -> bool:
    """Checkout the main branch (tries 'main' then 'master')."""
    stashed = _stash_if_dirty(project_dir)
    for branch in ("main", "master"):
        result = git_run(
            ["rev-parse", "--verify", branch], project_dir, check=False
        )
        if result.returncode == 0:
            checkout = git_run(["checkout", branch], project_dir, check=False)
            if stashed:
                _stash_pop(project_dir)
            return checkout.returncode == 0
    logger.error("Neither 'main' nor 'master' branch found")
    if stashed:
        _stash_pop(project_dir)
    return False


def merge_branch(branch_name: str, project_dir: Path) -> tuple:
    """Merge a sprint branch back to main using a two-phase approach.

    Phase 1: Attempt merge with --no-commit to detect conflicts before
    finalising. This lets us inspect the merge result and abort cleanly
    if conflicts are found, without leaving a broken merge commit.

    Phase 2: If no conflicts, finalise with git commit. If conflicts
    are detected, abort and return rich conflict context for PM to
    create a conflict-resolution sprint.

    Args:
        branch_name: The sprint branch to merge (e.g., "sprint/my-sprint")
        project_dir: Path to the project git repository

    Returns:
        Tuple of (success: bool, details: str). On conflict, details
        contains the conflicting files and per-branch change summaries.
        On success, details is empty.
    """
    # Checkout main before merging
    if not checkout_main(project_dir):
        return (False, "Failed to checkout main branch before merge")

    logger.info("Merging branch '%s' into main (two-phase)", branch_name)

    # Phase 1: Attempt merge with --no-commit to detect conflicts
    result = git_run(
        ["merge", "--no-commit", "--no-ff", branch_name],
        project_dir, check=False,
    )

    stderr = result.stderr or ""
    stdout = result.stdout or ""

    if "CONFLICT" in stdout or "CONFLICT" in stderr:
        # Conflict detected -- gather rich context before aborting
        conflict_context = _build_conflict_context(
            branch_name, project_dir
        )

        # Abort the merge to leave the repo in a clean state
        git_run(["merge", "--abort"], project_dir, check=False)

        logger.warning(
            "Merge conflict for branch '%s': %s",
            branch_name, conflict_context,
        )
        return (False, conflict_context)

    if result.returncode != 0:
        # Non-conflict merge failure (e.g., branch not found, dirty tree)
        # Abort any partial merge state just in case
        git_run(["merge", "--abort"], project_dir, check=False)
        error_msg = (
            f"Merge of '{branch_name}' failed: "
            f"{stderr.strip() or stdout.strip()}"
        )
        logger.error(error_msg)
        return (False, error_msg)

    # Phase 2: No conflicts -- finalise the merge commit
    commit_result = git_run(
        ["commit", "--no-edit", "-m",
         f"Merge branch '{branch_name}' into main"],
        project_dir, check=False,
    )

    if commit_result.returncode != 0:
        # Edge case: nothing to commit (fast-forward or empty merge)
        # This is still a success -- the merge was clean
        logger.info(
            "Merge commit note for '%s': %s",
            branch_name,
            (commit_result.stdout or commit_result.stderr or "").strip(),
        )

    logger.info("Branch '%s' merged successfully", branch_name)
    return (True, "")


def _build_conflict_context(
    branch_name: str, project_dir: Path
) -> str:
    """Build rich conflict context for PM to create a resolution sprint.

    Gathers:
    - Which files have conflicts
    - What the sprint branch changed (diff summary vs main)
    - What main changed since the branch diverged

    This context is passed to PM so it can create an informed
    conflict-resolution sprint without the orchestrator attempting
    to resolve conflicts itself.
    """
    # Get list of conflicting files
    diff_result = git_run(
        ["diff", "--name-only", "--diff-filter=U"],
        project_dir, check=False,
    )
    conflicting_files = (
        diff_result.stdout.strip() if diff_result.stdout else "unknown"
    )

    # Get what the sprint branch changed relative to merge-base
    # (shows only the sprint's contributions, not main's changes)
    merge_base = git_run(
        ["merge-base", "HEAD", branch_name],
        project_dir, check=False,
    )
    branch_changes = ""
    main_changes = ""

    if merge_base.returncode == 0:
        base_sha = merge_base.stdout.strip()

        # Sprint branch changes since divergence
        branch_diff = git_run(
            ["diff", "--stat", base_sha, branch_name],
            project_dir, check=False,
        )
        if branch_diff.returncode == 0 and branch_diff.stdout:
            branch_changes = branch_diff.stdout.strip()

        # Main branch changes since divergence
        main_diff = git_run(
            ["diff", "--stat", base_sha, "HEAD"],
            project_dir, check=False,
        )
        if main_diff.returncode == 0 and main_diff.stdout:
            main_changes = main_diff.stdout.strip()

    parts = [
        f"Merge conflict in branch '{branch_name}'.",
        f"Conflicting files: {conflicting_files}",
    ]
    if branch_changes:
        parts.append(f"Branch '{branch_name}' changes:\n{branch_changes}")
    if main_changes:
        parts.append(f"Main branch changes since divergence:\n{main_changes}")

    return "\n".join(parts)


def delete_branch(branch_name: str, project_dir: Path) -> bool:
    """Delete a merged sprint branch.

    Uses 'git branch -d' which only deletes if the branch has been
    fully merged. Logs a warning on failure but does not raise -- branch
    cleanup is non-blocking.

    Args:
        branch_name: The branch to delete (e.g., "sprint/my-sprint")
        project_dir: Path to the project git repository

    Returns:
        True if deleted, False otherwise.
    """
    result = git_run(["branch", "-d", branch_name], project_dir, check=False)

    if result.returncode == 0:
        logger.info("Deleted branch '%s'", branch_name)
        return True

    # Non-blocking failure -- log warning and continue
    logger.warning(
        "Failed to delete branch '%s': %s",
        branch_name, (result.stderr or "").strip(),
    )
    return False


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

def build_pm_context(
    state: OrchestratorState,
    pl_results: Optional[List[Dict[str, Any]]] = None,
    roadmap_content: Optional[str] = None,
) -> str:
    """Build the context string passed to the PM agent.

    When PL results are provided, categorizes them into succeeded/failed
    groups so PM has a clear picture and can decide recovery strategy
    for any failed sprints (retry, fix sprint, mark blocked).
    """
    parts = [
        f"PROJECT_DIR: {state.project_dir}",
        f"OUTCOMES_PATH: {state.outcomes_path}",
        f"ROADMAP_PATH: {state.roadmap_path}",
        f"VALUES_LOADED: {state.values_loaded}",
        f"CYCLE: {state.cycle_count}",
    ]

    if roadmap_content:
        parts.append(f"\n--- CURRENT ROADMAP ---\n{roadmap_content}\n--- END ROADMAP ---")

    if pl_results:
        # Categorize results so PM gets a structured view
        categorized = categorize_sprint_results(pl_results)

        parts.append("\n--- PL RESULTS FROM PREVIOUS CYCLE ---")
        parts.append(f"Overall: {categorized['summary']}")

        # Succeeded sprints (with merge status)
        if categorized["succeeded"]:
            parts.append("\nSUCCEEDED SPRINTS:")
            for pr in categorized["succeeded"]:
                parts.append(_format_pl_result(pr))

        # Failed sprints -- PM decides recovery strategy
        if categorized["failed"]:
            parts.append("\nFAILED SPRINTS (PM decides: retry, fix sprint, or mark blocked):")
            for pr in categorized["failed"]:
                parts.append(_format_pl_result(pr))

        # Unknown signal types -- PM should investigate
        if categorized["unknown"]:
            parts.append("\nUNKNOWN SIGNAL SPRINTS (unexpected signal type):")
            for pr in categorized["unknown"]:
                parts.append(_format_pl_result(pr))

        parts.append("--- END PL RESULTS ---")

    return "\n".join(parts)


def _format_pl_result(pr: Dict[str, Any]) -> str:
    """Format a single PL result for PM context.

    Includes sprint name, signal type, summary/details, and merge
    status when available. Provides enough context for PM to make
    informed recovery or progression decisions.
    """
    sprint = pr.get("sprint", {})
    sig = pr.get("signal", {})
    sig_type = sig.get("signal", "unknown")

    lines = [
        f"  Sprint: {sprint.get('name', 'unknown')}",
        f"    Branch: {sprint.get('branch', 'unknown')}",
        f"    Signal: {sig_type}",
    ]

    # Add signal-type-specific details
    if sig_type == "done":
        lines.append(
            f"    Summary: {sig.get('summary', 'N/A')}"
        )
        tasks_info = ""
        if "tasks_completed" in sig and "tasks_total" in sig:
            tasks_info = f" ({sig['tasks_completed']}/{sig['tasks_total']} tasks)"
        if tasks_info:
            lines.append(f"    Progress:{tasks_info}")

    elif sig_type == "blocked":
        lines.append(
            f"    Blocker: {sig.get('blocker_description', sig.get('details', 'N/A'))}"
        )
        if "tasks_completed" in sig and "tasks_total" in sig:
            lines.append(
                f"    Progress: {sig['tasks_completed']}/{sig['tasks_total']} tasks"
            )

    elif sig_type == "error":
        lines.append(
            f"    Error type: {sig.get('error_type', 'unknown')}"
        )
        lines.append(
            f"    Details: {sig.get('details', 'N/A')}"
        )

    else:
        # Unknown signal type -- dump what we have
        summary = sig.get("summary", sig.get("details", "N/A"))
        lines.append(f"    Details: {summary}")

    # Merge status (only present for succeeded sprints that were merged)
    if pr.get("merge_success") is True:
        lines.append("    Merge: succeeded (branch merged and deleted)")
    elif pr.get("merge_success") is False:
        lines.append(
            f"    Merge: CONFLICT -- {pr.get('merge_details', 'unknown')}"
        )
        lines.append(
            "    Action needed: create conflict-resolution sprint"
        )

    # Merge conflict attached to signal (from sequential merge failures)
    if sig.get("merge_conflict"):
        lines.append(f"    Merge conflict: {sig['merge_conflict']}")

    return "\n".join(lines)


def build_pl_context(sprint: Dict[str, Any], project_dir: Path) -> str:
    """Build the context string passed to the PL agent for a sprint."""
    return (
        f"SPRINT_PRD: {project_dir / sprint['prd']}\n"
        f"BRANCH: {sprint['branch']}\n"
        f"SPRINT_NAME: {sprint['name']}\n"
        f"PROJECT_DIR: {project_dir}"
    )


# ---------------------------------------------------------------------------
# Sprint execution
# ---------------------------------------------------------------------------

def _sanitize_graph_node_id(raw_name: str) -> str:
    """Convert a sprint name to a stable node identifier."""
    node_id = re.sub(r"[^a-z0-9-]", "-", raw_name.lower())
    node_id = re.sub(r"-{2,}", "-", node_id).strip("-")
    return node_id or "task"


def _sprints_to_graph(
    sprints: List[Dict[str, Any]],
    pm_signal: Dict[str, Any],
) -> Graph:
    """Convert legacy next_task sprint lists into a Graph definition."""
    nodes: Dict[str, GraphNode] = {}
    ordered_node_ids: List[str] = []
    parallel_flags: List[bool] = []
    used_ids: Set[str] = set()

    for idx, sprint in enumerate(sprints):
        if not isinstance(sprint, dict):
            logger.warning("Skipping non-dict sprint at index %d: %r", idx, sprint)
            continue

        sprint_name = str(sprint.get("name", "")).strip() or f"sprint-{idx + 1}"
        base_id = _sanitize_graph_node_id(sprint_name)
        node_id = base_id
        suffix = 2
        while node_id in used_ids:
            node_id = f"{base_id}-{suffix}"
            suffix += 1
        used_ids.add(node_id)

        nodes[node_id] = GraphNode(
            id=node_id,
            name=sprint_name,
            type=NodeType.TASK,
            node_class="implementation",
            handler="software",
            prd_path=_as_optional_str(sprint.get("prd")),
            branch=_as_optional_str(sprint.get("branch")),
        )
        ordered_node_ids.append(node_id)
        parallel_flags.append(bool(sprint.get("parallel_safe", False)))

    edges: List[GraphEdge] = []
    edge_keys: Set[Tuple[str, str]] = set()

    def add_edge(source: str, target: str) -> None:
        key = (source, target)
        if key in edge_keys:
            return
        edge_keys.add(key)
        edges.append(GraphEdge(source=source, target=target))

    previous_sequential_index: Optional[int] = None
    pending_parallel_indices: List[int] = []

    for idx, is_parallel in enumerate(parallel_flags):
        node_id = ordered_node_ids[idx]

        if is_parallel:
            if previous_sequential_index is not None:
                # Fan-out from the most recent sequential node.
                add_edge(ordered_node_ids[previous_sequential_index], node_id)
                pending_parallel_indices.append(idx)
            continue

        # Current node is sequential.
        if previous_sequential_index is not None:
            if pending_parallel_indices:
                # Fan-in from all parallel nodes to this sequential node.
                for parallel_idx in pending_parallel_indices:
                    add_edge(ordered_node_ids[parallel_idx], node_id)
                pending_parallel_indices = []
            else:
                # Linear chain when no parallel segment exists.
                add_edge(ordered_node_ids[previous_sequential_index], node_id)

        previous_sequential_index = idx

    domain = _coerce_enum(
        DomainType,
        pm_signal.get("domain", DomainType.SOFTWARE.value),
        DomainType.SOFTWARE,
        "next_task domain",
    )
    logger.info(
        "Converted %d sprints to linear graph (backward compatibility)",
        len(nodes),
    )
    return Graph(nodes=nodes, edges=edges, domain=domain)


def execute_sprints(
    sprints: List[Dict[str, Any]],
    state: OrchestratorState,
) -> List[Dict[str, Any]]:
    """Compatibility wrapper around SoftwareHandler-based node execution."""
    handler = SoftwareHandler()
    config = ModelConfig(
        provider="openai",
        model="gpt-5.3-codex",
        reasoning_effort="medium",
        tool_profile="codex",
        timeout=state.pl_timeout,
        fallback=[],
    )
    results: List[Dict[str, Any]] = []

    for sprint in sprints:
        check_shutdown(state)
        if not isinstance(sprint, dict):
            logger.warning("Skipping non-dict sprint payload: %r", sprint)
            continue

        sprint_name = str(sprint.get("name", "")).strip() or "Unnamed sprint"
        node_id = str(sprint.get("graph_node_id", "")).strip() or _sanitize_graph_node_id(sprint_name)
        branch = str(sprint.get("branch", "")).strip() or f"sprint/{node_id}"
        node = GraphNode(
            id=node_id,
            name=sprint_name,
            type=NodeType.TASK,
            node_class="implementation",
            handler="software",
            prd_path=_as_optional_str(sprint.get("prd")),
            branch=branch,
            inputs=sprint.get("inputs", {}) if isinstance(sprint.get("inputs"), dict) else {},
            criteria=_as_string_list(sprint.get("criteria"), f"sprint '{sprint_name}' criteria"),
        )
        outcome = handler.execute(
            node=node,
            context="",
            config=config,
            project_dir=state.project_dir,
            cycle=state.cycle_count,
        )
        result = _node_outcome_to_result(node, outcome)
        results.append(result)
        logger.info(
            "Sprint '%s' signal: %s",
            sprint_name,
            result.get("signal", {}).get("signal", "unknown"),
        )
        _capture_session_logs(result.get("sprint", {}), state.project_dir, state.cycle_count)

    checkout_main(state.project_dir)
    return results


# ---------------------------------------------------------------------------
# Sprint result categorization
# ---------------------------------------------------------------------------

def categorize_sprint_results(
    results: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Categorize sprint results into succeeded, failed, and unknown.

    Used after execute_sprints() to give PM a clear picture of what
    happened. PM decides recovery strategy -- the orchestrator does NOT
    make recovery decisions itself.

    Args:
        results: List of result dicts from execute_sprints(), each with
                 'sprint' and 'signal' keys.

    Returns:
        Dict with keys:
        - 'succeeded': sprints with signal 'done'
        - 'failed': sprints with signal 'error' or 'blocked'
        - 'unknown': sprints with unrecognised signal types
        - 'summary': human-readable one-line summary
    """
    succeeded: List[Dict[str, Any]] = []
    failed: List[Dict[str, Any]] = []
    unknown: List[Dict[str, Any]] = []

    for result in results:
        sig_type = result.get("signal", {}).get("signal", "unknown")
        if sig_type == "done":
            succeeded.append(result)
        elif sig_type in ("error", "blocked"):
            failed.append(result)
        else:
            unknown.append(result)

    summary = (
        f"{len(succeeded)} succeeded, {len(failed)} failed"
        f"{f', {len(unknown)} unknown' if unknown else ''}"
        f" (of {len(results)} total)"
    )

    return {
        "succeeded": succeeded,
        "failed": failed,
        "unknown": unknown,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Stuck loop detection
# ---------------------------------------------------------------------------

def detect_stuck_loop(
    sprint_history: List[str], new_sprints: List[str]
) -> Optional[str]:
    """Detect if PM keeps generating the same sprint name.

    Returns the stuck sprint name if detected, None otherwise.
    """
    combined = sprint_history + new_sprints
    if len(combined) < STUCK_THRESHOLD:
        return None

    # Check if the last STUCK_THRESHOLD entries are all the same name
    tail = combined[-STUCK_THRESHOLD:]
    if len(set(tail)) == 1:
        return tail[0]

    return None


# ---------------------------------------------------------------------------
# Graph traversal helpers
# ---------------------------------------------------------------------------

def _normalize_node_status(status: Any) -> str:
    """Normalize node status-like values into lowercase strings."""
    if isinstance(status, NodeStatus):
        return status.value
    return str(status).strip().lower()


def _status_map_for_ready_nodes(status_map: Dict[str, str]) -> Dict[str, str]:
    """Adapt checkpoint statuses so traversal can continue after failed nodes."""
    converted: Dict[str, str] = {}
    for node_id, status in status_map.items():
        normalized = _normalize_node_status(status)
        if normalized in (NodeStatus.FAILED.value, NodeStatus.SKIPPED.value):
            converted[node_id] = NodeStatus.COMPLETED.value
        else:
            converted[node_id] = normalized
    return converted


def _is_terminal_node_status(status: Any) -> bool:
    """Return True when status represents a finished node state."""
    normalized = _normalize_node_status(status)
    return normalized in (
        NodeStatus.COMPLETED.value,
        NodeStatus.FAILED.value,
        NodeStatus.SKIPPED.value,
    )


def _signal_to_display_status(signal: Dict[str, Any]) -> str:
    """Map PL signal types to pipeline display statuses."""
    signal_type = str(signal.get("signal", "unknown")).strip().lower()
    if signal_type == "done":
        return NodeStatus.COMPLETED.value
    if signal_type in ("error", "blocked"):
        return NodeStatus.FAILED.value
    if signal_type == "skipped":
        return NodeStatus.SKIPPED.value
    if signal_type in ("in_progress", "running"):
        return NodeStatus.IN_PROGRESS.value
    return NodeStatus.PENDING.value


def _node_status_label(status: Any) -> str:
    """Map normalized statuses to compact DAG labels."""
    normalized = _normalize_node_status(status)
    if normalized == NodeStatus.COMPLETED.value:
        return "DONE"
    if normalized == NodeStatus.IN_PROGRESS.value:
        return "RUN"
    if normalized == NodeStatus.FAILED.value:
        return "FAIL"
    if normalized == NodeStatus.SKIPPED.value:
        return "SKIP"
    return "PEND"


def render_graph_status(graph: Graph, status_map: Dict[str, str]) -> str:
    """Render DAG execution state with simple ASCII arrows."""
    children: Dict[str, List[str]] = {node_id: [] for node_id in graph.nodes}
    incoming_count: Dict[str, int] = {node_id: 0 for node_id in graph.nodes}

    for edge in sorted(graph.edges, key=lambda item: (item.source, item.target)):
        if edge.source not in graph.nodes or edge.target not in graph.nodes:
            continue
        children[edge.source].append(edge.target)
        incoming_count[edge.target] += 1

    roots = sorted(
        [node_id for node_id, count in incoming_count.items() if count == 0]
    )
    if not roots:
        roots = sorted(graph.nodes)

    lines = ["Pipeline Status:"]
    rendered_nodes: Set[str] = set()
    rendered_edges: Set[Tuple[str, str]] = set()

    def node_line(node_id: str) -> str:
        node = graph.nodes[node_id]
        label = _node_status_label(
            status_map.get(node_id, NodeStatus.PENDING.value)
        )
        display_name = node.name or node_id
        return f"[{label}] {display_name}"

    for root_id in roots:
        lines.append(f"  {node_line(root_id)}")
        rendered_nodes.add(root_id)
        queue: deque[Tuple[str, str]] = deque([(root_id, "    ")])

        while queue:
            parent_id, indent = queue.popleft()
            for child_id in sorted(children.get(parent_id, [])):
                edge_key = (parent_id, child_id)
                if edge_key in rendered_edges:
                    continue
                rendered_edges.add(edge_key)

                lines.append(f"{indent}|-> {node_line(child_id)}")
                if child_id in rendered_nodes:
                    continue
                rendered_nodes.add(child_id)
                queue.append((child_id, indent + "    "))

    for node_id in sorted(graph.nodes):
        if node_id in rendered_nodes:
            continue
        lines.append(f"  {node_line(node_id)}")

    return "\n".join(lines)


def _describe_blocked_nodes(
    graph: Graph,
    graph_engine: GraphEngine,
    status_map: Dict[str, str],
) -> str:
    """Build a concise description of pending nodes and unmet dependencies."""
    blocked: List[str] = []
    for node_id in sorted(graph.nodes):
        status = _normalize_node_status(
            status_map.get(node_id, NodeStatus.PENDING.value)
        )
        if status != NodeStatus.PENDING.value:
            continue

        upstream = sorted(graph_engine.get_upstream_nodes(node_id))
        if not upstream:
            blocked.append(f"{node_id}: pending (no upstream dependencies)")
            continue

        upstream_state = ", ".join(
            f"{dep}={_normalize_node_status(status_map.get(dep, NodeStatus.PENDING.value))}"
            for dep in upstream
        )
        blocked.append(f"{node_id}: waiting on {upstream_state}")

    return "; ".join(blocked) if blocked else "No blocked node details available"


def _collect_downstream_nodes(graph_engine: GraphEngine, start_node_id: str) -> List[str]:
    """Return all transitive downstream node IDs from the starting node."""
    queue: deque[str] = deque([start_node_id])
    seen: Set[str] = set()

    while queue:
        current = queue.popleft()
        for downstream_id in graph_engine.get_downstream_nodes(current):
            if downstream_id in seen:
                continue
            seen.add(downstream_id)
            queue.append(downstream_id)

    return sorted(seen)


def _resolve_discovery_context_artifact(
    upstream_id: str,
    checkpoint_manager: "CheckpointManager",
    project_dir: Path,
) -> Optional[Tuple[str, Path]]:
    """Resolve discovery CONTEXT.md artifact path for an upstream node."""
    artifact_paths = checkpoint_manager.get_artifacts(upstream_id)
    candidates: List[str] = []

    for artifact in artifact_paths:
        artifact_text = str(artifact or "").strip()
        if not artifact_text:
            continue
        if Path(artifact_text).name.lower() == "context.md":
            candidates.append(artifact_text)

    if not candidates:
        candidates.append(f"tasks/{upstream_id}/CONTEXT.md")

    for candidate in candidates:
        path = Path(candidate)
        if not path.is_absolute():
            path = project_dir / path
        if not path.is_file():
            continue

        try:
            relative = str(path.resolve().relative_to(project_dir.resolve()))
        except ValueError:
            relative = str(path)
        return (relative, path)

    logger.warning(
        "CONTEXT.md missing for discovery node '%s'; checked candidates: %s",
        upstream_id,
        ", ".join(candidates),
    )
    return None


def _collect_upstream_execution_path(
    graph_engine: GraphEngine,
    node_id: str,
) -> List[str]:
    """Collect all transitive upstream node IDs for a node."""
    queue: deque[str] = deque(sorted(graph_engine.get_upstream_nodes(node_id)))
    seen: Set[str] = set()
    ordered: List[str] = []

    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        ordered.append(current)

        for upstream_id in sorted(graph_engine.get_upstream_nodes(current)):
            if upstream_id not in seen:
                queue.append(upstream_id)

    return ordered


def estimate_token_count(text: str) -> int:
    """Estimate token count from character length using a 4:1 ratio."""
    return max(0, len(text) // 4)


def build_node_context(
    node: GraphNode,
    graph: Graph,
    checkpoint_mgr: "CheckpointManager",
    project_dir: Path,
    fidelity: ContextFidelityMode = ContextFidelityMode.MINIMAL,
) -> str:
    """Build node context with minimal, partial, and full fidelity modes."""
    graph_engine = GraphEngine(graph)
    fidelity_mode = _coerce_enum(
        ContextFidelityMode,
        fidelity,
        ContextFidelityMode.MINIMAL,
        f"graph node '{node.id}' context_fidelity",
    )

    node_payload = {
        "id": node.id,
        "name": node.name,
        "type": node.type.value if isinstance(node.type, Enum) else str(node.type),
        "class": node.node_class,
        "handler": node.handler,
        "inputs": node.inputs,
        "criteria": list(node.criteria),
        "complexity_hint": node.complexity_hint,
        "prd_path": node.prd_path,
        "branch": node.branch,
        "output_path": node.output_path,
        "source_materials": list(node.source_materials),
    }

    outcomes_path = project_dir / "tasks" / "OUTCOMES.md"
    outcomes_summary = "Unavailable"
    if outcomes_path.is_file():
        try:
            outcomes_text = outcomes_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            logger.warning("Failed to read OUTCOMES.md for node context: %s", exc)
        else:
            if outcomes_text:
                outcomes_summary = outcomes_text[:500]

    memory_paths: List[str] = []
    for path_text in (
        ".ai/ARCHITECTURE.json",
        ".ai/FILES.json",
        ".ai/PATTERNS.md",
        ".ai/QUICK.md",
        ".ai/BUSINESS.json",
    ):
        exists = (project_dir / path_text).is_file()
        suffix = "" if exists else " (missing)"
        memory_paths.append(f"- {path_text}{suffix}")

    lines = [
        f"NODE_CONTEXT_FIDELITY: {fidelity_mode.value}",
        "NODE_PARAMETERS:",
        json.dumps(node_payload, indent=2, sort_keys=True, ensure_ascii=True),
        "PROJECT_CONTEXT:",
        f"OUTCOMES_SUMMARY: {outcomes_summary}",
        "MEMORY_SYSTEM_PATHS:",
    ] + memory_paths

    direct_upstream_nodes = sorted(graph_engine.get_upstream_nodes(node.id))
    if fidelity_mode in (ContextFidelityMode.PARTIAL, ContextFidelityMode.FULL):
        upstream_summaries: List[Tuple[str, str]] = []
        discovery_contents: List[Tuple[str, str, str]] = []

        for upstream_id in direct_upstream_nodes:
            summary = checkpoint_mgr.get_output_summary(upstream_id)
            summary_text = str(summary or "").strip()
            if summary_text:
                if fidelity_mode == ContextFidelityMode.PARTIAL:
                    summary_text = summary_text[:500]
                upstream_summaries.append((upstream_id, summary_text))

            upstream_node = graph.nodes.get(upstream_id)
            is_discovery = (
                upstream_node is not None and upstream_node.type == NodeType.DISCOVERY
            )
            if not is_discovery:
                continue

            resolved = _resolve_discovery_context_artifact(
                upstream_id,
                checkpoint_mgr,
                project_dir,
            )
            if resolved is None:
                continue

            relative_path, absolute_path = resolved
            try:
                context_text = absolute_path.read_text(encoding="utf-8").strip()
            except OSError as exc:
                logger.warning(
                    "Failed to read CONTEXT.md for discovery node '%s': %s",
                    upstream_id,
                    exc,
                )
                continue

            if context_text:
                discovery_contents.append((upstream_id, relative_path, context_text))
                logger.info(
                    "Including CONTEXT.md from discovery node '%s' in context for '%s'",
                    upstream_id,
                    node.id,
                )

        if upstream_summaries:
            lines.append("UPSTREAM_NODE_SUMMARIES:")
            for upstream_id, text in upstream_summaries:
                lines.append(f"- {upstream_id}: {text}")

        if discovery_contents:
            lines.append("DISCOVERY_CONTEXT_CONTENT:")
            for upstream_id, path_text, text in discovery_contents:
                lines.append(f"--- BEGIN {upstream_id} ({path_text}) ---")
                lines.append(text)
                lines.append(f"--- END {upstream_id} ---")

    if fidelity_mode == ContextFidelityMode.FULL:
        all_upstream_nodes = _collect_upstream_execution_path(graph_engine, node.id)
        full_outputs: List[Tuple[str, str]] = []
        for upstream_id in all_upstream_nodes:
            summary = checkpoint_mgr.get_output_summary(upstream_id)
            summary_text = str(summary or "").strip()
            if summary_text:
                full_outputs.append((upstream_id, summary_text))

        if full_outputs:
            lines.append("FULL_UPSTREAM_OUTPUT:")
            for upstream_id, text in full_outputs:
                lines.append(f"--- BEGIN OUTPUT {upstream_id} ---")
                lines.append(text)
                lines.append(f"--- END OUTPUT {upstream_id} ---")

    context = "\n".join(lines)
    estimated_tokens = estimate_token_count(context)
    if fidelity_mode == ContextFidelityMode.MINIMAL and estimated_tokens > 30000:
        logger.warning(
            "Minimal context target exceeded for node '%s' (~%d tokens > 30K target)",
            node.id,
            estimated_tokens,
        )
    if fidelity_mode == ContextFidelityMode.PARTIAL and estimated_tokens > 60000:
        logger.warning(
            "Partial context target exceeded for node '%s' (~%d tokens > 60K target)",
            node.id,
            estimated_tokens,
        )
    if fidelity_mode == ContextFidelityMode.FULL and estimated_tokens > 100000:
        logger.warning(
            "Full context exceeds 100K tokens, downgrading to partial for node '%s' (~%d tokens)",
            node.id,
            estimated_tokens,
        )
        return build_node_context(
            node=node,
            graph=graph,
            checkpoint_mgr=checkpoint_mgr,
            project_dir=project_dir,
            fidelity=ContextFidelityMode.PARTIAL,
        )

    logger.info(
        "Built node context for '%s' with fidelity='%s' (~%d tokens)",
        node.id,
        fidelity_mode.value,
        estimated_tokens,
    )
    return context


def _build_node_context(
    node: GraphNode,
    graph_engine: GraphEngine,
    checkpoint_manager: "CheckpointManager",
    project_dir: Path,
) -> str:
    """Backward-compatible wrapper around public build_node_context()."""
    return build_node_context(
        node=node,
        graph=graph_engine.graph,
        checkpoint_mgr=checkpoint_manager,
        project_dir=project_dir,
        fidelity=_coerce_enum(
            ContextFidelityMode,
            node.context_fidelity,
            ContextFidelityMode.MINIMAL,
            f"graph node '{node.id}' context_fidelity",
        ),
    )


def _node_outcome_to_result(
    node: GraphNode,
    outcome: NodeOutcome,
) -> Dict[str, Any]:
    """Translate NodeOutcome back into legacy sprint/signal shape for PM context."""
    branch = node.branch or (
        f"sprint/{node.id}"
        if str(node.handler or "").strip().lower() == DomainType.SOFTWARE.value
        else ""
    )
    sprint_payload = {
        "name": node.name or node.id,
        "prd": node.prd_path or "",
        "branch": branch,
        "parallel_safe": False,
        "graph_node_id": node.id,
    }

    status = _normalize_node_status(outcome.status)
    signal: Dict[str, Any]
    if status == NodeStatus.COMPLETED.value:
        signal = {
            "signal": "done",
            "summary": outcome.output_summary,
        }
    elif status == NodeStatus.SKIPPED.value:
        signal = {
            "signal": "skipped",
            "reason": outcome.output_summary,
        }
    else:
        signal = {
            "signal": "error",
            "error_type": "execution_failed",
            "details": outcome.error_details or outcome.output_summary,
        }

    if outcome.commit_shas:
        signal["commit_shas"] = list(outcome.commit_shas)
    if outcome.merge_success is False and outcome.merge_details:
        signal["merge_conflict"] = outcome.merge_details

    return {
        "sprint": sprint_payload,
        "signal": signal,
        "merge_success": outcome.merge_success,
        "merge_details": outcome.merge_details,
        "artifacts": list(outcome.artifacts),
    }


def _find_resumable_run_dir(tasks_dir: Path, graph_hash: str) -> Optional[Path]:
    """Find the newest run-* directory with checkpoint hash matching graph."""
    run_dirs = sorted(
        [path for path in tasks_dir.glob("run-*") if path.is_dir()],
        key=lambda item: item.name,
        reverse=True,
    )
    saw_checkpoint = False

    for run_dir in run_dirs:
        checkpoint_path = run_dir / "checkpoint.json"
        if not checkpoint_path.is_file():
            continue
        saw_checkpoint = True

        try:
            payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                "Skipping resume candidate '%s' due to unreadable checkpoint: %s",
                run_dir,
                exc,
            )
            continue

        existing_hash = str(payload.get("graph_hash", "")).strip()
        if existing_hash and existing_hash == graph_hash:
            return run_dir

    if saw_checkpoint:
        logger.info(
            "Detected prior run checkpoints but none match current graph hash; "
            "starting a fresh run"
        )

    return None


# ---------------------------------------------------------------------------
# 7.4 -- Main PM-PL orchestration cycle loop
# ---------------------------------------------------------------------------

def run_orchestration(state: OrchestratorState) -> int:
    """Main orchestration loop. Returns exit code (0=success, 1=error)."""
    pm_error_retries = 0
    sprint_history: List[str] = []
    pl_results: Optional[List[Dict[str, Any]]] = None
    roadmap_content = read_roadmap(state)
    stylesheet_loader = StylesheetLoader(str(state.project_dir / "model-stylesheet.yaml"))
    handler_registry: Dict[str, NodeHandler] = {
        DomainType.SOFTWARE.value: SoftwareHandler(),
        DomainType.CONTENT.value: ContentHandler(),
        NodeType.DISCOVERY.value: DiscoveryHandler(),
    }

    while state.cycle_count < state.max_cycles:
        check_shutdown(state)

        state.cycle_count += 1
        logger.info(
            "=== Cycle %d / %d ===", state.cycle_count, state.max_cycles
        )

        # 1. Invoke PM
        pm_context = build_pm_context(state, pl_results, roadmap_content)

        try:
            pm_output = invoke_agent(
                "pm", pm_context, state.project_dir, timeout=state.pm_timeout,
                cycle=state.cycle_count,
            )
        except subprocess.TimeoutExpired:
            logger.error("PM agent timed out")
            if pm_error_retries < PM_ERROR_MAX_RETRIES:
                pm_error_retries += 1
                logger.info("Retrying PM (attempt %d)", pm_error_retries + 1)
                continue
            logger.error("PM timed out after %d retries -- halting", pm_error_retries)
            return 1
        except RuntimeError as exc:
            logger.error("PM invocation failed: %s", exc)
            if pm_error_retries < PM_ERROR_MAX_RETRIES:
                pm_error_retries += 1
                logger.info("Retrying PM (attempt %d)", pm_error_retries + 1)
                continue
            logger.error("PM failed after %d retries -- halting", pm_error_retries)
            return 1

        # 2. Parse PM signal
        pm_signal = parse_signal(pm_output)
        signal_type = pm_signal.get("signal", "unknown")
        signal_summary = pm_signal.get("summary", pm_signal.get("reason", ""))
        logger.info(
            "PM signal: %s%s",
            signal_type,
            f" -- {signal_summary}" if signal_summary else "",
        )
        logger.debug("PM signal parsed: %s", pm_signal)

        # 3. Handle PM signal
        if signal_type == "complete":
            summary = pm_signal.get("summary", "No summary provided")
            outcomes = pm_signal.get("outcomes_completed", [])
            logger.info("Project COMPLETE: %s", summary)
            if outcomes:
                logger.info("Outcomes completed: %s", ", ".join(str(o) for o in outcomes))
            print(f"\nProject complete: {summary}")
            return 0

        elif signal_type == "blocked":
            reason = pm_signal.get("reason", "Unknown reason")
            needed = pm_signal.get("what_is_needed", "Unknown")
            recommendation = pm_signal.get("recommendation", "None")
            logger.info(
                "PM BLOCKED: %s | Need: %s | Recommendation: %s",
                reason, needed, recommendation,
            )
            print(f"\nBlocked: {reason}")
            print(f"What is needed: {needed}")
            print(f"Recommendation: {recommendation}")
            return 1

        elif signal_type == "error":
            error_type = pm_signal.get("error_type", "unknown")
            details = pm_signal.get("details", "No details")
            logger.error("PM error (%s): %s", error_type, details)

            if pm_error_retries < PM_ERROR_MAX_RETRIES:
                pm_error_retries += 1
                logger.info("Retrying PM after error (attempt %d)", pm_error_retries + 1)
                continue
            logger.error(
                "PM errors exceeded retry limit (%d) -- halting", PM_ERROR_MAX_RETRIES
            )
            return 1

        elif signal_type in ("next_task", "next_graph"):
            pm_summary = pm_signal.get("summary", "")

            graph = pm_signal.get("graph")
            if not isinstance(graph, Graph):
                try:
                    if signal_type == "next_task":
                        sprints_data = pm_signal.get("sprints", [])
                        if not isinstance(sprints_data, list):
                            logger.error(
                                "PM sent next_task signal with non-list 'sprints' payload"
                            )
                            if pm_error_retries < PM_ERROR_MAX_RETRIES:
                                pm_error_retries += 1
                                logger.info(
                                    "Retrying PM after invalid next_task payload (attempt %d)",
                                    pm_error_retries + 1,
                                )
                                continue
                            return 1
                        graph = _sprints_to_graph(sprints_data, pm_signal)
                    else:
                        graph = _parse_graph_signal(pm_signal)
                except Exception as exc:
                    logger.error("Failed to parse PM %s payload: %s", signal_type, exc)
                    if pm_error_retries < PM_ERROR_MAX_RETRIES:
                        pm_error_retries += 1
                        logger.info(
                            "Retrying PM after parse failure (attempt %d)",
                            pm_error_retries + 1,
                        )
                        continue
                    return 1

            if not isinstance(graph, Graph):
                logger.error("PM %s signal did not produce a valid graph", signal_type)
                if pm_error_retries < PM_ERROR_MAX_RETRIES:
                    pm_error_retries += 1
                    logger.info(
                        "Retrying PM after invalid graph payload (attempt %d)",
                        pm_error_retries + 1,
                    )
                    continue
                return 1

            domain_raw = pm_signal.get("domain")
            domain_text = str(domain_raw).strip() if domain_raw is not None else ""
            if domain_text:
                graph.domain = _coerce_enum(
                    DomainType,
                    domain_text,
                    DomainType.SOFTWARE,
                    "graph domain",
                )
            else:
                try:
                    outcomes_content = state.outcomes_path.read_text(encoding="utf-8")
                except OSError as exc:
                    logger.warning(
                        "Failed to read OUTCOMES.md for domain detection: %s. "
                        "Defaulting to '%s'",
                        exc,
                        DomainType.SOFTWARE.value,
                    )
                    graph.domain = DomainType.SOFTWARE
                else:
                    graph.domain = detect_domain(outcomes_content)
                    logger.info(
                        "PM signal missing domain; detected '%s' from OUTCOMES.md",
                        graph.domain.value,
                    )

            logger.info(
                "PM planned graph with %d node(s), %d edge(s): %s",
                len(graph.nodes),
                len(graph.edges),
                pm_summary,
            )

            if not graph.nodes:
                logger.error("PM sent %s signal with empty graph definition", signal_type)
                if pm_error_retries < PM_ERROR_MAX_RETRIES:
                    pm_error_retries += 1
                    logger.info(
                        "Retrying PM after empty graph signal (attempt %d)",
                        pm_error_retries + 1,
                    )
                    continue
                return 1

            # Stuck loop detection
            new_names = [node.name for node in graph.nodes.values()]
            for name in new_names:
                sprint_history.append(name)

            stuck_name = detect_stuck_loop(sprint_history, [])
            if stuck_name:
                logger.error(
                    "STUCK: PM keeps generating same sprint '%s' "
                    "(%d times in sequence). Check ROADMAP.md for inconsistencies.",
                    stuck_name, STUCK_THRESHOLD,
                )
                print(
                    f"\nStuck: PM keeps generating same sprint '{stuck_name}'. "
                    "Check ROADMAP.md for inconsistencies."
                )
                return 1

            graph_engine = GraphEngine(graph)
            graph_valid, validation_errors = graph_engine.validate()
            if not graph_valid:
                for error_text in validation_errors:
                    logger.error("Graph validation error: %s", error_text)
                if pm_error_retries < PM_ERROR_MAX_RETRIES:
                    pm_error_retries += 1
                    logger.info(
                        "Retrying PM after graph validation failure (attempt %d)",
                        pm_error_retries + 1,
                    )
                    continue
                logger.error("Graph validation failed after %d retries -- halting", pm_error_retries)
                return 1

            # Reset error retry counter on successful PM planning.
            pm_error_retries = 0

            tasks_dir = state.project_dir / "tasks"
            expected_graph_hash = _compute_graph_hash(graph)
            resume_run_dir = _find_resumable_run_dir(tasks_dir, expected_graph_hash)

            if resume_run_dir is not None:
                run_id = resume_run_dir.name
                run_dir = resume_run_dir
                logger.info(
                    "Resuming graph run '%s' from %s (checkpoint hash matched)",
                    run_id,
                    run_dir,
                )
            else:
                run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
                run_dir = tasks_dir / run_id
                run_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Starting new graph run '%s' at %s", run_id, run_dir)

            checkpoint_manager = CheckpointManager(str(run_dir), graph)
            state.current_graph = graph
            state.checkpoint_manager = checkpoint_manager
            state.run_id = checkpoint_manager.run_id or run_id

            node_results: List[Dict[str, Any]] = []

            logger.info(
                "%s",
                render_graph_status(graph, checkpoint_manager.get_status_map()),
            )

            # Graph traversal loop.
            while True:
                check_shutdown(state)

                status_map = checkpoint_manager.get_status_map()
                ready_nodes = graph_engine.get_ready_nodes(
                    _status_map_for_ready_nodes(status_map)
                )
                all_nodes_complete = all(
                    _is_terminal_node_status(
                        status_map.get(node_id, NodeStatus.PENDING.value)
                    )
                    for node_id in graph.nodes
                )

                if all_nodes_complete:
                    break

                if not ready_nodes:
                    blocked_details = _describe_blocked_nodes(
                        graph,
                        graph_engine,
                        status_map,
                    )
                    logger.error(
                        "Pipeline is stuck: no ready nodes while graph is incomplete"
                    )
                    logger.error("Blocked nodes: %s", blocked_details)
                    print("\nPipeline stuck: no ready nodes while graph is incomplete.")
                    print(f"Blocked nodes: {blocked_details}")
                    return 1

                for node_id in ready_nodes:
                    check_shutdown(state)

                    node = graph.nodes[node_id]
                    model_config = stylesheet_loader.select(node.node_class)
                    model_hint = f"{model_config.provider}:{model_config.model}"
                    checkpoint_manager.record_node_start(node_id, model_hint)

                    handler_key = str(node.handler or "").strip().lower()
                    handler = handler_registry.get(handler_key)
                    if handler is None:
                        logger.warning(
                            "Graph node '%s' requested unknown handler '%s'; defaulting to '%s'",
                            node.id,
                            node.handler,
                            DomainType.SOFTWARE.value,
                        )
                        handler = handler_registry[DomainType.SOFTWARE.value]

                    node_context = _build_node_context(
                        node,
                        graph_engine,
                        checkpoint_manager,
                        state.project_dir,
                    )
                    logger.info(
                        "Executing graph node '%s' (%s via %s)",
                        node.name,
                        handler_key or DomainType.SOFTWARE.value,
                        model_hint,
                    )

                    outcome = handler.execute(
                        node=node,
                        context=node_context,
                        config=model_config,
                        project_dir=state.project_dir,
                        cycle=state.cycle_count,
                    )
                    result = _node_outcome_to_result(node, outcome)
                    node_results.append(result)
                    checkpoint_manager.record_node_completion(node_id, outcome)

                    if (
                        node.type == NodeType.DISCOVERY
                        and _normalize_node_status(outcome.status) == NodeStatus.COMPLETED.value
                    ):
                        context_artifact = next(
                            (
                                str(artifact).strip()
                                for artifact in outcome.artifacts
                                if str(artifact).strip()
                                and Path(str(artifact)).name.lower() == "context.md"
                            ),
                            "",
                        )
                        if not context_artifact:
                            logger.warning(
                                "Discovery node '%s' completed without CONTEXT.md artifact",
                                node.id,
                            )
                        else:
                            context_artifact_path = Path(context_artifact)
                            if not context_artifact_path.is_absolute():
                                context_artifact_path = state.project_dir / context_artifact_path
                            if not context_artifact_path.is_file():
                                logger.warning(
                                    "CONTEXT.md missing after discovery node '%s' completion: %s",
                                    node.id,
                                    context_artifact,
                                )

                        for downstream_id in _collect_downstream_nodes(graph_engine, node.id):
                            downstream_node = graph.nodes.get(downstream_id)
                            if downstream_node is None:
                                continue
                            if str(downstream_node.node_class).strip().lower() != "planning":
                                continue

                            current_fidelity = _coerce_enum(
                                ContextFidelityMode,
                                downstream_node.context_fidelity,
                                ContextFidelityMode.MINIMAL,
                                f"graph node '{downstream_node.id}' context_fidelity",
                            )
                            if current_fidelity == ContextFidelityMode.MINIMAL:
                                downstream_node.context_fidelity = ContextFidelityMode.PARTIAL
                                logger.info(
                                    "Promoted planning node '%s' context_fidelity to '%s' due to discovery node '%s'",
                                    downstream_node.id,
                                    ContextFidelityMode.PARTIAL.value,
                                    node.id,
                                )

                    for edge in graph_engine.forward_edges.get(node_id, []):
                        condition_active = graph_engine.evaluate_edge_condition(edge, outcome)
                        logger.info(
                            "Edge %s -> %s condition '%s' => %s",
                            edge.source,
                            edge.target,
                            edge.condition or "always",
                            "active" if condition_active else "inactive",
                        )

                    logger.info(
                        "Graph node '%s' completed in %.1fs with signal '%s'",
                        node.name,
                        outcome.duration,
                        result.get("signal", {}).get("signal", "unknown"),
                    )

                    _capture_session_logs(
                        result.get("sprint", {}),
                        state.project_dir,
                        state.cycle_count,
                    )

                    display_map = checkpoint_manager.get_status_map()
                    display_map[node_id] = _normalize_node_status(outcome.status)
                    logger.info("%s", render_graph_status(graph, display_map))

            pl_results = node_results

            # Categorize results for logging and PM context.
            categorized = categorize_sprint_results(pl_results)
            logger.info("Sprint execution: %s", categorized["summary"])

            if categorized["failed"]:
                for fr in categorized["failed"]:
                    sprint_name = fr.get("sprint", {}).get("name", "unknown")
                    sig = fr.get("signal", {})
                    logger.warning(
                        "Failed sprint '%s': %s -- %s",
                        sprint_name,
                        sig.get("signal", "unknown"),
                        sig.get("details", sig.get("blocker_description", "no details")),
                    )

            # Re-read roadmap for next PM cycle
            roadmap_content = read_roadmap(state)

        else:
            # Unknown signal type
            logger.error(
                "Unknown PM signal type: '%s'. Raw signal: %s",
                signal_type, str(pm_signal)[:300],
            )
            if pm_error_retries < PM_ERROR_MAX_RETRIES:
                pm_error_retries += 1
                continue
            return 1

    # Max cycles reached
    logger.error(
        "Maximum cycles (%d) reached. Project may be too large for a single "
        "orchestration run or PM is not making progress.",
        state.max_cycles,
    )
    print(
        f"\nMaximum cycles ({state.max_cycles}) reached. "
        "PM may not be making progress."
    )
    return 1


# ---------------------------------------------------------------------------
# Argument parsing and main entry point
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Post-completion archiving
# ---------------------------------------------------------------------------

# Files and directories to archive from tasks/ on successful completion.
# Anything in tasks/ not in this list and not in ARCHIVE_PRESERVE is moved
# to the archive as a sprint directory.
ARCHIVE_KNOWN_FILES = {
    "OUTCOMES.md",
    "DECISIONS.md",
    "PROJECT_STATE.md",
    "ROADMAP.md",
    "CONTEXT.md",
    "OUTCOMES_STATE.md",
    "outcomes-draft.md",
    "outcomes-refined.md",
    "outcomes-setup.xml",
    "orchestrator.log",
}

# Directories in tasks/ that are always archived as a unit.
ARCHIVE_KNOWN_DIRS = {
    "agent-logs",
    "red-team",
}

# Entries in tasks/ that must never be moved.
ARCHIVE_PRESERVE = {
    "archive",
    "screenshots",
}


def _derive_archive_name(state: OrchestratorState) -> str:
    """Derive a human-readable archive folder name from ROADMAP.md or project dir."""
    roadmap = state.roadmap_path
    name = None
    if roadmap.is_file():
        try:
            for line in roadmap.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("# "):
                    # Use the H1 heading, slugified
                    raw = line[2:].strip()
                    name = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
                    break
        except OSError:
            pass
    if not name:
        name = state.project_dir.name
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{name}-{date_str}"


def archive_completed_project(state: OrchestratorState) -> bool:
    """Archive all orchestrator artifacts into tasks/archive/<name>/.

    Moves known files, known directories, tool-use logs, and any remaining
    sprint directories. Preserves tasks/archive/ and tasks/screenshots/.

    Returns True on success, False on error.
    """
    tasks_dir = state.project_dir / "tasks"
    if not tasks_dir.is_dir():
        logger.warning("No tasks/ directory to archive")
        return False

    archive_name = _derive_archive_name(state)
    archive_dir = tasks_dir / "archive" / archive_name
    archive_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Archiving completed project to %s", archive_dir)

    moved = []
    errors = []

    # 1. Move known files
    for filename in ARCHIVE_KNOWN_FILES:
        src = tasks_dir / filename
        if src.is_file():
            try:
                shutil.move(str(src), str(archive_dir / filename))
                moved.append(filename)
            except OSError as exc:
                errors.append(f"{filename}: {exc}")

    # 2. Move tool-use logs (tool-use.log, tool-use.log.1, etc.)
    for path in sorted(tasks_dir.glob("tool-use.log*")):
        if path.is_file():
            try:
                shutil.move(str(path), str(archive_dir / path.name))
                moved.append(path.name)
            except OSError as exc:
                errors.append(f"{path.name}: {exc}")

    # 3. Move known directories
    for dirname in ARCHIVE_KNOWN_DIRS:
        src = tasks_dir / dirname
        if src.is_dir():
            try:
                shutil.move(str(src), str(archive_dir / dirname))
                moved.append(f"{dirname}/")
            except OSError as exc:
                errors.append(f"{dirname}/: {exc}")

    # 4. Move any remaining sprint directories (anything not preserved)
    for entry in sorted(tasks_dir.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name in ARCHIVE_PRESERVE:
            continue
        # Already moved or it's the archive target itself
        if entry.name in ARCHIVE_KNOWN_DIRS:
            continue
        try:
            shutil.move(str(entry), str(archive_dir / entry.name))
            moved.append(f"{entry.name}/")
        except OSError as exc:
            errors.append(f"{entry.name}/: {exc}")

    # 5. Recreate agent-logs for next run
    (tasks_dir / "agent-logs").mkdir(parents=True, exist_ok=True)

    if errors:
        logger.warning("Archive errors: %s", "; ".join(errors))
    logger.info("Archived %d items to %s", len(moved), archive_dir)
    for item in moved:
        logger.debug("  archived: %s", item)

    return len(errors) == 0


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Autonomous orchestrator for fat-controller. "
        "Drives PM-PL cycles to deliver project outcomes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              python3 orchestrator.py /path/to/project
              python3 orchestrator.py . --max-cycles 10
              python3 orchestrator.py ~/myproject --log-level DEBUG --pm-timeout 300
        """),
    )
    parser.add_argument(
        "project_dir",
        type=Path,
        help="Path to the project directory (must contain tasks/OUTCOMES.md)",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=DEFAULT_MAX_CYCLES,
        help=f"Maximum PM-PL cycles before halting (default: {DEFAULT_MAX_CYCLES})",
    )
    parser.add_argument(
        "--pm-timeout",
        type=int,
        default=DEFAULT_PM_TIMEOUT,
        help=f"PM agent timeout in seconds (default: {DEFAULT_PM_TIMEOUT})",
    )
    parser.add_argument(
        "--pl-timeout",
        type=int,
        default=DEFAULT_PL_TIMEOUT,
        help=f"PL agent timeout in seconds (default: {DEFAULT_PL_TIMEOUT})",
    )
    parser.add_argument(
        "--log-level",
        default=DEFAULT_LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help=f"Logging level (default: {DEFAULT_LOG_LEVEL})",
    )
    parser.add_argument(
        "--skip-values-check",
        action="store_true",
        default=False,
        help="Skip interactive VALUES.md prompts (use when launched from /orchestrate command)",
    )

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point. Returns exit code."""
    signal.signal(signal.SIGINT, _handle_sigint)

    args = parse_args(argv)

    # Resolve project directory
    project_dir = args.project_dir.resolve()
    if not project_dir.is_dir():
        print(f"Error: '{project_dir}' is not a directory", file=sys.stderr)
        return 1

    # Initialize state
    state = OrchestratorState(
        project_dir=project_dir,
        roadmap_path=project_dir / "tasks" / "ROADMAP.md",
        outcomes_path=project_dir / "tasks" / "OUTCOMES.md",
        log_dir=project_dir / "tasks",
        max_cycles=args.max_cycles,
        pm_timeout=args.pm_timeout,
        pl_timeout=args.pl_timeout,
    )

    # Setup logging
    setup_logging(state.log_dir, args.log_level)
    logger.info(
        "Orchestrator starting: project=%s, max_cycles=%d, pm_timeout=%d, pl_timeout=%d",
        project_dir, state.max_cycles, state.pm_timeout, state.pl_timeout,
    )

    # --- Pre-flight checks ---

    # 1. VALUES.md check
    if args.skip_values_check:
        # Launched from /orchestrate command -- it already handled the prompts
        state.values_loaded = VALUES_PATH.is_file()
        if state.values_loaded:
            logger.info("Values profile loaded from %s", VALUES_PATH)
        else:
            logger.warning(
                "RUNNING WITHOUT VALUES PROFILE -- agents operating in generic mode"
            )
    elif not check_values(state):
        return 0  # User chose to exit -- not an error

    # 2. OUTCOMES.md validation (hard requirement)
    if not validate_outcomes(state):
        return 1

    # 3. Verify git repo
    git_check = git_run(
        ["rev-parse", "--is-inside-work-tree"], project_dir, check=False
    )
    if git_check.returncode != 0:
        logger.error(
            "Not a git repository: %s. Initialize with 'git init' first.",
            project_dir,
        )
        return 1
    logger.info("Git repository confirmed at %s", project_dir)

    # --- Run orchestration ---
    try:
        exit_code = run_orchestration(state)
    except KeyboardInterrupt:
        logger.info("Interrupted by user (KeyboardInterrupt)")
        exit_code = 1
    except Exception as exc:
        logger.exception("Unhandled exception in orchestration loop: %s", exc)
        exit_code = 1

    # --- Archive on successful completion ---
    if exit_code == 0:
        logger.info("Project completed successfully -- archiving artifacts")
        try:
            archive_completed_project(state)
        except Exception as exc:
            # Archiving failure should not change the exit code
            logger.warning("Archiving failed (non-fatal): %s", exc)

    logger.info("Orchestrator exiting with code %d", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
