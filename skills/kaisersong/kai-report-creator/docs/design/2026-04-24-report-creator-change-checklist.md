# kai-report-creator Change Checklist

Date: 2026-04-24  
Scope: Required review checklist for rendering-affecting changes

Use this checklist before merging any change that affects IR format,
rendering engine, component system, or theme system.

---

## 1. Scope Check

Before touching code, answer these:

1. Which module am I changing?
   - IR format parsing
   - Rendering engine
   - Component system
   - Theme system
   - Language detection
   - Export pipeline

2. Is this a visual-only change or a rendering pipeline change?

3. Which component types are affected?
   - KPI, chart, table, list, image, timeline, diagram, callout

If it is a rendering pipeline change, plan the regression tests before the
code change.

---

## 2. IR Format Check

If the change affects IR format:

- [ ] YAML frontmatter is valid
- [ ] Component block syntax is parseable
- [ ] Markdown prose renders as rich text
- [ ] Machine-readable structure is valid

---

## 3. Component Check

If the change affects components:

### 3.1 KPI

- [ ] `items:` YAML format works
- [ ] Compatibility short-line format works
- [ ] No fabricated data in narrative reports
- [ ] Auto-downgrade to callout when invalid

### 3.2 Chart

- [ ] All 7 chart types work (bar, line, pie, scatter, radar, funnel, sankey)
- [ ] ECharts used (not Chart.js)
- [ ] Theme colors applied
- [ ] Auto-downgrade to table when invalid

### 3.3 Timeline

- [ ] Date tokens validated
- [ ] Chronological order enforced
- [ ] Auto-downgrade to list when invalid

### 3.4 Diagram

- [ ] All 4 diagram types work (sequence, flowchart, tree, mindmap)
- [ ] Required keys present for each type
- [ ] Auto-downgrade to callout when invalid

### 3.5 Other Components

- [ ] Table renders with theme styling
- [ ] List renders correctly
- [ ] Image renders with caption
- [ ] Callout renders with icon

---

## 4. Theme Check

If the change affects themes:

- [ ] All 7 built-in themes render correctly
- [ ] Theme CSS variables defined
- [ ] Theme overrides apply on top of base
- [ ] Content-type routing follows priority order
- [ ] Custom themes load correctly

---

## 5. Language Check

If the change affects language:

- [ ] CJK detection > 10% → zh
- [ ] Placeholder text matches language
- [ ] TOC label matches language
- [ ] HTML `lang` attribute set

---

## 6. Design Constraint Check

Before merging, confirm no design constraint violations:

- [ ] Zero dependencies in generated HTML
- [ ] Never fabricate data
- [ ] Machine-readable structure valid
- [ ] Mobile responsive

---

## 7. Test Checklist

Before merging, mark all that apply:

- [ ] Unit tests updated (if IR/component/theme changed)
- [ ] Integration tests updated (if cross-phase boundary changed)
- [ ] Visual verification in browser done (all affected components/themes)
- [ ] All tests pass (`python -m pytest tests/`)

---

## 8. Review Questions

Before you call the change done, answer these in plain language:

1. What exact user complaint does this fix or improve?
2. Which rendering phase was wrong before?
3. Which new regression would fail if this breaks again?
4. Does the generated HTML render correctly in browser on both desktop and mobile?

If question 4 is not clearly answered, the fix is not complete.