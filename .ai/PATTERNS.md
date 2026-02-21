# Pattern Index

*Quick reference for finding implementation patterns*

## How to Use This Index

1. **Find your need** in the Quick Pattern Lookup table below
2. **Load the domain file** from `patterns/[DOMAIN].md`
3. **Copy the template** and adapt to your use case
4. **Reference the codebase** location for working examples

## Pattern Domains

Create domain-specific pattern files as your project grows:

| Domain | File | Description | Status |
|--------|------|-------------|--------|
| Template | `patterns/_TEMPLATE.md` | How to create new domain files | Ready |
| [YOUR_DOMAIN] | `patterns/[NAME].md` | Add as needed | - |

**Common domains to create:**
- `WEB.md` - Frontend patterns (components, state, routing)
- `API.md` - Backend patterns (endpoints, middleware, auth)
- `DATABASE.md` - Data access patterns (queries, repos, migrations)
- `TESTING.md` - Test patterns (unit, integration, e2e)
- `INFRASTRUCTURE.md` - DevOps patterns (deploy, logging, monitoring)

---

## Quick Pattern Lookup

Find the right pattern for your task:

| Need | Pattern | Domain File |
|------|---------|-------------|
| Service with business logic | Service Layer Pattern | patterns/API.md |
| API endpoint | Controller Pattern | patterns/API.md |
| Database queries | Repository Pattern | patterns/DATABASE.md |
| Error handling | Result Type Pattern | patterns/API.md |
| Input validation | Validation Pattern | patterns/API.md |
| Component structure | Component Pattern | patterns/WEB.md |
| State management | State Pattern | patterns/WEB.md |
| Unit tests | Unit Test Pattern | patterns/TESTING.md |
| Integration tests | Integration Test Pattern | patterns/TESTING.md |
| Authentication | Auth Pattern | patterns/AUTH.md |
| Logging | Logging Pattern | patterns/INFRASTRUCTURE.md |
| Agent delegation | Command-Agent Pattern | (below) |
| Authority routing | Authority-Based Memory | (below) |
| Automated capture | Knowledge Capture Pattern | (below) |
| Codex validation | Three-Tier Execution | (below) |
| Dual-model code review | Parallel Model Orchestration | (below) |
| Downstream effects analysis | Downstream Effects Pattern | (below) |
| Multi-model debate | Debate Orchestration Pattern | (below) |
| Autonomous PM-PL cycles | Autonomous Orchestration Pattern | (below) |
| Values-driven agent boot | Values-Driven Agent Boot Pattern | (below) |
| Structured agent signals | Structured Output Protocol | (below) |
| Tmux background execution | Tmux Background Orchestration | (below) |
| DAG-based graph execution | Graph Engine Orchestration Pattern | (below) |
| Model class routing | Model Stylesheet Pattern | (below) |
| Discovery before implementation | Discovery Node Pattern | (below) |
| Quality gate with retry | Goal Gate Convergence Pattern | (below) |
| Outcome-to-delivery | Project Lead Orchestration Pattern | (below) |
| Dev-to-production .claude/ sync | Dev-to-Production Sync Pattern | See ARCHITECTURE.json devToProductionSync |

*Table expands as you add patterns. Update when adding new domain files.*

---

## Built-in Pattern: Command-Agent Delegation

This pattern is core to the fat-controller workflow.

### When to Use
- Heavy document generation (PRDs, task lists)
- Work requiring isolated context
- Autonomous processing without interactive Q&A
- Pattern matching across entire codebase

### Command Structure
```yaml
---
description: Short description for command list
---

# Command Role and Instructions

[Command gathers context through batched Q&A]
[Confirms summary with user]
[Invokes agent with structured context]
```

### Agent Structure
```yaml
---
name: agent-name
description: When to invoke with examples
model: sonnet
color: blue
---

# Agent Role and Instructions

[Reads memory system for context]
[Processes input autonomously]
[Generates output to /tasks/]
[Returns confirmation summary]
```

### Context Handoff Format
```yaml
FEATURE_NAME: kebab-case-name
PROBLEM: One sentence problem statement
MUST_HAVE:
- Requirement 1
- Requirement 2
NICE_TO_HAVE:
- Optional requirement
USER_FLOWS:
  HAPPY_PATH:
    - Step 1
    - Step 2
  ERROR_FLOWS:
    - Error scenario
SUCCESS_CRITERIA: How we know it's done
COMPLEXITY: Low/Medium/High
```

**Reference**: `.claude/commands/prd.md` → `.claude/agents/prd-writer.md`

---

## Built-in Pattern: Authority-Based Memory

This pattern ensures single source of truth for all content types.

### When to Use
- Updating memory system
- Adding new content to .ai/ files
- Preventing content duplication
- Routing updates to correct authoritative file

### Authority Map

**See QUICK.md** for the complete Authority Map table showing which file owns each content type.

### Implementation Checklist
- [ ] Identify content type using authority map
- [ ] Check if content already exists in authoritative file
- [ ] Add content to authoritative file (or update existing)
- [ ] If needed, add pointer in QUICK.md (not copy)
- [ ] Validate: no content duplication across files

**Reference**: `.ai/decisions/001-use-authority-based-memory.md`

---

## Built-in Pattern: Automated Knowledge Capture

