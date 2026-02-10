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
