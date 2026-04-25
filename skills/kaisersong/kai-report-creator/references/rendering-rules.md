# Component Rendering Rules

When rendering IR to HTML, apply these rules per block type. Each component must be wrapped with `data-component` attribute for AI readability.

## CRITICAL: IR Directive Parsing — Never Let `:::` Leak Into Output

**Before emitting any HTML, do a mental pass to ensure zero `:::` sequences appear in the final output.** Any `:::` in the output means an IR directive was not converted — this is a bug.

### Block Detection Rules

A `:::` directive block has this structure:

    :::tag [param=value ...]
    [content — can be multiple lines, YAML, or a Markdown list]
    :::

**The closing `:::` is ALWAYS on its own line.** Parse the IR line by line:
1. When you see a line starting with `:::tag`, begin collecting the block body.
2. Collect all lines until you hit a line that is exactly `:::` (the closing marker).
3. Convert the entire block (opening tag + body + closing `:::`) to HTML per the rules below.
4. Never output the `:::tag`, params, closing `:::`, or any part of the directive syntax as text.

**Single-line `:::` format also exists** (generated when the block body is short):

    :::list style=ordered 1. Item A 2. Item B :::

When the opening and closing `:::` appear on the same line, treat everything between the tag/params and the trailing `:::` as the block body, split on the item separators (numbered or bullet items).

**Compatibility only:** Do not generate new single-line blocks as the primary format. They are accepted only to keep older IR renderable.

**NEVER pass `:::` lines through to HTML as `<p>` tags or any other text node.** If in doubt: parse it as a block, not as prose.

## IR Validity Taxonomy

Use these labels consistently when reasoning about IR failures:

- `invalid_syntax` — the body cannot be deterministically parsed into the component's contract.
- `invalid_semantics` — the structure parses, but the component is still the wrong choice for the content.
- `contract_conflict` — repository docs disagree about the same contract.
- `auto_downgrade_target` — the safer component to emit instead.

## Plain Markdown (default)

Convert using standard Markdown rules. Wrap each `##` section in:

    <section data-section="[heading text]" data-summary="[one sentence summary]">
      <h2 id="section-[slug]">[heading text]</h2>
      [section content]
    </section>

**`data-summary` must be plain text only** — write a short human-readable summary of the section in natural language. Never copy raw IR content (lists, prose, component bodies) into it. Especially never include `:::` directive syntax in `data-summary`.

For `###` headings: `<h3 id="section-[slug]">[heading text]</h3>`

`highlight-sentence` is a prose pattern, not an IR tag. If a paragraph deserves emphasized treatment, render it as prose upgraded to `<p class="highlight-sentence">...</p>`; do not invent `:::highlight-sentence`.

`lead-block`, `section-quote`, and `action-grid` are also prose/HTML patterns, not IR tags. Use them only when the surrounding prose clearly supports them.

- `lead-block` — decisive opening sentence that frames the section
- `section-quote` — strongest judgment sentence in a prose-heavy section
- `action-grid` — 2–5 implications, contrasts, or next actions that scan better as cards

For `narrative` reports, prefer `claim -> explanation -> scan anchor` over leaving every section as plain paragraphs.
If uncertain, stay with plain prose plus one callout/list/timeline rather than forcing a rhythm block.

## :::kpi

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

Trend: `↑` = positive (green), `↓` = negative (red), `→` = neutral (gray).

**Allowed input:** `value` must be a short numeric value or brief phrase. `delta` may be a symbol alone (`→`) or a short status like `↑12% MoM`.

**Compatibility note:** Labels containing literal colons should use the canonical YAML form, not the short-line form.

- `invalid_syntax`: body is neither canonical `items:` YAML nor the compatibility short-line format.
- `invalid_semantics`: `value` is a sentence/paragraph, or the whole block exists only as placeholder decoration.
- `contract_conflict`: none.
- `auto_downgrade_target`: `callout`.

Extract the numeric part of Value into `data-target-value`, set `data-prefix` and `data-suffix`.

**Default mode: do not add `data-accent` to KPI cards.** KPI values should stay on the neutral report text color, while the card top rule uses the shared structural accent.

**Comparison mode:** Set `data-report-mode="comparison"` on the comparison wrapper only when the report is explicitly comparing named entities. In that mode, keep KPI values neutral and use `.badge--entity-a`, `.badge--entity-b`, and `.badge--entity-c` only for entity identity chips or table-cell labels.

