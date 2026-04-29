# Business Blueprint Quality Hardening Design

## Status

Adopted

## Goal

Strengthen `kai-business-blueprint` as an IR-first skill by adding explicit export integrity gates, clearer route contracts, a reusable failure-map/evals layer, and better cross-platform CLI coverage without regressing the existing `blueprint -> projection -> export` workflow.

## Why This Matters

The recent `slide-creator` documents surfaced a pattern that also applies here:

- the hardest bugs were not caused by missing product intent
- they were caused by missing structural guarantees
- review logic focused on content quality, but not on output integrity
- route boundaries were soft enough that the wrong renderer could still produce a superficially plausible artifact

`kai-business-blueprint` already has the correct top-level architecture:

- `solution.blueprint.json` as semantic truth
- `solution.projection.json` as downstream machine handoff
- viewer/export outputs as derived artifacts

The next step is not inventing a new artifact. The next step is making derived artifacts harder to generate incorrectly.

## Current Strengths

The current skill already has four strong foundations:

1. IR-first artifact boundaries are explicit.
2. The skill contract already states that unsupported diagram requests fall back to `freeflow`.
3. Architecture-specific layout rules are partially locked by contract tests.
4. Export quality has improved through targeted fixes and regression tests.

This means the right move is to harden the existing architecture, not replace it.

## Current Weaknesses

Despite recent improvements, four structural gaps remain:

### 1. Export integrity is still mostly implicit

Today the tests prove many specific regressions are fixed, but there is not yet a formal integrity layer for exports.

Examples:

- referenced defs like `marker-end="url(#...)"`, gradients, patterns, or filters may be used without a generalized integrity check
- canvas bounds are still validated through view-specific regressions rather than a shared geometry guarantee
- label placement and readability still rely on local heuristics rather than a formal threshold set

### 2. Route selection and rendering are too tightly coupled

`business_blueprint/export_svg.py` now contains route selection, layout strategy, theme logic, label placement, and multiple view renderers in one large surface.

That creates two risks:

- new routing changes can silently affect the wrong renderer
- bug fixes for one view can regress another because they share too much implementation context

### 3. Failure knowledge is not yet first-class

The team now knows a recognizable set of recurring blueprint export failures:

- toothpaste squeezing in layered diagrams
- top-right legend overlays
- clipped bottom canvas
- partial dark backgrounds
- labels sitting on elbow turns
- long swimlane titles wrapping too early
- actors rendered as ordinary system cards
- sparse blueprints causing downstream over-inference

But this knowledge mostly lives in commits and tests, not in a durable failure taxonomy.

### 4. Cross-platform behavior is under-specified

The skill is CLI-first, but current E2E coverage is still biased toward local happy-path execution.

Known risk areas include:

- Windows path handling
- PowerShell/cmd stdout and stderr behavior
- CRLF file output
- Unicode input/output under different console defaults
- `python -m` entry paths versus direct script assumptions

## Design Principles

1. Preserve the existing IR-first artifact stack. Do not add a third planning artifact.
2. Treat export correctness as a structural integrity problem, not just a visual polish problem.
3. Make route selection explicit and reviewable before renderer logic runs.
4. Promote known failure modes into reusable eval assets.
5. Add cross-platform guarantees at the CLI layer rather than hoping renderer tests cover them indirectly.
6. Prefer shared engine utilities over copy-pasted heuristics, but keep view renderers isolated from each other.

## Decision Summary

This design proposes five coordinated changes.

### Decision 1: Keep `blueprint -> projection` as the only durable machine contract

No new durable artifact is introduced.

The stable contract remains:

- `solution.blueprint.json` = semantic source of truth
- `solution.projection.json` = downstream narrative/machine projection
- viewer/export outputs = derived presentation artifacts only

This explicitly rejects any move back toward markdown-centric planning artifacts for business-blueprint itself.

### Decision 2: Introduce an explicit export route contract layer

Before rendering, the skill should resolve a route contract that says:

- which export family is being requested
- why that family is valid for the current blueprint/request
- which fallback applies if the preferred route is not structurally safe

Conceptually, the route layer should distinguish:

- `freeflow`
- `architecture-template`
- `poster`
- `swimlane`
- `hierarchy`
- `evolution`

The important point is not the exact names. The important point is that route selection becomes a first-class decision surface instead of an implicit side effect inside rendering code.

#### Route Eligibility Matrix

