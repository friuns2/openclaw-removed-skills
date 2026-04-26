---
name: kai-report-creator
description: Use when the user wants to CREATE or GENERATE a report, business summary, data dashboard, or research doc — 报告/数据看板/商业报告/研究文档/KPI仪表盘. Handles Chinese and English equally. Supports generating from raw notes, data, URLs, or an approved plan file. Use for --plan (structure first), --generate (render to HTML), --review (one-pass automatic refinement), --themes (preview styles), --from FILE, --bundle, --export-image flags. Does NOT apply to exporting finished HTML to PPTX/PNG (use kai-html-export) or creating slide decks (use kai-slide-creator).
version: 1.20.1
user-invocable: true
metadata: {"openclaw": {"emoji": "📊"}}
---

# kai-report-creator

Generate beautiful, single-file HTML reports with mixed text, charts, KPIs, timelines, diagrams, and images — zero build dependencies, mobile responsive, embeddable anywhere, and machine-readable for AI pipelines.

## Core Principles

1. **Zero Dependencies** — Single HTML files with all CSS/JS inline or from CDN. No npm, no build tools.
2. **User Provides Data, AI Provides Structure** — Never fabricate numbers or facts. Use placeholder text (`[INSERT VALUE]`) if data is missing.
3. **Progressive Disclosure for AI** — Output HTML embeds a 3-layer machine-readable structure (summary JSON → section annotations → component raw data) so downstream AI agents can read reports efficiently.
4. **Mobile Responsive** — Reports render correctly on both desktop and mobile.
5. **Plan Before Generate** — For complex reports, `--plan` creates a `.report.md` IR file first; `--generate` renders it to HTML.

## Command Routing

When invoked as `/report [flags] [content]`, parse flags and route:

| Flag | Action |
|------|--------|
| `--plan "topic"` | Generate a `.report.md` IR file only. Do NOT generate HTML. Save as `report-<slug>.report.md`. |
| `--generate [file]` | Read the specified `.report.md` file (or IR from context if no file given), render to HTML. |
| `--review [file]` | Read the specified HTML file and run one-pass automatic refinement using the report review checklist. |
| `--themes` | Output `report-themes-preview.html` showing all 7 built-in themes. Do not generate a report. |
| `--bundle` | Generate HTML with all CDN libraries inlined. Overrides `charts: cdn` in frontmatter. |
| `--from <file>` | If file's first line is `---`, treat as IR and render directly. Otherwise treat as raw content, generate IR first then render. If ambiguous, ask user to confirm. |
| `--theme <name>` | Override theme. Built-in: `corporate-blue`, `minimal`, `dark-tech`, `dark-board`, `data-story`, `newspaper`, `regular-lumen`. Custom: any folder name under `themes/` (e.g. `--theme my-brand` uses `themes/my-brand/`). See `themes/README.zh-CN.md`. |
| `--template <file>` | Use a custom HTML template file. Read it and inject rendered content into placeholders. |
| `--output <filename>` | Save HTML to this filename instead of the default. |
| `--export-image [mode]` | After generating HTML, also export to image via `scripts/export-image.py`. Mode: `im` (default), `mobile`, `desktop`, `all`. Requires: `pip install playwright && playwright install chromium`. |
| (no flags, text given) | One-step: generate IR internally (do not save it), immediately render to HTML. |
| (no flags, no text, IR in context) | Detect IR in context (starts with `---`), render directly to HTML. |

**`--export-image` usage:** When this flag is present, after saving the HTML file run:
```
python <skill-dir>/scripts/export-image.py <output.html> --mode <mode>
```
Report the image path(s) to the user. If playwright is not installed, print the install instructions and skip — do not error out.

**Default output filename:** `report-<YYYY-MM-DD>-<slug>.html`

**Slug rule:** Lowercase the title/topic. Replace spaces and non-ASCII characters with hyphens. Keep only alphanumeric ASCII and hyphens. Collapse consecutive hyphens. Trim leading/trailing hyphens. Max 30 chars. Examples: `"2024 Q3 销售报告"` → `2024-q3`, `"AI产品调研"` → `ai`, `"Monthly Sales Report"` → `monthly-sales-report`.

**Flag precedence:** `--bundle` CLI flag overrides `charts: cdn` or `charts: bundle` in frontmatter.

## IR Format (.report.md)

The Intermediate Representation (IR) is a `.report.md` file with three parts:
1. YAML frontmatter (between `---` delimiters)
2. Markdown prose (regular headings, paragraphs, bold, lists)
3. Fence blocks for components: `:::tag [param=value] ... :::`

