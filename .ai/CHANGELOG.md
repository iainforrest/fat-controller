# Changelog

All notable changes to this project are documented here. This file is automatically updated by the `/update` command during memory system updates.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- orchestrator.py: Python 3 stdlib orchestrator for autonomous PM-PL execution cycles (~1500 lines)
- PM agent (.claude/agents/pm.md): Project Manager for sprint planning and PRD generation (273 lines)
- PL agent (.claude/agents/pl.md): Project Lead for sprint execution via TaskGen and Execute (276 lines)
- templates/ROADMAP.md: Sprint state tracking template (198 lines)
- Structured Output Protocol: YAML signal blocks between ---ORCHESTRATOR_SIGNAL--- markers for orchestrator-agent communication
- Values-Driven Agent Boot: PM, PL, and CTO agents load ~/.claude/VALUES.md for personalized decision-making
- Graduated Warning Flow: orchestrator checks for VALUES.md, warns if missing, allows user to proceed in generic mode
- Generic Mode: agents use conservative judgments (~60% confidence threshold) when VALUES.md absent
- /values-discovery and /domain-values commands copied to fat-controller
- Git branch management: orchestrator creates sprint/* branches per sprint
- Parallel PL execution: orchestrator spawns multiple PL agents for independent sprints
- Two-phase merge: orchestrator runs git merge --no-commit to detect conflicts before committing
- Graceful shutdown: SIGINT (Ctrl+C) handler preserves ROADMAP.md state
- Stuck detection: orchestrator halts if same sprint name appears 3 times in sequence
- Session logging: .claude-orchestrator/orchestrator.log with structured timestamps
- Autonomous Orchestration pattern in PATTERNS.md
- Values-Driven Agent Boot pattern in PATTERNS.md
- Structured Output Protocol pattern in PATTERNS.md
- Python bytecode and orchestrator log exclusions in .gitignore

### Changed
- CTO agent (.claude/agents/cto.md) refactored for dynamic VALUES.md loading with graceful degradation
- README.md, INSTALL-NEW.md, INSTALL-EXISTING.md updated with orchestrator documentation and usage examples
- Memory system updated to track orchestrator components, agents, patterns, and data flows

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
