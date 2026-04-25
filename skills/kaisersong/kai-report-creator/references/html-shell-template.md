# HTML Shell Template

When generating the final HTML report, produce a complete self-contained HTML file using this structure. Replace all `[...]` placeholders with actual content.

    <!DOCTYPE html>
    <!-- kai-report-creator v[version] -->
    <html lang="[lang]" data-template="kai-report-creator" data-version="[version]" data-theme="[theme]">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta name="generator" content="kai-report-creator [theme-display] v[version]">
      <meta name="ir-hash" content="sha256:[ir-hash]">
      <title>[title]</title>

      <!-- CDN libraries (add only what's needed; omit if --bundle, inline instead) -->
      <!-- If any :::chart blocks present: -->
      <!-- <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script> -->
      <!-- If any :::code blocks present: -->
      <!-- <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11/styles/github.min.css"> -->
      <!-- (use github-dark.min.css for dark-tech theme) -->
      <!-- <script src="https://cdn.jsdelivr.net/npm/highlight.js@11/lib/highlight.min.js"></script> -->
      <!-- <script>document.addEventListener('DOMContentLoaded', () => hljs.highlightAll());</script> -->

      <style>
        /* [Paste the selected theme CSS here, e.g., the corporate-blue block] */

        /* Shared Component CSS — fixed verbatim; do NOT regenerate or summarize */
        *, *::before, *::after { box-sizing: border-box; }
        .report-wrapper { max-width: 920px; margin: 0 auto; padding: 2rem 1.5rem; }
        @media (min-width: 1100px) { .report-wrapper { padding: 2.5rem 3rem; } }
        .report-meta { color: var(--text-muted); font-size: .9rem; margin-top: -.5rem; margin-bottom: 1.5rem; }

        /* Watermark footer */
        .report-footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--report-border, var(--border)); text-align: center; color: var(--text-muted); font-size: .7rem; opacity: .5; letter-spacing: .03em; }
        @media print { .report-footer { display: none; } }
        @media (max-width: 768px) { .report-footer { margin-top: 1.5rem; } }

        /* KPI */
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: .75rem; margin: 1.1rem 0; }
        .kpi-card { background: var(--report-surface, var(--surface)); border: 1px solid var(--report-border, var(--border)); border-radius: var(--radius); padding: .9rem; text-align: center; border-top: 2px solid var(--report-structure, var(--primary)); display: flex; flex-direction: column; align-items: center; }
        .kpi-label { font-size: .78rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: .4rem; }
        .kpi-value { font-size: 2rem; font-weight: 800; color: var(--report-text, var(--text)); line-height: 1.2; font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; font-variant-numeric: lining-nums tabular-nums; flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; word-break: break-word; overflow-wrap: break-word; }
        .kpi-value .kpi-suffix { font-size: .75em; font-weight: 600; line-height: 1.3; }
        .kpi-trend { font-size: .85rem; margin-top: .3rem; }
        .kpi-trend--up { color: var(--success); } .kpi-trend--down { color: var(--danger); } .kpi-trend--neutral { color: var(--text-muted); }
        .kpi-card[data-accent] { border-top-color: var(--report-structure, var(--primary)); }
        .kpi-card[data-accent] .kpi-value { color: var(--report-text, var(--text)); }
        .kpi-delta { display: inline-block; padding: .15rem .48rem; border-radius: 999px; font-size: .74rem; font-weight: 700; margin-top: .28rem; }
        .kpi-delta--up   { background: var(--report-delta-up-bg, #E7F1EA); color: var(--report-delta-up-text, var(--success)); }
        .kpi-delta--down { background: var(--report-delta-down-bg, #F6E8E6); color: var(--report-delta-down-text, var(--danger)); }
        .kpi-delta--info { background: var(--report-delta-flat-bg, #EEE7DE); color: var(--report-delta-flat-text, var(--text-muted)); }
        .badge { display: inline-flex; align-items: center; padding: .18rem .55rem; border-radius: 999px; font-size: .75rem; font-weight: 600; letter-spacing: .01em; white-space: nowrap; border: 1px solid var(--report-chip-border, var(--report-border, var(--border))); }
        .badge--blue   { background: var(--report-chip-bg, var(--surface)); color: var(--report-chip-text, var(--text-muted)); }
        .badge--green  { background: var(--report-chip-bg, var(--surface)); color: var(--report-chip-text, var(--text-muted)); }
        .badge--purple { background: var(--report-chip-bg, var(--surface)); color: var(--report-chip-text, var(--text-muted)); }
        .badge--orange { background: var(--report-chip-bg, var(--surface)); color: var(--report-chip-text, var(--text-muted)); }
        .badge--red    { background: var(--report-chip-bg, var(--surface)); color: var(--report-chip-text, var(--text-muted)); }
        .badge--gray   { background: var(--report-chip-bg, var(--surface)); color: var(--report-chip-text, var(--text-muted)); }
        .badge--teal   { background: var(--report-chip-bg, var(--surface)); color: var(--report-chip-text, var(--text-muted)); }
        .badge--done   { background: var(--report-chip-bg, var(--surface)); color: var(--report-chip-text, var(--text-muted)); }
        .badge--wip    { background: var(--report-chip-bg, var(--surface)); color: var(--report-chip-text, var(--text-muted)); }
        .badge--todo   { background: var(--report-chip-bg, var(--surface)); color: var(--report-chip-text, var(--text-muted)); }
        .badge--ok     { background: var(--report-chip-bg, var(--surface)); color: var(--report-chip-text, var(--text-muted)); }
        .badge--warn   { background: var(--report-delta-up-bg, #E7F1EA); color: var(--report-delta-up-text, var(--success)); border-color: transparent; }
        .badge--err    { background: var(--report-delta-down-bg, #F6E8E6); color: var(--report-delta-down-text, var(--danger)); border-color: transparent; }
        [data-report-mode="comparison"] .badge--entity-a { background: rgba(47, 107, 80, .12); color: var(--entity-a, #2F6B50); border-color: rgba(47, 107, 80, .18); }
        [data-report-mode="comparison"] .badge--entity-b { background: rgba(111, 106, 124, .12); color: var(--entity-b, #6F6A7C); border-color: rgba(111, 106, 124, .18); }
        [data-report-mode="comparison"] .badge--entity-c { background: rgba(92, 118, 138, .12); color: var(--entity-c, #5C768A); border-color: rgba(92, 118, 138, .18); }

        /* Tables */
        .table-wrapper { overflow-x: auto; margin: 1.1rem 0; }
        .report-table { width: 100%; border-collapse: collapse; font-size: .9rem; }
        .report-table th { background: var(--report-surface, var(--surface)); border-bottom: 2px solid var(--report-structure, var(--primary)); padding: .7rem 1rem; text-align: left; font-weight: 600; }
        .report-table td { padding: .6rem 1rem; border-bottom: 1px solid var(--border); }
        .report-table tr:hover td { background: var(--report-surface, var(--surface)); }

        /* Callout */
        .callout { display: flex; gap: .75rem; padding: .9rem 1.1rem; border-radius: var(--radius); margin: .75rem 0; border-left: 4px solid; align-items: flex-start; }
        .callout--note { background: #EFF6FF; border-color: #3B82F6; }
        .callout--tip { background: #F0FDF4; border-color: #22C55E; }
        .callout--warning { background: #FFFBEB; border-color: #F59E0B; }
        .callout--danger { background: #FEF2F2; border-color: #EF4444; }
        .callout-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: .05rem; }
        .callout-body { flex: 1; min-width: 0; line-height: 1.6; font-size: .93rem; color: #1F2937; }
        /* Callout icon color — ensure contrast on light backgrounds regardless of theme */
        .callout--note .callout-icon { color: #3B82F6; }
        .callout--tip .callout-icon { color: #22C55E; }
        .callout--warning .callout-icon { color: #F59E0B; }
        .callout--danger .callout-icon { color: #EF4444; }

        /* Semantic highlight extraction — from design-quality.md §6 */
        .highlight-sentence { font-size: 1.15rem; font-weight: 700; color: var(--primary); border-left: 3px solid var(--primary); padding-left: 1rem; margin: 1.5rem 0; line-height: 1.5; }
        .lead-block {
          margin: 1.1rem 0 1rem;
          padding: 1rem 1.15rem;
          border-left: 4px solid var(--primary);
          border-radius: 16px;
          background: rgba(255,255,255,.72);
          font-size: 1.02rem;
          line-height: 1.72;
          max-width: 60rem;
        }
        .section-quote {
          margin: 1rem 0;
          padding: 1rem 1.15rem;
          border-radius: 18px;
          background: linear-gradient(135deg, rgba(255,255,255,.78), rgba(0,0,0,.03));
          border: 1px solid var(--border);
          font-family: var(--font-display);
          font-size: 1.18rem;
          line-height: 1.58;
        }
        .action-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: .8rem;
          margin: 1rem 0;
        }
        .action-card {
          padding: 1rem;
          border-radius: 18px;
          border: 1px solid var(--border);
          background: rgba(255,255,255,.78);
        }
        .action-card strong {
          display: block;
          margin-bottom: .45rem;
          color: var(--primary);
        }
        .action-card p {
          margin: 0;
          font-size: .92rem;
          line-height: 1.62;
          color: var(--text-muted);
        }

        /* Timeline */
        .timeline { position: relative; padding-left: 2rem; margin: 1.1rem 0; }
        .timeline::before { content: ''; position: absolute; left: .45rem; top: 0; bottom: 0; width: 2px; background: var(--border); }
        .timeline-item { position: relative; margin-bottom: 1rem; }
        .timeline-dot { position: absolute; left: -1.65rem; top: .3rem; width: 12px; height: 12px; border-radius: 50%; background: var(--report-structure, var(--primary)); border: 2px solid var(--report-bg, var(--bg)); }
        .timeline-date { font-size: .78rem; color: var(--text-muted); margin-bottom: .15rem; font-weight: 600; }
        .timeline-content { color: var(--text); line-height: 1.6; }

        /* Image */
        .report-image { margin: 1.1rem 0; } .report-image img { max-width: 100%; border-radius: var(--radius); }
        .report-image figcaption { font-size: .82rem; color: var(--text-muted); text-align: center; margin-top: .4rem; }
        .report-image--left { float: left; max-width: 40%; margin-right: 1.5rem; margin-bottom: .5rem; }
        .report-image--right { float: right; max-width: 40%; margin-left: 1.5rem; margin-bottom: .5rem; }
        .report-image--full { width: 100%; display: block; }
        .clearfix::after { content: ''; display: table; clear: both; }

        /* Code */
        .code-wrapper { margin: 1.1rem 0; border-radius: var(--radius); overflow: hidden; border: 1px solid var(--border); }
        .code-title { background: var(--surface); padding: .35rem 1rem; font-size: .78rem; color: var(--text-muted); font-family: var(--font-mono); border-bottom: 1px solid var(--border); }
        .code-wrapper pre { margin: 0; overflow-x: auto; }

        /* List */
        .report-list { margin: .75rem 0; }
        .styled-list { padding-left: 1.5rem; line-height: 1.8; }
        .styled-list li { margin-bottom: .25rem; }

        /* Diagram */
        .diagram-wrapper { margin: 1.1rem 0; text-align: center; }
        .diagram-wrapper svg { max-width: 100%; height: auto; display: block; margin: 0 auto; }

        /* Chart */
        [data-component="chart"] { margin: 1.1rem 0; }

        /* Animations — all easing uses cubic-bezier(0.22,1,0.36,1) (ease-out-expo). Never use bounce (overshoot >1) or elastic (spring oscillation) easing — they read as dated and tacky. */
        .fade-in-up { opacity: 0; transform: translateY(18px); transition: opacity .5s cubic-bezier(0.22,1,0.36,1), transform .5s cubic-bezier(0.22,1,0.36,1); }
        .fade-in-up.visible { opacity: 1; transform: translateY(0); }
        .print-exporting .fade-in-up { opacity: 1 !important; transform: none !important; transition: none !important; }
        body.no-animations .fade-in-up { opacity: 1; transform: none; transition: none; }
        .kpi-grid.stagger-ready .kpi-card { opacity: 0; transform: translateY(20px) scale(0.95); transition: opacity .45s cubic-bezier(0.34,1.56,0.64,1), transform .45s cubic-bezier(0.34,1.56,0.64,1); }
        .kpi-grid.stagger-ready .kpi-card.visible { opacity: 1; transform: none; }
        .print-exporting .kpi-grid .kpi-card { opacity: 1 !important; transform: none !important; transition: none !important; }
        .timeline.stagger-ready .timeline-item { opacity: 0; transform: translateX(-12px); transition: opacity .4s cubic-bezier(0.22,1,0.36,1), transform .4s cubic-bezier(0.22,1,0.36,1); }
        .timeline.stagger-ready .timeline-item.visible { opacity: 1; transform: none; }
        .print-exporting .timeline .timeline-item { opacity: 1 !important; transform: none !important; transition: none !important; }
        body.no-animations .kpi-grid .kpi-card,
        body.no-animations .timeline .timeline-item { opacity: 1 !important; transform: none !important; transition: none !important; }

        /* Edit mode */
        .edit-hotzone { position: fixed; bottom: 0; left: 0; width: 80px; height: 80px; z-index: 10000; cursor: pointer; }
        .edit-toggle { position: fixed; bottom: 16px; left: 16px; background: var(--primary); color: #fff; border: none; border-radius: 6px; padding: .45rem .9rem; font-size: .82rem; cursor: pointer; font-weight: 600; opacity: 0; pointer-events: none; transition: opacity .25s ease, background .2s ease; z-index: 10001; box-shadow: 0 2px 8px rgba(0,0,0,.25); letter-spacing: .02em; }
        .edit-toggle.show { opacity: 1; pointer-events: auto; }
        .edit-toggle.active { opacity: 1; pointer-events: auto; background: var(--success); }
        body.edit-mode [contenteditable] { outline: 1px dashed var(--border); border-radius: 2px; cursor: text; }
        body.edit-mode [contenteditable]:hover { outline-color: var(--primary); }
        body.edit-mode [contenteditable]:focus { outline: 2px solid var(--primary); }

        /* Export */
        .export-btn { position: fixed; bottom: 16px; right: 16px; z-index: 10001; background: var(--primary); color: #fff; border: none; border-radius: 6px; padding: .45rem .9rem; font-size: .82rem; cursor: pointer; font-weight: 600; box-shadow: 0 2px 8px rgba(0,0,0,.2); font-family: var(--font-sans, system-ui); letter-spacing: .02em; }
        .export-menu { position: fixed; bottom: 52px; right: 16px; z-index: 10001; background: var(--surface, #fff); border: 1px solid var(--border, #e5e7eb); border-radius: 6px; overflow: hidden; display: none; box-shadow: 0 4px 16px rgba(0,0,0,.15); min-width: 148px; }
        .export-menu.open { display: block; }
        .export-item { display: block; width: 100%; padding: .55rem 1rem; font-size: .84rem; background: none; border: none; cursor: pointer; text-align: left; color: var(--text, #111); font-family: var(--font-sans, system-ui); white-space: nowrap; border-bottom: 1px solid var(--border, #e5e7eb); }
        .export-item:last-child { border-bottom: none; }
        .export-item:hover { background: var(--primary-light, #e3edff); }
        @page { size: A4; margin: 1.5cm; }
        @media print {
          * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
          html, body {
            background: var(--print-bg-color, var(--report-bg, var(--bg, #ffffff))) !important;
            color: var(--report-text, var(--text, #111111)) !important;
          }
          .toc-toggle, .toc-sidebar, .edit-hotzone, .edit-toggle, .export-btn, .export-menu { display: none !important; }
          h2 { break-after: avoid; }
          .kpi-grid, .kpi-card, .callout, .timeline, .timeline-item,
          .table-wrapper, [data-component="chart"], .diagram-wrapper { break-inside: avoid; }
          .chart-container { height: 200px !important; }
          canvas { max-height: 200px !important; width: 100% !important; }
          img { max-height: 260px !important; width: auto !important; object-fit: contain; }
          .fade-in-up { opacity: 1 !important; transform: translateY(0) !important; }
          .kpi-grid .kpi-card, .timeline .timeline-item { opacity: 1 !important; transform: none !important; }
        }

        /* Floating TOC overlay — default collapsed on all screen sizes */
        .toc-sidebar {
          position: fixed; top: 0; left: 0; width: 240px; height: 100vh;
          overflow-y: auto; padding: 3rem 1rem 1.5rem; background: var(--surface);
          border-right: 1px solid var(--border); font-size: .83rem; z-index: 100;
          transform: translateX(-100%); transition: transform .28s ease;
        }
        .toc-sidebar.open {
          transform: translateX(0); box-shadow: 4px 0 24px rgba(0,0,0,.18);
        }
        .toc-sidebar h4 {
          font-size: .72rem; text-transform: uppercase; letter-spacing: .08em;
          color: var(--text-muted); margin: 0 0 .75rem; font-weight: 600;
        }
        .toc-sidebar a {
          display: block; color: var(--text-muted); text-decoration: none;
          padding: .28rem .5rem; border-radius: 4px; margin-bottom: 1px; transition: all .18s;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .toc-sidebar a:hover, .toc-sidebar a.active { color: var(--primary); background: var(--primary-light); }
        .toc-sidebar a.toc-h3 { padding-left: 1.1rem; font-size: .78rem; opacity: .85; }
        .main-with-toc { margin-left: 0; }
        .toc-toggle {
          position: fixed; top: .75rem; left: .75rem; z-index: 200;
          background: var(--primary); color: #fff; border: none; border-radius: 6px;
          padding: .45rem .7rem; cursor: pointer; font-size: 1rem; line-height: 1;
          box-shadow: 0 2px 8px rgba(0,0,0,.2);
        }
        .toc-toggle.locked { box-shadow: 0 0 0 2px #fff, 0 2px 8px rgba(0,0,0,.2); }
        @media (max-width: 768px) {
          .report-wrapper { padding: 1.5rem 1rem; }
        }
        /* Responsive rule: never hide critical functionality (export, edit toggle, KPI values, charts) on mobile.
           Only decorative/progressive-enhancement elements (animations, TOC overlay) may be suppressed. */
        body.no-toc .toc-sidebar, body.no-toc .toc-toggle { display: none; }
        body.no-toc .main-with-toc { margin-left: 0; }

        /* Summary card button — bottom-aligned with h1 */
        .title-row { display: flex; align-items: flex-end; gap: 1rem; }
        .title-row h1 { flex: 1; }
        .card-mode-btn {
          flex-shrink: 0; margin-bottom: .6rem;
          background: var(--surface); border: 1px solid var(--border); border-radius: 4px;
          padding: .28rem .65rem; font-size: .76rem; font-weight: 600;
          color: var(--text-muted); cursor: pointer; transition: all .15s;
          font-family: var(--font-sans, system-ui); white-space: nowrap;
        }
        .card-mode-btn:hover { background: var(--primary-light); color: var(--primary); border-color: var(--primary); }

        /* Summary card overlay */
        .sc-overlay {
          display: none; position: fixed; inset: 0; z-index: 500;
          background: rgba(0,0,0,.52); backdrop-filter: blur(6px);
          align-items: center; justify-content: center; padding: 2rem;
        }
        body.card-mode .sc-overlay { display: flex; }
        body.card-mode { overflow: hidden; height: 100vh; }
        html:has(body.card-mode) { overflow: hidden; height: 100vh; }
        body.card-mode .main-with-toc,
        body.card-mode .toc-toggle,
        body.card-mode .toc-sidebar { visibility: hidden; }
        body.card-mode .sc-overlay { visibility: visible; }

        /* Card — editorial two-column, high density */
        .sc-card {
          position: relative; display: flex; width: min(900px, 92vw);
          background: #fff; border: 1px solid rgba(0,0,0,.12);
          border-radius: 8px; overflow: hidden;
          box-shadow: 0 24px 72px rgba(0,0,0,.3);
        }
        /* Left panel */
        .sc-left {
          flex: 0 0 46%; display: flex; flex-direction: column;
          padding: 1.8rem 2rem 1.6rem;
          background: var(--primary); color: #fff;
        }
        .sc-label {
          font-size: .55rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase;
          opacity: .5; margin-bottom: .55rem; display: flex; align-items: center; gap: .45rem;
        }
        .sc-label::before { content: ''; display: inline-block; width: 20px; height: 1px; background: currentColor; }
        /* poster title should dominate the card */
        .sc-title-main {
          font-size: clamp(3.45rem, 6.9vw, 5.25rem);
          font-weight: 900;
          line-height: .92;
          letter-spacing: -.05em;
          margin-bottom: .35rem;
          word-break: break-word;
        }
        .sc-title-sub {
          font-size: 1.08rem;
          line-height: 1.5;
          color: rgba(255,255,255,.88);
          margin-bottom: .9rem;
          max-width: 82%;
        }
        .sc-note {
          margin-top: auto;
          padding-top: 1.4rem;
          width: 72%;
          font-size: .84rem;
          line-height: 1.68;
          opacity: .9;
        }
        /* Right panel */
        .sc-right {
          flex: 1; display: flex; flex-direction: column;
          padding: 1.8rem 1.8rem 1.8rem;
          border-left: 1px solid var(--border);
        }
        /* KPI rows — compact 2-col, no card boxes */
        .sc-kpi-rows { display: grid; grid-template-columns: 1fr 1fr; gap: 0 .6rem; margin-bottom: .5rem; }
        .sc-kpi-row { padding: .32rem 0; border-bottom: 1px solid var(--border); }
        .sc-kpi-row-l { font-size: .56rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: .06em; }
        .sc-kpi-row-v { font-size: 1.15rem; font-weight: 800; color: var(--primary); line-height: 1.15; }
        .sc-kpi-row-t { font-size: .6rem; color: var(--success, #057A55); font-weight: 600; }
        /* Section summaries — divider rows */
        .sc-summaries { flex: 1; display: flex; flex-direction: column; }
        .sc-sum-item { padding: .35rem 0; border-bottom: 1px solid var(--border); }
        .sc-sum-item:last-child { border-bottom: none; }
        .sc-sum-name { font-size: .56rem; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: .08em; }
        .sc-sum-text { font-size: .74rem; color: var(--text); line-height: 1.45; margin-top: .06rem; opacity: .72; }
        /* Close button */
        .sc-close {
          position: absolute; top: .8rem; right: .8rem; z-index: 1;
          background: rgba(255,255,255,.15); border: 1px solid rgba(255,255,255,.25); border-radius: 3px;
          width: 24px; height: 24px; cursor: pointer; color: #fff;
          display: flex; align-items: center; justify-content: center; font-size: .75rem;
          transition: background .15s;
        }
        .sc-close:hover { background: rgba(255,255,255,.28); }
        @media (max-width: 900px) {
          .action-grid { grid-template-columns: 1fr; }
          .sc-card { flex-direction: column; width: min(92vw, 640px); }
          .sc-right { border-left: none; border-top: 1px solid var(--border); }
        }
        @media print { .sc-overlay, .card-mode-btn { display: none !important; } }
      </style>
    </head>
    <body data-report-mode="[default|comparison]" class="[add 'no-toc' if toc:false] [add 'no-animations' if animations:false]">

      <!-- AI Readability Layer 1: Report Summary JSON -->
      <!-- Always present, even if not visible to humans -->
      <script type="application/json" id="report-summary">
      {
        "title": "[title]",
        "author": "[author or empty string]",
        "date": "[date]",
        "abstract": "[abstract from frontmatter, or auto-generate a 1-sentence summary of the report content]",
        "poster_title": "[optional stronger summary-card title; opt-in only when the core judgment should read like a poster headline]",
        "poster_subtitle": "[optional subtitle shown below the poster title; only used when poster_title is present]",
        "poster_note": "[optional one-sentence closing line for the left panel; falls back to a short sentence from abstract]",
        "sections": ["[heading of section 1]", "[heading of section 2]", "..."],
        "kpis": [
          {"label": "[label]", "value": "[display value]", "trend": "[trend text or empty]"}
        ]
      }
      </script>

      <!-- Edit mode (always present) -->
      <div class="edit-hotzone" id="edit-hotzone"></div>
      <button class="edit-toggle" id="edit-toggle" title="Edit mode (E)">✏ Edit</button>

      <!-- Export (always present) -->
      <!-- lang:en labels: "↓ Export" / "🖨 Print / PDF" / "🖥 Save PNG (Desktop)" / "📱 Save PNG (Mobile)" / "💬 IM Image" -->
      <!-- lang:zh labels: "↓ 导出"  / "🖨 打印 / PDF"  / "🖥 保存图片（桌面）"    / "📱 保存图片（手机）"  / "💬 IM 分享长图"   -->
      <div class="export-menu" id="export-menu">
        <button class="export-item" id="export-print">[🖨 Print / PDF|🖨 打印 / PDF]</button>
        <button class="export-item" id="export-png-desktop">[🖥 Save PNG (Desktop)|🖥 保存图片（桌面）]</button>
        <button class="export-item" id="export-png-mobile">[📱 Save PNG (Mobile)|📱 保存图片（手机）]</button>
        <button class="export-item" id="export-im-share">[💬 IM Image|💬 IM 长图]</button>
      </div>
      <button class="export-btn" id="export-btn" title="Export">[↓ Export|↓ 导出]</button>

      <!-- Floating TOC (omit entirely if toc:false) -->
      <!-- TOC label localization: lang:en → aria-label="Contents" / "Table of Contents" / <h4>Contents</h4> -->
      <!--                         lang:zh → aria-label="目录" / "报告目录" / <h4>目录</h4> -->
      <button class="toc-toggle" id="toc-toggle-btn" aria-label="[Contents|目录]" aria-expanded="false">☰</button>
      <nav class="toc-sidebar" id="toc-sidebar" aria-label="[Table of Contents|报告目录]">
        <h4>[Contents|目录]</h4>
        <!-- Generate one <a> per ## heading and one per ### heading in the report -->
        <!-- Example (lang:en): <a href="#section-core-metrics" data-section="Core Metrics">Core Metrics</a> -->
        <!-- For ### heading: add class="toc-h3" -->
        [TOC links generated from all ## and ### headings in the IR]
      </nav>

      <div class="main-with-toc">
        <div class="report-wrapper">

          <!-- Report title and meta -->
          <!-- lang:en card button label: "⊞ Summary" | lang:zh: "⊞ 摘要卡" -->
          <div class="title-row">
            <h1>[title]</h1>
            <button class="card-mode-btn" id="card-mode-btn" title="[Summary card|摘要卡片]">[⊞ Summary|⊞ 摘要卡]</button>
          </div>
          [if abstract: <p class="report-subtitle">[abstract]</p>]
          [if author or date: <p class="report-meta">[author] · [date]</p>]

          <!-- Summary card overlay (always present) — left+right panels injected by buildCard() -->
          <div class="sc-overlay" id="sc-overlay">
            <div class="sc-card" id="sc-card">
              <button class="sc-close" id="sc-close" aria-label="Close">✕</button>
              <!-- .sc-left and .sc-right injected by JS -->
            </div>
          </div>

          <!-- AI Readability Layer 2: Section annotations are on each <section> element -->
          <!-- Rendered sections — each ## becomes: -->
          <!-- <section data-section="[heading]" data-summary="[1-sentence summary]"> -->
          <!--   <h2 id="section-[slug]">[heading]</h2> -->
          <!--   [section content] -->
          <!-- </section> -->

          [All rendered section content here]

          <!-- Visible footer (deterministic shell metadata only; do not add debug hashes, source notes, or extra prose) -->
          <div class="report-footer">kai-report-creator v[version] [theme]</div>

          <!-- Invisible watermark (must match the visible footer exactly) -->
          <div style="display:none;visibility:hidden;opacity:0;font-size:0;line-height:0;height:0;overflow:hidden;" aria-hidden="true" data-watermark="kai-report-creator v[version] [theme]">
            kai-report-creator v[version] [theme]
          </div>

        </div>
      </div>

      <script>
        // Scroll-triggered animations
        if (!document.body.classList.contains('no-animations')) {
          // Generic fade-in-up
          const fadeObserver = new IntersectionObserver(
            entries => entries.forEach(e => {
              if (e.isIntersecting) { e.target.classList.add('visible'); fadeObserver.unobserve(e.target); }
            }),
            { threshold: 0.08 }
          );
          document.querySelectorAll('.fade-in-up').forEach(el => fadeObserver.observe(el));

          // Stagger helper: observe parent, animate children one by one
          function staggerGroup(parentSel, childSel, delay) {
            document.querySelectorAll(parentSel).forEach(parent => {
              new IntersectionObserver((entries, obs) => {
                if (!entries[0].isIntersecting) return;
                obs.disconnect();
                parent.classList.add('stagger-ready');
                parent.querySelectorAll(childSel).forEach((el, i) =>
                  setTimeout(() => el.classList.add('visible'), i * delay)
                );
              }, { threshold: 0.1 }).observe(parent);
            });
          }
          staggerGroup('.kpi-grid', '.kpi-card', 100);   // KPI cards: spring bounce stagger
          staggerGroup('.timeline', '.timeline-item', 130); // Timeline items: slide-in stagger

          // KPI counter animation (CountUp)
          const kpiObserver = new IntersectionObserver(entries => {
            entries.forEach(e => {
              if (!e.isIntersecting) return;
              const el = e.target;
              const target = parseFloat(el.dataset.targetValue);
              if (isNaN(target)) return;
              const prefix = el.dataset.prefix || '';
              const suffix = el.dataset.suffix || '';
              const isFloat = String(target).includes('.');
              const decimals = isFloat ? String(target).split('.')[1].length : 0;
              let startTime = null;
              const duration = 1200;
              const animate = ts => {
                if (!startTime) startTime = ts;
                const progress = Math.min((ts - startTime) / duration, 1);
                const ease = 1 - Math.pow(1 - progress, 3);
                const current = isFloat
                  ? (ease * target).toFixed(decimals)
                  : Math.floor(ease * target).toLocaleString();
                el.textContent = prefix + current + suffix;
                if (progress < 1) requestAnimationFrame(animate);
                else el.textContent = prefix + (isFloat ? target.toFixed(decimals) : target.toLocaleString()) + suffix;
              };
              requestAnimationFrame(animate);
              kpiObserver.unobserve(el);
            });
          }, { threshold: 0.3 });
          document.querySelectorAll('.kpi-value[data-target-value]').forEach(el => kpiObserver.observe(el));
        }

        // TOC: hover to open, click to lock, no backdrop
        const tocBtn = document.getElementById('toc-toggle-btn');
        const tocSidebar = document.getElementById('toc-sidebar');
        if (tocBtn && tocSidebar) {
          let locked = false, closeTimer;
          function openToc() {
            clearTimeout(closeTimer);
            tocSidebar.classList.add('open');
            tocBtn.setAttribute('aria-expanded', 'true');
          }
          function scheduleClose() {
            closeTimer = setTimeout(() => {
              if (!locked) {
                tocSidebar.classList.remove('open');
                tocBtn.setAttribute('aria-expanded', 'false');
              }
            }, 150);
          }
          tocBtn.addEventListener('mouseenter', openToc);
          tocSidebar.addEventListener('mouseenter', openToc);
          tocBtn.addEventListener('mouseleave', scheduleClose);
          tocSidebar.addEventListener('mouseleave', scheduleClose);
          tocBtn.addEventListener('click', () => {
            locked = !locked;
            tocBtn.classList.toggle('locked', locked);
            if (locked) openToc(); else scheduleClose();
          });
          document.querySelectorAll('.toc-sidebar a').forEach(a => a.addEventListener('click', () => {
            if (!locked) scheduleClose();
          }));
        }

        // TOC active state tracking
        const tocLinks = document.querySelectorAll('.toc-sidebar a[data-section]');
        if (tocLinks.length) {
          const sectionObserver = new IntersectionObserver(entries => {
            entries.forEach(e => {
              const id = e.target.dataset.section;
              const link = document.querySelector(`.toc-sidebar a[data-section="${CSS.escape(id)}"]`);
              if (link) link.classList.toggle('active', e.isIntersecting);
            });
          }, { rootMargin: '-10% 0px -60% 0px' });
          document.querySelectorAll('section[data-section]').forEach(s => sectionObserver.observe(s));
        }
      </script>

      <script>
        // Edit mode: hover bottom-left hotzone to reveal button, click to toggle
        (function() {
          const hotzone = document.getElementById('edit-hotzone');
          const toggle  = document.getElementById('edit-toggle');
          if (!hotzone || !toggle) return;
          let active = false, hideTimer;
          function showBtn() { clearTimeout(hideTimer); toggle.classList.add('show'); }
          function schedHide() { hideTimer = setTimeout(() => { if (!active) toggle.classList.remove('show'); }, 400); }
          hotzone.addEventListener('mouseenter', showBtn);
          hotzone.addEventListener('mouseleave', schedHide);
          toggle.addEventListener('mouseenter', showBtn);
          toggle.addEventListener('mouseleave', schedHide);
          function enterEdit() {
            active = true; toggle.classList.add('active', 'show'); toggle.textContent = '✓ Done';
            document.body.classList.add('edit-mode');
            document.querySelectorAll('h1,h2,h3,p,li,td,th,figcaption').forEach(el => el.setAttribute('contenteditable', 'true'));
          }
          function exitEdit() {
            active = false; toggle.classList.remove('active'); toggle.textContent = '✏ Edit';
            document.body.classList.remove('edit-mode');
            document.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));
            schedHide();
          }
          hotzone.addEventListener('click', () => active ? exitEdit() : enterEdit());
          toggle.addEventListener('click', () => active ? exitEdit() : enterEdit());
          document.addEventListener('keydown', e => {
            if ((e.key === 'e' || e.key === 'E') && !document.activeElement.getAttribute('contenteditable')) {
              active ? exitEdit() : enterEdit();
            }
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
              e.preventDefault();
              const html = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
              const a = Object.assign(document.createElement('a'), {
                href: URL.createObjectURL(new Blob([html], {type: 'text/html'})),
                download: location.pathname.split('/').pop() || 'report.html'
              });
              a.click(); URL.revokeObjectURL(a.href);
            }
          });
        })();
      </script>

      <script>
        // Export: Print/PDF via prepared print mode; images via html2canvas (preloaded on page open)
        // Desktop PNG : full-page, adaptive scale (2× short / 1.5× long pages), PNG
        // Mobile PNG  : .report-wrapper 750px wide (iPhone 2× Retina), JPEG 92%
        // IM Share    : .report-wrapper 800px wide (WeChat/Feishu/DingTalk), JPEG 92%
        (function() {
          const exportBtn  = document.getElementById('export-btn');
          const exportMenu = document.getElementById('export-menu');
          const printBtn   = document.getElementById('export-print');
          const pngDesktop = document.getElementById('export-png-desktop');
          const pngMobile  = document.getElementById('export-png-mobile');
          const pngIM      = document.getElementById('export-im-share');
          if (!exportBtn || !exportMenu) return;
          const LABEL = exportBtn.textContent;
          const PRINT_MODE_CLASS = 'print-exporting';

          exportBtn.addEventListener('click', e => { e.stopPropagation(); exportMenu.classList.toggle('open'); });
          document.addEventListener('click', e => {
            if (!exportBtn.contains(e.target) && !exportMenu.contains(e.target))
              exportMenu.classList.remove('open');
          });

          /* Preload html2canvas immediately — ready before first click */
          let libPromise = null;
          function loadLib() {
            if (libPromise) return libPromise;
            libPromise = new Promise(resolve => {
              if (window.html2canvas) { resolve(); return; }
              const s = document.createElement('script');
              s.src = 'https://cdn.jsdelivr.net/npm/html2canvas@1/dist/html2canvas.min.js';
              s.onload = resolve; document.head.appendChild(s);
            });
            return libPromise;
          }
          loadLib(); /* fire immediately */

          function restore() { exportBtn.style.visibility = ''; exportBtn.textContent = LABEL; }
          function preparePrintExport() {
            exportMenu.classList.remove('open');
            exportBtn.style.visibility = 'hidden';
            exportBtn.textContent = '…';
            document.documentElement.classList.add(PRINT_MODE_CLASS);
            document.documentElement.style.setProperty('--print-bg-color', exportBackgroundColor());
          }
          function cleanupPrintExport() {
            document.documentElement.classList.remove(PRINT_MODE_CLASS);
            document.documentElement.style.removeProperty('--print-bg-color');
            restore();
          }
          function filename(suffix, ext) {
            const d = new Date(), pad = n => String(n).padStart(2,'0');
            const date = `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}`;
            return (document.title||'report').replace(/[/\\:*?"<>|]/g,'_') + `_${date}${suffix}.${ext}`;
          }
          function exportBackgroundColor() {
            const rootStyles = getComputedStyle(document.documentElement);
            const cssVar = (rootStyles.getPropertyValue('--bg') || '').trim();
            if (cssVar) return cssVar;
            const bodyColor = getComputedStyle(document.body).backgroundColor;
            if (bodyColor && bodyColor !== 'rgba(0, 0, 0, 0)' && bodyColor !== 'rgba(0,0,0,0)' && bodyColor !== 'transparent') {
              return bodyColor;
            }
            return '#ffffff';
          }
          function saveBlob(canvas, fname, jpeg) {
            canvas.toBlob(blob => {
              const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: fname });
              a.click(); URL.revokeObjectURL(a.href); restore();
            }, jpeg ? 'image/jpeg' : 'image/png', jpeg ? 0.92 : 1);
          }
          function capture(el, cfg, fname, jpeg) {
            exportMenu.classList.remove('open');
            exportBtn.style.visibility = 'hidden';
            exportBtn.textContent = '…';
            const cardBtn = document.getElementById('card-mode-btn');
            if (cardBtn) cardBtn.style.visibility = 'hidden';
            // When summary card is open, capture .sc-card directly
            // (html2canvas cannot capture position:fixed overlays)
            if (document.body.classList.contains('card-mode')) {
              const card = document.getElementById('sc-card');
              const cardFname = filename('-摘要卡', jpeg ? 'jpg' : 'png');
              loadLib().then(() => html2canvas(card, { scale: 2, useCORS: true, allowTaint: true, backgroundColor: '#ffffff' }).then(c => {
                if (cardBtn) cardBtn.style.visibility = '';
                restore();
                saveBlob(c, cardFname, jpeg);
              }));
              return;
            }
            const tocSidebar = document.getElementById('toc-sidebar');
            const tocToggle = document.getElementById('toc-toggle-btn');
            const tocIsOpen = tocSidebar && tocSidebar.classList.contains('open');
            if (tocToggle && !tocIsOpen) tocToggle.style.visibility = 'hidden';
            document.querySelectorAll('.fade-in-up').forEach(e => e.classList.add('visible'));
            loadLib().then(() => html2canvas(el, cfg).then(c => {
              if (tocToggle && !tocIsOpen) tocToggle.style.visibility = '';
              if (cardBtn) cardBtn.style.visibility = '';
              saveBlob(c, fname, jpeg);
            }));
          }
          window.addEventListener('afterprint', cleanupPrintExport);

          printBtn && printBtn.addEventListener('click', () => {
            preparePrintExport();
            requestAnimationFrame(() => {
              requestAnimationFrame(() => {
                window.print();
              });
            });
          });

          pngDesktop && pngDesktop.addEventListener('click', () => {
            const H = document.documentElement.scrollHeight;
            capture(document.documentElement, {
              scale: H > 4000 ? 2.5 : 3, useCORS: true, allowTaint: true,
              scrollX: 0, scrollY: 0,
              width: document.documentElement.scrollWidth, height: H,
              windowWidth: document.documentElement.scrollWidth, windowHeight: H
            }, filename('', 'png'), false);
          });

          pngMobile && pngMobile.addEventListener('click', () => {
            const el = document.querySelector('.report-wrapper') || document.documentElement;
            capture(el, {
              scale: (750 / el.offsetWidth) * 2, useCORS: true, allowTaint: true,
              backgroundColor: exportBackgroundColor(),
              scrollX: 0, scrollY: 0, width: el.scrollWidth, height: el.scrollHeight
            }, filename('-mobile', 'jpg'), true);
          });

          pngIM && pngIM.addEventListener('click', () => {
            const el = document.querySelector('.report-wrapper') || document.documentElement;
            capture(el, {
              scale: (800 / el.offsetWidth) * 2, useCORS: true, allowTaint: true,
              backgroundColor: exportBackgroundColor(),
              scrollX: 0, scrollY: 0, width: el.scrollWidth, height: el.scrollHeight
            }, filename('-im', 'jpg'), true);
          });
        })();
      </script>

      <script>
        // Summary card — editorial two-column layout, built from #report-summary JSON + DOM data-summary
        (function() {
          const btn      = document.getElementById('card-mode-btn');
          const overlay  = document.getElementById('sc-overlay');
          const closeBtn = document.getElementById('sc-close');
          if (!btn || !overlay) return;

          function splitPosterTitle(d) {
            const explicitTitle = (d.poster_title || '').trim();
            const explicitSubtitle = (d.poster_subtitle || '').trim();
            const raw = (d.title || '').trim();
            return { main: explicitTitle || raw, sub: explicitTitle ? explicitSubtitle : '' };
          }

          function summaryCardLabel() {
            const lang = (document.documentElement.lang || '').toLowerCase();
            return lang.startsWith('zh') ? '报告摘要' : 'Report Summary';
          }

          function posterNoteText(d) {
            const explicit = (d.poster_note || '').trim();
            if (explicit) return explicit;
            const raw = (d.abstract || '').trim();
            if (!raw) return '';
            const sentence = raw.match(/^(.{0,72}?[。！？!?]|.{0,120})/)?.[1]?.trim() || raw;
            return sentence.length > 72 ? sentence.slice(0, 72).trim() + '…' : sentence;
          }

          function buildCard() {
            try {
              const d = JSON.parse(document.getElementById('report-summary').textContent);
              const poster = splitPosterTitle(d);
              const note = posterNoteText(d);

              // Left panel: poster title hierarchy + one short closing sentence near the bottom.
              const leftHtml = `
                <div class="sc-left">
                  <div class="sc-label">${summaryCardLabel()}</div>
                  <div class="sc-title-main">${poster.main || ''}</div>
                  ${poster.sub ? `<div class="sc-title-sub">${poster.sub}</div>` : ''}
                  ${note ? `<div class="sc-note">${note}</div>` : ''}
                </div>`;

              // Right panel: compact KPI rows + section summaries only. Keep the card poster-like.
              const kpiRowsHtml = (d.kpis || []).slice(0, 6).map(k => `
                <div class="sc-kpi-row">
                  <div class="sc-kpi-row-l">${k.label || ''}</div>
                  <div class="sc-kpi-row-v">${k.value || ''}${k.trend ? ` <span class="sc-kpi-row-t">${k.trend}</span>` : ''}</div>
                </div>`).join('');
              const sectionSummaries = Array.from(
                document.querySelectorAll('section[data-section]')
              ).map(s => ({ name: s.dataset.section || '', text: s.dataset.summary || '' }))
               .filter(s => s.name)
               .slice(0, 3);
              const summariesHtml = sectionSummaries.map(s => `
                <div class="sc-sum-item">
                  <div class="sc-sum-name">${s.name}</div>
                  ${s.text ? `<div class="sc-sum-text">${s.text}</div>` : ''}
                </div>`).join('');
              const rightHtml = `
                <div class="sc-right">
                  ${kpiRowsHtml ? `<div class="sc-kpi-rows">${kpiRowsHtml}</div>` : ''}
                  ${summariesHtml ? `<div class="sc-summaries" style="margin-top:.5rem">${summariesHtml}</div>` : ''}
                </div>`;

              const card = document.getElementById('sc-card');
              card.insertAdjacentHTML('beforeend', leftHtml + rightHtml);
            } catch(e) {
              const card = document.getElementById('sc-card');
              card.insertAdjacentHTML('beforeend', '<div style="padding:2rem;color:#666">Summary unavailable.</div>');
            }
          }

          let built = false;
          function openCard() {
            if (!built) { buildCard(); built = true; }
            document.body.classList.add('card-mode');
            overlay.setAttribute('aria-hidden', 'false');
          }
          function closeCard() {
            document.body.classList.remove('card-mode');
            overlay.setAttribute('aria-hidden', 'true');
          }

          btn.addEventListener('click', openCard);
          closeBtn && closeBtn.addEventListener('click', closeCard);
          overlay.addEventListener('click', e => { if (e.target === overlay) closeCard(); });
          document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && document.body.classList.contains('card-mode')) closeCard();
          });
        })();
      </script>

    </body>
    </html>