### Frontmatter Fields

    ---
    title: Report Title                    # Required
    theme: corporate-blue                  # Optional. Default: corporate-blue
    author: Name                           # Optional
    date: YYYY-MM-DD                       # Optional. Auto-calculated based on report_class: weekly → YYYY-MM-DD～YYYY-MM-DD; monthly → YYYY-MM; daily → YYYY-MM-DD. Default: today
    lang: zh                               # Optional. zh | en. Auto-detected from content if omitted.
    report_class: mixed                    # Optional but strongly recommended. narrative | mixed | data
    archetype: research                    # Optional lightweight archetype hint for silent classification. `brief`, `research`, `comparison`, `update`
    audience: "Busy decision-maker"        # Optional but strongly recommended for async reading + evals.
    decision_goal: "Decide next move"      # Optional but strongly recommended for async reading + evals.
    must_include:                          # Optional. Source truths that must survive compression.
      - Key fact that must remain
    must_avoid:                            # Optional. Known traps to block during generation/review.
      - Decorative placeholder chart
    charts: cdn                            # Optional. cdn | bundle. Default: cdn
    toc: true                              # Optional. true | false. Default: true
    animations: true                       # Optional. true | false. Default: true
    abstract: "One-sentence summary"       # Optional. Used in AI summary block.
    poster_title: "Short poster headline"  # Optional. Poster summary mode is opt-in; use only when H1 is too literal.
    poster_subtitle: "Subtitle below the poster title"  # Optional. Only use with poster_title. Never infer or merge from title punctuation.
    poster_note: "One short closing sentence"  # Optional. Summary-card left panel should end with one short sentence, not a paragraph block.
    template: ./my-template.html           # Optional. Custom HTML template path.
    theme_overrides:                       # Optional. Override theme CSS variables.
      primary_color: "#E63946"
      font_family: "PingFang SC"
      logo: "./logo.png"
    custom_blocks:                         # Optional. User-defined component tags.
      my-tag: |
        <div class="my-class">{{content}}</div>
    ---

For simple reports these metadata fields can be omitted. For complex or high-stakes reports, keep `report_class`, `audience`, `decision_goal`, `must_include`, and `must_avoid` in the IR so review and eval can measure whether the async-reading intent survived. `archetype` remains optional; use it only as a lightweight hint when the structure clearly matches `brief`, `research`, `comparison`, or `update`.

Poster summary mode is opt-in. Do not infer `poster_title` or `poster_subtitle` from punctuation in `title`.

### Component Block Syntax

    :::tag [param=value ...]
    [YAML fields or plain text]
    :::

Plain Markdown between blocks renders as rich text (headings, paragraphs, bold, lists, links).

### IR Validity Taxonomy

Use these four terms consistently when describing bad IR:

- `invalid_syntax` — the parser cannot deterministically recover the intended structure.
- `invalid_semantics` — the block is structurally parseable but expresses the wrong thing for that component.
- `contract_conflict` — `SKILL.md`, `references/`, examples, or templates disagree about the contract.
- `auto_downgrade_target` — the safer fallback component when the original block should not survive as-is.

`examples/` are illustrative, not canonical. If examples disagree with `SKILL.md` or `references/rendering-rules.md`, that is a `contract_conflict` and must be fixed before expanding the rules further.

### Built-in Tag Reference

| Tag | Canonical body schema | Compatibility | Auto downgrade target |
|-----|-----------------------|---------------|-----------------------|
| `:::kpi` | `items:` list of `{label, value, delta?, note?}` | Short-line `- Label: Value Delta` accepted for compatibility only | `callout` |
| `:::chart` | By `type`: standard charts use `labels + datasets`; `funnel` uses `stages`; `sankey` uses `nodes + links` | None | `table` |
| `:::table` | Markdown table body | None | — |
| `:::list` | Multiline Markdown list body | Single-line `:::list ... :::` accepted for compatibility only | — |
| `:::image` | Param-driven + caption text | None | — |
| `:::timeline` | Multiline `- Date: Description` with whitelist date tokens | None | `list` |
| `:::diagram` | YAML body that matches the selected `type` schema | None | `callout` |
| `:::code` | Plain text body | None | — |
| `:::callout` | Plain text / Markdown body | `icon` override allowed only from whitelist | — |

**Plain text (default):** Any Markdown outside a `:::` block is rendered as rich text — no explicit `:::text` tag needed.

**Chart library rule:** Use **ECharts** for ALL charts. `Chart.js` is not part of the active contract.

### Canonical Contracts for High-Risk Tags

#### `:::kpi`

Canonical input:

```md
:::kpi
items:
  - label: 总营收
    value: ¥2,450万
    delta: ↑12%
    note: 同比
:::
```

Compatibility input:

```md
:::kpi
- 总营收: ¥2,450万 ↑12%
:::
```

