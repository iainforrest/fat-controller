# Technical Debt

*Code review findings and known issues not immediately fixed*

**Authority**: This is the single source of truth for known unfixed issues. All MEDIUM and LOW code review findings that don't get fixed immediately are tracked here.

---

## Purpose

This file captures:
- **MEDIUM and LOW findings** from code review that aren't fixed immediately
- **Known issues** that are accepted but should be addressed later
- **Refactoring opportunities** identified but deferred
- **Documentation gaps** that need filling

**Why this matters**: Tech debt is inevitable. Tracking it prevents:
- Rediscovering the same issues repeatedly
- Losing context on why issues were deferred
- Accumulating invisible debt that slows development

---

## Severity Levels

| Level | Definition | Typical Response |
|-------|------------|------------------|
| **CRITICAL** | Security issue, data loss risk | Fix immediately (NOT tracked here) |
| **HIGH** | Functional bug, major degradation | Fix in current sprint (NOT tracked here) |
| **MEDIUM** | Minor bug, code smell, pattern violation | Fix when touching related code |
| **LOW** | Cosmetic issue, optimization opportunity | Fix when convenient |

**Note**: CRITICAL and HIGH findings should be fixed immediately, not added to this file.

---

## Known Issues

### MEDIUM Severity

#### [TD-004] pull-fc: CTO agent sync missing

**Severity**: MEDIUM

**Location**: `.claude/commands/pull-fc.md`

**Description**: pull-fc command syncs `.claude/commands/` and `.claude/agents/` but does not explicitly list `.claude/agents/cto.md` in its documentation or validation. Since cto.md is now a mandatory dependency for prd/bugs/feature/execute commands, it should be included in the sync list.

**Why Deferred**: Current sync behavior already covers `.claude/agents/` glob, so cto.md is synced. This is a documentation gap, not a functional gap.

**Impact**: User confusion if they manually check what pull-fc syncs.

**Suggested Fix**: Add `.claude/agents/cto.md` to the explicit file list in pull-fc documentation, or add a validation step confirming cto.md exists after sync.

**Added**: 2026-02-10

**Source**: CR-CTO-integration (Code review finding from commits 7581f6f-977d85c)

---

### LOW Severity

#### [TD-001] prd.md: Checkbox format for automated validation

**Severity**: LOW

**Location**: `.claude/commands/prd.md` (Phase 5 validation section)

**Description**: Validation step uses markdown checkboxes for automated validation steps instead of describing as code logic. Other automated phases describe validation as numbered steps with failure behaviors.

**Why Deferred**: Cosmetic issue. Current checkbox format is actually more scannable and readable.

**Impact**: Minor documentation style inconsistency.

**Suggested Fix**: Convert checkboxes to numbered automated check descriptions with explicit failure handling.

**Added**: 2026-02-04

**Source**: CR-2026-02-04 (Both)

---

#### [TD-002] prd.md: Pseudo-code uses wrong block type

**Severity**: LOW

**Location**: `.claude/commands/prd.md` (Phase 5 reconciliation steps)

**Description**: Uses ```bash code blocks for pseudo-code that isn't valid bash syntax (e.g., "ORIGINAL_CONTEXT = read /tasks/...").

**Why Deferred**: Purely cosmetic. Anyone reading understands this is pseudocode. The syntax highlighting improves readability.

**Impact**: Minimal - no functional impact.

**Suggested Fix**: Change to ```yaml or unlabeled code blocks for pseudo-code.

**Added**: 2026-02-04

**Source**: CR-2026-02-04 (Codex only)

---

#### [TD-003] prd.md: Post-Agent Response option change unexplained

**Severity**: LOW

**Location**: `.claude/commands/prd.md` (Post-Agent Response section)

**Description**: Option 4 in Post-Agent Response may have changed from previous versions without documenting the reason. Phase 6 covers ADR capture separately.

**Why Deferred**: Historical context issue. Current options are functional.

**Impact**: Minimal - users may wonder about option changes if familiar with older version.

**Suggested Fix**: Add comment explaining option rationale or restore as option 5 if needed.

**Added**: 2026-02-04

**Source**: CR-2026-02-04 (Claude only)

---

#### [TD-005] execute.md: Ambiguous 1-2 non-CRITICAL fix failure handling

**Severity**: LOW

**Location**: `.claude/commands/execute.md` (post-execution code review triage section)

**Description**: When 1-2 non-CRITICAL fix agents fail, the error handling description says "continue triage" but doesn't specify whether to skip those failed fixes or retry them. This could lead to inconsistent behavior.

**Why Deferred**: In practice, the CTO would make a judgment call based on the specific failure. The ambiguity reflects real-world complexity rather than a specification error.

**Impact**: Minimal - orchestrator will make reasonable decisions, but explicit guidance would improve consistency.

**Suggested Fix**: Add explicit guidance: "For 1-2 non-CRITICAL failures, log the failure, continue triage, and add the failed fix to TECH_DEBT.md with the failure reason."

