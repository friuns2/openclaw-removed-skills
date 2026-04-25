# kai-report-creator Component System Design

Date: 2026-04-24  
Project: `kai-report-creator`  
Status: Active reference design  
Scope: Component block types, rendering contracts, data binding, auto-downgrade targets

---

## 1. Why This Document Exists

report-creator has **8 component block types** that transform YAML/Markdown
input into rendered HTML:

- KPI cards
- Charts (ECharts)
- Tables
- Lists
- Images
- Timelines
- Diagrams
- Callouts

That means component bugs are **not rendering issues**. They are failures
at the boundary between:

- component block syntax and data structure
- YAML parsing and rendering contract
- auto-downgrade target selection
- component placement based on report class (narrative/mixed/data)

This document is the reference architecture for those boundaries.

---

## 2. KPI Component (`:::kpi`)

### 2.1 Canonical Input

```md
:::kpi
items:
  - label: 总营收
    value: ¥2,450万
    delta: ↑12%
    note: 同比
:::
```

### 2.2 Compatibility Input

```md
:::kpi
- 总营收: ¥2,450万 ↑12%
:::
```

### 2.3 Rendering Contract

- Each item renders as a KPI card
- `label` → card label (smaller text)
- `value` → card value (larger, bold text)
- `delta` → trend indicator (↑ green, ↓ red, → neutral)
- `note` → supplementary text (smaller, muted color)

### 2.4 Input Rules

- Allowed: short numeric values or short phrases in `value`
- Allowed: `delta` may be `↑12%`, `↓2%`, `→`, or short contextual text
- Prohibited: descriptive sentences in `value`
- Prohibited: placeholder-only KPI blocks in `narrative` reports
- Prohibited: placeholder-only KPI blocks in `mixed` reports with no real numbers

### 2.5 Validity

| Term | Condition |
|------|-----------|
| `invalid_syntax` | Body is neither canonical `items:` YAML nor compatibility short-line format |
| `invalid_semantics` | `value` contains sentence/paragraph, or KPI block fabricates visual anchor with placeholders |
| `auto_downgrade_target` | `callout` |

---

## 3. Chart Component (`:::chart`)

### 3.1 Allowed Types

`bar`, `line`, `pie`, `scatter`, `radar`, `funnel`, `sankey`

### 3.2 Canonical Body Schemas

**Standard charts** (`bar|line|pie|radar`):
```md
:::chart type=bar
labels: [Jan, Feb, Mar]
datasets:
  - name: 营收
    values: [100, 120, 140]
  - name: 利润
    values: [30, 40, 50]
:::
```

**Scatter**:
```md
:::chart type=scatter
datasets:
  - name: 产品A
    points: [[1, 2], [3, 4], [5, 6]]
:::
```

**Funnel**:
```md
:::chart type=funnel
stages:
  - label: 浏览
    value: 10000
  - label: 加购
    value: 3000
  - label: 下单
    value: 800
:::
```

**Sankey**:
```md
:::chart type=sankey
nodes: [A, B, C, D]
links:
  - source: A, target: B, value: 10
  - source: B, target: C, value: 8
:::
```

### 3.3 Rendering Contract

- All charts use **ECharts**
- Chart.js is NOT part of the active contract
- Charts render with theme colors
- Responsive sizing

### 3.4 Input Rules

- Prohibited: free-form YAML with undeclared keys
- Prohibited: placeholder-only charts in `narrative` reports
- Prohibited: placeholder-only charts in `mixed` reports with no real numbers

### 3.5 Validity

| Term | Condition |
|------|-----------|
| `invalid_syntax` | Body does not match the schema required by its `type` |
| `invalid_semantics` | Chart shape is parseable but mismatched to content, or only decorative placeholder data |
| `contract_conflict` | Prior Chart.js/ECharts split — resolved now: ECharts-only |
| `auto_downgrade_target` | `table` (preferred) or `callout` when source has no chartable data |

---

## 4. Table Component (`:::table`)

### 4.1 Canonical Input

```md
:::table
| 产品 | Q1 | Q2 | Q3 |
|------|----|----|----|
| A | 100 | 120 | 140 |
| B | 80 | 90 | 95 |
:::
```

### 4.2 Rendering Contract

- Renders as HTML `<table>` with theme styling
- Header row distinguished from data rows
- Responsive: horizontal scroll on mobile

### 4.3 Validity

- No auto-downgrade target (falls through to Markdown rendering)

---

## 5. Timeline Component (`:::timeline`)

