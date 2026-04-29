---
name: paper-deep-reading
description: Produce a source-aware, research-generative, MIT-0-compatible single-file deep-reading report for a research paper, with a rich narrative body, a final claim-to-evidence appendix, and the companion artifacts report.md, traceability_manifest.json, latex_paragraphs.json, artifact_index.json, and research_lens.json. Use for OpenClaw or ClawHub paper-reading tasks that need deep analysis without a webpage reader.
---

# Paper Deep Reading: Source-Aware + Research-Generative Single-File Pipeline

Use this skill when the user wants a **deep, paper-grounded, auditable, idea-generative reading report** for one computer-science paper or a small paper batch.

The input may be:

- a user-provided PDF
- a user-provided LaTeX source tree or `.tex` files
- only the paper title or citation-like paper name

The default output is **text-first, audit-first, and idea-oriented**.
This version intentionally **does not rely on a webpage reader**.

## 1) Core deliverables

1. **Human-readable report**
   - `report.md`

2. **Machine-readable trace artifacts**
   - `traceability_manifest.json`
   - `latex_paragraphs.json`
   - `artifact_index.json`

3. **Machine-readable research artifact**
   - `research_lens.json`

The report is the primary user-facing deliverable.
It must read like a serious deep-reading memo, not a thin checklist dump.

## 2) ClawHub and MIT-0 package discipline

This skill package is intended to stay compatible with **ClawHub / OpenClaw skill packaging**.

Keep the package lean:

- keep only files that another agent needs to execute the workflow
- do not reintroduce auxiliary docs such as `README.md` or `CHANGELOG.md`
- keep support files, templates, and scripts focused on execution

Keep the package license-safe:

- this package is prepared for ClawHub's `MIT-0` publication model, and the local bundle keeps the same text in `LICENSE.txt`
- do not add restrictive or conflicting license terms elsewhere in the package
- do not vendor third-party projects or assets into the skill unless their license is compatible with `MIT-0` redistribution expectations
- when external tooling is useful, document it or install it outside the skill instead of copying its source tree into the package

## 3) Depth bar: match the Codex version even in single-file mode

Do **not** treat the OpenClaw / ClawHub version as a lightweight summary mode.

The report depth bar should stay close to the richer Codex version:

- cover the full 25-section reading scope
- preserve central equations instead of flattening them into prose
- explain why modules exist, not only what they are called
- reconstruct likely author-side reasoning when the evidence supports it
- connect experiments back to claims, ablations, and alternative explanations
- extract reusable research patterns and future ideas

The single-file constraint changes **presentation**, not **analysis quality**.

## 4) Research-generative overlay

This version keeps the original traceability and formula-preservation bar, but adds the **research-generative reading layer** from the new methodology.

The report must now help the user answer not only:

- what the paper did

but also:

- how the authors may have found the direction
- what hidden assumption `C` broke
- what unavailable mechanism `Y` had to be replaced
- what surrogate mechanism `Z` the paper constructed
- how each module maps to a failure mode
- why key citations matter in the story
- what hidden assumption can seed the next paper

Use [references/research-generative-methodology.md](references/research-generative-methodology.md) whenever the user wants:

- author-perspective reading
- idea mining
- reverse story construction
- module-level design logic
- citation-function analysis
- boundary-pushing future directions

## 5) Verification surface: body first, appendix last

The report itself remains the primary verification surface, but the **detailed evidence placement** is:

1. **Main body**
   - readable section-by-section analysis
   - `### Anchored Points` blocks near the relevant discussion
   - concise claim bullets in the form `- [C5.2][evidence-backed interpretation] ...`

2. **Final appendix**
   - detailed claim-by-claim evidence records
   - exact source files
   - section paths
   - line spans
   - page hints when available
   - quote snippets and excerpt windows
   - notes that help a human verify the claim quickly

Do **not** clutter the main narrative by inserting long locator bullets immediately after every claim.
Keep the main body readable, and move the detailed original-paragraph explanation to the final `# Appendix: Claim -> Evidence Index`.

