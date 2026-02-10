# PRD: CTO Command Integration

**Generated:** 2026-02-10
**Status:** Draft
**Version:** v1.0
**Complexity:** Medium (Score: 14)

**Architecture Pattern:** Agent file reference pattern (read + adopt at startup) -- new pattern for fat-controller
**Integration Points:** 4 command files, 2 agent files, Task tool subagent invocation
**Key Files:** ~/.claude/agents/cto.md (source), .claude/agents/cto.md (target), .claude/agents/cto-technical-advisor.md, .claude/commands/execute.md, .claude/commands/prd.md, .claude/commands/bugs.md, .claude/commands/feature.md

---

## Overview

Fat-controller's four core commands (execute, prd, bugs, feature) currently either interrupt the user for technical judgment calls or make decisions without a consistent values framework. The CTO agent exists at user level but isn't wired into any workflow. This feature copies the CTO agent into the project, integrates its decision-making personality into all four commands via a lightweight file reference pattern, updates the CTO-advisor to understand its relationship with the CTO, and adds a new post-execution task completion review step to the execute command.

**Architecture Integration:** Introduces a new "personality overlay" pattern where commands read an agent file at startup and adopt its decision-making framework. This is additive to existing command logic -- the CTO personality doesn't replace command instructions, it provides the decision-making lens for judgment calls that currently either interrupt the user or get skipped.

**Implementation Strategy:** Compact file reference at the top of each command ("Read .claude/agents/cto.md and adopt its decision-making framework"), command-specific "Decision Authority" sections defining what the CTO handles in that command's context, and a new post-code-review step in execute.md that invokes CTO-advisor via Task tool.

---

## Goals

- Eliminate unnecessary user interruptions during command execution by giving commands a consistent, values-driven decision-making framework
- Preserve the CTO escalation criteria so the user IS interrupted for decisions that genuinely need human judgment (costs >$20/month, external lock-in, people decisions, value conflicts, scope changes, <70% confidence + high downside)
- Add holistic task completion verification to execute command via CTO-advisor review before memory update
- Establish single source of truth for CTO personality at `.claude/agents/cto.md` (project-level, version controlled)
- Keep CTO-advisor independently usable as a standalone agent while enhancing it to serve the CTO efficiently

**Success looks like:** Running `/execute` on a task file and seeing all code review findings triaged, fix agents spawned, task completion verified, and memory updated -- without the user being asked a single technical question they shouldn't need to answer.

---

## User Stories

- As Iain, I want the execute command to triage code review findings autonomously so that I don't have to manually decide fix/defer/skip for every MEDIUM and LOW finding
- As Iain, I want the PRD command to make architectural decisions during discovery (using my values) so that I'm only asked about genuine ambiguities, not routine technical choices
- As Iain, I want the bugs command to validate complexity assessments and make tier decisions using CTO judgment so that the right routing (inline/tasks/PRD) happens without my intervention
- As Iain, I want the feature command to assess design approaches and complexity with CTO judgment so that tier routing is decided consistently
- As Iain, I want a task completion review after code review passes in execute so that I have confidence all tasks were actually completed correctly -- not just that individual verify steps passed
- As a fat-controller user from GitHub, I want the CTO personality to be project-level (`.claude/agents/cto.md`) so that I can see, fork, and customise the decision-making framework for my own use

---

## Feature Components

**Priority Formula:** (User Value x Impact) / (Effort x Risk)
Critical: >5.0 | High: 2.0-5.0 | Medium: 0.5-2.0 | Low: <0.5

### Component 1: Project-Level CTO Agent File [Priority: Critical]
**Responsibility:** Copy ~/.claude/agents/cto.md into .claude/agents/cto.md as a version-controlled project-level agent. Single source of truth for CTO personality across all commands.
**Priority Score:** 8.3 (User Value: 5, Impact: 5, Effort: 1, Risk: 1)
**Files:** .claude/agents/cto.md (new, copied from ~/.claude/agents/cto.md)
**Dependencies:** None -- this is the foundation all other components reference

### Component 2: CTO-Advisor Relationship Update [Priority: High]
**Responsibility:** Update .claude/agents/cto-technical-advisor.md to understand its relationship with the CTO agent, align tone with CTO values, add disallowedTools, restructure output as decision-ready briefing while preserving standalone usability.
**Priority Score:** 4.2 (User Value: 4, Impact: 4, Effort: 2, Risk: 2)
**Files:** .claude/agents/cto-technical-advisor.md (modify)
**Dependencies:** Component 1 (must understand what CTO.md contains)

### Component 3: Execute Command CTO Integration [Priority: Critical]
**Responsibility:** Add CTO personality overlay to execute.md. Replace user-interrupting code review triage with CTO-driven autonomous triage. Add post-code-review CTO-advisor task completion review step. Change "DO NOT make implementation decisions" to allow CTO-level architectural decisions.
**Priority Score:** 6.3 (User Value: 5, Impact: 5, Effort: 2, Risk: 2)
**Files:** .claude/commands/execute.md (modify -- lines 11-97, 1417-1469)
**Dependencies:** Component 1, Component 2

