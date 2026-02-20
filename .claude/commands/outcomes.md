---
description: Outcomes v2 state-machine orchestrator with XML phase tracking, resumability, and agent-team dispatch
---

# Outcomes v2 Command

**Objective:** Orchestrate outcomes setup as a resumable, phase-based pipeline backed by `tasks/outcomes-setup.xml`.

This command is an orchestrator:
- Delegate phase work to Task tool agents with fresh context.
- Persist progress in XML after each meaningful transition.
- Resume from the first incomplete phase on every invocation.
- Keep all handoffs file-based (input/output files only).

---

## Required References (Read First)

Before execution:
1. Read `~/.claude/agents/task-protocol.md`
2. Read `~/.claude/commands/execute.md` (XML and resumability patterns)
3. Read `~/.claude/commands/code-review.md` (parallel Task spawning pattern)

---

## 1) State File Contract (`tasks/outcomes-setup.xml`)

### File Location

- State file: `tasks/outcomes-setup.xml`
- Corrupt backups: `tasks/outcomes-setup.corrupt-<timestamp>.xml`

### Allowed Status Values

Use only:
- `not_started`
- `in_progress`
- `complete`
- `failed`

### Required XML Shape

```xml
<?xml version="1.0" encoding="UTF-8"?>
<outcomes_setup schema_version="1">
  <metadata>
    <created_at>2026-02-20T12:30:00Z</created_at>
    <last_updated_at>2026-02-20T12:30:00Z</last_updated_at>
    <project_path>/absolute/project/path</project_path>
  </metadata>

  <phases>
    <phase id="discovery" order="1" status="not_started">
      <started_at></started_at>
      <completed_at></completed_at>
      <failed_at></failed_at>
      <output_file>tasks/outcomes-draft.md</output_file>
      <summary></summary>
    </phase>

    <phase id="red-team" order="2" status="not_started">
      <started_at></started_at>
      <completed_at></completed_at>
      <failed_at></failed_at>
      <output_file>tasks/red-team/</output_file>
      <summary></summary>
      <agents>
        <agent id="paperclip-maximizer" status="not_started">
          <started_at></started_at>
          <completed_at></completed_at>
          <failed_at></failed_at>
          <attempts>0</attempts>
          <output_file>tasks/red-team/paperclip-maximizer.md</output_file>
          <last_error></last_error>
        </agent>
        <agent id="pre-mortem" status="not_started">
          <started_at></started_at>
          <completed_at></completed_at>
          <failed_at></failed_at>
          <attempts>0</attempts>
          <output_file>tasks/red-team/pre-mortem.md</output_file>
          <last_error></last_error>
        </agent>
        <agent id="boundary-tester" status="not_started">
          <started_at></started_at>
          <completed_at></completed_at>
          <failed_at></failed_at>
          <attempts>0</attempts>
          <output_file>tasks/red-team/boundary-tester.md</output_file>
          <last_error></last_error>
        </agent>
        <agent id="stakeholder-advocate" status="not_started">
          <started_at></started_at>
          <completed_at></completed_at>
          <failed_at></failed_at>
          <attempts>0</attempts>
          <output_file>tasks/red-team/stakeholder-advocate.md</output_file>
          <last_error></last_error>
        </agent>
        <agent id="specification-gamer" status="not_started">
          <started_at></started_at>
          <completed_at></completed_at>
          <failed_at></failed_at>
          <attempts>0</attempts>
          <output_file>tasks/red-team/specification-gamer.md</output_file>
          <last_error></last_error>
        </agent>
      </agents>
    </phase>

    <phase id="synthesis" order="3" status="not_started">
      <started_at></started_at>
      <completed_at></completed_at>
      <failed_at></failed_at>
      <output_file>tasks/red-team/synthesis.md</output_file>
      <summary></summary>
    </phase>

    <phase id="context" order="4" status="not_started">
      <started_at></started_at>
      <completed_at></completed_at>
      <failed_at></failed_at>
      <output_file>tasks/CONTEXT.md</output_file>
      <summary></summary>
    </phase>

    <phase id="refinement" order="5" status="not_started">
      <started_at></started_at>
      <completed_at></completed_at>
      <failed_at></failed_at>
      <output_file>tasks/outcomes-refined.md</output_file>
      <summary></summary>
    </phase>

    <phase id="finalize" order="6" status="not_started">
      <started_at></started_at>
      <completed_at></completed_at>
      <failed_at></failed_at>
      <output_file>tasks/OUTCOMES.md</output_file>
      <summary></summary>
    </phase>
  </phases>
</outcomes_setup>
```

### Phase Order (Source of Truth)

1. `discovery`
2. `red-team`
3. `synthesis`
4. `context`
5. `refinement`
6. `finalize`

---

## 2) Initialization, Read, Parse, and Atomic Update

### First Invocation (File Missing)

If `tasks/outcomes-setup.xml` does not exist:
1. Ensure `tasks/` exists.
2. Create the XML file with all phase and red-team agent statuses set to `not_started`.
3. Set both `metadata.created_at` and `metadata.last_updated_at` to current ISO-8601 timestamp.
4. Set `metadata.project_path` to current working directory.

### Existing File (Read + Validate)

1. Read `tasks/outcomes-setup.xml`.
2. Attempt XML parse.
3. Validate required structure:
- `<outcomes_setup>`
- `<metadata>` with `created_at`, `last_updated_at`, `project_path`
- `<phases>` with all six required phase IDs
- `<agents>` for `red-team`

If validation fails, treat as corrupt.

### Corrupt/Malformed XML Handling

On parse/validation failure:
1. Create backup: `tasks/outcomes-setup.corrupt-<YYYYMMDDTHHMMSSZ>.xml`
2. Preserve exact original bytes in backup.
3. Display clear error with parse/validation reason.
4. Offer:
- `(1) Start fresh with new outcomes-setup.xml`
- `(2) Cancel`
5. Only create a fresh file if user selects `(1)`.

### Atomic Write Rule (Mandatory)

All updates to `tasks/outcomes-setup.xml` must be atomic:
1. Render full XML content in memory.
2. Write to temporary file in same directory: `tasks/outcomes-setup.xml.tmp`
3. Flush write completely.
4. Rename temp file over target (`rename`/move in same filesystem).
5. Update `metadata.last_updated_at` on every write.

Never edit the XML in-place.

---

## 3) Phase State Transitions and Resume Logic

### Transition Rules

When a phase starts:
- Set phase status to `in_progress`
- Set `started_at` if empty

When a phase succeeds:
- Set phase status to `complete`
- Set `completed_at`
- Set concise `summary`
- Keep `output_file` path current

When a phase fails:
- Set phase status to `failed`
- Set `failed_at`
- Write reason into `summary`

### Red-Team Agent Transitions

Per agent:
- Start: `status="in_progress"`, set `started_at` if empty
- Success: `status="complete"`, set `completed_at`, clear `last_error`
- Failure attempt: increment `<attempts>`
- Final failure after retry: `status="failed"`, set `failed_at`, set `last_error`

### Resume Selection

On each invocation:
1. Load XML state.
2. Find first phase in canonical order where `status != "complete"`.
3. Resume from that phase.
4. Skip phases already `complete`.

If all phases are `complete`, display completion status and exit.

### Red-Team Resume Behavior

