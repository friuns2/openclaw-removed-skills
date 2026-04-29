#!/usr/bin/env python3
"""Build a dry-run agent-travel query plan without performing network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from should_travel import Decision, InputError, decide, get_event_kind


KNOWN_HOSTS = [
    "Claude Code",
    "OpenClaw",
    "Hermes",
    "Codex",
    "OpenAI",
    "GitHub Actions",
    "Vercel",
]
MAX_CONTEXT_CHARS = 12000
MAX_TERM_CHARS = 96
QUERY_LIMITS = {"low": 1, "medium": 3, "high": 5}

SECRET_PATTERNS = [
    (
        "credential_assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|token|secret|password|authorization|bearer)\s*[:=]\s*[^\s`'\"]+"
        ),
    ),
    (
        "token_like",
        re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,})\b"),
    ),
    (
        "internal_url",
        re.compile(
            r"https?://(?:localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|"
            r"172\.(?:1[6-9]|2\d|3[0-1])\.\d+\.\d+|[^/\s]+\.internal|[^/\s]+\.local)"
            r"(?:/[^\s`'\"]*)?"
        ),
    ),
    (
        "private_path",
        re.compile(
            r"(?:[A-Za-z]:\\Users\\[^\\\s]+\\[^\s`'\"]+|/Users/[^/\s]+/[^\s`'\"]+|/home/[^/\s]+/[^\s`'\"]+)"
        ),
    ),
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", help="Path to a JSON host state file")
    parser.add_argument("--context", help="Optional thread/context text file")
    return parser.parse_args()


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def read_state(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    state = json.loads(raw)
    if not isinstance(state, dict):
        raise ValueError("state must be a JSON object")
    return state


def read_context(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")[:MAX_CONTEXT_CHARS]


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    redacted = text
    counts: dict[str, int] = {}
    for label, pattern in SECRET_PATTERNS:
        redacted, count = pattern.subn(f"[REDACTED_{label.upper()}]", redacted)
        counts[label] = count
    return redacted, counts


def merge_counts(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    keys = set(left) | set(right)
    return {key: left.get(key, 0) + right.get(key, 0) for key in sorted(keys)}


def redact_value(value: Any) -> tuple[Any, dict[str, int]]:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        redacted_items: list[Any] = []
        total: dict[str, int] = {}
        for item in value:
            redacted, counts = redact_value(item)
            redacted_items.append(redacted)
            total = merge_counts(total, counts)
        return redacted_items, total
    if isinstance(value, dict):
        redacted_dict: dict[str, Any] = {}
        total: dict[str, int] = {}
        for key, item in value.items():
            redacted, counts = redact_value(item)
            redacted_dict[key] = redacted
            total = merge_counts(total, counts)
        return redacted_dict, total
    return value, {}


def clean_term(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\[REDACTED_[A-Z_]+\]", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\b(?:with|at|from|to|for|and|or)\s*$", "", text, flags=re.I)
    text = text.strip("`'\" ")
    if not text:
        return fallback
    if len(text) > MAX_TERM_CHARS:
        return text[: MAX_TERM_CHARS - 1].rstrip() + "..."
    return text


def first_state_value(state: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = state.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def find_known_host(state: dict[str, Any], context: str) -> str:
    explicit = first_state_value(state, ["host", "agent_host", "product", "agent"])
    if explicit:
        return clean_term(explicit, "unknown-host")
    context_lower = context.lower()
    for host in KNOWN_HOSTS:
        if host.lower() in context_lower:
            return host
    return "unknown-host"


def find_version(state: dict[str, Any], context: str) -> str:
    explicit = first_state_value(state, ["version", "host_version", "agent_version"])
    if explicit:
        return clean_term(explicit, "current-version")
    match = re.search(r"\b(?:v|version\s*)?(\d+\.\d+(?:\.\d+)?(?:[-+][A-Za-z0-9_.-]+)?)\b", context, re.I)
    if match:
        return clean_term(match.group(0), "current-version")
    return "current-version"


def pick_relevant_line(context: str, keywords: list[str], fallback: str) -> str:
    for line in context.splitlines():
        lowered = line.lower()
        if any(keyword in lowered for keyword in keywords):
            return clean_term(line, fallback)
    return fallback


def build_terms(state: dict[str, Any], context: str) -> dict[str, str]:
    symptom = first_state_value(state, ["symptom", "recent_error", "error", "failure"])
    constraint = first_state_value(state, ["constraint", "constraint_pattern", "privacy_constraint"])
    outcome = first_state_value(state, ["desired_outcome", "goal", "next_outcome"])
    return {
        "host": find_known_host(state, context),
        "version": find_version(state, context),
        "symptom": clean_term(
            symptom or pick_relevant_line(context, ["error", "failed", "failure", "timeout", "crash"], "unresolved issue"),
            "unresolved issue",
        ),
        "constraint": clean_term(
            constraint
            or pick_relevant_line(
                context,
                ["public-only", "cron", "heartbeat", "scheduled", "privacy", "memory", "quiet"],
                "current thread constraints",
            ),
            "current thread constraints",
        ),
        "outcome": clean_term(
            outcome
            or pick_relevant_line(context, ["goal", "need", "want", "expected", "should"], "next useful answer"),
            "next useful answer",
        ),
    }


def fingerprint_hash(fingerprint: str) -> str:
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
    return f"h64:{digest}"


def compact_query(*parts: str) -> str:
    seen: set[str] = set()
    kept: list[str] = []
    for part in parts:
        cleaned = clean_term(part, "")
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        kept.append(cleaned)
    return " ".join(kept)


def build_queries(terms: dict[str, str], search_mode: str) -> list[dict[str, str]]:
    candidates = [
        {
            "tier": "primary",
            "surface": "official docs / release notes",
            "purpose": "Anchor the suggestion in official behavior before considering community advice.",
            "query": compact_query(terms["host"], terms["version"], terms["symptom"], "official docs"),
        },
        {
            "tier": "secondary",
            "surface": "GitHub issues / Stack Overflow",
            "purpose": "Find independent reports with the same symptom and constraints.",
            "query": compact_query(terms["host"], terms["symptom"], terms["constraint"], "GitHub issue Stack Overflow"),
        },
        {
            "tier": "secondary",
            "surface": "search engine community results",
            "purpose": "Cross-check whether the same workaround appears in practical workflows.",
            "query": compact_query(terms["host"], terms["symptom"], terms["outcome"], "community workflow"),
        },
        {
            "tier": "tertiary",
            "surface": "forums / blogs",
            "purpose": "Use only for extra color after primary and secondary evidence exist.",
            "query": compact_query(terms["host"], terms["constraint"], terms["outcome"], "forum blog"),
        },
        {
            "tier": "tertiary",
            "surface": "social discussion",
            "purpose": "Use as weak evidence only when it matches official grounding.",
            "query": compact_query(terms["host"], terms["symptom"], "discussion workaround"),
        },
    ]
    return candidates[: QUERY_LIMITS.get(search_mode, 1)]


def decision_payload(decision: Decision) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "should_run": decision.should_run,
        "search_mode": decision.search_mode,
        "trigger_reason": decision.trigger_reason,
        "reason": decision.reason,
    }
    if decision.error_code is not None:
        payload["error_code"] = decision.error_code
    if decision.observed_signals:
        payload["observed_signals"] = decision.observed_signals
    return payload


def build_plan(state: dict[str, Any], context: str) -> dict[str, Any]:
    decision = decide(state)
    redacted_context, context_redaction_counts = redact_text(context)
    redacted_state, state_redaction_counts = redact_value(state)
    if not isinstance(redacted_state, dict):
        redacted_state = state
    terms = build_terms(redacted_state, redacted_context)
    fingerprint = "|".join(
        [terms["host"], terms["version"], terms["symptom"], terms["constraint"], terms["outcome"]]
    )
    queries = build_queries(terms, decision.search_mode) if decision.should_run else []
    return {
        "dry_run": True,
        "network_used": False,
        "decision": decision_payload(decision),
        "problem_fingerprint": fingerprint,
        "fingerprint_hash": fingerprint_hash(fingerprint),
        "redaction_summary": {
            "context_chars_seen": len(context),
            "context_chars_used": len(redacted_context),
            "context_redacted_items": context_redaction_counts,
            "state_redacted_items": state_redaction_counts,
            "total_redacted_items": merge_counts(context_redaction_counts, state_redaction_counts),
        },
        "query_budget": {
            "search_mode": decision.search_mode,
            "max_queries": QUERY_LIMITS.get(decision.search_mode, 1),
        },
        "queries": queries,
        "notes": [
            "This is a dry-run plan. The host agent performs any web/search calls.",
            "Review queries before executing them with private connectors or internal search tools.",
            "Store only cross-validated advisory hints in the isolated suggestion channel.",
        ],
    }


def main() -> int:
    args = parse_args()
    try:
        state = read_state(Path(args.state))
        context = read_context(args.context)
        emit(build_plan(state, context))
        return 0
    except FileNotFoundError as exc:
        emit({"dry_run": True, "network_used": False, "error_code": "file_not_found", "reason": str(exc)})
        return 1
    except json.JSONDecodeError as exc:
        emit({"dry_run": True, "network_used": False, "error_code": "invalid_json", "reason": exc.msg})
        return 1
    except InputError as exc:
        emit(
            {
                "dry_run": True,
                "network_used": False,
                "decision": decision_payload(Decision(False, "low", get_event_kind(state), exc.message, exc.code)),
                "queries": [],
            }
        )
        return 0
    except ValueError as exc:
        emit({"dry_run": True, "network_used": False, "error_code": "invalid_input", "reason": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