### Component 4: PRD Command CTO Integration [Priority: High]
**Responsibility:** Add CTO personality overlay to prd.md so architectural decisions during discovery rounds are made using CTO values instead of asking the user.
**Priority Score:** 3.1 (User Value: 4, Impact: 4, Effort: 2, Risk: 2.5)
**Files:** .claude/commands/prd.md (modify -- questioning process, architectural decision points)
**Dependencies:** Component 1

### Component 5: Bugs Command CTO Integration [Priority: High]
**Responsibility:** Add CTO personality overlay to bugs.md for complexity assessment validation and tier decision-making (inline 1-2 / task-writer 3-6 / prd-writer 7+).
**Priority Score:** 3.1 (User Value: 4, Impact: 4, Effort: 2, Risk: 2.5)
**Files:** .claude/commands/bugs.md (modify -- solution options, tier decisions)
**Dependencies:** Component 1

### Component 6: Feature Command CTO Integration [Priority: High]
**Responsibility:** Add CTO personality overlay to feature.md for design approach validation and tier decision-making.
**Priority Score:** 3.1 (User Value: 4, Impact: 4, Effort: 2, Risk: 2.5)
**Files:** .claude/commands/feature.md (modify -- design approach, complexity, tier decisions)
**Dependencies:** Component 1

---

## Functional Requirements

### Project-Level CTO Agent (Component 1)

**FR1.1:** The system must contain a file at `.claude/agents/cto.md` that is an exact copy of `~/.claude/agents/cto.md` at time of implementation.
- **Input:** Source file at ~/.claude/agents/cto.md (143 lines, includes frontmatter, values, decision process, escalation criteria, response format, communication style, boundaries)
- **Output:** Identical file at .claude/agents/cto.md
- **Validation:** File diff shows zero differences
- **Error States:** Source file not found -- abort with clear error message

**FR1.2:** The project-level CTO agent file must be the single source of truth referenced by all four commands.
- **Input:** All command files referencing CTO personality
- **Output:** All references point to `.claude/agents/cto.md` (project-level, relative path)
- **Validation:** Grep for CTO references in all four commands shows consistent path
- **Error States:** N/A -- enforced by implementation

### CTO-Advisor Relationship Update (Component 2)

**FR2.1:** The CTO-advisor must include a "Relationship to CTO" section explaining its dual-use role.
- **Input:** New section added to cto-technical-advisor.md
- **Output:** Section covering: (a) when invoked by CTO -- deliver decision-ready briefing, (b) when invoked standalone by user -- deliver advisory response as today
- **Validation:** Section present and clear on both usage modes
- **Error States:** N/A

**FR2.2:** The CTO-advisor must adopt values alignment with the CTO agent.
- **Input:** Reference to CTO values as analysis lens
- **Output:** Updated identity section replacing "20 years of battle-tested experience" corporate framing with values-aligned, direct tone matching the CTO
- **Validation:** No corporate buzzwords, tone matches CTO style (direct, warm, grounded)
- **Error States:** N/A

**FR2.3:** The CTO-advisor must add `disallowedTools: Write, Edit, NotebookEdit` to its frontmatter.
- **Input:** Updated frontmatter
- **Output:** `disallowedTools: Write, Edit, NotebookEdit` present in YAML frontmatter
- **Validation:** Frontmatter parses correctly with new field
- **Error States:** N/A

**FR2.4:** The CTO-advisor response structure must support decision-ready briefing format for CTO consumption.
- **Input:** Response structure section
- **Output:** Updated 7-step structure where each step produces output optimised for a decision-maker (clear verdict, trade-offs as bullet points, recommendation with confidence level)
- **Validation:** Response structure documented and distinct from verbose advisory style
- **Error States:** N/A

**FR2.5:** The CTO-advisor must preserve its existing capabilities: feasibility spectrum (Trivial through Infeasible), implementation options (2-3 with effort estimates), risk assessment, mandatory .ai/ memory reading, 7-step response structure (updated per FR2.4).
- **Input:** Existing capabilities in current file
- **Output:** All capabilities preserved in updated file
- **Validation:** Side-by-side comparison shows no capability loss
- **Error States:** N/A

### Execute Command CTO Integration (Component 3)

**FR3.1:** The execute command must read `.claude/agents/cto.md` at startup and adopt its decision-making framework.
- **Input:** New instruction block at top of execute.md (after the CRITICAL orchestrator section)
- **Output:** Instruction: "Read .claude/agents/cto.md and adopt its decision-making framework for all judgment calls during orchestration. You are the CTO-orchestrator: lightweight orchestrator with CTO decision-making authority."
- **Validation:** Instruction present and positioned correctly (after orchestrator identity, before wave building)
- **Error States:** If .claude/agents/cto.md not found, fall back to existing behavior (no CTO personality), log warning

**FR3.2:** The execute command line 24 ("DO NOT make implementation decisions") must be updated to reflect CTO authority.
- **Input:** Current line: "DO NOT make implementation decisions"
- **Output:** Updated to: "DO NOT make implementation decisions at the code level -- delegate ALL coding to execution agents. You DO make architectural and strategic decisions using your CTO decision-making framework."
- **Validation:** Line updated, distinction between code decisions (no) and architectural decisions (yes) is clear
- **Error States:** N/A

