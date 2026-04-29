# LEARNINGS.md — Corrections / Best Practices / Insights

> Managed by self-improvement-loop skill. When editing manually, keep the `## [ID] category` header format intact.

---

## Template Format (Do Not Delete)

```markdown
## [LRN-YYYYMMDD-NNN] correction|best_practice|insight|knowledge_gap
**Logged**: ISO-8601
**Status**: pending | active | in_progress | resolved | promoted | dormant
**Pattern-Key**: <source>.<type>.<identifier>

### What Happened
[Specific scenario in 1-2 sentences — describe what happened and in what context]

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

## [LRN-20260401-001] correction
**Logged**: 2026-04-01T00:00:00+08:00
**Status**: pending
**Pattern-Key**: workflow.redundancy.multi_path_different_oversight

### What Happened
Two paths were designed for the same function: one where the AI directly promotes insights in memory-daily-distill, and another that follows the A/B/C/D user-confirmation path.

### Root Cause
There was no design-level check for "only one path per outcome with consistent user oversight." This led to a path with weaker supervision bypassing the main path's authority.

### How To Avoid Next Time
Before adding a new workflow path, ask: "Does this path do the same thing as an existing one? Do the oversight levels match?" If yes — merge the paths.

**Tags**: 
**Recurrence-Count**: 

*---*
