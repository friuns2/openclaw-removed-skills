# Blueprint Cross-Skill Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a canonical blueprint projection surface in `kai-business-blueprint`, then teach `kai-report-creator` and `kai-slide-creator` to import that projection and generate their own native IR without parsing the raw blueprint graph.

**Architecture:** `kai-business-blueprint` becomes the sole owner of a derived `solution.projection.json` compatibility artifact produced by a new `--project` CLI path. `kai-report-creator` and `kai-slide-creator` add prompt-native blueprint/projection import handling that consumes that projection and stops at their native IR boundaries (`.report.md` and `PLANNING.md` respectively), preserving existing generation flows.

**Tech Stack:** Python 3.12 + argparse + pytest in `business-blueprint`; prompt-routed skill docs and markdown references in `kai-report-creator` and `slide-creator`.

---

### Task 1: Add The Canonical Projection Module In `kai-business-blueprint`

**Files:**
- Create: `business_blueprint/projection.py`
- Create: `tests/test_projection.py`
- Test: `tests/test_projection.py`

- [ ] **Step 1: Write the failing projection contract test**

```python
from pathlib import Path

from business_blueprint.projection import build_narrative_projection


def test_build_narrative_projection_returns_v1_contract(tmp_path: Path) -> None:
    blueprint = {
        "meta": {
            "title": "Retail Blueprint",
            "industry": "retail",
            "revisionId": "rev-20260420-01",
        },
        "context": {
            "goals": ["Reduce checkout queue time"],
            "scope": ["Store operations", "Member operations"],
            "assumptions": ["POS remains system of record"],
            "constraints": ["No ERP replacement in phase 1"],
            "clarifyRequests": [],
            "clarifications": [],
        },
        "library": {
            "capabilities": [
                {
                    "id": "cap-store",
                    "name": "Store Operations",
                    "description": "Run daily store operations",
                    "ownerActorIds": ["actor-manager"],
                    "supportingSystemIds": ["sys-pos"],
                }
            ],
            "actors": [{"id": "actor-manager", "name": "Store Manager"}],
            "flowSteps": [
                {
                    "id": "flow-checkout",
                    "name": "Checkout",
                    "actorId": "actor-manager",
                    "capabilityIds": ["cap-store"],
                    "systemIds": ["sys-pos"],
                    "stepType": "task",
                }
            ],
            "systems": [
                {
                    "id": "sys-pos",
                    "kind": "system",
                    "name": "POS",
                    "description": "Cashier system",
                    "capabilityIds": ["cap-store"],
                }
            ],
        },
    }

    projection = build_narrative_projection(
        blueprint,
        blueprint_path=tmp_path / "solution.blueprint.json",
    )

    assert projection["meta"]["adapterVersion"] == "v1"
    assert projection["summary"]["goals"] == ["Reduce checkout queue time"]
    assert projection["business"]["actors"][0]["storyRoles"] == ["operator"]
    assert projection["technology"]["systems"][0]["name"] == "POS"
    assert projection["provenance"]["blueprintHash"]
    assert projection["diagnostics"]["warnings"] == []
```

- [ ] **Step 2: Run the unit test to verify it fails**

Run: `pytest tests/test_projection.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'business_blueprint.projection'`

- [ ] **Step 3: Write the minimal projection module**

