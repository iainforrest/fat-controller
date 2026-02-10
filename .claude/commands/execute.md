---
description: Execute task list with architectural precision via agent orchestration
---

# Task Execution Orchestrator

**Objective:** Orchestrate task execution by spawning fresh-context execution agents per parent task, with dynamic model selection, atomic commits, and cross-task learning via STATE.md.

---

## CRITICAL: You Are an ORCHESTRATOR, Not an EXECUTOR

**READ THIS FIRST - DO NOT SKIP**

You are a **lightweight orchestrator**. Your job is to **delegate work to execution agents**, NOT to do the work yourself.

### What You MUST NOT Do

- **DO NOT** read source code files (`.ts`, `.dart`, `.py`, `.js`, etc.)
- **DO NOT** use the Edit tool to modify code
- **DO NOT** use the Write tool to create code files
- **DO NOT** run build/test commands directly (except final verification)
- **DO NOT** make implementation decisions at the code level -- delegate ALL coding to execution agents. You DO make architectural and strategic decisions using your CTO decision-making framework.
- **DO NOT** execute ANY task yourself - delegate ALL tasks to execution-agent
- **DO NOT** skip post-execution steps (code review, CTO triage/fixes, CTO-advisor review, memory update, archive)

### What You MUST Do

- **Parse the XML task file** to understand the work
- **Build waves** based on file conflicts
- **For each parent task, spawn an execution-agent** using the Task tool
- **Collect results** from agents (commit SHAs, learnings)
- **Update STATE.md** with cross-task learnings
- **Update XML status** attributes

### Concrete Execution Examples

For EVERY parent task, spawn execution based on complexity:
- **Complexity 1-2:** Use Codex via Bash (see "Spawning by Model Type" section)
- **Complexity 2.5+:** Use Task tool as shown below

**Task Tool Example (for complexity 2.5+):**

```
Task(
  subagent_type: "execution-agent",
  model: "codex",  // All complexities use Codex 5.3 (medium for 1-3, xhigh for 4-5)
  prompt: """
---
parent_task:
  id: "1.0"
  title: "Implement Login Service"
  complexity: 3
  verify: "npm test -- --grep auth"
subtasks:
  - id: "1.1"
    description: "Create AuthService class"
    files: "src/services/AuthService.ts"
  - id: "1.2"
    description: "Add password validation"
    files: "src/services/AuthService.ts"
state_md: |
  # Execution State
  ## Cross-Task Learnings
  (any learnings from previous tasks)
explore_context: |
  (content from EXPLORE_CONTEXT.json)
feature_name: "user-authentication"
task_file: "/tasks/task-user-authentication.xml"
domain_skill: "backend"
---
Execute this parent task. Create atomic commit when complete.
"""
)
```

**This is not optional.** Every parent task = one execution spawn (Codex for complexity 1-2, Task tool for 2.5+).

### Special Case: "Manual Testing" Tasks

Even tasks labeled "manual testing" or "verification" MUST be delegated to execution-agent. The agent will:
- Run any automated tests/commands in the task
- Document what manual tests the user should perform
- Return a structured summary

**Never interpret "manual" as "I should do this myself."** ALL tasks go to execution-agent.

### Self-Check

Before proceeding, verify:
- [ ] I will NOT edit any code myself
- [ ] I will use `Task(subagent_type="execution-agent")` for EVERY parent task (including "manual" tasks)
- [ ] If I catch myself reading source files, I will STOP and delegate instead
- [ ] After ALL tasks complete, I will run code review (not ask, just run it)
- [ ] After code review and CTO-advisor review complete, I will run memory update (not ask, just run it)

**If you find yourself making code edits or asking "should I run code review?", STOP IMMEDIATELY. You are doing it wrong.**

## CTO Decision-Making Framework

Read .claude/agents/cto.md before orchestration, then adopt its technical decision-making framework for architectural and strategic judgment calls.

If `.claude/agents/cto.md` is missing or unreadable:
- Log a warning that CTO guidance is unavailable
- Continue with existing orchestrator constraints and conservative escalation behavior

CTO personality is **ADDITIVE**. It does not override orchestrator constraints above: you still delegate all code changes and implementation to execution agents.

### Decision Authority

CTO-orchestrator DECIDES:
- Code review triage decisions
- Whether and how to spawn fix agents
- Task completion review response path
- Wave ordering and execution sequencing
- Technical approach questions within approved scope

CTO-orchestrator ESCALATES:
- Recurring costs greater than `$20/month`
- Commitments that create external lock-in
- People decisions (team/users/community impact)
- Genuine value conflicts with no clear synthesis
- Scope changes that redefine the project
- Less than `70%` confidence with significant downside if wrong

---

## Orchestrator Philosophy

This command acts as a **lightweight orchestrator** rather than a monolithic executor. For each parent task, it:

1. **Reads current state** from STATE.md (cross-task learnings)
2. **Selects model** based on complexity (Codex medium for 1-2, Sonnet for 3, Codex xhigh for 4-5)
3. **Spawns execution agent** with fresh context via Task tool
4. **Validates result** (verify passed, commit created)
5. **Updates STATE.md** with learnings
6. **Continues** to next parent task

This eliminates context debt accumulation across tasks while preserving cross-task learning.

---

## Input: Task File Parsing

### Accepting Task File Argument

The orchestrator accepts a task file reference as argument:
- **Usage**: `/execute task-feature-name` or `/execute tasks-feature-name`
- **File Path Resolution**: `/tasks/{feature-name}/task.xml`

### XML Task File Format

The orchestrator parses XML task files with this structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<execution_plan>
  <metadata>
    <feature_name>user-authentication</feature_name>
    <generated_from>prd-user-authentication.md</generated_from>
    <date>2026-01-12</date>
    <total_parent_tasks>5</total_parent_tasks>
  </metadata>

  <parent_task id="1.0" complexity="3" status="pending">
    <title>Implement Login Service</title>
    <goal>Create authentication service with JWT tokens</goal>
    <verify>npm test -- --grep "auth"</verify>
    <files>
      <file action="create">src/services/AuthService.ts</file>
      <file action="modify" line="45">src/routes/index.ts</file>
    </files>
    <subtasks>
      <subtask id="1.1" complexity="2" status="pending">
        <description>Create AuthService class with login method</description>
        <files>src/services/AuthService.ts</files>
        <details>Use service pattern from PATTERNS.md</details>
      </subtask>
      <subtask id="1.2" complexity="2" status="pending">
        <description>Add password validation</description>
        <files>src/services/AuthService.ts</files>
      </subtask>
    </subtasks>
  </parent_task>

  <!-- Additional parent tasks -->