**Trend badge:** Prefer `.kpi-delta` pill over plain `.kpi-trend` for stronger visual emphasis. Keep `kpi-delta--up`, `kpi-delta--down`, and `kpi-delta--info` visually restrained so they read as status hints, not a second palette system.

**Suffix length rule:** Keep `data-suffix` short (≤4 chars: `K`, `%`, `ms`, `x`). If the unit is longer (e.g. `commits/hour`, `req/sec`, `美元/月`), split number and unit — put the numeric part directly in `.kpi-value` and wrap the unit in `<span class="kpi-suffix">unit</span>`:

    <!-- ✅ Short suffix — inline is fine -->
    <div class="kpi-value" data-target-value="128" data-suffix="K">128K</div>

    <!-- ✅ Long unit — use kpi-suffix span, NO data-target-value (countUp rewrites textContent and destroys the span) -->
    <div class="kpi-value">1,000<span class="kpi-suffix">commits/hour</span></div>

    <!-- ❌ Never put long units directly as plain text content -->
    <div class="kpi-value">1000 commits/hour</div>

    <!-- ❌ Never combine data-target-value with kpi-suffix span — countUp will overwrite the span -->
    <div class="kpi-value" data-target-value="1000">1,000<span class="kpi-suffix">commits/hour</span></div>

**KPI value length rule (MANDATORY):** The `.kpi-value` must contain ONLY a short numeric value or very brief phrase. Maximum length:
- Numeric/currency/percentage: `128K`, `¥2,450万`, `8.6%`, `72`, `↑18%` — ✅
- Short phrase (≤8 Chinese chars / ≤3 English words): `全场景`, `行业领先`, `Top 3` — ✅
- Descriptive sentences or paragraphs: `支持CSV/Excel等表格文件的统计汇总、趋势分析、数据可视化` — ❌

If the content is a full sentence or descriptive paragraph, it belongs in prose, a `:::callout`, or a table cell — **NEVER** in a KPI card. The `:::kpi` block is for at-a-glance metrics, not explanations. When planning a report, if the source content has no short numbers to extract, use `:::callout` or `:::timeline` instead of forcing a `:::kpi` block.

**Summary card KPI value rule:** The `report-summary` JSON `kpis[].value` field feeds the summary card's `.sc-kpi-row-v` (1.15rem, compact). If a KPI value exceeds the length rule above, use the kpi-label or a separate callout for the explanation, and keep the KPI value short for the card.

**Summary card title hierarchy:** When building `report-summary` JSON, support `poster_title` and `poster_subtitle` as optional fields. Use them when the strongest summary-card headline should be more poster-like than the document H1. Render them into `.sc-title-main` and `.sc-title-sub`, with the subtitle below the title rather than merged into one dense line.

**Column count rule (from design-quality.md):** Do NOT default all grids to 3 columns. Match to KPI count:
- 1–2 KPIs → `grid-template-columns: repeat(2, 1fr)`
- 3 KPIs → `grid-template-columns: repeat(3, 1fr)`
- 4 KPIs → `grid-template-columns: repeat(2, 1fr)` (2×2 grid)
- 5–6 KPIs → `grid-template-columns: repeat(3, 1fr)`
- 7+ KPIs → `grid-template-columns: repeat(3, 1fr)` with larger `gap` and visual group dividers
- When one KPI is the hero metric, consider `grid-template-columns: 2fr 1fr 1fr` for emphasis

    <div data-component="kpi" class="kpi-grid">
      <div class="kpi-card fade-in-up">
        <div class="kpi-label">MAU</div>
        <div class="kpi-value" data-target-value="128" data-suffix="K">128K</div>
        <div class="kpi-delta kpi-delta--up">↑18% MoM</div>
      </div>
      <div class="kpi-card fade-in-up">
        <div class="kpi-label">Paid Conversion</div>
        <div class="kpi-value" data-target-value="8.6" data-suffix="%">8.6%</div>
        <div class="kpi-delta kpi-delta--up">↑1.2 pts</div>
      </div>
      <div class="kpi-card fade-in-up">
        <div class="kpi-label">D1 Retention</div>
        <div class="kpi-value" data-target-value="67" data-suffix="%">67%</div>
        <div class="kpi-delta kpi-delta--info">vs 55% avg</div>
      </div>
      <div class="kpi-card fade-in-up">
        <div class="kpi-label">NPS</div>
        <div class="kpi-value" data-target-value="72">72</div>
        <div class="kpi-delta kpi-delta--up">↑8 pts</div>
      </div>
    </div>

