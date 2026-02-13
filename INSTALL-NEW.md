# The Fat Controller - Bootstrap v3.0

**Welcome!** This interactive process sets up your AI-assisted development system by customizing the `.ai/` memory files for your project.

## What Happens During Bootstrap

1. **Question Rounds** (6-8 rounds, ~15 minutes)
   - You answer 1-3 questions at a time about your project
   - Claude validates answers and provides recommendations

2. **Memory System Setup**
   - Claude populates your `.ai/` files with project-specific context
   - This is where all your project knowledge will live

3. **Ready to Build**
   - Commands like `/prd`, `/TaskGen`, `/execute` will read from `.ai/`
   - Everything works out of the box

## Key Concept: Generic Commands + Project-Specific Memory

```
.claude/commands/     → Generic (same across all projects)
.claude/agents/       → Generic (same across all projects)
.ai/                  → YOUR project's context (populated during bootstrap)
```

Commands don't contain project-specific code. They read from `.ai/` for context. This means:
- You can sync command updates with `/pull-fc`
- Your project knowledge stays in `.ai/`
- Same commands work for any project

---

## For Claude: Bootstrap Instructions

### Critical Rules

**STAY ON TRACK**: Use the checklist below. After each user response:
1. Validate/provide feedback
2. Handle ONE clarifying question if needed
3. Return to checklist and proceed to next round

**NEVER skip rounds**. Complete all 8 before memory setup.

---

## Internal Checklist (FOR CLAUDE)

- [ ] Round 1: Project Basics
- [ ] Round 2: Technology Stack
- [ ] Round 3: Build & Test Systems
- [ ] Round 4: Architecture Patterns
- [ ] Round 5: Scale & Complexity
- [ ] Round 6: Development Workflow
- [ ] Round 7: Special Requirements
- [ ] Round 8: Confirmation
- [ ] Populate .ai/ memory files
- [ ] Final recommendations

---

## Round 1: Project Basics

**Ask:**

1. **What type of project are you building?**
   - Web app, mobile app, API, CLI, library, desktop app, etc.

2. **In 1-2 sentences, what does this project do?**

3. **Do you have a project name?**

**After answers**: Validate, note internally, proceed to Round 2.

---

## Round 2: Technology Stack

**Ask:**

1. **What programming language?**
   - If unsure: "I can recommend based on your project type"

2. **Any specific frameworks or libraries?**
   - If unsure: "I can suggest popular options"

3. **Database and other key technologies?**
   - Cloud platform, services, etc.

**After answers**: Validate tech compatibility, note all choices, proceed to Round 3.

---

## Round 3: Build & Test Systems

**Ask:**

1. **What build system?**
   - npm/yarn/pnpm, Gradle, cargo, make, etc.

2. **Testing framework?**
   - Jest, pytest, JUnit, etc.

3. **Other dev tools?**
   - Linters, formatters, CI/CD

**After answers**: Validate matches tech stack, proceed to Round 4.

---

## Round 4: Architecture Patterns

**Ask:**

1. **Architectural pattern?**
   - MVVM, Clean Architecture, MVC, Layered, etc.
   - If unsure: recommend based on project type

2. **Single app or multi-component?**
   - Monolith, frontend+backend, microservices, etc.

**After answers**: Validate pattern fits project, proceed to Round 5.

---

## Round 5: Scale & Complexity

**Ask:**

1. **Expected project size?**
   - Small (<50 files), Medium (50-500), Large (500+)

2. **Team size?**
   - Solo, Small (2-5), Large (6+)

**After answers**: Validate expectations match, proceed to Round 6.

---

## Round 6: Development Workflow

**Ask:**

1. **Git workflow preference?**
   - Feature branches, trunk-based, standard

2. **CI/CD plans?**
   - GitHub Actions, GitLab CI, none yet, etc.

**After answers**: Note preferences, proceed to Round 7.

---

## Round 7: Special Requirements

**Ask:**

1. **Performance requirements?**
   - Real-time, offline, resource constraints, none specific

2. **Security/compliance requirements?**
   - Auth needs, GDPR, HIPAA, standard practices

3. **Other considerations?**
   - Accessibility, i18n, platform constraints

**After answers**: Note all requirements, proceed to Round 8.

---

## Round 8: Confirmation

**Present summary:**

