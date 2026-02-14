# AI Memory System Guide

## What This Is

The `.ai/` folder is your project's **persistent memory system** for AI-assisted development. It prevents context loss between Claude sessions by storing structured knowledge about your project.

## Core Philosophy

**Context Efficiency**: Load only what you need, when you need it.

This system is designed to:
- Keep total memory under ~3,000 lines for single-app projects
- Allow selective loading based on task type
- Scale gracefully to mono-repos when needed
- Provide instant access without re-analyzing the codebase

## CLAUDE.md vs .ai/ Integration

**CLAUDE.md** and the `.ai/` folder serve different purposes:

| File | Purpose | Target Size |
|------|---------|-------------|
| `CLAUDE.md` | Project identity + memory router | 50-80 lines |
| `.ai/` folder | Authoritative project knowledge | ~3,000 lines |

**CLAUDE.md should contain ONLY:**
- Project identity (1-2 sentences)
- Tech stack one-liner
- Memory system pointer table (routes to .ai/ files)
- Slash commands reference
- Universal rules (2-3 max, only if they affect every task)

**CLAUDE.md should NOT contain:**
- Build/test/deploy commands (use OPS.md)
- Architecture details (use ARCHITECTURE.json)
- Code patterns (use PATTERNS.md)
- Constraints/limitations (use CONSTRAINTS.md)
- File locations (use FILES.json)

**Why this matters:**
- CLAUDE.md is read on every Claude Code session
- Lean CLAUDE.md = faster startup, less noise
- Content in .ai/ files is updated by `/update` command
- Content in CLAUDE.md requires manual maintenance

**Migration:** If your CLAUDE.md exceeds 100 lines, see `.ai/solutions/claude-md-migration.yaml` for a step-by-step guide to slim it down.

**Health Check:** The `/update` command includes a CLAUDE.md health check that warns about bloat and duplication.

## Quick Navigation

| Working On | Files to Load | Est. Tokens |
|------------|---------------|-------------|
| **Quick lookup** | QUICK.md | ~1,000-2,000 |
| **New feature** | QUICK.md + ARCHITECTURE.json + PATTERNS.md | ~4,000-6,000 |
| **Bug fix** | QUICK.md + FILES.json + solutions/ | ~3,000-5,000 |
| **Business logic** | BUSINESS.json + ARCHITECTURE.json | ~5,000-8,000 |
| **Operations** | QUICK.md + OPS.md | ~2,000-4,000 |
| **Architecture decision** | decisions/ + ARCHITECTURE.json | ~3,000-6,000 |
| **Full context** | All core files | ~20,000-30,000 |

**Rule**: Always start with QUICK.md - it routes you to authoritative sources.

---

## Authority Matrix

**Core Principle**: Each piece of knowledge has ONE authoritative home. No duplication across files.

Refer to QUICK.md for the authority map and content routing.

**Navigation**: Use QUICK.md as your router to find where specific content lives.

**Anti-Pattern**: Never duplicate content across files. If you're tempted to copy information, add a reference instead.

---

## The Files

### QUICK.md (Start Here)
**Purpose**: Navigation hub pointing to authoritative sources.

Load first for: Any task. Routes you to the right file for commands, patterns, or knowledge.

### ARCHITECTURE.json
**Purpose**: Architectural patterns, data flows, component relationships.

Load for: Understanding system structure, planning new features, integration work.

### BUSINESS.json
**Purpose**: Business rules, feature specs, user flows, performance targets.

Load for: Understanding requirements, business logic, data models.

### FILES.json
**Purpose**: Smart file index organized by purpose and layer.

Load for: Finding files, understanding dependencies, navigation.

### PATTERNS.md (Index)
**Purpose**: Lightweight index pointing to domain-specific pattern files.

Load for: Finding implementation templates. Then load specific `patterns/[DOMAIN].md` file.

### patterns/ folder
**Purpose**: Domain-specific implementation patterns and copy-paste templates.

Structure: Create files like `patterns/WEB.md`, `patterns/API.md`, `patterns/DATABASE.md` as your project grows.

### templates/ folder
**Purpose**: Clean starter templates for bootstrapping new projects.

Load for: Project setup. Contains pristine .ai/ starter files and task directory structure.

### TODO.md
**Purpose**: Current sprint tasks and completed work.

Load for: Understanding current priorities and recent history.

### SPRINT_UPDATE.md
**Purpose**: Process guide for updating the memory system.

Load for: End-of-sprint maintenance procedures.

### OPS.md
**Purpose**: Runbooks, debug commands, deploy procedures, incident response.

Load for: Running, debugging, deploying, or responding to operational issues.

### CONSTRAINTS.md
**Purpose**: Platform limitations, non-goals, technical boundaries.