**Badges / chips** (`.badge .badge--[color]`): Generic badge classes remain valid input, but they should render through one neutral linen chip system by default, including in prose, table cells, and timeline items.

**Badges are optional visual enhancements, not a first-class IR tag.** Use them only when they materially improve scanability:

| Location | Example | Recommended badge |
|----------|---------|-------------------|
| Section `##` heading | `## 核心能力 <span class="badge badge--teal">核心</span>` | `badge--teal`, `badge--blue`, `badge--purple` |
| `:::kpi` card label | `<div class="kpi-label">转化率 <span class="badge badge--green">已上线</span></div>` | `badge--green`, `badge--orange`, `badge--blue` |
| `:::table` cell | `<td><span class="badge badge--wip">进行中</span></td>` | `badge--wip`, `badge--done`, `badge--todo` |
| `:::timeline` item | `<div class="timeline-content"><span class="badge badge--blue">里程碑</span> 内容</div>` | `badge--blue`, `badge--purple` |
| Callout header area | Before callout body content as a category tag | `badge--orange`, `badge--teal` |

**Badge color selection:** Choose color based on semantic meaning, not aesthetics:
- Status/progress: `badge--done` (completed), `badge--wip` (in progress), `badge--todo` (planned)
- Severity: `badge--warn` (caution), `badge--err` (error/blocker)
- Category/tag: `badge--teal` (capability), `badge--blue` (priority/important), `badge--purple` (feature/special), `badge--orange` (highlight), `badge--green` (positive/verified), `badge--gray` (misc/neutral)
- Entity comparison (only in `data-report-mode="comparison"`): `badge--entity-a`, `badge--entity-b`, `badge--entity-c`

**Do NOT overuse:** Maximum 3 badges per section. More than 3 dilutes their signal value.

**Entity badges:** Only in explicit comparison reports should entity identity use `.badge--entity-a`, `.badge--entity-b`, and `.badge--entity-c`.

    <span class="badge badge--green">Shipped</span>
    <span class="badge badge--orange">In Progress</span>
    <span class="badge badge--red">Critical</span>
    <span class="badge badge--blue">Q4 Priority</span>

    <div data-report-mode="comparison">
      <span class="badge badge--entity-a">OpenAI</span>
      <span class="badge badge--entity-b">Anthropic</span>
      <span class="badge badge--entity-c">Cursor</span>
    </div>

## :::chart

Use **ECharts** for ALL charts in the report. ECharts covers bar/line/pie/scatter/radar/funnel/heatmap/multi-axis/sankey with a single library, avoiding the pitfalls of mixed-library switching (rotated label clipping, artificial data splits, HTML shell rewrites).

Add `<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>` in `<head>` (or inline if `--bundle`).

**Chart.js is NOT used in the standard template.** Do NOT generate Chart.js chart code.

Body schema by `type`:

| Type | Required body keys | Notes |
|------|--------------------|-------|
| `bar`, `line`, `pie`, `radar` | `labels`, `datasets` | Each dataset must provide `label` and `data`. |
| `scatter` | `datasets` | Each dataset must provide `label` and `points: [[x, y], ...]`. |
| `funnel` | `stages` | Each stage is `{label, value}`. |
| `sankey` | `nodes`, `links` | `links` encode quantified flows. |

- `invalid_syntax`: body keys do not match the selected `type`.
- `invalid_semantics`: chart is parseable but wrong for the content, or all data is placeholder-only decoration.
- `contract_conflict`: prior Chart.js/ECharts split. Resolved here as ECharts-only.
- `auto_downgrade_target`: `table` (preferred) or `callout` when the source has no chartable data.

### ECharts bar chart

    <div data-component="chart" data-type="bar" class="fade-in-up">
      <div id="chart-[unique-id]" style="height:300px"></div>
      <script>
        var chart = echarts.init(document.getElementById('chart-[unique-id]'));
        chart.setOption({
          title: { text: '[title]', textStyle: { color: '#94A3B8', fontSize: 13 } },
          grid: { top: 50, right: 30, bottom: 30, left: 60 },
          xAxis: { type: 'category', data: ['...'], axisLabel: { color: '#94A3B8' }, axisLine: { lineStyle: { color: '#334155' } } },
          yAxis: { type: 'value', axisLabel: { color: '#94A3B8' }, splitLine: { lineStyle: { color: '#334155' } } },
          series: [{ name: '[series]', type: 'bar', data: [...], barWidth: '50%', label: { show: true, position: 'top', color: '#E2E8F0', formatter: '{c}' } }],
          tooltip: { trigger: 'item', backgroundColor: '#1E293B', borderColor: '#334155', textStyle: { color: '#E2E8F0' } }
        });
      </script>
    </div>

