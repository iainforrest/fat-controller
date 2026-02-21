# Changelog

All notable changes to this project are documented here. This file is automatically updated by the `/update` command during memory system updates.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- Project-scoped task directories: all orchestrator task paths now under `tasks/{slug}/` for multi-project isolation
- `--project slug` CLI argument to orchestrator.py; auto-detected when single `tasks/*/OUTCOMES.md` found
- `_project_tasks_dir(project_dir, slug)` helper as single path-resolution function in orchestrator.py
- `_is_valid_project_slug(slug)` validator: `[a-z0-9]+(-[a-z0-9]+)*`, max 64 chars
- `_find_project_slugs(tasks_dir)` scanner for auto-detection
- PRD path confinement: validates paths stay within `tasks/{slug}/` scope
- `/outcomes` Section 0: project slug resolution before any path use; startup scan for incomplete projects
- `/outcomes` resume detection: scans `tasks/*/outcomes/setup.xml` on startup
- `/outcomes` legacy detection: warns if `tasks/outcomes-setup.xml` exists, offers migration
- `/orchestrate` slug detection: scans `tasks/*/OUTCOMES.md` with find, auto-selects or prompts user
- Orchestrator archive: moves `tasks/{slug}/` as a unit to `tasks/archive/{slug}-{date}/` on completion
- execute.md: skip archive prompt when running under orchestration (`SPRINT_PRD` context present)

### Changed
- All node handlers (SoftwareHandler, ContentHandler, DiscoveryHandler) accept `project_slug` param
- PM agent derives all paths from `OUTCOMES_PATH`/`ROADMAP_PATH` context vars (no hardcoded `tasks/`)
- PL agent derives all paths from `dirname("$SPRINT_PRD")` (no hardcoded `tasks/{sprint-name}/`)
- PL log file path: `$(dirname "$SPRINT_PRD")/pl-session.log` (was `tasks/{SPRINT_NAME}/pl-session.log`)
- PL task.xml path: `$(dirname "$SPRINT_PRD")/task.xml` (was `tasks/{sprint-name}/task.xml`)
- /outcomes state file: `tasks/{slug}/outcomes/setup.xml` (was `tasks/outcomes-setup.xml`)
- /orchestrate launch: passes `--project {slug}` to orchestrator.py
- Orchestrator log: `tasks/{slug}/orchestrator.log` (was `tasks/orchestrator.log`)
- tasks/ filesystem: cleaned up stale files (prd-sync-command-agent-system.md, tasks-sync-command-agent-system.md, prd-templating-system.md, archive/cto-command-integration/)

### Fixed
- Code review findings: path safety (PRD confinement), archive logic, edge cases in orchestrator.py

### Added
- Graph Engine Core: DAG-based execution engine replacing linear PM-PL orchestration in orchestrator.py
- GraphNode, GraphEdge, Graph, NodeOutcome, ModelConfig, CheckpointState, NodeCheckpoint data models
- NodeType enum: TASK, DISCOVERY, GATE, FAN_OUT, FAN_IN
- ContextFidelityMode enum: MINIMAL, PARTIAL, FULL - controls upstream context passed to nodes
- DomainType enum: SOFTWARE, CONTENT, MIXED - drives handler selection
- GraphEngine class: DAG validation, ready-node selection, edge condition evaluation, cycle detection
- Per-node CheckpointManager: atomic write-then-rename persists state after every node transition
- Graph resume: restart interrupted runs from last checkpoint, not from scratch
- SoftwareHandler: code-focused node execution with worktree creation, merge, and git operations
- ContentHandler: content/writing node execution with source material aggregation
- DiscoveryHandler: adaptive complexity routing (simple vs complex discovery mode)
- GoalGate: deterministic acceptance criteria evaluator for gate nodes
- Goal gate retry routing: gate failures re-run retry_target node up to max_retries then escalate
- model-stylesheet.yaml: external model class definitions (planning, implementation, implementation-complex, review, gate, content-draft, discovery, discovery-simple, research, default) with provider, model, reasoning_effort, tool_profile, timeout, and fallback chains
- Provider-native invocation: claude CLI for Anthropic nodes, codex CLI for OpenAI nodes
- /lead command: boot Project Lead personality, load state files, generate briefing, begin orchestration
- project-lead.md agent: Project Lead identity, values, decision authority, sprint pipeline behavior
- discovery.md agent: Discovery node agent producing CONTEXT.md with approach, rationale, constraints
- prompt-architect.md agent: Prompt engineering specialist for prompt refinement work
- /outcomes v2: Full rewrite with 6-phase state machine (discovery, red-team, synthesis, context, refinement, finalize), XML phase tracking, resumability, and parallel red-team dispatch
- Auto-archiving: orchestrator archives completed project artifacts to tasks/archive/<name>-<date>/ on successful exit
- Graph Engine Orchestration pattern in PATTERNS.md
- Model Stylesheet pattern in PATTERNS.md
- Discovery Node pattern in PATTERNS.md
- Goal Gate Convergence pattern in PATTERNS.md
- Project Lead Orchestration pattern in PATTERNS.md
- /orchestrate command: Launch orchestrator in tmux background session with pre-flight checks
- PM agent (.claude/agents/pm.md): Project Manager for sprint planning and PRD generation
- PL agent (.claude/agents/pl.md): Project Lead for sprint execution via TaskGen and Execute
- templates/ROADMAP.md: Sprint state tracking template
- Structured Output Protocol: YAML signal blocks between ---ORCHESTRATOR_SIGNAL--- markers
- Values-Driven Agent Boot: PM, PL, and CTO agents load ~/.claude/VALUES.md for personalized decision-making
- Graduated Warning Flow: orchestrator checks for VALUES.md, warns if missing, allows user to proceed

