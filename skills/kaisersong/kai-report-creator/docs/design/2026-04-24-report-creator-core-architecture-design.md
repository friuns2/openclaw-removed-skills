# kai-report-creator Core Architecture Design

Date: 2026-04-24  
Project: `kai-report-creator`  
Status: Active reference design  
Scope: IR format, rendering engine, command routing, language auto-detection, theme routing

---

## 1. Why This Document Exists

report-creator generates **zero-dependency, single-file HTML reports** with
mixed text, charts, KPIs, timelines, diagrams, and images.

That means generation bugs are **not formatting issues**. They are failures
at the boundary between:

- IR format syntax and semantic validity
- component block parsing and rendering
- language auto-detection and content tone
- theme routing and CSS variable application
- machine-readable structure and human-readable output

This document is the reference architecture for those boundaries.

---

## 2. What Counts As "Core" In report-creator

"Core" means the report processing pipeline that transforms input into
rendered HTML.

It includes:

- Command routing (`--plan`, `--generate`, `--review`, `--themes`, `--from`, `--bundle`, `--export-image`)
- IR format (`.report.md`) — YAML frontmatter + Markdown prose + component blocks
- HTML rendering engine — zero-dependency single-file output
- Language auto-detection (CJK character counting)
- Content-type → theme routing (8 priority levels)
- Numeric density classification (narrative/mixed/data)
- Machine-readable structure (3-layer: summary JSON → section annotations → component raw data)

It does **not** include:

- Component system details (see Component System Design)
- Theme CSS definitions (see Theme System Design)
- PPTX export (handled by other tools)

---

## 3. Design Goals

The core pipeline must satisfy these goals simultaneously:

1. **Zero dependency output**
   - Generated HTML works when opened directly in browser
   - No build tools, no npm runtime

2. **Never fabricate data**
   - Use `[INSERT VALUE]` placeholder for missing data
   - User provides data, AI provides structure

3. **Machine-readable output**
   - 3-layer structure for downstream AI agents
   - Summary JSON, section annotations, component raw data

4. **Mobile responsive**
   - Reports render correctly on desktop and mobile

5. **IR validity**
   - Clear taxonomy: invalid_syntax, invalid_semantics, contract_conflict, auto_downgrade_target

---

## 4. Command Routing

### 4.1 Command Reference

| Flag | Action |
|------|--------|
| `--plan "topic"` | Generate `.report.md` IR file only. Save as `report-<slug>.report.md`. |
| `--generate [file]` | Read `.report.md`, render to HTML. |
| `--review [file]` | Read HTML, run one-pass automatic refinement. |
| `--themes` | Output theme preview HTML. Do not generate report. |
| `--bundle` | Generate HTML with all CDN libraries inlined. |
| `--from <file>` | If starts with `---`, treat as IR and render. Otherwise treat as raw content. |
| `--theme <name>` | Override theme. Built-in or custom folder under `themes/`. |
| `--template <file>` | Use custom HTML template file. |
| `--output <filename>` | Save HTML to custom filename. |
| `--export-image [mode]` | After generating HTML, export to image via Playwright. |

### 4.2 Slug Rule

- Lowercase the title/topic
- Replace spaces and non-ASCII with hyphens
- Keep only alphanumeric ASCII and hyphens
- Collapse consecutive hyphens
- Trim leading/trailing hyphens
- Max 30 chars

### 4.3 Default Output

`report-<YYYY-MM-DD>-<slug>.html`

### 4.4 Flag Precedence

- `--bundle` CLI flag overrides `charts: cdn` or `charts: bundle` in frontmatter
- `--theme` CLI flag overrides `theme:` in frontmatter

---

## 5. IR Format (.report.md)

### 5.1 Three Parts

1. **YAML frontmatter** (between `---` delimiters)
2. **Markdown prose** (regular headings, paragraphs, bold, lists)
3. **Component blocks** (`:::tag [param=value] ... :::`)

### 5.2 Frontmatter Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `title` | Yes | — | Report title |
| `theme` | No | `corporate-blue` | Theme name |
| `author` | No | — | Author name |
| `date` | No | Today / auto-calculated | Report date |
| `lang` | No | Auto-detected | `zh` or `en` |
| `report_class` | No | `mixed` | `narrative` / `mixed` / `data` |
| `archetype` | No | — | `brief` / `research` / `comparison` / `update` |
| `audience` | No | — | Target reader description |
| `decision_goal` | No | — | What decision this report supports |
| `must_include` | No | — | Source truths that must survive compression |
| `must_avoid` | No | — | Known traps to block |
| `charts` | No | `cdn` | `cdn` or `bundle` |
| `toc` | No | `true` | Table of contents |
| `animations` | No | `true` | CSS animations |
| `abstract` | No | — | One-sentence summary for AI summary block |
| `poster_title` | No | — | Poster headline (opt-in) |
| `poster_subtitle` | No | — | Poster subtitle |
| `poster_note` | No | — | One short closing sentence |
| `template` | No | — | Custom HTML template path |
| `theme_overrides` | No | — | Override theme CSS variables |
| `custom_blocks` | No | — | User-defined component tags |

### 5.3 Numeric Density Classification

| Class | Density | Description |
|-------|---------|-------------|
| `narrative` | < 5% | Primarily text — research, editorial, prose |
| `mixed` | 5–20% | Mix of text and data — project reports, updates |
| `data` | > 20% | Data-heavy — sales dashboards, KPI reports |

