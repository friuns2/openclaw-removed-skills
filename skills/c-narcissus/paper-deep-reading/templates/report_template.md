# Deep Reading Report: <paper-title>

Use this template together with `traceability_manifest.json` and `research_lens.json`.
Write the final report in Chinese when the user's current request is primarily in Chinese; keep proper nouns, fixed technical identifiers, claim IDs, filenames, and JSON keys in English. Otherwise write the report in English.

For every numbered section below:

- start with `### Anchored Points`
- add one or more claims in the exact form `- [C<section>.<index>][label] claim text`
- keep the claim bullets concise and judgment-focused
- make sure every main-body claim ID appears in `traceability_manifest.json`
- if a claim is reconstructive rather than directly stated, mark it as inferential in the manifest
- if one claim depends on multiple source locations, list every materially necessary source location as separate evidence rows in `traceability_manifest.json`
- if one bullet contains multiple independent claims, split it into multiple claim IDs before writing the manifest
- after the anchored points, add the longer explanation, tables, formulas, critique, and author-side reconstruction as needed
- do not paste detailed locator bullets in the middle of the body; reserve that for the final appendix

## 1. Paper Identification and Source Package Used
### Anchored Points
After anchored points, state the title, authors, venue or status, reading mode (`LaTeX-primary`, `PDF-primary`, or mixed), exact source files used, what was searched for, and what was missing.

## 2. One-Sentence Thesis and Research Equation
### Anchored Points
After anchored points, summarize the paper in one sentence and express the research equation in the form: old success -> broken assumption -> hard setting -> borrowed tool -> unavailable mechanism -> surrogate mechanism.

## 3. Title Interpretation
### Anchored Points
After anchored points, interpret the title term by term and explain how each keyword maps to the actual method, setting, and claim scope.

## 4. What Problem the Paper Really Solves
### Anchored Points
After anchored points, explain the direct problem, the practical pain point, the scientific question, and the larger pressure from the parent field.

## 5. Scientific Problem Ladder
### Anchored Points
After anchored points, build the ladder explicitly from paper-local problem to broader AI or systems boundary, and note any upper-level bottlenecks introduced by the method itself.

## 6. How the Authors May Have Found This Direction
### Anchored Points
After anchored points, reconstruct the likely dissatisfaction, near-transfer from neighboring methods, blocking constraint, and why the surrogate mechanism was worth trying. Keep uncertainty explicit.

## 7. How the Authors Built the Story
### Anchored Points
After anchored points, map challenge -> failure mode -> design principle -> module -> ablation or evidence, and judge whether the story forms a coherent loop instead of a bag of modules.

## 8. Related Work, Key Citations, and What Was Still Missing
### Anchored Points
After anchored points, explain what the key cited works solved, what they left open, and the narrative role of each citation cluster: field anchor, limitation evidence, method ancestor, baseline pressure, protocol justification, or contrast boundary.

## 9. Main Idea
### Anchored Points
After anchored points, explain the conceptual replacement or coordination logic that makes the method coherent, rather than repeating only module names.

## 10. Symbols, Assumptions, and Notation
### Anchored Points
After anchored points, introduce the important symbols, operators, assumptions, and task-specific objects before relying on them heavily later.

## 11. Key Formulas and Equation-by-Equation Explanation
### Anchored Points
After anchored points, preserve the central formulas in readable math form. For each one, explain symbols, role, why this form was chosen, how it connects to adjacent modules, and what looks fragile, heuristic, or expensive.

## 12. Theory / Proof / Practice Mapping
### Anchored Points
After anchored points, explain what is proved, why it is proved, what reviewer concern it addresses, how theory maps to implementation, and where theory and practice diverge.

## 13. Algorithm or Module Walkthrough with Concrete Example
### Anchored Points
After anchored points, give a step-by-step pipeline walkthrough with at least one concrete mini-example that instantiates inputs, intermediate states, and outputs.

