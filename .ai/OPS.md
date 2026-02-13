# Operations Guide

*Runbooks, debug commands, deploy procedures, and operational playbooks*

**Authority**: This is the single source of truth for operational procedures. If it's about running, debugging, deploying, or responding to incidents, it lives here.

---

## Quick Operations Index

| Operation | Section | When to Use |
|-----------|---------|-------------|
| Build/test commands | Build Commands | Starting development |
| Debug issues | Debug Commands | Investigating problems |
| Deploy changes | Deploy Procedures | Releasing to production |
| Monitor health | Monitoring | Checking system status |
| Handle incidents | Incident Response | Production issues |

---

## Build Commands

```bash
# Build
[BUILD_COMMAND]              # e.g., "npm run build", "./gradlew build", "cargo build"

# Test
[TEST_COMMAND]               # e.g., "npm test", "./gradlew test", "cargo test"

# Development/Watch mode
[DEV_COMMAND]                # e.g., "npm run dev", "./gradlew run", "cargo run"

# Lint/Format
[LINT_COMMAND]               # e.g., "npm run lint", "./gradlew lint"

# Install dependencies
[INSTALL_DEPS]               # e.g., "npm install", "./gradlew dependencies"

# Clean build
[CLEAN_BUILD]                # e.g., "npm run clean && npm run build"

# Autonomous Orchestrator
python3 orchestrator.py /path/to/project [--max-cycles 50] [--log-level INFO]
# Drives autonomous PM-PL cycles
# Logs to .claude-orchestrator/orchestrator.log
# Ctrl+C for graceful shutdown
```

---

## Debug Commands

```bash
# Debug mode
[DEBUG_COMMAND]              # e.g., "npm run debug", "cargo build --debug"

# Logs
[LOG_COMMAND]                # e.g., "tail -f logs/app.log"

# Test specific file
[TEST_FILE_COMMAND]          # e.g., "npm test -- path/to/test"
```

### Common Debug Scenarios

#### Issue: [Common Problem]
**Symptoms**: [Description]
**Debug Steps**:
1. [First check]
2. [Second check]
3. [Resolution]

**Commands**:
```bash
[Specific diagnostic commands]
```

---

## Deploy Procedures

### Production Deploy

**Prerequisites**:
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Staging validated

**Steps**:
```bash
# 1. Final checks
[PRE_DEPLOY_CHECKS]

# 2. Deploy
[DEPLOY_COMMAND]

# 3. Verify deployment
[POST_DEPLOY_VERIFY]
```

### Rollback Procedure

**When to rollback**: [Criteria for rollback decision]

**Steps**:
```bash
# 1. Identify last good version
[VERSION_CHECK]

# 2. Rollback
[ROLLBACK_COMMAND]

# 3. Verify rollback
[VERIFY_ROLLBACK]
```

---

## Monitoring

### Health Checks

```bash
# System health
[HEALTH_CHECK_COMMAND]

# Performance metrics
[METRICS_COMMAND]

# Error rates
[ERROR_CHECK_COMMAND]
```

### Key Metrics

| Metric | Command | Alert Threshold |
|--------|---------|-----------------|
| [Metric 1] | `[command]` | [threshold] |
| [Metric 2] | `[command]` | [threshold] |

---

## Incident Response

### Incident Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| **P0** | Complete outage | Immediate | Service down |
| **P1** | Critical degradation | < 15 minutes | 50% error rate |
| **P2** | Partial degradation | < 1 hour | Feature broken |
| **P3** | Minor issue | < 1 day | Cosmetic bug |

### Incident Response Playbook

#### 1. Detect and Triage
- [ ] Identify severity level
- [ ] Check monitoring dashboards
- [ ] Review recent deployments

#### 2. Investigate
```bash
# Check logs
[LOG_INVESTIGATION_COMMAND]

# Check system resources
[RESOURCE_CHECK]

# Check dependencies
[DEPENDENCY_CHECK]
```

#### 3. Mitigate
- [ ] If deployment related: consider rollback
- [ ] If infrastructure: check service status
- [ ] If data: verify database integrity

