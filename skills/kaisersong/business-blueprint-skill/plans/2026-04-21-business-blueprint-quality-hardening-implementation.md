# Business Blueprint Quality Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden `kai-business-blueprint` so export routing, export integrity, eval taxonomy, and cross-platform CLI behavior are explicit, testable, and less coupled.

**Architecture:** Keep `solution.blueprint.json` and `solution.projection.json` unchanged as the only durable machine contracts. Add a new route-resolution layer and export-integrity layer around the existing SVG/HTML export path, then move reusable exporter logic into shared modules so route choice, integrity checks, and renderers can evolve independently.

**Tech Stack:** Python 3.12 + argparse + pytest + JSON fixtures in `business_blueprint`; markdown/json reference artifacts under `plans/`, `evals/`, and `references/`.

---

### Task 1: Lock The Reviewed Contract In Docs And Fixtures

**Files:**
- Modify: `SKILL.md`
- Modify: `references/architecture-design-system.md`
- Create: `evals/export-integrity-thresholds.json`
- Create: `evals/defect-taxonomy.json`
- Create: `evals/export-scoring-schema.json`
- Test: `tests/test_architecture_skill_contract.py`

- [ ] **Step 1: Add failing contract tests for the new reviewed decisions**

Add assertions to `tests/test_architecture_skill_contract.py` for:
- route eligibility matrix language
- terminal export failure behavior
- machine-readable threshold file references
- deferred Windows/terminal scope language
- defect taxonomy as the durable source instead of hand-maintained `failure-map.md`

- [ ] **Step 2: Run the contract test subset and confirm it fails**

Run: `pytest tests/test_architecture_skill_contract.py -q`
Expected: FAIL because the new route-matrix / thresholds / deferred-scope language does not exist yet.

- [ ] **Step 3: Update the skill and design-system docs**

Document these points in `SKILL.md` and `references/architecture-design-system.md`:
- route families and explicit eligibility/fallback policy
- `freeflow` as the universal fallback, plus terminal non-zero failure when even fallback output is structurally invalid
- geometry-sensitive integrity checks must use threshold configuration, not prose heuristics
- Windows support scope is limited in Phase 2, with `python -m business_blueprint.cli` and `PYTHONIOENCODING=utf-8` as the documented workaround path

- [ ] **Step 4: Create the new machine-readable eval artifacts**

Create:
- `evals/export-integrity-thresholds.json`
- `evals/defect-taxonomy.json`
- `evals/export-scoring-schema.json`

Minimum threshold seed:

```json
{
  "minLabelClearancePx": 4,
  "legendBottomMarginPx": 8,
  "legendContentGapPx": 8,
  "titleOverflowTolerancePx": 0,
  "cardTextInsetPx": 12
}
```

Minimum taxonomy seed categories:

```json
[
  "route_mismatch",
  "defs_reference_missing",
  "canvas_clipping",
  "legend_intrusion",
  "label_collision",
  "premature_text_wrapping",
  "actor_system_semantic_confusion",
  "dark_theme_incomplete_coverage",
  "sparse_input_hallucination_risk"
]
```

- [ ] **Step 5: Re-run the contract tests**

Run: `pytest tests/test_architecture_skill_contract.py -q`
Expected: PASS

- [ ] **Step 6: Commit the contract layer**

```bash
git add SKILL.md references/architecture-design-system.md evals/export-integrity-thresholds.json evals/defect-taxonomy.json evals/export-scoring-schema.json tests/test_architecture_skill_contract.py
git commit -m "docs: lock export integrity and eval contracts"
```

### Task 2: Add Explicit Export Route Resolution

**Files:**
- Create: `business_blueprint/export_routes.py`
- Modify: `business_blueprint/export_svg.py`
- Modify: `business_blueprint/cli.py`
- Create: `tests/test_export_routes.py`
- Test: `tests/test_export_routes.py`

- [ ] **Step 1: Write failing route-resolution tests**

Cover:
- any valid blueprint defaults to `freeflow`
- architecture-shaped blueprints resolve to `architecture-template`
- chronology/staged blueprints resolve to `evolution`
- route result includes `route`, `reason`, `fallback_route`, and `terminal_behavior`

Example expectation shape:

