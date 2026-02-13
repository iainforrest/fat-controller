# The Fat Controller - Install into Existing Project

**Purpose:** Set up The Fat Controller development system in a project that already has code. Claude will explore your codebase and populate the `.ai/` memory files automatically.

## How This Differs from New Projects

| New Project | Existing Project |
|-------------|------------------|
| Ask questions, populate from answers | Explore codebase, extract knowledge |
| ~15 minutes of Q&A | Varies by project size |
| User provides all context | Claude discovers context |

## Before You Start

Make sure you've copied the Fat Controller files into your project:
```bash
# From fat-controller repo
cp -r .claude/ /path/to/your-project/
cp -r .ai/ /path/to/your-project/
```

---

## For Claude: Installation Instructions

### Phase 1: Project Assessment

**First, determine project size:**

```bash
# Count files (excluding common non-source directories)
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.java" -o -name "*.kt" -o -name "*.swift" -o -name "*.go" -o -name "*.rs" -o -name "*.rb" -o -name "*.php" -o -name "*.cs" -o -name "*.cpp" -o -name "*.c" -o -name "*.h" \) ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/vendor/*" ! -path "*/build/*" ! -path "*/dist/*" ! -path "*/__pycache__/*" | wc -l

# Get directory structure (top 2 levels)
find . -type d ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/vendor/*" ! -path "*/build/*" ! -path "*/dist/*" -maxdepth 2 | head -50

# Identify primary language
find . -type f ! -path "*/node_modules/*" ! -path "*/.git/*" | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10
```

**Classify the project:**

| Size | File Count | Approach |
|------|------------|----------|
| Small | < 50 files | Single-pass exploration |
| Medium | 50-200 files | Focused exploration |
| Large | 200-500 files | Domain-based exploration |
| Very Large | 500+ files | Agent-assisted exploration |

**Report to user:**
```
Project Assessment:
- Size: [Small/Medium/Large/Very Large]
- Files: ~[X] source files
- Primary Language: [Language]
- Structure: [Monolith/Monorepo/Multi-component]

Recommended approach: [Single-pass/Focused/Domain-based/Agent-assisted]
```

---

### Phase 2: Quick Questions (2-3 only)

**Ask the user:**

1. **In one sentence, what does this project do?**
   - Don't need details - just the core purpose

2. **Are there specific areas you want me to focus on first?**
   - Or should I explore everything equally?

3. **(For Large/Very Large only) Can you name the main domains or modules?**
   - e.g., "auth, api, frontend, database"
   - This helps break down exploration

---

### Phase 3: Exploration Strategy

#### For Small Projects (< 50 files)

**Single-pass exploration:**

1. Read README.md and any docs
2. Read main config files (package.json, build.gradle, Cargo.toml, etc.)
3. Identify entry points (main.ts, index.js, App.tsx, etc.)
4. Read key source files
5. Populate `.ai/` files directly

#### For Medium Projects (50-200 files)

**Focused exploration:**

1. Read README and config files
2. Map the directory structure
3. Identify architectural patterns from structure
4. Read 10-15 key files (entry points, core modules)
5. Populate `.ai/` files

#### For Large Projects (200-500 files)

**Domain-based exploration:**

1. Read README and config files
2. Map directory structure
3. Identify domains/modules
4. For each domain:
   - Read 3-5 representative files
   - Note patterns and dependencies
5. Synthesize findings into `.ai/` files

#### For Very Large Projects (500+ files)

**Agent-assisted exploration:**

Use the Task tool with Explore agents to parallelize:

```
Launch 3-4 Explore agents in parallel:
- Agent 1: "Explore the authentication/user system"
- Agent 2: "Explore the API/backend layer"
- Agent 3: "Explore the frontend/UI layer"
- Agent 4: "Explore the data/database layer"

Each agent reports:
- Key files found
- Patterns observed
- Dependencies identified
- Architecture insights
```

Synthesize agent findings into `.ai/` files.

---

### Phase 4: Key Information to Extract

**From config files:**
- Project name
- Dependencies and versions
- Build commands
- Test commands
- Scripts

**From directory structure:**
- Architecture pattern (layered, feature-based, etc.)
- Module/domain boundaries
- Test organization

**From source code:**
- Primary patterns (repositories, services, controllers, etc.)
- State management approach
- Data flow patterns
- Error handling patterns

**From README/docs:**
- Project purpose
- Setup instructions
- Architecture decisions

---

### Phase 5: Populate `.ai/` Files

#### BUSINESS.json