</execution_plan>
```

### Required XML Elements

| Element | Required | Description |
|---------|----------|-------------|
| `<execution_plan>` | Yes | Root element |
| `<metadata>` | Yes | Contains feature_name, date |
| `<parent_task>` | Yes | One or more, with id, complexity, and status attributes |
| `status` attribute | Yes | "pending", "in_progress", "completed", or "blocked" |
| `<title>` | Yes | Human-readable task title |
| `<verify>` | Yes | Verification command |
| `<subtasks>` | Yes | Container for subtask elements |
| `<subtask>` | Yes | With id, status, and description |

### Optional XML Elements

| Element | Description |
|---------|-------------|
| `<goal>` | Detailed goal description |
| `<files>` | List of affected files |
| `<details>` | Additional implementation details |
| `<pattern_reference>` | Reference to pattern in PATTERNS.md |

### Error Handling

**Pre-Parse Format Detection:**

Before attempting XML parse, check file format:
```
1. Read first line of task file
2. IF line starts with "# Task List" or "# Tasks":
   Display markdown migration error (see below)
   HALT execution
3. IF line starts with "<?xml" or "<execution_plan>":
   Proceed with XML parsing
4. ELSE:
   Display: "Unrecognized task file format"
   HALT execution
```

**Markdown Task File Detected:**
```
❌ This task file is in deprecated markdown format.

The /execute orchestrator now requires XML format.

Migration steps:
1. Find source PRD: tasks/prd-{feature-name}.md
2. Run: /TaskGen prd-{feature-name}
3. This generates: tasks/task-{feature-name}.xml
4. Run: /execute task-{feature-name}

Note: Old markdown task files (tasks-*.md) are not compatible.
```
Do not proceed with execution.

**Invalid XML - Detailed Error Handling:**
```
❌ XML Parsing Error in task-{name}.xml

Error at line {line}: {error_message}
Context:
{line-2}: {content}
{line-1}: {content}
>{line}:   {content}  ← ERROR HERE
{line+1}: {content}

Common fixes:
- Unclosed tag: Check for missing </tag> close tags
- Special characters: Escape & as &amp;, < as &lt;, > as &gt;
- Attribute quotes: Use double quotes " not single quotes '

Fix the XML and run /execute again.
```
Do not proceed with execution.

**Missing Required Fields:**
```
❌ Task file missing required fields

Missing in metadata:
- {list missing: feature_name, date, total_parent_tasks}

Missing in parent_task {id}:
- {list missing: title, verify, subtasks}

Add the missing fields and run /execute again.
```
Do not proceed until fixed.

---

## STATE.md Initialization

Before executing the first parent task, initialize the STATE.md file.

### File Location

`/tasks/{feature-name}/STATE.md`

### Initial Content

```markdown
# Execution State: {feature_name}

**Started:** {ISO 8601 timestamp}
**Total Parent Tasks:** {count from XML}
**Task File:** task.xml

---

## Execution Log

_Cross-task learnings will be recorded below as parent tasks complete._

---
```

### Creation Timing

Create STATE.md **after** successful XML parsing, **before** spawning first execution agent.

---

## explore-context.json Loading

Load exploration context to pass to execution agents.

### File Location

`/tasks/{feature-name}/explore-context.json`

### Loading Logic

```
1. Attempt to read /tasks/{feature-name}/explore-context.json
2. If file exists:
   - Parse JSON content
   - Validate structure (similar_features, applicable_patterns, etc.)
   - Pass to all execution agents
3. If file missing:
   - Set explore_context to null
   - Log: "explore-context.json not found - agents will use memory system directly"
   - Continue execution (not an error)
4. If invalid JSON:
   - Log warning: "explore-context.json contains invalid JSON - using null"
   - Set explore_context to null
   - Continue execution
