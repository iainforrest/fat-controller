# The Fat Controller v3.3

*"Really useful engines, every one."*

A complete AI-assisted development system that orchestrates Claude Code agents to build software. Like having an entire engineering team in your terminal.

> Named after Sir Topham Hatt from Thomas the Tank Engine - the one who keeps all the engines running on time.

## What This Is

- **Commands & Agents**: Reusable workflow tools that work across any project
- **AI Memory System**: Persistent project knowledge in `.ai/` that prevents context loss
- **Autonomous Orchestrator**: Hands-off PM-PL cycles that deliver outcomes while you sleep
- **Sync System**: Keep projects up-to-date with `/pull-fc` and `/push-fc`

## Installation

```bash
npx create-fat-controller
```

The installer asks if you're setting up a **new** or **existing** project, copies all files, and guides you to the next steps.

| Scenario | Guide |
|----------|-------|
| **New project** (empty or minimal code) | `@INSTALL-NEW.md` - Asks questions, populates `.ai/` |
| **Existing project** (has code already) | `@INSTALL-EXISTING.md` - Explores codebase, extracts knowledge |

### Quick Start

```bash
cd your-project
npx create-fat-controller     # Install
# Follow installer prompts, then open Claude Code:
@INSTALL-NEW.md               # or @INSTALL-EXISTING.md
```

### Manual Installation

```bash
git clone https://github.com/iainforrest/fat-controller.git
cp -r fat-controller/.claude your-project/
cp -r fat-controller/templates your-project/
cp fat-controller/INSTALL-*.md your-project/
cp fat-controller/orchestrator.py your-project/
```

## Two Ways to Work

### Standard Flow (Interactive)

You drive each step manually inside Claude Code:

```
/prd [feature idea]     -> Generate requirements document
/TaskGen [prd-file]     -> Break PRD into implementation tasks
/execute [tasks-file]   -> Execute tasks via agent orchestration
/commit                 -> Intelligent grouped git commits
/update                 -> Update .ai/ memory from git diffs
```

### Autonomous Flow (Hands-off)

Define outcomes, then let the orchestrator deliver them:

```
/outcomes               -> Define what the project should deliver
/orchestrate            -> Launch autonomous orchestrator in background
```

The orchestrator runs in a tmux session, surviving Claude Code context exhaustion. It cycles autonomously:

```
PM plans sprints -> PL executes them -> PM reviews results -> repeat
```

Monitor with `tmux attach -t orchestrator` or `tail -f tasks/orchestrator.log`.

For autonomous mode, we strongly recommend running `/values-discovery` first -- it ensures agents make decisions you'd recognise as your own. Without it, agents operate with generic professional judgment.

## Commands Reference

### Core Workflow

| Command | Purpose | Output |
|---------|---------|--------|
| `/prd` | Generate requirements from feature idea | `tasks/[name]/prd.md` |
| `/TaskGen` | Convert PRD to implementation tasks | `tasks/[name]/task.xml` |
| `/execute` | Orchestrate task execution via agents | Implemented code + commits |
| `/commit` | Group and commit changes intelligently | Git commits + push |
| `/update` | Update memory system from git diffs | Updated `.ai/` files |

### Autonomous Orchestration

| Command | Purpose | Output |
|---------|---------|--------|
| `/outcomes` | Interactive project outcome discovery | `tasks/OUTCOMES.md` + state files |
| `/orchestrate` | Launch autonomous orchestrator in background | tmux session running `orchestrator.py` |
| `/lead` | Interactive orchestration within current session | Sprint-by-sprint guidance |

### Analysis & Quality

| Command | Purpose | Output |
|---------|---------|--------|
| `/code-review` | Dual-model review (Claude + Codex) | Findings with severity + auto-fix |
| `/debate` | Multi-model analysis of any topic | Structured debate with synthesis |
| `/bugs` | Explore bugs, analyse root causes | Fix options with downstream effects |
| `/investigate` | Deep investigation of an issue | Research findings |
| `/feature` | Research, design, and implement small features | Working code |

### Values & Personalisation

| Command | Purpose | Output |
|---------|---------|--------|
| `/values-discovery` | Create personal values profile | `~/.claude/VALUES.md` |
| `/domain-values` | Create domain-specific values | `~/.claude/domains/*.md` |

### Sync

| Command | Purpose |
|---------|---------|
| `/pull-fc` | Pull latest commands/agents from fat-controller |
| `/push-fc` | Push improvements back as PR |

## Agents

Agents provide domain expertise and are invoked automatically by commands:

| Agent | Expertise |
|-------|-----------|
| `pm` | Sprint planning, PRD generation, roadmap management |
| `pl` | Sprint execution via TaskGen and Execute |
| `cto` | Architecture decisions, technical judgment (values-driven) |
| `task-protocol` | Execution protocol for Codex/Claude — subtask handling, commits, verification |
| `code-review-agent` | Dual-model code quality review |
| `research-agent` | Deep research with plan/execute/synthesize phases |
| `cto-technical-advisor` | Architecture decisions, feasibility assessment |
| `security-auditor` | Security reviews, vulnerability detection |
| `ui-ux-expert` | Interface design, accessibility, user flows |
| `prd-writer` | Requirements documentation |
| `task-writer` | Task breakdown in XML format with complexity ratings |
| `update-memory-agent` | Git diff analysis, memory updates |