Use [scripts/render_inline_trace_report.py](scripts/render_inline_trace_report.py) after drafting the report and manifest to materialize or refresh that appendix.

## 6) Formula-first preservation

When the paper contains key formulas, the report must **not** compress them into prose-only summaries.

For each central equation or objective, the report must explicitly include:

1. the equation itself in readable math form
2. symbol-by-symbol explanation
3. what optimization / estimation / filtering role it plays
4. why the authors likely wrote it in this form instead of a nearby alternative
5. how it connects to the previous and next module
6. what may be brittle, heuristic, under-justified, or computationally expensive about it

Do not weaken equation detail for the sake of shorter presentation.

## 7) Source acquisition policy

Always assemble the **best available evidence package** before writing.

Preferred reading order:

1. **arXiv LaTeX/source package**
2. **user-provided LaTeX**
3. **best available PDF**
4. **supplementary material**
5. **OpenReview thread / rebuttal / meta-review when relevant**

### 7.1 When LaTeX is available

Treat LaTeX as the primary structural source.

Use PDF only as a visual and pagination aid for:

- figure interpretation
- table reading
- page-local narrative flow
- page anchors

### 7.2 When only PDF is available

Do not stop at PDF summarization immediately.

First check whether the same paper has a matching arXiv LaTeX/source package.
If it exists and matches the same paper, switch to **LaTeX-primary + PDF-assisted** reading.

If not, continue with the PDF and say explicitly that the reading is **PDF-primary**.

### 7.3 When only title is available

Search for the paper and collect:

1. arXiv source package if available
2. the best PDF
3. supplementary PDF or appendix if available
4. OpenReview forum if venue is ICLR or otherwise OpenReview-hosted

Never silently analyze the wrong paper.
Disambiguate by title, authors, abstract, year, and method keywords.

### 7.4 OpenReview policy

If the paper is an ICLR or OpenReview-hosted paper, look for:

- reviewer comments
- meta-review or area-chair summary
- author rebuttal or response
- revision signals relevant to acceptance

Use them to enrich:

- reviewer-lens audit
- confidence in claimed contributions
- limitations and unresolved doubts

## 8) Language policy

Write the **skill instructions, internal prompts, and template skeletons in English**.
Choose the **report language** from the user's current request language by default.

- if the user's current request is primarily in Chinese, write the report in Chinese
- if the user's current request is primarily not Chinese, write the report in English
- if the user explicitly requests another language, follow that explicit instruction
- if the request is mixed-language, follow the dominant user language in the current request

When writing the report in Chinese:

- keep proper nouns and fixed technical identifiers in English
- this includes paper titles, method names, module names, datasets, baselines, theorem or object names, citation names, equation symbols, claim IDs, filenames, and JSON keys
- translate section headings and explanatory prose into Chinese, but do not translate artifact filenames, schema fields, or claim IDs

## 9) Mandatory artifacts

### 9.1 `report.md`

The report must cover, whenever the evidence supports it:

1. paper identification and source package used
2. one-sentence thesis and research equation
3. title interpretation
4. what problem the paper really solves
5. scientific problem ladder
6. how the authors may have found the direction
7. how the authors built the story
8. related work, key citations, and what was still missing
9. main idea
10. symbols, assumptions, and notation
11. key formulas and equation-by-equation explanation
12. theory / proof / practice mapping
13. algorithm or module walkthrough with concrete example
14. method deep reading: the author-thinking behind each module
15. figure explanation
16. experimental design
17. experiments as story evidence and claim alignment audit
18. reviewer-lens audit
19. innovation points and claim-by-claim support audit
20. story-making pattern worth learning
21. weaknesses and limitations
22. innovation type and scientific-boundary judgment
23. future directions and stronger idea paths
24. vivid plain-language story summary
25. exact sources used

Use [templates/report_template.md](templates/report_template.md) as the default skeleton.

For each numbered section:

- start with `### Anchored Points`
- add one or more claim bullets in the exact form `- [C<section>.<index>][label] claim text`
- keep the bullets concise
- follow the bullets with a **real explanatory section**, not just more bullets
- add tables, formulas, examples, reviewer-style critique, or story reconstruction when they help understanding