When resuming `red-team`:
- Spawn agents with status `not_started`, `in_progress`, or `failed` where `<attempts> < 2`.
- Do not rerun agents already `complete`.
- Do not rerun agents with `failed` status and `<attempts> >= 2` unless user explicitly resets them.
- For agents with `failed` status and `<attempts> < 2`, resume selection must include them for mandatory retry.

---

## 4) Status Display (Every Invocation)

Before executing work, print a scannable status block:

```text
Outcomes Pipeline Status

Completed:
- discovery: complete at 2026-02-20T13:01:22Z (elapsed 00:04:12)

Current:
- red-team: in_progress (started 2026-02-20T13:01:23Z)

Red-Team Agents:
- paperclip-maximizer: complete (attempts 1)
- pre-mortem: in_progress (attempts 1)
- boundary-tester: failed (attempts 2)
- stakeholder-advocate: not_started
- specification-gamer: not_started

Remaining:
- synthesis
- context
- refinement
- finalize
```

Display requirements:
- Show completed phases with timestamps and elapsed duration.
- Show current phase and status.
- Show remaining phases.
- For `red-team`, always show per-agent status and attempts.

---

## 5) Agent Teams Dispatch Contract

Use Task tool agents with fresh context for each phase.

### File-Based Handoff Rule

Pass only explicit input files required for each phase:
- `discovery`: input context + user responses; output `tasks/outcomes-draft.md`
- `red-team`: input `tasks/outcomes-draft.md`; outputs `tasks/red-team/*.md`
- `synthesis`: input red-team outputs; output `tasks/red-team/synthesis.md`
- `context`: input draft+synthesis+memory files; output `tasks/CONTEXT.md`
- `refinement`: input synthesis+context+draft; output `tasks/outcomes-refined.md`
- `finalize`: input refined outputs; outputs `tasks/OUTCOMES.md`, `tasks/PROJECT_STATE.md`, `tasks/DECISIONS.md`

Do not grant broad implicit project context to agents when explicit file inputs are sufficient.

### Single-Agent Phases

For non-red-team phases, spawn one Task call per phase with:
- phase objective
- strict input file list
- required output file path
- completion criteria

Pattern:

```text
Task(
  subagent_type: "general-purpose",
  prompt: """
  Phase: {phase_id}
  Inputs (read-only):
  - {explicit input files only}

  Required output:
  - {single phase output file}

  Return:
  - completion summary
  - failure reason if any
  """
)
```

### Red-Team Parallel Spawn

For `red-team`, dispatch all incomplete agents in parallel Task calls in a single batch.

Use lens-specific prompts and fixed outputs:
- `paperclip-maximizer` -> `tasks/red-team/paperclip-maximizer.md`
- `pre-mortem` -> `tasks/red-team/pre-mortem.md`
- `boundary-tester` -> `tasks/red-team/boundary-tester.md`
- `stakeholder-advocate` -> `tasks/red-team/stakeholder-advocate.md`
- `specification-gamer` -> `tasks/red-team/specification-gamer.md`

Pattern:

```text
parallel([
  Task(...paperclip-maximizer...),
  Task(...pre-mortem...),
  Task(...boundary-tester...),
  Task(...stakeholder-advocate...),
  Task(...specification-gamer...)
])
```

### Retry-on-Failure Policy (Mandatory)

Per agent (including non-red-team phase agents):
1. Attempt once.
2. If failed, retry exactly one time.
3. If retry succeeds, mark `complete`.
4. If retry fails, mark `failed` and persist error details.

Always persist state after each attempt using atomic XML write.

---

## 6) Output Validation Before Marking Complete

Before setting any phase/agent to `complete`:
1. Verify expected output file exists.
2. Verify file is non-empty.
3. Record concise summary in XML.

If validation fails:
- Treat as failure
- Apply retry policy

---

## 7) Operational Guardrails

- Never lose state: every status change must be written atomically.
- Never skip phase order unless a phase is already `complete`.
- Never mark phase `complete` without validated output.
- Never overwrite corrupt XML without first creating a backup.
- Always show status before doing work.

This command establishes the outcomes-v2 orchestration foundation around `tasks/outcomes-setup.xml`.

---

## 8) Discovery Phase Agent Contract (Interactive)

The `discovery` phase is interactive and must run in conversational rounds while persisting progress to `tasks/outcomes-draft.md`.

### Discovery Start/Resume Rules

When `discovery` is selected as the first incomplete phase:
1. If phase status is `not_started`, set it to `in_progress` and set `started_at` (if empty).
2. If phase status is already `in_progress`, attempt resume from `tasks/outcomes-draft.md`.
3. If a partial draft exists, count currently defined outcomes across primary/secondary/stretch and display:
   - `Resuming discovery. We had X outcomes defined.`
4. Keep `discovery` status as `in_progress` until completion validation passes.

### Questioning Cadence (Mandatory)

- Ask at most 3 questions per batch.
- Start open, then progressively refine.
- Push back on vague answers; require concrete, testable language.
- Typical flow is 5-7 total questions, but continue if clarity is still missing.

Round flow:
1. Round 1 (Open Context Gathering):
   - Understand problem, users/stakeholders, desired change, and why now.
2. Round 2 (Outcome Extraction and Proposal):
   - Propose candidate outcomes grouped as `primary`, `secondary`, and `stretch`.
   - Ask user to confirm, reorder, merge, or split outcomes.
3. Round 3+ (Refinement):
   - Tighten scope, constraints, non-goals, and measurable success criteria.
   - Resolve ambiguity before completion.

### Vagueness Pushback Rule

Do not accept soft wording such as "better", "faster", "improve quality", or "user-friendly" without measurable definition.

If vague, ask targeted follow-up (max 3 questions/batch), for example:
- "What numeric target defines success?"
- "By when should this be achieved?"
- "How will we verify this outcome is complete?"

### Outcome Categorization and Quality Gates

For every outcome captured:
- Required fields:
  - `name`
  - `description`
  - at least 1 measurable `success criterion`
- Category must be one of:
  - `primary` (must-have, required to declare project success)
  - `secondary` (valuable but not critical)
  - `stretch` (aspirational, pursued only if capacity allows)

Completion minimums:
- At least 1 `primary` outcome is mandatory.
- Every listed outcome must include at least 1 measurable success criterion.

### Discovery Draft Output (`tasks/outcomes-draft.md`)

Discovery writes/updates `tasks/outcomes-draft.md` throughout the session using this structure:

```markdown
# Outcomes Draft
<!-- discovery_status: in_progress|complete -->

## Project Summary
[1-2 sentence summary of the project and intent]

## Primary Outcomes
### Outcome P1: [Name]
**Description:** [What success looks like]
**Success Criteria:**
- [ ] [Measurable criterion with observable threshold]

## Secondary Outcomes
### Outcome S1: [Name]
**Description:** [Value delivered]
**Success Criteria:**
- [ ] [Measurable criterion]

## Stretch Outcomes
### Outcome X1: [Name]
**Description:** [Aspirational value]
**Success Criteria:**
- [ ] [Measurable criterion]

## Initial Constraints
- [Specific constraint, boundary, or limitation]

## Non-Goals
- [Explicitly out of scope]
```

Required sections for completion gating:
- `Project Summary`
- `Primary Outcomes`
- `Secondary Outcomes`
- `Initial Constraints`
- `Non-Goals`