**Grid bottom rule (MANDATORY):** If x-axis labels are rotated (`rotate > 0`), `grid.bottom` MUST be ≥ 60. Without rotation, `bottom: 30` is sufficient.

### ECharts radar chart

    <div data-component="chart" data-type="radar" class="fade-in-up">
      <div id="chart-[unique-id]" style="height:300px"></div>
      <script>
        var chart = echarts.init(document.getElementById('chart-[unique-id]'));
        chart.setOption({
          title: { text: '[title]', textStyle: { color: '#94A3B8', fontSize: 13 } },
          legend: { data: ['...'], bottom: 0, textStyle: { color: '#94A3B8', fontSize: 11 } },
          radar: { indicator: [{ name: '...' }], axisName: { color: '#E2E8F0', fontSize: 11 }, splitLine: { lineStyle: { color: '#334155' } }, splitArea: { areaStyle: { color: ['rgba(30,41,59,0.6)', 'rgba(15,23,42,0.8)'] } } },
          series: [{ type: 'radar', data: [{ value: [...], name: '...' }] }],
          tooltip: { trigger: 'item', backgroundColor: '#1E293B', borderColor: '#334155', textStyle: { color: '#E2E8F0' } }
        });
      </script>
    </div>

### ECharts line chart

    <div data-component="chart" data-type="line" class="fade-in-up">
      <div id="chart-[unique-id]" style="height:300px"></div>
      <script>
        var chart = echarts.init(document.getElementById('chart-[unique-id]'));
        chart.setOption({
          title: { text: '[title]', textStyle: { color: '#94A3B8', fontSize: 13 } },
          grid: { top: 50, right: 30, bottom: 50, left: 55 },
          xAxis: { type: 'category', data: ['...'], axisLabel: { color: '#94A3B8', interval: 0 }, axisLine: { lineStyle: { color: '#334155' } } },
          yAxis: { type: 'value', axisLabel: { color: '#94A3B8' }, splitLine: { lineStyle: { color: '#334155' } } },
          series: [{ name: '[series]', type: 'line', data: [...], smooth: true, lineStyle: { color: '#818CF8', width: 2 }, itemStyle: { color: '#818CF8' }, areaStyle: { color: 'rgba(129,140,248,0.1)' } }],
          legend: { data: ['[series]'], bottom: 0, textStyle: { color: '#94A3B8', fontSize: 11 } },
          tooltip: { trigger: 'item', backgroundColor: '#1E293B', borderColor: '#334155', textStyle: { color: '#E2E8F0' } }
        });
      </script>
    </div>

**Line data rule (MANDATORY):** If the IR provides a single `data` array, render as a **single series**. Do NOT split into multiple series with `null` values unless the IR explicitly defines separate series via `series:` YAML key.

### ECharts pie chart

    <div data-component="chart" data-type="pie" class="fade-in-up">
      <div id="chart-[unique-id]" style="height:300px"></div>
      <script>
        var chart = echarts.init(document.getElementById('chart-[unique-id]'));
        chart.setOption({
          title: { text: '[title]', textStyle: { color: '#94A3B8', fontSize: 13 } },
          series: [{ type: 'pie', radius: ['40%', '70%'], data: [{ name: 'A', value: 10 }, ...], label: { formatter: '{b}: {d}%' }, emphasis: { itemStyle: { shadowBlur: 10 } } }],
          tooltip: { trigger: 'item', backgroundColor: '#1E293B', borderColor: '#334155', textStyle: { color: '#E2E8F0' } }
        });
      </script>
    </div>

### ECharts sankey rendering (triggered by `type=sankey`)

IR input format:
```
:::chart type=sankey title=资金流向
nodes: [A, B, C, D]
links: [A->B:120, A->C:80, B->D:90, C->D:110]
:::
```

Parse `nodes` as `[{name: "A"}, ...]` and `links` as `[{source: "A", target: "B", value: 120}, ...]`.