```python
decision = resolve_export_route(blueprint, requested_route=None)
assert decision.route == "freeflow"
assert decision.fallback_route is None
assert decision.terminal_behavior == "error"
```

- [ ] **Step 2: Run the route test file and confirm it fails**

Run: `pytest tests/test_export_routes.py -q`
Expected: FAIL with missing module or missing resolver symbols.

- [ ] **Step 3: Create the route resolver module**

Implement `business_blueprint/export_routes.py` with:
- a small `ExportRouteDecision` dataclass
- a `resolve_export_route()` function
- explicit route-family constants
- initial structural predicates for `freeflow`, `architecture-template`, `poster`, `swimlane`, `hierarchy`, and `evolution`

Keep this first cut deliberately conservative. If a specialized route is not clearly eligible, return `freeflow`.

- [ ] **Step 4: Integrate route resolution into the export path**

Modify `business_blueprint/export_svg.py` and `business_blueprint/cli.py` so that:
- route resolution happens before renderer selection
- the chosen route can be tested independently from the SVG output
- current user-facing behavior stays stable unless a route is clearly eligible

- [ ] **Step 5: Re-run route tests**

Run: `pytest tests/test_export_routes.py -q`
Expected: PASS

- [ ] **Step 6: Commit route resolution**

```bash
git add business_blueprint/export_routes.py business_blueprint/export_svg.py business_blueprint/cli.py tests/test_export_routes.py
git commit -m "feat: add explicit export route resolution"
```

### Task 3: Add Definition-Integrity Checks First

**Files:**
- Create: `business_blueprint/export_integrity.py`
- Modify: `business_blueprint/export_svg.py`
- Create: `tests/test_export_integrity.py`
- Test: `tests/test_export_integrity.py`

- [ ] **Step 1: Write failing tests for defs/reference integrity**

Cover:
- missing `marker-end="url(#...)"` target is detected
- missing gradient/pattern/filter references are detected
- valid defs pass cleanly

Expected API shape:

```python
result = check_svg_definition_integrity(svg_text)
assert result.errors == [{"kind": "missing_def", "ref": "arrow-solid"}]
```

- [ ] **Step 2: Run the integrity test file and confirm it fails**

Run: `pytest tests/test_export_integrity.py -q`
Expected: FAIL because the integrity module does not exist yet.

- [ ] **Step 3: Implement the pure structural integrity pass**

Implement in `business_blueprint/export_integrity.py`:
- parsing of referenced ids from `url(#...)`
- parsing of defined ids from `<marker>`, gradients, patterns, filters, and other defs nodes
- a small result object with `errors` and `warnings`

Do not add geometry checks yet. This phase is definition-only.

- [ ] **Step 4: Wire the check into export assembly**

Modify the export path so the integrity result is available immediately after SVG assembly and before the artifact is finalized.

At this stage:
- structural definition failures should return a non-zero CLI outcome or raise a typed error in library mode
- no fallback logic is added yet

- [ ] **Step 5: Re-run the integrity tests**

Run: `pytest tests/test_export_integrity.py -q`
Expected: PASS

- [ ] **Step 6: Commit definition integrity**

```bash
git add business_blueprint/export_integrity.py business_blueprint/export_svg.py tests/test_export_integrity.py
git commit -m "feat: add svg definition integrity checks"
```

### Task 4: Add Geometry Integrity And Fallback Cascade

**Files:**
- Modify: `business_blueprint/export_integrity.py`
- Modify: `business_blueprint/export_svg.py`
- Modify: `tests/test_exporters.py`
- Modify: `tests/test_svg_quality.py`
- Test: `tests/test_exporters.py`
- Test: `tests/test_svg_quality.py`

- [ ] **Step 1: Add failing geometry-integrity tests**

Cover:
- canvas must include the last content row, legend, and footer
- legend must stay inside the bottom safe area
- title overflow tolerance is zero
- route fallback triggers when a specialized route exceeds density/safety constraints
- terminal failure occurs when even `freeflow` cannot pass integrity

- [ ] **Step 2: Run the geometry test subset and confirm it fails**

Run: `pytest tests/test_exporters.py tests/test_svg_quality.py -q`
Expected: FAIL because threshold-driven integrity and fallback behavior are not implemented yet.