`Stretch Outcomes` is optional but recommended when useful.

### Partial Save and Abandonment Handling

If user cancels or abandons mid-discovery:
1. Persist latest structured draft to `tasks/outcomes-draft.md`.
2. Include incomplete marker:
   - `<!-- discovery_status: in_progress -->`
3. Preserve whatever is known (even partial outcomes/constraints/non-goals).
4. Keep XML `discovery` phase status as `in_progress`.
5. Update discovery summary with partial counts (for resume visibility).

### Discovery Completion Signaling to Orchestrator

Before marking discovery `complete`, validate:
1. `tasks/outcomes-draft.md` exists.
2. `tasks/outcomes-draft.md` is non-empty.
3. At least 1 primary outcome exists.
4. Every outcome includes at least 1 measurable success criterion.

If validation passes:
1. Write final draft marker:
   - `<!-- discovery_status: complete -->`
2. Update XML phase `discovery`:
   - `status="complete"`
   - set `completed_at` timestamp
   - set summary, e.g. `3 primary outcomes, 2 secondary, 1 stretch, 5 constraints`
3. Persist XML atomically.
4. Proceed to next phase (`red-team`).

If validation fails:
- Keep `discovery` as `in_progress`.
- Continue questioning/refinement until criteria are met or user cancels.

---

## 9) Red-Team Phase Agent Contracts (5 Adversarial Lenses)

The `red-team` phase stress-tests `tasks/outcomes-draft.md` using five independent adversarial lenses.

### Red-Team Inputs, Outputs, and Setup

- Allowed input for each lens: `tasks/outcomes-draft.md` only.
- Pre-spawn setup: create output directory with `mkdir -p tasks/red-team`.
- Fixed outputs:
  - `paperclip-maximizer` -> `tasks/red-team/paperclip-maximizer.md`
  - `pre-mortem` -> `tasks/red-team/pre-mortem.md`
  - `boundary-tester` -> `tasks/red-team/boundary-tester.md`
  - `stakeholder-advocate` -> `tasks/red-team/stakeholder-advocate.md`
  - `specification-gamer` -> `tasks/red-team/specification-gamer.md`

### Lens A: Paperclip Maximizer (`paperclip-maximizer`)

Purpose:
- Identify how seemingly valid outcomes could be over-optimized into absurd or harmful extremes.
- Apply specification-gaming framing from DeepMind research (proxy optimization diverges from true intent).

Minimum required coverage:
- For every outcome in `tasks/outcomes-draft.md`, produce at least 2 distinct gaming scenarios.

Required output format (`tasks/red-team/paperclip-maximizer.md`):
- `Lens Description`
- `Findings` (repeat per finding):
  - `Title`
  - `Outcome Affected`
  - `Risk`
  - `Gaming Strategy`
  - `Recommended Mitigation`
  - `Severity` (`low|medium|high|critical`)
- `Summary` with total outcomes analyzed and total gaming scenarios.

Task prompt contract:

```text
Task(
  subagent_type: "general-purpose",
  prompt: """
  You are the Paperclip Maximizer red-team lens.
  Read only: tasks/outcomes-draft.md

  Goal:
  - Find how each outcome could be over-optimized in ways that satisfy metrics while violating intent.
  - Use DeepMind specification-gaming framing (proxy vs intent divergence).
  - Produce >=2 gaming scenarios per outcome.

  Write output to:
  - tasks/red-team/paperclip-maximizer.md

  Follow the required output format exactly.
  """
)
```

### Lens B: Pre-Mortem (`pre-mortem`)

Purpose:
- Assume project failure and identify the most plausible causes.

Minimum required coverage:
- At least 3 failure modes spanning technical, organizational, and external factors.
- Every failure mode must include likelihood and impact.

Required output format (`tasks/red-team/pre-mortem.md`):
- `Lens Description`
- `Failure Modes` (repeat per mode):
  - `Title`
  - `Outcome Affected`
  - `Failure Mechanism`
  - `Likelihood` (`low|medium|high`)
  - `Impact` (`low|medium|high|critical`)
  - `Early Warning Signal`
  - `Preventive Action`
- `Summary` with highest-risk modes.

Task prompt contract:

```text
Task(
  subagent_type: "general-purpose",
  prompt: """
  You are the Pre-Mortem red-team lens.
  Read only: tasks/outcomes-draft.md

  Prompt:
  - Imagine this project has failed spectacularly. Why?
  - Identify >=3 failure modes with likelihood and impact.
  - Cover technical, organizational, and external failure paths.

  Write output to:
  - tasks/red-team/pre-mortem.md

  Follow the required output format exactly.
  """
)
```

### Lens C: Boundary Tester (`boundary-tester`)

Purpose:
- Identify edge cases at input, state, timing, and scale boundaries.

Minimum required coverage:
- At least 5 edge cases across multiple boundary types.

Required output format (`tasks/red-team/boundary-tester.md`):
- `Lens Description`
- `Edge Cases` (repeat per case):
  - `Title`
  - `Outcome Affected`
  - `Boundary Type` (`input|state|timing|scale|dependency`)
  - `Boundary Condition`
  - `Expected Failure or Degradation`
  - `Detection Method`
  - `Recommended Guardrail`
- `Summary` with boundary coverage counts.

Task prompt contract:

```text
Task(
  subagent_type: "general-purpose",
  prompt: """
  You are the Boundary Tester red-team lens.
  Read only: tasks/outcomes-draft.md

  Goal:
  - Find >=5 edge cases across input, state, timing, and scale boundaries.
  - Include invalid input, race conditions, and limit behavior.

  Write output to:
  - tasks/red-team/boundary-tester.md

  Follow the required output format exactly.
  """
)
```

### Lens D: Stakeholder Advocate (`stakeholder-advocate`)

Purpose:
- Surface impacts on users, systems, and processes that are not explicit in draft outcomes.

Minimum required coverage:
- Analyze at least 2 stakeholder groups not fully represented in the draft.

Required output format (`tasks/red-team/stakeholder-advocate.md`):
- `Lens Description`
- `Stakeholder Impacts` (repeat per impact):
  - `Stakeholder Group`
  - `Outcome Affected`
  - `Hidden Impact`
  - `System/Process Touchpoint`
  - `Risk if Ignored`
  - `Recommended Adjustment`
  - `Severity` (`low|medium|high|critical`)
- `Summary` with stakeholder groups covered.

Task prompt contract:

```text
Task(
  subagent_type: "general-purpose",
  prompt: """
  You are the Stakeholder Advocate red-team lens.
  Read only: tasks/outcomes-draft.md

  Goal:
  - Identify downstream impacts not explicitly captured in the outcomes.
  - Cover users, operational teams, dependent systems, and business processes.
  - Analyze >=2 stakeholder groups.

  Write output to:
  - tasks/red-team/stakeholder-advocate.md

  Follow the required output format exactly.
  """
)
```

### Lens E: Specification Gamer (`specification-gamer`)

Purpose:
- Identify how an AI agent could technically satisfy outcome text while violating true intent.
- This lens is critical to `/orchestrate` safety.

Minimum required coverage:
- For every outcome, produce at least 2 concrete gaming strategies and mitigations.