```python
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json


def default_projection_path(blueprint_path: Path) -> Path:
    if blueprint_path.name.endswith(".blueprint.json"):
        name = blueprint_path.name.replace(".blueprint.json", ".projection.json")
        return blueprint_path.with_name(name)
    return blueprint_path.with_name(f"{blueprint_path.stem}.projection.json")


def build_narrative_projection(
    blueprint: dict[str, Any],
    *,
    blueprint_path: Path | None = None,
) -> dict[str, Any]:
    meta = blueprint.get("meta", {})
    context = blueprint.get("context", {})
    library = blueprint.get("library", {})
    actors = {row["id"]: row for row in library.get("actors", [])}
    systems = {row["id"]: row for row in library.get("systems", [])}
    capabilities = library.get("capabilities", [])
    flow_steps = library.get("flowSteps", [])

    projection = {
        "meta": {
            "adapterVersion": "v1",
            "title": meta.get("title", "Untitled Blueprint"),
            "industry": meta.get("industry", "common"),
            "revisionId": meta.get("revisionId"),
            "generatedAt": meta.get("lastModifiedAt"),
        },
        "summary": {
            "goals": context.get("goals", []),
            "scope": context.get("scope", []),
            "assumptions": context.get("assumptions", []),
            "constraints": context.get("constraints", []),
            "openQuestions": [row.get("question", "") for row in context.get("clarifyRequests", [])],
        },
        "business": {
            "capabilityGroups": [
                {
                    "name": "Core Capabilities",
                    "capabilityIds": [row["id"] for row in capabilities],
                    "summary": "Primary capabilities extracted from the blueprint library.",
                }
            ],
            "keyCapabilities": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "summary": row.get("description", ""),
                    "ownerActors": [actors[aid]["name"] for aid in row.get("ownerActorIds", []) if aid in actors],
                    "supportingSystems": [systems[sid]["name"] for sid in row.get("supportingSystemIds", []) if sid in systems],
                }
                for row in capabilities
            ],
            "actors": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "storyRoles": ["operator"],
                }
                for row in actors.values()
            ],
            "coreFlows": [
                {
                    "name": "primary-flow",
                    "goal": context.get("goals", [""])[0] if context.get("goals") else "",
                    "primaryActor": actors.get(flow_steps[0].get("actorId", ""), {}).get("name", "") if flow_steps else "",
                    "stepSummaries": [row["name"] for row in flow_steps],
                    "capabilityIds": sorted({cap_id for row in flow_steps for cap_id in row.get("capabilityIds", [])}),
                    "systemIds": sorted({sys_id for row in flow_steps for sys_id in row.get("systemIds", [])}),
                }
            ] if flow_steps else [],
        },
        "technology": {
            "systems": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "kind": row.get("kind", "system"),
                    "summary": row.get("description", ""),
                    "supportsCapabilityIds": row.get("capabilityIds", []),
                }
                for row in systems.values()
            ],
            "systemLandscapeSummary": "Systems supporting the capabilities captured in the blueprint library.",
        },
        "narrativeHints": {
            "keyProblems": context.get("constraints", []),
            "keyDesignChoices": context.get("assumptions", []),
            "narrativeAngles": [
                {
                    "name": "capability-transformation",
                    "summary": "Frame the blueprint as an operating-model and system-support transformation.",
                    "aiGenerated": True,
                    "sourceRefs": ["context.goals", "library.capabilities", "library.flowSteps"],
                }
            ],
        },
        "provenance": {
            "blueprintPath": str(blueprint_path) if blueprint_path else "",
            "derivedFromRevisionId": meta.get("revisionId"),
            "blueprintHash": sha256(
                json.dumps(blueprint, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest(),
        },
        "diagnostics": {
            "warnings": [],
        },
    }
    if not projection["summary"]["goals"]:
        projection["diagnostics"]["warnings"].append(
            {
                "field": "summary.goals",
                "severity": "warning",
                "message": "No explicit business goals found in blueprint context.",
            }
        )
    return projection
```

- [ ] **Step 4: Run the unit test to verify it passes**

Run: `pytest tests/test_projection.py -q`
Expected: PASS

- [ ] **Step 5: Commit the projection module**

```bash
git add business_blueprint/projection.py tests/test_projection.py
git commit -m "feat: add canonical blueprint projection module"
```

### Task 2: Expose The Projection Through The CLI

**Files:**
- Modify: `business_blueprint/cli.py`
- Modify: `tests/test_cli_smoke.py`
- Modify: `tests/test_e2e.py`
- Test: `tests/test_cli_smoke.py`
- Test: `tests/test_e2e.py`

- [ ] **Step 1: Add failing CLI coverage for `--project`**

```python
def test_cli_help_lists_projection_command() -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    assert "--project" in result.stdout


def test_project_writes_default_projection_path(tmp_path: Path) -> None:
    blueprint_path = tmp_path / "solution.blueprint.json"
    blueprint_path.write_text(
        json.dumps(
            {
                "meta": {"title": "Test", "industry": "retail", "revisionId": "rev-1"},
                "context": {"goals": ["Shorten lines"]},
                "library": {"capabilities": [], "actors": [], "flowSteps": [], "systems": []},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = run_cli("--project", str(blueprint_path))

    assert result.returncode == 0
    assert (tmp_path / "solution.projection.json").exists()
```