### 9.2 `traceability_manifest.json`

This is the claim-to-evidence map.

Rules:

- every claim id in the main report body must appear in the manifest
- one bullet must not hide multiple independent claims under one id
- if a claim depends on multiple paragraphs / equations / tables / appendix passages, list them separately
- each claim entry should include `interpretation_type`
- each claim entry should preferably include `research_role`
- each claim entry should include human-friendly locator data when possible

### 9.3 `latex_paragraphs.json`

This is the stable LaTeX anchor index.

Each entry must keep:

- `paragraph_id`
- `source_path`
- `line_start`
- `line_end`
- `section_path`
- `kind`
- `text`

### 9.4 `artifact_index.json`

A compact index for the generated text-first bundle.

It should list the locations of:

- `report.md`
- `traceability_manifest.json`
- `latex_paragraphs.json`
- `research_lens.json`
- main PDF if any
- supplementary PDF if any
- source package path if known

### 9.5 `research_lens.json`

This is the compact idea-mining artifact.
Use [templates/research_lens.template.json](templates/research_lens.template.json) and [references/artifact_contract.md](references/artifact_contract.md).

It should capture:

- the paper's research equation
- the likely direction-finding path
- challenge-to-module mapping
- per-module hidden assumptions
- citation logic
- story pattern worth reusing
- strongest future idea directions

## 10) Claim discipline

### 10.1 Claim ids

Use stable section-local ids such as:

- `C3.1`
- `C5.2`
- `C14.4`

### 10.2 Claim splitting rule

Do not hide multiple judgments in one claim bullet.

### 10.3 Evidence completeness rule

List all materially relevant evidence for a claim, not just one convenient paragraph.

### 10.4 Interpretation labels

Each claim must declare exactly one of:

- `evidence-backed interpretation`
- `plausible inference`
- `speculation`

### 10.5 Research-generative honesty rule

If the report reconstructs likely author reasoning, it must still point to the exact paragraphs that motivate that reconstruction.
Idea generation is required, but fabrication is forbidden.

## 11) Writing style for verification and idea generation

Prefer a report that is pleasant to read **and** easy to audit.

For every claim, the user should be able to answer:

1. What section-level conclusion is being made?
2. Is it direct evidence, plausible inference, or speculation?
3. Where should I verify it in the appendix?

For the strongest sections, the report should also answer:

1. What hidden assumption broke?
2. What missing mechanism was replaced?
3. What future paper becomes possible if that assumption fails harder?

Use phrasing such as:

- "A plausible author-side thinking path is ..."
- "This module is best understood as a surrogate for ..."
- "The citation is not ornamental; it functions as ..."
- "The deepest reusable lesson is ..."
- "This weakness can be converted into a new research direction ..."

The report should sound like a research mentor reconstructing how the work may have been invented, not like a generic summarizer.

## 12) Grounded workflow

1. Assemble the best source package.
2. If LaTeX is available, extract paragraph anchors with `scripts/extract_latex_paragraphs.py`.
3. Draft `report.md` using anchored claim IDs in the main body.
4. Keep the claim bullets concise and put the longer explanation in prose, tables, and formula walkthroughs after them.
5. Fill `traceability_manifest.json` so each claim points to one or more paragraph IDs or fallback anchors.
6. Fill `research_lens.json` so the paper's research equation, story structure, module logic, citation functions, and future directions are captured in structured form.
7. Fill `artifact_index.json` so the bundle stays portable.
8. Run `scripts/validate_traceability.py`.
9. Run `scripts/render_inline_trace_report.py` to append or refresh the final `Claim -> Evidence Index` appendix in `report.md`.
10. Only then finalize the bundle.

## 13) Failure handling

If some sources cannot be found, do not abort.
State clearly what was attempted, what was found, what was missing, and how that affects confidence.
Then continue with the best grounded report possible.

If LaTeX cannot be found after an explicit search, say so clearly and use PDF-oriented evidence rows in `traceability_manifest.json` instead of pretending paragraph anchors exist.