Required output format (`tasks/red-team/specification-gamer.md`):
- `Lens Description`
- `Gaming Paths` (repeat per finding):
  - `Title`
  - `Outcome Affected`
  - `How the Spec Could Be Gamed`
  - `Why It Still Passes Naive Validation`
  - `Intent Violation`
  - `Mitigation` (constraint, anti-outcome, or stronger verification)
  - `Severity` (`low|medium|high|critical`)
- `Summary` with total strategies and top safety constraints.

Task prompt contract:

```text
Task(
  subagent_type: "general-purpose",
  prompt: """
  You are the Specification Gamer red-team lens.
  Read only: tasks/outcomes-draft.md

  Goal:
  - Find how an AI agent could technically satisfy outcomes while violating intent.
  - Produce >=2 gaming strategies per outcome, each with concrete mitigations.
  - Prioritize /orchestrate execution safety.

  Write output to:
  - tasks/red-team/specification-gamer.md

  Follow the required output format exactly.
  """
)
```

---

## 10) Red-Team Parallel Dispatch, Retry, and Partial Completion

### Parallel Spawn via Agent Teams (Mandatory)

For phase `red-team`:
1. Ensure `tasks/red-team/` exists before spawning.
2. Select agents with status `not_started` or `in_progress`.
3. Spawn all selected agents in one parallel batch via Task tool.
4. Start all five lenses within 5 seconds when all are eligible.
5. Set timeout per agent to 5 minutes.
6. Pass only one input file to each agent: `tasks/outcomes-draft.md`.

Pattern:

```text
parallel([
  Task(...paperclip-maximizer..., timeout: "5m"),
  Task(...pre-mortem..., timeout: "5m"),
  Task(...boundary-tester..., timeout: "5m"),
  Task(...stakeholder-advocate..., timeout: "5m"),
  Task(...specification-gamer..., timeout: "5m")
])
```

### Per-Agent Validation Rules

An agent attempt is successful only if:
1. Output file exists at the required fixed path.
2. Output file is non-empty.
3. Lens minimum coverage is satisfied:
   - `paperclip-maximizer`: >=2 scenarios per outcome
   - `pre-mortem`: >=3 failure modes with likelihood + impact
   - `boundary-tester`: >=5 edge cases
   - `stakeholder-advocate`: >=2 stakeholder groups analyzed
   - `specification-gamer`: >=2 gaming strategies per outcome

If validation fails, treat as an agent failure.

### Retry-on-Failure and XML Tracking (Mandatory)

For each failed attempt:
1. Increment `<attempts>`.
2. Set agent status to `failed`.
3. Set/update `failed_at` and `last_error`.
4. Persist XML atomically.

Retry policy:
1. If `<attempts>` is `1`, retry exactly once:
   - set status back to `in_progress`
   - rerun same lens with same single input
2. If `<attempts>` reaches `2` and failure persists:
   - keep status `failed`
   - preserve `last_error`
   - continue pipeline without blocking other red-team agents

### Partial Completion Handling for Synthesis

After all attempts finish:
1. Compute completed red-team outputs (`1` to `5` possible).
2. If completed count is `0`:
   - mark red-team phase `failed`
   - do not proceed automatically to synthesis
3. If completed count is `1`:
   - mark red-team `complete` with high-risk warning
   - proceed to synthesis with warning about limited lens coverage
4. If completed count is `2` to `4`:
   - mark red-team `complete` with warning listing missing lenses
   - proceed to synthesis (partial completion is acceptable)
5. If completed count is `5`:
   - mark red-team `complete` with full coverage summary

Synthesis input contract:
- Must handle `1` to `5` available red-team files gracefully.
- Must explicitly list missing lens files in synthesis summary when coverage is partial.

---

## 11) Synthesis Phase Agent Contract (Merge, Deduplicate, Recommend)

The `synthesis` phase consolidates red-team findings into one decision artifact:
- Output: `tasks/red-team/synthesis.md`
- Purpose: produce deduplicated critical findings, actionable constraints, anti-outcomes, and a risk matrix.

### Synthesis Inputs and Coverage Detection

Attempt to read these files in this order:
1. `tasks/red-team/paperclip-maximizer.md`
2. `tasks/red-team/pre-mortem.md`
3. `tasks/red-team/boundary-tester.md`
4. `tasks/red-team/stakeholder-advocate.md`
5. `tasks/red-team/specification-gamer.md`

Build:
- `available_lenses`: files that exist and are non-empty
- `missing_lenses`: expected files that are missing or empty

Rules:
1. If `available_lenses` is empty:
   - mark `synthesis` phase `failed`
   - set summary: `No red-team outputs available for synthesis`
   - do not mark complete
2. If `available_lenses` has `1` to `4` files:
   - continue synthesis
   - include explicit warning and list of missing lenses in executive summary and risk summary table
3. If all `5` are available:
   - continue synthesis with full coverage

### Finding Collection and Normalization

For each available lens file:
1. Extract each finding block from lens-specific sections (`Findings`, `Failure Modes`, `Edge Cases`, `Stakeholder Impacts`, `Gaming Paths`).
2. Normalize into a common record with required fields:
   - `title`
   - `outcome_affected`
   - `risk` (or equivalent failure/impact text)
   - `severity` (`low|medium|high|critical`)
   - `identified_by` (lens id)
3. If a candidate finding is missing any required field, skip it and note skip count in synthesis summary.

Severity mapping for lenses without explicit severity:
- `pre-mortem`: derive severity from impact (`critical` -> `critical`; `high` -> `high`; else `medium`)
- `boundary-tester`: derive severity from expected failure/degradation and guardrail urgency (`critical` for data loss/security/safety; `high` for major degradation; else `medium`)

### Cross-Lens Deduplication (Mandatory)

Use a deterministic hash-based merge strategy adapted from code-review deduplication:

```
hash = hash(normalize(severity + outcome_affected + first_50_chars_of_risk))
```

Normalization rules:
- lowercase all text
- collapse whitespace
- strip punctuation that does not change meaning

Merge rules:
1. Exact duplicate hash across multiple lenses:
   - keep one merged finding
   - combine all lens names into `identified_by`
   - mark `confidence: convergent`
   - keep the most detailed description (longest risk text)
2. Hash unique to one lens:
   - keep the finding
   - mark `confidence: single-lens`
3. Same `outcome_affected` with similar risk but severity mismatch:
   - keep one primary finding at higher severity
   - list lower-severity variant as related context
   - note severity mismatch in finding rationale

Every merged finding must include:
- `Finding ID` (`F-01`, `F-02`, ...)
- `Identified By` (one or more lens names)
- `Outcome Affected`
- `Severity`
- `Risk Summary`

### Constraint Recommendation Generation

Generate constraints from merged findings with explicit traceability.

Constraint grouping:
1. `Hard Constraints (Inviolable)`:
   - derived from `critical` findings and high-confidence gaming/intent-violation risks
   - must use unambiguous "must/must not" language
2. `Soft Constraints (Prefer to Follow)`:
   - derived from `high` and repeated `medium` findings where tradeoffs may exist
   - should use "should" language with clear preference
3. `Boundaries (Scope Limits)`:
   - derived from boundary/stakeholder/scope creep risks
   - define out-of-scope behavior and operational limits

Each constraint entry must include:
- `Constraint ID` (`HC-01`, `SC-01`, `B-01`)
- `Constraint` (specific language)
- `Rationale`
- `Source Findings` (finding IDs and lens attribution)

