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
import logging
import os
import re
import signal
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


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


signal.signal(signal.SIGINT, _handle_sigint)


def check_shutdown() -> None:
    """Check if a graceful shutdown was requested and exit if so."""
    if _shutting_down:
        logger.info("Graceful shutdown: exiting between operations")
        sys.exit(0)


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
        return _parse_simple_yaml(yaml_text)
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

        if stripped.startswith("- "):
            item_content = stripped[2:].strip()

            # Check if this array item has nested key: value pairs
            # e.g., "- name: foo" followed by indented "  prd: bar"
            item_match = re.match(r'^([\w_-]+)\s*:\s*(.*)', item_content)
            if item_match:
                # Object array item -- collect all fields at this or deeper indent
                obj: Dict[str, Any] = {}
                obj[item_match.group(1)] = _parse_scalar(item_match.group(2).strip())
                item_indent = current_indent
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
                    if field_match:
                        obj[field_match.group(1)] = _parse_scalar(
                            field_match.group(2).strip()
                        )
                    i += 1

                result.append(obj)
            else:
                # Simple scalar array item
                result.append(_parse_scalar(item_content))
                i += 1
        else:
            # Not an array item -- we're done
            break

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
    if lower in ("null", "~", "none"):
        return None

    # Numbers
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    return value


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