## 14. Method Deep Reading: The Author-Thinking Behind Each Module
### Anchored Points
After anchored points, explain for each major module: the failure being fixed, the ideal but unavailable solution, the proxy signal actually used, the hidden assumption, the risk, and the future idea that appears if the assumption breaks.

## 15. Figure Explanation
### Anchored Points
After anchored points, interpret the key figures or captions, explain what each figure is meant to demonstrate, and judge whether the visual evidence really supports the associated claim.

## 16. Experimental Design
### Anchored Points
After anchored points, explain datasets, tasks, baselines, metrics, ablations, implementation details, and how the compared methods map back to the related-work landscape.

## 17. Experiments as Story Evidence and Claim Alignment Audit
### Anchored Points
After anchored points, explain what claim each main result is supposed to support, what alternative explanation it rules out, and whether the evidence strongly, partially, or weakly supports the claim.

## 18. Reviewer-Lens Audit
### Anchored Points
After anchored points, assess novelty, significance, soundness, rigor, reproducibility, clarity, missing controls, limitations honesty, and any OpenReview reviewer or rebuttal signal when available.

## 19. Innovation Points and Claim-by-Claim Support Audit
### Anchored Points
After anchored points, list the paper's main contribution claims and judge whether each one is supported by theory, experiments, qualitative evidence, reviewer discussion, or only weak evidence.

## 20. Story-Making Pattern Worth Learning
### Anchored Points
After anchored points, extract the reusable pattern from the paper, such as a replacement story, three-module story, closed loop, empty-cell positioning, or hidden-assumption break.

## 21. Weaknesses and Limitations
### Anchored Points
After anchored points, discuss unresolved weaknesses, failure modes, scope limits, hidden costs, and where the current idea is likely to break.

## 22. Innovation Type and Scientific-Boundary Judgment
### Anchored Points
After anchored points, judge whether the work is incremental, cross-pollinated, conceptually reframing, or potentially boundary-pushing, and explain why.

## 23. Future Directions and Stronger Idea Paths
### Anchored Points
After anchored points, propose next-step ideas, stronger boundary directions, alternative modules, or more decisive experiments. Tie the best future ideas to hidden assumptions whose failure would break the current method.

## 24. Vivid Plain-Language Story Summary
### Anchored Points
After anchored points, write a short memorable story that stays technically faithful while remaining accessible to a non-specialist.

## 25. Exact Sources Used
### Anchored Points
After anchored points, list exactly which PDFs, LaTeX files, supplementary materials, OpenReview pages, or screenshots were used, and explicitly mention missing or ambiguous sources.

---

## Optional Structured Notes for `research_lens.json`

### Research Equation
- old success / paradigm:
- broken assumption:
- hard setting:
- borrowed tool:
- unavailable mechanism:
- surrogate mechanism:

### Challenge-to-Module Map

| Challenge | Failure mode | Design principle | Module | Evidence |
|---|---|---|---|---|

### Module Lens Table

| Module | Failure fixed | Ideal unavailable solution | Available proxy | Hidden assumption | Future research point |
|---|---|---|---|---|---|

### Citation Function Table

| Citation cluster | Narrative function | Assumption inherited | How the paper modifies it |
|---|---|---|---|

### Story Pattern Worth Reusing
- pattern name:
- compact formula:
- lesson:

### Boundary-Pushing Idea List
- hidden assumption:
- what breaks:
- next mechanism worth exploring:
- linked claim ids:

---

# Appendix: Claim -> Evidence Index

Render this appendix only after the main body is complete.
Use `scripts/render_inline_trace_report.py` to append or refresh the detailed evidence appendix.

For each claim ID from the main report body, create a subsection like:

## C<section>.<index>
- Interpretation type:
- Statement:
- Research role:
- Confidence:

### Evidence 1
- Source file:
- Section path:
- Lines:
- Page:
- Locator method:
- Quote:
- Excerpt window:
- Notes:
