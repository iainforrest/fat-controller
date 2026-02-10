# Changelog

All notable changes to this project are documented here. This file is automatically updated by the `/update` command during memory system updates.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- CTO agent file (.claude/agents/cto.md) with values-driven decision framework
- CTO Decision-Making Framework sections in prd.md, bugs.md, feature.md, execute.md
- Decision Authority sections defining what CTO decides vs escalates in each command
- Autonomous code review triage by CTO-orchestrator (no user interruption for fixes)
- CTO-advisor task completion review as post-execution validation step
- 9-step post-execution flow: code review → CTO triage → fix agents → verification → CTO-advisor → memory update → archive
- Dual-mode output for cto-technical-advisor (Mode A: briefing, Mode B: full advisory)
- STATE.md audit trail for all CTO triage decisions
- CTO Personality Overlay pattern in PATTERNS.md
- CTO Code Review Triage pattern in PATTERNS.md

### Changed
- Execute command now uses Codex 5.3 (gpt-5.3-codex) for all complexity levels
- Model selection: Codex 5.3 medium for complexity 1-3, xhigh for complexity 4-5
- Eliminated Sonnet tier (replaced with Codex 5.3 medium)
- Codex 5.3 provides 50% token reduction and 25% faster execution vs prior versions
- Commands (prd, bugs, feature, execute) now read cto.md at startup and adopt CTO decision framework
- cto-technical-advisor agent updated with dual-mode output and Relationship to CTO section

### Fixed
- TD-004: pull-fc command missing explicit cto.md sync validation (deferred to TECH_DEBT.md)
- TD-005: execute.md ambiguous 1-2 non-CRITICAL fix failure handling (deferred to TECH_DEBT.md)
- TD-006: Escalation criteria duplication across commands (deferred to TECH_DEBT.md)

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
