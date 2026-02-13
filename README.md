# The Fat Controller v3.0 🚂

*"Really useful engines, every one."*

A complete AI-assisted development system that orchestrates Claude Code agents to build software. Like having an entire engineering team in your terminal.

> Named after Sir Topham Hatt from Thomas the Tank Engine - the one who keeps all the engines running on time. That's what this does for your AI agents.

## What This Is

- **Generic Commands & Agents**: Reusable workflow tools that work across any project
- **AI Memory System**: Persistent project knowledge in `.ai/` that prevents context loss
- **Sync System**: Keep your projects up-to-date with `/pull-fc` and `/push-fc`

## Installation

### One-Command Install (Recommended)

Install into any project with a single command:

```bash
npx create-fat-controller
```

The installer will:
1. Ask if you're setting up a **new** or **existing** project
2. Copy all necessary files (`.claude/`, `.ai/`, installers)
3. Guide you to the next steps

### Choose Your Path

| Scenario | Installer Will Guide You To |
|----------|------------------------------|
| **New project** (empty or minimal code) | `@INSTALL-NEW.md` - Asks questions, populates `.ai/` from your answers |
| **Existing project** (has code already) | `@INSTALL-EXISTING.md` - Explores your codebase, extracts knowledge into `.ai/` |

### Quick Start

1. **Run the installer** in your project directory:
   ```bash
   cd your-project
   npx create-fat-controller
   ```

2. **Follow the installer prompts** (new vs existing)

3. **Open Claude Code** and run the appropriate installer:
   - For new projects: `@INSTALL-NEW.md`
   - For existing projects: `@INSTALL-EXISTING.md`

4. **Start building**:
   ```
   /prd → /TaskGen → /execute → /commit → /update
   ```

### Manual Installation (Alternative)

If you prefer to install manually:

```bash
git clone https://github.com/iainforrest/fat-controller.git
cp -r fat-controller/.claude your-project/
cp -r fat-controller/.ai your-project/
cp fat-controller/INSTALL-*.md your-project/
```

Then run the appropriate installer with Claude Code.

## Key Architecture (v3.0)

```
.claude/                    # Generic (syncs across projects)
├── commands/               # Workflow commands (/prd, /TaskGen, /execute, etc.)
├── agents/                 # Specialized AI agents (CTO, Security, UI/UX, etc.)
├── skills/                 # Domain-specific skills loaded by agents
└── WORKFLOW.md             # Command/agent documentation

.ai/                        # Project-specific (never syncs)
├── ARCHITECTURE.json       # Your project's patterns and data flows
├── BUSINESS.json           # Your features and requirements
├── FILES.json              # Your file index with cross-references
├── PATTERNS.md             # Your implementation patterns
├── QUICK.md                # Your build commands and shortcuts
└── ...                     # Other memory files
```

**The key insight**: Commands and agents are fully generic - they read from `.ai/` for all project-specific context. This means:
- Commands work identically across all projects
- Updates can be synced without customization
- Project knowledge lives in one place (`.ai/`)

## Development Workflow

### The Command Flow

```
/prd [feature idea]     → Generate Product Requirements Document
/TaskGen [prd-file]     → Break PRD into implementation tasks
/execute [tasks-file]   → Systematically execute tasks
/commit                 → Intelligent grouped git commits
/update                 → Update .ai/ memory from git diffs
```

### Sync Commands

```
/pull-fc               → Pull latest commands/agents from this repo
/push-fc               → Push improvements back as PR
```

## Autonomous Orchestrator

Fat-controller works out of the box with the command flow above. The autonomous orchestrator takes it further -- it runs the full plan-execute-commit cycle without manual intervention.

For the autonomous orchestrator, we strongly recommend running `/values-discovery` first. It ensures the autonomous agents make decisions you'd recognise as your own.

### Two Tiers

**Standard flow** (works without values):
```
Install → Project bootstrap → /prd → /TaskGen → /execute → /commit
```

**Autonomous flow** (strongly recommended with values):
```
Install → /values-discovery → Project bootstrap → python3 orchestrator.py .
```

The autonomous orchestrator reads your `tasks/OUTCOMES.md`, plans sprints via a PM agent, executes them via a PL agent, and loops until all outcomes are delivered. Values-discovery is optional but strongly recommended -- without it, agents operate with generic professional judgment instead of your personal principles.

### Key Components