- Allowed input: short numeric values or short phrases in `value`; optional `delta` may be `↑12%`, `↓2%`, `→`, or short contextual text such as `↑12% MoM`.
- Prohibited input: descriptive sentences in `value`; placeholder-only KPI blocks in `narrative` reports; placeholder-only KPI blocks in `mixed` reports with no real numbers.
- `invalid_syntax`: body is neither canonical `items:` YAML nor the compatibility short-line format.
- `invalid_semantics`: `value` contains a sentence/paragraph, or the entire KPI block fabricates a visual anchor with placeholders.
- `contract_conflict`: none.
- `auto_downgrade_target`: `callout`.

#### `:::chart`

- Allowed `type`: `bar`, `line`, `pie`, `scatter`, `radar`, `funnel`, `sankey`.
- Canonical body schemas:
  - Standard charts (`bar|line|pie|radar`) use `labels:` plus `datasets:`.
  - `scatter` uses `datasets:` where each dataset provides `points: [[x, y], ...]`.
  - `funnel` uses `stages:` with `{label, value}` objects.
  - `sankey` uses `nodes:` plus `links:`.
- Prohibited input: free-form YAML that invents undeclared keys; placeholder-only charts in `narrative` reports; placeholder-only charts in `mixed` reports with no real numbers.
- `invalid_syntax`: body does not match the schema required by its `type`.
- `invalid_semantics`: the chart shape is parseable but mismatched to the content, or the chart is only decorative placeholder data.
- `contract_conflict`: prior Chart.js/ECharts split. Resolved now: ECharts-only.
- `auto_downgrade_target`: `table` (preferred) or `callout` when the source has no chartable data.

#### `:::timeline`

- Canonical input: multiline `- Date: Description`.
- Allowed `Date` tokens: `YYYY-MM-DD`, `YYYY-MM`, `YYYY`, `Q[1-4] YYYY`, `Day N`, `Week N`, `Month N`.
- Prohibited input: principles, categories, capability buckets, or any parallel items that are not genuinely chronological.
- `invalid_syntax`: not in `- Date: Description` form.
- `invalid_semantics`: syntactically valid but `Date` is not actually a time marker.
- `contract_conflict`: none.
- `auto_downgrade_target`: `list`.

#### `:::diagram`

- Allowed `type`: `sequence`, `flowchart`, `tree`, `mindmap`.
- Canonical body schemas:
  - `sequence` → `actors:` + `steps:` with `{from, to, msg}`
  - `flowchart` → `nodes:` + `edges:` with `{from, to, label?}`
  - `tree` → `root:` + recursive `children:`
  - `mindmap` → `center:` + `branches:`
- Prohibited input: ad-hoc YAML invented per document without a declared per-type schema.
- `invalid_syntax`: body missing the required keys for the chosen `type`.
- `invalid_semantics`: structure is parseable but the chosen diagram type misrepresents the content.
- `contract_conflict`: examples acting as hidden spec. Resolved now: schema is declared here and in `references/rendering-rules.md`.
- `auto_downgrade_target`: `callout`.

## Language Auto-Detection

When generating any report, auto-infer `lang` from the user's message if not explicitly set in frontmatter:
- Count Unicode range `\u4e00-\u9fff` (CJK characters) in the user's topic/message
- If CJK characters > 10% of total characters, or the title/topic contains any CJK characters → `lang: zh`
- Otherwise → `lang: en`
- If `lang:` is explicitly set in frontmatter, always use that value

Apply `lang` to: the HTML `lang` attribute, placeholder text (`[数据待填写]` for zh, `[INSERT VALUE]` for en), TOC label (`目录` vs `Contents`), and `report-meta` date format.

## Content-Type → Theme Routing

When no `--theme` is specified and no `theme:` in frontmatter, suggest a theme based on the topic keywords. This is a recommendation only — the user can always override with `--theme`.

**Routing priority (order matters — first match wins):**

| Priority | Topic keywords | Recommended theme | Use case |
|----------|----------------|-------------------|---------|
| **1st** | 周报、日报、月报、工作汇报、进展汇报、团队汇报、本周、下周、本周期 / weekly, daily, monthly, work report, progress report, team report, this week, next week | `regular-lumen` | 周期性工作报告（本周期复盘 + 下周期规划）· 暖色调 Poster-style |
| **2nd** | 季报、销售、业绩、营收、KPI、数据分析、商业、季度 / quarterly, sales, revenue, KPI, business | `corporate-blue` | Business & commercial |
| **3rd** | 研究、调研、学术、白皮书、内部文档、团队文档 / research, survey, academic, whitepaper, internal, team | `minimal` | Academic & research & editorial |
| **4th** | 技术、架构、API、系统、性能、部署、代码、工程 / tech, architecture, API, system, performance, engineering | `dark-tech` | Technical documentation |
| **5th** | 新闻、行业、趋势、观察、报道 / news, industry, trend, newsletter | `newspaper` | Editorial & news |
| **6th** | 年度、故事、增长、复盘、回顾 / annual, story, growth, retrospective | `data-story` | Data narrative |
| **7th** | 项目看板、状态看板、进度看板、品牌、用研 / project board, status board, progress board, brand, UX | `dark-board` | Project boards & system dashboards |
| **8th** | 项目进展、项目状态、项目完成、任务进展 / project progress, project status, task progress (通用工作报告关键词，不含看板) | `corporate-blue` | 通用工作报告 fallback — 当主题不明确时，使用商务风格而非暗色技术风格 |