#### 4. Resolve
- [ ] Apply fix
- [ ] Verify resolution
- [ ] Monitor for recurrence

#### 5. Document
- [ ] Create incident report
- [ ] Add solution to `.ai/solutions/`
- [ ] Update this playbook if new pattern discovered

---

## Performance Monitoring

```bash
# Profile
[PROFILE_COMMAND]            # e.g., "npm run profile"

# Analyze bundle/build
[ANALYZE_COMMAND]            # e.g., "npm run analyze"
```

---

## Runbook Template

When you discover a new operational procedure, add it here using this format:

### [Procedure Name]

**Purpose**: [What this procedure accomplishes]

**When to Use**: [Triggering conditions]

**Prerequisites**:
- [ ] [Requirement 1]
- [ ] [Requirement 2]

**Steps**:
```bash
# 1. [Step description]
[command]

# 2. [Step description]
[command]
```

**Validation**: [How to verify success]

**Rollback**: [How to undo if needed]

---

---

## Orchestrator Operations

### Running the Orchestrator

**Start orchestrator:**
```bash
cd /path/to/project
python3 orchestrator.py . --max-cycles 50 --log-level INFO
```

**Prerequisites:**
- [ ] tasks/OUTCOMES.md exists with defined outcomes
- [ ] ~/.claude/VALUES.md exists (recommended, not required)
- [ ] Git working directory clean (no uncommitted changes)
- [ ] Git remote configured (for push operations)

**Orchestrator will:**
1. Check for VALUES.md (graduated warning if missing, user can proceed)
2. Read or create tasks/ROADMAP.md
3. Invoke PM agent to plan next sprint(s)
4. Create sprint/* git branches
5. Invoke PL agent(s) to execute sprint(s)
6. Merge completed sprints to main
7. Update ROADMAP.md with status
8. Loop until PM signals completed or blocked

**Logs:**
- Structured logs: `.claude-orchestrator/orchestrator.log`
- Stderr: Human-friendly progress messages

**Graceful Shutdown:**
- Press Ctrl+C once: graceful shutdown, preserves state in ROADMAP.md
- Press Ctrl+C twice: immediate exit (may leave state inconsistent)

### Resuming After Stop

The orchestrator is stateless. Resume by re-running:
```bash
python3 orchestrator.py /path/to/project
```

Orchestrator reads ROADMAP.md to determine where to resume:
- Sprints with status `backlog`: not started, eligible for execution
- Sprints with status `in_progress`: were interrupted, PM will assess
- Sprints with status `done`: completed, skip
- Sprints with status `blocked`: require user intervention

### Common Issues

#### Issue: PM signals "blocked" - OUTCOMES.md missing
**Symptoms**: Orchestrator halts immediately after PM invocation
**Resolution**:
1. Create tasks/OUTCOMES.md with project outcomes
2. Use template or run /outcomes command
3. Re-run orchestrator

#### Issue: PL execution fails - git merge conflict
**Symptoms**: Orchestrator logs "Merge conflict detected, aborting merge"
**Resolution**:
1. Check `.claude-orchestrator/orchestrator.log` for conflict details
2. Manually resolve conflict on sprint/* branch
3. Update ROADMAP.md: change sprint status from `in_progress` to `done` or `blocked`
4. Re-run orchestrator (PM will assess state)

#### Issue: Stuck detection - same sprint loops
**Symptoms**: "Stuck detection: sprint 'X' attempted 3 times, halting"
**Resolution**:
1. Check ROADMAP.md for sprint definition issues
2. Check sprint PRD for clarity/feasibility
3. Fix sprint definition or mark as blocked
4. Re-run orchestrator

#### Issue: VALUES.md missing warning
**Symptoms**: Orchestrator warns "VALUES.md not found" at startup
**Resolution (optional)**:
1. Run /values-discovery command to create VALUES.md
2. Or proceed in generic mode (agents use conservative judgments)
3. VALUES.md is recommended but NOT required

---

## Notes

- Update this file when you discover new operational patterns
- Add runbooks for any procedure you've done twice
- Keep commands platform-agnostic where possible (document platform differences)
- Link to `.ai/solutions/` when referencing past incidents