**FR3.3:** The execute command must include a "Decision Authority" section defining what the CTO-orchestrator decides vs escalates during execution.
- **Input:** New section after CTO personality adoption
- **Output:** Section listing: (a) CTO decides: code review triage (fix/defer/skip for all severity levels), fix agent spawning, task completion review response, wave ordering adjustments; (b) CTO escalates to user per CTO escalation criteria: costs >$20/month, external lock-in, people decisions, value conflicts, scope changes, <70% confidence + high downside
- **Validation:** Section present, criteria match CTO.md escalation criteria exactly
- **Error States:** N/A

**FR3.4:** The execute command code review handling (lines 1455-1466) must be replaced with CTO-driven autonomous triage.
- **Input:** Current behavior: CRITICAL/HIGH auto-fix, MEDIUM/LOW pause for user triage
- **Output:** New behavior: CTO triages ALL findings autonomously. CRITICAL/HIGH: spawn fix agents immediately. MEDIUM: CTO assesses -- fix now (spawn agent) or defer (add to tech debt). LOW: CTO assesses -- skip or add to tech debt. No user interruption for triage decisions.
- **Validation:** No "pause for user" or "ask user" language in triage section
- **Error States:** If fix agent fails on a CRITICAL finding, CTO escalates to user with context. If >3 fix agents fail, CTO escalates entire review to user.

**FR3.5:** The execute command must include a new post-code-review step: CTO-advisor task completion review.
- **Input:** New step between "code review passes" and "memory update"
- **Output:** After code review passes (with or without CTO-triaged fixes), invoke CTO-advisor via Task tool: `Task(subagent_type="cto-technical-advisor", prompt="Review task completion for [task file]. Verify all tasks in the XML file were completed correctly. Check: (a) all parent tasks have status=done, (b) verify steps actually passed, (c) commits exist for each task, (d) no tasks were skipped or partially done. Return: completion status, gaps found, recommendation (proceed/fix/escalate).")`
- **Validation:** Step present in post-execution flow, invocation uses Task tool with correct subagent_type
- **Error States:** CTO-advisor finds gaps -- CTO-orchestrator decides: if gaps are minor (missing test, documentation), spawn fix agent. If gaps are significant (entire task skipped, wrong approach), escalate to user.

**FR3.6:** The updated post-execution flow must be:
```
1. ALL TASKS COMPLETE
   |
2. INVOKE CODE REVIEW (mandatory, existing)
   |
3. CTO TRIAGES CODE REVIEW FINDINGS (new)
   - CRITICAL/HIGH: spawn fix agents
   - MEDIUM: CTO decides fix/defer
   - LOW: CTO decides skip/tech-debt
   |
4. FIX AGENTS RUN (if any spawned)
   |
5. VERIFY FIXES PASS
   |
6. CTO-ADVISOR TASK COMPLETION REVIEW (new)
   - Verifies all XML tasks completed correctly
   |
7. CTO RESPONDS TO ADVISOR FINDINGS (new)
   - Minor gaps: spawn fix agent
   - Significant gaps: escalate to user
   |
8. INVOKE MEMORY UPDATE (mandatory, existing)
   |
9. OFFER ARCHIVE WORKFLOW (existing)
```
- **Input:** Updated flow diagram in execute.md
- **Output:** Flow diagram matching above, with each step clearly documented
- **Validation:** Flow is sequential, no ambiguity about step ordering
- **Error States:** Covered by individual step error handling (FR3.4, FR3.5)

### PRD Command CTO Integration (Component 4)

**FR4.1:** The PRD command must read `.claude/agents/cto.md` at startup and adopt its decision-making framework.
- **Input:** New instruction block in prd.md after "Role & Authority" section
- **Output:** Instruction: "Read .claude/agents/cto.md and adopt its decision-making framework. During discovery rounds, make architectural decisions using CTO values instead of asking the user. Escalate only per CTO escalation criteria."
- **Validation:** Instruction present before questioning process begins
- **Error States:** If .claude/agents/cto.md not found, fall back to existing behavior (ask user for architectural decisions)

**FR4.2:** The PRD command must include a "Decision Authority" section for architectural calls during discovery.
- **Input:** New section in prd.md
- **Output:** CTO decides during PRD discovery: storage approach, data architecture, integration patterns, tooling choices within established patterns, implementation strategy, API design. CTO escalates: costs >$20/month, external lock-in, scope changes, <70% confidence + high downside.
- **Validation:** Questioning rounds reference Decision Authority for architectural questions
- **Error States:** N/A

**FR4.3:** The PRD command questioning process must be updated so architectural questions are resolved by CTO judgment instead of asked to the user.
- **Input:** Current Round 2+ questions include architectural queries ("Follow [pattern] or introduce new?", "Integrate with [system] or standalone?")
- **Output:** These become CTO decisions: the command makes the call using CTO values, states the decision briefly in the round summary ("Going with [pattern] because [reason]"), and only asks the user about non-architectural requirements
- **Validation:** User-facing questions are purely about requirements and desired behavior, not technical approach
- **Error States:** If CTO is <70% confident on an architectural call AND downside is significant, escalate to user with recommendation