## Architecture

```
.claude/                    # Generic (syncs across projects)
├── commands/               # Workflow commands (/prd, /execute, /orchestrate, etc.)
├── agents/                 # AI agents (PM, PL, CTO, execution, review, etc.)
├── skills/                 # Domain-specific skills (frontend, backend, security, etc.)
└── WORKFLOW.md             # Command/agent documentation

.ai/                        # Project-specific (never syncs)
├── ARCHITECTURE.json       # Patterns, data flows, integration points
├── BUSINESS.json           # Features, requirements, performance targets
├── FILES.json              # File index with dependencies and cross-refs
├── PATTERNS.md             # Implementation patterns and templates
├── QUICK.md                # Build commands, debugging tips, routing
├── OPS.md                  # Operational runbooks
├── CHANGELOG.md            # Auto-generated changelog
└── ...                     # TECH_DEBT.md, CONSTRAINTS.md, decisions/, solutions/

templates/                  # Starter templates
├── .ai/                    # Clean memory system templates
├── tasks/                  # Task directory structure
└── ROADMAP.md              # Sprint state tracking template

orchestrator.py             # Autonomous PM-PL cycle orchestrator (Python 3, stdlib only)
```

**Key insight**: Commands and agents are fully generic -- they read from `.ai/` for project-specific context. Updates sync without customisation. Project knowledge lives in one place.

## Memory System (`.ai/`)

The memory system is your project's brain. Populated during installation, it grows with your project.

| File | Purpose |
|------|---------|
| `ARCHITECTURE.json` | Patterns, data flows, integration points |
| `BUSINESS.json` | Features, requirements, performance targets |
| `FILES.json` | File index with dependencies and cross-refs |
| `PATTERNS.md` | Implementation templates and examples |
| `QUICK.md` | Build commands, routing to other memory files |
| `OPS.md` | Operational runbooks and debugging guides |
| `TECH_DEBT.md` | Tracked tech debt with source attribution |
| `CHANGELOG.md` | Auto-generated from git diffs |

Each file has one authority -- no duplication. The `/update` command routes changes to the right file automatically.

## Key Features

### Wave-Based Parallel Execution

The `/execute` command runs non-conflicting tasks in parallel:

```
Wave 1 (parallel):  [Task 1: frontend]  [Task 2: backend]  [Task 3: infra]
Wave 2 (sequential):              [Task 4: touches frontend + backend]
```

Tasks are grouped by file conflicts. Each parallel agent gets fresh context and writes to its own STATE file. Failed tasks retry with a stronger model.

### Domain Skills

Agents dynamically load domain-specific skills based on file patterns:

| Skill | Triggers On | Focus |
|-------|-------------|-------|
| `frontend` | `*.tsx`, `*/components/*` | React patterns, accessibility |
| `backend` | `*/api/*`, `*/services/*` | Service layers, API design |
| `data` | `*/models/*`, `*.sql` | Query optimisation, transactions |
| `security` | `*/auth/*`, `*security*` | OWASP, auth flows, secrets |
| `infrastructure` | `Dockerfile`, `*.tf` | Container patterns, CI/CD |
| `mobile` | `*.swift`, `*.kt`, `*.dart` | Platform lifecycle, offline-first |

### Dual-Model Code Review

`/code-review` runs Claude and Codex in parallel, merges findings, and deduplicates:

- **Convergent findings** (both models agree): high confidence
- **Single-model findings**: flagged with source
- Auto-fix for CRITICAL/HIGH issues
- User triage for MEDIUM/LOW (fix now, tech debt, or skip)

### Values-Driven Agents

Agents load `~/.claude/VALUES.md` at boot for personalised decision-making. Without values, they operate in generic mode with conservative defaults. Values are recommended but never required -- no hard gates.

### XML Task Format

Tasks are generated in XML with complexity ratings, file references, and verification commands:

```xml
<parent_task id="1.0" complexity="3" status="pending">
  <title>Implement Login Service</title>
  <verify>npm test -- --grep auth</verify>
  <subtasks>...</subtasks>
</parent_task>
```

Status tracking (`pending` -> `in_progress` -> `completed`) enables stopping and resuming execution.

## Keeping in Sync

```
/pull-fc    # Pull latest commands/agents from fat-controller
/push-fc    # Push improvements back as PR
```

| Syncs | Never Syncs |
|-------|-------------|
| `.claude/commands/*.md` | `.ai/*` (project-specific) |
| `.claude/agents/*.md` | `.claude/settings.local.json` |
| `.claude/skills/*.md` | `templates/.ai/*` (distribution-only) |
| `orchestrator.py` | |
| `templates/ROADMAP.md` | |

## Credits

This project builds on ideas from the Claude Code community:

- [Ryan Carson's AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks) - The original PRD and task-based execution approach
- [How to AI with Claire Vo](https://youtu.be/fD4ktSkNCw4) - Where the workflow was first discovered
- [GSD (Get Shit Done)](https://github.com/glittercowboy/get-shit-done) by TACHES - Pioneered the subagent execution model with fresh context windows per task

---

**Ready to start?**
- New project: `npx create-fat-controller` then `@INSTALL-NEW.md`
- Existing project: `npx create-fat-controller` then `@INSTALL-EXISTING.md`
