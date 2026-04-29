#!/usr/bin/env python3
"""Compare the current validator against the v0.1.0 baseline validator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from _test_mutators import append_suggestions, ensure_legacy_budget, replace_line, replace_once


ROOT = Path(__file__).resolve().parent.parent
CURRENT_VALIDATOR = ROOT / "scripts" / "validate_suggestions.py"
BASELINE_VALIDATOR = ROOT / "scripts" / "baselines" / "validate_suggestions_v0_1_0.py"
CANONICAL = ROOT / "references" / "suggestion-contract.md"
REPORT_PATH = ROOT / "assets" / "ablation_report.json"
TIMEOUT_SECONDS = 10


def mutate(text: str, case_id: str) -> str:
    if case_id == "canonical":
        return text
    if case_id == "valid_optional_fields":
        text = replace_line(text, "visibility", "show_on_next_relevant_turn")
        text = replace_line(text, "trigger_reason", "heartbeat")
        return replace_line(text, "reuse_gate", "min_4_of_5_axes_and_ttl_valid")
    if case_id == "low_mode_two_suggestions":
        return append_suggestions(text, 2)
    if case_id == "medium_mode_four_suggestions":
        text = replace_line(text, "search_mode", "medium")
        return append_suggestions(text, 4)
    if case_id == "invalid_confidence":
        return replace_line(text, "confidence", "certain")
    if case_id == "ttl_too_long":
        return replace_line(text, "expires_at", "2026-05-10T03:00:00+08:00")
    if case_id == "invalid_visibility":
        return replace_line(text, "visibility", "always_show")
    if case_id == "invalid_trigger_reason":
        return replace_line(text, "trigger_reason", "manual_override")
    if case_id == "invalid_reuse_gate":
        return replace_line(text, "reuse_gate", "ttl_valid_only")
    if case_id == "invalid_source_scope_part":
        return replace_line(text, "source_scope", "primary+quaternary")
    if case_id == "evidence_outside_source_scope":
        return replace_once(
            text,
            "- secondary_community: https://example.com/community-thread",
            "- tertiary_community: https://example.com/community-thread",
        )
    if case_id == "invalid_fingerprint_hash":
        return replace_line(text, "fingerprint_hash", "h64:xyz")
    if case_id == "short_problem_fingerprint":
        return replace_line(text, "problem_fingerprint", "host|symptom|version")
    if case_id == "invalid_dates":
        return replace_line(text, "expires_at", "2026-04-18T03:00:00+08:00")
    if case_id == "missing_timezone":
        return replace_line(text, "generated_at", "2026-04-20T03:00:00")
    if case_id == "no_independent_evidence":
        return replace_once(
            text,
            "- secondary_community: https://example.com/community-thread",
            "- primary_official_discussion: https://example.com/maintainer-thread",
        )
    if case_id == "empty_fit_reason":
        return replace_line(text, "fit_reason", "")
    if case_id == "misplaced_top_level_visibility":
        needle = "fit_reason: This fits when the user already edited the skill locally and needs a fast low-risk check before more changes.\n"
        return replace_once(text, needle, needle + "visibility: silent_until_relevant\n")
    if case_id == "malformed_evidence_item":
        return replace_once(
            text,
            "- secondary_community: https://example.com/community-thread",
            "- secondary_community\n",
        )
    raise ValueError(f"unknown case: {case_id}")


CASES = [
    {"id": "canonical", "kind": "safe"},
    {"id": "valid_optional_fields", "kind": "safe"},
    {"id": "low_mode_two_suggestions", "kind": "guardrail"},
    {"id": "medium_mode_four_suggestions", "kind": "guardrail"},
    {"id": "invalid_confidence", "kind": "guardrail"},
    {"id": "ttl_too_long", "kind": "guardrail"},
    {"id": "invalid_visibility", "kind": "guardrail"},
    {"id": "invalid_trigger_reason", "kind": "guardrail"},
    {"id": "invalid_reuse_gate", "kind": "guardrail"},
    {"id": "invalid_source_scope_part", "kind": "guardrail"},
    {"id": "evidence_outside_source_scope", "kind": "guardrail"},
    {"id": "invalid_fingerprint_hash", "kind": "guardrail"},
    {"id": "short_problem_fingerprint", "kind": "guardrail"},
    {"id": "missing_timezone", "kind": "guardrail"},
    {"id": "no_independent_evidence", "kind": "guardrail"},
    {"id": "empty_fit_reason", "kind": "guardrail"},
    {"id": "misplaced_top_level_visibility", "kind": "guardrail"},
    {"id": "malformed_evidence_item", "kind": "guardrail"},
    {"id": "invalid_dates", "kind": "shared-invalid"},
]


def invoke(validator: Path, target: Path) -> dict[str, object]:
    try:
        proc = subprocess.run(
            [sys.executable, str(validator), str(target)],
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
        output = (proc.stdout + proc.stderr).strip()
        crashed = "Traceback" in output
        passed = proc.returncode == 0
    except subprocess.TimeoutExpired:
        output = f"TIMEOUT after {TIMEOUT_SECONDS}s"
        crashed = True
        passed = False
    return {
        "passed": passed,
        "output": output,
        "crashed": crashed,
    }


def rate(items: list[dict[str, object]], predicate) -> float:
    if not items:
        return 0.0
    return sum(1 for item in items if predicate(item)) / len(items)


def main() -> int:
    canonical = CANONICAL.read_text(encoding="utf-8")
    case_results = []
    with tempfile.TemporaryDirectory(prefix="agent-travel-ablation-") as temp:
        temp_dir = Path(temp)
        for case in CASES:
            target = temp_dir / f"{case['id']}.md"
            current_case = mutate(canonical, case["id"])
            target.write_text(current_case, encoding="utf-8")
            baseline_target = temp_dir / f"{case['id']}.baseline.md"
            baseline_target.write_text(ensure_legacy_budget(current_case), encoding="utf-8")
            baseline = invoke(BASELINE_VALIDATOR, baseline_target)
            current = invoke(CURRENT_VALIDATOR, target)
            case_results.append(
                {
                    "case": case["id"],
                    "kind": case["kind"],
                    "baseline_passed": baseline["passed"],
                    "current_passed": current["passed"],
                    "baseline_crashed": baseline["crashed"],
                    "current_crashed": current["crashed"],
                }
            )

    guardrail_cases = [item for item in case_results if item["kind"] == "guardrail"]
    safe_cases = [item for item in case_results if item["kind"] == "safe"]
    shared_invalid_cases = [item for item in case_results if item["kind"] == "shared-invalid"]
    report = {
        "baseline_ref": "v0.1.0-local-baseline",
        "current_ref": "agent-travel-current",
        "summary": {
            "baseline_guardrail_rejection_rate": rate(guardrail_cases, lambda item: not item["baseline_passed"]),
            "current_guardrail_rejection_rate": rate(guardrail_cases, lambda item: not item["current_passed"]),
            "baseline_safe_acceptance_rate": rate(safe_cases, lambda item: item["baseline_passed"]),
            "current_safe_acceptance_rate": rate(safe_cases, lambda item: item["current_passed"]),
            "baseline_shared_invalid_rejection_rate": rate(
                shared_invalid_cases,
                lambda item: not item["baseline_passed"],
            ),
            "current_shared_invalid_rejection_rate": rate(
                shared_invalid_cases,
                lambda item: not item["current_passed"],
            ),
        },
        "cases": case_results,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    current_summary = report["summary"]
    return 0 if (
        current_summary["current_guardrail_rejection_rate"] == 1.0
        and current_summary["current_safe_acceptance_rate"] == 1.0
        and current_summary["current_shared_invalid_rejection_rate"] == 1.0
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
