#!/usr/bin/env python3
"""Run reliability tests for agent-travel validators and trigger logic."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from _report_utils import normalize_report_paths
from _test_mutators import append_suggestions, replace_line, replace_match_reasoning_block, replace_once


ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts" / "validate_suggestions.py"
SHOULD_TRAVEL = ROOT / "scripts" / "should_travel.py"
PLAN_TRAVEL = ROOT / "scripts" / "plan_travel.py"
CANONICAL = ROOT / "references" / "suggestion-contract.md"
REPORT_PATH = ROOT / "assets" / "reliability_report.json"
START = "<!-- agent-travel:suggestions:start -->"
END = "<!-- agent-travel:suggestions:end -->"
TIMEOUT_SECONDS = 10

def mutate_missing_markers(text: str) -> str:
    return text.replace(START, "").replace(END, "")


def mutate_invalid_dates(text: str) -> str:
    return replace_line(text, "expires_at", "2026-04-18T03:00:00+08:00")


def mutate_missing_timezone(text: str) -> str:
    return replace_line(text, "generated_at", "2026-04-20T03:00:00")


def mutate_missing_source_scope(text: str) -> str:
    return replace_once(text, "source_scope: primary+secondary\n", "")


def mutate_missing_match_reasoning(text: str) -> str:
    return replace_match_reasoning_block(text, "")


def mutate_no_primary_evidence(text: str) -> str:
    return (
        text.replace("primary_official_discussion:", "secondary_discussion:", 1)
        .replace("secondary_community:", "tertiary_community:", 1)
    )


def mutate_no_independent_evidence(text: str) -> str:
    return replace_once(
        text,
        "- secondary_community: https://example.com/community-thread",
        "- primary_official_discussion: https://example.com/maintainer-thread",
    )


def mutate_stray_list_item(text: str) -> str:
    needle = "problem_fingerprint: host|subsystem|symptom|version\n"
    return replace_once(text, needle, needle + "- stray item at top level\n")


def mutate_bad_match_axes(text: str) -> str:
    replacement = (
        "match_reasoning:\n"
        "- host: matched the same skill-host reload surface\n"
        "- host: matched the same host build family where scan timing matters\n"
        "- symptom: matched stale behavior after a local edit\n"
        "- symptom: matched a low-risk reload check before more edits\n"
    )
    return replace_match_reasoning_block(text, replacement)


def mutate_low_mode_two_suggestions(text: str) -> str:
    return append_suggestions(text, 2)


def mutate_medium_mode_four_suggestions(text: str) -> str:
    text = replace_line(text, "search_mode", "medium")
    return append_suggestions(text, 4)


def mutate_invalid_confidence(text: str) -> str:
    return replace_line(text, "confidence", "certain")


def mutate_ttl_too_long(text: str) -> str:
    return replace_line(text, "expires_at", "2026-05-10T03:00:00+08:00")


def mutate_invalid_visibility(text: str) -> str:
    return replace_line(text, "visibility", "always_show")


def mutate_invalid_trigger_reason(text: str) -> str:
    return replace_line(text, "trigger_reason", "manual_override")


def mutate_invalid_reuse_gate(text: str) -> str:
    return replace_line(text, "reuse_gate", "ttl_valid_only")


def mutate_invalid_source_scope_part(text: str) -> str:
    return replace_line(text, "source_scope", "primary+quaternary")


def mutate_evidence_outside_source_scope(text: str) -> str:
    return replace_once(
        text,
        "- secondary_community: https://example.com/community-thread",
        "- tertiary_community: https://example.com/community-thread",
    )


def mutate_invalid_fingerprint_hash(text: str) -> str:
    return replace_line(text, "fingerprint_hash", "h64:xyz")


def mutate_short_problem_fingerprint(text: str) -> str:
    return replace_line(text, "problem_fingerprint", "host|symptom|version")


def mutate_empty_fit_reason(text: str) -> str:
    return replace_line(text, "fit_reason", "")


def mutate_valid_optional_fields(text: str) -> str:
    text = replace_line(text, "visibility", "show_on_next_relevant_turn")
    text = replace_line(text, "trigger_reason", "heartbeat")
    return replace_line(text, "reuse_gate", "min_4_of_5_axes_and_ttl_valid")


def mutate_misplaced_top_level_visibility(text: str) -> str:
    needle = "fit_reason: This fits when the user already edited the skill locally and needs a fast low-risk check before more changes.\n"
    return replace_once(text, needle, needle + "visibility: silent_until_relevant\n")


def mutate_malformed_evidence_item(text: str) -> str:
    return replace_once(
        text,
        "- secondary_community: https://example.com/community-thread",
        "- secondary_community\n",
    )


VALIDATOR_CASES = [
    ("canonical", lambda text: text, True),
    ("missing_markers", mutate_missing_markers, False),
    ("invalid_dates", mutate_invalid_dates, False),
    ("missing_timezone", mutate_missing_timezone, False),
    ("missing_source_scope", mutate_missing_source_scope, False),
    ("missing_match_reasoning", mutate_missing_match_reasoning, False),
    ("no_primary_evidence", mutate_no_primary_evidence, False),
    ("no_independent_evidence", mutate_no_independent_evidence, False),
    ("stray_list_item", mutate_stray_list_item, False),
    ("bad_match_axes", mutate_bad_match_axes, False),
    ("low_mode_two_suggestions", mutate_low_mode_two_suggestions, False),
    ("medium_mode_four_suggestions", mutate_medium_mode_four_suggestions, False),
    ("invalid_confidence", mutate_invalid_confidence, False),
    ("ttl_too_long", mutate_ttl_too_long, False),
    ("invalid_visibility", mutate_invalid_visibility, False),
    ("invalid_trigger_reason", mutate_invalid_trigger_reason, False),
    ("invalid_reuse_gate", mutate_invalid_reuse_gate, False),
    ("invalid_source_scope_part", mutate_invalid_source_scope_part, False),
    ("evidence_outside_source_scope", mutate_evidence_outside_source_scope, False),
    ("invalid_fingerprint_hash", mutate_invalid_fingerprint_hash, False),
    ("short_problem_fingerprint", mutate_short_problem_fingerprint, False),
    ("empty_fit_reason", mutate_empty_fit_reason, False),
    ("misplaced_top_level_visibility", mutate_misplaced_top_level_visibility, False),
    ("malformed_evidence_item", mutate_malformed_evidence_item, False),
    ("valid_optional_fields", mutate_valid_optional_fields, True),
]


TRIGGER_CASES = [
    (
        "should_travel_heartbeat_quiet_low",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "related_failures": 0,
            "user_corrections": 0,
            "unresolved_blocker_count": 0,
            "version_mismatch_seen": False,
            "user_explicit_search_request": False,
            "user_explicit_deep_research_request": False,
        },
        True,
        "low",
        "ready",
    ),
    (
        "should_travel_required_timestamp_null_is_missing",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": None,
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
        },
        False,
        "low",
        "missing_required_field",
    ),
    (
        "should_travel_user_active",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T11:50:00+00:00",
            "last_user_action": "2026-04-20T11:50:00+00:00",
            "last_agent_action": "2026-04-20T11:40:00+00:00",
            "user_operation_in_progress": True,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
        },
        False,
        "low",
        "user_operation_in_progress",
    ),
    (
        "should_travel_failure_recovery_medium",
        {
            "enabled": True,
            "event_kind": "failure_recovery",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "related_failures": 2,
            "user_corrections": 0,
            "unresolved_blocker_count": 1,
            "version_mismatch_seen": False,
            "user_explicit_search_request": False,
            "user_explicit_deep_research_request": False,
        },
        True,
        "medium",
        "ready",
    ),
    (
        "should_travel_failure_recovery_bypasses_repeat_cooldown",
        {
            "enabled": True,
            "event_kind": "failure_recovery",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "related_failures": 2,
            "current_fingerprint_hash": "h64:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "last_travel_fingerprint_hash": "h64:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "last_travel_generated_at": "2026-04-20T07:30:00+00:00",
            "repeat_fingerprint_cooldown": "12h",
        },
        True,
        "medium",
        "ready",
    ),
    (
        "should_travel_explicit_deep_request_high",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "user_explicit_deep_research_request": True,
        },
        True,
        "high",
        "ready",
    ),
    (
        "should_travel_single_failure_stays_blocked",
        {
            "enabled": True,
            "event_kind": "failure_recovery",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "related_failures": 1,
            "user_corrections": 0,
            "unresolved_blocker_count": 0,
            "version_mismatch_seen": False,
        },
        False,
        "low",
        "recovery_signal_missing",
    ),
    (
        "should_travel_task_end_defaults_medium",
        {
            "enabled": True,
            "event_kind": "task_end",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
        },
        True,
        "medium",
        "ready",
    ),
    (
        "should_travel_invalid_duration",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "quiet_after_user_action": "abc",
        },
        False,
        "low",
        "invalid_duration",
    ),
    (
        "should_travel_negative_duration",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "quiet_after_user_action": "-5m",
        },
        False,
        "low",
        "invalid_duration",
    ),
    (
        "should_travel_idle_fallback_needs_opt_in",
        {
            "enabled": True,
            "event_kind": "idle_fallback",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "host_supports_heartbeat": True,
            "idle_fallback_enabled": False,
            "user_prefers_idle_fallback": False,
        },
        False,
        "low",
        "idle_fallback_not_enabled",
    ),
    (
        "should_travel_idle_fallback_without_heartbeat_runs",
        {
            "enabled": True,
            "event_kind": "idle_fallback",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "host_supports_heartbeat": False,
        },
        True,
        "low",
        "ready",
    ),
    (
        "should_travel_duplicate_fingerprint_cooldown",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "current_fingerprint_hash": "h64:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "last_travel_fingerprint_hash": "h64:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "last_travel_generated_at": "2026-04-20T06:30:00+00:00",
            "repeat_fingerprint_cooldown": "12h",
        },
        False,
        "low",
        "duplicate_fingerprint_cooldown",
    ),
    (
        "should_travel_duplicate_fingerprint_after_cooldown_runs",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "current_fingerprint_hash": "h64:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "last_travel_fingerprint_hash": "h64:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "last_travel_generated_at": "2026-04-19T18:00:00+00:00",
            "repeat_fingerprint_cooldown": "12h",
        },
        True,
        "low",
        "ready",
    ),
    (
        "should_travel_manual_scheduled_prompt_may_keep_emotion",
        {
            "enabled": True,
            "event_kind": "scheduled",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "user_configured_periodic_travel": True,
            "scheduled_prompt_origin": "manual",
            "scheduled_prompt_emotion": "frustrated",
        },
        True,
        "low",
        "ready",
    ),
    (
        "should_travel_host_managed_schedule_runs_without_manual_opt_in",
        {
            "enabled": True,
            "event_kind": "scheduled",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "scheduled_trigger_managed_by_host": True,
            "scheduled_prompt_origin": "host_generated",
            "scheduled_prompt_emotion": "neutral",
        },
        True,
        "low",
        "ready",
    ),
    (
        "should_travel_scheduled_defaults_closed_without_host_signal",
        {
            "enabled": True,
            "event_kind": "scheduled",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
        },
        False,
        "low",
        "scheduled_opt_in_required",
    ),
    (
        "should_travel_scheduled_without_host_or_opt_in_blocks",
        {
            "enabled": True,
            "event_kind": "scheduled",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "scheduled_trigger_managed_by_host": False,
        },
        False,
        "low",
        "scheduled_opt_in_required",
    ),
    (
        "should_travel_host_generated_scheduled_prompt_stays_neutral",
        {
            "enabled": True,
            "event_kind": "scheduled",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "scheduled_trigger_managed_by_host": True,
            "scheduled_prompt_origin": "host_generated",
            "scheduled_prompt_emotion": "frustrated",
        },
        False,
        "low",
        "scheduled_prompt_must_be_neutral",
    ),
    (
        "should_travel_idle_fallback_stays_low_with_passive_signals",
        {
            "enabled": True,
            "event_kind": "idle_fallback",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "host_supports_heartbeat": False,
            "related_failures": 2,
            "unresolved_blocker_count": 1,
        },
        True,
        "low",
        "ready",
    ),
    (
        "should_travel_negative_thread_runs_rejected",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "thread_runs_today": -5,
        },
        False,
        "low",
        "invalid_integer",
    ),
    (
        "should_travel_negative_related_failures_rejected",
        {
            "enabled": True,
            "event_kind": "failure_recovery",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "related_failures": -1,
        },
        False,
        "low",
        "invalid_integer",
    ),
]

PLAN_CASES = [
    (
        "plan_travel_heartbeat_low_query",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "host": "OpenClaw",
            "symptom": "cron digest repeats stale notes",
            "constraint": "public-only search",
            "desired_outcome": "fresh advisory hint",
        },
        "Host: OpenClaw\nObserved issue: cron digest repeats stale notes\n",
        True,
        "low",
        1,
        [],
    ),
    (
        "plan_travel_scheduled_blocked_no_queries",
        {
            "enabled": True,
            "event_kind": "scheduled",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "host": "Claude Code",
            "symptom": "scheduled task repeats old log triage",
        },
        "",
        False,
        "low",
        0,
        [],
    ),
    (
        "plan_travel_redacts_state_secrets",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "host": "OpenClaw",
            "symptom": "cron failed with token=sk-test_should_redact_1234567890",
            "constraint": "public-only search",
            "desired_outcome": "safe query",
        },
        "Internal URL: http://localhost:3000/admin\nPath: C:\\Users\\admin\\private\\repo\\.env\n",
        True,
        "low",
        1,
        ["sk-test_should_redact", "localhost:3000", "private\\repo"],
    ),
]


def run_validator_case(name: str, body: str, expected_pass: bool, temp_dir: Path) -> dict[str, object]:
    path = temp_dir / f"{name}.md"
    path.write_text(body, encoding="utf-8")
    try:
        proc = subprocess.run(
            [sys.executable, str(VALIDATOR), str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
        output = (proc.stdout + proc.stderr).strip()
        crashed = "Traceback" in output
        actual_pass = proc.returncode == 0
    except subprocess.TimeoutExpired:
        output = f"TIMEOUT after {TIMEOUT_SECONDS}s"
        crashed = True
        actual_pass = False
    return {
        "case": name,
        "kind": "validator",
        "expected_pass": expected_pass,
        "actual_pass": actual_pass,
        "ok": actual_pass == expected_pass and not crashed,
        "crashed": crashed,
        "output": output,
    }


def run_trigger_case(
    name: str,
    state: dict[str, object],
    expected_should_run: bool,
    expected_search_mode: str,
    expected_error_code: str,
    temp_dir: Path,
) -> dict[str, object]:
    path = temp_dir / f"{name}.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        proc = subprocess.run(
            [sys.executable, str(SHOULD_TRAVEL), str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
        output = (proc.stdout + proc.stderr).strip()
        crashed = "Traceback" in output
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            payload = {}
            crashed = True
    except subprocess.TimeoutExpired:
        output = f"TIMEOUT after {TIMEOUT_SECONDS}s"
        crashed = True
        payload = {}
        proc = subprocess.CompletedProcess([], 1)
    actual_should_run = payload.get("should_run")
    actual_search_mode = payload.get("search_mode")
    actual_error_code = payload.get("error_code")
    ok = (
        actual_should_run == expected_should_run
        and actual_search_mode == expected_search_mode
        and actual_error_code == expected_error_code
        and proc.returncode == 0
        and not crashed
    )
    return {
        "case": name,
        "kind": "trigger",
        "expected_should_run": expected_should_run,
        "actual_should_run": actual_should_run,
        "expected_search_mode": expected_search_mode,
        "actual_search_mode": actual_search_mode,
        "expected_error_code": expected_error_code,
        "actual_error_code": actual_error_code,
        "ok": ok,
        "crashed": crashed,
        "output": output,
    }


def run_plan_case(
    name: str,
    state: dict[str, object],
    context: str,
    expected_should_run: bool,
    expected_search_mode: str,
    expected_query_count: int,
    forbidden_substrings: list[str],
    temp_dir: Path,
) -> dict[str, object]:
    state_path = temp_dir / f"{name}.json"
    context_path = temp_dir / f"{name}.txt"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    context_path.write_text(context, encoding="utf-8")
    try:
        proc = subprocess.run(
            [sys.executable, str(PLAN_TRAVEL), str(state_path), "--context", str(context_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
        output = (proc.stdout + proc.stderr).strip()
        crashed = "Traceback" in output
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            payload = {}
            crashed = True
    except subprocess.TimeoutExpired:
        output = f"TIMEOUT after {TIMEOUT_SECONDS}s"
        crashed = True
        payload = {}
        proc = subprocess.CompletedProcess([], 1)

    decision = payload.get("decision", {}) if isinstance(payload.get("decision"), dict) else {}
    queries = payload.get("queries", [])
    serialized = json.dumps(payload, ensure_ascii=False)
    leaked = [text for text in forbidden_substrings if text in serialized]
    ok = (
        decision.get("should_run") == expected_should_run
        and decision.get("search_mode") == expected_search_mode
        and isinstance(queries, list)
        and len(queries) == expected_query_count
        and not leaked
        and proc.returncode == 0
        and not crashed
    )
    return {
        "case": name,
        "kind": "plan",
        "expected_should_run": expected_should_run,
        "actual_should_run": decision.get("should_run"),
        "expected_search_mode": expected_search_mode,
        "actual_search_mode": decision.get("search_mode"),
        "expected_query_count": expected_query_count,
        "actual_query_count": len(queries) if isinstance(queries, list) else None,
        "leaked_forbidden_substrings": leaked,
        "ok": ok,
        "crashed": crashed,
        "output": output,
    }


def main() -> int:
    canonical = CANONICAL.read_text(encoding="utf-8")
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="agent-travel-reliability-") as temp:
        temp_dir = Path(temp)
        for name, mutator, expected_pass in VALIDATOR_CASES:
            results.append(run_validator_case(name, mutator(canonical), expected_pass, temp_dir))
        for name, state, expected_should_run, expected_search_mode, expected_error_code in TRIGGER_CASES:
            results.append(
                run_trigger_case(
                    name,
                    state,
                    expected_should_run,
                    expected_search_mode,
                    expected_error_code,
                    temp_dir,
                )
            )
        for (
            name,
            state,
            context,
            expected_should_run,
            expected_search_mode,
            expected_query_count,
            forbidden_substrings,
        ) in PLAN_CASES:
            results.append(
                run_plan_case(
                    name,
                    state,
                    context,
                    expected_should_run,
                    expected_search_mode,
                    expected_query_count,
                    forbidden_substrings,
                    temp_dir,
                )
            )

    validator_results = [item for item in results if item["kind"] == "validator"]
    trigger_results = [item for item in results if item["kind"] == "trigger"]
    plan_results = [item for item in results if item["kind"] == "plan"]
    summary = {
        "total_cases": len(results),
        "passed_cases": sum(1 for item in results if item["ok"]),
        "crash_count": sum(1 for item in results if item["crashed"]),
        "validator_cases": len(validator_results),
        "validator_passed": sum(1 for item in validator_results if item["ok"]),
        "trigger_cases": len(trigger_results),
        "trigger_passed": sum(1 for item in trigger_results if item["ok"]),
        "plan_cases": len(plan_results),
        "plan_passed": sum(1 for item in plan_results if item["ok"]),
        "results": results,
    }
    summary = normalize_report_paths(summary)
    REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed_cases"] == summary["total_cases"] and summary["crash_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
