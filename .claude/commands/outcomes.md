---
description: Interactive project setup -- discover outcomes, create state files, enable Project Lead orchestration
---

# Project Outcomes Setup Command

## Role and Goal
You are configuring the project for Project Lead orchestration.
Your job is to:
- Discover clear project outcomes through interactive questioning
- Create and maintain `tasks/OUTCOMES.md`
- Initialize `tasks/PROJECT_STATE.md` and `tasks/DECISIONS.md` without destroying history
- Optionally add the Project Lead personality section to `CLAUDE.md`

## Required References (Read First)
Before taking any action:
1. Read `~/.claude/agents/project-lead.md` and use its exact templates for:
- `OUTCOMES.md`
- `PROJECT_STATE.md`
- `DECISIONS.md`
- `CLAUDE.md` Project Lead section

## 1) Idempotency Gate (Run First)
1. Check whether `tasks/OUTCOMES.md` exists.
2. If it exists, ask exactly:
   `Existing outcomes found. Would you like to: (1) Review and update outcomes, (2) Start fresh (overwrites OUTCOMES.md only), (3) Cancel`
3. If user selects `(1) Review and update outcomes`:
- Read existing outcomes and use them as starting context for discovery.
- Re-run the full discovery and confirmation process.
4. If user selects `(2) Start fresh`:
- Continue discovery.
- Overwrite `tasks/OUTCOMES.md` after confirmation.
- Preserve existing `tasks/PROJECT_STATE.md` and `tasks/DECISIONS.md`.
5. If user selects `(3) Cancel`: stop immediately.

## 2) Interactive Discovery
Rules:
- Max 3 questions per batch. Wait for answers before asking more.
- Start open, then refine. Don't prescribe how many outcomes there should be.
- Push back on vagueness until criteria are measurable.

### Round 1: Open Context Gathering (1 question)
Start with one open prompt:
`In your own words, describe this project. The context, the history, what you're trying to achieve -- in as much detail as you can.`

Let Iain talk. Don't interrupt with follow-ups until he's done.

### Round 2: Extract and Propose Outcomes (1-3 questions)
From what Iain described, extract candidate outcomes yourself. Present them back:
`Based on what you've described, it sounds like these might be your outcomes:
1. [Extracted outcome] -- [your one-sentence summary]
2. [Extracted outcome] -- [your one-sentence summary]
...
Is that accurate? Are there others you'd add, or any of these wrong?`

There might be 1 outcome or 10. Don't constrain the count -- let the project dictate it.

Then ask about success criteria:
`For each of those, what does "done" look like? How will you know it's complete?`

### Round 3+: Refinement (only if needed, max 3 questions per batch)
Continue rounds until stopping criteria are met. Focus on:
- **Contradictions**: If outcomes conflict with each other, flag it immediately. `Outcomes [X] and [Y] seem to pull in different directions -- which takes priority?`
- **Vagueness**: `You said [vague term] -- give me something measurable.`
- **Dependencies**: If an outcome relies on external information, systems, people, or processes you don't know about, call it out. `Outcome [X] seems to depend on [thing] -- can you tell me more about that?`
- **Non-goals**: `What should this project NOT do?`
- **Constraints**: `Any hard constraints? Timeline, budget, technical, regulatory?`

### Stopping Criteria
Stop questioning when all are true:
- Each outcome fits in one sentence
- Each outcome has at least one measurable success criterion
- No unresolved contradictions between outcomes
- Dependencies on external information are documented or resolved
- Constraints are explicit
- Non-goals are identified

## 3) Confirmation (Required Before File Creation)
After stopping criteria are met, summarize and ask for confirmation:

`Based on our discussion, here are the project outcomes:
Outcome 1: [name] -- [one sentence]
  Success: [criteria]
  Constraints: [list]
Outcome 2: ...
Non-Goals: [list]

Is this correct? Anything to add or change?`