The route contract should include an explicit eligibility matrix.

Minimum initial shape:

| Route | Structural prerequisites | First fallback | Terminal behavior |
|------|---------------------------|----------------|-------------------|
| `freeflow` | Any valid blueprint with at least one renderable node or relation | None | If integrity still fails, export exits non-zero with a structural diagnostics payload |
| `architecture-template` | Recognizable L→R architecture shape, categorized systems, limited per-layer density, and no route-breaking overflow risk | `freeflow` | Same as above |
| `poster` | Clear layer/group structure with bounded peer density per row or wrapped-row support | wrapped poster or `freeflow` | Same as above |
| `swimlane` | Actor-owned flow steps with meaningful lane grouping | `freeflow` | Same as above |
| `hierarchy` | Stable tree/group relationship with low ambiguity in parent-child grouping | `freeflow` | Same as above |
| `evolution` | Ordered chronological or staged progression data | `freeflow` | Same as above |

The exact thresholds belong in machine-readable configuration, not in prose, but the proposal should lock the existence of this matrix and the final failure path.

### Decision 3: Add an export integrity gate for SVG/HTML artifacts

Add a shared integrity pass that runs after render assembly and before the artifact is considered valid.

The integrity layer should cover at least these classes of checks:

#### 3.1 Definition integrity

- every referenced marker/gradient/pattern/filter exists
- every referenced animation or defs block exists when applicable

This is a pure structural pass and should ship before geometry-sensitive checks.

#### 3.2 Canvas integrity

- the final canvas/viewBox encloses the last content block, legend, footer, and any safe-area decorations
- no view relies on clipping to hide overflow

This is a geometry pass and should be introduced only after thresholds are formalized.

#### 3.3 Layout integrity

- legend placement respects bottom safe-area rules
- labels avoid known no-go zones such as elbow joints and card boundaries
- titles use available width before wrapping and never overflow their card

These checks must be driven by explicit numeric thresholds rather than prose heuristics.

Recommended machine-readable source:

- `evals/export-integrity-thresholds.json`

Minimum initial fields:

```json
{
  "minLabelClearancePx": 4,
  "legendBottomMarginPx": 8,
  "legendContentGapPx": 8,
  "titleOverflowTolerancePx": 0,
  "cardTextInsetPx": 12
}
```

#### 3.4 Fallback integrity

- if a standard template produces squeezed, clipped, or overcrowded output, the route contract must fall back to `freeflow` or a wrapped variant

The gate does not need to understand business meaning. It needs to prove structural completeness.

### Decision 4: Create a first-class `evals/` and failure-map layer

Introduce a lightweight evaluation layer dedicated to artifact quality.

Recommended contents:

- `evals/defect-taxonomy.json`
- `evals/export-scoring-schema.json`
- `evals/fixtures/` for small blueprint fixtures
- `evals/goldens/` for representative target outputs or snapshots

The durable source of truth should be machine-readable taxonomy data, not prose.

If a human-readable `failure-map.md` exists, it should be generated from that taxonomy and current test references, not hand-maintained.

Example categories:

- route mismatch
- canvas clipping
- legend intrusion
- label collision
- premature text wrapping
- actor/system semantic confusion
- dark-theme incomplete coverage
- sparse-input hallucination risk

This makes future regressions easier to classify and easier to prevent systematically without creating a stale markdown artifact.

### Decision 5: Add a cross-platform CLI compatibility track

Create a small but explicit compatibility layer in tests and docs for Windows/terminal behavior.

The first target is not full platform emulation. The first target is preventing avoidable shell/runtime assumptions.

Coverage should include:

- Windows-style paths and space-containing paths
- UTF-8 Chinese source material round-trips
- CRLF-safe JSON/HTML/SVG writes
- `python -m business_blueprint.cli` behavior as the canonical execution path
- stdout/stderr contract for `--validate`, `--plan`, `--project`, and `--export`

This mirrors the lesson from recent terminal/navigation bugs elsewhere: runtime assumptions break real users before core algorithms do.

### Explicitly Deferred Cases

Phase 2 does not attempt full Windows terminal parity.

Known deferred cases:

- PowerShell pipe quirks beyond documented CLI contract tests
- console-default encoding issues outside explicit UTF-8 execution paths

Accepted workaround for deferred encoding-sensitive runs:

- use `python -m business_blueprint.cli`
- set `PYTHONIOENCODING=utf-8` where needed