**Label display rule (mandatory):** Node labels MUST show both name and value. Use ECharts `rich` text to give them distinct visual weight — name in muted small text, value in bold primary-color larger text. Never show name-only labels; a Sankey without numbers loses its core meaning.

    <div data-component="chart" data-type="sankey" class="fade-in-up">
      <div id="chart-[unique-id]" style="height:380px"></div>
      <script>
        // Pre-compute node totals for label display
        var nodeTotal = {};
        var links = [{ source: 'A', target: 'B', value: 120 }, ...];
        links.forEach(function(l) { nodeTotal[l.target] = (nodeTotal[l.target]||0) + l.value; });
        links.forEach(function(l) { if (!nodeTotal[l.source]) nodeTotal[l.source] = links.filter(function(x){return x.source===l.source;}).reduce(function(s,x){return s+x.value;},0); });

        var chart = echarts.init(document.getElementById('chart-[unique-id]'));
        chart.setOption({
          tooltip: {
            trigger: 'item', triggerOn: 'mousemove',
            formatter: function(p) {
              if (p.dataType === 'edge') {
                var pct = (p.data.value / (nodeTotal[p.data.source]||1) * 100).toFixed(1);
                return p.data.source + ' → ' + p.data.target + '<br/>' + p.data.value.toLocaleString() + ' (' + pct + '%)';
              }
              return p.name + '<br/>' + (nodeTotal[p.name]||0).toLocaleString();
            }
          },
          series: [{
            type: 'sankey',
            layout: 'none',
            emphasis: { focus: 'adjacency' },
            nodeWidth: 18,
            nodeGap: 14,
            lineStyle: { color: 'gradient', opacity: 0.4 },
            label: {
              fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif',
              formatter: function(p) {
                var v = nodeTotal[p.name] || 0;
                return '{name|' + p.name + '}\n{val|' + v.toLocaleString() + '}';
              },
              rich: {
                name: { fontSize: 12, color: '#555', fontWeight: 'normal', lineHeight: 18 },
                val:  { fontSize: 15, color: '#0B6E6E', fontWeight: '700', lineHeight: 20 }
              }
            },
            edgeLabel: {
              show: true, fontSize: 11, color: '#555',
              formatter: function(p) { return p.data.value.toLocaleString(); }
            },
            data: [{ name: 'A' }, { name: 'B' }, ...],
            links: links
          }]
        });
      </script>
    </div>

**val color rule:** Use theme's `--primary` color for the value text (default `#0B6E6E`). For dark themes substitute the theme accent color.

Use cases: budget flows, conversion funnels (multi-step), resource allocation, supply chain. Height default 380px; increase to 500px for 8+ nodes.

## :::table

Body is a Markdown table. Convert to HTML. If `caption` param is provided, emit `<caption>[caption text]</caption>` as the first child of `<table>`.

    <div data-component="table" class="table-wrapper fade-in-up">
      <table class="report-table">
        <caption>Table title if provided</caption>
        <thead><tr><th>Col1</th>...</tr></thead>
        <tbody><tr><td>Val</td>...</tr></tbody>
      </table>
    </div>

## :::list

Body is a Markdown list (ordered `1. Item` or unordered `- Item`). `style=ordered` → `<ol>`, default → `<ul>`.

**Single-line format (compatibility only):** `:::list style=ordered 1. A 2. B :::` — split on `N. ` or `- ` separators to recover individual items; render the same HTML below. Do not generate this as the primary syntax.

    <div data-component="list" class="report-list">
      <ul class="styled-list">  <!-- or <ol> if style=ordered -->
        <li>Item</li>
        <li>Item with sub-items
          <ul><li>Sub-item</li></ul>
        </li>
      </ul>
    </div>

If an item has indented sub-items (2-space or 4-space indent), render them as nested `<ul>` or `<ol>` inside the parent `<li>`.

**Do NOT output `:::list`, params, or `:::` closing marker as text — they are never user-visible content.**

## :::image

    <figure data-component="image" class="report-image report-image--[layout]">
      <img src="[src]" alt="[alt]" loading="lazy">
      <figcaption>[caption]</figcaption>
    </figure>

layout=left: float left, max-width 40%, text wraps right.
layout=right: float right, max-width 40%, text wraps left.
layout=full (default): full width, centered.

## :::timeline

Each item: `- Date: Description`

Whitelist for `Date`:

- `YYYY-MM-DD`
- `YYYY-MM`
- `YYYY`
- `Q[1-4] YYYY`
- `Day N`
- `Week N`
- `Month N`

**Temporal content rule (MANDATORY):** The `:::timeline` component is ONLY for content with actual dates, timestamps, or sequential time markers (e.g. `2024-07`, `Q1 2025`, `Day 1`, `Week 3`). It represents chronological progression — items must have a clear before/after relationship.