### Bugs Command CTO Integration (Component 5)

**FR5.1:** The bugs command must read `.claude/agents/cto.md` at startup and adopt its decision-making framework.
- **Input:** New instruction block in bugs.md after "Role & Authority" section
- **Output:** Same pattern as FR3.1 and FR4.1
- **Validation:** Instruction present before investigation begins
- **Error States:** Fallback to existing behavior if file not found

**FR5.2:** The bugs command must include a "Decision Authority" section for bug assessment decisions.
- **Input:** New section in bugs.md
- **Output:** CTO decides: complexity score validation (adjust Explore's assessment if CTO disagrees), tier routing (inline 1-2 / task-writer 3-6 / prd-writer 7+), solution recommendation (which fix option from Phase 4), effort estimation validation. CTO escalates: fixes affecting other people's workflows, fixes with >$20/month cost implications, fixes where CTO is <70% confident on root cause.
- **Validation:** Phase 5 (Recommendation & Next Steps) references CTO Decision Authority
- **Error States:** N/A

**FR5.3:** The bugs command Phase 5 tier decision must be made by CTO judgment rather than presented to the user.
- **Input:** Current: complexity score drives tier routing but user sees the recommendation
- **Output:** CTO validates Explore's complexity assessment, makes the tier call, states decision: "Going with [tier] because [reason]." Proceeds directly to handoff without waiting for user confirmation on technical approach.
- **Validation:** No "which option do you prefer?" for tier decisions
- **Error States:** If CTO disagrees significantly with Explore's assessment, CTO states its reasoning and proceeds with its own assessment

### Feature Command CTO Integration (Component 6)

**FR6.1:** The feature command must read `.claude/agents/cto.md` at startup and adopt its decision-making framework.
- **Input:** New instruction block in feature.md after "Role & Authority" section
- **Output:** Same pattern as FR3.1, FR4.1, FR5.1
- **Validation:** Instruction present before analysis begins
- **Error States:** Fallback to existing behavior if file not found

**FR6.2:** The feature command must include a "Decision Authority" section for feature assessment decisions.
- **Input:** New section in feature.md
- **Output:** CTO decides: complexity score validation, tier routing, design approach (pattern selection, component structure), effort estimation. CTO escalates: features affecting other people, scope changes, <70% confidence + high downside.
- **Validation:** Phase 4 (Complexity Assessment & Decision) references CTO Decision Authority
- **Error States:** N/A

**FR6.3:** The feature command Phase 5 tier decision must be made by CTO judgment.
- **Input:** Current: three-tier decision based on complexity score
- **Output:** CTO validates Explore's assessment, makes tier call, proceeds to handoff. For inline implementation (complexity 1-2), CTO proceeds without confirmation. For task-writer handoff (3-6), CTO proceeds with brief decision statement. For prd-writer handoff (7+), CTO proceeds with rationale.
- **Validation:** No user triage loop for tier decisions
- **Error States:** Same as FR5.3

---

## Data Specifications

### Data Models

No new data structures are introduced. This feature modifies prompt files (markdown) and agent definition files (markdown with YAML frontmatter).

**Agent File Format (existing pattern):**
```yaml
---
name: agent-name
description: Brief description
model: opus
color: green
disallowedTools: Write, Edit, NotebookEdit
---

[Agent instructions in markdown]
```

**Command File Format (existing pattern):**
```yaml
---
description: Brief command description
---

[Command instructions in markdown]
```

### CTO-Advisor Task Completion Review Request

When execute invokes CTO-advisor for task completion review:

```
Task(
  subagent_type: "cto-technical-advisor",
  prompt: """
  Review task completion for: [TASK_FILE_PATH]
  Feature: [FEATURE_NAME]

  Verify all tasks in the XML file were completed correctly:
  1. All parent tasks have status=done
  2. Verify steps results (pass/fail)
  3. Commits exist for each completed task
  4. No tasks skipped or partially implemented
  5. Overall feature coherence (do the pieces fit together?)

  STATE.md content:
  [STATE_MD_CONTENT]

  Return:
  - Completion Status: [COMPLETE / GAPS_FOUND / SIGNIFICANT_ISSUES]
  - Gaps: [list of specific gaps if any]
  - Recommendation: [PROCEED / FIX_MINOR / ESCALATE]
  - Confidence: [percentage]
  """
)
```

### CTO-Advisor Response Format (Decision-Ready Briefing)

When serving the CTO (as opposed to standalone use):

```markdown
**Verdict:** [Clear one-line assessment]
**Confidence:** [X%]

**Key Findings:**
- [Finding 1 with evidence]
- [Finding 2 with evidence]

**Gaps (if any):**
- [Gap 1]: [severity] -- [what's missing]
- [Gap 2]: [severity] -- [what's missing]

**Recommendation:** [PROCEED / FIX_MINOR / ESCALATE]
**Rationale:** [2-3 sentences]
```

### CTO Code Review Triage Decision Format

```markdown
**Triage Decision: [FINDING_ID]**
Severity: [CRITICAL/HIGH/MEDIUM/LOW]
Action: [FIX_NOW / DEFER_TECH_DEBT / SKIP]
Reason: [Brief CTO rationale]
[If FIX_NOW:] Fix Agent: spawning with [approach]
[If DEFER:] Tech Debt: logged to .ai/TECH_DEBT.md
```

---

## User Flow Examples

### Happy Path: Execute Command with CTO Integration
1. User runs `/execute /tasks/cto-command-integration/task.xml`
2. Orchestrator reads `.claude/agents/cto.md`, adopts CTO decision-making framework
3. Orchestrator parses XML tasks, builds execution waves (existing flow)
4. Execution agents complete all parent tasks (existing flow)
5. Code review runs automatically (existing)
6. Code review returns 1 HIGH finding, 3 MEDIUM findings, 2 LOW findings
7. CTO-orchestrator triages autonomously:
   - HIGH: spawns fix agent immediately
   - MEDIUM #1: assesses as real issue, spawns fix agent
   - MEDIUM #2: assesses as style preference, defers to tech debt
   - MEDIUM #3: assesses as legitimate concern, spawns fix agent
   - LOW #1: assesses as negligible, skips
   - LOW #2: assesses as valid minor improvement, defers to tech debt
8. Fix agents run (3 spawned), all pass verification
9. CTO-orchestrator invokes CTO-advisor: "Review task completion for task.xml"
10. CTO-advisor responds: "Verdict: All tasks complete. Confidence: 95%. Recommendation: PROCEED"
11. CTO-orchestrator proceeds to memory update
12. Memory update runs (existing)
13. Archive workflow offered (existing)
14. User sees complete execution summary -- zero interruptions for technical decisions

### Error Flow 1: CTO Escalates During Execution
1. User runs `/execute` with a task file
2. During code review triage, CTO encounters a finding about external API integration that would commit to a third-party service
3. CTO recognises this as "external lock-in" -- matches escalation criteria
4. CTO pauses triage and presents to user:
   ```
   Escalating: Code review finding [CR-7] suggests integrating with [Service X]
   Context: This would create a dependency on [Service X]'s API
   Recommendation: Defer this finding -- it's a design decision, not a code quality issue
   Uncertain about: Whether you're comfortable with this vendor dependency
   ```
5. User responds with direction
6. CTO resumes triage with user's input applied

### Error Flow 2: CTO-Advisor Finds Task Gaps
1. Execute command completes all tasks, code review passes after CTO triage
2. CTO-orchestrator invokes CTO-advisor for task completion review
3. CTO-advisor responds:
   ```
   Verdict: Gaps found in task completion
   Confidence: 85%
   Gaps:
   - Task 3.2 (unit tests): verify step passed but only 2 of 4 specified test cases written
   - Task 5.0 (documentation): status=done but no documentation file created
   Recommendation: FIX_MINOR
   ```
4. CTO-orchestrator assesses: task 3.2 is a minor gap (2 missing tests), task 5.0 is more concerning
5. CTO spawns fix agent for task 3.2 with specific instructions
6. CTO spawns fix agent for task 5.0 with specific instructions
7. Both fix agents complete
8. CTO proceeds to memory update

### Error Flow 3: Multiple Fix Agent Failures
1. Code review returns 4 CRITICAL findings
2. CTO spawns fix agents for all 4
3. Fix agent 1 passes, fix agent 2 passes, fix agents 3 and 4 fail
4. CTO assesses: >1 CRITICAL fix agent failure is significant
5. CTO escalates to user:
   ```
   Escalating: 2 of 4 CRITICAL code review fixes failed
   Context: [Finding 3] and [Finding 4] could not be resolved by fix agents
   Recommendation: Manual investigation needed -- these may require architectural changes
   Uncertain about: Whether the task design accounts for [specific constraint]
   ```
6. Execution pauses for user input

### Edge Case: CTO.md File Not Found
1. User runs `/execute` (or any command)
2. Command attempts to read `.claude/agents/cto.md`
3. File does not exist (perhaps user cloned repo without agent files)
4. Command logs: "Warning: .claude/agents/cto.md not found. Running without CTO decision-making framework."
5. Command proceeds with existing behavior -- user triage for code review, questions for architectural decisions
6. All existing functionality works as before

---

## Technical Considerations

### Key Files & Documentation

**Relevant Files (from codebase):**
- `~/.claude/agents/cto.md` -- Source CTO agent file (143 lines, user-level)
- `.claude/agents/cto.md` -- Target CTO agent file (new, project-level copy)
- `.claude/agents/cto-technical-advisor.md:1-119` -- Advisor agent to update
- `.claude/commands/execute.md:11-97` -- Orchestrator philosophy section to modify
- `.claude/commands/execute.md:24` -- "DO NOT make implementation decisions" line to change
- `.claude/commands/execute.md:1417-1469` -- Post-execution steps to extend
- `.claude/commands/execute.md:1455-1466` -- Code review failure handling to replace
- `.claude/commands/prd.md:1-80` -- Role & Authority and stopping criteria
- `.claude/commands/prd.md:139-300` -- Questioning process to modify
- `.claude/commands/bugs.md:238-289` -- Three-tier decision section
- `.claude/commands/feature.md:215-262` -- Complexity assessment and tier decision

**External Documentation:**
- None -- this is internal tooling using existing Claude Code capabilities

### Architecture
Follows agent file reference pattern. Commands reference the CTO agent file at startup and adopt its decision framework as a personality overlay. State remains in the existing mechanisms (XML task files, STATE.md, code review output). Data flows through existing Task tool subagent invocations.

### Integration Points
- `.claude/agents/cto.md` is read by all four commands at startup
- `.claude/agents/cto-technical-advisor.md` is invoked by execute.md via Task tool after code review
- Execute.md spawns fix agents using existing execution-agent subagent_type
- PRD.md, bugs.md, feature.md use CTO judgment inline (no additional agent calls required)

### Patterns & Conventions
- New pattern: "CTO personality overlay" -- read agent file at startup, adopt decision framework
- New pattern: "Decision Authority section" -- standardised section format across commands
- Follows existing: Task tool subagent invocation for CTO-advisor
- Follows existing: Agent frontmatter format (name, description, model, color, disallowedTools)
- Consistency: all four commands use identical file reference instruction and fallback behavior

### Performance
- CTO.md is 143 lines -- negligible context window impact
- CTO-advisor task completion review adds one subagent invocation to execute flow
- No API calls, no external services, no runtime performance impact
- Execute.md is already ~1600 lines; CTO additions estimated at ~80-100 lines (Decision Authority section + updated triage logic + task completion review step)

### Security
- No authentication changes
- No new credentials or API keys
- No user data handling changes
- CTO escalation criteria include security-sensitive decisions (external lock-in, costs)

---

## Assumptions & Validation

### Assumption 1: File reference approach won't significantly impact context window
- **Risk if Wrong:** Commands run out of context on complex tasks because CTO.md consumes too much
- **Validation Method:** CTO.md is 143 lines. Execute.md is ~1600 lines. Adding 143 lines is ~9% increase. Well within Claude's context limits.
- **Confidence:** High
- **Owner:** Implementer
- **Timeline:** Verify during implementation

### Assumption 2: CTO personality won't conflict with command-specific instructions
- **Risk if Wrong:** CTO overrides important command guardrails (e.g., orchestrator starts making code edits because CTO says "just handle it")
- **Validation Method:** CTO file explicitly says "You make architectural and strategic technical decisions -- you don't write code." This aligns with orchestrator's "DO NOT edit code" constraint. CTO personality is additive decision authority, not operational override.
- **Confidence:** High
- **Owner:** Implementer
- **Timeline:** Verify during implementation by reviewing potential conflicts

### Assumption 3: CTO-advisor task completion review adds value vs just trusting verify steps
- **Risk if Wrong:** Unnecessary overhead slowing execute without catching real issues
- **Validation Method:** Verify steps check individual task outputs (did the test pass?). CTO-advisor checks holistic completion (were all tasks actually done? do the pieces fit together?). These are complementary, not redundant.
- **Confidence:** Medium (80%) -- may prove unnecessary for simple task files. Worth trying.
- **Owner:** Iain (after a few executions with the feature)
- **Timeline:** Evaluate after 5 executions

### Assumption 4: CTO can triage MEDIUM code review findings without user context
- **Risk if Wrong:** CTO makes wrong triage calls on MEDIUM findings that require domain knowledge the CTO doesn't have
- **Validation Method:** CTO has access to project memory (.ai/ files) and the code review context. For truly domain-specific decisions, CTO escalation criteria ("less than 70% confident AND high downside") should catch these.
- **Confidence:** Medium (75%) -- some MEDIUM findings may be domain-specific
- **Owner:** Iain
- **Timeline:** Monitor first 3 executions for incorrect triage calls

---

## Breaking Changes Analysis

### User Impact
- [x] Changes existing workflows? Yes -- commands now make decisions autonomously that previously interrupted the user. **Impact:** Fewer interruptions. **Migration:** None needed -- this is purely additive behavior.
- [ ] Users must take action? No -- commands work as before, just with smarter decision-making.
- [ ] Data migrations? No.
- [ ] Communication plan? Changelog noting CTO integration in fat-controller commands.

### API/Interface Changes
- [ ] Removing/changing APIs? No APIs affected.
- [ ] Breaks integrations? No -- all changes are within prompt files.
- [x] Backward compatibility? Yes -- if CTO.md file is missing, all commands fall back to existing behavior.

### Data Model Changes
- [ ] Schema changes? No.
- [ ] Data migration? No.
- [ ] Old/new coexist? N/A.

**Fully backward compatible.** If `.claude/agents/cto.md` doesn't exist, all commands fall back to their current behavior. No existing functionality is removed.

---

## Security Considerations

### Authentication & Authorization
- [ ] Changes auth flow? No.
- [ ] New permissions? No.
- [ ] User data access modified? No.
- [ ] Database/security policies affected? No.

### Data Privacy
- [ ] Collects new user data? No.
- [ ] PII involved? No.
- [ ] Privacy policies affected? No.

### API Security
- [ ] New API keys/credentials? No.
- [ ] Rate limiting affected? No.
- [ ] New attack vectors? No.

**No significant security considerations beyond standard practices.** The CTO escalation criteria include escalating for external service commitments and costs, which provides a security-conscious safety net.

---

## Asset & Resource Requirements

### Visual Assets
- [ ] New assets? No.

### Configuration Assets
- [x] New config files? Yes -- `.claude/agents/cto.md` (copy of existing user-level file)
- [ ] Environment config? No.
- [ ] Secret management? No.

**No special assets required beyond the agent file copy.**

---

## Acceptance Criteria

### For Component 1 (Project-Level CTO Agent)
- [ ] `.claude/agents/cto.md` exists and matches `~/.claude/agents/cto.md` content
  - **Test:** `diff ~/.claude/agents/cto.md .claude/agents/cto.md` returns no differences
- [ ] File is tracked by git
  - **Test:** `git ls-files .claude/agents/cto.md` returns the file path

### For Component 2 (CTO-Advisor Update)
- [ ] "Relationship to CTO" section exists in cto-technical-advisor.md
  - **Test:** Read file, verify section present with dual-use explanation
- [ ] Corporate framing removed, tone matches CTO style
  - **Test:** No instances of "20 years of battle-tested experience" or similar corporate language
- [ ] `disallowedTools: Write, Edit, NotebookEdit` in frontmatter
  - **Test:** Parse YAML frontmatter, verify field present
- [ ] Decision-ready briefing format documented
  - **Test:** Response structure section includes briefing format
- [ ] Standalone usability preserved
  - **Test:** File still functions as standalone agent (feasibility spectrum, implementation options, risk assessment all present)

### For Component 3 (Execute CTO Integration)
- [ ] CTO personality adoption instruction present in execute.md
  - **Test:** Grep for "Read .claude/agents/cto.md" in execute.md
- [ ] Line 24 updated to allow CTO-level decisions
  - **Test:** "DO NOT make implementation decisions at the code level" present (not original text)
- [ ] Decision Authority section present
  - **Test:** Section with CTO decides/escalates in execute.md
- [ ] Code review triage is CTO-driven (no user interruption)
  - **Test:** No "pause for user" or "ask user" in triage section
- [ ] CTO-advisor task completion review step present in post-execution flow
  - **Test:** Task tool invocation with subagent_type="cto-technical-advisor" in post-code-review section
- [ ] Updated flow diagram matches FR3.6
  - **Test:** Flow diagram has 9 steps matching specification
- [ ] Fallback behavior documented for missing CTO.md
  - **Test:** Fallback instruction present

### For Components 4, 5, 6 (PRD, Bugs, Feature CTO Integration)
- [ ] CTO personality adoption instruction present in each command
  - **Test:** Grep for "Read .claude/agents/cto.md" in prd.md, bugs.md, feature.md
- [ ] Decision Authority section present in each command
  - **Test:** Section exists with command-specific CTO decides/escalates
- [ ] Architectural/technical decisions made by CTO, not asked to user
  - **Test:** No user-facing questions about technical approach in decision sections
- [ ] Fallback behavior documented for missing CTO.md
  - **Test:** Fallback instruction present in each command
- [ ] Consistent Decision Authority section format across all four commands
  - **Test:** Section headings and structure match across execute.md, prd.md, bugs.md, feature.md

### General
- [ ] All error states handled gracefully -- **Test:** Verify fallback for missing CTO.md in all four commands
- [ ] No runtime errors/warnings -- **Test:** Run each command manually, verify no errors
- [ ] CTO escalation criteria consistent across all commands -- **Test:** Compare escalation criteria in all Decision Authority sections against CTO.md source
- [ ] Existing command functionality preserved -- **Test:** Commands still perform their core functions (execute runs tasks, prd generates PRDs, bugs investigates bugs, feature implements features)

---

## Implementation Roadmap

### Phase 1: Foundation (Critical Priority)
**Goal:** Establish project-level CTO agent and update CTO-advisor relationship
**Components:** Component 1, Component 2
**Tasks:**
1. Copy ~/.claude/agents/cto.md to .claude/agents/cto.md
2. Update .claude/agents/cto-technical-advisor.md: add Relationship to CTO section, align tone, add disallowedTools, update response structure for decision-ready briefing
3. Verify both files parse correctly and cto-advisor preserves standalone capabilities
**Validation:** Both agent files exist, frontmatter valid, no capability regressions in cto-advisor

### Phase 2: Core Command Integration (High Priority)
**Goal:** Integrate CTO personality into all four commands
**Components:** Component 3, Component 4, Component 5, Component 6
**Tasks:**
1. Add CTO personality overlay to execute.md (startup reference, update line 24, add Decision Authority section)
2. Replace execute.md code review triage with CTO-driven triage (lines 1455-1466)
3. Add CTO-advisor task completion review step to execute.md post-execution flow
4. Add CTO personality overlay to prd.md (startup reference, Decision Authority, update questioning process)
5. Add CTO personality overlay to bugs.md (startup reference, Decision Authority, update Phase 5)
6. Add CTO personality overlay to feature.md (startup reference, Decision Authority, update Phase 5)
**Dependencies:** Phase 1 must complete first (commands reference the CTO agent file)
**Validation:** All four commands contain CTO reference, Decision Authority sections, and fallback behavior. Execute.md has updated post-execution flow.

### Phase 3: Testing and Validation (Medium Priority)
**Goal:** Verify integration works end-to-end
**Tasks:**
1. Run each command manually and verify CTO decisions appear in output
2. Verify execute command triages code review findings without user interruption
3. Verify CTO-advisor task completion review invocation works
4. Verify fallback behavior when CTO.md is missing
5. Verify escalation criteria trigger correctly (test with a scenario matching escalation criteria)
**Validation:** All acceptance criteria pass

### Rollout
- [ ] All changes are in prompt/agent files -- no deployment needed, changes take effect on next command invocation
- [ ] Monitor first 5 executions for incorrect CTO triage calls
- [ ] Monitor first 3 PRD generations for inappropriate architectural decisions
- [ ] Adjust CTO Decision Authority sections if decision boundaries need tuning

### Critical Path
**Blockers:** None -- all files are under project control, no external dependencies
**Critical Timeline:** Phase 1 then Phase 2 (sequential dependency). Phase 3 can overlap with Phase 2 for completed commands.
**Risk Mitigation:** Fallback behavior in all commands means a bad CTO integration doesn't break existing workflows -- it just gets ignored if the file is missing.

---

## Non-Goals

- Will NOT create a new agent -- the CTO agent already exists, we're copying and referencing it
- Will NOT change CTO values or decision criteria -- the CTO.md file is copied as-is, any values changes are a separate concern
- Will NOT add CTO personality to agents other than the four core commands -- other commands (TaskGen, code-review, update, etc.) are out of scope
- Will NOT make CTO-advisor non-standalone -- it must remain callable directly by the user for ad-hoc technical questions
- Will NOT add a CTO personality toggle or configuration -- it's always on when the file exists, always off when it doesn't
- Will NOT modify the execution-agent or explore agent -- only the orchestrator layer gets CTO personality

---

## Open Questions

- [ ] Should the CTO-advisor task completion review be skippable for simple task files (e.g., <3 tasks)?
  - **Impact:** Could reduce overhead for trivial executions
  - **Options:** Always run / Skip for <3 tasks / Make configurable
  - **Owner:** Iain
  - **Deadline:** After first 5 executions with the feature

- [ ] Should CTO triage decisions be logged to a file (e.g., `.ai/cto-decisions.log`) for review?
  - **Impact:** Would provide audit trail of autonomous decisions
  - - **Options:** No logging / Log to file / Include in STATE.md
  - **Owner:** Iain
  - **Deadline:** After first 3 executions

---

## Red Flags & Risks

### Prompt Length: Execute.md Size
**Description:** execute.md is already ~1600 lines. Adding CTO personality reference, Decision Authority section, updated triage logic, and task completion review step adds ~80-100 lines.
**Impact:** Increases context consumption for every execute invocation. At ~1700 lines, still well within limits, but approaching the point where every additional line matters.
**Mitigation:** Keep CTO reference compact (one instruction line + file path, not embedded values). Decision Authority section should be concise (bullet points, not paragraphs). CTO.md itself is only 143 lines and is read once at startup.
**Owner:** Implementer
**Status:** Open -- mitigated by design (compact references)

### Decision Propagation: Wrong CTO Calls in PRD
**Description:** If CTO makes a wrong architectural decision during PRD discovery, that decision propagates through task generation and execution -- potentially building the wrong thing.
**Impact:** Could result in implementation that doesn't meet actual requirements. Cost is proportional to how far execution gets before the error is caught.
**Mitigation:** CTO decisions are visible in PRD output. User reviews PRD before running /TaskGen. This creates a natural checkpoint. CTO escalation criteria (<70% confidence + high downside) should catch genuinely uncertain decisions.
**Owner:** Iain (review PRD output)
**Status:** Open -- mitigated by review checkpoint

### Role Confusion: CTO vs CTO-Advisor
**Description:** Two agents with "CTO" in the name could confuse users about which one to invoke and what each does.
**Impact:** User invokes wrong agent, gets advice when they wanted a decision (or vice versa).
**Mitigation:** Clear naming (cto = decides, cto-technical-advisor = researches). Clear descriptions in frontmatter. Relationship section in cto-advisor explicitly explains the distinction. Commands only reference the CTO agent -- users interact with CTO-advisor only when they explicitly want research.
**Owner:** Implementer (clear naming/docs)
**Status:** Open -- mitigated by documentation

**Risk Summary:**
- High Risk: 0
- Medium Risk: 3 (prompt length, decision propagation, role confusion)
- Mitigation Plan: All three risks have concrete mitigations. Prompt length is addressed by compact references. Decision propagation is addressed by PRD review checkpoint. Role confusion is addressed by clear naming and documentation.