- [ ] **Step 2: Run the CLI tests to verify they fail**

Run: `pytest tests/test_cli_smoke.py tests/test_e2e.py -q`
Expected: FAIL because `--project` is not in the parser and no projection file is created

- [ ] **Step 3: Wire the new CLI path**

```python
from .projection import build_narrative_projection, default_projection_path
from .model import load_json, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="business-blueprint")
    parser.add_argument("--plan", help="Generate only the canonical blueprint JSON.")
    parser.add_argument("--project", help="Generate canonical projection JSON for downstream skills.")
    parser.add_argument("--output", help="Optional output path for projection generation.")
    ...
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.project:
        blueprint_path = Path(args.project)
        projection = build_narrative_projection(
            load_json(blueprint_path),
            blueprint_path=blueprint_path,
        )
        output_path = Path(args.output) if args.output else default_projection_path(blueprint_path)
        write_json(output_path, projection)
        return 0
```

- [ ] **Step 4: Re-run the CLI tests**

Run: `pytest tests/test_cli_smoke.py tests/test_e2e.py -q`
Expected: PASS, including creation of `solution.projection.json`

- [ ] **Step 5: Commit the CLI surface**

```bash
git add business_blueprint/cli.py tests/test_cli_smoke.py tests/test_e2e.py
git commit -m "feat: add blueprint projection cli"
```

### Task 3: Update `kai-business-blueprint` Docs And Deprecate The Viewer Handoff As A Downstream Input

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Test: `tests/test_projection.py`
- Test: `tests/test_cli_smoke.py`
- Test: `tests/test_viewer.py`

- [ ] **Step 1: Update the skill command table and collaboration boundary**

```markdown
| `--project <path>` | Generate canonical projection JSON for downstream skills |

## Collaboration Boundary

This skill produces two distinct machine artifacts:

- `solution.handoff.json` — viewer manifest only, used by the editable viewer
- `solution.projection.json` — canonical narrative projection for downstream skills

Downstream skills should consume `solution.projection.json` or call `business-blueprint --project <blueprint.json>`.
Downstream skills should never use `solution.handoff.json` as a narrative source.
```

- [ ] **Step 2: Fix the README AI-agent examples**

```markdown
## For AI Agents

```bash
# Generate the canonical machine projection
business-blueprint --project solution.blueprint.json

# Then prompt downstream skills with the blueprint or projection artifact path
# Example prompt: "Use solution.blueprint.json to generate a report IR first."
# Example prompt: "Use solution.blueprint.json to generate a deck PLANNING.md first."
```

`solution.handoff.json` remains a viewer manifest and is not the cross-skill narrative contract.
```

- [ ] **Step 3: Add the same clarification to the Chinese README**

```markdown
`solution.handoff.json` 仅用于 viewer 清单，不是下游 skill 的 narrative adapter。
跨 skill 传递统一使用 `business-blueprint --project` 生成的 `solution.projection.json`。
```

- [ ] **Step 4: Run upstream smoke tests and a manual CLI check**

Run: `pytest tests/test_projection.py tests/test_cli_smoke.py tests/test_viewer.py -q`
Expected: PASS

Run: `python -m business_blueprint.cli --project demos/retail.blueprint.json --output /tmp/retail.projection.json`
Expected: `/tmp/retail.projection.json` exists and contains `adapterVersion`, `business`, and `diagnostics` keys

- [ ] **Step 5: Commit the upstream docs**

```bash
git add SKILL.md README.md README.zh-CN.md
git commit -m "docs: document canonical blueprint projection handoff"
```

### Task 4: Add Prompt-Native Blueprint Import To `kai-report-creator`

**Files:**
- Create: `/Users/song/.codex/skills/kai-report-creator/references/blueprint-import.md`
- Create: `/Users/song/.codex/skills/kai-report-creator/examples/business-blueprint.report.md`
- Modify: `/Users/song/.codex/skills/kai-report-creator/SKILL.md`
- Modify: `/Users/song/.codex/skills/kai-report-creator/README.md`
- Modify: `/Users/song/.codex/skills/kai-report-creator/README.zh-CN.md`
- Test: `/Users/song/.codex/skills/kai-report-creator/tests`

