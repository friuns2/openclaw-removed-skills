#!/usr/bin/env python3
"""Validate the canonical agent-travel suggestion block."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


START = "<!-- agent-travel:suggestions:start -->"
END = "<!-- agent-travel:suggestions:end -->"
TOP_LEVEL_REQUIRED = {
    "generated_at",
    "expires_at",
    "search_mode",
    "tool_preference",
    "source_scope",
    "thread_scope",
    "problem_fingerprint",
    "advisory_only",
}
TOP_LEVEL_OPTIONAL = {
    "trigger_reason",
    "visibility",
    "fingerprint_hash",
    "reuse_gate",
    "budget",
}
ITEM_REQUIRED = {
    "title",
    "applies_when",
    "hint",
    "confidence",
    "manual_check",
    "solves_point",
    "new_idea",
    "fit_reason",
    "match_reasoning",
    "version_scope",
    "do_not_apply_when",
}
ALLOWED_LEVELS = {"low", "medium", "high"}
ALLOWED_TOOL_PREFERENCES = {"public-only", "all-available", "custom"}
ALLOWED_VISIBILITY = {"silent_until_relevant", "show_on_next_relevant_turn"}
ALLOWED_SOURCE_SCOPE_PARTS = {"primary", "secondary", "tertiary"}
ALLOWED_TRIGGER_REASONS = {
    "heartbeat",
    "scheduled",
    "task_end",
    "failure_recovery",
    "idle_fallback",
}
ALLOWED_REUSE_GATES = {"min_4_of_5_axes_and_ttl_valid"}
SUGGESTION_LIMITS = {"low": 1, "medium": 3, "high": 5}
MAX_TTL = timedelta(days=14)
FINGERPRINT_HASH_PATTERN = re.compile(r"^(?:h64|sha256):[0-9a-f]{64}$")
MATCH_AXES = {
    "host",
    "version",
    "symptom",
    "constraint_pattern",
    "desired_next_outcome",
}
MATCH_AXIS_ALIASES = {
    "constraint": "constraint_pattern",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Path to a markdown file containing suggestion markers")
    return parser.parse_args()


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


def parse_iso(value: str) -> datetime:
    if not value.strip():
        raise ValueError("timestamp must be non-empty")
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone offset")
    return parsed


def normalize_part(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def split_scope(value: str) -> set[str]:
    return {normalize_part(part) for part in re.split(r"[^A-Za-z0-9]+", value) if part.strip()}


def canonicalize_axis(axis: str) -> str:
    normalized = normalize_part(axis)
    return MATCH_AXIS_ALIASES.get(normalized, normalized)


def parse_evidence_source(item: str) -> tuple[str, str]:
    label, separator, reference = str(item).partition(":")
    normalized_label = normalize_part(label)
    normalized_reference = reference.strip() if separator else ""
    if normalized_reference:
        parsed = urlparse(normalized_reference)
        if parsed.scheme and parsed.netloc:
            host = parsed.netloc.lower()
            path = parsed.path.rstrip("/")
            query = f"?{parsed.query}" if parsed.query else ""
            normalized_reference = f"{host}{path}{query}"
    return normalized_label, normalized_reference


def parse_block(path: Path) -> tuple[dict[str, str], list[dict[str, object]], list[str]]:
    text = path.read_text(encoding="utf-8")
    start = text.rfind(START)
    end = text.rfind(END)
    if start == -1 or end == -1 or end <= start:
        return {}, [], ["missing or invalid agent-travel markers"]

    block = text[start + len(START) : end].strip()
    lines = [line.rstrip() for line in block.splitlines()]
    errors: list[str] = []
    top_level: dict[str, str] = {}
    suggestions: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    current_evidence: list[str] | None = None
    current_match_reasoning: list[str] | None = None

    key_pattern = re.compile(r"^([a-z_]+):\s*(.*)$")
    heading_pattern = re.compile(r"^##\s+suggestion-\d+\s*$")

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("# agent-travel suggestions"):
            continue
        if heading_pattern.match(line):
            current = {"evidence": [], "match_reasoning": []}
            suggestions.append(current)
            current_evidence = None
            current_match_reasoning = None
            continue
        if line == "evidence:":
            if current is None:
                errors.append("found evidence block before any suggestion heading")
                continue
            current_evidence = current["evidence"]  # type: ignore[assignment]
            current_match_reasoning = None
            continue
        if line == "match_reasoning:":
            if current is None:
                errors.append("found match_reasoning block before any suggestion heading")
                continue
            current_match_reasoning = current["match_reasoning"]  # type: ignore[assignment]
            current_evidence = None
            continue
        if line.startswith("- "):
            if current_evidence is not None:
                current_evidence.append(line[2:].strip())
                continue
            if current_match_reasoning is not None:
                current_match_reasoning.append(line[2:].strip())
                continue
            errors.append(f"unexpected list item outside block: {line}")
            continue

        match = key_pattern.match(line)
        if not match:
            errors.append(f"unrecognized line: {line}")
            current_evidence = None
            current_match_reasoning = None
            continue

        key, value = match.groups()
        current_evidence = None
        current_match_reasoning = None
        if current is None:
            if key in ITEM_REQUIRED:
                errors.append(f"suggestion field {key} must appear under a suggestion heading")
                continue
            top_level[key] = value
        else:
            if key in TOP_LEVEL_REQUIRED or key in TOP_LEVEL_OPTIONAL:
                errors.append(f"top-level field {key} must appear before the first suggestion heading")
                continue
            current[key] = value

    return top_level, suggestions, errors


def suggestion_limit(top_level: dict[str, str]) -> int | None:
    values = []
    for key in ("budget", "search_mode"):
        value = top_level.get(key)
        if value in SUGGESTION_LIMITS:
            values.append(SUGGESTION_LIMITS[value])
    return min(values) if values else None


def validate_top_level(top_level: dict[str, str], suggestion_count: int) -> list[str]:
    errors: list[str] = []
    missing = sorted(TOP_LEVEL_REQUIRED - set(top_level))
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")
        return errors

    if top_level.get("advisory_only", "").lower() != "true":
        errors.append("advisory_only must be true")
    if top_level.get("thread_scope") != "active_conversation_only":
        errors.append("thread_scope must be active_conversation_only")
    for field in sorted(TOP_LEVEL_REQUIRED - {"advisory_only"}):
        if not top_level.get(field, "").strip():
            errors.append(f"{field} must be non-empty")

    budget = top_level.get("budget", "")
    if budget and budget not in ALLOWED_LEVELS:
        errors.append("budget must be one of: low, medium, high")
    search_mode = top_level.get("search_mode", "")
    if search_mode not in ALLOWED_LEVELS:
        errors.append("search_mode must be one of: low, medium, high")
    if budget and search_mode and budget != search_mode:
        errors.append("budget must match search_mode when both are present")
    tool_preference = top_level.get("tool_preference", "")
    if tool_preference not in ALLOWED_TOOL_PREFERENCES:
        errors.append("tool_preference must be one of: all-available, custom, public-only")

    source_scope = split_scope(top_level.get("source_scope", ""))
    if "primary" not in source_scope:
        errors.append("source_scope must include primary")
    invalid_source_scope = sorted(source_scope - ALLOWED_SOURCE_SCOPE_PARTS)
    if invalid_source_scope:
        errors.append(f"source_scope contains unsupported tiers: {', '.join(invalid_source_scope)}")

    visibility = top_level.get("visibility")
    if visibility and visibility not in ALLOWED_VISIBILITY:
        errors.append("visibility must be one of: show_on_next_relevant_turn, silent_until_relevant")

    trigger_reason = top_level.get("trigger_reason")
    if trigger_reason and trigger_reason not in ALLOWED_TRIGGER_REASONS:
        errors.append(
            "trigger_reason must be one of: failure_recovery, heartbeat, idle_fallback, scheduled, task_end"
        )

    reuse_gate = top_level.get("reuse_gate")
    if reuse_gate and reuse_gate not in ALLOWED_REUSE_GATES:
        errors.append("reuse_gate must be: min_4_of_5_axes_and_ttl_valid")

    fingerprint_hash = top_level.get("fingerprint_hash", "")
    if fingerprint_hash and not FINGERPRINT_HASH_PATTERN.fullmatch(fingerprint_hash):
        errors.append("fingerprint_hash must be formatted as h64:<64 lowercase hex chars>")

    fingerprint_parts = [part.strip() for part in top_level.get("problem_fingerprint", "").split("|") if part.strip()]
    if len(fingerprint_parts) < 4:
        errors.append("problem_fingerprint must contain at least 4 non-empty segments")

    if {"generated_at", "expires_at"} <= set(top_level):
        try:
            generated = parse_iso(top_level["generated_at"])
            expires = parse_iso(top_level["expires_at"])
            if expires <= generated:
                errors.append("expires_at must be later than generated_at")
            if expires - generated > MAX_TTL:
                errors.append("expires_at must be within 14 days of generated_at")
        except (TypeError, ValueError) as exc:
            errors.append(f"invalid ISO date: {exc}")

    limit = suggestion_limit(top_level)
    if limit is not None and suggestion_count > limit:
        errors.append(f"{search_mode} allows at most {limit} suggestion(s)")

    return errors


def validate_suggestion(
    index: int,
    suggestion: dict[str, object],
    declared_source_scope: set[str],
) -> list[str]:
    errors: list[str] = []
    missing = sorted(ITEM_REQUIRED - set(suggestion))
    if missing:
        errors.append(f"suggestion-{index} is missing fields: {', '.join(missing)}")
        return errors

    for field in sorted(ITEM_REQUIRED - {"match_reasoning"}):
        value = str(suggestion.get(field, "")).strip()
        if not value:
            errors.append(f"suggestion-{index} field {field} must be non-empty")

    confidence = str(suggestion.get("confidence", ""))
    if confidence not in ALLOWED_LEVELS:
        errors.append(f"suggestion-{index} confidence must be one of: low, medium, high")

    evidence = suggestion.get("evidence", [])
    if not isinstance(evidence, list) or len(evidence) < 2:
        errors.append(f"suggestion-{index} needs at least 2 evidence items")
    else:
        evidence_tiers = set()
        evidence_sources = set()
        evidence_format_error = False
        for item in evidence:
            if ":" not in str(item):
                errors.append(f"suggestion-{index} evidence items must use source_label: reference format")
                evidence_format_error = True
                continue
            label, source_key = parse_evidence_source(str(item))
            if not label or not source_key:
                errors.append(f"suggestion-{index} evidence items must include a non-empty source label and reference")
                evidence_format_error = True
                continue
            tier = label.split("_", 1)[0]
            evidence_tiers.add(tier)
            evidence_sources.add(source_key)
            if tier not in declared_source_scope:
                errors.append(
                    f"suggestion-{index} evidence tier {tier} must be declared in source_scope"
                )
        if evidence_format_error:
            evidence_tiers.clear()
            evidence_sources.clear()
        if not evidence_format_error and "primary" not in evidence_tiers:
            errors.append(f"suggestion-{index} needs at least 1 primary evidence item")
        if not evidence_format_error and not any(tier != "primary" for tier in evidence_tiers):
            errors.append(f"suggestion-{index} needs at least 1 non-primary cross-validation evidence item")
        if not evidence_format_error and len(evidence_sources) < 2:
            errors.append(f"suggestion-{index} needs at least 1 independent evidence source")

    match_reasoning = suggestion.get("match_reasoning", [])
    if not isinstance(match_reasoning, list) or len(match_reasoning) < 4:
        errors.append(f"suggestion-{index} needs at least 4 match_reasoning items")
    else:
        axes = set()
        for item in match_reasoning:
            if ":" not in str(item):
                errors.append(f"suggestion-{index} match_reasoning items must use axis: explanation format")
                break
            axis, explanation = str(item).split(":", 1)
            normalized_axis = canonicalize_axis(axis)
            if normalized_axis not in MATCH_AXES:
                continue
            if not explanation.strip():
                errors.append(f"suggestion-{index} match_reasoning explanations must be non-empty")
                break
            axes.add(normalized_axis)
        if len(axes) < 4:
            errors.append(f"suggestion-{index} needs at least 4 distinct match_reasoning axes")

    return errors


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    if not path.exists():
        return fail([f"file not found: {path}"])

    try:
        top_level, suggestions, errors = parse_block(path)
    except OSError as exc:
        return fail([f"failed to read {path}: {exc}"])

    errors.extend(validate_top_level(top_level, len(suggestions)))
    if not suggestions:
        errors.append("no suggestions found")

    declared_source_scope = split_scope(top_level.get("source_scope", ""))
    for index, suggestion in enumerate(suggestions, start=1):
        errors.extend(validate_suggestion(index, suggestion, declared_source_scope))

    if errors:
        return fail(errors)

    print(f"OK: validated {len(suggestions)} suggestion(s) in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