### Changed
- orchestrator.py massively expanded (~4600 lines): graph engine replaces simple PM-PL loop
- /outcomes command fully rewritten as v2 with 6-phase state machine
- OrchestratorState extended with current_graph, checkpoint_manager, run_id fields
- _log_agent_io extended with command parameter for provider-native command logging

### Fixed
- Code review findings: security, logic, and deduplication issues in orchestrator.py
- Improved SIGINT handler with graceful shutdown and state preservation
- _compare_scalar_values extracted for deterministic gate criterion evaluation

---

## [3.1.2] - 2026-01-29

### Added
- Downstream effects analysis in /bugs, /feature, and /prd commands
- /debate command for multi-model decision analysis with Claude + Codex
- debate-agent.md for structured 3-round debate protocol
- debates/ directory output structure (brief.md, state.md, debate.md)

### Changed
- Exploration protocols now include "Map Downstream Effects" step
- Agent return formats extended with downstream_effects array
- Return format word limits increased to accommodate downstream effects sections

---

## [3.1.1] - 2026-01-25

### Added
- Changelog auto-generation during `/update` command
- Template separation system: `templates/.ai/` contains clean starter files
- `templates/tasks/` directory structure for task organization
- CHANGELOG.md to authority map and memory navigation
- Historical changelog entries from git commit history (1.0.0 - 3.0.6)

### Changed
- Model selection now uses gpt-5.2-codex with reasoning effort levels instead of model switching
  - Complexity 1-2: gpt-5.2-codex with medium reasoning effort
  - Complexity 3: Sonnet (unchanged)
  - Complexity 4-5: gpt-5.2-codex with xhigh reasoning effort
- `/pull-fc` command now syncs `templates/.ai/` and `templates/tasks/` from fat-controller
- Update-memory-agent now includes CHANGELOG.md in authority-based routing

---

## [1.0.0]

### Added
- Initial Claude Project Starter with AI memory system
- PRD generation v3.0 chain architecture and decision frameworks
- PRD generation v3.1 unified prompt improvements
- Prompt analysis framework for task review

### Removed
- Prompt analysis framework file

---

## [2.0.0]

### Added
- v2.0 upgrade package with slash commands and specialized agents
- Mandatory code documentation standards in the execute command
- Context-efficient memory system architecture
- Sync commands for starter kit updates
- Dual installation paths for new vs existing projects
- Explore agent integration for context-efficient codebase analysis
- Code review agent and `/review` command
- Step 5 "Future Proof" guidance in AI Assistant instructions
- EXPLORE_CONTEXT propagation through agent handoffs
- npx installable setup with interactive installer

### Changed
- Sync system simplified to use generic commands/agents
- `/tasks` renamed to `/TaskGen`
- Feature command delegates task generation to task-writer agent
- `/review` renamed to `/code-review` to avoid Claude conflict

---

## [2.3.0]

### Added
- Parallel task execution and domain skills in the execute command

---

## [3.0.0]

### Added
- `.gitignore` for development artifacts

### Changed
- Project renamed to The Fat Controller v3.0
- Sync commands renamed from cps to fc

---

## [3.0.1]

### Added
- Skills directory included in pull-fc and push-fc sync

---

## [3.0.2]

### Removed
- Legacy pull-cps/push-cps via migration in pull-fc

---

## [3.0.3]

### Fixed
- Critical guardrails to prevent orchestrator takeover in execute

---

## [3.0.4]

### Fixed
- Guardrails for task delegation and post-execution checks in execute

---

## [3.0.5]

### Fixed
- Mandatory code review and memory update tasks in task-writer XML template

---

## [3.0.6]

### Changed
- Updated .gitignore patterns for new structure

---

## Version History

_Previous releases will be documented below as versions are tagged._

---

<!--
CHANGELOG MAINTENANCE GUIDE (for update-memory-agent):

1. Add entries under [Unreleased] as changes are made
2. When releasing, move [Unreleased] content to a versioned section
3. Categories:
   - Added: New features
   - Changed: Changes to existing functionality
   - Fixed: Bug fixes
   - Deprecated: Features to be removed
   - Removed: Removed features
   - Security: Security fixes

4. Entry format: "- Brief description of change"
5. Group related changes together
6. Most recent changes at top of each category
-->