### 5.1 Canonical Input

```md
:::timeline
- 2024-Q1: 产品发布
- 2024-Q2: 用户增长 50%
- 2024-Q3: 营收突破 1000万
- 2024-Q4: 团队扩张至 50人
:::
```

### 5.2 Allowed Date Tokens

- `YYYY-MM-DD`
- `YYYY-MM`
- `YYYY`
- `Q[1-4] YYYY`
- `Day N`
- `Week N`
- `Month N`

### 5.3 Input Rules

- Prohibited: principles, categories, capability buckets, or any parallel items that are not genuinely chronological

### 5.4 Validity

| Term | Condition |
|------|-----------|
| `invalid_syntax` | Not in `- Date: Description` form |
| `invalid_semantics` | Syntactically valid but `Date` is not actually a time marker |
| `auto_downgrade_target` | `list` |

---

## 6. Diagram Component (`:::diagram`)

### 6.1 Allowed Types

`sequence`, `flowchart`, `tree`, `mindmap`

### 6.2 Canonical Body Schemas

**Sequence**:
```md
:::diagram type=sequence
actors: [用户, API, 数据库]
steps:
  - from: 用户, to: API, msg: 请求
  - from: API, to: 数据库, msg: 查询
  - from: 数据库, to: API, msg: 返回
:::
```

**Flowchart**:
```md
:::diagram type=flowchart
nodes: [开始, 判断, 处理, 结束]
edges:
  - from: 开始, to: 判断
  - from: 判断, to: 处理, label: 是
  - from: 判断, to: 结束, label: 否
:::
```

**Tree**:
```md
:::diagram type=tree
root: 公司
children:
  - name: 技术部
    children:
      - name: 前端组
      - name: 后端组
  - name: 产品部
:::
```

**Mindmap**:
```md
:::diagram type=mindmap
center: 核心主题
branches:
  - name: 分支1
    sub: [子项1, 子项2]
  - name: 分支2
    sub: [子项3, 子项4]
:::
```

### 6.3 Rendering Contract

- Renders as SVG diagram
- Nodes and edges styled with theme colors
- Responsive sizing

### 6.4 Validity

| Term | Condition |
|------|-----------|
| `invalid_syntax` | Body missing required keys for chosen `type` |
| `invalid_semantics` | Structure parseable but diagram type misrepresents content |
| `auto_downgrade_target` | `callout` |

---

## 7. Callout Component (`:::callout`)

### 7.1 Canonical Input

```md
:::callout
这是重要的提示内容。可以包含 **Markdown** 格式。
:::
```

### 7.2 Icon Override

- `icon` parameter allowed only from whitelist
- Default icon if not specified

### 7.3 Rendering Contract

- Renders as highlighted box
- Icon on left, content on right
- Theme-colored border and background

---

## 8. Image Component (`:::image`)

### 8.1 Canonical Input

```md
:::image src=photo.jpg alt=产品截图
这是一张产品截图，展示了主要功能。
:::
```

### 8.2 Rendering Contract

- Renders as `<img>` with caption
- Responsive sizing
- Alt text for accessibility

---

## 9. Component Routing by Report Class

### 9.1 Narrative Reports (< 5% numeric density)

- Primary: text, callout, timeline
- Avoid: KPI blocks, chart blocks (unless real data exists)
- Visual anchors: callout boxes, timeline entries

### 9.2 Mixed Reports (5–20% numeric density)

- Primary: text, KPI (with real data), chart (with real data), table
- Conditional: timeline (if chronological data exists)
- Visual anchors: mix of text and data components

### 9.3 Data Reports (> 20% numeric density)

- Primary: KPI, chart, table
- Secondary: callout for insights
- Visual anchors: data components

---

## 10. Anti-Patterns

Do not do these:

1. **Using Chart.js**
   - ECharts only for all charts
   - Chart.js is not part of the active contract

2. **Fabricating KPI data**
   - Use `[INSERT VALUE]` for missing data
   - No placeholder-only KPI blocks in narrative reports

3. **Non-chronological timelines**
   - Timeline must be genuinely chronological
   - Use list for parallel items

4. **Ad-hoc diagram YAML**
   - Must follow declared per-type schema
   - No invented keys

5. **Placeholder-only charts**
   - Charts require real data
   - Auto-downgrade to table or callout

---

## 11. Operational Rule

For component bugs:

> A fix is not complete until the component renders correctly AND the auto-downgrade target works when the original block is invalid.