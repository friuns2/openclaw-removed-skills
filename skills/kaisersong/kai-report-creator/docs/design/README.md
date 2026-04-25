# kai-report-creator Design Docs

Last updated: 2026-04-24  
Scope: HTML report generation — IR format, rendering engine, component system, theme system

This directory is the canonical design set for `kai-report-creator`, covering:

- IR format (.report.md) — YAML frontmatter + Markdown prose + component blocks
- HTML rendering engine — zero-dependency single-file output
- Component system — KPI cards, charts, timelines, diagrams, tables
- Theme system — 7 built-in themes + custom themes
- Review and export system

Use these documents in the following order:

1. **Core Architecture**
   - [2026-04-24-report-creator-core-architecture-design.md](./2026-04-24-report-creator-core-architecture-design.md)
   - Read this first when changing IR format, rendering engine,
     or component system.

2. **Component System Design**
   - [2026-04-24-report-creator-component-system-design.md](./2026-04-24-report-creator-component-system-design.md)
   - Read this first when adding a new component type, changing
     component rendering, or modifying data binding.

3. **Theme System Design**
   - [2026-04-24-report-creator-theme-system-design.md](./2026-04-24-report-creator-theme-system-design.md)
   - Read this first when changing theme colors, custom themes,
     or theme CSS overrides.

4. **Test Matrix**
   - [2026-04-24-report-creator-test-matrix.md](./2026-04-24-report-creator-test-matrix.md)
   - Use this when deciding which regression layers must be updated.

5. **Change Checklist**
   - [2026-04-24-report-creator-change-checklist.md](./2026-04-24-report-creator-change-checklist.md)
   - Use this before merging any rendering-affecting change.

## What belongs here

This design set covers:

- IR format (.report.md) — YAML frontmatter, Markdown prose, component blocks
- Command routing — --plan, --generate, --review, --themes, --from, --bundle, --export-image
- HTML rendering engine — zero-dependency single-file output
- Component system — KPI cards, charts, timelines, diagrams, tables, images
- Theme system — 7 built-in themes + custom themes
- Mobile responsive design
- Machine-readable structure (summary JSON, section annotations, component raw data)
- Review system — one-pass automatic refinement
- Export system — image export via Playwright

## What does not belong here

This design set does not define:

- slide deck generation (handled by `kai-slide-creator`)
- HTML-to-PPTX export (handled by `kai-export-ppt-lite` or `kai-html-export`)
- prompt engineering for content writing
- data source connection (APIs, databases)

## Operational rule

If a rendering bug changes the user-visible report output, or a component
bug changes the data display contract, update this directory in the same
change instead of writing an implementation-only fix.

## Critical design constraints

These constraints are load-bearing and must never be violated:

1. **Zero dependencies for generated HTML**
   - All CSS/JS inline or from CDN
   - Single HTML file works when opened directly in browser

2. **Never fabricate data**
   - Use `[INSERT VALUE]` placeholder for missing data
   - User provides data, AI provides structure

3. **Machine-readable output**
   - 3-layer structure: summary JSON → section annotations → component raw data
   - Downstream AI agents must be able to read reports efficiently

4. **Mobile responsive**
   - Reports must render correctly on both desktop and mobile
