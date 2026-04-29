# FEATURE_REQUESTS.md — Feature Requests

> Managed by self-improvement-loop skill.When editing manually, keep the `## [ID] category` header format intact.

---

## Template Format (Do Not Delete)

```markdown
## [FEAT-YYYYMMDD-NNN] feature
**Logged**: ISO-8601
**Status**: pending | resolved
**Pattern-Key**: <source>.feature.<identifier>

### What Happened
[What capability is missing and what problem it causes]

### Root Cause
[Why this capability is missing — design gap or oversight]

### How To Avoid Next Time
[How to ensure this capability is correctly designed and validated]

**Tags**: 
**Recurrence-Count**: 

*---*
```

---

## Examples (delete after reading)

## [FEAT-20260401-001] feature
**Logged**: 2026-04-01T00:00:00+08:00
**Status**: pending
**Pattern-Key**: workflow.auto_commit.conditional

### What Happened
The auto-commit script commits all changes every time, with no way to selectively ignore .log or other temporary files, creating noisy commit history.

### Root Cause
The script was designed without an ignore/exclude mechanism and no extension points were预留.

### How To Avoid Next Time
Automation scripts must include ignore/exclude extension points and clearly document which file types should not enter the commit.

**Tags**: 
**Recurrence-Count**: 

*---*
