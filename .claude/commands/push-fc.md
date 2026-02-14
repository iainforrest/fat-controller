---
description: Push command/agent improvements back to fat-controller as a PR
---

# Push Improvements to Fat Controller

Push improved commands or agents back to The Fat Controller repository as a pull request.

## Key Principle

**Commands and agents should already be generic** - they should reference `.ai/` memory files for project-specific context rather than hardcoding values. This command validates that principle before pushing.

## What Can Be Pushed

| Can Push | Cannot Push |
|----------|-------------|
| `.claude/commands/*.md` | `.ai/*` (project-specific) |
| `.claude/agents/*.md` | `.claude/settings.local.json` |
| `.claude/skills/*.md` | Project-specific commands |
| `.claude/WORKFLOW.md` | |
| `orchestrator.py` | |
| `templates/ROADMAP.md` | |

## Steps

### 1. Ask what to push

Ask the user: "What improvements do you want to push back to the starter?"

Examples:
- "the updated /prd command"
- "the new review-memory command"
- "changes to execute.md and task-writer agent"

### 2. Read and validate files

For each file the user wants to push, read it and scan for project-specific content.

**Red Flags (BLOCK the push):**
- Project names (MyVoi, CoachOps, RealNZ, etc.)
- Absolute paths (`/root/projects/...`, `/Users/...`, `C:\...`)
- Service account emails or API keys
- Hardcoded commands (should say "from QUICK.md" not `./gradlew build`)
- Specific URLs (firebase project URLs, production domains)
- Company or personal names

**Acceptable content:**
- References to `.ai/` files (ARCHITECTURE.json, BUSINESS.json, etc.)
- Placeholders like `[BUILD_COMMAND]`, `[PROJECT_NAME]`
- Generic examples in code blocks (e.g., `npm test` as an illustration)
- Pattern descriptions without specific implementations

### 3. Report validation results

If clean:
```
✅ Files are generic and ready to push:
- commands/prd.md
- agents/task-writer.md
```

If issues found:
```
❌ Found project-specific content:

commands/feature.md:32
  "MyVoi - Android voice-to-text application"
  → Should reference: "Load project context from .ai/BUSINESS.json"

commands/feature.md:38
  "/root/projects/MyVoi/services/functions/"
  → Should remove or use relative paths

Fix these issues before pushing, or confirm you want to proceed anyway.
```

### 4. Confirm before proceeding

If issues were found, ask:
- "Fix issues first?" (recommended)
- "Push anyway?" (user takes responsibility)
- "Cancel"

If clean, ask:
- "Ready to create PR?"

### 5. Clone and create branch

```bash
TEMP_DIR=$(mktemp -d)
git clone https://github.com/iainforrest/fat-controller.git "$TEMP_DIR"
cd "$TEMP_DIR"

BRANCH_NAME="update/[descriptive-name]"
git checkout -b "$BRANCH_NAME"
```

### 6. Copy files

Copy the validated files from this project to the temp clone.

### 7. Commit and push

```bash
cd "$TEMP_DIR"
git add .
git commit -m "feat: [Description of improvement]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push -u origin "$BRANCH_NAME"
```

### 8. Create PR

```bash
cd "$TEMP_DIR"
gh pr create \
  --repo iainforrest/fat-controller \
  --title "feat: [Title]" \
  --body "## Summary

[Brief description]

## Files Changed

- [List files]

## Validation

- [x] No project-specific names
- [x] No hardcoded paths
- [x] References .ai/ for project context
- [x] Tested in source project

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

### 9. Cleanup and report

```bash
rm -rf "$TEMP_DIR"
```

Provide the PR URL to the user.

---

**Execute this workflow now.** Start by asking what the user wants to push.
