# Project Roadmap: {PROJECT_NAME}

**Created:** {ISO8601_TIMESTAMP}
**Last Updated:** {ISO8601_TIMESTAMP}
**Outcomes:** tasks/OUTCOMES.md

<!--
  ROADMAP.md -- Sprint state tracking for the autonomous orchestrator.

  This file is the single source of truth for sprint planning and progress.
  The PM agent creates and updates it; the orchestrator reads it on resume.

  =========================================================================
  FIELD REFERENCE
  =========================================================================

  Header Fields:
    - Project Name:   From OUTCOMES.md or user input
    - Created:        ISO 8601 timestamp (e.g., 2026-02-14T10:00:00Z)
    - Last Updated:   ISO 8601 timestamp, updated on every PM write
    - Outcomes:       Relative path to OUTCOMES.md

  Sprint Fields:
    - Target Outcome: Must match an outcome name in OUTCOMES.md exactly
    - Status:         One of: backlog, in_progress, done, blocked
    - Dependencies:   Comma-separated sprint names, or "none"
    - PRD:            Relative path to sprint PRD, or "null" if not yet created
    - Branch:         Git branch name (sprint/{sprint-name}), or "null"
    - Started:        ISO 8601 timestamp, or "null"
    - Completed:      ISO 8601 timestamp, or "null"
    - Summary:        Completion or blocker description, or "null"

  =========================================================================
  SPRINT NAME FORMAT
  =========================================================================

  - Kebab-case, lowercase alphanumeric and hyphens only
  - Length: 3-60 characters
  - Pattern: ^[a-z0-9][a-z0-9-]{1,58}[a-z0-9]$
  - Must be unique within this roadmap
  - Examples: "auth-service", "sprint-1-pm-agent", "fix-login-regression"

  =========================================================================
  BRANCH NAMING
  =========================================================================

  - Always prefixed with "sprint/"
  - Format: sprint/{sprint-name}
  - Pattern: ^sprint/[a-z0-9][a-z0-9-]+$
  - Examples: "sprint/auth-service", "sprint/sprint-1-pm-agent"

  =========================================================================
  STATUS VALUES AND TRANSITIONS
  =========================================================================

  Valid statuses:
    backlog       -- Sprint is planned but not yet started
    in_progress   -- PL is actively executing this sprint
    done          -- Sprint completed, branch merged to main
    blocked       -- Sprint hit a blocker, needs user or PM intervention

  Valid transitions:
    backlog     -> in_progress   (PL begins execution)
    in_progress -> done          (PL completes, PM merges branch)
    in_progress -> blocked       (PL or PM encounters a blocker)

  Invalid transitions (these must never happen):
    done -> in_progress          (completed work is final)
    blocked -> in_progress       (create a new sprint instead)
    backlog -> done              (cannot skip execution)
    backlog -> blocked           (must start before blocking)

  =========================================================================
  DEPENDENCY RULES
  =========================================================================

  - Dependencies reference other sprint names in this file
  - A sprint cannot start until ALL its dependencies have status "done"
  - No circular dependencies allowed (A depends on B depends on A)
  - Use "none" when a sprint has no dependencies
  - The PM agent validates dependencies before planning execution

  =========================================================================
  STRUCTURED OUTPUT PROTOCOL
  =========================================================================

  The PM and PL agents communicate with the orchestrator via structured
  YAML signal blocks. Signals are delimited by markers on their own lines:

    ---ORCHESTRATOR_SIGNAL---
    signal: <signal_type>
    <type-specific fields>
    ---ORCHESTRATOR_SIGNAL---

  The signal block MUST be the last output from the agent. The orchestrator
  parses stdout looking for these markers. Any text after the closing
  marker may be lost.

  PM Signal Types:
  ----------------
  next_task     -- Sprints are ready for PL execution
                   Required fields:
                     sprints: array of objects, each with:
                       name:          sprint name (kebab-case)
                       prd:           relative path to PRD file
                       branch:        git branch name (sprint/{name})
                       parallel_safe: boolean (can run concurrently?)
                     summary: string describing what was planned

  complete      -- All project outcomes are done
                   Required fields:
                     summary:             string describing final state
                     outcomes_completed:  array of outcome names

  blocked       -- Cannot proceed, needs user input
                   Required fields:
                     reason:          what is unknown or preventing progress
                     what_is_needed:  specific information required
                     recommendation:  PM's best suggestion for resolution

  error         -- Something went wrong during planning
                   Required fields:
                     error_type:          category of error
                     details:             full error description
                     recovery_suggestion: how to recover

  PL Signal Types:
  ----------------
  done          -- Sprint completed successfully
                   Required fields:
                     sprint_name:     name of the completed sprint
                     branch:          git branch with commits
                     commits:         array of commit SHAs
                     tasks_completed: integer count of completed tasks
                     tasks_total:     integer count of total tasks
                     summary:         description of what was delivered

  blocked       -- Sprint hit a blocker during execution
                   Required fields:
                     sprint_name:         name of the blocked sprint
                     branch:              git branch (may have partial work)
                     blocker_description: what is blocking progress
                     tasks_completed:     integer count completed so far
                     tasks_total:         integer count of total tasks

  error         -- Sprint execution failed
                   Required fields:
                     sprint_name:  name of the failed sprint
                     branch:       git branch (may have partial work)
                     error_type:   category of error
                     details:      full error description

  Signal Examples:

    PM next_task:
      ---ORCHESTRATOR_SIGNAL---
      signal: next_task
      sprints:
        - name: auth-service
          prd: tasks/auth-service/prd.md
          branch: sprint/auth-service
          parallel_safe: true
      summary: "Initial sprint for authentication service"
      ---ORCHESTRATOR_SIGNAL---

    PL done:
      ---ORCHESTRATOR_SIGNAL---
      signal: done
      sprint_name: auth-service
      branch: sprint/auth-service
      commits:
        - "a1b2c3d"
        - "e4f5g6h"
      tasks_completed: 5
      tasks_total: 5
      summary: "Auth service with JWT login, logout, token refresh"
      ---ORCHESTRATOR_SIGNAL---

    PM blocked:
      ---ORCHESTRATOR_SIGNAL---
      signal: blocked
      reason: "Cannot determine authentication strategy"
      what_is_needed: "Decision on API keys vs OAuth"
      recommendation: "API keys for simplicity given single-user system"
      ---ORCHESTRATOR_SIGNAL---
-->

---

## Sprint: {sprint-name}
**Target Outcome:** {outcome name from OUTCOMES.md}
**Status:** backlog
**Dependencies:** none
**PRD:** null
**Branch:** null
**Started:** null
**Completed:** null
**Summary:** null