**Added**: 2026-02-10

**Source**: CR-CTO-integration (Code review finding CR-007 from commits 7581f6f-977d85c)

---

#### [TD-006] execute.md: Escalation criteria duplication

**Severity**: LOW

**Location**: `.claude/commands/prd.md`, `.claude/commands/bugs.md`, `.claude/commands/feature.md`, `.claude/commands/execute.md`

**Description**: CTO escalation criteria (recurring costs >$20/month, external lock-in, people impact, value conflicts, scope changes, <70% confidence with significant downside) are duplicated across four command files. If criteria change, all four files need manual updates.

**Why Deferred**: Duplication ensures each command is self-contained and understandable without cross-references. The escalation criteria are stable and unlikely to change frequently.

**Impact**: Maintenance burden if escalation criteria evolve.

**Suggested Fix**: Extract escalation criteria to `.claude/agents/cto.md` and reference from commands, or accept duplication as the trade-off for self-contained documentation.

**Added**: 2026-02-10

**Source**: CR-CTO-integration (Code review finding CR-005 from commits 7581f6f-977d85c)

---

## Refactoring Opportunities

### [RO-001] [Refactoring Name]

**Opportunity**: [What could be refactored]

**Location**: `[files/modules affected]`

**Benefit**: [Why this refactoring would help]

**Effort**: [Estimated effort - Small/Medium/Large]

**Trigger**: [When to do this - e.g., "When adding new auth methods"]

**Added**: [YYYY-MM-DD]

**Source**: [Where this was identified]

---

## Documentation Gaps

### [DOC-001] [What's Undocumented]

**Gap**: [What documentation is missing]

**Location**: `[files/modules that need docs]`

**Impact**: [Why this matters]

**Suggested**: [What documentation should be added]

**Added**: [YYYY-MM-DD]

**Source**: [CR-YYYY-MM-DD]

---

## Tech Debt Summary

| ID | Type | Severity | Component | Added | Status |
|----|------|----------|-----------|-------|--------|
| TD-001 | Issue | LOW | prd.md | 2026-02-04 | Open |
| TD-002 | Issue | LOW | prd.md | 2026-02-04 | Open |
| TD-003 | Issue | LOW | prd.md | 2026-02-04 | Open |
| TD-004 | Issue | MEDIUM | pull-fc.md | 2026-02-10 | Open |
| TD-005 | Issue | LOW | execute.md | 2026-02-10 | Open |
| TD-006 | Issue | LOW | commands/ | 2026-02-10 | Open |

---

## Resolved Tech Debt

*Items resolved are moved here for historical tracking*

### [TD-XXX] [Resolved Item]

**Resolution Date**: [YYYY-MM-DD]

**Resolution**: [How it was fixed]

**Commit**: [commit SHA]

**Original Issue**: [Original description]

---

## Tech Debt Workflow

### When Code Review Finds Issues

1. **CRITICAL/HIGH**: Fix immediately, don't add to this file
2. **MEDIUM**:
   - Add to this file if not fixed in current work
   - Include context for future fix
3. **LOW**:
   - Add to this file
   - Tag with trigger conditions for when to fix

### When Fixing Tech Debt

1. **Update Status**: Mark as in-progress while working
2. **Complete**: Move to "Resolved Tech Debt" section when done
3. **Reference**: Include TD-XXX ID in commit message
4. **Clean Up**: Periodically archive old resolved items

### When to Address Tech Debt

**Triggers for fixing**:
- You're touching related code anyway
- Issue severity increases (MEDIUM → HIGH)
- Multiple LOW issues in same component (batch fix)
- Sprint planning allocates time for tech debt
- Issue blocks new feature development

---

## Template for New Tech Debt Item

```markdown
#### [TD-XXX] [Component/File]: [Brief Description]

**Severity**: [MEDIUM/LOW]

**Location**: [file path or stable glob]

**Description**: [Detailed explanation of what's wrong]

**Why Deferred**: [Clear reason for not fixing now]

**Impact**: [What this affects or could affect]

**Suggested Fix**: [Recommended approach]

**Added**: YYYY-MM-DD

**Source**: [CR-YYYY-MM-DD] [Claude only|Codex only|Both]

**Related**: [Links to related items/ADRs]
```

---

## Template for Refactoring Opportunity

```markdown
### [RO-XXX] [Refactoring Name]

**Opportunity**: [What could be improved]

**Location**: [files/modules]

**Benefit**: [Why this would help]

**Effort**: [Small/Medium/Large estimate]

**Trigger**: [When to do this]

**Added**: YYYY-MM-DD

**Source**: [Where identified]
```

---

## Notes

- Tech debt is not shame - it's pragmatic trade-offs documented
- Update this file immediately when code review identifies deferred issues
- Review this file during sprint planning to allocate cleanup time
- Batch similar LOW items for efficient fixing
- Archive resolved items older than 6 months to keep file manageable
- Link to `.ai/solutions/` when fixes reveal reusable patterns