Load for: Understanding what we can't or won't do. Prevents wasted effort.

### DEPRECATIONS.md
**Purpose**: Deprecated APIs, patterns, and experimental features.

Load for: Migration paths and stability expectations.

### TECH_DEBT.md
**Purpose**: Known unfixed issues from code reviews (MEDIUM/LOW severity).

Load for: Understanding deferred issues and refactoring opportunities.

### decisions/ folder
**Purpose**: Architecture Decision Records (ADRs) documenting key decisions.

Load for: Understanding why architectural choices were made.

### solutions/ folder
**Purpose**: YAML-captured solutions to past problems (grep-friendly).

Load for: Finding how similar problems were solved previously.

---

## Token Budget Guidelines

### Single-App Project (Target: ~4,000 lines total)

```
File              Lines       Tokens (approx)
─────────────────────────────────────────────
QUICK.md          50-150      500-1,500 (router)
ARCHITECTURE.json 200-500     2,000-5,000
BUSINESS.json     300-800     3,000-8,000
FILES.json        200-600     2,000-6,000
PATTERNS.md       ~200        ~1,000 (index only)
patterns/[DOMAIN] ~400 each   ~2,500 each
TODO.md           50-200      500-2,000
SPRINT_UPDATE.md  ~200        ~1,000 (static)
OPS.md            200-400     2,000-4,000
CONSTRAINTS.md    100-300     1,000-3,000
DEPRECATIONS.md   100-300     1,000-3,000
TECH_DEBT.md      100-400     1,000-4,000
decisions/*.md    ~100 each   ~1,000 each
solutions/*.yaml  ~50 each    ~500 each
─────────────────────────────────────────────
TOTAL TARGET      ~4,000      ~20,000-30,000
```

### Typical Task Load

Most tasks need only 2-3 files (~3,000-6,000 tokens), not the full system.

---

## Usage Workflow

### Before Any Feature

1. **Read QUICK.md** - Get oriented (30 seconds)
2. **Read relevant memory** - Based on task type (see navigation table)
3. **Implement** - Using knowledge from memory
4. **Update memory** - Add what you learned

### When to Update

| Trigger | Action |
|---------|--------|
| New file created | Add to FILES.json |
| New pattern discovered | Add to patterns/ folder, update PATTERNS.md index |
| Sprint complete | Follow SPRINT_UPDATE.md process |
| Bug fixed with solution | Add to solutions/ directory (YAML) |
| Architecture decision | Create ADR in decisions/ directory |
| Architecture change | Update ARCHITECTURE.json |
| New limitation found | Add to CONSTRAINTS.md |
| Code review finds deferred issue | Add MEDIUM/LOW findings to TECH_DEBT.md |
| API/pattern deprecated | Add to DEPRECATIONS.md with migration path |
| New operational runbook | Add to OPS.md |

---

## Critical Rules

1. **No separate sprint files** - Integrate learnings into core files
2. **Keep it under 3,000 lines** - Split into domains or apps if exceeding
3. **Use stable references** - Descriptive names, globs, purposes (not line numbers)
4. **JSON for structured data** - Machine-parseable, greppable
5. **Markdown for patterns** - Human-readable, copy-paste ready
6. **One authority per topic** - No duplication; use QUICK.md to route

---

## Scaling to Mono-Repo

When your project grows to multiple apps or exceeds 3,000 lines:

See **MONOREPO_GUIDE.md** for:
- When to upgrade
- How to create app-specific memory folders
- MONOREPO.json template
- Context loading strategies for multi-app projects

---

## File Structure

**For detailed file listings:** See FILES.json for authoritative file paths and organization.

**For mono-repo structure guidance:** See MONOREPO_GUIDE.md for when and how to scale the memory system for multi-app projects.

---

## Common Mistakes

| Mistake | Instead Do |
|---------|------------|
| Creating SPRINT_X.md files | Update core files with sprint learnings |
| Loading all files for every task | Use navigation table, load selectively |
| Letting memory exceed 4,000 lines | Split into domains or app-specific folders |
| Skipping memory before features | Always start with QUICK.md to route |
| Not updating after sprints | Follow SPRINT_UPDATE.md process |
| Duplicating content across files | Use authority matrix - one home per topic |
| Using line numbers as references | Use stable names, globs, descriptive purposes |
| Fixing all tech debt immediately | Defer MEDIUM/LOW to TECH_DEBT.md with context |

---

## Getting Started

1. **Review QUICK.md** - Understand current project state
2. **Customize templates** - Replace placeholders with real data
3. **Use memory immediately** - Reference before implementing
4. **Update as you work** - Memory grows with your project
5. **Run /update** - Use the update command after significant work

---

*The memory system is your project's brain. Keep it lean, keep it current.*