When routing, output: *"推荐使用 `[theme]` 主题 ([theme description])，可用 `--theme` 覆盖。"* (or English equivalent).

## --plan Mode

When the user runs `/report --plan "topic"`:

**Step 0 — Auto-detect language.** Apply language auto-detection rules above.

**Step 1 — Suggest theme.** Check content-type routing table using **priority order matching**:

1. Scan topic for **周期报告关键词**（第1优先级）：周报、日报、月报、工作汇报、进展汇报、本周、下周 → if found, suggest `regular-lumen`
2. If not found, scan for **商务关键词**（第2优先级）：季报、销售、业绩、营收、KPI → if found, suggest `corporate-blue`
3. If not found, scan for **研究关键词**（第3优先级）：研究、调研、学术、白皮书 → if found, suggest `minimal`
4. If not found, scan for **技术关键词**（第4优先级）：技术、架构、API、系统、性能 → if found, suggest `dark-tech`
5. If not found, scan for **新闻关键词**（第5优先级）：新闻、行业、趋势、观察 → if found, suggest `newspaper`
6. If not found, scan for **年度关键词**（第6优先级）：年度、故事、增长、复盘 → if found, suggest `data-story`
7. If not found, scan for **看板关键词**（第7优先级）：看板、board、dashboard → if found, suggest `dark-board`
8. **Fallback (第8优先级)**：如果包含"项目/进展/状态/任务"等通用工作关键词 → suggest `corporate-blue`（而非dark-tech/dark-board）
9. If no keyword matches, default to `corporate-blue`

**Important:** Report the match to user: *"推荐使用 `[theme]` 主题 ([theme description])，可用 `--theme` 覆盖。"* (or English equivalent).

**Step 1.5 — Analyze content nature.**

Scan the user's topic/content input and compute numeric density:
- Count **numeric tokens**: words/phrases containing digits with quantitative meaning — e.g. `128K`, `8.6%`, `¥3200万`, `$1.2B`, `+18%`, `3x`. Exclude ordinals used as labels (`Q3`, `第一`, `Step 2`).
- **Density** = numeric token count / total word count (Chinese: character-segment count; English: whitespace-split word count)

Classify:

| Class | Density | Description |
|-------|---------|-------------|
| `narrative` | < 5% | Primarily text — research, editorial, philosophy, retrospective prose |
| `mixed` | 5–20% | Mix of text and data — project reports, team updates, product reviews |
| `data` | > 20% | Data-heavy — sales dashboards, KPI reports, financial summaries |

(Boundary: exactly 20% counts as `mixed`.)

If total word count < 10 (e.g. a bare topic like `Q3`), skip density calculation and default to `mixed`.

Announce the classification to the user. Examples:
- narrative: "内容以文字叙述为主（narrative），将使用 callout/timeline 作为视觉锚点，不插入空 KPI 占位符。"
- mixed: "内容为图文混合（mixed），有明确数字的章节才会使用 KPI/图表组件。"
- data: "内容以数据为主（data），将使用 KPI/图表作为主要视觉锚点。"
- (English equivalent when `lang: en`)

Store the class (`narrative` / `mixed` / `data`) and apply it in Step 2 item 3.5 (component routing) and item 4 (visual rhythm rules).

**Silent classify with `references/spec-loading-matrix.md`.** Keep this internal. Optionally add `archetype` only when the report clearly behaves like `brief`, `research`, `comparison`, or `update`. Never turn this into a separate user-facing phase.

**Step 2 — Plan the structure.**

**Pre-load content extraction rules:** If frontmatter `theme: regular-lumen` OR topic keywords match **周期报告关键词**（周报|日报|月报|工作汇报|进展汇报|本周|下周|daily|weekly|monthly|periodic report）, read `references/regular-report-content-rules.md` before generating the IR. Apply periodic-specific extraction rules (KPI selection, timeline narrative, period divider) to refine user content into structured periodic report format.