```json
{
  "meta": {
    "projectName": "[Extracted from package.json/config]",
    "description": "[From README or user input]",
    "techStack": ["[Discovered languages/frameworks]"],
    "lastUpdated": "[Today's date]"
  },
  "features": {
    "[Feature 1]": {
      "status": "existing",
      "description": "[Discovered from code]"
    }
  }
}
```

#### QUICK.md

```markdown
## Build Commands

- **Build**: `[From package.json scripts or build config]`
- **Dev**: `[Dev server command]`
- **Test**: `[Test command]`
- **Lint**: `[Lint command]`

## Project Info

- **Type**: [Discovered type]
- **Architecture**: [Discovered pattern]
- **Main Language**: [Primary language]

## Key Entry Points

- [Main file]: [Purpose]
- [Config file]: [What it configures]
```

#### ARCHITECTURE.json

```json
{
  "meta": {
    "projectName": "[Name]",
    "pattern": "[Discovered architecture pattern]",
    "lastUpdated": "[Today's date]"
  },
  "patterns": {
    "[Pattern 1]": {
      "description": "[How it's used]",
      "example": "[File.ext:line]"
    }
  },
  "layers": {
    "[Layer]": {
      "purpose": "[Purpose]",
      "location": "[Directory]"
    }
  },
  "dataFlow": {
    "description": "[How data moves through the system]"
  }
}
```

#### FILES.json

```json
{
  "meta": {
    "projectName": "[Name]",
    "lastUpdated": "[Today's date]",
    "totalFiles": "[Approximate count]"
  },
  "keyFiles": {
    "[File path]": {
      "purpose": "[What it does]",
      "dependencies": ["[Related files]"]
    }
  },
  "structure": {
    "[Directory]": "[Purpose of directory]"
  }
}
```

#### PATTERNS.md

```markdown
# Patterns

## [Pattern Name]

**Used for**: [Purpose]
**Example**: `[File.ext:line]`

```[language]
[Code example from the codebase]
```

## [Pattern Name 2]
...
```

#### TODO.md

```markdown
# TODO

## Current Sprint

- [ ] Review and refine .ai/ memory files
- [ ] Add any missing patterns to PATTERNS.md

## Discovered Technical Debt

- [Any issues noticed during exploration]

## Completed

- [x] Initial memory system setup
```

---

### Phase 6: Validation

**After populating files:**

1. Verify JSON files parse correctly
2. Check file references exist
3. Confirm build commands work:
   ```bash
   # Try the discovered build command
   [BUILD_COMMAND]
   ```

**Ask user:**
```
Memory system populated. Here's what I discovered:

- Project: [Name]
- Type: [Type]
- Architecture: [Pattern]
- Key files indexed: [X]
- Patterns documented: [Y]

Does this look accurate? Anything I missed or got wrong?
```

---

### Phase 7: Final Report

```markdown
## Installation Complete!

### What Was Set Up

- `.claude/commands/` - Generic workflow commands
- `.claude/agents/` - Specialized AI agents
- `.ai/` - Memory system populated from your codebase

### What I Discovered

**Project**: [Name]
**Type**: [Type]
**Architecture**: [Pattern]
**Size**: [X] files across [Y] directories

**Key Patterns Found:**
- [Pattern 1]
- [Pattern 2]

**Build Commands:**
- Build: `[command]`
- Test: `[command]`
- Dev: `[command]`

### Next Steps

1. **Review the memory files** - Check `.ai/` for accuracy
2. **Refine as needed** - Add patterns I missed
3. **Start using the workflow**:
   ```
   /prd [new feature]
   /TaskGen [prd file]
   /execute [tasks file]
   ```

### Keeping Updated

- Run `/update` after significant changes
- Run `/pull-fc` to get latest commands
- Run `/push-fc` to contribute improvements
```

---

## Optional: Values Discovery

If you plan to use the autonomous orchestrator (`orchestrator.py`), we recommend running `/values-discovery` to create a personal values profile at `~/.claude/VALUES.md`. This enables values-driven agent decisions -- the autonomous PM and PL agents will make planning and execution choices aligned with your principles.

This is not required for standard Fat Controller usage. The command flow (`/prd`, `/TaskGen`, `/execute`, `/commit`) works without it.

---

## Error Handling

**If exploration gets stuck:**
- Break into smaller chunks
- Ask user for guidance on specific area
- Use Explore agents for parallel discovery

**If project is too complex:**
- Focus on one domain at a time
- Build memory incrementally over multiple sessions
- Document what's known, mark unknowns for later

**If patterns aren't clear:**
- Ask user about architectural decisions
- Note uncertainty in memory files
- Refine as you learn more through usage

---

## Ready to Start?

**Claude**: Begin with Phase 1 (Project Assessment) now!