### Anti-Outcome Generation (Gaming + Failure Prevention)

Generate anti-outcomes from:
- specification-gaming paths
- paperclip-maximizer gaming strategies
- pre-mortem failure modes likely to be exploited by naive success metrics

Required format for every anti-outcome line:
- `Do NOT: [anti-outcome] -- Prevents: [gaming strategy or failure mode]`

Rules:
1. Every anti-outcome must map to at least one source finding.
2. Prioritize anti-outcomes that prevent "metric pass, intent fail" behavior.
3. Keep language testable and observable.

### Required Output Structure (`tasks/red-team/synthesis.md`)

```markdown
# Red-Team Synthesis

## Executive Summary
[2-3 sentences: overall risk posture, coverage level, and immediate action signal]

## Critical Findings
### F-01: [Title]
**Severity:** [critical|high|medium|low]
**Outcome Affected:** [Outcome]
**Identified By:** [Lens A, Lens B]
**Risk Summary:** [Concise merged risk statement]
**Why It Matters:** [Impact on project success/safety]

## Recommended Constraints
### Hard Constraints (Inviolable)
- **HC-01:** [Constraint text]
  **Rationale:** [Why]
  **Source Findings:** [F-01, F-03]

### Soft Constraints (Prefer to Follow)
- **SC-01:** [Constraint text]
  **Rationale:** [Why]
  **Source Findings:** [F-02]

### Boundaries (Scope Limits)
- **B-01:** [Boundary text]
  **Rationale:** [Why]
  **Source Findings:** [F-04]

## Recommended Anti-Outcomes
- Do NOT: [Anti-outcome statement] -- Prevents: [Gaming strategy or failure mode]
- Do NOT: [Anti-outcome statement] -- Prevents: [Gaming strategy or failure mode]

## Risk Summary
| Risk Category | Critical | High | Medium | Low | Notes |
|---|---:|---:|---:|---:|---|
| Specification Gaming | X | X | X | X | [Top concern] |
| Delivery Failure Modes | X | X | X | X | [Top concern] |
| Boundary/Scale Failures | X | X | X | X | [Top concern] |
| Stakeholder/Process Risk | X | X | X | X | [Top concern] |
| Lens Coverage Gaps | X | X | X | X | [Missing lenses or "None"] |
```

### Synthesis Task Prompt Contract

```text
Task(
  subagent_type: "general-purpose",
  prompt: """
  Phase: synthesis
  Read available files only:
  - tasks/red-team/paperclip-maximizer.md
  - tasks/red-team/pre-mortem.md
  - tasks/red-team/boundary-tester.md
  - tasks/red-team/stakeholder-advocate.md
  - tasks/red-team/specification-gamer.md

  Requirements:
  - Handle missing files gracefully and explicitly report missing lenses.
  - Normalize and deduplicate findings across lenses.
  - Keep lens attribution when findings are merged.
  - Generate constraints grouped into Hard/Soft/Boundaries.
  - Generate anti-outcomes in exact required format.
  - Write final synthesis to tasks/red-team/synthesis.md.
  """
)
```

### Completion Validation for `synthesis` Phase

Before marking `synthesis` phase `complete`:
1. Verify `tasks/red-team/synthesis.md` exists.
2. Verify file is non-empty.
3. Verify required sections are present:
   - `Executive Summary`
   - `Critical Findings`
   - `Recommended Constraints`
   - `Recommended Anti-Outcomes`
   - `Risk Summary`
4. Verify every critical/high finding has at least one constraint or anti-outcome mapping.
5. If partial lens coverage, verify missing lenses are explicitly listed.

If validation fails:
- mark phase `failed`
- apply retry-on-failure policy (exactly one retry)

---

## 15) Edge Cases and Operational Guidance

This section defines required degraded-mode behavior for missing context, large files, long-running phases, and standalone lens execution.

### 15.1 Empty Project Handling (`.ai/` Missing)

If `.ai/` does not exist, or required memory files cannot be read:
1. Log a warning and continue:
   - `warning: memory system unavailable (.ai missing); continuing in greenfield mode`
2. Do not fail `discovery`, `context`, or later phases solely due to missing `.ai/` files.
3. Discovery must compensate with extended questioning (additional rounds) to capture architecture assumptions, dependencies, and constraints directly from user input.
4. Context phase must explicitly record:
   - `No prior art found - greenfield project`
5. `tasks/CONTEXT.md` must list missing inputs under `Input Coverage` and mark the run as degraded context mode.
6. All phase agents must use available files only and continue with partial inputs instead of hard-failing.

### 15.2 Large Outcomes Stress Handling (`tasks/outcomes-draft.md` 500+ Lines)

When the draft is large (500+ lines), keep handoffs file-based and apply bounded processing:
1. Never inline full `tasks/outcomes-draft.md` into prompts; pass file path only.
2. Red-team lenses must start with a short structural index (outcome IDs and sections) before deep analysis to keep reasoning organized.
3. Process findings in batches when needed (per outcome group or severity group) and merge incrementally.
4. If synthesis input volume is high, produce:
   - Primary synthesis: `tasks/red-team/synthesis.md`
   - Optional overflow details: `tasks/red-team/synthesis-appendix.md`
5. If any lens output is too large/noisy, summarize repetitive findings while preserving all critical/high-severity issues and explicit mitigations.

### 15.3 Progress Indicator Formats (Red-Team and Synthesis)

Use consistent, explicit progress lines during long phases.

Red-team progress format:
- `[progress][red-team] <completed>/<total> agents complete...`
- Example: `[progress][red-team] 3/5 agents complete...`

Synthesis progress format:
- `[progress][synthesis] <processed>/<total> lens reports processed | merged=<count> | deduped=<count>`
- Example: `[progress][synthesis] 4/5 lens reports processed | merged=22 | deduped=9`

Progress rules:
1. Emit a line at phase start (`0/N`), after each completion increment, and at phase finish (`N/N`).
2. Keep the format stable across runs for easy scanning and log parsing.
3. Include warning suffix when inputs are missing, e.g. `| missing=stakeholder-advocate`.

### 15.4 Standalone Red-Team Lens Invocation

Support standalone lens execution without running the full pipeline.

Command:
- `/outcomes red-team <lens> [file]`

Behavior:
1. `<lens>` is required; accepted aliases:
   - `paperclip` -> `paperclip-maximizer`
   - `pre-mortem` -> `pre-mortem`
   - `boundary` -> `boundary-tester`
   - `stakeholder` -> `stakeholder-advocate`
   - `spec-gamer` -> `specification-gamer`
2. `[file]` is optional; default is `tasks/outcomes-draft.md`.
3. Any readable specification file path is allowed (for example PRDs or task specs).
4. Output defaults to `tasks/red-team/<resolved-lens>.md` unless caller overrides destination.
5. Standalone lens mode does not require all pipeline phases to be complete.
6. Unknown lens names must fail fast with a usage hint showing valid lens values.

---

## 14) Finalize Phase Agent Contract (Orchestrate-Ready Artifacts)

The `finalize` phase creates execution-ready project artifacts from refinement outputs.

- Primary outputs:
  - `tasks/OUTCOMES.md`
  - `tasks/PROJECT_STATE.md`
  - `tasks/DECISIONS.md`
- Required inputs:
  - `tasks/outcomes-refined.md`
  - `tasks/OUTCOMES_STATE.md`