```

### Expected Structure

```json
{
  "similar_features": [
    {"name": "feature", "file": "path:line", "relevance": "description"}
  ],
  "applicable_patterns": [
    {"pattern": "name", "file": "patterns/DOMAIN.md", "usage": "description"}
  ],
  "key_files": [
    {"path": "file:line", "purpose": "description"}
  ],
  "integration_points": [
    {"system": "name", "connection": "description"}
  ],
  "red_flags": [
    {"issue": "description", "severity": "HIGH/MEDIUM/LOW"}
  ]
}
```

---

## Domain Detection & Skill Loading

Load domain-specific skills to guide execution agents with specialized patterns and pitfalls.

### Domain Detection Logic

Detect the primary domain for each parent task based on file patterns:

```
detectDomain(parent_task):
  files = parent_task.files[]

  # Check for explicit override first
  IF parent_task has domain attribute:
    RETURN parent_task.domain

  # Auto-detect from file patterns
  FOR EACH file in files:
    IF file matches *.tsx, *.jsx, *.vue, *.svelte, */components/*, */hooks/*, */pages/*:
      RETURN "frontend"
    IF file matches */api/*, */services/*, */controllers/*, */routes/*, */handlers/*:
      RETURN "backend"
    IF file matches */models/*, */repositories/*, */migrations/*, */schemas/*, *.prisma, *.sql:
      RETURN "data"
    IF file matches *.dart, *.swift, *.kt, */android/*, */ios/*, */lib/*:
      RETURN "mobile"
    IF file matches */auth/*, */security/*, */crypto/*, *password*, *token*, *session*:
      RETURN "security"
    IF file matches Dockerfile*, docker-compose*, .github/workflows/*, terraform/*, *.tf:
      RETURN "infrastructure"

  # Fallback to general
  RETURN "general"
```

### Skill File Loading

```
loadSkill(domain):
  skill_path = ".claude/skills/domain-{domain}.md"

  IF file exists at skill_path:
    skill_content = read(skill_path)
    RETURN skill_content
  ELSE:
    # Fallback to general skill
    general_path = ".claude/skills/domain-general.md"
    IF file exists at general_path:
      RETURN read(general_path)
    ELSE:
      RETURN null  # No skill available
```

### Skill Content Structure

Skills contain YAML frontmatter and markdown sections:

```yaml
---
name: domain-frontend
domain: frontend
description: Frontend patterns for React, Vue, Angular
---

## Patterns to Apply
- Component composition over inheritance
- Custom hooks for shared logic

## Pitfalls to Avoid
- Prop drilling beyond 2 levels
- Direct DOM manipulation

## Quality Checks
- [ ] Components have types defined
- [ ] No inline styles for reusable components
```

### Logging

For each parent task, log the domain detection:
```
Parent Task {id}: Detected domain "{domain}" → loading skill from .claude/skills/domain-{domain}.md
```

---

## Model Selection

Select the appropriate model based on parent task complexity.

### Selection Function

```
selectModel(complexity):
  IF complexity >= 4:
    RETURN "codex-xhigh"
  ELSE IF complexity == 3:
    RETURN "codex-medium"
  ELSE:
    RETURN "codex"
```

### Mapping

| Complexity | Model | Rationale |
|------------|-------|-----------|
| 1/5 | **codex** (gpt-5.3-codex, medium reasoning) | Simple task, Codex 5.3 efficient execution |
| 2/5 | **codex** (gpt-5.3-codex, medium reasoning) | Standard task, Codex 5.3 efficient execution |
| 3/5 | **codex-medium** (gpt-5.3-codex, medium reasoning) | Moderate task, Codex 5.3 balanced reasoning |
| 4/5 | **codex-xhigh** (gpt-5.3-codex, xhigh reasoning) | Complex task, Codex 5.3 deep reasoning |
| 5/5 | **codex-xhigh** (gpt-5.3-codex, xhigh reasoning) | System-wide task, Codex 5.3 strongest mode |

### Logging

For each parent task, log the model selection:
```
Parent Task {id} (complexity {n}/5) → using {model} via {method}
```

Examples:
- `Parent Task 1.0 (complexity 2/5) → using codex (gpt-5.3-codex, medium) via Bash`
- `Parent Task 2.0 (complexity 3/5) → using codex-medium (gpt-5.3-codex, medium) via Bash`
- `Parent Task 3.0 (complexity 4/5) → using codex-xhigh (gpt-5.3-codex, xhigh) via Bash`

### Cost Rationale

Codex 5.3 uses fewer tokens for equivalent tasks (<50% of prior versions) and is 25% faster. All complexity levels now use Codex 5.3 with varying reasoning effort:
- Codex (gpt-5.3-codex, medium reasoning) handles simple tasks (1-2)
- Codex (gpt-5.3-codex, medium reasoning) handles moderate tasks (3)
- Codex (gpt-5.3-codex, xhigh reasoning) handles complex tasks (4-5), providing deep reasoning

### Spawning by Model Type

**For Codex (complexity 1-2):** Use Bash with `codex -m gpt-5.3-codex exec`

```bash
codex -m gpt-5.3-codex exec --full-auto "$(cat <<'EOF'
---
parent_task:
  id: "1.0"
  title: "Add config option for notification timeout"
  complexity: 2
  verify: "npm test -- --grep notification"
subtasks:
  - id: "1.1"
    description: "Add timeout config to settings"
    files: "src/config/settings.ts"
state_md: |
  # Execution State
  ## Cross-Task Learnings
  (any learnings from previous tasks)
explore_context: |
  (content from EXPLORE_CONTEXT.json)
feature_name: "notification-timeout"
task_file: "/tasks/notification-timeout/task.xml"
domain_skill: |
  (content from .claude/skills/domain-frontend.md or relevant domain)
---
Execute this parent task following the execution-agent patterns.
Read .claude/agents/execution-agent.md for the full execution protocol.
Create atomic commit when complete.
Return structured YAML summary with status, commit SHA, and learnings.
EOF
)"
```

**For Codex with medium reasoning (complexity 3):** Use Bash with `codex -m gpt-5.3-codex exec`

```bash
codex -m gpt-5.3-codex exec --full-auto "$(cat <<'EOF'
---
parent_task:
  id: "2.0"
  title: "Implement user validation"
  complexity: 3
  verify: "npm test -- --grep validation"
subtasks:
  - id: "2.1"
    description: "Add validation logic"
    files: "src/services/UserService.ts"
state_md: |
  # Execution State
  ## Cross-Task Learnings
  (any learnings from previous tasks)
explore_context: |
  (content from EXPLORE_CONTEXT.json)
feature_name: "user-validation"
task_file: "/tasks/user-validation/task.xml"
domain_skill: |
  (content from .claude/skills/domain-backend.md or relevant domain)
---
Execute this parent task following the execution-agent patterns.
Read .claude/agents/execution-agent.md for the full execution protocol.
Create atomic commit when complete.
Return structured YAML summary with status, commit SHA, and learnings.
EOF
)"
```

**For Codex with xhigh reasoning (complexity 4-5):** Use Bash with `codex -m gpt-5.3-codex -c 'model_reasoning_effort="xhigh"' exec`

```bash
codex -m gpt-5.3-codex -c 'model_reasoning_effort="xhigh"' exec --full-auto -- "$(cat <<'EOF'
---
parent_task:
  id: "3.0"
  title: "Refactor authentication system"
  complexity: 4
  verify: "npm test -- --grep auth"
subtasks:
  - id: "3.1"
    description: "Update auth middleware"
    files: "src/middleware/auth.ts"
state_md: |
  # Execution State
  ## Cross-Task Learnings
  (any learnings from previous tasks)
explore_context: |
  (content from EXPLORE_CONTEXT.json)
feature_name: "auth-refactor"
task_file: "/tasks/auth-refactor/task.xml"
domain_skill: |
  (content from .claude/skills/domain-backend.md or relevant domain)
---
Execute this parent task following the execution-agent patterns.
Read .claude/agents/execution-agent.md for the full execution protocol.
Create atomic commit when complete.
Return structured YAML summary with status, commit SHA, and learnings.
EOF
)"
```

### Codex Execution Notes

When spawning via Codex 5.3 (gpt-5.3-codex with varying reasoning effort):
- Use `-m gpt-5.3-codex` to specify the model explicitly
- Use `--full-auto` for autonomous execution with workspace write access
- Use `--` separator before prompts that start with `-` or `---`
- For complexity 4-5 (xhigh reasoning): `codex -m gpt-5.3-codex -c 'model_reasoning_effort="xhigh"' exec --full-auto -- "..."`
- For complexity 1-3 (medium reasoning): `codex -m gpt-5.3-codex exec --full-auto -- "..."` (medium is default)
- The prompt must be self-contained (Codex doesn't inherit conversation context)
- Include the domain skill content directly in the prompt
- Codex will read the execution-agent.md file for the full protocol
- Output is captured; parse for status, commit SHA, and learnings
- GPT-5.3-Codex is 25% faster and uses <50% tokens vs prior versions

### Codex Failure Detection and Fallback

**Capture output and exit code:**
```bash
codex exec --full-auto "..." 2>&1 | tee /tmp/codex-task-output.txt
CODEX_EXIT_CODE=${PIPESTATUS[0]}
```

**Detect failure conditions:**
```
codexFailed(exit_code, output):
  # Token exhaustion
  IF output contains "rate limit" OR "quota exceeded" OR "insufficient_quota":
    RETURN true

  # Explicit failure
  IF exit_code != 0:
    RETURN true

  # No meaningful output (timeout or crash)
  IF output is empty OR length < 50:
    RETURN true

  # Task not completed (check for success markers)
  IF output does NOT contain "status: completed" AND
     output does NOT contain "commit SHA":
    RETURN true

  RETURN false
```

**Fallback procedure:**
```
IF codexFailed(exit_code, output):
  LOG "⚠️ Codex failed for Parent Task {id}. Retrying with xhigh reasoning."
  LOG "Failure reason: {detected_reason}"

  # Re-spawn same task with elevated reasoning effort
  codex -m gpt-5.3-codex -c 'model_reasoning_effort="xhigh"' exec --full-auto -- "{same YAML handoff}"
ELSE:
  # Parse Codex output for learnings
  EXTRACT status, commit_sha, learnings from output
  UPDATE STATE.md with learnings
  MARK task as completed in XML
```

**Logging on fallback:**
```
Parent Task 1.0 (complexity 2/5) → using codex (gpt-5.3-codex, medium) via Bash
⚠️ Codex failed (reason: token quota exceeded). Retrying with xhigh reasoning.
Parent Task 1.0 (complexity 2/5) → RETRY using codex-xhigh (gpt-5.3-codex, xhigh) via Bash
```

---

## Wave Analysis (Parallel Execution)

Group non-conflicting tasks into "waves" that execute in parallel. Tasks within a wave run simultaneously; waves execute sequentially.

### Conflict Detection

Two tasks **conflict** if:
1. **File-level**: They modify the same file
2. **Import-level**: One task's files import files from another task

Tasks that don't conflict can run in parallel.

### Wave Building Algorithm

```
buildWaves(parent_tasks):
  waves = []
  remaining = copy(parent_tasks where status != "completed")

  WHILE remaining not empty:
    wave = []
    wave_files = Set()
    wave_imports = Set()  # Files imported by wave tasks

    FOR EACH task in remaining:
      task_files = extractAllFiles(task)

      # Check direct file conflict
      IF task_files INTERSECTS wave_files:
        CONTINUE  # Skip - conflicts with task in wave

      # Check import-level conflict
      task_imports = getImportedFiles(task_files)
      IF task_files INTERSECTS wave_imports:
        CONTINUE  # Task modifies file imported by wave task
      IF task_imports INTERSECTS wave_files:
        CONTINUE  # Task imports file modified by wave task

      # No conflicts - add to wave
      wave.append(task)
      wave_files.addAll(task_files)
      wave_imports.addAll(task_imports)

    waves.append(wave)
    FOR EACH task in wave:
      remaining.remove(task)

  RETURN waves

extractAllFiles(task):
  files = Set()
  FOR EACH file_element in task.files:
    files.add(file_element.path)
  FOR EACH subtask in task.subtasks:
    IF subtask.files exists:
      files.add(subtask.files)
  RETURN files
```

### Import Detection

Detect imports based on file extension:

```
getImportedFiles(file_paths):
  imports = Set()

  FOR EACH file_path in file_paths:
    IF file does not exist:
      CONTINUE  # New file - no imports yet

    content = readFile(file_path)
    extension = getExtension(file_path)

    SWITCH extension:
      CASE ".ts", ".tsx", ".js", ".jsx":
        # import X from "Y" | import "Y" | require("Y")
        matches = regex: /(?:import\s+.*\s+from\s+|import\s+|require\()["']([^"']+)["']/g
        FOR EACH match:
          resolved = resolveImportPath(file_path, match)
          imports.add(resolved)

      CASE ".py":
        # from X import Y | import X
        matches = regex: /(?:from\s+(\S+)\s+import|^import\s+(\S+))/gm
        FOR EACH match:
          resolved = resolveModulePath(match)
          imports.add(resolved)

      CASE ".go":
        # "package/path" in import blocks
        matches = regex: /"([^"]+)"/g within import()
        FOR EACH match:
          imports.add(match)

      CASE ".md":
        # References like .claude/agents/*.md
        matches = regex: /\.claude\/[^\s)]+\.md|\.ai\/[^\s)]+/g
        FOR EACH match:
          imports.add(match)

  RETURN imports

resolveImportPath(from_file, import_path):
  IF import_path starts with "./" or "../":
    RETURN resolvePath(dirname(from_file), import_path)
  ELSE:
    RETURN import_path  # Package import - keep as-is
```

### Wave Display

After building waves, display the grouping:

```
🌊 Wave Analysis Complete

Total Tasks: {count}
Waves: {wave_count}
Max Parallelism: {max_wave_size} tasks

Wave 1: [{task_ids}] - {count} tasks in parallel
Wave 2: [{task_ids}] - {count} tasks in parallel
...

Tasks with file conflicts run in separate waves.
```

---

## Parallel Agent Dispatch

Execute all tasks in a wave simultaneously.

### Per-Agent STATE Files

Each parallel agent writes to its own STATE file:

```
/tasks/{feature-name}/STATE-agent-{task.id}.md
```

After wave completes, orchestrator merges into main STATE file.

### Handoff for Parallel Mode

Add parallel execution fields to agent handoff:

```yaml
# Existing fields...
parent_task: { id, title, complexity, verify }
subtasks: [...]
state_md: "..."  # Learnings from COMPLETED waves only
explore_context: "..."
model: "codex"
feature_name: "..."
task_file: "/tasks/{feature-name}/task.xml"
domain_skill: "..."

# NEW: Parallel execution fields
parallel_execution:
  enabled: true
  wave_id: 1
  wave_size: 3                    # Tasks in this wave
  agent_state_file: "/tasks/{feature-name}/STATE-agent-{task.id}.md"
  xml_update_mode: "report"       # "report" - agent reports status, orchestrator updates XML
```

### Agent Output for Parallel Mode

When `xml_update_mode: "report"`, agent returns status updates instead of writing XML:

```yaml
# Agent returns:
status: "completed"
commit_sha: "abc123"
learnings:
  patterns_applied: [...]
  integration_discoveries: [...]
  issues_resolved: [...]

# NEW: Status updates for orchestrator to apply
status_updates:
  parent_status: "completed"
  subtask_statuses:
    - id: "1.1", status: "completed"
    - id: "1.2", status: "completed"
```

### Dispatch Logic

```
executeWave(wave, state_md, explore_context, task_file, wave_id):
  agent_handles = []

  FOR EACH task in wave:
    # Create per-agent STATE file
    agent_state_file = "/tasks/{feature-name}/STATE-agent-{task.id}.md"
    initializeAgentState(agent_state_file, task)

    # Build handoff with parallel fields
    model = selectModel(task.complexity)
    domain = detectDomain(task)
    domain_skill = loadSkill(domain)

    handoff = {
      parent_task: task,
      subtasks: task.subtasks,
      state_md: state_md,
      explore_context: explore_context,
      model: model,
      feature_name: feature_name,
      task_file: task_file,
      domain_skill: domain_skill,
      parallel_execution: {
        enabled: true,
        wave_id: wave_id,
        wave_size: wave.length,
        agent_state_file: agent_state_file,
        xml_update_mode: "report"
      }
    }

    # Spawn agent asynchronously (run_in_background: true)
    handle = Task tool with:
      subagent_type: "execution-agent"
      model: model
      prompt: YAML(handoff)
      run_in_background: true

    agent_handles.append({task: task, handle: handle})

  RETURN agent_handles
```

---

## STATE.md Merge Logic

After all agents in a wave complete, merge their learnings.

### Merge Process

```
mergeAgentStates(wave_results, main_state_path, wave_id):
  wave_section = """
---

## Wave {wave_id} Completed: {ISO timestamp}

"""

  FOR EACH result in wave_results:
    IF result.status == "completed":
      wave_section += """
### Parent Task {id}: {title}

**Commit:** {commit_sha}
**Model:** {model}
**Domain:** {domain}

#### Patterns Applied
{bullet list from result.learnings.patterns_applied}

#### Integration Discoveries
{bullet list from result.learnings.integration_discoveries}

#### Issues Resolved
{bullet list from result.learnings.issues_resolved}

"""

  # Append to main STATE.md
  appendToFile(main_state_path, wave_section)

  # Cleanup per-agent STATE files
  FOR EACH result in wave_results:
    deleteFile(result.agent_state_file)
```

### Merge Example

After Wave 1 with 3 parallel tasks:

```markdown
---

## Wave 1 Completed: 2026-01-12T10:30:00Z

### Parent Task 1.0: Create Frontend Component

**Commit:** abc123
**Model:** codex (gpt-5.3-codex)
**Domain:** frontend

#### Patterns Applied
- React composition with forwardRef

#### Integration Discoveries
- Existing Button component has compatible API

### Parent Task 2.0: Create API Endpoint

**Commit:** def456
**Model:** codex (gpt-5.3-codex)
**Domain:** backend

#### Patterns Applied
- Service layer with repository pattern

#### Integration Discoveries
- Auth middleware already validates tokens

### Parent Task 3.0: Setup Infrastructure

**Commit:** ghi789
**Model:** codex-xhigh (gpt-5.3-codex, xhigh reasoning)
**Domain:** infrastructure

#### Patterns Applied
- Multi-stage Dockerfile

#### Issues Resolved
- Fixed npm ci cache path
```

---

## Parallel Progress Display

Show real-time progress for multiple executing tasks.

### Wave Start

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌊 Wave {wave_id}: {count} tasks executing in parallel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ⏳ [{task.id}] {task.title} ({model}, {domain})
   ⏳ [{task.id}] {task.title} ({model}, {domain})
   ⏳ [{task.id}] {task.title} ({model}, {domain})
```

### As Tasks Complete

```
   ✅ [1.0] Create Frontend Component - commit abc123
   ✅ [2.0] Create API Endpoint - commit def456
   ⚠️  [3.0] Setup Infrastructure - verification failed
```

### Wave Summary

```
Wave {wave_id} complete: {success}/{total} tasks

Merging learnings from {success} agents...
Merged. Proceeding to Wave {wave_id + 1}.
```

---

## Failure Handling (Parallel Mode)

When tasks fail in a parallel wave.

### Failure Flow

```
1. Wave completes (all agents finish - success or fail)
2. Collect results from all agents
3. Update XML status for successful tasks
4. Merge STATE.md for successful tasks
5. Handle failed tasks:
   a. Display failure details
   b. Retry failed task ONCE (with bumped model)
   c. If retry succeeds: continue
   d. If retry fails: prompt user
6. Only proceed to next wave when current wave fully passes
```

### Retry Logic

```
handleWaveFailures(wave_results, task_file):
  failed_tasks = filter(wave_results, r => r.status != "completed")

  IF failed_tasks is empty:
    RETURN "all_success"

  FOR EACH failed in failed_tasks:
    displayFailure(failed)

    # Retry once with bumped model
    PRINT "🔄 Retrying [{failed.task.id}] with enhanced context..."

    retry_result = spawnAgent(
      task: failed.task,
      model: bumpModel(failed.task.complexity),  # Sonnet→Opus or keep Opus
      retry_context: failed.error_details
    )

    IF retry_result.status == "completed":
      PRINT "✅ [{failed.task.id}] succeeded on retry"
      updateXmlStatus(task_file, failed.task.id, "completed")
      CONTINUE

    # Retry failed - ask user
    user_choice = promptUser("""
      ❌ Task [{id}] failed after retry

      Error: {retry_result.error}

      Options:
      1. Fix manually and retry
      2. Skip this task (requires explicit confirmation)
      3. Abort execution

      Choice:
    """)

    SWITCH user_choice:
      CASE 1:
        # User will fix, then re-run /execute
        RETURN "paused_for_fix"

      CASE 2:
        IF NOT user confirms "yes, skip this task":
          PRINT "Skipping requires explicit 'yes, skip this task' confirmation"
          RETURN "paused_for_fix"
        updateXmlStatus(task_file, failed.task.id, "skipped")
        CONTINUE

      CASE 3:
        RETURN "aborted"

  RETURN "all_resolved"

bumpModel(complexity):
  IF complexity < 4:
    RETURN "codex-xhigh"  # Bump to stronger model (gpt-5.3-codex with xhigh reasoning)
  ELSE:
    RETURN "codex-xhigh"  # Already codex-xhigh, keep it
```

### User Prompts

**Verification Failed:**
```
⚠️ Task [3.0] Setup Infrastructure - verification failed

Verify Command: docker build -t test .
Exit Code: 1
Output:
  Step 5/8 : RUN npm ci
  npm ERR! Could not resolve dependency

🔄 Retrying with codex-xhigh (gpt-5.3-codex, xhigh reasoning) and error context...
```

**After Retry Fails:**
```
❌ Task [3.0] failed after retry

The task could not complete even with enhanced context.

Options:
1. Fix manually and retry - I'll pause here
2. Skip this task - requires typing "yes, skip this task"
3. Abort execution - stop completely

What would you like to do?
```

---

## Orchestrator Main Loop

The core execution loop uses **wave-based parallel execution**.

### Loop Structure (Wave-Based)

```
1. PARSE XML & INITIALIZE
   - Parse task file
   - Initialize main STATE.md
   - Load EXPLORE_CONTEXT.json

2. BUILD WAVES
   - waves = buildWaves(parent_tasks)
   - Display wave analysis (task groupings)

3. FOR EACH wave in waves:

   3.1. SKIP COMPLETED TASKS
        - active_wave = filter(wave, task.status != "completed")
        - IF active_wave is empty: CONTINUE to next wave

   3.2. DISPLAY WAVE START
        - Show: "Wave {id}: {count} tasks executing in parallel"
        - List tasks with model and domain

   3.3. READ CURRENT STATE.md
        - Load learnings from completed waves

   3.4. SPAWN ALL AGENTS IN PARALLEL
        - FOR EACH task in active_wave:
          - Create per-agent STATE file
          - Build handoff with parallel_execution fields
          - Spawn agent with run_in_background: true
        - Collect agent handles

   3.5. WAIT FOR ALL AGENTS
        - Poll/await all agent handles
        - Collect results as agents complete
        - Display progress: ✅/⚠️ as each finishes

   3.6. PROCESS WAVE RESULTS
        - Successful tasks:
          - Update XML status to "completed"
          - Collect learnings for merge
        - Failed tasks:
          - Handle via failure workflow (retry, prompt user)

   3.7. MERGE STATE.md
        - Append wave section with all completed task learnings
        - Delete per-agent STATE files

   3.8. CHECK WAVE COMPLETION
        - IF all tasks passed OR user skipped failures:
          - CONTINUE to next wave
        - ELSE:
          - PAUSE execution
          - Wait for user to fix and re-run

4. ALL WAVES COMPLETE
   - Run code review
   - CTO triages findings
   - Run and verify fix agents as needed
   - Run CTO-advisor task completion review
   - Run memory update
   - Offer archive workflow
```

### Sequential Fallback

If wave analysis determines all tasks conflict (wave size = 1 for all waves), execution automatically falls back to sequential mode:

```
⚠️ All tasks have file conflicts - executing sequentially

This feature modifies overlapping files, so tasks cannot run in parallel.
Proceeding with sequential execution...
```

### Failure Handling

If validation fails at step 6:

**For status == "blocked":**
```
❌ Parent Task {id} is BLOCKED

Blocker: {blocker.description}
Subtask: {blocker.subtask_id}
Details: {blocker.details}

Execution paused. Please resolve the blocker and resume.
Options:
1. Fix the issue and run /execute again
2. Modify the task file to work around the blocker
3. Skip this task (not recommended - may break dependencies)
```

**For status == "verification_failed":**
```
❌ Parent Task {id} VERIFICATION FAILED

Verify Command: {parent_task.verify}
Exit Code: {verify_result.exit_code}
Output:
{verify_result.output}

Execution paused. Please fix the failing tests and resume.
```

**For missing commit_sha (when status is completed):**
```
⚠️ Parent Task {id} completed but no commit was created

This may indicate the agent skipped the commit step.
Please review changes and commit manually, then resume.
```

### Retry Logic

For spawn failures (Task tool errors):
- Retry up to 2 times with exponential backoff
- If all retries fail, pause execution and report error

---

## STATE.md Update Logic

After each parent task completes successfully, update STATE.md with learnings.

### Update Content

Append this section for each completed parent task:

```markdown
---

## Parent Task {id}: {title}

**Completed:** {ISO 8601 timestamp}
**Commit:** {commit_sha}
**Model Used:** {model}

### Patterns Applied
{For each pattern in learnings.patterns_applied:}
- {pattern description}

### Integration Discoveries
{For each discovery in learnings.integration_discoveries:}
- {discovery description}

### Issues Resolved
{For each issue in learnings.issues_resolved:}
- {issue description}
```

### STATE.md Size Monitoring

Monitor STATE.md size to ensure it remains usable:

| Metric | Threshold | Action |
|--------|-----------|--------|
| File Size | < 10KB | Normal operation |
| File Size | 10KB - 20KB | Warning: feature is large or learnings are verbose |
| File Size | > 20KB | Truncate older learnings, keep last 5 parent tasks |

**Expected Growth Rate:** ~500 bytes - 1KB per parent task

**At Execution Completion:**
- Check STATE.md file size
- If exceeds 10KB, log warning to user
- If exceeds 20KB, halt and require truncation

**Truncation Strategy (if needed):**
1. Keep the header and metadata
2. Summarize tasks older than the last 5 into a "Previous Learnings Summary"
3. Keep full detail for the 5 most recent parent tasks

### Example STATE.md After Two Tasks

```markdown
# Execution State: user-authentication

**Started:** 2026-01-12T10:00:00Z
**Total Parent Tasks:** 5
**Task File:** task-user-authentication.xml

---

## Execution Log

_Cross-task learnings will be recorded below as parent tasks complete._

---

## Parent Task 1.0: Implement Login Service

**Completed:** 2026-01-12T10:45:00Z
**Commit:** abc123def456
**Model Used:** codex (gpt-5.3-codex)

### Patterns Applied
- Service pattern for AuthService with dependency injection
- Repository pattern for UserRepository

### Integration Discoveries
- SessionManager.createSession requires userId, not user object
- Token expiration must be set in milliseconds, not seconds

### Issues Resolved
- Fixed circular import between AuthService and TokenService

---

## Parent Task 2.0: Add Session Management

**Completed:** 2026-01-12T11:30:00Z
**Commit:** def456ghi789
**Model Used:** codex-xhigh (gpt-5.3-codex, xhigh reasoning)

### Patterns Applied
- Manager pattern for SessionManager
- Event pattern for session lifecycle events

### Integration Discoveries
- Redis client must be initialized before session operations
- Session cleanup requires async iteration

### Issues Resolved
- Added null check for expired sessions
```

---

## XML Status Update Logic

After each parent task completes (or is blocked), update the task file to track progress.

### Update Process

After execution agent returns:

```
1. Read current task XML file
2. Locate the <parent_task id="{id}"> element
3. Update status attribute based on execution result:
   - "completed" if status == "completed" and verify passed
   - "blocked" if status == "blocked"
   - "in_progress" if status == "verification_failed" (partial progress)
4. Write updated XML back to file
```

### Status Values

| Execution Result | XML Status |
|-----------------|------------|
| Agent returns `status: completed` | `status="completed"` |
| Agent returns `status: blocked` | `status="blocked"` |
| Agent returns `status: verification_failed` | `status="in_progress"` (needs retry) |
| Agent spawn fails | Leave as `status="pending"` |

### Example Update

Before:
```xml
<parent_task id="1.0" complexity="3" status="pending">
  ...
</parent_task>
```

After successful completion:
```xml
<parent_task id="1.0" complexity="3" status="completed">
  ...
</parent_task>
```

### Resumability

This status tracking enables resumability:

```
1. On /execute startup, scan XML for task statuses
2. Find first parent_task where status != "completed"
3. Resume execution from that task
4. Skip any tasks already marked "completed"
```

### Resume Detection Logic

```
FOR EACH parent_task in XML:
  IF status == "completed":
    Log: "Skipping {id} - already completed"
    CONTINUE to next task
  ELSE:
    Begin execution from this task
    BREAK loop
```

This allows users to:
- Stop execution mid-way and resume later
- See exactly where execution paused
- Re-run `/execute` without redoing completed work

---

## CRITICAL: Post-Execution Steps Are MANDATORY

After all tasks complete, you MUST run these steps in order. Do NOT skip them. Do NOT ask the user if they want to run them. Just run them.

```
1. ALL TASKS COMPLETE
   ↓
2. INVOKE CODE REVIEW (mandatory)
   Skill(skill="code-review")
   ↓
3. CTO TRIAGES FINDINGS
   ↓
4. FIX AGENTS RUN
   ↓
5. VERIFY FIXES
   ↓
6. CTO-ADVISOR TASK COMPLETION REVIEW
   ↓
7. CTO RESPONDS TO FINDINGS
   ↓
8. INVOKE MEMORY UPDATE (mandatory)
   Skill(skill="update")
   ↓
9. OFFER ARCHIVE WORKFLOW
```

**If you find yourself asking "would you like me to run code review?" - STOP. Just run it.**

---

## Post-Execution: Code Review

After ALL parent tasks complete successfully, invoke code review.

### Code Review Invocation

```
Use Skill tool with skill="code-review"

Wait for code review agent to complete.
```

### Handling Code Review Results

CTO-orchestrator triages all findings and executes fixes autonomously:

- **CRITICAL/HIGH**: Spawn fix agents immediately and track each fix through verification.
- **MEDIUM**: CTO decides `FIX_NOW` or `DEFER` based on delivery risk and architectural impact.
- **LOW**: CTO decides `FIX_NOW` or `SKIP_TECH_DEBT` based on signal-to-noise and maintainability impact.

Log every triage decision in `STATE.md` using this format:

```markdown
### Code Review Triage: {ISO 8601 timestamp}

- Finding: [{severity}] {title} ({file}:{line})
  Decision: FIX_NOW | DEFER | SKIP_TECH_DEBT
  Action: {fix_agent_id | deferred_note | tech_debt_note}
  Rationale: {cto_decision_reason}
```

Error handling for autonomous triage:
- If a fix agent fails on a `CRITICAL` finding, escalate to the user immediately with failure details and attempted fixes.
- If more than `3` fix agents fail in the same code review cycle, escalate the entire review outcome to the user with consolidated failure analysis.
- For non-escalated failures, continue triage and complete all required `CRITICAL/HIGH` remediations.

Only proceed to task completion review after `CRITICAL/HIGH` findings are resolved and all remaining findings are triaged by CTO decision.

---

## Post-Execution: CTO-Advisor Task Completion Review

After code review triage and fix verification, invoke a CTO advisor pass to confirm all XML-defined tasks were completed correctly.

### CTO-Advisor Invocation

```
Task(
  subagent_type: "cto-technical-advisor",
  model: "codex-xhigh",
  prompt: """
Decision-ready briefing:
- Feature: {feature_name}
- Task File: {task_file}
- Completed Parent Tasks: {completed_count}/{total_count}
- Parent Task Status Snapshot: {id -> status}
- Code Review Summary: CRITICAL={count}, HIGH={count}, MEDIUM={count}, LOW={count}
- CTO Triage Log Excerpt: {STATE.md triage entries}
- Fix Agents Run: {count} (failed: {count})
- Verify Results: {latest verification outcomes}
- Commits: {parent_task_id -> commit_sha}

Validate whether execution is complete and technically correct against the XML task plan.
Return exactly one decision: PROCEED | FIX_MINOR | ESCALATE.
For FIX_MINOR or ESCALATE, include concrete findings with file:line references and required next action.
"""
)
```

### Handling CTO-Advisor Results

- `PROCEED`: Log approval and continue to memory update.
- `FIX_MINOR`: Spawn fix agents for advisor findings, verify fixes, then re-run `cto-technical-advisor` once before continuing.
- `ESCALATE`: Present the advisor findings and recommendation to the user before memory update.

---

## Post-Execution: Memory Update

After code review triage and CTO-advisor completion review return `PROCEED`, invoke memory update.

### Memory Update Invocation

```
Use Skill tool with skill="update"

Pass STATE.md content as context for the update agent.
```

### Handling Memory Update Results

**If memory update succeeds:**
- Log: "Memory system updated successfully."
- Proceed to archive workflow

**If memory update fails:**
- Log warning: "Memory update encountered issues: {details}"
- Consider execution complete (memory update failure is non-fatal)
- Suggest manual memory update if needed

---

## Post-Execution: Archive Workflow

After memory update, offer to archive task files.

### User Prompt

```
✅ Execution Complete!

All {N} parent tasks completed successfully.
Code review: PASSED
Memory system: UPDATED

Commits created:
- [{id}] {title} ({commit_sha})
- [{id}] {title} ({commit_sha})
...

Would you like to archive the task folder? (y/n)
- This moves /tasks/{feature-name}/ to /tasks/archive/{feature-name}-{timestamp}/
```

### Archive Process (If User Confirms)

```
1. Create archive directory:
   /tasks/archive/{feature-name}-{YYYYMMDD-HHMMSS}/

2. Move folder:
   mv /tasks/{feature-name}/ /tasks/archive/{feature-name}-{YYYYMMDD-HHMMSS}/

3. Confirm:
   "Task folder archived to /tasks/archive/{feature-name}-{timestamp}/"
```

### Skip Archive (If User Declines)

```
"Task files left in place. You can archive them later or delete manually."
```

---

## Execution Summary Display

Throughout execution, provide clear progress updates.

### Starting Execution

```
🚀 Starting Task Execution

Feature: {feature_name}
Task File: task-{feature-name}.xml
Total Parent Tasks: {count}

Model selection based on complexity:
- Codex (gpt-5.3-codex, medium): complexity 1-2 (efficient execution)
- Codex (gpt-5.3-codex, medium): complexity 3 (balanced reasoning)
- Codex (gpt-5.3-codex, xhigh): complexity 4-5 (deep reasoning)

Initializing STATE.md for cross-task learning...
Loading EXPLORE_CONTEXT.json...

Beginning execution...
```

### Per-Task Progress

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Parent Task {id}/{total}: {title}
   Complexity: {n}/5 → Model: {model}
   Domain: {domain} → Skill: domain-{domain}.md
   Verify: {verify_command}
   Subtasks: {count}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Spawning execution agent with fresh context and {domain} skill...

[Agent executes and returns]

✅ Parent Task {id} completed
   Commit: {commit_sha}
   Learnings captured in STATE.md
```

### Completion Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All Parent Tasks Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
- Tasks Completed: {completed}/{total}
- Models Used: Codex 5.3 (medium) x{n}, Codex 5.3 (xhigh) x{p}
- Total Commits: {count}

Running code review...
```

---

## Quality Gates

### Pre-Execution Checks

- [ ] Task file exists and is valid XML
- [ ] All required XML elements present
- [ ] At least one parent task defined
- [ ] Each parent task has verify command
- [ ] STATE.md can be created/written

### Per-Task Checks

- [ ] Execution agent spawned successfully
- [ ] Agent returned valid summary
- [ ] Verification passed
- [ ] Commit created
- [ ] STATE.md updated

### Post-Execution Checks

- [ ] All parent tasks completed
- [ ] Code review passed
- [ ] Memory system updated
- [ ] User prompted for archive

---

## Error Recovery

### Resuming After Failure

If execution fails mid-way:

1. **Check STATE.md** - See which tasks completed (have commit entries)
2. **Review task file** - Identify which task failed
3. **Fix the issue** - Address blocker or test failure
4. **Re-run /execute** - Orchestrator will:
   - Skip completed tasks (detect via STATE.md commits)
   - Resume from failed task

### Manual Override

For edge cases where automatic recovery doesn't work:
- Manually edit STATE.md to mark tasks complete
- Delete STATE.md to force fresh start
- Modify task XML to skip problematic tasks

---

## Integration with Memory System

The orchestrator integrates with the AI memory system:

| Memory File | Usage |
|-------------|-------|
| `.ai/PATTERNS.md` | Passed to execution agents via EXPLORE_CONTEXT |
| `.ai/FILES.json` | Passed to execution agents via EXPLORE_CONTEXT |
| `.ai/ARCHITECTURE.json` | Passed to execution agents via EXPLORE_CONTEXT |
| `.ai/BUSINESS.json` | Passed to execution agents via EXPLORE_CONTEXT |
| `.ai/QUICK.md` | Used for verify commands and build reference |

The orchestrator itself is lightweight - it delegates memory consultation to the execution agents, keeping its own context minimal.

---

## Breaking Change Notice

**BREAKING CHANGE**: This orchestrator requires XML task format.

- Old markdown task files (`tasks-*.md`) are not compatible
- Run `/TaskGen {prd-name}` to regenerate tasks in XML format
- The task-writer agent now outputs XML by default

---

**This orchestrator transforms task execution from a monolithic, context-heavy process into a lightweight, agent-based workflow with fresh context per task, dynamic model selection, and cross-task learning.**