| Component | Purpose |
|-----------|---------|
| `orchestrator.py` | Python loop that drives PM/PL cycles |
| `.claude/agents/pm.md` | Plans sprints, writes PRDs, manages the roadmap |
| `.claude/agents/pl.md` | Executes sprints via TaskGen and Execute |
| `tasks/ROADMAP.md` | Sprint state tracking (created automatically) |
| `/values-discovery` | Optional: creates `~/.claude/VALUES.md` for values-driven agents |

---

## Commands Reference

| Command | Purpose | Output |
|---------|---------|--------|
| `/prd` | Generate requirements from feature idea | `/tasks/prd-[name].md` |
| `/TaskGen` | Convert PRD to implementation tasks | `/tasks/task-[name].xml` |
| `/execute` | Orchestrate task execution via agents | Implemented code + commits |
| `/commit` | Group and commit changes intelligently | Git commits |
| `/update` | Update memory system from git diffs | Updated `.ai/` files |
| `/pull-fc` | Sync latest from starter repo | Updated commands/agents |
| `/push-fc` | Contribute improvements back | GitHub PR |

## Specialized Agents

Agents provide domain expertise and are invoked automatically or on request:

| Agent | Expertise |
|-------|-----------|
| `execution-agent` | Fresh-context task execution with domain skill loading |
| `code-review-agent` | Code quality review with domain-specific checks |
| `research-agent` | Deep research with plan/execute/synthesize phases |
| `cto-technical-advisor` | Architecture decisions, feasibility assessment |
| `security-auditor` | Security reviews, vulnerability detection |
| `ui-ux-expert` | Interface design, accessibility, user flows |
| `prd-writer` | Requirements documentation |
| `task-writer` | Task breakdown in XML format with complexity ratings |
| `update-memory-agent` | Git diff analysis, memory updates |

## Memory System (`.ai/`)

The memory system is your project's brain. It's populated during installation and grows with your project.

| File | Purpose |
|------|---------|
| `ARCHITECTURE.json` | Patterns, data flows, integration points |
| `BUSINESS.json` | Features, requirements, performance targets |
| `FILES.json` | File index with dependencies and cross-refs |
| `PATTERNS.md` | Implementation templates and examples |
| `QUICK.md` | Build commands, debugging tips, shortcuts |
| `TODO.md` | Current and completed tasks |
| `SPRINT_UPDATE.md` | Process for updating memory |
| `README.md` | Guide to the memory system |

**Key rule**: Commands reference `.ai/` for context. Keep it updated with `/update`.

## Keeping in Sync

### Pull Updates

When new commands or agents are added to this repo:

```
/pull-fc
```

This compares your `.claude/` with the latest, shows diffs, and lets you selectively update.

### Push Improvements

When you improve a command or agent:

```
/push-fc
```

This validates your changes are generic (no project-specific content), then creates a PR.

### What Syncs vs What Doesn't

| Syncs | Never Syncs |
|-------|-------------|
| `.claude/commands/*.md` | `.ai/*` (project-specific) |
| `.claude/agents/*.md` | `.claude/settings.local.json` |
| `.claude/skills/*.md` | Project-specific commands |
| `.claude/WORKFLOW.md` | |

## What's New in v2.3 - Parallel Task Execution

### Wave-Based Parallelism

The `/execute` command now runs non-conflicting tasks in parallel, dramatically reducing execution time for features with independent components:

```
Wave 1 (parallel):  [Task 1: frontend]  [Task 2: backend]  [Task 3: infra]
                            ↓                   ↓                ↓
                         commit              commit           commit
                            └───────────────────┴────────────────┘
                                         merge STATE
                                              ↓
Wave 2 (sequential):              [Task 4: touches frontend + backend]
```

### Conflict Detection

Tasks are grouped into waves based on file dependencies:

| Conflict Type | Example | Result |
|---------------|---------|--------|
| **File-level** | Both tasks modify `auth.ts` | Run in separate waves |
| **Import-level** | Task B imports file Task A modifies | Run in separate waves |
| **No conflict** | Frontend vs Backend files | Run in parallel |

### Per-Agent STATE Files

Each parallel agent writes learnings to its own STATE file:
```
/tasks/STATE-feature-agent-1.0.md  # Agent 1
/tasks/STATE-feature-agent-2.0.md  # Agent 2
/tasks/STATE-feature-agent-3.0.md  # Agent 3
```