def invoke_agent(
    agent_name: str,
    context: str,
    project_dir: Path,
    timeout: int = DEFAULT_PM_TIMEOUT,
) -> str:
    """Invoke a Claude agent via CLI and capture stdout.

    Uses `claude --print --agent <name> -p <context>` to run the agent
    non-interactively. Falls back to piping context via stdin if -p is
    not supported.

    Args:
        agent_name: Agent to invoke (e.g., "pm", "pl")
        context: Context string to pass to the agent
        project_dir: Working directory for the subprocess
        timeout: Maximum time in seconds before killing the agent

    Returns:
        The agent's stdout output as a string.

    Raises:
        subprocess.TimeoutExpired: If the agent exceeds the timeout.
        RuntimeError: If the agent exits with a non-zero return code
                      and produces no stdout.
    """
    cmd = ["claude", "--print", "--agent", agent_name, "-p", context]

    logger.info("Invoking agent '%s' (timeout: %ds)", agent_name, timeout)
    start_time = time.monotonic()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(project_dir),
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start_time
        logger.error(
            "Agent '%s' timed out after %.1fs (limit: %ds)",
            agent_name, elapsed, timeout,
        )
        raise
    except FileNotFoundError:
        logger.error(
            "Claude CLI not found. Ensure 'claude' is on your PATH. "
            "Install via: npm install -g @anthropic-ai/claude-code"
        )
        raise RuntimeError("Claude CLI ('claude') not found on PATH")

    elapsed = time.monotonic() - start_time
    logger.info(
        "Agent '%s' completed in %.1fs (exit code: %d)",
        agent_name, elapsed, result.returncode,
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


def create_branch(branch_name: str, project_dir: Path) -> bool:
    """Create and checkout a git branch. Returns True on success."""
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
            return False
        return True

    # Create new branch from current HEAD
    logger.info("Creating branch '%s'", branch_name)
    result = git_run(["checkout", "-b", branch_name], project_dir, check=False)
    if result.returncode != 0:
        logger.error("Failed to create branch '%s': %s", branch_name, result.stderr)
        return False
    return True


def checkout_main(project_dir: Path) -> bool:
    """Checkout the main branch (tries 'main' then 'master')."""
    for branch in ("main", "master"):
        result = git_run(
            ["rev-parse", "--verify", branch], project_dir, check=False
        )
        if result.returncode == 0:
            checkout = git_run(["checkout", branch], project_dir, check=False)
            return checkout.returncode == 0
    logger.error("Neither 'main' nor 'master' branch found")
    return False


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

def build_pm_context(
    state: OrchestratorState,
    pl_results: Optional[List[Dict[str, Any]]] = None,
    roadmap_content: Optional[str] = None,
) -> str:
    """Build the context string passed to the PM agent."""
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
        parts.append("\n--- PL RESULTS FROM PREVIOUS CYCLE ---")
        for pr in pl_results:
            sprint = pr.get("sprint", {})
            sig = pr.get("signal", {})
            parts.append(
                f"Sprint: {sprint.get('name', 'unknown')}\n"
                f"  Signal: {sig.get('signal', 'unknown')}\n"
                f"  Summary: {sig.get('summary', sig.get('details', sig.get('blocker_description', 'N/A')))}"
            )
        parts.append("--- END PL RESULTS ---")

    return "\n".join(parts)


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

def execute_sprints(
    sprints: List[Dict[str, Any]],
    state: OrchestratorState,
) -> List[Dict[str, Any]]:
    """Execute sprints -- parallel if marked safe, sequential otherwise.

    For parallel sprints, each PL runs on its own branch concurrently.
    For sequential sprints, they run one at a time.

    Returns a list of result dicts with 'sprint' and 'signal' keys.
    """
    parallel = [s for s in sprints if s.get("parallel_safe", False)]
    sequential = [s for s in sprints if not s.get("parallel_safe", False)]
    results: List[Dict[str, Any]] = []

    # --- Parallel sprints ---
    if parallel:
        logger.info("Launching %d parallel sprint(s)", len(parallel))
        processes: List[tuple] = []

        for idx, sprint in enumerate(parallel):
            check_shutdown()

            # Checkout main before creating each branch
            checkout_main(state.project_dir)
            if not create_branch(sprint["branch"], state.project_dir):
                results.append({
                    "sprint": sprint,
                    "signal": {
                        "signal": "error",
                        "error_type": "branch_creation_failed",
                        "details": f"Failed to create branch {sprint['branch']}",
                    },
                })
                continue

            context = build_pl_context(sprint, state.project_dir)
            proc = invoke_agent_async("pl", context, state.project_dir)
            processes.append((sprint, proc))

            # Rate-limit to avoid API throttling
            if idx < len(parallel) - 1:
                time.sleep(PARALLEL_LAUNCH_DELAY)

        # Collect parallel results
        for sprint, proc in processes:
            try:
                stdout, stderr = proc.communicate(timeout=state.pl_timeout)
                sig = parse_signal(stdout or "")
                results.append({"sprint": sprint, "signal": sig})
                logger.info(
                    "Parallel sprint '%s' signal: %s",
                    sprint["name"], sig.get("signal", "unknown"),
                )
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                results.append({
                    "sprint": sprint,
                    "signal": {
                        "signal": "error",
                        "error_type": "timeout",
                        "details": f"PL timed out after {state.pl_timeout}s",
                    },
                })

    # --- Sequential sprints ---
    for sprint in sequential:
        check_shutdown()

        # Checkout main before creating branch
        checkout_main(state.project_dir)
        if not create_branch(sprint["branch"], state.project_dir):
            results.append({
                "sprint": sprint,
                "signal": {
                    "signal": "error",
                    "error_type": "branch_creation_failed",
                    "details": f"Failed to create branch {sprint['branch']}",
                },
            })
            continue

        context = build_pl_context(sprint, state.project_dir)
        try:
            output = invoke_agent(
                "pl", context, state.project_dir, timeout=state.pl_timeout
            )
            sig = parse_signal(output)
        except subprocess.TimeoutExpired:
            sig = {
                "signal": "error",
                "error_type": "timeout",
                "details": f"PL timed out after {state.pl_timeout}s",
            }
        except RuntimeError as exc:
            sig = {
                "signal": "error",
                "error_type": "invocation_failed",
                "details": str(exc),
            }

        results.append({"sprint": sprint, "signal": sig})
        logger.info(
            "Sequential sprint '%s' signal: %s",
            sprint["name"], sig.get("signal", "unknown"),
        )

    # Return to main branch after all sprints
    checkout_main(state.project_dir)

    return results


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
# 7.4 -- Main PM-PL orchestration cycle loop
# ---------------------------------------------------------------------------

def run_orchestration(state: OrchestratorState) -> int:
    """Main orchestration loop. Returns exit code (0=success, 1=error)."""
    pm_error_retries = 0
    sprint_history: List[str] = []
    pl_results: Optional[List[Dict[str, Any]]] = None
    roadmap_content = read_roadmap(state)

    while state.cycle_count < state.max_cycles:
        check_shutdown()

        state.cycle_count += 1
        logger.info(
            "=== Cycle %d / %d ===", state.cycle_count, state.max_cycles
        )

        # 1. Invoke PM
        pm_context = build_pm_context(state, pl_results, roadmap_content)

        try:
            pm_output = invoke_agent(
                "pm", pm_context, state.project_dir, timeout=state.pm_timeout
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
        logger.info("PM signal: %s", signal_type)

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

        elif signal_type == "next_task":
            # Reset error retry counter on success
            pm_error_retries = 0

            sprints_data = pm_signal.get("sprints", [])
            pm_summary = pm_signal.get("summary", "")
            logger.info("PM planned %d sprint(s): %s", len(sprints_data), pm_summary)

            if not sprints_data:
                logger.error("PM sent next_task signal with empty sprints list")
                if pm_error_retries < PM_ERROR_MAX_RETRIES:
                    pm_error_retries += 1
                    continue
                return 1

            # Normalize sprint data
            sprint_tasks = []
            for s in sprints_data:
                if isinstance(s, dict):
                    sprint_tasks.append(s)
                else:
                    logger.warning("Skipping non-dict sprint entry: %s", s)

            # Stuck loop detection
            new_names = [s.get("name", "") for s in sprint_tasks]
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

            # 4. Execute sprints
            check_shutdown()
            pl_results = execute_sprints(sprint_tasks, state)

            # Log PL results summary
            succeeded = [r for r in pl_results if r["signal"].get("signal") == "done"]
            failed = [
                r for r in pl_results
                if r["signal"].get("signal") in ("error", "blocked")
            ]
            logger.info(
                "Sprint execution: %d succeeded, %d failed",
                len(succeeded), len(failed),
            )

            # 5. Re-read roadmap for next PM cycle
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

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point. Returns exit code."""
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

    # 1. VALUES.md graduated warning (NOT a hard gate)
    if not check_values(state):
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

    logger.info("Orchestrator exiting with code %d", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