- [ ] **Step 3: Load thresholds from `evals/export-integrity-thresholds.json`**

Implement a small loader in `business_blueprint/export_integrity.py` and use it for:
- label clearance
- legend spacing
- title overflow tolerance
- any initial safe-area calculations

- [ ] **Step 4: Implement geometry checks in the integrity layer**

Add checks for:
- canvas bottom/right coverage
- legend placement bounds
- title overflow
- minimum label clearance near elbows/cards where the geometry can be measured reliably

Keep this deterministic and numeric. Do not attempt semantic aesthetic scoring.

- [ ] **Step 5: Implement fallback cascade in route execution**

Behavior:
- if a specialized route fails geometry integrity, fall back to its configured fallback route
- if `freeflow` also fails integrity, return a structural diagnostics error and non-zero exit

Ensure the diagnostics payload reports:
- requested route
- attempted route
- fallback route
- terminal reason

- [ ] **Step 6: Re-run exporter and quality tests**

Run: `pytest tests/test_exporters.py tests/test_svg_quality.py -q`
Expected: PASS

- [ ] **Step 7: Commit geometry integrity**

```bash
git add business_blueprint/export_integrity.py business_blueprint/export_svg.py tests/test_exporters.py tests/test_svg_quality.py
git commit -m "feat: add geometry integrity checks and route fallback"
```

### Task 5: Add Eval Taxonomy And Fixture Coverage

**Files:**
- Create: `evals/fixtures/route-freeflow.json`
- Create: `evals/fixtures/route-architecture.json`
- Create: `evals/fixtures/route-evolution.json`
- Create: `evals/README.md`
- Modify: `tests/test_export_routes.py`
- Modify: `tests/test_export_integrity.py`
- Test: `tests/test_export_routes.py`
- Test: `tests/test_export_integrity.py`

- [ ] **Step 1: Create small blueprint fixtures for route and integrity cases**

Each fixture should isolate one case:
- ambiguous graph -> `freeflow`
- clear layered architecture -> `architecture-template`
- chronological staged flow -> `evolution`
- intentionally broken defs/canvas examples when needed for integrity tests

- [ ] **Step 2: Tie defect taxonomy to tests**

Extend tests so important failures mention taxonomy ids directly, for example:
- `defs_reference_missing`
- `canvas_clipping`
- `legend_intrusion`

This keeps the machine-readable taxonomy connected to actual regression coverage.

- [ ] **Step 3: Add a short eval README**

Document:
- what each fixture is for
- which taxonomy ids it covers
- which tests consume it

Do not introduce a hand-maintained `failure-map.md` source file.

- [ ] **Step 4: Re-run the eval-linked test subset**

Run: `pytest tests/test_export_routes.py tests/test_export_integrity.py -q`
Expected: PASS

- [ ] **Step 5: Commit the eval layer**

```bash
git add evals tests/test_export_routes.py tests/test_export_integrity.py
git commit -m "test: add export eval fixtures and defect taxonomy coverage"
```

### Task 6: Expand CLI And E2E Coverage For Cross-Platform Cases

**Files:**
- Create: `tests/test_cli_cross_platform.py`
- Modify: `tests/test_cli_smoke.py`
- Modify: `tests/test_e2e.py`
- Test: `tests/test_cli_cross_platform.py`
- Test: `tests/test_cli_smoke.py`
- Test: `tests/test_e2e.py`

- [ ] **Step 1: Write failing CLI compatibility tests**

Cover:
- blueprint paths with spaces
- Windows-style path strings normalized or handled safely
- UTF-8 Chinese source text round-trip through `--plan`
- JSON/HTML/SVG writes remain readable under CRLF line endings
- stdout/stderr contracts for `--validate`, `--plan`, `--project`, and `--export`

- [ ] **Step 2: Run the CLI compatibility subset and confirm it fails**

Run: `pytest tests/test_cli_cross_platform.py tests/test_cli_smoke.py tests/test_e2e.py -q`
Expected: FAIL on at least one path/encoding/contract case.

- [ ] **Step 3: Fix CLI assumptions without broad shell-specific logic**

Modify `business_blueprint/cli.py` and any helper modules only as needed so that:
- `python -m business_blueprint.cli` remains the canonical tested entry path
- path handling does not assume POSIX separators
- Unicode and line-ending-sensitive writes are explicit and deterministic

