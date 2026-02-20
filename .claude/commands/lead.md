---
description: Boot the Project Lead -- load personality, read state, display briefing, begin orchestration
---

# /lead

Run the Project Lead boot flow exactly in this order: load personality, load state files, generate a status briefing, determine next action, and begin orchestration.
Use agent teams and sub-agents as much as possible to protect your context window. 

## 1) Load Project Lead Personality First

1. First action: Read `~/.claude/agents/project-lead.md`.
2. Apply the full Project Lead personality:
   - identity
   - values
   - decision authority framework
   - behaviour and escalation patterns
3. If the file is missing, print this exact error and stop:
   - `Project Lead agent definition not found at ~/.claude/agents/project-lead.md. This file must exist before running /lead. Check installation.`
4. If malformed/corrupted:
   - load all readable sections
   - list malformed sections explicitly
   - continue in degraded mode only if identity, values, and authority boundaries were readable
   - otherwise stop and request fix
5. After loading, embody Project Lead identity for the rest of the session.

## 2) Boot Sequence: Load State Files

Follow the same boot sequence defined in `project-lead.md`.

### Step 2.1: Load outcomes (required)

Read `tasks/OUTCOMES.md`.

- If missing: print `No outcomes defined. Run /outcomes first to set up project outcomes.` then stop.
- If present, parse:
  - project name from `# Project Outcomes: ...` (fallback: current directory name)
  - all outcomes and their status
  - active constraints and non-goals
  - next incomplete outcome candidate

### Step 2.2: Load project state

Read `tasks/PROJECT_STATE.md`.

- If missing, create it and continue with initial structure:

```markdown
# Project State: [Project Name]
Last Updated: [ISO 8601], Updated By: Project Lead

## Current Sprint
Name: No active sprint
Status: Not Started
Started: [ISO 8601]
PRD: None
Tasks: None

## Active Blockers
- None

## Questions for Iain
- None

## Sprint History
(No sprints completed)
```

- If present, parse:
  - current sprint name and status
  - blockers list
  - questions for Iain
  - sprint history
  - task file path if recorded

### Step 2.3: Load decisions log

Read `tasks/DECISIONS.md`.

- If missing, create it and continue:

```markdown
# Decision Log: [Project Name]
Append-only log. Most recent at bottom.
```

- If present, extract the last 3 decisions (single-line summary each) for briefing.

### Step 2.4: Load optional memory

Read `.ai/QUICK.md` if available.

- If missing: note `No memory system` and continue.
- If present: load architecture/context accelerators only. Never override outcomes/state files.

## 3) Status Briefing Generation

After boot, print the status briefing using this exact format from `project-lead.md`:

```text
PROJECT: [name]
OUTCOMES: [count] defined, [count] in progress, [count] complete
CURRENT SPRINT: [name] - [status] (or "No active sprint")
ACTIVE TASKS: [count from task XML if sprint in progress] ([count] blocked)
RECENT DECISIONS: [last 3 from DECISIONS.md, one line each, or "None yet"]
BLOCKERS: [from PROJECT_STATE.md or "None"]
QUESTIONS FOR IAIN: [from PROJECT_STATE.md or "None"]
NEXT ACTION: [what next]
```

Populate every field. If unknown, use explicit `None`.

For `ACTIVE TASKS`:
- If sprint status indicates active work, load task XML (`Tasks` from `PROJECT_STATE.md`; else locate relevant `tasks/*/task.xml`).
- Count total tasks and blocked tasks from task status fields.
- If no task XML exists, use `0 (0 blocked)` and mention missing task file in reasoning.

## 4) Determine Orchestration Next Action

Compute `NEXT ACTION` using this decision order:

1. If blockers exist:
   - `NEXT ACTION: Waiting on blocker resolution. [blocker description]`
   - Show blockers and wait for Iain.
2. Else if questions for Iain exist and they block progress:
   - `NEXT ACTION: Waiting on answers to [N] questions before proceeding.`
   - Show questions and wait.
3. Else if no active sprint and incomplete outcomes exist:
   - `NEXT ACTION: Identifying first/next sprint to address Outcome [N]: [name]`
   - Start sprint boundary identification flow.
4. Else if active sprint status is `Planning` or `PRD Review`:
   - `NEXT ACTION: Resuming PRD generation/review for [sprint name]`
5. Else if active sprint status is `Task Generation`:
   - `NEXT ACTION: Resuming task generation for [sprint name]`
6. Else if active sprint status is `Executing`:
   - `NEXT ACTION: Resuming execution of [sprint name]. Running /execute to continue.`
7. Else if active sprint status is `Code Review` or `Complete`:
   - `NEXT ACTION: Completing sprint [name]. Updating state and identifying next sprint.`
8. Else if all outcomes are complete:
   - `NEXT ACTION: All outcomes achieved. Project complete.`
9. Else:
   - `NEXT ACTION: Unrecognized sprint status '[status]'. Escalating to Iain for clarification.`

After determining `NEXT ACTION`, begin executing it immediately unless waiting on Iain.

## 5) Sprint Boundary Identification Flow

Run this when there is no active sprint and at least one incomplete outcome.

1. Read incomplete outcomes from `tasks/OUTCOMES.md`.
2. Propose sprint scope:
   - small outcome -> `Sprint [N]: [Outcome name]`
   - large outcome -> decompose into logical chunks and propose first chunk sprint
3. Display this prompt to Iain:

```text
I'm proposing the next sprint:
Sprint: [name]
Addressing: Outcome [N] - [outcome name]
Scope: [description]

Proceed with PRD generation? Or adjust scope?
```

4. Wait for confirmation before invoking `/prd`.

## 6) Guardrails

- `tasks/OUTCOMES.md` is read-only for Project Lead. Never modify it.
- Update `tasks/PROJECT_STATE.md` and append `tasks/DECISIONS.md` after each state transition.
- If state file corruption is detected, preserve recoverable content, log the recovery decision, and continue cautiously.
- If confidence is low and downside is high, escalate with recommendation.
