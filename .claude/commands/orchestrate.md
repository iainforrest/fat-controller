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

### 2. Check Project OUTCOMES.md and Detect Slug

Scan for non-empty outcomes files at `tasks/*/OUTCOMES.md`, excluding `tasks/archive/`.

Use Bash:

```bash
mapfile -t OUTCOMES_FILES < <(find tasks -mindepth 2 -maxdepth 2 -type f -name OUTCOMES.md ! -path "tasks/archive/*" -size +0c | sort)
```

Then branch:

- If count is `0`, show:
```
No outcomes defined yet. Run /outcomes first.
```
Stop here.

- If count is `1`, auto-detect the project slug:
```bash
PROJECT_SLUG="$(basename "$(dirname "${OUTCOMES_FILES[0]}")")"
```
Continue.

- If count is `>1`, ask user which project to orchestrate using AskUserQuestion:
```
question: "Multiple project outcomes were found. Which project should /orchestrate run?"
header: "Project"
options:
  - label: "{slug-1}"
    description: "Use tasks/{slug-1}/OUTCOMES.md"
  - label: "{slug-2}"
    description: "Use tasks/{slug-2}/OUTCOMES.md"
  - ... one option per detected slug
```

Set `PROJECT_SLUG` from the selected option and continue.

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

### 4. Determine Session Name

The tmux session name is project-specific so multiple orchestrators can run in parallel for different projects. Derive it from the project directory:

```bash
SESSION_NAME="orch-$(basename "$PWD")"
```

Store this for use in all subsequent tmux commands.

### 5. Check for Existing Orchestrator Session

Run via Bash: `tmux has-session -t {SESSION_NAME} 2>/dev/null`

If a session exists, use AskUserQuestion:
```
question: "An orchestrator session '{SESSION_NAME}' is already running for this project. What would you like to do?"
header: "Session"
options:
  - label: "Attach to it"
    description: "Connect to the running orchestrator session to monitor progress."
  - label: "Kill and restart"
    description: "Stop the current orchestrator and launch a fresh one."
  - label: "Cancel"
    description: "Leave the existing session running and exit."
```

- Attach: tell user to run `tmux attach -t {SESSION_NAME}` in their terminal
- Kill and restart: run `tmux kill-session -t {SESSION_NAME}` then continue to launch
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
tmux new-session -d -s {SESSION_NAME} "python3 {ORCH} {project_dir} --project {PROJECT_SLUG} --skip-values-check 2>&1 | tee tasks/{PROJECT_SLUG}/orchestrator.log; echo ''; echo '--- Orchestrator exited. Session will close in 30 seconds. ---'; sleep 30"
```

The `--skip-values-check` flag is used because we already handled the VALUES.md check above with better UX.

The session auto-closes 30 seconds after the orchestrator exits. All output is preserved in `tasks/{PROJECT_SLUG}/orchestrator.log`. If someone is attached and watching, they have 30 seconds to read the final output before the session closes.

### Verify launch

After running the tmux command, verify it started:

```bash
tmux has-session -t {SESSION_NAME} 2>/dev/null && echo "running" || echo "failed"
```

If it failed, check `tasks/{PROJECT_SLUG}/orchestrator.log` for errors and report them.

### Confirmation

After verifying the session is running, respond with (substituting the actual session name):

```
Orchestrator started successfully as '{SESSION_NAME}'.

It's running in the background as a tmux session -- it will keep running even if you close this Claude Code session. The session auto-closes 30 seconds after the orchestrator finishes.

To view it from any terminal:
  tmux attach -t {SESSION_NAME}

Other useful commands:
  tail -f tasks/{PROJECT_SLUG}/orchestrator.log     # Follow the log without attaching
  tmux send-keys -t {SESSION_NAME} C-c              # Graceful shutdown (saves state)
  tmux kill-session -t {SESSION_NAME}                # Force kill

To resume after stopping:
  Run /orchestrate again -- it reads ROADMAP.md and picks up where it left off.
```

**IMPORTANT:** After displaying this message, remain in the Claude Code session. The user may want to continue working on other things while the orchestrator runs. Do NOT end the conversation or suggest closing the session.

---

## Error Handling

- If `tmux` is not installed: suggest `sudo apt install tmux` or fall back to running directly via Bash with `run_in_background: true`
- If `python3` is not available: tell user Python 3 is required
- If orchestrator.py is not found at any location: tell user to check their fat-controller installation
- If tmux session fails to start: read `tasks/{PROJECT_SLUG}/orchestrator.log` and report the error