After wave completes, orchestrator merges into main `STATE-feature.md`.

### Failure Handling

- Other tasks in wave continue if one fails
- Failed task retried once with bumped model (Sonnet → Opus)
- User must explicitly approve skipping a failed task
- Next wave only starts after current wave fully passes

### Progress Display

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌊 Wave 1: 3 tasks executing in parallel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ⏳ [1.0] Create Frontend Component (sonnet, frontend)
   ⏳ [2.0] Create API Endpoint (sonnet, backend)
   ⏳ [3.0] Setup Infrastructure (opus, infrastructure)

   ✅ [1.0] Create Frontend Component - commit abc123
   ✅ [2.0] Create API Endpoint - commit def456
   ✅ [3.0] Setup Infrastructure - commit ghi789

Wave 1 complete: 3/3 tasks
```

---

## What's New in v2.2 - Specialized Agent Architecture

### Domain Skills System

Agents now dynamically load **domain-specific skills** based on the files being modified. This provides specialized guidance without bloating agent context:

```
Base Agent  ×  Domain Skill  =  Specialized Behavior
───────────────────────────────────────────────────
execution   ×  frontend      =  React patterns, a11y checks
execution   ×  backend       =  Service layers, API design
code-review ×  security      =  OWASP checks, crypto review
research    ×  data          =  Query optimization research
```

**Available Domain Skills:**

| Skill | File Patterns | Focus Areas |
|-------|---------------|-------------|
| `frontend` | `*.tsx`, `*/components/*`, `*/hooks/*` | React/Vue patterns, state management, accessibility |
| `backend` | `*/api/*`, `*/services/*`, `*/routes/*` | Service layers, REST design, error handling |
| `data` | `*/repositories/*`, `*.sql`, `*/models/*` | Query optimization, N+1 prevention, transactions |
| `mobile` | `*/ios/*`, `*/android/*`, `*.swift`, `*.kt` | Platform patterns, lifecycle, offline-first |
| `security` | `*/auth/*`, `*/crypto/*`, `*security*` | OWASP Top 10, auth flows, secrets management |
| `infrastructure` | `Dockerfile`, `*.yaml`, `*/terraform/*` | Container patterns, IaC, CI/CD pipelines |
| `general` | (fallback) | Senior dev best practices, code quality |

### Domain Detection

The orchestrator automatically detects domains from file paths in each task:

```xml
<!-- Auto-detected from files -->
<parent_task id="1.0" complexity="3" status="pending">
  <files>src/components/Button.tsx</files>  <!-- → frontend skill -->
  ...
</parent_task>

<!-- Explicit override when needed -->
<parent_task id="2.0" complexity="4" status="pending" domain="security">
  <files>src/services/auth.ts</files>  <!-- Override: use security skill -->
  ...
</parent_task>
```

### New & Refactored Agents

| Agent | Change |
|-------|--------|
| `execution-agent` | **Refactored**: Now accepts and applies domain skills |
| `code-review-agent` | **Refactored**: Domain-specific review checks |
| `research-agent` | **New**: Plan → Execute → Synthesize research workflow |

### New Files

| File | Purpose |
|------|---------|
| `.claude/skills/domain-*.md` | 7 domain skill files (~2KB each) |

---

## What's New in v2.1 - Integrated Execution Architecture

### Orchestrator Pattern

The `/execute` command has been refactored from a monolithic executor to a **lightweight orchestrator** that spawns fresh-context execution agents per parent task:

```
/execute task-feature-name
    │
    ├── Parses XML task file
    ├── Initializes STATE.md for cross-task learning
    ├── Loads EXPLORE_CONTEXT.json
    │
    └── For each parent task:
        ├── Selects model (Sonnet 1-3, Opus 4-5)
        ├── Spawns execution-agent with fresh context
        ├── Agent executes subtasks → verifies → commits
        ├── Updates STATE.md with learnings
        └── Continues to next task
```

**Benefits:**
- **Eliminates context debt**: Fresh context per parent task
- **Cross-task learning**: STATE.md passes learnings between agents
- **Dynamic model selection**: Complex tasks (4-5) use Opus, others use Sonnet
- **Atomic commits**: One commit per parent task with full traceability
- **Progress tracking**: Status attributes on tasks enable resumability

### XML Task Format (Breaking Change)

Task files are now generated in **XML format** for structured parsing:

```xml
<execution_plan>
  <metadata>
    <feature_name>user-auth</feature_name>
    <total_parent_tasks>5</total_parent_tasks>
  </metadata>
  <parent_task id="1.0" complexity="3" status="pending">
    <title>Implement Login Service</title>
    <verify>npm test</verify>
    <subtasks>
      <subtask id="1.1" status="pending">...</subtask>
    </subtasks>
  </parent_task>
</execution_plan>
```

The `status` attribute tracks progress (`pending` → `in_progress` → `completed`), enabling you to stop and resume execution without losing progress.

**Migration**: Run `/TaskGen prd-{name}` to regenerate existing PRDs in XML format.

### New Files

| File | Purpose |
|------|---------|
| `.claude/agents/execution-agent.md` | Fresh-context agent for executing parent tasks |
| `/tasks/STATE-{feature}.md` | Cross-task learning state file (generated during execution) |
| `.ai/EXPLORE_CONTEXT.json` | Cached exploration context for execution agents |

### Previous Updates (v2.0)

- **Sync System**: `/pull-fc` and `/push-fc` commands for keeping projects updated
- **Cleaner Architecture**: Commands/agents are now fully generic
- **Memory-First Design**: All project context lives in `.ai/`
- **Dual Installation**: Separate paths for new vs existing projects
- **Better Agents**: Enhanced prd-writer and task-writer with structured output

## Project Structure After Installation

```
your-project/
├── .claude/
│   ├── commands/           # Workflow commands
│   │   ├── prd.md
│   │   ├── TaskGen.md
│   │   ├── execute.md
│   │   ├── commit.md
│   │   ├── update.md
│   │   ├── pull-fc.md
│   │   └── push-fc.md
│   ├── agents/             # Specialized agents
│   │   ├── execution-agent.md      # Task executor with skill loading
│   │   ├── code-review-agent.md    # Domain-aware code review
│   │   ├── research-agent.md       # NEW: Deep research workflow
│   │   ├── prd-writer.md
│   │   ├── task-writer.md
│   │   ├── update-memory-agent.md
│   │   ├── cto-technical-advisor.md
│   │   ├── security-auditor.md
│   │   └── ui-ux-expert.md
│   ├── skills/             # Domain-specific skills (NEW)
│   │   ├── domain-general.md
│   │   ├── domain-frontend.md
│   │   ├── domain-backend.md
│   │   ├── domain-data.md
│   │   ├── domain-mobile.md
│   │   ├── domain-security.md
│   │   └── domain-infrastructure.md
│   └── WORKFLOW.md
├── .ai/
│   ├── ARCHITECTURE.json   # Your patterns
│   ├── BUSINESS.json       # Your features
│   ├── FILES.json          # Your files
│   ├── PATTERNS.md         # Your templates
│   ├── QUICK.md            # Your commands
│   └── ...
├── tasks/                  # Generated PRDs and task lists
└── CLAUDE.md               # Project overview (create with `claude init`)
```

## Philosophy

**AI works best with persistent, structured knowledge.**

The memory system prevents Claude from "forgetting" your project between sessions. The generic commands ensure consistent workflows. Together, they enable rapid, high-quality development.

### Key Benefits

- **Zero Context Loss**: Memory system preserves project knowledge
- **Consistent Quality**: Commands enforce best practices
- **Rapid Development**: Templates and patterns enable fast implementation
- **Stay Current**: Sync commands keep all projects updated
- **Contribute Back**: Improvements benefit everyone

## Credits

This project builds on ideas from the Claude Code community:

**PRD → Tasks → Execute workflow:**
- [Ryan Carson's AI Dev Tasks](https://github.com/snarktank/ai-dev-tasks) - The original PRD and task-based execution approach
- [How to AI with Claire Vo - YouTube](https://youtu.be/fD4ktSkNCw4) - Where I first discovered this workflow

**Subagent orchestration and fresh context patterns:**
- [GSD (Get Shit Done)](https://github.com/glittercowboy/get-shit-done) by TÂCHES - Pioneered the subagent execution model with fresh context windows per task. The wave-based parallel execution and "context debt" prevention in The Fat Controller were directly inspired by GSD's approach.

---

**Ready to start?** Choose your installation path:
- New project → `INSTALL-NEW.md`
- Existing project → `INSTALL-EXISTING.md`
