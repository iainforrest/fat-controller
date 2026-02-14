---
description: Pull latest commands and agents from fat-controller
---

# Pull Fat Controller Updates

Pull the latest generic commands and agents from The Fat Controller repository.

## Key Principle

**Commands and agents are fully generic** - they reference `.ai/` memory files for project-specific context. No customization or templating is needed when pulling updates.

## What Gets Synced

| Syncs | Never Syncs |
|-------|-------------|
| `.claude/commands/*.md` | `.ai/*` (project-specific memory) |
| `.claude/agents/*.md` | `.claude/settings.local.json` (machine-specific) |
| `.claude/skills/*.md` | |
| `.claude/WORKFLOW.md` | |
| `templates/.ai/*` (clean starter templates) | |
| `templates/tasks/.gitkeep` | |
| `orchestrator.py` (autonomous orchestrator) | |
| `templates/ROADMAP.md` (sprint state template) | |

## Steps

### 0. Migration Check (IMPORTANT)

**Before doing anything else**, check for and remove legacy sync commands:

```bash
# Remove old sync commands if they exist
rm -f .claude/commands/pull-cps.md .claude/commands/push-cps.md
```

If these files existed, inform the user:
```
Migrated: Removed legacy pull-cps.md and push-cps.md (replaced by pull-fc.md and push-fc.md)
```

### 1. Clone starter repo

```bash
TEMP_DIR=$(mktemp -d)
git clone --depth 1 https://github.com/iainforrest/fat-controller.git "$TEMP_DIR"
echo "Cloned to $TEMP_DIR"
```

### 1.5. Self-Update Check (CRITICAL)

Before comparing all files, check if `pull-fc.md` itself has changed:

```bash
diff -q "$TEMP_DIR/.claude/commands/pull-fc.md" ".claude/commands/pull-fc.md"
```

**If pull-fc.md differs:**

1. Show the user: "pull-fc.md itself has been updated. Applying self-update first so the latest sync rules are used."
2. Copy ONLY the new pull-fc.md into place:
   ```bash
   cp "$TEMP_DIR/.claude/commands/pull-fc.md" ".claude/commands/pull-fc.md"
   ```
3. Clean up the temp directory:
   ```bash
   rm -rf "$TEMP_DIR"
   ```
4. Tell the user: "pull-fc has been updated. Re-running with new sync rules..."
5. Re-invoke `/pull-fc` using the Skill tool: `Skill(skill="pull-fc")`
6. **STOP here** — do NOT continue to Step 2. The re-invoked command will handle everything with the updated sync list.

**If pull-fc.md is unchanged:** Continue to Step 2.

### 2. Compare files

Compare these directories and files:
- `.claude/commands/` (all files including pull-fc.md and push-fc.md)
- `.claude/agents/`
- `.claude/skills/`
- `.claude/WORKFLOW.md` (if exists)
- `templates/.ai/` (all template files and subdirectories)
- `templates/tasks/.gitkeep`
- `orchestrator.py` (project root)
- `templates/ROADMAP.md`

For each file, determine:
- **New**: Exists in starter but not locally
- **Updated**: Exists in both, content differs
- **Same**: No changes needed

Use `diff` to show what changed in updated files.

### 3. Present changes

Show the user:
```
Files to update:
- commands/prd.md (updated - 15 lines changed)
- commands/execute.md (updated - 8 lines changed)
- agents/new-agent.md (new)

Files unchanged:
- commands/commit.md
- commands/update.md
```

For updated files, show the diff.

### 4. Confirm

Ask the user:
- "Apply all changes?"
- "Apply selectively?" (then confirm each file)
- "Cancel"

### 5. Apply changes

Copy approved files from temp directory:
- `.claude/` files to this project's `.claude/` directory
- `templates/` files to this project's `templates/` directory (create if needed)
- `orchestrator.py` to this project's root directory
- `templates/ROADMAP.md` to this project's `templates/` directory

### 6. Cleanup

```bash
rm -rf "$TEMP_DIR"
```

### 7. Report

```
Updated:
- commands/prd.md
- commands/execute.md

Added:
- agents/new-agent.md

Your commands and agents are now in sync with fat-controller.
```

---

**Execute this workflow now.**