Do not claim full PowerShell parity. Keep behavior within the documented Phase 2 scope.

- [ ] **Step 4: Re-run the CLI compatibility subset**

Run: `pytest tests/test_cli_cross_platform.py tests/test_cli_smoke.py tests/test_e2e.py -q`
Expected: PASS

- [ ] **Step 5: Commit the CLI coverage**

```bash
git add business_blueprint/cli.py tests/test_cli_cross_platform.py tests/test_cli_smoke.py tests/test_e2e.py
git commit -m "test: cover cross-platform cli path and encoding behavior"
```

### Task 7: Refactor Exporter Internals Without Changing Contracts

**Files:**
- Create: `business_blueprint/export_text.py`
- Create: `business_blueprint/export_theme.py`
- Modify: `business_blueprint/export_svg.py`
- Modify: `business_blueprint/export_routes.py`
- Modify: `business_blueprint/export_integrity.py`
- Test: `tests/test_exporters.py`
- Test: `tests/test_svg_quality.py`
- Test: `tests/test_export_routes.py`
- Test: `tests/test_export_integrity.py`

- [ ] **Step 1: Extract shared text and theme helpers**

Move only obviously shared utilities:
- text width estimation
- width-aware wrapping
- theme token resolution

Do not move renderer-specific layout code yet.

- [ ] **Step 2: Re-run the export test subset**

Run: `pytest tests/test_exporters.py tests/test_svg_quality.py tests/test_export_routes.py tests/test_export_integrity.py -q`
Expected: PASS

- [ ] **Step 3: Extract any remaining route-agnostic helpers**

Possible candidates:
- safe-area sizing helpers
- common diagnostics assembly
- non-renderer-specific defs tracking

Do not allow one renderer to import implementation details from another renderer.

- [ ] **Step 4: Re-run the export test subset again**

Run: `pytest tests/test_exporters.py tests/test_svg_quality.py tests/test_export_routes.py tests/test_export_integrity.py -q`
Expected: PASS

- [ ] **Step 5: Run the full test suite**

Run: `pytest tests -q`
Expected: PASS across the full repo.

- [ ] **Step 6: Commit the internal refactor**

```bash
git add business_blueprint/export_text.py business_blueprint/export_theme.py business_blueprint/export_svg.py business_blueprint/export_routes.py business_blueprint/export_integrity.py tests
git commit -m "refactor: separate export routing integrity and shared helpers"
```

### Task 8: Final Documentation Sync

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `plans/2026-04-21-business-blueprint-quality-hardening.md`
- Test: `pytest tests -q`

- [ ] **Step 1: Update README surfaces**

Document:
- explicit route resolution
- export integrity behavior
- machine-readable eval artifacts
- declared Windows/terminal scope and workaround

- [ ] **Step 2: Mark the reviewed design as adopted**

Update `plans/2026-04-21-business-blueprint-quality-hardening.md` from `Proposed` to the appropriate post-implementation status once the work lands.

- [ ] **Step 3: Re-run the full suite**

Run: `pytest tests -q`
Expected: PASS

- [ ] **Step 4: Commit docs sync**

```bash
git add README.md README.zh-CN.md plans/2026-04-21-business-blueprint-quality-hardening.md
git commit -m "docs: describe export integrity and route contracts"
```

## Spec Coverage Check

- Route eligibility matrix: covered by Task 2.
- Definition integrity: covered by Task 3.
- Threshold-driven geometry integrity and fallback cascade: covered by Task 4.
- Machine-readable taxonomy/evals: covered by Task 1 and Task 5.
- Cross-platform CLI scope: covered by Task 6.
- Exporter boundary cleanup: covered by Task 7.

No proposal section is left without an implementation task.

## Notes For Execution

- Keep renderer behavior stable until Task 4. Do not mix route refactor, geometry heuristics, and helper extraction in one change.
- If `freeflow` terminal failures show up on existing fixtures, fix the integrity thresholds or the freeflow renderer before enabling non-zero terminal behavior by default.
- Do not create a hand-maintained `failure-map.md` source artifact. If a markdown report is needed later, generate it from taxonomy data and test references.