- Supporting input:
  - `tasks/CONTEXT.md` (for dependency reference in `PROJECT_STATE.md`)

### Finalize Entry Rules

When `finalize` is selected as the first incomplete phase:
1. If status is `not_started`, set to `in_progress` and set `started_at` (if empty).
2. Validate required inputs exist and are non-empty before generation.
3. If required inputs are missing, set phase `failed` with explicit missing-file summary.
4. If required inputs pass, generate all three outputs in one finalize run.

### 14.1 Generate Enhanced `tasks/OUTCOMES.md` (Backward Compatible + Additive)

Build `tasks/OUTCOMES.md` from `tasks/outcomes-refined.md` using the `project-lead.md` outcomes template as the base structure:

```markdown
# Project Outcomes: [Project Name]
Created: [date], Last Reviewed: [date], Owner: Iain Forrest
## Outcome N: [Name]
Description: [What this outcome changes]
Success Criteria:
- [Criterion 1]
- [Criterion 2]
Constraints:
- [Constraint 1]
Status: [Not Started | In Progress | Complete]
Sprint(s): [Sprint names or IDs]
## Project Constraints
- [Constraint]
## Non-Goals
- [Explicitly out of scope]
```

Compatibility rules:
1. Preserve all existing template sections and field labels in the same order.
2. Populate outcomes from refined outcomes (primary, secondary, stretch) with measurable success criteria.
3. Default `Status` to `Not Started` and `Sprint(s)` to `Sprint 0 - Setup` unless refined content specifies otherwise.

Additive section rules (append at end only; do not alter base template shape):
1. `## Progress Markers`
   - Include `Expect to See`, `Like to See`, `Love to See` for each primary outcome.
   - Preserve checklist format (`- [ ] ...`) for execution tracking.
2. `## Constraint Hierarchy`
   - `### Hard Constraints (Inviolable)`
   - `### Soft Constraints (Prefer to Follow)`
   - `### Boundaries (Scope Limits)`
   - Include only accepted/modified constraint text with source IDs when available.
3. `## Anti-Outcomes`
   - Include finalized anti-outcomes using:
     - `Do NOT: [anti-outcome] -- Prevents: [failure/gaming mode]`

### 14.2 Generate `tasks/PROJECT_STATE.md` (Execution Initialization)

Generate `tasks/PROJECT_STATE.md` using the `project-lead.md` template structure:

```markdown
# Project State: [Project Name]
Last Updated: [ISO 8601], Updated By: Project Lead | Iain
## Current Sprint
Name: [Sprint Name]
**Status:** [Not Started | Planning | Ready | PRD Review | Task Generation | Executing | Code Review | Complete]
Started: [ISO 8601]
PRD: [path or None]
Tasks: [path or None]
## Active Blockers
- [Blocker or None]
## Questions for Iain
- [Question or None]
## Sprint History
- [ISO 8601] [Sprint Name] - [Result]
```

Initialization requirements:
1. Set `Name` to `Sprint 0 - Setup`.
2. Set `Status` to `Ready`.
3. Set `Started` and `Last Updated` to current ISO-8601 UTC timestamp.
4. Set `PRD` to `None`.
5. Set `Tasks` to `None`.
6. Set `Active Blockers` to `None`.
7. Set `Questions for Iain` to `None`.
8. Add a context reference line pointing to `tasks/CONTEXT.md` for dependencies/assumptions.

### 14.3 Generate `tasks/DECISIONS.md` (Seed from Refinement State)

Generate `tasks/DECISIONS.md` using the `project-lead.md` decision-log template:

```markdown
# Decision Log: [Project Name]
Append-only log. Most recent at bottom.
## [ISO 8601] - [Decision Title]
Context: [What prompted the decision]
Decision: [What was decided]
Authority: [Project Lead | CTO | Iain]
Rationale: [Why this is the right call]
Alternatives Considered:
- [Alternative A]
- [Alternative B]
Impact: [Expected effect on outcomes, scope, or risk]
```

Seeding requirements from `tasks/OUTCOMES_STATE.md`:
1. Create initial decision entries for outcome-definition baseline (refined outcomes accepted for execution).
2. Create decision entries for constraint outcomes:
   - accepted constraints
   - modified constraints (with final text context)
   - rejected constraints (with rationale)
3. Add entries for key refinement decisions affecting execution safety:
   - anti-outcome adoption
   - progress marker commitments
4. Keep log append-only and chronological (`most recent at bottom`).

### 14.4 Finalize Validation Checklist (Before `finalize` = `complete`)

Before marking phase `complete`, verify all checks:
1. `tasks/OUTCOMES.md` exists and is non-empty.
2. `tasks/OUTCOMES.md` contains at least 1 `## Outcome` block with `Success Criteria`.
3. `tasks/OUTCOMES.md` includes additive sections:
   - `## Progress Markers`
   - `## Constraint Hierarchy`
   - `## Anti-Outcomes`
4. `tasks/PROJECT_STATE.md` exists and is non-empty.
5. `tasks/PROJECT_STATE.md` includes `Current Sprint` with `Sprint 0 - Setup` and `Status: Ready`.
6. `tasks/PROJECT_STATE.md` includes `tasks/CONTEXT.md` reference.
7. `tasks/DECISIONS.md` exists and is non-empty.
8. `tasks/DECISIONS.md` has decision log header and at least 1 seeded decision entry.

If any check fails:
- mark `finalize` phase `failed`
- write missing/invalid items into phase summary
- apply retry-on-failure policy (exactly one retry)

### 14.5 Completion Display and `/orchestrate` Integration

On successful validation:
1. Set `finalize` phase status to `complete`, set `completed_at`, and persist XML atomically.
2. Write concise summary with counts:
   - outcomes generated
   - constraints captured by hierarchy
   - anti-outcomes captured
   - seeded decisions created
3. Display completion block:

```text
Finalize Phase Complete

Generated:
- tasks/OUTCOMES.md
- tasks/PROJECT_STATE.md
- tasks/DECISIONS.md

Validation: PASS
Next: Artifacts are /orchestrate-ready.
Run /orchestrate now? (yes/no)
```

If user confirms `yes`, transition control to `/orchestrate` in the next command step.

---

## 13) Refinement Phase Agent Contract (Interactive Outcomes Lead)

The `refinement` phase is interactive and runs in the Outcomes Lead context (no separate Task agent).

- Primary outputs:
  - `tasks/outcomes-refined.md`
  - `tasks/OUTCOMES_STATE.md`
- Required inputs:
  - `tasks/outcomes-draft.md`
  - `tasks/red-team/synthesis.md`
  - `tasks/CONTEXT.md`
- Resume input (if present):
  - `tasks/OUTCOMES_STATE.md`

### Refinement Entry and Resume Rules

When `refinement` is selected as the first incomplete phase:
1. If status is `not_started`, set to `in_progress` and set `started_at` (if empty).
2. If status is `in_progress`, read `tasks/OUTCOMES_STATE.md` and resume from last unresolved decision point.
3. If `tasks/OUTCOMES_STATE.md` is missing during resume, reconstruct progress from:
   - `tasks/outcomes-refined.md` decision log (if present), else
   - start refinement from findings presentation.
4. Persist refinement state after every user response (do not wait for end of phase).

### Interaction Cadence (Mandatory)