## Proposed Architecture

### Layer A: Artifact Contracts

No semantic change:

- blueprint authoring and validation remain upstream
- projection remains the only downstream machine contract
- viewer/handoff separation remains intact

### Layer B: Route Resolution

A dedicated route resolver decides:

- requested view family
- matched standard template, if any
- safety fallback, if needed

This resolver should be inspectable in tests without requiring full SVG diff assertions.

### Layer C: Shared Export Engine Utilities

Move reusable logic toward shared utilities:

- text width estimation and wrapping
- label collision avoidance
- safe-area and canvas sizing
- theme token resolution
- defs/reference tracking

These are engine concerns, not view concerns.

### Layer D: View Renderers

Keep each renderer focused on its own semantics:

- freeflow renderer
- architecture renderer(s)
- poster renderer
- swimlane renderer
- hierarchy renderer
- evolution renderer

Renderers should consume shared utilities rather than re-implementing placement heuristics.

### Layer E: Integrity Gate

Run shared structural validation after render assembly.

Possible outcomes:

- pass
- warn but allow
- fail and force route fallback

The gate should be deterministic and testable without visual inspection.

## Scope

This design is in scope for:

- skill contract hardening
- export pipeline hardening
- eval/failure-map introduction
- cross-platform CLI test expansion
- internal module boundary cleanup in export code

This design is out of scope for:

- rewriting the business blueprint schema
- changing projection ownership or downstream consumption rules
- redesigning the viewer as a new application
- introducing a new markdown planning artifact
- broad visual restyling unrelated to structural correctness

## Trade-Offs

### Why not keep adding one-off regression tests only?

That approach fixed many recent bugs, but it does not scale well. The same classes of failures reappear with slightly different shapes. A shared integrity gate and failure map give the tests a better organizing model.

### Why not consolidate overlapping views?

Because some specialized views still carry real value when they fit the request. The right design is not “keep every renderer forever,” but “retain a specialized renderer only when it provides meaningfully better structure than `freeflow` for a recognizable route family.”

### Why not introduce another planning artifact?

Because business-blueprint already has the right separation:

- semantic graph
- downstream narrative projection

Adding another durable layer would increase ambiguity without solving the current failure class.

## Risks

### Risk 1: Over-engineering the integrity gate

If the gate tries to infer too much semantic intent, it will become brittle.

Mitigation:
- keep checks structural
- keep route safety rules simple
- let view-specific tests cover nuanced aesthetics

### Risk 2: Export refactor causes short-term churn

Splitting shared engine logic from view renderers may cause temporary diff noise.

Mitigation:
- keep semantic behavior unchanged during extraction
- move helpers first, then tighten contracts
- rely on golden fixtures and current regressions before behavior changes

### Risk 3: Cross-platform tests become aspirational only

If platform coverage is described too broadly, the work may stall.

Mitigation:
- start with path, encoding, line-ending, and CLI contract cases
- avoid pretending we have full Windows GUI parity

## Success Criteria

This design is successful when:

1. Export route selection is explicit enough to test independently.
2. Shared integrity checks catch structural export failures before users do.
3. Known failure modes are represented in a machine-readable defect taxonomy tied to tests/evals.
4. CLI coverage explicitly protects Windows/path/encoding edge cases within the declared Phase 2 scope.
5. Export refactor leaves route resolution and renderer boundaries testable in isolation, with no renderer importing sibling renderer logic directly.

## Recommended Rollout

Roll out in four phases:

### Phase 1a: Contract Hardening

- define route contract
- define route eligibility matrix
- define terminal failure behavior

### Phase 1b: Structural Integrity Baseline

- add definition-reference checks
- add threshold configuration for geometry-sensitive checks

### Phase 1c: Eval Taxonomy Hardening

- define machine-readable defect taxonomy
- wire taxonomy to scoring schema and fixtures

### Phase 2: Test and Eval Hardening

- add eval fixtures
- add structural integrity tests in staged layers
- add cross-platform CLI coverage within declared limits

### Phase 3: Internal Refactor

- extract shared exporter utilities
- isolate renderer responsibilities
- keep behavior stable while reducing coupling

## Recommendation

Adopt this design as the next quality-hardening track for `kai-business-blueprint`.

It extends the current IR-first architecture instead of replacing it, and it directly addresses the class of failures exposed by recent real-world generation defects: not bad intent, but weak structural guarantees.
