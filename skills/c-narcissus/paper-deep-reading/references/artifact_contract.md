# Artifact Contract

## `artifact_index.json`

Top-level index for all outputs that belong to one paper reading bundle.

Required keys:

- `schema_version`
- `paper_id`
- `report`
- `traceability_manifest`
- `latex_paragraphs`
- `research_lens`

Optional keys:

- `source_package`
- `pdfs`
- `notes`

## `traceability_manifest.json`

Maps report claims to source evidence.

Each claim entry should include:

- `claim_id`
- `section_id`
- `report_anchor`
- `statement`
- `interpretation_type`
- `confidence`
- `evidences`

Recommended extra fields:

- `research_role`
- `human_locators`

Each evidence entry may include:

- `evidence_id`
- `source_kind`
- `source_file`
- `paragraph_id`
- `page`
- `line_start`
- `line_end`
- `locator_method`
- `synctex`
- `quote_text`
- `notes`

## `latex_paragraphs.json`

Stable anchor list extracted from LaTeX.

Each paragraph entry should include:

- `paragraph_id`
- `source_path`
- `line_start`
- `line_end`
- `section_path`
- `kind`
- `text`

## `research_lens.json`

This is the compact idea-mining layer.
It should capture:

- research equation
- direction reconstruction
- challenge-to-module map
- module hidden assumptions
- citation logic
- reusable story pattern
- strongest future directions

Every `claim_ids` entry inside `research_lens.json` must point to a real report claim.

## Report requirement

In `report.md`, every main-body claim bullet should appear in the form:

- `[C<section>.<index>][interpretation label] statement`

The detailed locator material should live in the final `# Appendix: Claim -> Evidence Index`, not inside the middle of the narrative body.

For each claim entry in the appendix, provide enough detail for a human verifier to know:

- which source file to open
- which section / subsection to inspect
- which line span or page span to inspect
- what quote snippet or excerpt window to look for
- what note or role explains why that evidence matters

## Claim typing

Allowed interpretation labels:

- `evidence-backed interpretation`
- `plausible inference`
- `speculation`
