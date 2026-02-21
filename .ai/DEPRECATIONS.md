# Deprecations

*Deprecated APIs, patterns, and experimental features*

**Authority**: This is the single source of truth for deprecation tracking. If code/patterns are deprecated or experimental, they're documented here.

---

## Purpose

This file tracks:
- **Deprecated APIs**: Old interfaces scheduled for removal
- **Deprecated Patterns**: Outdated approaches replaced by better ones
- **Experimental Features**: Unstable features that may change or be removed

**Why this matters**: Clear deprecation tracking prevents confusion, guides migrations, and sets expectations.

---

## Deprecation Status Legend

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| 🟡 **Deprecated** | Still works, but scheduled for removal | Plan migration |
| 🔴 **Removed** | No longer available | Must migrate immediately |
| 🔵 **Experimental** | May change or be removed | Use with caution |

---

## Removed Patterns

### Three-Tier .claude/ Layout (projects-level intermediate layer)

**Status**: Removed

**Deprecated Date**: 2026-02-21

**Removal Date**: 2026-02-21

**Reason**: The intermediate `~/projects/.claude/` layer added complexity with no benefit. Symlinks across 10 projects were fragile and hard to audit. Consolidated to a two-tier system: fat-controller dev → `~/.claude/` production via git hook.

**Old Pattern**:
```
fat-controller .claude/  →  ~/projects/.claude/  →  ~/.claude/
(symlinks)                   (manual sync)
```

**New Pattern**:
```
fat-controller .claude/  →  ~/.claude/
(scripts/sync-to-root.sh via git post-commit/post-merge hook)
```

**Migration**:
- `~/projects/.claude/` directory removed
- Symlinks removed from 10 downstream projects
- `~/projects/.claude/skills/entities/` moved to `~/.claude/skills/entities/`
- `execution-agent.md` added directly to fat-controller `.claude/agents/`

**Reference**: Commit `8367785 feat: Add dev-to-production sync for .claude/ files`

---

## Deprecated APIs

### [API Name or Module]

**Status**: 🟡 Deprecated

**Deprecated Date**: [YYYY-MM-DD]

**Removal Date**: [YYYY-MM-DD] *(or "TBD" if not set)*

**Reason**: [Why this API is being deprecated]

**Migration Path**:
```
# Old approach (deprecated)
[deprecated code example]

# New approach (use this instead)
[replacement code example]
```

**Affected Components**:
- `[file/module 1]`
- `[file/module 2]`

**Breaking Changes**: [Any behavior differences in new approach]

---

### [Another Deprecated API]

**Status**: 🔴 Removed

**Deprecated Date**: [YYYY-MM-DD]

**Removal Date**: [YYYY-MM-DD]

**Reason**: [Why removed]

**Migration Path**: See [ADR reference or documentation]

---

## Deprecated Patterns

### [Pattern Name]

**Status**: 🟡 Deprecated

**Deprecated Date**: [YYYY-MM-DD]

**Reason**: [Why this pattern is no longer recommended]

**Old Pattern**:
```
[example of deprecated pattern]
```

**New Pattern**:
```
[example of replacement pattern]
```

**Reference**: See `PATTERNS.md` or `.ai/decisions/[ADR-number]` for new pattern

**Migration Checklist**:
- [ ] [Step 1]
- [ ] [Step 2]
- [ ] [Step 3]

---

## Experimental Features

### [Experimental Feature Name]

**Status**: 🔵 Experimental

**Added Date**: [YYYY-MM-DD]

**Stability**: [Alpha/Beta/Preview]

**Purpose**: [What this experimental feature does]

**Known Issues**:
- [Issue 1]
- [Issue 2]

**May Change**:
- [What might change about this feature]
- [What's not stable yet]

**Use Cases**: [When it's appropriate to use this despite experimental status]

**Feedback**: [How to report issues or feedback]

**Stabilization Plan**: [Expected timeline or criteria for moving to stable]

---

## Deprecation Schedule

| Item | Type | Deprecated | Removal | Status |
|------|------|------------|---------|--------|
| [Item 1] | API | [date] | [date] | 🟡 Deprecated |
| [Item 2] | Pattern | [date] | TBD | 🟡 Deprecated |
| [Item 3] | Feature | [date] | [date] | 🔴 Removed |

---

## Deprecation Workflow

### When Deprecating Code

1. **Announce**: Add entry to this file with deprecation date
2. **Set Timeline**: Determine removal date (minimum 3 months notice recommended)
3. **Document Migration**: Provide clear migration path with examples
4. **Mark in Code**: Add deprecation warnings/annotations in the code itself
5. **Notify Users**: Communicate through appropriate channels
6. **Track Usage**: Monitor which components still use deprecated code
7. **Remove**: After removal date, delete deprecated code and mark as 🔴 Removed

### When Marking Experimental

1. **Document**: Add entry to Experimental Features section
2. **Set Expectations**: Clearly state what may change
3. **Track Feedback**: Note known issues and gather user feedback
4. **Decide**: Either stabilize, iterate, or deprecate based on feedback

---

## Template for New Deprecation

```markdown
### [API/Pattern/Feature Name]

**Status**: 🟡 Deprecated

**Deprecated Date**: YYYY-MM-DD

**Removal Date**: YYYY-MM-DD *(or TBD)*

**Reason**: [Clear explanation of why this is being deprecated]

**Migration Path**:
[Old code example]
→ [New code example]

**Affected Components**:
- [component 1]
- [component 2]

**Breaking Changes**: [Any behavioral differences]

**Reference**: [Link to ADR or documentation if applicable]
```

---

## Template for Experimental Features

```markdown
### [Feature Name]

**Status**: 🔵 Experimental

**Added Date**: YYYY-MM-DD

**Stability**: [Alpha/Beta/Preview]

**Purpose**: [What it does]

**Known Issues**:
- [Issue 1]

**May Change**:
- [What's not stable]

**Use Cases**: [When to use despite experimental status]

**Stabilization Plan**: [Timeline or criteria]
```

---

## Notes

- **Deprecation is not deletion** - it's a migration period
- Provide generous timelines (3+ months minimum for APIs)
- Clear migration paths reduce upgrade friction
- Experimental features should graduate to stable or be deprecated
- Reference ADRs for context on why deprecation decisions were made
- Update `.ai/TECH_DEBT.md` if deprecated code isn't migrated immediately
