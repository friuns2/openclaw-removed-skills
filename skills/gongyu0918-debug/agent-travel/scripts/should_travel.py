#!/usr/bin/env python3
"""Decide whether agent-travel should run for a given host state."""

from __future__ import annotations

import json
import re
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


DEFAULTS = {
    "active_conversation_window": "24h",
    "quiet_after_user_action": "20m",
    "quiet_after_agent_action": "5m",
    "repeat_fingerprint_cooldown": "12h",
    "max_runs_per_thread_per_day": 1,
    "max_runs_per_user_per_day": 3,
}
EVENTS = {"heartbeat", "scheduled", "task_end", "failure_recovery", "idle_fallback"}


@dataclass
class Decision:
    should_run: bool
    search_mode: str
    trigger_reason: str
    reason: str
    error_code: str | None = None
    observed_signals: list[str] | None = None


class InputError(Exception):
    """Raised when a readable state file has malformed fields."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def emit(decision: Decision) -> None:
    payload = {
        "should_run": decision.should_run,
        "search_mode": decision.search_mode,
        "trigger_reason": decision.trigger_reason,
        "reason": decision.reason,
    }
    if decision.error_code is not None:
        payload["error_code"] = decision.error_code
    if decision.observed_signals:
        payload["observed_signals"] = decision.observed_signals
    print(json.dumps(payload, ensure_ascii=False))


def parse_duration(value: str) -> timedelta:
    stripped = value.strip().lower()
    match = re.fullmatch(r"([+-]?\d+)([mhd])", stripped)
    if not match:
        raise InputError("invalid_duration", f"invalid duration: {value}")
    amount = int(match.group(1))
    unit = match.group(2)
    if amount <= 0:
        raise InputError("invalid_duration", f"duration must be a positive integer with unit: {value}")
    if unit == "m":
        return timedelta(minutes=amount)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "d":
        return timedelta(days=amount)
    raise InputError("invalid_duration", f"invalid duration unit: {value}")


def parse_timestamp(name: str, value: str) -> datetime:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise InputError("invalid_timestamp", f"invalid {name}: {exc}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InputError("invalid_timestamp", f"{name} must include a timezone offset")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Path to a JSON state file")
    return parser.parse_args()


def as_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    raise InputError("invalid_boolean", f"invalid boolean value: {value}")


def as_int(value: object, default: int, *, minimum: int | None = None) -> int:
    if value is None:
        parsed = default
    elif isinstance(value, bool):
        raise InputError("invalid_integer", f"invalid integer value: {value}")
    else:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise InputError("invalid_integer", f"invalid integer value: {value}") from exc
    if minimum is not None and parsed < minimum:
        raise InputError("invalid_integer", f"invalid integer value: {value}")
    return parsed


def get_duration(state: dict[str, object], key: str) -> timedelta:
    raw = state.get(key, DEFAULTS[key])
    if isinstance(raw, str):
        return parse_duration(raw)
    raise InputError("invalid_duration", f"invalid duration value for {key}: {raw}")


def get_event_kind(state: dict[str, object]) -> str:
    raw = str(state.get("event_kind", "")).strip().lower()
    if raw == "idle":
        raw = "idle_fallback"
    return raw


def normalize_label(value: object, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip().lower()
    return text or default


def get_optional_timestamp(state: dict[str, object], key: str) -> datetime | None:
    raw = state.get(key)
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    return parse_timestamp(key, text)


def get_required_raw(state: dict[str, object], key: str) -> str:
    if key not in state:
        raise KeyError(key)
    raw = state[key]
    if raw is None:
        raise KeyError(key)
    text = str(raw).strip()
    if not text or text.lower() == "none":
        raise KeyError(key)
    return text


def get_fallback_timestamp(state: dict[str, object], key: str, fallback: datetime) -> datetime:
    raw = state.get(key)
    if raw is None:
        return fallback
    text = str(raw).strip()
    if not text or text.lower() == "none":
        return fallback
    return parse_timestamp(key, text)


def blocked(
    event_kind: str,
    reason: str,
    error_code: str,
    observed_signals: list[str] | None = None,
) -> Decision:
    return Decision(False, "low", event_kind, reason, error_code, observed_signals or [])


def collect_escalation_signals(state: dict[str, object]) -> list[str]:
    signals: list[str] = []
    if as_int(state.get("related_failures"), 0, minimum=0) >= 2:
        signals.append("related_failures")
    if as_int(state.get("user_corrections"), 0, minimum=0) >= 2:
        signals.append("user_corrections")
    if as_int(state.get("unresolved_blocker_count"), 0, minimum=0) >= 1:
        signals.append("unresolved_blocker_count")
    if as_bool(state.get("version_mismatch_seen"), False):
        signals.append("version_mismatch_seen")
    if as_bool(state.get("user_explicit_search_request"), False):
        signals.append("user_explicit_search_request")
    if as_bool(state.get("user_explicit_deep_research_request"), False):
        signals.append("user_explicit_deep_research_request")
    return signals


def infer_search_mode(event_kind: str, signals: list[str]) -> tuple[str, list[str]]:
    if "user_explicit_deep_research_request" in signals:
        return "high", ["user_explicit_deep_research_request"]
    if "user_explicit_search_request" in signals:
        return "medium", ["user_explicit_search_request"]
    if event_kind == "task_end":
        mode_signals = ["task_end_default"]
        if signals:
            mode_signals.extend(signals)
        return "medium", mode_signals
    if event_kind == "failure_recovery":
        mode_signals = ["failure_recovery_default"]
        if signals:
            mode_signals.extend(signals)
        return "medium", mode_signals
    if event_kind in {"heartbeat", "scheduled"} and signals:
        return "medium", signals
    return "low", [f"{event_kind}_default"]


def decide(state: dict[str, object]) -> Decision:
    event_kind = get_event_kind(state)
    if event_kind not in EVENTS:
        return blocked(event_kind or "unknown", "unsupported event_kind", "unsupported_event_kind")

    if not as_bool(state.get("enabled"), True):
        return blocked(event_kind, "travel is disabled", "disabled")

    try:
        now = parse_timestamp("now", get_required_raw(state, "now"))
        last_thread_activity = parse_timestamp(
            "last_thread_activity",
            get_required_raw(state, "last_thread_activity"),
        )
        last_user_action = get_fallback_timestamp(state, "last_user_action", last_thread_activity)
        last_agent_action = get_fallback_timestamp(state, "last_agent_action", last_thread_activity)
    except KeyError as exc:
        return blocked(event_kind, f"missing required field: {exc.args[0]}", "missing_required_field")

    active_window = get_duration(state, "active_conversation_window")
    quiet_after_user = get_duration(state, "quiet_after_user_action")
    quiet_after_agent = get_duration(state, "quiet_after_agent_action")
    repeat_fingerprint_cooldown = get_duration(state, "repeat_fingerprint_cooldown")
    max_runs_per_thread = as_int(
        state.get("max_runs_per_thread_per_day"),
        DEFAULTS["max_runs_per_thread_per_day"],
        minimum=0,
    )
    max_runs_per_user = as_int(
        state.get("max_runs_per_user_per_day"),
        DEFAULTS["max_runs_per_user_per_day"],
        minimum=0,
    )

    if as_bool(state.get("user_operation_in_progress"), False):
        return blocked(event_kind, "user operation in progress", "user_operation_in_progress")
    if as_bool(state.get("agent_response_in_progress"), False):
        return blocked(event_kind, "agent response in progress", "agent_response_in_progress")
    if as_bool(state.get("tool_approval_pending"), False):
        return blocked(event_kind, "tool approval pending", "tool_approval_pending")
    if now - last_thread_activity > active_window:
        return blocked(event_kind, "active conversation window expired", "active_window_expired")
    if now - last_user_action < quiet_after_user:
        return blocked(event_kind, "quiet window after user action has not elapsed", "quiet_after_user_action")
    if now - last_agent_action < quiet_after_agent:
        return blocked(event_kind, "quiet window after agent action has not elapsed", "quiet_after_agent_action")
    if as_int(state.get("thread_runs_today"), 0, minimum=0) >= max_runs_per_thread:
        return blocked(event_kind, "thread run limit reached", "thread_run_limit_reached")
    if as_int(state.get("user_runs_today"), 0, minimum=0) >= max_runs_per_user:
        return blocked(event_kind, "user run limit reached", "user_run_limit_reached")

    host_supports_heartbeat = as_bool(state.get("host_supports_heartbeat"), True)
    user_prefers_idle_fallback = as_bool(state.get("user_prefers_idle_fallback"), False)
    idle_fallback_enabled = as_bool(state.get("idle_fallback_enabled"), False)
    if event_kind == "idle_fallback" and not (
        idle_fallback_enabled or not host_supports_heartbeat or user_prefers_idle_fallback
    ):
        return blocked(
            event_kind,
            "idle fallback needs explicit opt-in or a host without heartbeat support",
            "idle_fallback_not_enabled",
            [
                "host_supports_heartbeat" if host_supports_heartbeat else "host_without_heartbeat",
                "idle_fallback_not_opted_in",
            ],
        )

    signals = collect_escalation_signals(state)
    current_fingerprint_hash = str(state.get("current_fingerprint_hash", "")).strip()
    last_travel_fingerprint_hash = str(state.get("last_travel_fingerprint_hash", "")).strip()
    last_travel_generated_at = get_optional_timestamp(state, "last_travel_generated_at")
    cooldown_active = bool(
        current_fingerprint_hash
        and last_travel_fingerprint_hash
        and current_fingerprint_hash == last_travel_fingerprint_hash
        and last_travel_generated_at is not None
        and now - last_travel_generated_at < repeat_fingerprint_cooldown
    )
    cooldown_bypassed = cooldown_active and bool(signals)
    if cooldown_active and not cooldown_bypassed:
        return blocked(
            event_kind,
            "repeat fingerprint cooldown is still active",
            "duplicate_fingerprint_cooldown",
            ["fingerprint_repeat_window_active"],
        )
    user_configured_periodic_travel = as_bool(state.get("user_configured_periodic_travel"), False)
    scheduled_trigger_managed_by_host = as_bool(
        state.get("scheduled_trigger_managed_by_host"),
        False,
    )

    if event_kind == "failure_recovery":
        has_recovery_signal = any(
            [
                "related_failures" in signals,
                "user_corrections" in signals,
                "unresolved_blocker_count" in signals,
                "version_mismatch_seen" in signals,
                "user_explicit_search_request" in signals,
                "user_explicit_deep_research_request" in signals,
            ]
        )
        if not has_recovery_signal:
            return blocked(
                event_kind,
                "failure recovery needs 2 related failures, 2 user corrections, 1 blocker, or version mismatch",
                "recovery_signal_missing",
                signals,
            )

    if event_kind == "scheduled" and not (
        scheduled_trigger_managed_by_host or user_configured_periodic_travel
    ):
        return blocked(
            event_kind,
            "scheduled travel needs a host-managed schedule or explicit periodic travel",
            "scheduled_opt_in_required",
            signals,
        )
    if event_kind == "scheduled":
        scheduled_prompt_origin = normalize_label(state.get("scheduled_prompt_origin"), "manual")
        scheduled_prompt_emotion = normalize_label(state.get("scheduled_prompt_emotion"), "neutral")
        if scheduled_prompt_origin != "manual" and scheduled_prompt_emotion not in {"neutral", "none"}:
            return blocked(
                event_kind,
                "host-generated scheduled prompts must stay neutral",
                "scheduled_prompt_must_be_neutral",
                ["host_generated_scheduled_prompt", f"scheduled_prompt_emotion:{scheduled_prompt_emotion}"],
            )

    search_mode, observed_signals = infer_search_mode(event_kind, signals)
    if event_kind == "scheduled":
        if scheduled_trigger_managed_by_host:
            observed_signals = ["scheduled_trigger_managed_by_host", *observed_signals]
        elif user_configured_periodic_travel:
            observed_signals = ["user_configured_periodic_travel", *observed_signals]
    if cooldown_bypassed:
        observed_signals = ["repeat_fingerprint_escalation_bypass", *observed_signals]
    return Decision(
        True,
        search_mode,
        event_kind,
        "active conversation, quiet window, within cooldown",
        "ready",
        observed_signals,
    )


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        emit(Decision(False, "low", "error", f"unable to read state file: {exc}"))
        return 1

    try:
        state = json.loads(raw)
    except json.JSONDecodeError as exc:
        emit(Decision(False, "low", "error", f"invalid JSON: {exc.msg}"))
        return 1

    if not isinstance(state, dict):
        emit(Decision(False, "low", "error", "state must be a JSON object"))
        return 0

    try:
        decision = decide(state)
    except InputError as exc:
        emit(Decision(False, "low", get_event_kind(state), exc.message, exc.code))
        return 0
    except Exception as exc:  # pragma: no cover - defensive fallback
        emit(
            Decision(
                False,
                "low",
                get_event_kind(state),
                f"unexpected error: {exc}",
                "unexpected_internal_error",
            )
        )
        return 1

    emit(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