**Prohibited:** Do NOT use `:::timeline` for parallel, non-sequential items like principles, rules, features, or categories (e.g. "真诚服务", "安全可信", "专业高效" — these are并列关系, not chronological). For parallel items, use `:::list` or prose with `:::callout` instead.

**When in doubt:** If the items could be reordered without changing meaning, they are NOT timeline content.

- `invalid_syntax`: the item is not in `- Date: Description` form.
- `invalid_semantics`: the item is syntactically valid but `Date` is not actually chronological.
- `contract_conflict`: none.
- `auto_downgrade_target`: `list`.

    <div data-component="timeline" class="timeline fade-in-up">
      <div class="timeline-item">
        <div class="timeline-date">2024-07</div>
        <div class="timeline-dot"></div>
        <div class="timeline-content">Project kickoff</div>
      </div>
    </div>

## :::diagram

Generate inline SVG. All SVGs must be self-contained (no external refs). Wrap in:

    <div data-component="diagram" data-type="[type]" class="diagram-wrapper fade-in-up">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 [w] [h]">
        <!-- generated SVG -->
      </svg>
    </div>

**viewBox height rule:** Always add 30px of bottom padding beyond the last drawn element's bottom edge. For example, if the lowest element ends at y=346, set viewBox height to 376. This prevents content clipping.

Schema by `type`:

- `sequence`:
  ```yaml
  actors: [A, B, C]
  steps:
    - from: A
      to: B
      msg: 请求
  ```
- `flowchart`:
  ```yaml
  nodes:
    - id: start
      kind: oval
      label: 开始
  edges:
    - from: start
      to: step1
      label: 可选
  ```
- `tree`:
  ```yaml
  root: 平台
  children:
    - name: 数据层
      children: []
  ```
- `mindmap`:
  ```yaml
  center: 协同能力
  branches:
    - name: 流程
      items: [采集, 编排]
  ```

- `invalid_syntax`: body is missing the required keys for the chosen `type`.
- `invalid_semantics`: the structure parses but the chosen diagram type misrepresents the content.
- `contract_conflict`: examples previously acted as hidden spec. The schema above is now canonical.
- `auto_downgrade_target`: `callout`.

**type=sequence:** Draw vertical lifelines for each actor, horizontal arrows for each step. Actors as columns at top with labels, steps numbered on left, arrows with labels between lifelines.
Sizing: width = 180 × (actor count), height = 80 + 50 × (step count).

**type=flowchart:** Draw nodes as shapes (circle=oval, diamond=rhombus, rect=rectangle). Connect with directed arrows. Use edge labels where provided.
Sizing: width = 600, height = 120 × (node count).

**type=tree:** Top-down tree with root at top, children below, connected by lines.
Sizing: width = 200 × (max leaf count at any level), height = 120 × (depth).

**type=mindmap:** Radial layout, center node in middle, branches radiating out with items as leaf nodes.
Sizing: width = 700, height = 500.

## :::code

    <div data-component="code" class="code-wrapper">
      <div class="code-title">[title if provided]</div>
      <pre><code class="language-[lang]">[HTML-escaped code content]</code></pre>
    </div>

Add `<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11/styles/github.min.css">` and `<script src="https://cdn.jsdelivr.net/npm/highlight.js@11/lib/highlight.min.js"></script>` + `<script>hljs.highlightAll();</script>` in head (or inline the full highlight.js CSS and JS if `--bundle` mode).

For dark-tech theme use `github-dark.min.css` instead of `github.min.css`.

## :::callout

    <div data-component="callout" class="callout callout--[type] fade-in-up">
      <span class="callout-icon">[icon or default]</span>
      <div class="callout-body">[content]</div>
    </div>

Default icons: note→ℹ, tip→💡, warning→⚠, danger→🚫

`icon` overrides must be normalized before rendering:

- Allowed whitelist: `ℹ`, `💡`, `⚠`, `🚫`, `✓`, `!`, `→`
- Strip U+FE0F if present.
- If the icon is still outside the whitelist after normalization, ignore it and fall back to the default icon for that callout type.

## Custom Blocks

For each `:::tag-name` matching a key in frontmatter `custom_blocks`:
1. Get the HTML template string from `custom_blocks.[tag-name]`
2. Parse block body as YAML to get field values
3. Replace `{{field}}` with the value
4. Replace `{{content}}` with any non-YAML plain text lines in the block
5. For `{{#each list}}...{{this}}...{{/each}}`, iterate the array and repeat the inner template
6. Wrap result in: `<div data-component="custom" data-tag="[tag-name]">[expanded HTML]</div>`