Commands automatically capture decisions, solutions, deprecations, and tech debt.

### When to Use
- During /prd → capture architectural decisions
- During /bugs → capture solutions (YAML)
- During /execute → capture solutions, decisions, deprecations
- During /code-review → capture MEDIUM/LOW findings to TECH_DEBT.md

### Capture Formats
```yaml
# solutions/*.yaml (grep-friendly)
problem: "Brief problem description"
symptoms: ["Observable symptom 1", "Symptom 2"]
rootCause: "Why this happened"
solution: "What fixed it"
preventionSteps: ["How to prevent recurrence"]

# decisions/*.md (ADR format)
# Use template at .ai/decisions/000-template.md

# TECH_DEBT.md entries
### [TD-NNN] [Component]: [Brief Description]
**Severity**: MEDIUM | LOW
**Location**: `file or glob`
**Description**: [Details]
**Why Deferred**: [Reason]
```

### Implementation Checklist
- [ ] Identify capture opportunity in command workflow
- [ ] Choose correct format (YAML for solutions, ADR for decisions)
- [ ] Capture without interrupting user workflow
- [ ] Use grep-friendly structure (YAML keys, ADR headings)
- [ ] Reference captured knowledge in memory files

**Reference**: `.claude/commands/execute.md` (solution capture), `.claude/commands/code-review.md` (tech debt capture)

---

## Built-in Pattern: Three-Tier Execution

Route tasks to appropriate model tier based on complexity.

### When to Use
- Tier 1 (Codex Max gpt-5.1-codex-max): Complex tasks (4-5), deep reasoning
- Tier 2 (Sonnet): Moderate tasks (3), balanced cost/capability
- Tier 3 (Codex gpt-5.2-codex): Simple tasks (1-2), saves Claude tokens

### Execution Strategy
```
Task arrives
    ↓
Complexity assessment
    ↓
┌────────────────────────┬──────────────────┬─────────────────────────────┐
│ COMPLEX (4-5)          │ STANDARD (3)     │ SIMPLE (1-2)                │
│ Codex (xhigh)          │ Sonnet 4.5       │ Codex (medium)              │
│ (gpt-5.2-codex, xhigh) │                  │ (gpt-5.2-codex, medium)     │
├────────────────────────┼──────────────────┼─────────────────────────────┤
│ - Architecture         │ - Implementation │ - Validation                │
│ - Complex refactor     │ - Bug fixes      │ - Simple edits              │
│ - System-wide tasks    │ - Code review    │ - Config changes            │
└────────────────────────┴──────────────────┴─────────────────────────────┘
```

### Implementation Checklist
- [ ] Assess task complexity (lines of code, decision points, context needed)
- [ ] Route to appropriate tier
- [ ] Use Codex (medium) for simple tasks (1-2) via Bash with `codex exec --full-auto`
- [ ] Use Sonnet for moderate tasks (3) via Task tool
- [ ] Use Codex (xhigh) for complex tasks (4-5) via Bash with `codex -c 'model_reasoning_effort="xhigh"' exec --full-auto`

**Reference**: `.claude/commands/execute.md` (model selection), `.claude/commands/code-review.md` (uses Codex)

---

## Built-in Pattern: Downstream Effects Analysis

This pattern ensures changes are evaluated for ripple effects before implementation.