1. Think about the report structure: appropriate sections, data the user likely has.
2. Generate a complete `.report.md` IR file containing:
   - Complete frontmatter with all relevant fields filled in
   - Explicit async-reading metadata for non-trivial reports: `report_class`, `audience`, `decision_goal`, `must_include`, `must_avoid`
   - Add `poster_title` and `poster_subtitle` only when the report truly needs a stronger poster headline than the document title, and only if that stronger headline stays faithful to the source
   - If you use poster summary mode, keep the left panel minimal: title hierarchy plus one short closing sentence (`poster_note`) near the bottom
   - At least 3–5 sections with `##` headings
   - A mix of component types (kpi, chart, table, timeline, callout, etc.)
   - **Optional emphasis plan:** If badges would materially improve scanability, note 1–2 possible `.badge` placements. Badges are optional visual enhancements, not first-class IR tags.
   - Placeholder values for data: use `[数据待填写]` (zh) or `[INSERT VALUE]` (en) — **never fabricate numbers**
   - Comments for fields the user should customize
   - **Content-tone color hint:** Based on topic keywords, add a `theme_overrides` block in the frontmatter with a commented `primary_color` suggestion matching the content tone (see `references/design-quality.md` § Content-Tone Color Calibration). Example for a research report:
     ```yaml
     theme_overrides:
       primary_color: "#7C6853"  # 思辨/研究气质 — 温暖棕色 (change to suit your brand)
     ```
3. **Chart type selection guidance** — when choosing `:::chart type=?`, apply these rules:
   - `bar` / `line` / `pie`: standard comparisons, trends, proportions
   - `radar`: multi-dimension capability/coverage comparison
   - `funnel`: single-path conversion with ordered stages
   - `sankey`: **use when data has quantified flows between named categories** — budget allocation across departments, multi-source conversion funnels (where users branch to different paths), supply chain, energy/material flows. Key signal: the data has `source → target: value` triples. Requires ECharts.
   - Do NOT use sankey for simple proportions (use pie) or ordered stages with no branching (use funnel).

3.5. **Content Nature → Component Routing** — apply based on the class determined in Step 1.5:

| Class | Preferred visual anchors | Prohibited |
|-------|--------------------------|------------|
| `narrative` | `:::callout`, `:::timeline`, `:::diagram`, highlighted prose (`.highlight-sentence`, not an IR tag) | `:::kpi` and `:::chart` with all-placeholder values |
| `mixed` | `:::callout`/`:::timeline` by default; `:::kpi`/`:::chart` only when that section contains real numbers from the source | `:::kpi` or `:::chart` where every value is a placeholder |
| `data` | `:::kpi` > `:::chart` > others | — (existing behavior) |

**narrative strict rule:** Never generate a `:::kpi` or `:::chart` block where all values are `[数据待填写]` / `[INSERT VALUE]`. If a section has no numbers, use `:::callout`, `:::timeline`, or `:::diagram` instead.

**mixed rule:** A `:::kpi` block is only allowed if at least one value in that block is a real number extracted from the source content.

**KPI value content rule:** KPI values must be short numbers or brief phrases (≤8 Chinese chars / ≤3 English words). Never put descriptive sentences or paragraphs in KPI values. If the source content has long descriptions, extract the key number/phrase for the KPI value and put the full explanation in prose or a callout.

4. **Apply visual rhythm rules** when laying out sections:
   - Never place 3 or more consecutive sections containing only plain Markdown prose (no components)
   - Every 4–5 sections, insert a "visual anchor" — type depends on content class from Step 1.5:
     - `narrative`: use `:::callout`, `:::timeline`, `:::diagram`, or a highlighted prose paragraph (`.highlight-sentence`, not an IR tag)
     - `mixed`: use `:::callout`/`:::timeline` by default; use `:::kpi`/`:::chart` only if that section has real numbers
     - `data`: use `:::kpi` or `:::chart` (existing behavior)
   - Ideal rhythm by class:
     - `narrative`: `lead-block/claim → explanation → scan anchor → explanation → quote/action-grid → ...`
     - `mixed`: `prose → callout → prose → kpi(if numbers) → prose → timeline → ...`
     - `data`: `prose → kpi → chart/table → callout/timeline → prose → ...`
   - For `narrative` and `mixed`, prefer the cadence `claim -> explanation -> scan anchor` over a uniform stack of ordinary paragraphs.
   - These are optional prose upgrades, not default required blocks.
   - When a section opens with a decisive statement, upgrade it into a `lead-block` or `highlight-sentence` instead of leaving it as plain body text.
   - When a section resolves into 2–5 concrete implications or actions, prefer an `action-grid` / `action-card` pattern over one long paragraph or a weak unordered list.
   - When a single sentence carries the section's strongest judgment, render it as a `section-quote` instead of burying it inside prose.
   - Do not add more than one of `lead-block` / `section-quote` / `action-grid` by default inside the same section unless the source material clearly warrants it.
   - If uncertain, keep normal paragraphs and add one clearer scan anchor instead of forcing a cadence block.
   - **Never** break up consecutive prose sections by inserting a `:::kpi` with placeholder values in `narrative` or `mixed` reports — use `:::callout` instead