```markdown
## Project Configuration

**Project**: [Name]
**Type**: [Type]
**Description**: [Description]

**Technology:**
- Language: [Language]
- Framework: [Framework]
- Database: [Database]
- Build: [Build tool]
- Test: [Test framework]

**Architecture:**
- Pattern: [Pattern]
- Structure: [Single/Multi]

**Scale:**
- Size: [Size]
- Team: [Team size]

**Workflow:**
- Git: [Workflow]
- CI/CD: [Tools]

**Requirements:**
- Performance: [Requirements]
- Security: [Requirements]
- Other: [Requirements]
```

**Ask**: "Does this look correct? Any changes?"

**After confirmation**: Proceed to memory setup.

---

## Memory System Setup

### Populate `.ai/` Files

Using the confirmed configuration, update these files:

#### 1. BUSINESS.json

Add to `meta` section:
```json
{
  "meta": {
    "projectName": "[Project name]",
    "description": "[Project description]",
    "owner": "[Ask user or leave blank]",
    "techStack": ["[Language]", "[Framework]", "[Database]"],
    "lastUpdated": "[Today's date]"
  }
}
```

#### 2. QUICK.md

Add build commands section:
```markdown
## Build Commands

- **Build**: `[Build command based on tech stack]`
- **Dev**: `[Dev server command]`
- **Test**: `[Test command]`
- **Lint**: `[Lint command if applicable]`

## Project Info

- **Type**: [Project type]
- **Architecture**: [Pattern]
- **Main Language**: [Language]
```

#### 3. ARCHITECTURE.json

Add initial structure:
```json
{
  "meta": {
    "projectName": "[Project name]",
    "pattern": "[Architecture pattern]",
    "lastUpdated": "[Today's date]"
  },
  "patterns": {
    "primary": {
      "name": "[Pattern name]",
      "description": "[Brief description of how pattern is used]"
    }
  },
  "layers": {
    "[Layer 1]": { "purpose": "[Purpose]" },
    "[Layer 2]": { "purpose": "[Purpose]" }
  }
}
```

#### 4. FILES.json

Add initial structure based on project type:
```json
{
  "meta": {
    "projectName": "[Project name]",
    "lastUpdated": "[Today's date]"
  },
  "structure": {
    "source": "[src/ or app/ or similar]",
    "tests": "[tests/ or __tests__/ or similar]",
    "config": "[Config file locations]"
  }
}
```

#### 5. TODO.md

Initialize with first task:
```markdown
# TODO

## Current Sprint

- [ ] Set up initial project structure
- [ ] Create first feature with /prd

## Completed

(None yet)
```

### Validation

After populating files:
1. Verify JSON files parse correctly
2. Verify all placeholder values are filled
3. Verify tech stack is consistent across files

---

## Final Recommendations

**Present:**

```markdown
## Bootstrap Complete!

Your development system is ready.

### What Was Set Up

- `.ai/BUSINESS.json` - Project identity and tech stack
- `.ai/QUICK.md` - Build commands and shortcuts
- `.ai/ARCHITECTURE.json` - Architecture patterns
- `.ai/FILES.json` - Project structure
- `.ai/TODO.md` - Initial tasks

### Next Steps

1. **Create your first feature**:
   ```
   /prd [describe your first feature]
   ```

2. **Generate tasks**:
   ```
   /TaskGen @tasks/prd-[feature-name].md
   ```

3. **Execute**:
   ```
   /execute @tasks/tasks-[feature-name].md
   ```

4. **After completing work**:
   ```
   /commit
   /update
   ```

### Keeping Updated

Pull latest commands/agents anytime:
```
/pull-fc
```

Contribute improvements back:
```
/push-fc
```

### Files Reference

- Commands: `.claude/commands/` - Workflow commands
- Agents: `.claude/agents/` - Specialized AI experts
- Memory: `.ai/` - Your project knowledge (grows over time)

Ready to build!
```

---

## Optional: Values Discovery

If you plan to use the autonomous orchestrator (`orchestrator.py`), we recommend running `/values-discovery` to create a personal values profile at `~/.claude/VALUES.md`. This enables values-driven agent decisions -- the autonomous PM and PL agents will make planning and execution choices aligned with your principles.

This is not required for standard Fat Controller usage. The command flow (`/prd`, `/TaskGen`, `/execute`, `/commit`) works without it.

---

## Error Recovery

If something goes wrong:
1. Note the error
2. Fix the issue
3. Resume from where you left off

If user wants to restart:
1. Reset `.ai/` files to templates
2. Restart from Round 1

---

## Ready to Start?

**Claude**: Begin with Round 1 questions now!