### 5.4 Component Block Syntax

```md
:::tag [param=value ...]
[body]
:::
```

### 5.5 Built-in Tag Reference

| Tag | Canonical body schema | Auto downgrade target |
|-----|----------------------|----------------------|
| `:::kpi` | `items:` list of `{label, value, delta?, note?}` | `callout` |
| `:::chart` | By `type`: standard charts use `labels + datasets`; `funnel` uses `stages`; `sankey` uses `nodes + links` | `table` |
| `:::table` | Markdown table body | — |
| `:::list` | Multiline Markdown list body | — |
| `:::image` | Param-driven + caption text | — |
| `:::timeline` | Multiline `- Date: Description` | `list` |
| `:::diagram` | YAML body matching selected `type` schema | `callout` |
| `:::code` | Plain text body | — |
| `:::callout` | Plain text / Markdown body | — |

### 5.6 IR Validity Taxonomy

| Term | Meaning |
|------|---------|
| `invalid_syntax` | Parser cannot deterministically recover the intended structure |
| `invalid_semantics` | Block is structurally parseable but expresses the wrong thing |
| `contract_conflict` | SKILL.md, references, examples, or templates disagree |
| `auto_downgrade_target` | Safer fallback component when original block should not survive |

---

## 6. Language Auto-Detection

### 6.1 Algorithm

- Count Unicode range `一-鿿` (CJK characters) in user's topic/message
- If CJK characters > 10% of total, or title/topic contains any CJK → `lang: zh`
- Otherwise → `lang: en`
- If `lang:` is explicitly set in frontmatter, always use that value

### 6.2 Applied To

- HTML `lang` attribute
- Placeholder text (`[数据待填写]` vs `[INSERT VALUE]`)
- TOC label (`目录` vs `Contents`)
- `report-meta` date format

---

## 7. Theme Routing

### 7.1 Priority Order

| Priority | Keywords | Theme | Use Case |
|----------|----------|-------|----------|
| 1st | 周报、日报、月报、工作汇报、本周、下周 | `regular-lumen` | Periodic reports |
| 2nd | 季报、销售、业绩、营收、KPI | `corporate-blue` | Business & commercial |
| 3rd | 研究、调研、学术、白皮书 | `minimal` | Academic & research |
| 4th | 技术、架构、API、系统、性能 | `dark-tech` | Technical documentation |
| 5th | 新闻、行业、趋势、观察 | `newspaper` | Editorial & news |
| 6th | 年度、故事、增长、复盘 | `data-story` | Data narrative |
| 7th | 看板、board、dashboard | `dark-board` | Project boards & dashboards |
| 8th | 项目、进展、状态、任务 (fallback) | `corporate-blue` | General work reports |

### 7.2 Built-in Themes

| Theme | Description |
|-------|-------------|
| `corporate-blue` | Business & commercial |
| `minimal` | Clean, academic |
| `dark-tech` | Technical documentation |
| `dark-board` | Project dashboards |
| `data-story` | Data narrative |
| `newspaper` | Editorial & news |
| `regular-lumen` | Periodic reports (warm tone, poster-style) |

---

## 8. Machine-Readable Structure

### 8.1 Three Layers

1. **Summary JSON** — Top-level metadata for quick AI reading
2. **Section annotations** — HTML data attributes for section-level access
3. **Component raw data** — Structured data for each component block

### 8.2 Summary JSON Structure

```json
{
  "title": "Report Title",
  "date": "YYYY-MM-DD",
  "author": "Name",
  "theme": "corporate-blue",
  "report_class": "mixed",
  "sections": [
    {"id": "section-1", "title": "...", "type": "kpi|chart|text|..."},
    ...
  ],
  "kpi_values": [
    {"label": "...", "value": "...", "delta": "..."},
    ...
  ]
}
```

### 8.3 Invariants

- Summary JSON must be valid and parseable
- Section annotations must match actual HTML structure
- Component raw data must match component block input

---

## 9. Cross-Module Boundaries

### 9.1 IR → Rendering

- IR is single source of truth for report structure
- Renderer parses IR and generates HTML
- Invalid IR = generation failure with actionable error

### 9.2 Theme → Rendering

- Theme provides CSS variables and component styles
- Theme overrides apply on top of base theme
- Custom themes in `themes/` directory

### 9.3 Components → Rendering

- Each component type has a rendering contract
- Rendering must match component block input
- Auto-downgrade targets apply when component is invalid

---

## 10. Anti-Patterns

Do not do these:

1. **Fabricating data**
   - Use `[INSERT VALUE]` placeholder for missing data
   - Never invent numbers or facts

2. **Using Chart.js**
   - ECharts only for all charts
   - Chart.js is not part of the active contract

3. **Using generic title labels**
   - Follow title quality rules from slide-creator
   - Titles should be informative

4. **Ignoring IR validity taxonomy**
   - Use consistent terms: invalid_syntax, invalid_semantics, contract_conflict, auto_downgrade_target
   - Don't invent new terms

5. **Placeholder-only KPI blocks in narrative reports**
   - Narrative reports should not have KPI placeholders
   - Use callout instead

6. **Non-chronological timeline**
   - Timeline must be genuinely chronological
   - Use list for parallel items

---

## 11. Operational Rule

For core pipeline bugs:

> A fix is not complete until the generated HTML is valid, renders correctly in browser, and machine-readable structure is parseable.