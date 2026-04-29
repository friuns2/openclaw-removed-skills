# ERRORS.md — Command / Integration Errors

> Managed by self-improvement-loop skill.When editing manually, keep the `## [ID] category` header format intact.

---

## Template (Do Not Delete)

```markdown
## [ERR-YYYYMMDD-NNN] error
**Logged**: ISO-8601
**Status**: pending | resolved
**Pattern-Key**: <source>.error.<identifier>

### What Happened
[Specific scenario — describe what happened and in what context]

### Root Cause
[Why it happened — structural reason, not surface symptom]

### How To Avoid Next Time
[One actionable principle that can transfer to similar situations]

**Tags**: 
**Recurrence-Count**: 

*---*
```

---

## Examples (delete after reading)

## [ERR-20260401-001] error
**Logged**: 2026-04-01T00:00:00+08:00
**Status**: resolved
**Pattern-Key**: tool.hook.keyword.missing

### What Happened
The hook misclassified "能不能帮我做某事" as an error keyword, triggering a false error notification.

### Root Cause
The ERROR_KEYWORDS list in handler.js contained "能不能", which is a feature request signal, not an error signal. Keyword matching is literal, not semantic.

### How To Avoid Next Time
Separate error signals from feature-request signals in keyword lists. Literal matching without semantic context causes false positives.

**Tags**: 
**Recurrence-Count**: 

*---*