# kai-report-creator Theme System Design

Date: 2026-04-24  
Project: `kai-report-creator`  
Status: Active reference design  
Scope: 7 built-in themes, custom themes, CSS variable system, theme overrides

---

## 1. Why This Document Exists

report-creator has **7 built-in themes** plus support for custom themes.
Theme selection affects all visual aspects of the generated report.

That means theme bugs are **not cosmetic issues**. They are failures at
the boundary between:

- theme CSS variables and component rendering
- theme overrides and base theme values
- custom theme loading and validation
- content-type → theme routing

This document is the reference architecture for those boundaries.

---

## 2. Built-in Themes

| Theme | Description | Primary Use |
|-------|-------------|-------------|
| `corporate-blue` | Business & commercial | Sales, revenue, KPI reports |
| `minimal` | Clean, academic | Research, whitepapers |
| `dark-tech` | Technical documentation | API docs, system architecture |
| `dark-board` | Project dashboards | Status boards, progress tracking |
| `data-story` | Data narrative | Annual reports, growth stories |
| `newspaper` | Editorial & news | Industry trends, observations |
| `regular-lumen` | Periodic reports (warm tone, poster-style) | Weekly, daily, monthly reports |

---

## 3. Theme Structure

### 3.1 Theme Directory

Each theme has its own directory under `themes/`:

```
themes/
├── corporate-blue/
│   ├── theme.css       # Theme CSS variables and component styles
│   └── preview.html    # Theme preview
├── minimal/
│   ├── theme.css
│   └── preview.html
└── ...
```

### 3.2 CSS Variables

Each theme defines CSS variables:

```css
:root {
    --primary-color: #XXXXXX;
    --secondary-color: #XXXXXX;
    --accent-color: #XXXXXX;
    --text-color: #XXXXXX;
    --text-muted: #XXXXXX;
    --bg-color: #XXXXXX;
    --card-bg: #XXXXXX;
    --border-color: #XXXXXX;
    --chart-colors: #XXX, #XXX, #XXX, #XXX, #XXX;
    --font-family: '...';
    --heading-font: '...';
}
```

### 3.3 Component Styles

Each theme defines styles for:

- KPI cards
- Charts (ECharts theme)
- Tables
- Timelines
- Diagrams
- Callouts
- Code blocks

---

## 4. Theme Routing

### 4.1 Priority Order

| Priority | Keywords | Theme |
|----------|----------|-------|
| 1st | 周报、日报、月报、工作汇报 | `regular-lumen` |
| 2nd | 季报、销售、业绩、营收、KPI | `corporate-blue` |
| 3rd | 研究、调研、学术、白皮书 | `minimal` |
| 4th | 技术、架构、API、系统、性能 | `dark-tech` |
| 5th | 新闻、行业、趋势、观察 | `newspaper` |
| 6th | 年度、故事、增长、复盘 | `data-story` |
| 7th | 看板、board、dashboard | `dark-board` |
| 8th | 项目、进展、状态、任务 (fallback) | `corporate-blue` |

### 4.2 Override Priority

1. `--theme` CLI flag (highest)
2. `theme:` in frontmatter
3. Content-type routing (automatic)
4. Default: `corporate-blue`

---

## 5. Theme Overrides

### 5.1 Frontmatter Overrides

```yaml
theme_overrides:
    primary_color: "#E63946"
    font_family: "PingFang SC"
    logo: "./logo.png"
```

### 5.2 Applied Variables

| Override | CSS Variable |
|----------|-------------|
| `primary_color` | `--primary-color` |
| `secondary_color` | `--secondary-color` |
| `accent_color` | `--accent-color` |
| `text_color` | `--text-color` |
| `bg_color` | `--bg-color` |
| `card_bg` | `--card-bg` |
| `font_family` | `--font-family` |
| `logo` | Logo image URL |

### 5.3 Invariants

- Overrides apply on top of base theme
- Unspecified variables use base theme values
- Invalid override values fall back to base theme

---

## 6. Custom Themes

### 6.1 Structure

Custom themes are directories under `themes/`:

```
themes/
└── my-brand/
    ├── theme.css
    └── preview.html
```

### 6.2 Usage

```bash
/report --theme my-brand "My Report"
```

### 6.3 Requirements

Custom theme must define all required CSS variables:

- `--primary-color`
- `--secondary-color`
- `--accent-color`
- `--text-color`
- `--text-muted`
- `--bg-color`
- `--card-bg`
- `--border-color`
- `--chart-colors`
- `--font-family`
- `--heading-font`

---

## 7. Content-Tone Color Calibration

Based on topic keywords, suggest `theme_overrides.primary_color`:

| Content Tone | Color | Description |
|-------------|-------|-------------|
| 思辨/研究 | `#7C6853` | Warm brown |
| 商业/销售 | `#1E40AF` | Corporate blue |
| 技术/工程 | `#059669` | Technical green |
| 创意/品牌 | `#7C3AED` | Creative purple |
| 新闻/媒体 | `#DC2626` | Editorial red |

---

## 8. Anti-Patterns

Do not do these:

1. **Missing CSS variables in custom theme**
   - All required variables must be defined
   - Missing variables = fallback to base theme

2. **Overriding chart colors individually**
   - Use `--chart-colors` for consistent palette
   - Don't override individual chart colors

3. **Ignoring theme routing priority**
   - First match wins in priority order
   - Don't skip priority levels

4. **Using invalid override values**
   - Invalid values fall back to base theme
   - Validate override values

---

## 9. Operational Rule

For theme bugs:

> A fix is not complete until the theme renders correctly AND overrides apply correctly on top of the base theme.