- [ ] **Step 1: Create a dedicated import reference instead of bloating `SKILL.md`**

```markdown
# Blueprint Import

When the user prompt contains a business blueprint JSON path, a projection JSON path, or clearly says the report should be generated from a business blueprint:

1. If the provided artifact ends with `.blueprint.json`, ensure a sibling `.projection.json` exists.
2. If the sibling projection is missing, instruct the agent to run:
   `business-blueprint --project <file>` as an internal preparation step.
3. Read the projection JSON, not the raw blueprint graph.
4. Generate `report-<slug>.report.md` with these sections:
   - Executive summary
   - Business goals and scope
   - Capability map and ownership
   - Core flows
   - System landscape
   - Assumptions, constraints, and open questions
   - Recommended next actions
5. If diagnostics contain only warnings and there is no substantive narrative data, write a skeleton IR with explicit placeholders instead of fabricating details.
6. Stop after saving the `.report.md` file. Rendering remains a separate step.
```

- [ ] **Step 2: Add the new prompt route to `SKILL.md`**

```markdown
description: ... Supports generating from raw notes, data, URLs, approved plan files, and business blueprint / projection JSON artifacts passed in the prompt.

| Input is a business blueprint / projection JSON artifact | Load `references/blueprint-import.md` and the projection JSON | Create a `.report.md` IR from a business blueprint, then stop for review. |
```

Also tighten the existing `--from <file>` row so it only covers raw content or existing IR, not blueprint imports.

- [ ] **Step 3: Add a concrete example IR and README examples**

```markdown
Use `solution.blueprint.json` to generate a report IR first. Do not render HTML yet.
Then render `report-solution.report.md` to HTML.
```

Example IR snippet:

```markdown
---
title: Retail Business Blueprint Report
theme: corporate-blue
lang: en
abstract: "A report generated from a business blueprint projection."
---

## Executive Summary

:::callout type=note
This report was generated from `solution.projection.json`.
:::

## Capability Map And Ownership

:::table caption="Core capabilities"
| Capability | Owner | Supporting systems |
|------------|-------|--------------------|
| Store Operations | Store Manager | POS |
:::
```

- [ ] **Step 4: Run tests and a manual import smoke**

Run: `python -m pytest /Users/song/.codex/skills/kai-report-creator/tests -q`
Expected: PASS

Manual skill smoke:

```text
请基于 /Users/song/projects/business-blueprint-skill/demos/retail.blueprint.json 生成一份 report IR，先不要出 HTML。
```

Expected: `report-retail.report.md` is created, includes capability/system sections, and does not invent KPI values that are absent from the projection

- [ ] **Step 5: Commit the report-skill import path**

```bash
git -C /Users/song/.codex/skills/kai-report-creator add SKILL.md README.md README.zh-CN.md references/blueprint-import.md examples/business-blueprint.report.md
git -C /Users/song/.codex/skills/kai-report-creator commit -m "feat: add blueprint import route for report ir"
```

### Task 5: Add Prompt-Native Blueprint Import To `slide-creator`

**Files:**
- Create: `/Users/song/projects/slide-creator/references/blueprint-import.md`
- Modify: `/Users/song/projects/slide-creator/SKILL.md`
- Modify: `/Users/song/projects/slide-creator/README.md`
- Modify: `/Users/song/projects/slide-creator/README.zh-CN.md`
- Modify: `/Users/song/projects/slide-creator/references/planning-template.md`
- Modify: `/Users/song/projects/slide-creator/references/workflow.md`
- Test: `/Users/song/projects/slide-creator/tests/test_doc_sync.py`

- [ ] **Step 1: Add a blueprint-specific planning reference**

```markdown
# Blueprint Import

When the user prompt contains a business blueprint JSON path, a projection JSON path, or clearly says the deck should be generated from a business blueprint:

1. If the provided artifact ends with `.blueprint.json`, ensure a sibling `.projection.json` exists.
2. If the sibling projection is missing, instruct the agent to run:
   `business-blueprint --project <file>` as an internal preparation step.
3. Read the projection JSON, not the raw blueprint graph.
4. Generate `PLANNING.md` with the default 8-slide arc:
   - Cover / transformation thesis
   - Current-state pain
   - Goals and scope
   - Capability map
   - Core business flow
   - System landscape
   - Design choices / operating model
   - Rollout / next steps
5. Stop after saving `PLANNING.md`. HTML generation still goes through `--generate`.
6. If projection diagnostics indicate sparse data, keep the 8-slide structure but mark missing sections explicitly in speaker notes instead of fabricating detail.
```