- Ask at most 3 questions/decisions per batch.
- Keep interaction scannable:
  - short severity headers
  - one-line decision prompts
  - explicit next action
- Always persist `tasks/OUTCOMES_STATE.md` after each batch.

### Findings Presentation Flow (6.1)

Read `tasks/red-team/synthesis.md` and `tasks/CONTEXT.md`, then present in this order:

1. Executive summary first:
   - format: `Red team found X critical issues. Recommending Y new constraints.`
   - include counts for:
     - critical/high findings
     - hard/soft/boundary constraints
     - anti-outcomes
     - missing lens coverage warnings (if any)
2. Action-required findings:
   - present `critical` then `high`, grouped by severity
   - include per finding:
     - `Finding ID`
     - short risk statement
     - affected outcome(s)
     - mapped constraint IDs
3. Lower-priority findings:
   - summarize `medium/low` findings in compact form for optional batch handling.

### Constraint Decision Flow (6.2)

Build a constraint decision queue ordered by source severity:
1. critical-linked constraints
2. high-linked constraints
3. medium/low-linked constraints

Decision options per constraint:
- `Accept`
- `Modify` (requires replacement text)
- `Reject` (requires rationale)

Mandatory decision rules:
1. Every `critical`/`high` linked constraint requires explicit per-item decision (no batch shortcut).
2. `medium/low` constraints may use batch accept:
   - `Accept all remaining medium/low constraints? (yes/no)`
   - if `yes`, stamp all remaining medium/low items as accepted with same timestamp
   - if `no`, continue item-by-item
3. Do not advance to progress markers while any critical/high constraint is undecided.

Timestamping and recording:
- Every decision must record ISO-8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`).
- Persist each decision in `tasks/OUTCOMES_STATE.md` immediately.
- Include fields:
  - `constraint_id`
  - `decision` (`accepted|modified|rejected`)
  - `final_text` (for accepted/modified)
  - `rationale` (required for rejected, optional for modified)
  - `decision_timestamp`
  - `decision_mode` (`individual|batch`)

### Progress Marker Input Flow (6.3)

For each `primary` outcome in `tasks/outcomes-draft.md`, collect:
- `Expect to See (Minimum Viable)` (required)
- `Like to See (Target)` (optional)
- `Love to See (Stretch)` (optional)

Rules:
1. `Expect to See` must contain at least one marker for each primary outcome.
2. Secondary/stretch outcome markers are optional.
3. Keep prompts in batches of at most 3 questions.
4. Save markers as checklist items (`- [ ] ...`) for execution tracking.

Recommended prompt sequence (per primary outcome):
1. `Expect to See` markers
2. `Like to See` markers
3. `Love to See` markers

### Required Output Structure (`tasks/outcomes-refined.md`) (6.4)

```markdown
# Outcomes Refined
<!-- refinement_status: in_progress|complete -->

## Refinement Metadata
- Started At: [ISO-8601 UTC]
- Last Updated At: [ISO-8601 UTC]
- Inputs:
  - tasks/outcomes-draft.md
  - tasks/red-team/synthesis.md
  - tasks/CONTEXT.md

## Executive Summary
[Refined intent, major risks accepted/mitigated, notable user modifications]

## Outcomes (From Draft, Refined)
### Primary Outcomes
#### Outcome P1: [Name]
**Description:** [Original or user-modified text]
**Success Criteria:**
- [ ] [Measurable criterion]
**Progress Markers**
**Expect to See (Minimum Viable):**
- [ ] [Marker]
**Like to See (Target):**
- [ ] [Marker]
**Love to See (Stretch):**
- [ ] [Marker]

### Secondary Outcomes
[Original outcomes + optional marker additions]

### Stretch Outcomes
[Original outcomes + optional marker additions]

## Constraint Decisions
### Hard Constraints (Inviolable)
- **HC-01** (`accepted|modified|rejected`)
  - Final Text: [Text or "Rejected"]
  - Source Findings: [F-IDs]
  - Decision Timestamp: [ISO-8601 UTC]
  - Rationale: [Required if rejected; include reason if modified]

### Soft Constraints (Prefer to Follow)
- **SC-01** (`accepted|modified|rejected`)
  - Final Text: [...]
  - Source Findings: [...]
  - Decision Timestamp: [...]
  - Rationale: [...]

### Boundaries (Scope Limits)
- **B-01** (`accepted|modified|rejected`)
  - Final Text: [...]
  - Source Findings: [...]
  - Decision Timestamp: [...]
  - Rationale: [...]

## Recommended Anti-Outcomes
- Do NOT: [Anti-outcome] -- Prevents: [Gaming strategy or failure mode]

## Rejected Constraints Converted to Non-Goals
- [Constraint ID + rejected text] -- Why rejected: [Rationale]

## User Modifications
- [Outcome edits, added constraints, custom anti-outcomes, or scope changes]

## Decision Log (Chronological)
- [timestamp] [decision/action]
```

Content requirements:
1. Include original outcomes from draft (with user modifications applied explicitly).
2. Include accepted/modified/rejected constraints with timestamps.
3. Include anti-outcomes from synthesis plus user changes.
4. Include primary-outcome progress markers (`Expect/Like/Love`).
5. Include rejected-constraint rationale under non-goals.

### Required State Structure (`tasks/OUTCOMES_STATE.md`) (6.5)

```markdown
# Outcomes State

## Phase Log
### Red Team Phase
**Completed:** [timestamp]
**Agents Status:**
- paperclip-maximizer: [status]
- pre-mortem: [status]
- boundary-tester: [status]
- stakeholder-advocate: [status]
- specification-gamer: [status]
**Critical Findings:** [count]

### Refinement Phase
**Status:** [in_progress|complete]
**Started:** [timestamp]
**Last Updated:** [timestamp]
**Last Decision Point:** [present_findings|constraint:<ID>|markers:<OutcomeID>:<marker_type>|finalize]
**Pending Decisions:** [count]

## Refinement Decisions
### Constraint Decisions
- [timestamp] [Constraint ID] [accepted|modified|rejected]
  - Final Text: [text]
  - Rationale: [required for rejected]
  - Mode: [individual|batch]

### Progress Marker Decisions
- [timestamp] [Outcome ID]
  - Expect to See: [count + items]
  - Like to See: [count + items]
  - Love to See: [count + items]

### Custom Additions
- [timestamp] [user-added constraint/anti-outcome/modification]