Wait for explicit confirmation before creating or updating files.

## 4) State File Creation Logic
After user confirms:

1. Ensure `tasks/` exists.
- If not, create it.
- If directory creation fails, report the error and stop.

2. Create or overwrite `tasks/OUTCOMES.md`.
- Populate using the `OUTCOMES.md` template from `~/.claude/agents/project-lead.md`.
- Include all required fields:
  - Project Name
  - Created date
  - Last Reviewed date
  - Owner: `Iain Forrest`
  - Each outcome with: Description, Success Criteria, Constraints, Status (`Not Started`), Sprint(s) (`TBD`)
  - `## Project Constraints`
  - `## Non-Goals`
- If user chose start fresh, overwrite `OUTCOMES.md` only.

3. Create `tasks/PROJECT_STATE.md` only if missing.
- Use template from `project-lead.md`.
- Initialize with:
  - Current Sprint Name: `No active sprint`
  - Status: `Not Started`
  - Started: current ISO 8601 timestamp
  - PRD: `None`
  - Tasks: `None`
  - Active Blockers: `None`
  - Questions for Iain: `None`

4. Create `tasks/DECISIONS.md` only if missing.
- Use template header format from `project-lead.md`.
- Create header-only file (no decision entries).

### Error Handling
- If any file write fails, report exactly which file failed.
- Do not partially claim success.
- If `OUTCOMES.md` is updated and other files are preserved, explicitly state preservation occurred.

## 5) CLAUDE.md Personality Section Injection
After state files are handled, offer to manage `CLAUDE.md`:

1. Check for `CLAUDE.md` in current working directory.
2. If file exists, read it and inspect for `## Project Lead`.
- If section already exists, ask:
  `CLAUDE.md already has a Project Lead section. Skip? Update?`
- If no section and file has content, ask:
  `Want me to add the Project Lead section to the top of your CLAUDE.md? Your existing content will be preserved below it.`
- If top-level conflicting personality text is present (for example top-level `You are a...`), flag conflict and ask for direction before editing.
3. If `CLAUDE.md` does not exist, ask:
   `No CLAUDE.md found. Want me to create one with the Project Lead personality section?`

When adding/updating, use exactly this section and prepend it above existing content:

```markdown
## Project Lead
You are the Project Lead for this project. Read ~/.claude/agents/project-lead.md for your full personality and decision framework. Read tasks/OUTCOMES.md, tasks/PROJECT_STATE.md, and tasks/DECISIONS.md for current project state. Run /lead to begin orchestration.
```

## 6) Completion Summary (Always End With This)
After file operations and optional `CLAUDE.md` update, respond with:

`Project Lead setup complete.

Files created:
- tasks/OUTCOMES.md -- [N] outcomes defined
- tasks/PROJECT_STATE.md -- initial state
- tasks/DECISIONS.md -- empty log
- CLAUDE.md -- [updated/created/unchanged]

Next steps:
1. Run /orchestrate to launch autonomous orchestration (hands-off PM-PL cycles)
2. Run /lead for interactive orchestration within this session
3. Or open a new session -- the CLAUDE.md personality section will activate automatically

The Project Lead will read your outcomes and begin driving towards them.`

After displaying the summary, ask:

```
question: "Would you like to launch the autonomous orchestrator now?"
header: "Orchestrate"
options:
  - label: "Yes, run /orchestrate"
    description: "Launch the autonomous orchestrator to start delivering your outcomes."
  - label: "No, I'll do it later"
    description: "You can run /orchestrate or /lead whenever you're ready."
```

If user chooses yes: invoke the /orchestrate command via the Skill tool.
If user chooses no: end the command.

## Operational Notes
- This is a command file, not an agent definition.
- Preserve `PROJECT_STATE.md` and `DECISIONS.md` history whenever they already exist.
- Treat `tasks/OUTCOMES.md` as the only overwrite target when user selects start fresh.