### When to Use
- During bug investigation (what breaks when we fix this?)
- During feature exploration (what depends on the code we're changing?)
- During PRD creation (what systems are affected by this feature?)
- Before any significant refactoring

### Analysis Structure
```yaml
downstream_effects:
  - file: "path/to/file.ext:line"
    impact: "What breaks if this changes"
    likelihood: "HIGH / MEDIUM / LOW"
  - file: "path/to/consumer.ext:line"
    impact: "Consumers/dependents affected"
    likelihood: "HIGH / MEDIUM / LOW"
```

### Questions to Ask
1. **Who consumes this API/function/data?** - Search for imports and references
2. **What tests cover this code?** - Check test files for dependencies
3. **What features depend on current behavior?** - Review related user flows
4. **What breaks if we change the contract?** - Consider interface changes
5. **What needs updating if we modify this?** - Documentation, configs, related code

### Implementation Checklist
- [ ] Search codebase for references to changed code
- [ ] Identify direct consumers (imports, function calls)
- [ ] Identify indirect consumers (data dependencies, shared state)
- [ ] Assess likelihood of breakage (HIGH/MEDIUM/LOW)
- [ ] Document effects in exploration context
- [ ] Include in fix options or implementation plan

**Reference**: `.claude/commands/bugs.md`, `.claude/commands/feature.md`, `.claude/commands/prd.md`

---

## Built-in Pattern: Debate Orchestration

Multi-model debate system for holistic analysis of complex decisions.

### When to Use
- Complex architectural decisions with multiple valid approaches
- Feature prioritization requiring different perspectives
- Risk assessment needing comprehensive coverage
- Technical strategy planning
- Any decision where "it depends" is the honest answer

### Debate Structure
```
Phase 1: Input + Context
  ├─ Parse topic and create debate directory
  ├─ Load project context from .ai/ if available
  └─ Optionally run Explore agent for codebase context

Phase 2: Clarify (1 round)
  ├─ Ask 2-4 questions about decision, constraints, success criteria
  └─ Write brief.md and lock it

Phase 3: Agent Array
  ├─ Analyst A: Claude (Task tool, Sonnet)
  └─ Analyst B: Codex (Bash, codex exec --full-auto)

Phase 4: Round 1 (Parallel)
  ├─ Both agents analyze independently
  └─ Write state.md with Round 1 responses

Phase 5: Rounds 2-3 (Sequential Cross-Examination)
  ├─ Each agent sees all previous responses
  ├─ Concede valid points, challenge disagreements
  └─ Add new evidence and refine positions

Phase 6: Synthesis (Orchestrator)
  ├─ Consensus points
  ├─ Key divergences
  ├─ Recommendation
  ├─ Validation steps
  └─ Action plan

Phase 7: Output
  └─ Assemble debate.md with all sections
```

### Output Files
```
debates/{topic-slug}/
  ├─ brief.md          # Decision context and constraints
  ├─ state.md          # All rounds with agent responses
  └─ debate.md         # Complete debate with synthesis
```

### Implementation Checklist
- [ ] Parse topic and generate slug
- [ ] Clarify decision with user (mandatory)
- [ ] Spawn agents in parallel for Round 1
- [ ] Append all responses to state.md
- [ ] Run cross-examination rounds sequentially
- [ ] Synthesize findings (orchestrator, not agents)
- [ ] Assemble final debate.md
- [ ] Handle Codex failures (fallback to Claude-haiku)

### Error Handling
- **Codex unavailable**: Fall back to Claude-haiku as Analyst B
- **Agent timeout**: Ask user to continue or retry
- **State file corruption**: Reconstruct from memory

**Reference**: `.claude/commands/debate.md`, `.claude/agents/debate-agent.md`

---

## Built-in Pattern: Parallel Model Orchestration

This pattern enables parallel execution of multiple AI models with finding merge and deduplication.

### When to Use
- Code review requiring maximum coverage (catch more issues via diverse perspectives)
- Analysis benefiting from model diversity (different strengths surface different insights)
- Quality assurance where convergent findings indicate high confidence
- Situations where single-model blind spots could miss critical issues

### Architecture Structure
```
Orchestrator (code-review.md)
    ↓
Parallel Spawn
    ├─ Claude (Opus) via Task tool → JSON output
    └─ Codex via Bash → JSON output
    ↓
Merge Phase
    ├─ Deduplicate findings (hash-based)
    ├─ Tag convergent findings (both models)
    └─ Tag single-model findings (claude|codex)
    ↓
Output
    └─ Merged findings with confidence indicators
```

### JSON Schema (Standardized Output)
```json
{
  "findings": [
    {
      "id": "CR-001",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "category": "Security|Architecture|Pattern|Quality|Testing|Performance|ErrorHandling|Documentation",
      "location": "path/to/file.ext:123-145",
      "issue": "Description of the issue",
      "why_matters": "Impact if not fixed",
      "evidence": "Code snippet showing the problem",
      "recommended_fix": "How to fix it",
      "task_description": "Task-ready description",
      "source": "claude|codex|both",
      "confidence": "convergent|single-model"
    }
  ]
}
```

### Deduplication Algorithm
```python
def finding_hash(finding):
    """Hash findings for deduplication"""
    location = normalize(finding["location"])  # file:line-range
    issue_start = normalize(finding["issue"][:50])
    return hash(
        finding["severity"] +
        finding["category"] +
        location +
        issue_start
    )

def normalize(text):
    """Lowercase and remove whitespace"""
    return text.lower().replace(" ", "")
```

**Merge Rules:**
1. Same hash in both outputs → keep one, mark `source: "both"`, `confidence: "convergent"`
2. Hash only in Claude output → mark `source: "claude"`, `confidence: "single-model"`
3. Hash only in Codex output → mark `source: "codex"`, `confidence: "single-model"`
4. Similar but not identical (same file:line, different severity) → keep both, mark as related

### Implementation Checklist
- [ ] Define standardized JSON output schema for all models
- [ ] Implement parallel spawning (Task tool for Claude, Bash for Codex)
- [ ] Write temp files for each model's output
- [ ] Implement deduplication hash function
- [ ] Merge findings and tag with source/confidence
- [ ] Handle model failure gracefully (fall back to single model)
- [ ] Present findings with convergent indicators

### Error Handling
- **Codex unavailable**: Fall back to Claude-only mode, mark all findings `source: "claude"`
- **Claude failure**: Fall back to Codex-only mode (rare, Task tool is reliable)
- **Both fail**: Exit with error and suggest manual review
- **Parse error**: Log raw output, skip that model's findings

### User Triage Integration

After merge, route findings by severity:
- **CRITICAL/HIGH**: Offer auto-fix immediately
- **MEDIUM/LOW**: User triage loop (fix now, tech debt, skip)

**Triage Loop Pattern:**
```
For each MEDIUM/LOW finding:
  Present: severity, source, confidence, location, issue, fix
  Ask: "1. Fix now | 2. Tech debt | 3. Skip"
  Based on response:
    - Fix now → add to /tmp/code-review-fixes.json
    - Tech debt → add to /tmp/tech-debt-additions.json
    - Skip → continue to next finding
```

After triage:
1. Batch-fix all "fix now" findings via Codex
2. Append all "tech debt" findings to TECH_DEBT.md with source attribution

**Reference**: `.claude/commands/code-review.md`, `.claude/agents/code-review-agent.md`

---

## Built-in Pattern: CTO Decision Framework

Commands adopt CTO personality and values for autonomous technical decision-making.

### When to Use
- PRD creation requiring architectural choices
- Bug investigation requiring complexity assessment
- Feature analysis requiring design decisions
- Execute orchestration requiring triage decisions

### Pattern Structure
```yaml
# In command frontmatter or early sections
## CTO Decision-Making Framework

Read .claude/agents/cto.md and adopt its decision-making framework.
Make technical decisions using CTO values. Escalate only per CTO escalation criteria.

### Decision Authority

**CTO DECIDES (no user interruption):**
- [List of autonomous decision types for this command]

**CTO ESCALATES to user:**
- Fixes affecting other people's workflows
- Recurring costs above ~$20/month
- Commitments creating external lock-in
- Scope changes redefining the project
- Genuine value conflicts
- Less than 70% confidence AND significant downside if wrong
```

### CTO Values (Summary)
- **People above all else**: Happy people → everything else follows
- **Do it right now**: Front-load effort, fix all issues (not just critical)
- **Simple > clever**: Minimum complexity for current need
- **The power of the "and"**: Look for synthesis before accepting either/or
- **Honest uncertainty over confident guessing**: <95% certain → say so
- **Question everything**: Challenge assumptions (including user's)
- **Speak up when something isn't right**: Make the point approachable, but make it

### Implementation Checklist
- [ ] Read `.claude/agents/cto.md` at command startup
- [ ] Add "CTO Decision-Making Framework" section to command
- [ ] Define Decision Authority (what CTO decides vs escalates)
- [ ] Apply CTO values when making technical choices
- [ ] Log decisions with rationale in STATE.md or command output
- [ ] Fallback to existing behavior if cto.md missing

### Error Handling
- If `.claude/agents/cto.md` not found: Log warning, continue with conservative escalation
- If CTO personality conflicts with command constraints: Command constraints win

**Reference**: `.claude/agents/cto.md`, `.claude/commands/prd.md`, `.claude/commands/bugs.md`, `.claude/commands/feature.md`, `.claude/commands/execute.md`

---

## Built-in Pattern: CTO Code Review Triage

Autonomous triage of code review findings with fix agent spawning.

### When to Use
- Post-execution in `/execute` command after all waves complete
- Code review returns findings that need action
- Want to eliminate user interruption for routine fixes

### Pattern Structure
```python
# After code review completes
findings = parseCodeReview(output)

FOR each finding in findings:
  IF severity == CRITICAL OR severity == HIGH:
    decision = "FIX_NOW"  # No CTO input needed, always fix
  ELSE IF severity == MEDIUM:
    decision = cto_decide(finding, context="delivery_risk")
  ELSE IF severity == LOW:
    decision = cto_decide(finding, context="maintainability")

  LOG to STATE.md:
    - Finding: {severity} {title} ({file}:{line})
      Decision: {decision}
      Action: {fix_agent_id | deferred_note | tech_debt_note}
      Rationale: {cto_reasoning}

  IF decision == "FIX_NOW":
    spawn_execution_agent(finding.recommended_fix)
    verify_fix(finding.location)
```

### CTO Decision Criteria
- **FIX_NOW**: Issue creates delivery risk or technical debt multiplier
- **DEFER**: Can wait until touching related code
- **SKIP_TECH_DEBT**: Signal-to-noise ratio too low, skip and log

### Implementation Checklist
- [ ] Parse code review findings into severity buckets
- [ ] Auto-fix all CRITICAL/HIGH findings
- [ ] Invoke CTO for MEDIUM/LOW triage decisions
- [ ] Log all triage decisions in STATE.md with rationale
- [ ] Spawn execution-agent per fix (same as wave tasks)
- [ ] Verify each fix via original task verify command
- [ ] Escalate if >3 fix agents fail or any CRITICAL fix fails

### Error Handling
- **Fix agent fails**: Log failure, continue triage, escalate if CRITICAL
- **>3 fix agents fail**: Escalate entire review with consolidated analysis
- **Verify command fails**: Re-run fix agent with failure context

**Reference**: `.claude/commands/execute.md` (post-execution steps), `.claude/agents/cto.md`

---

## Built-in Pattern: Autonomous Orchestration

Python orchestrator drives PM-PL cycles for autonomous project execution.

### When to Use
- Multi-sprint projects with defined outcomes
- Want autonomous progress without human intervention
- Need structured state tracking across sprints
- Want parallel sprint execution for independent work

### Pattern Structure
```
orchestrator.py (Python, stdlib-only)
    ↓
Resolve project slug (--project flag, or auto-detect via tasks/*/OUTCOMES.md)
    ↓
_project_tasks_dir(project_dir, slug) = tasks/{slug}/
    ↓
Read tasks/{slug}/ROADMAP.md (sprint state)
    ↓
Invoke PM agent with OUTCOMES_PATH and ROADMAP_PATH as absolute context vars
    ↓
PM signals next_task or parallel_tasks (PRDs at tasks/{slug}/{sprint}/prd.md)
    ↓
For each sprint:
    - Create git branch sprint/{sprint-name}
    - Invoke PL agent with SPRINT_PRD=tasks/{slug}/{sprint}/prd.md
    - PL derives all paths from dirname("$SPRINT_PRD")
    - PL: TaskGen → Execute → commit → merge
    - PL signals sprint_result (success/error)
    - Update tasks/{slug}/ROADMAP.md with status
    ↓
On PM completed: archive tasks/{slug}/ → tasks/archive/{slug}-{date}/
Loop until PM signals completed or blocked
```

### Key Components

**orchestrator.py:**
- Python 3 stdlib only (no pip dependencies)
- Filesystem is truth, sessions are disposable
- Structured signal parsing (YAML blocks)
- `--project slug` CLI arg; auto-detected from `tasks/*/OUTCOMES.md` if one project
- `_project_tasks_dir(project_dir, slug)` is the single path-resolution helper
- Slug constraint: `[a-z0-9]+(-[a-z0-9]+)*`, max 64 chars
- Git branch management per sprint
- Parallel PL execution for independent sprints
- Two-phase merge (--no-commit, then commit or abort)

**PM Agent (.claude/agents/pm.md):**
- Plans sprints from OUTCOMES_PATH and ROADMAP_PATH (absolute paths in context)
- Writes just-in-time PRDs to `dirname(ROADMAP_PATH)/{sprint}/prd.md`
- Never hardcodes `tasks/` — paths always derived from context vars
- Outputs structured signals (next_task, parallel_tasks, completed, blocked, halt)
- Values-driven planning decisions

**PL Agent (.claude/agents/pl.md):**
- Receives SPRINT_PRD as absolute path; derives ALL paths via `dirname("$SPRINT_PRD")`
- Log file: `$(dirname "$SPRINT_PRD")/pl-session.log`
- Task XML: `$(dirname "$SPRINT_PRD")/task.xml`
- Runs TaskGen → Execute → commits
- Outputs sprint_result signals
- Values-driven execution decisions

**ROADMAP.md (tasks/{slug}/ROADMAP.md):**
- Single source of truth for sprint state
- Fields: sprint name, target outcome, status, PRD path, branch, summary
- Updated by PM and orchestrator

### Implementation Checklist
- [ ] Run /outcomes to create `tasks/{slug}/OUTCOMES.md` (derives slug from project name)
- [ ] Run /orchestrate (auto-detects slug via `find tasks -mindepth 2 -maxdepth 2 -name OUTCOMES.md`)
- [ ] /orchestrate passes `--project {slug}` to orchestrator.py
- [ ] Orchestrator checks for VALUES.md (graduated warning if missing)
- [ ] PM creates/updates `tasks/{slug}/ROADMAP.md` with sprint plan
- [ ] PM signals next sprint(s); PRDs at `tasks/{slug}/{sprint}/prd.md`
- [ ] Orchestrator creates sprint/* branches
- [ ] PL executes sprints with paths from SPRINT_PRD, commits code, signals results
- [ ] Orchestrator archives `tasks/{slug}/` on PM completed signal
- [ ] Loop continues until PM signals completed or blocked

### Error Handling
- **PM signal parse failure**: Retry once, then halt with error
- **PL execution failure**: Mark sprint as blocked, continue to next sprint
- **Git merge conflict**: Abort merge, mark sprint as blocked, notify user
- **Stuck detection**: Same sprint name 3 times in sequence → halt
- **SIGINT (Ctrl+C)**: Graceful shutdown, preserve state in ROADMAP.md
- **Invalid slug**: Halt with error explaining slug format constraint

### Graduated Warning Flow (VALUES.md)
```
orchestrator.py startup:
  ├─ Check ~/.claude/VALUES.md exists
  │
  ├─ If missing:
  │   ├─ Warn: "VALUES.md not found. Agents will use generic mode."
  │   ├─ Recommend: "Run /values-discovery to create personalized values profile."
  │   ├─ Prompt: "Continue without values? (y/n)"
  │   │   ├─ No → Exit
  │   │   └─ Yes → Confirm: "Agents will use conservative generic judgments. Proceed? (y/n)"
  │   │       ├─ No → Exit
  │   │       └─ Yes → Proceed in generic mode
  │   └─
  └─ If found: Load and proceed
```

**Reference**: `orchestrator.py`, `.claude/agents/pm.md`, `.claude/agents/pl.md`, `templates/ROADMAP.md`

---

## Built-in Pattern: Tmux Background Orchestration

Launch long-running autonomous processes in tmux sessions that survive context exhaustion.

### When to Use
- Long-running autonomous orchestration (PM-PL cycles)
- Want process to survive Claude Code session ending
- Need to attach/detach from running process
- Want to view progress without interrupting execution

### Pattern Structure
```
Command checks prerequisites
    ↓
Launch in tmux background session
    ↓
Verify session started
    ↓
Return to user immediately
    ↓
Session runs independently
    ↓
User can attach/detach anytime
```

### Implementation Checklist
- [ ] Check if tmux is installed
- [ ] Check if session already exists (offer attach/kill/cancel)
- [ ] Build command with proper logging
- [ ] Launch in detached tmux session with descriptive name
- [ ] Verify session started successfully
- [ ] Provide attach/monitor/shutdown instructions
- [ ] Keep Claude Code session open (do NOT end conversation)

### Tmux Session Command Pattern
```bash
tmux new-session -d -s {session-name} "{command} 2>&1 | tee {log-file}; echo '--- Process exited. Press Enter to close. ---'; read"
```

### User Instructions Template
```
{Process} started successfully.

It's running in the background as a tmux session -- it will keep running even if you close this Claude Code session.

To view it from any terminal:
  tmux attach -t {session-name}

Other useful commands:
  tail -f {log-file}                          # Follow the log without attaching
  tmux send-keys -t {session-name} C-c        # Graceful shutdown (saves state)
  tmux kill-session -t {session-name}         # Force kill

To resume after stopping:
  {resume-instructions}
```

### Error Handling
- **tmux not installed**: suggest installation or fall back to Bash run_in_background
- **session exists**: offer attach/kill/cancel options
- **session fails to start**: read log file and report error
- **process not found**: provide installation instructions

### Important Notes
- After launching, remain in Claude Code session (do NOT end conversation)
- User may want to continue working while background process runs
- Background process survives context window exhaustion
- Tmux session persists across terminal sessions

**Reference**: `.claude/commands/orchestrate.md`

---

## Built-in Pattern: Values-Driven Agent Boot

Agents load ~/.claude/VALUES.md for personalized decision-making, gracefully degrade if missing.

### When to Use
- Agent needs to make value-driven decisions (priorities, trade-offs, quality thresholds)
- Want personalized behavior aligned to user's values
- Need graceful degradation if values not available

### Pattern Structure
```yaml
# In agent frontmatter or Boot Sequence section

## Boot Sequence

### Step 1: Load Values

Read ~/.claude/VALUES.md if it exists.

- **If found**: These are your values -- not guidelines to consider, but how you think and decide. Apply them to all decisions: what to prioritize, how to sequence work, quality vs speed trade-offs, when to flag uncertainty, and what "done" means.
- **If NOT found**: Log WARNING. Operating in generic mode. Make conservative decisions. Lower confidence threshold (~60% vs ~70%). Do NOT refuse to work -- the user has chosen to proceed without values.

**IMPORTANT**: Missing VALUES.md is NOT a blocker. The orchestrator has already warned the user and received consent to proceed. You note it and continue in generic mode.
```

### Generic Mode Behavior
- Use conservative professional judgment
- Escalate more frequently (lower confidence threshold to ~60% instead of ~70%)
- Prefer correctness over speed when ambiguous
- Prefer doing less well over doing more poorly
- Note in first output: "Operating without values profile -- recommend running /values-discovery"

### Implementation Checklist
- [ ] Add "Load Values" step to agent boot sequence
- [ ] Check if ~/.claude/VALUES.md exists
- [ ] If found: load values, adopt decision framework
- [ ] If NOT found: log WARNING, switch to generic mode
- [ ] Do NOT block or refuse to work if missing
- [ ] Apply values (or generic mode) to all decision points

### Error Handling
- **VALUES.md corrupt/unparseable**: Log warning, fall back to generic mode
- **VALUES.md exists but empty**: Treat as missing, use generic mode
- **User cancels values-discovery**: Continue in generic mode (no retry loop)

**Reference**: `.claude/agents/cto.md`, `.claude/agents/pm.md`, `.claude/agents/pl.md`

---

## Built-in Pattern: Structured Output Protocol

Agents output YAML signal blocks between ---ORCHESTRATOR_SIGNAL--- markers for reliable machine parsing.

### When to Use
- Orchestrator needs to parse agent output programmatically
- Need reliable control flow between orchestrator and agents
- Want structured error handling and blocking conditions
- Supporting parallel task execution

### Signal Format
```yaml
---ORCHESTRATOR_SIGNAL---
action: next_task | parallel_tasks | completed | blocked | halt | sprint_result
# ... action-specific fields
---ORCHESTRATOR_SIGNAL---
```

### PM Agent Signals

**next_task** (single sprint):
```yaml
---ORCHESTRATOR_SIGNAL---
action: next_task
sprint_name: "auth-service"
target_outcome: "User Authentication"
prd_path: "tasks/{slug}/auth-service/prd.md"
branch: "sprint/auth-service"
---ORCHESTRATOR_SIGNAL---
```

**parallel_tasks** (multiple independent sprints):
```yaml
---ORCHESTRATOR_SIGNAL---
action: parallel_tasks
sprints:
  - sprint_name: "api-layer"
    target_outcome: "API Foundation"
    prd_path: "tasks/{slug}/api-layer/prd.md"
    branch: "sprint/api-layer"
  - sprint_name: "db-schema"
    target_outcome: "Data Persistence"
    prd_path: "tasks/{slug}/db-schema/prd.md"
    branch: "sprint/db-schema"
---ORCHESTRATOR_SIGNAL---
```

**completed** (all work done):
```yaml
---ORCHESTRATOR_SIGNAL---
action: completed
message: "All outcomes achieved. Project complete."
---ORCHESTRATOR_SIGNAL---
```

**blocked** (cannot proceed):
```yaml
---ORCHESTRATOR_SIGNAL---
action: blocked
reason: "OUTCOMES.md missing critical acceptance criteria for outcome 3."
needs: "User input to clarify success criteria."
---ORCHESTRATOR_SIGNAL---
```

**halt** (graceful shutdown):
```yaml
---ORCHESTRATOR_SIGNAL---
action: halt
reason: "User requested shutdown."
---ORCHESTRATOR_SIGNAL---
```

### PL Agent Signals

**sprint_result** (sprint execution complete):
```yaml
---ORCHESTRATOR_SIGNAL---
action: sprint_result
status: success | error
summary: "Sprint completed: auth service implemented, 15 tests passing, merged to main."
---ORCHESTRATOR_SIGNAL---
```

### Implementation Checklist
- [ ] Define signal schema for orchestrator and agents
- [ ] Agents output YAML between ---ORCHESTRATOR_SIGNAL--- markers
- [ ] Orchestrator parses signals with regex extraction
- [ ] Validate required fields present
- [ ] Handle parse failures (retry once, then halt)
- [ ] Log all signals to orchestrator.log

### Error Handling
- **Signal missing**: Treat as error, retry agent call once
- **Signal malformed YAML**: Log parse error, retry once, then halt
- **Signal missing required fields**: Log validation error, halt
- **Multiple signals in one output**: Use first valid signal, warn about duplicates

**Reference**: `orchestrator.py`, `.claude/agents/pm.md`, `.claude/agents/pl.md`

---

## Built-in Pattern: Graph Engine Orchestration

DAG-based execution engine where nodes are typed, domain-appropriate, and checkpointed per step.

### When to Use
- Multi-step projects requiring typed execution nodes (task, discovery, gate, fan_out, fan_in)
- Need resumability: resume from last checkpoint if interrupted
- Want domain-appropriate handlers (software vs content vs discovery)
- Quality gates needed before downstream work begins

### Node Types
```
TASK       - Implementation work (SoftwareHandler or ContentHandler)
DISCOVERY  - Approach determination before implementation (DiscoveryHandler)
GATE       - Acceptance criteria evaluation (GoalGate, deterministic)
FAN_OUT    - Spawn parallel branches
FAN_IN     - Merge parallel branches
```

### Context Fidelity Modes
```
MINIMAL  - Only immediate upstream summary passed (default, token efficient)
PARTIAL  - Upstream summaries + key artifacts
FULL     - Complete upstream context passed
```

### Graph Definition Structure
```yaml
nodes:
  discover-approach:
    type: discovery
    node_class: discovery
    handler: discovery
    inputs:
      outcome_name: "Feature X"
  implement:
    type: task
    node_class: implementation
    handler: software
    context_fidelity: partial
  quality-gate:
    type: gate
    node_class: gate
    handler: gate
    criteria:
      - "output.status == completed"
      - "output.artifacts contains tests"
    max_retries: 3
    retry_target: implement
edges:
  - source: discover-approach
    target: implement
    condition: "status == completed"
  - source: implement
    target: quality-gate
    condition: always
```

### Implementation Checklist
- [ ] Define nodes with types and handler classes
- [ ] Map edges with conditions (always|status==completed|status==failed)
- [ ] Set context_fidelity per node (default: minimal)
- [ ] Configure model-stylesheet.yaml node classes
- [ ] Run orchestrator.py which auto-validates DAG and creates checkpoint
- [ ] Monitor via checkpoint.json for state inspection

**Reference**: `orchestrator.py`, `model-stylesheet.yaml`

---

## Built-in Pattern: Model Stylesheet

External YAML file defines model selection per node class with fallback chains. Decouples model assignment from orchestrator logic.

### When to Use
- Node needs a specific model tier (planning, implementation, review, gate)
- Want to tune cost/quality trade-offs without touching orchestrator code
- Need fallback resilience when a provider is unavailable

### Node Class Mapping
```yaml
# model-stylesheet.yaml
classes:
  planning:           # Claude Opus + xhigh reasoning (architecture decisions)
  implementation:     # Codex medium (code tasks, fast and efficient)
  implementation-complex:  # Codex xhigh (complex multi-file refactors)
  review:             # Claude Opus + xhigh (code review, quality assessment)
  gate:               # Claude Sonnet + medium (gate evaluation, deterministic)
  content-draft:      # Claude Opus + medium (writing tasks)
  discovery:          # Claude Opus + xhigh (complex approach decisions)
  discovery-simple:   # Claude Sonnet + medium (quick approach assessment)
  research:           # Claude Opus + xhigh (investigation tasks)
  default:            # Codex medium (unspecified node classes)
```

### Fallback Chain Pattern
```yaml
implementation:
  provider: openai
  model: gpt-5.3-codex
  reasoning_effort: medium
  tool_profile: codex
  timeout: 7200
  fallback:
    - provider: anthropic
      model: claude-sonnet-4-6
      reasoning_effort: medium
      tool_profile: claude
      timeout: 7200
```

### Implementation Checklist
- [ ] Assign node_class in graph definition
- [ ] Confirm class exists in model-stylesheet.yaml
- [ ] Set tool_profile correctly (claude for Anthropic, codex for OpenAI)
- [ ] Add fallback chain for resilience

**Reference**: `model-stylesheet.yaml`, `orchestrator.py` (ModelConfig, NodeHandler)

---

## Built-in Pattern: Discovery Node

Run a discovery phase to determine approach before implementation. Prevents wasted implementation effort on the wrong approach.

### When to Use
- Before any non-trivial implementation node
- When approach is ambiguous or has multiple valid options
- Complex domain problems needing research before coding

### Simple vs Complex Mode
```
Simple mode (complexity < threshold):
  - Quick approach assessment
  - Outputs: Approach + Rationale + Constraints
  - Model: discovery-simple class (Sonnet)

Complex mode (complexity >= threshold):
  - Deep investigation (/investigate tool)
  - Optional /debate for competing approaches
  - Outputs: Approach + Rationale + Constraints + Findings + Alternatives
  - Model: discovery class (Opus)
```

### Output: CONTEXT.md
```markdown
# Discovery: {Outcome Name}

## Approach
{Chosen method}

## Rationale
{Why selected}

## Constraints
{Known limitations}

## Investigation Findings
{Complex only}

## Alternatives Considered
{Complex only}
```

### Signal Format
```yaml
---ORCHESTRATOR_SIGNAL---
signal: done
summary: "Discovery complete: use REST API with JWT auth"
context_path: "tasks/{node-id}/CONTEXT.md"
complexity_used: "simple|complex"
---ORCHESTRATOR_SIGNAL---
```

**Reference**: `.claude/agents/discovery.md`, `orchestrator.py` (DiscoveryHandler)

---

## Built-in Pattern: Goal Gate Convergence

Deterministic acceptance criteria evaluation with retry routing before downstream nodes execute.

### When to Use
- Quality checkpoint before downstream work proceeds
- Ensure implementation meets defined criteria
- Prevent propagation of defects to dependent work

### Gate Criteria Syntax
```yaml
criteria:
  - "output.status == completed"           # Node status check
  - "output.artifacts contains tests"      # Artifact presence
  - "output.merge_success == true"         # Specific field value
  - "file:tasks/output.md exists"          # File existence check
```

### Retry Routing
```
Gate fails → retry_target node re-executed → gate re-evaluated
Max retries exceeded → escalate to user
```

### Gate Flow
```
Upstream node(s) complete
    ↓
GoalGate.evaluate(upstream_outcomes)
    ↓
All criteria pass? → COMPLETED (downstream proceeds)
Any fail? → FAILED
    ↓
Retry count < max_retries?
    Yes → re-run retry_target → re-evaluate gate
    No → ESCALATE to user with criteria failure details
```

### Implementation Checklist
- [ ] Define gate node in graph with criteria list
- [ ] Set retry_target (node to re-run on failure)
- [ ] Set max_retries (default: 3)
- [ ] Criteria should be deterministic (no LLM needed for evaluation)
- [ ] Use node_class: gate (routes to Sonnet medium, efficient)

**Reference**: `orchestrator.py` (GoalGate, GraphEngine)

---

## Built-in Pattern: Project Lead Orchestration

Project Lead drives sprints from OUTCOMES.md through PRD → TaskGen → Execute pipeline using agent teams for parallel work.

### When to Use
- Multi-sprint outcome-driven project work
- Want to delegate heavy pipeline work to protect context window
- Need structured state tracking (PROJECT_STATE.md, DECISIONS.md)

### Sprint Pipeline
```
/lead boot (load personality, state, briefing)
    ↓
Identify next sprint from OUTCOMES.md
    ↓
Propose sprint scope to Iain (confirm before PRD)
    ↓
/prd → PRD document
    ↓
/TaskGen → task XML
    ↓
/execute → code delivery
    ↓
Update PROJECT_STATE.md + DECISIONS.md
    ↓
Identify next sprint → repeat
```

### Decision Authority
```
Project Lead DECIDES:
  - Sprint sequencing and scope
  - Whether to use agent teams (TeamCreate) for parallel work
  - PRD and task review outcomes (proceed/adjust)
  - State file updates

Project Lead ESCALATES to Iain:
  - OUTCOMES.md modification requests (read-only)
  - Conflicts between outcomes
  - Blockers persisting after one recovery attempt
  - <70% confidence AND significant downside risk
```

### Context Window Protection
```python
# Protect context by delegating to sub-agents
# Instead of running PRD→Tasks→Execute inline, spawn an agent team
team = TeamCreate("sprint-N")
assign(teammate, "/prd context")
monitor_until_complete()
```

**Reference**: `.claude/commands/lead.md`, `.claude/agents/project-lead.md`

---

## Adding New Patterns

### 1. Create Domain File
```bash
cp .ai/patterns/_TEMPLATE.md .ai/patterns/[DOMAIN].md
```

### 2. Update This Index
- Add row to Pattern Domains table
- Add entries to Quick Pattern Lookup table

### 3. Pattern Format
Each pattern in domain files should have:
- **When to Use** - Trigger conditions
- **Template** - Copy-paste code
- **Checklist** - Implementation steps
- **Reference** - `FileName.ext:lineNumber`

---

## Token Efficiency

| Load | Tokens |
|------|--------|
| This index only | ~1,000 |
| Index + 1 domain file | ~3,500 |
| Index + 2 domain files | ~6,000 |

**Strategy**: Load index first, then only the domain file(s) you need.

---

## Maintenance

### After Each Sprint
- Add patterns discovered during implementation
- Update file:line references if code moved
- Remove patterns that didn't work well

### When Patterns Exceed ~400 Lines
- Split into more specific domain files
- Keep each domain file focused

---

*This is an index. Detailed patterns live in `patterns/[DOMAIN].md` files.*