## Cross-Phase Learnings
- [learning impacting finalize/orchestrate safety]
```

State requirements:
1. Phase log entries must be timestamped.
2. Constraint decisions must preserve accepted/rejected/modified outcomes.
3. Red-team agent status snapshot must be present.
4. `Last Decision Point` must be updated after every saved interaction.

### Timeout/Abandonment and Resume Logic (6.6)

If user abandons refinement mid-flow (timeout, cancel, disconnect, or explicit pause):
1. Save current decisions immediately to `tasks/OUTCOMES_STATE.md`.
2. Save partial `tasks/outcomes-refined.md` with marker:
   - `<!-- refinement_status: in_progress -->`
3. Keep XML phase `refinement` as `in_progress`.
4. Record resume cursor in state:
   - `Last Decision Point`
   - pending critical/high constraints
   - pending required `Expect to See` markers

On next invocation:
1. Read `tasks/OUTCOMES_STATE.md`.
2. Display concise resume summary:
   - what is already decided
   - what remains required
   - exact next decision prompt
3. Continue from first unresolved required item:
   - unresolved critical/high constraints first
   - then missing required primary `Expect to See` markers
   - then optional markers and remaining medium/low constraint decisions

### Completion Validation for `refinement` Phase

Before marking `refinement` phase `complete`:
1. Verify `tasks/outcomes-refined.md` exists and is non-empty.
2. Verify `tasks/OUTCOMES_STATE.md` exists and is non-empty.
3. Verify every critical/high-linked constraint has explicit decision.
4. Verify every primary outcome has at least one `Expect to See` marker.
5. Verify every rejected constraint has recorded rationale.
6. Verify `tasks/outcomes-refined.md` contains:
   - outcomes from draft
   - constraint decisions
   - anti-outcomes
   - progress markers
   - user modifications

If validation passes:
1. set `<!-- refinement_status: complete -->` in `tasks/outcomes-refined.md`
2. set phase status to `complete` with `completed_at`
3. write refinement summary to XML (counts of accepted/modified/rejected and markers captured)
4. persist XML atomically

If validation fails:
- keep phase as `in_progress`
- continue interactive refinement until required decisions are complete

---

## 12) Context Phase Agent Contract (Dependencies, Assumptions, Sphere, Prior Art)

The `context` phase produces a project-context artifact for downstream agents:
- Output: `tasks/CONTEXT.md`
- Purpose: document internal/external dependencies, assumptions with risk, sphere of influence, and prior art/pattern guidance.

### Context Inputs and Read Order

Read these inputs in order:
1. `tasks/outcomes-draft.md`
2. `tasks/red-team/synthesis.md`
3. `.ai/FILES.json`
4. `.ai/ARCHITECTURE.json`
5. `.ai/PATTERNS.md`
6. `.ai/BUSINESS.json`

Input handling rules:
1. `tasks/outcomes-draft.md` is required.
2. `tasks/red-team/synthesis.md` is strongly preferred; if missing, continue with explicit warning.
3. Missing `.ai/*` files do not block phase completion if at least 2 memory files are available.
4. Every missing input must be listed in `tasks/CONTEXT.md` under `Input Coverage`.

### Explore Analysis Pattern (Mandatory)

Use the Explore-agent workflow pattern from `~/.claude/commands/investigate.md:149-200`:
1. Start from memory files for architecture and file-map grounding.
2. Analyze relevant codebase structure and integration points.
3. Produce concrete, file-referenced findings (path references required).
4. Keep output decision-oriented for downstream refinement/finalize phases.

### Required Output Structure (`tasks/CONTEXT.md`)

```markdown
# Context Capture

## Input Coverage
- Available Inputs:
  - [file path]
- Missing Inputs:
  - [file path + impact of missing context]

## Dependencies
### Internal Dependencies
- **Dependency:** [module/service/path]
  **Why Needed:** [role in outcomes-v2]
  **Impact if Changed:** [breakage/risk]
  **Reference:** [file path]

### External Dependencies
- **Dependency:** [API/service/library]
  **Why Needed:** [role in outcomes-v2]
  **Fallback if Unavailable:** [degraded mode or alternative]
  **Reference:** [file path]

## Assumptions
- **Assumption:** [statement]
  **Risk if Wrong:** [impact]
  **Validation Method:** [how to verify]
  **Confidence:** [high|medium|low]

## Sphere of Influence
### Files Affected
- `[path]` - [create|modify|delete] - [impact type]

### Services Affected
- `[service/component]` - [behavioral/operational impact]

### Users Affected
- `[user group]` - [workflow/experience impact]

## Prior Art
### Similar Features
- **Feature:** [name]
  **What to Reuse/Learn:** [specific lesson]
  **Reference:** [file path]

### Applicable Patterns
- **Pattern:** [pattern name]
  **How to Apply Here:** [specific usage guidance]
  **Reference:** [file path]
```

### Context Content Requirements

#### Dependencies Section

Minimum coverage:
1. At least 5 internal dependencies from project files/modules.
2. At least 3 external dependencies (APIs/services/libraries/runtime tools).
3. Every dependency must include `Why Needed` and either `Impact if Changed` (internal) or `Fallback if Unavailable` (external).

#### Assumptions Section

Minimum coverage:
1. At least 5 assumptions sourced from discovery/synthesis and architecture context.
2. At least 2 assumptions must be explicitly marked high-risk (`Risk if Wrong` materially affects delivery or safety).
3. Every assumption must include confidence level and an actionable validation method.

#### Sphere of Influence Section

Minimum coverage:
1. Files Affected must include concrete paths with change type (`create|modify|delete`).
2. Services Affected must include at least 3 concrete service/component names.
3. Users Affected must include at least 2 user/stakeholder groups.

#### Prior Art Section

Minimum coverage:
1. At least 2 similar features from `.ai/BUSINESS.json` or command history context.
2. At least 3 applicable patterns from `.ai/PATTERNS.md`.
3. Every entry must include clear reuse/apply guidance and a file reference.
4. Conditional degraded-mode minima when memory inputs are unavailable:
   - similar features >= 0 (instead of 2)
   - applicable patterns >= 0 (instead of 3)
5. When degraded minima are used, `tasks/CONTEXT.md` must explicitly annotate degraded context mode in `Input Coverage` and the `Prior Art` section.

### Context Task Prompt Contract

```text
Task(
  subagent_type: "Explore",
  prompt: """
  Phase: context

  Read inputs (in order):
  - tasks/outcomes-draft.md
  - tasks/red-team/synthesis.md
  - .ai/FILES.json
  - .ai/ARCHITECTURE.json
  - .ai/PATTERNS.md
  - .ai/BUSINESS.json

  Goal:
  - Produce tasks/CONTEXT.md with: Dependencies, Assumptions, Sphere of Influence, Prior Art.
  - Use concrete file references and explicit risk language.
  - If inputs are missing, continue with available files and include Input Coverage section.

  Requirements:
  - Internal and external dependencies with rationale and impact/fallback.
  - Assumptions with risk-if-wrong, validation method, confidence.
  - Sphere of influence across files, services, users.
  - Prior art and applicable patterns with practical reuse guidance.

  Write output to:
  - tasks/CONTEXT.md
  """
)
```

### Completion Validation for `context` Phase

Before marking `context` phase `complete`:
1. Verify `tasks/CONTEXT.md` exists.
2. Verify file is non-empty.
3. Verify required sections are present:
   - `Input Coverage`
   - `Dependencies`
   - `Assumptions`
   - `Sphere of Influence`
   - `Prior Art`
4. Verify minimum coverage counts are satisfied:
   - internal dependencies >= 5
   - external dependencies >= 3
   - assumptions >= 5
   - services affected >= 3
   - users affected >= 2
   - if memory inputs are available: similar features >= 2 and applicable patterns >= 3
   - if memory inputs are unavailable (degraded mode): similar features >= 0 and applicable patterns >= 0, and degraded-mode annotations are present in `Input Coverage` and `Prior Art`
5. Verify every assumption has `Risk if Wrong`, `Validation Method`, and `Confidence`.
6. Verify all missing inputs (if any) are explicitly listed under `Input Coverage`.

If validation fails:
- mark phase `failed`
- apply retry-on-failure policy (exactly one retry)