5. Save to `report-<slug>.report.md` using the Write tool.
6. Tell the user:
   - The IR file path
   - Which placeholders need to be filled in
   - The suggested theme (from routing) and how to override it
   - The command to render: `/report --generate <filename>.report.md`

**Stop after saving the IR file. Do NOT generate HTML in --plan mode.**

## --themes Mode

When the user runs `/report --themes`:
1. Read `templates/themes-preview.html` (relative to this skill file's directory) using the Read tool.
2. Write its content verbatim to `report-themes-preview.html` using the Write tool.
3. Tell the user the file path and ask them to open it in a browser.

## Review Mode

When the user runs `/report --review [file]`:

1. Read the specified HTML file.
2. Load `references/review-checklist.md`.
3. Run the 8-checkpoint report review system.
4. Apply **hard rules** automatically.
5. Apply **ai-advised rules** only when confidence is high enough to preserve factual accuracy.
6. This is **one-pass automatic refinement** — no confirmation window, no interactive approval loop.
7. If the user wants a structured summary of what changed, format it using `references/review-report-template.md`.
8. Write the revised HTML back to the target file unless the user asked for diagnosis only.
9. Tell the user what improved and what was intentionally left untouched.

## Component Rendering Rules

When rendering IR to HTML, apply component-specific rendering rules. Each component must be wrapped with `data-component` attribute for AI readability.

**Load `references/rendering-rules.md` and `references/design-quality.md` before generating any HTML.** These files contain the detailed rendering rules and design quality baseline.

**Always load `references/anti-patterns.md` before `--generate`.** Use it to reject report-specific failure modes such as fake KPI anchors, decorative charts, pseudo timelines, template headings, badge quota thinking, color flood, summary without judgment, and action without decision context.

**Load `references/diagram-decision-rules.md` whenever a diagram or diagram-like structure is being considered.** Use it to decide whether the content should stay prose/list/callout instead of becoming `:::diagram`.

**Load `references/spec-loading-matrix.md` before `--plan` and `--generate` as a silent classifier.** Use it to keep routing minimal: determine `report_class`, optionally add `archetype`, then load only the references that materially help the current report.

### HARD RULES (must be enforced before writing HTML)

These rules are non-negotiable. After assembling the full HTML, search for violations and fix them before writing the file.

**Rule 1 — KPI value length:** Every `.kpi-value` element must contain ≤8 Chinese characters OR ≤3 English words. If any KPI value is a sentence or paragraph, move the explanation to prose/callout and keep only the short number/phrase in the KPI.

**Rule 2 — Timeline validity:** Every `.timeline-item` must have a `.timeline-date` with an actual whitelist date/timestamp. If any timeline item uses a generic label (e.g. a principle name or feature description) as its "date", convert the entire timeline to `:::list` or `:::callout`.

**Rule 3 — Callout icon normalization:** `icon` may only render from the whitelist in `references/rendering-rules.md`. Strip U+FE0F if present; if the icon is still outside the whitelist, ignore it and fall back to the default icon for that callout type.

**Rule 4 — No U+FE0F in output:** The final HTML must contain zero U+FE0F characters. Default callout icons use base emoji without variant selectors (ℹ not ℹ️, ⚠ not ⚠️).

**Rule 5 — KPI summary values are short:** The `report-summary` JSON `kpis[].value` field feeds the compact summary card. If a value exceeds Rule 1 length, use a short phrase and move the explanation elsewhere.

### Heading quality rules

**Do NOT use these generic labels as h2 headings:** 身份定位, 核心能力, 核心原则, 使用场景, Overview, Background, Key Findings, Summary, Next Steps, 问题分析, 关键发现, 总结, 简介, 概述, 结论, 展望, 背景, 方法论.

**Instead, use information-bearing headings that state a claim or implication:**
- ❌ `## 身份定位` → ✅ `## 不是搜索框，是办公搭档`
- ❌ `## 核心能力` → ✅ `## 四大能力覆盖办公全场景`
- ❌ `## 核心原则` → ✅ `## 真诚、安全、专业 — 三条底线加一条准则`
- ❌ `## 使用场景` → ✅ `## 六大场景，从信息查询到汇报全覆盖`

**Template for h2 headings:** Choose one pattern based on content:
- "不是 X，是 Y" — identity/positioning sections
- "N 个 [noun] 覆盖/支撑/驱动 [scope]" — capability/capacity sections
- "[A]、[B]、[C] — N 条底线/准则/支柱" — principle/rules sections
- "N 大场景，从 [X] 到 [Y]" — scenario/coverage sections

When the report is explicitly comparing named vendors, models, or tools, set `data-report-mode="comparison"` on the outer report container and use `.badge--entity-a/.badge--entity-b/.badge--entity-c` only for entity identity. Do not use entity colors on generic KPI values or generic badges.

**Badges are optional visual enhancements, not a first-class IR tag.** Only emit badge HTML when it clarifies status, category, or entity identity. Never insert badges just to satisfy a quota.

**CRITICAL: The final HTML must contain zero `:::` sequences.** Any `:::tag`, param line, or closing `:::` appearing in the output means a directive was not converted — find it and fix it before writing the file.

### Component Overview

| Tag | Purpose | Required params | Optional params |
|-----|---------|----------------|-----------------|
| `:::kpi` | KPI cards with trend indicators | (none — list items in body) | (none) |
| `:::chart` | Charts (bar/line/pie/scatter/radar/funnel/sankey) | `type` | `title`, `height` |
| `:::table` | Data tables | (none — Markdown table in body) | `caption` |
| `:::list` | Styled lists | (none — list items in body) | `style` (ordered\|unordered) |
| `:::image` | Images with captions | `src` | `layout` (left\|right\|full), `caption`, `alt` |
| `:::timeline` | Timeline (dates only — parallel items use `:::list`) | (none — list items in body) | (none) |
| `:::diagram` | Diagrams (sequence/flowchart/tree/mindmap) | `type` | (none) |
| `:::code` | Syntax-highlighted code blocks | `lang` | `title` |
| `:::callout` | Callout boxes | `type` (note\|tip\|warning\|danger) | `icon` |

Plain Markdown outside `:::` blocks renders as rich text (headings, paragraphs, bold, lists, links).

**Chart library rule:** Use **ECharts** for ALL charts. Do not generate `Chart.js` branches.

## Theme CSS

Load theme CSS from `templates/themes/` and assemble in order.

**See `references/theme-css.md` for CSS assembly rules.**

## HTML Shell Template

Generate a complete self-contained HTML file with embedded CSS/JS.

**See `references/html-shell-template.md` for the full HTML structure.**

## TOC Link Generation

**See `references/toc-and-template.md` for TOC link rules, theme override injection, and custom template mode.**

## --generate Mode

When the user runs `/report --generate [file]`:

1. **Read the IR file** — read the specified `.report.md` file (or IR from context).
2. **Load reference files** — read ALL of these before generating any HTML:
   - `references/spec-loading-matrix.md` — silent classification + minimal spec routing
   - `references/rendering-rules.md` — component rendering rules
   - `references/design-quality.md` — design quality baseline + anti-slop rules
   - `references/anti-patterns.md` — report-specific failure modes to reject before render
   - `references/html-shell-template.md` — HTML shell structure
   - `references/theme-css.md` — CSS assembly rules
   - `references/review-checklist.md` — review checklist
   - `references/diagram-decision-rules.md` — load whenever a diagram or diagram-like structure is being considered
3. Parse the frontmatter to get metadata and settings.
   **智能日期显示规则（仅适用于周期报告主题：regular-lumen、corporate-blue 等）**：
   - 如果 `date` 字段已存在 → 直接使用
   - 否则根据 `report_class` 和主题自动计算：
     - **周报**：从标题/内容提取周信息，计算周一～周日范围，显示 `YYYY-MM-DD～YYYY-MM-DD`
     - **月报**：显示 `YYYY-MM`
     - **日报**：显示 `YYYY-MM-DD`
     - **其他报告类型**：显示当天 `YYYY-MM-DD`
   - 其他主题（dark-tech、minimal 等）使用默认日期显示 `YYYY-MM-DD`
4. Select the appropriate theme CSS.
4.5. **Run guard validation** — call Python guard before rendering (v4 guardrails):
     - If file-backed: read IR file content → ir_text
     - If context-backed: use IR string from context → ir_text
     - Call guard: `python <skill-dir>/scripts/guard_validate.py` (pass ir_text via stdin or temp file)
     - Guard resolves report_class using the same path as --generate (Step 1.5 density detection → default "mixed")
     - Guard calls contract_checks validators with resolved class (zero drift)
     - Read JSON output from guard
     - If exit code 2 (fatal: missing title) → STOP generation, report error to user
     - If exit code 1 (invalid blocks) → for each invalid block, apply auto_downgrade_target:
       - `:::kpi` invalid → downgrade to `:::callout`
       - `:::chart` invalid → downgrade to `:::table`
       - `:::timeline` invalid → downgrade to `:::list`
       - `:::diagram` invalid → downgrade to `:::callout`
       - Tell user which blocks were downgraded and why (status field in JSON)
     - If exit code 0 (valid) → continue generation normally
5. Render all components according to Component Rendering Rules (including HARD RULES).
6. Apply chart library selection rule.
7. Build the HTML shell with TOC, AI summary, animations. **Replace `[version]` in the footer with the current skill version from SKILL.md frontmatter.**
   **Embed IR hash meta tag:**
   - Replace `[ir-hash]` placeholder in `<meta name="ir-hash" content="sha256:[ir-hash]">`
   - HASH = sha256 of the IR text content (first 16 hex chars), prefixed with `sha256:`
   - IR text 来源：
     - File-backed: IR file content (`read_text()` from the `.report.md` file)
     - Context-backed: IR string extracted directly from context (no file read)
   - Both paths hash the same `ir_text` content, not the file path
8. **Pre-write validation** — scan the assembled HTML for these violations and fix each one found:
   - **L0: Content checks**
     - Search `:::` in HTML → convert unconverted directives
     - Search `<meta name="ir-hash"` → must exist with non-empty `sha256:` prefix content (validates IR hash embedded)
     - Search for generic h2 headings from the forbidden list → rewrite with information-bearing text
     - Search `.kpi-value` elements → verify each ≤8 Chinese chars / ≤3 English words AND has `font-variant-numeric: lining-nums tabular-nums` (or equivalent)
     - Search `.number` in CSS → must exist with `font-variant-numeric: lining-nums tabular-nums` for body text numbers
     - Search `<span class="number"` → verify numbers in body text use this class for consistent rendering
     - Search `<span class="badge"` → if badges exist, verify each one clarifies status, category, or entity identity instead of filling a quota
     - Search `.timeline-date` → verify each contains a date/timestamp, not a label
     - Search `\uFE0F` → remove all variant selectors from callout icons
     - Search `report-summary` JSON `kpis[].value` → verify each is short (Rule 5)
   - **L1: Design quality checks**
     - Search `text-align: justify` in CSS → replace with left-align
     - Search `#000000` or `#000` as background color → replace with `#111` or `#18181B`
     - Search `letter-spacing` values > `0.05em` on body text → reduce
     - Check `@media (max-width)` rules → ensure no critical functionality is hidden on mobile
   - **L2: HTML Shell Structure (MANDATORY — see `references/design-quality.md` §8)**
     - Search `id="toc-toggle-btn"` → must exist
     - Search `id="toc-sidebar"` → must exist
     - Search `id="card-mode-btn"` → must exist
     - Search `id="sc-overlay"` → must exist
     - Search `id="export-btn"` → must exist
     - Search `id="export-menu"` → must exist
     - Search `id="export-print"` → must exist
     - Search `id="export-png-desktop"` → must exist
     - Search `id="export-png-mobile"` → must exist
     - Search `id="export-im-share"` → must exist
     - Search `id="report-summary"` → must exist (JSON summary block)
     - Search `const printBtn   = document.getElementById('export-print');` → must exist
     - Search `const pngDesktop = document.getElementById('export-png-desktop');` → must exist
     - Search `const pngMobile  = document.getElementById('export-png-mobile');` → must exist
     - Search `const pngIM      = document.getElementById('export-im-share');` → must exist
     - Any missing export item or binding → reconstruct the full export block from `references/html-shell-template.md` instead of patching a partial menu
     - Any other missing shell element → reconstruct from `references/html-shell-template.md` and re-inject
9. **Silent final review pass** — apply `references/review-checklist.md` checkpoints (Category 0: visual hard rules, then Category 1: hard rules 1.1–1.5). Auto-fix violations. This exact step is the `silent final review pass`.
10. Write to `[output_filename].html` using the Write tool.
11. Tell the user the file path and a 1-sentence summary of the report.

**CRITICAL: Follow `references/html-shell-template.md` EXACTLY**

When building the HTML shell, you MUST follow the template structure from `references/html-shell-template.md`:

**CSS Assembly Order** (see `references/theme-css.md`):

**MANDATORY CSS Split Procedure:**
1. Read theme file `templates/themes/[theme-name].css`
2. Search for `/* === POST-SHARED OVERRIDE */` marker
3. Split theme file into two parts: **before-marker** + **after-marker**
4. Assemble `<style>` content in this exact order:
   - **Theme before-marker** (variables + base styles)
   - **Shared CSS** (entire `templates/themes/shared.css`)
   - **Theme after-marker** (overrides + enhancements)
   - **TOC CSS** (inline, from `html-shell-template.md`)
   - **Theme overrides** (if `theme_overrides` in frontmatter)

**Critical:** Do NOT embed the entire theme file in one block. The POST-SHARED section must load AFTER shared.css to override shared defaults (e.g., `.kpi-grid`, `.callout`, `.timeline`). Loading it before shared.css causes shared definitions to override theme-specific styles, breaking the design.

**Pre-write CSS check:** Verify the assembled `<style>` follows the split order above. If a theme has POST-SHARED section, it must appear after shared.css content, not before.

**JavaScript** (inline, NOT from external files):
- Animation scripts (scroll-triggered fade-in, KPI counter)
- TOC scripts (hover to open, click to lock, active state tracking)
- Edit mode scripts
- Export scripts (html2canvas for image export)

All scripts are defined inline in `references/html-shell-template.md`. **Never** attempt to load scripts from external files like `templates/scripts/*.js` — those files do not exist.
