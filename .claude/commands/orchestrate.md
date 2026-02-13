---
description: Launch the autonomous orchestrator for hands-off PM-PL cycle execution
---

# Autonomous Orchestrator Launcher

Launch the Python orchestrator that drives autonomous PM-PL cycles to deliver project outcomes. The orchestrator runs in a tmux session, spawning fresh Claude Code sessions as subprocesses -- it survives context window exhaustion and runs unattended.

---

## Pre-flight Checks

Run these checks in order. Stop at the first failure.

### 1. Check Git Repository

Run `git rev-parse --is-inside-work-tree` via Bash.

If not a git repo:
```
This directory is not a git repository. Initialize with `git init` first.
```
Stop here.

### 2. Check OUTCOMES.md

Check if `tasks/OUTCOMES.md` exists and is non-empty.

If missing or empty:
```
No outcomes defined yet. Run /outcomes first to define what this project should deliver, then come back to /orchestrate.
```
Stop here.

### 3. Check VALUES.md

Check if `~/.claude/VALUES.md` exists.

**If VALUES.md exists:**
- Note: "Values profile found. The orchestrator will use your values to guide agent decisions."
- Continue to launch step.

**If VALUES.md is missing:**

Use AskUserQuestion with this flow:

**First question:**
```
question: "No values profile found at ~/.claude/VALUES.md. Values-driven agents make decisions aligned with your principles. Would you like to set up your values profile first?"
header: "Values"
options:
  - label: "Run /values-discovery (Recommended)"
    description: "Interactive session to create your values profile. Takes ~10 minutes. Come back to /orchestrate after."
  - label: "Proceed without values"
    description: "Agents will operate generically without your personal principles guiding decisions."
```

If user chooses /values-discovery:
```
Run /values-discovery to create your values profile. When it's done, come back and run /orchestrate again.
```
Stop here.

If user chooses "Proceed without values", ask the **second question:**
```
question: "Operating without values means the PM and PL agents will make autonomous decisions without your personal principles. Are you sure you want to proceed?"
header: "Confirm"
options:
  - label: "Yes, proceed without values"
    description: "Agents operate in generic mode with conservative defaults."
  - label: "No, I'll set up values first"
    description: "Exit and run /values-discovery."
```

If user confirms proceed: continue to launch step.
If user chooses to set up values:
```
Run /values-discovery when ready, then come back to /orchestrate.
```
Stop here.

### 4. Check for Existing Orchestrator Session

Run via Bash: `tmux has-session -t orchestrator 2>/dev/null`

If a session exists, use AskUserQuestion:
```
question: "An orchestrator tmux session is already running. What would you like to do?"
header: "Session"
options:
  - label: "Attach to it"
    description: "Connect to the running orchestrator session to monitor progress."
  - label: "Kill and restart"
    description: "Stop the current orchestrator and launch a fresh one."
  - label: "Cancel"
    description: "Leave the existing session running and exit."
```

- Attach: tell user to run `tmux attach -t orchestrator` in their terminal
- Kill and restart: run `tmux kill-session -t orchestrator` then continue to launch
- Cancel: stop here

---

## Launch

All pre-flight checks passed. Launch the orchestrator.

### Build the command

The orchestrator script lives at the fat-controller install location. Detect it:

```bash
# Try common locations
if [ -f "./orchestrator.py" ]; then
  ORCH="./orchestrator.py"
elif [ -f "$(npm root -g)/create-fat-controller/orchestrator.py" ]; then
  ORCH="$(npm root -g)/create-fat-controller/orchestrator.py"
elif [ -f "$HOME/projects/fat-controller/orchestrator.py" ]; then
  ORCH="$HOME/projects/fat-controller/orchestrator.py"
fi
```

### Launch in tmux

```bash
tmux new-session -d -s orchestrator "python3 {ORCH} {project_dir} --skip-values-check 2>&1 | tee tasks/orchestrator.log; echo '--- Orchestrator exited. Press Enter to close. ---'; read"
```

The `--skip-values-check` flag is used because we already handled the VALUES.md check above with better UX.

### Confirmation

After successful launch, respond with:

```
Orchestrator launched in tmux session "orchestrator".

The PM-PL cycle is now running autonomously:
  PM plans sprints from your outcomes → PL executes them → PM reviews and plans next

Monitor:
  tmux attach -t orchestrator     # Watch live output
  tail -f tasks/orchestrator.log  # Follow the log file

Stop:
  tmux send-keys -t orchestrator C-c  # Graceful shutdown (saves state)
  tmux kill-session -t orchestrator    # Force kill

Resume after stop:
  Run /orchestrate again -- the orchestrator reads ROADMAP.md and picks up where it left off.
```

---

## Error Handling

- If `tmux` is not installed: suggest `sudo apt install tmux` or fall back to running directly via Bash with `run_in_background: true`
- If `python3` is not available: tell user Python 3 is required
- If orchestrator.py is not found at any location: tell user to check their fat-controller installation