- [ ] **Step 2: Update `SKILL.md` prompt routing**

```markdown
description: ... Also supports business blueprint / projection JSON artifacts passed in the prompt when planning a deck.

| 业务蓝图 / projection JSON 输入 | `references/blueprint-import.md` + `references/planning-template.md` | 从业务蓝图生成 `PLANNING.md`，不生成 HTML |
```

Also add a note near `deck_type` routing that blueprint imports default to `user-content` with an 8-slide architecture/business-transformation arc unless the projection clearly supports expansion.

- [ ] **Step 3: Add traceability fields to the planning template and workflow**

```markdown
**Source Artifact**: solution.blueprint.json
**Projection Artifact**: solution.projection.json
**Source Revision**: rev-20260420-01
**Import Diagnostics**:
- none
```

Workflow addition:

```markdown
If the request is explicitly based on a business blueprint or projection artifact, skip Phase 1 content discovery and build `PLANNING.md` directly from the projection artifact.
```

- [ ] **Step 4: Update the English and Chinese READMEs and run doc checks**

Run: `python /Users/song/projects/slide-creator/check-doc-sync.py --root /Users/song/projects/slide-creator --dry-run`
Expected: PASS

Run: `pytest /Users/song/projects/slide-creator/tests/test_doc_sync.py -q`
Expected: PASS

Manual skill smoke:

```text
请基于 /Users/song/projects/business-blueprint-skill/demos/retail.blueprint.json 生成 deck 的 PLANNING.md，先不要生成 HTML。
```

Expected: `PLANNING.md` is created with an 8-slide arc that includes capability map, core flow, and system landscape slides

- [ ] **Step 5: Commit the slide import route**

```bash
git -C /Users/song/projects/slide-creator add SKILL.md README.md README.zh-CN.md references/blueprint-import.md references/planning-template.md references/workflow.md
git -C /Users/song/projects/slide-creator commit -m "feat: add blueprint import route for slide planning"
```

### Task 6: Run The End-To-End Cross-Skill Smoke

**Files:**
- Test: `demos/retail.blueprint.json`
- Test: `/tmp/retail.projection.json`
- Test: `/Users/song/.codex/skills/kai-report-creator/report-retail.report.md`
- Test: `/Users/song/projects/slide-creator/PLANNING.md`

- [ ] **Step 1: Generate a fresh canonical projection from the upstream demo**

Run: `python -m business_blueprint.cli --project demos/retail.blueprint.json --output /tmp/retail.projection.json`
Expected: PASS and `/tmp/retail.projection.json` exists

- [ ] **Step 2: Smoke-test the report import**

```text
请基于 /Users/song/projects/business-blueprint-skill/demos/retail.blueprint.json 生成一份 report IR，先不要出 HTML。
```

Expected: a `.report.md` file is written first, with no fabricated quantitative claims

- [ ] **Step 3: Smoke-test the slide import**

```text
请基于 /Users/song/projects/business-blueprint-skill/demos/retail.blueprint.json 生成 deck 的 PLANNING.md，先不要生成 HTML。
```

Expected: `PLANNING.md` is written first, with the 8-slide blueprint arc instead of a generic product deck

- [ ] **Step 4: Verify downstream boundaries stay intact**

Run: `rg -n -- "solution\\.handoff\\.json|--from-blueprint|raw blueprint graph|library\\.capabilities" /Users/song/.codex/skills/kai-report-creator /Users/song/projects/slide-creator`
Expected: no downstream doc path tells the agent to use `solution.handoff.json` as the narrative source, no prompt contract depends on a `--from-blueprint` flag, and no instructions tell the agent to parse the raw blueprint graph directly

- [ ] **Step 5: Record the verification results**

```bash
printf "blueprint-cross-skill-smoke-ok\n"
```

Expected: `blueprint-cross-skill-smoke-ok`
