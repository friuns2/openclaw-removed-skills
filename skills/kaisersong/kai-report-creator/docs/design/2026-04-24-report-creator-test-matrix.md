# kai-report-creator Test Matrix

Date: 2026-04-24  
Scope: Test strategy for IR format, rendering engine, component system, and theme system

---

## 1. Test Layers

### Layer A: Focused Unit Tests

Primary files:

- `tests/test_ir_parsing.py` — IR format validation
- `tests/test_component_parsing.py` — Component block parsing
- `tests/test_language_detection.py` — Language auto-detection
- `tests/test_theme_routing.py` — Theme routing logic

Use this layer when the change is about:

- a single component type's parsing
- IR frontmatter field validation
- language detection threshold
- theme routing keyword matching

### Layer B: Integration Tests

Primary files:

- `tests/test_full_generation.py` — End-to-end generation
- `tests/test_rendering.py` — HTML rendering output
- `tests/test_export.py` — Image export pipeline

Use this layer when the change is about:

- multi-phase generation pipeline
- component rendering in context
- theme application to output

### Layer C: Visual Verification

Manual testing in browser:

- Open generated HTML in browser
- Test all 7 themes render correctly
- Test all 8 component types
- Test on mobile viewport

---

## 2. Invariants By Area

### 2.1 IR Format

Must always hold:

- YAML frontmatter is valid
- Component blocks are parseable
- Markdown prose renders as rich text

### 2.2 Components

Must always hold:

- KPI blocks render as cards
- Charts use ECharts (not Chart.js)
- Timelines are genuinely chronological
- Diagrams match their type schema

### 2.3 Theme System

Must always hold:

- Theme CSS variables are defined
- Theme overrides apply on top of base
- Content-type routing follows priority order

### 2.4 Language

Must always hold:

- CJK detection > 10% → zh
- Placeholder text matches language
- TOC label matches language

---

## 3. Bug Class To Test Mapping

| Bug / Change Type | Unit | Integration | Visual |
|---|---|---|---|
| IR format change | Required | Required | Optional |
| Component type change | Required | Required | Required |
| Theme change | Optional | Optional | Required |
| Language detection change | Required | Optional | Optional |
| Rendering engine change | Optional | Required | Required |
| Export pipeline change | Optional | Required | Required |

---

## 4. Scenario Matrix

### 4.1 Golden Scenarios

1. Generate narrative report (no fake data)
2. Generate mixed report (text + real data)
3. Generate data report (KPIs + charts)
4. All 7 themes render correctly
5. All 8 component types render correctly
6. Language auto-detection works
7. Theme routing follows priority order
8. Mobile viewport renders correctly

### 4.2 High-Risk Scenarios

1. Fabricating data in narrative reports
2. Chart.js instead of ECharts
3. Non-chronological timelines
4. Missing CSS variables in custom theme
5. Theme override not applying
6. Placeholder text in wrong language
7. KPI block with sentence in value field

---

## 5. Assertion Patterns

### 5.1 Good Assertions

```python
# ECharts used, not Chart.js
assert 'echarts' in html_content.lower()
assert 'chart.js' not in html_content.lower()

# No fabricated data
assert '[INSERT VALUE]' in html_content or '[数据待填写]' in html_content

# Language detection
assert 'lang="zh"' in html_content or 'lang="en"' in html_content

# Theme CSS variables
assert '--primary-color' in html_content
```

### 5.2 Weak Assertions to Avoid

```python
# Too vague
assert 'html' in output

# Only checks structure
assert len(components) > 0
```

---

## 6. Anti-Patterns

Do not do these:

1. "The HTML renders, so generation is fine."
2. "The chart looks close enough, no need to check ECharts."
3. "The theme colors are similar, no need to verify variables."
4. "We can skip the language detection test for a small change."

---

## 7. Practical Rule

For report-creator bugs:

> A scenario is not covered until generated HTML renders correctly in browser AND all component types display correctly.