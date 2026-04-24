#!/usr/bin/env python3
"""Companion state manager — updates state, learns preferences, outputs context JSON for the agent."""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


DEFAULT_STYLE_VARIANTS = ["soft_curious", "teasing_checkin", "light_service_nudge"]
DEFAULT_CONTENT_TYPES = ["checkin_question", "playful_poke", "small_share"]

MODE_STYLE_VARIANTS = {
    "morning": ["soft_curious", "teasing_checkin", "light_service_nudge"],
    "afternoon": ["teasing_checkin", "soft_curious", "light_service_nudge"],
    "evening": ["service_nudge", "teasing_checkin", "competent_report"],
    "night": ["soft_wrapup", "gentle_clingy", "service_wrapup"],
    "heartbeat": ["soft_curious", "light_service_nudge", "gentle_clingy"],
}

MODE_CONTENT_TYPES = {
    "morning": ["checkin_question", "playful_poke", "small_share"],
    "afternoon": ["checkin_question", "playful_poke", "small_share"],
    "evening": ["task_invite", "micro_report", "checkin_question"],
    "night": ["soft_goodnight", "gentle_miss", "task_invite"],
    "heartbeat": ["checkin_question", "playful_poke", "small_share"],
}


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def run_shell(template: str, values: dict, expect_json=False, timeout_sec=15):
    quoted = {k: shlex.quote(str(v)) for k, v in values.items()}
    cmd = template.format(**quoted)
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"command timed out after {timeout_sec}s: {cmd}")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"command failed: {cmd}")
    stdout = result.stdout.strip()
    if expect_json:
        return json.loads(stdout)
    return stdout


STATE_SCHEMA_VERSION = 2


def fill_missing_defaults(target: dict, defaults: dict) -> bool:
    changed = False
    for key, value in defaults.items():
        if key not in target:
            target[key] = json.loads(json.dumps(value, ensure_ascii=False))
            changed = True
            continue
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            if fill_missing_defaults(target[key], value):
                changed = True
    return changed


def ensure_state(state_file: Path):
    defaults = {
        "schema_version": STATE_SCHEMA_VERSION,
        "day": "",
        "daily_count": 0,
        "last_proactive_at": 0,
        "last_heartbeat_at": 0,
        "last_mode": "",
        "last_style": "",
        "last_content_type": "",
        "mode_days": {},
        "pending_send": {
            "mode": "",
            "generated_at": 0,
            "style": "",
            "content_type": "",
            "emotion_level": "",
        },
        "preference_profile": {"service": 0, "clingy": 0, "curious": 0, "teasing": 0, "wrapup": 0},
        "relationship_state": {
            "last_owner_reply_at": 0,
            "last_response_delay_sec": 0,
            "last_seen_reply_text": "",
            "attention_balance": "steady",
        },
    }
    state = load_json(state_file, {}) or {}
    if not isinstance(state, dict):
        state = {}
    original_schema_version = state.get("schema_version", 1)
    changed = fill_missing_defaults(state, defaults)

    if original_schema_version < STATE_SCHEMA_VERSION:
        if state.get("last_mode") == "heartbeat" and state.get("last_proactive_at", 0) and not state.get("last_heartbeat_at", 0):
            state["last_heartbeat_at"] = state.get("last_proactive_at", 0)
            state["last_proactive_at"] = 0
            changed = True
        state["schema_version"] = STATE_SCHEMA_VERSION
        changed = True

    if state.get("last_mode") == "heartbeat" and state.get("last_proactive_at", 0) and not state.get("last_heartbeat_at", 0):
        state["last_heartbeat_at"] = state.get("last_proactive_at", 0)
        state["last_proactive_at"] = 0
        changed = True

    if changed:
        save_json(state_file, state)
    return state


def parse_hhmm(value: str) -> int:
    hh, mm = value.split(":")
    return int(hh) * 100 + int(mm)


def is_in_quiet_hours(hour_min: int, quiet_start: int, quiet_end: int) -> bool:
    if quiet_start == quiet_end:
        return False
    if quiet_start < quiet_end:
        return quiet_start <= hour_min < quiet_end
    return hour_min >= quiet_start or hour_min < quiet_end


def infer_emotion(idle_sec: int, attention_balance: str, thresholds: dict) -> str:
    if idle_sec >= thresholds.get("misses_him_sec", 43200):
        emotion = "misses_him"
    elif idle_sec >= thresholds.get("slightly_needy_sec", 21600):
        emotion = "slightly_needy"
    elif idle_sec >= thresholds.get("present_sec", 10800):
        emotion = "present"
    else:
        emotion = "light_touch"
    if attention_balance == "warm" and idle_sec < 14400:
        emotion = "secure"
    return emotion


def resolve_session_entry(sessions_store: Path, owner_session_key: str) -> dict:
    """Resolve the owner's session entry from sessions.json with case-insensitive fallback."""
    sessions = load_json(sessions_store, {}) or {}
    entry = sessions.get(owner_session_key)
    if isinstance(entry, dict):
        return entry
    lower_key = owner_session_key.lower()
    for key, val in sessions.items():
        if key.lower() == lower_key and isinstance(val, dict):
            return val
    return {}


def resolve_session_file(sessions_store: Path, owner_session_key: str) -> Path | None:
    """Dynamically resolve the owner's session JSONL file from sessions.json."""
    entry = resolve_session_entry(sessions_store, owner_session_key)
    session_file = entry.get("sessionFile")
    if session_file:
        p = Path(session_file)
        if p.exists():
            return p
    return None


def is_noise_text(text: str) -> bool:
    return (
        text.startswith("System:")
        or text.startswith("A new session was started via /new or /reset")
        or text.startswith("Conversation info (untrusted metadata):")
        or any(text.startswith(f"[{d} ") for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        or "要主动给主人" in text
    )


def learn_from_replies(state: dict, recent_messages_path: Path | None):
    last_at = state.get("last_proactive_at", 0)
    if not recent_messages_path or not recent_messages_path.exists() or not last_at:
        return state

    user_messages = []
    for line in recent_messages_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("type") != "message":
            continue
        message = item.get("message", {})
        if message.get("role") != "user":
            continue
        created_at = item.get("createdAt")
        if not created_at:
            continue
        try:
            epoch = int(datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp())
        except ValueError:
            continue
        if epoch <= last_at:
            continue
        text = "\n".join(part.get("text", "") for part in message.get("content", []) if part.get("type") == "text").strip()
        if text and not is_noise_text(text):
            user_messages.append((epoch, text))

    if not user_messages:
        return state

    reply_at, reply_text = user_messages[0]
    delay = max(0, reply_at - last_at)
    attention = "warm" if delay <= 3600 else "steady" if delay <= 21600 else "distant"

    pref = state["preference_profile"]
    if any(token in reply_text for token in ["帮", "处理", "看下", "看看", "查", "修", "改", "重启", "任务", "跑一下"]):
        pref["service"] += 2
    if any(token in reply_text for token in ["在干嘛", "干嘛", "想你", "不理", "晚安", "早点休息", "抱抱", "陪我", "聊"]):
        pref["clingy"] += 2
    if any(token in reply_text for token in ["怎么", "为什么", "啥", "什么", "最近", "今天", "忙什么"]):
        pref["curious"] += 1
    if any(token in reply_text for token in ["哼", "笨", "慢", "又", "还不", "终于"]):
        pref["teasing"] += 1
    if any(token in reply_text for token in ["晚安", "睡", "明天", "收尾", "先这样", "休息"]):
        pref["wrapup"] += 1
    if delay <= 3600:
        pref["service"] += 1
        pref["clingy"] += 1

    state["relationship_state"] = {
        "last_owner_reply_at": reply_at,
        "last_response_delay_sec": delay,
        "last_seen_reply_text": reply_text[:120],
        "attention_balance": attention,
    }
    return state


def recent_context(recent_messages_path: Path | None):
    if not recent_messages_path or not recent_messages_path.exists():
        return []
    rows = []
    for line in recent_messages_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("type") != "message":
            continue
        message = item.get("message", {})
        if message.get("role") != "user":
            continue
        for part in message.get("content", []):
            if part.get("type") != "text":
                continue
            text = part.get("text", "").strip()
            if not text:
                continue
            if is_noise_text(text):
                continue
            rows.append(text)
    return rows[-5:]


def hotspot_snippet(config: dict, now_epoch: int):
    source = config.get("sources", {}).get("x_trending", {})
    if not source.get("enabled"):
        return "disabled", []
    cache_path = Path(source["cache_path"])
    if not cache_path.exists():
        return "agent_fetch_needed", []
    payload = load_json(cache_path, {})
    fetched = payload.get("fetched_at", 0)
    if now_epoch - fetched > source.get("refresh_ttl_sec", 21600):
        return "agent_fetch_needed", []
    highlights = payload.get("highlights") or []
    if highlights:
        return "available", highlights[:5]
    trends = payload.get("trends") or []
    if trends:
        return "available", [t.get("title", "") for t in trends[:5]]
    return "unavailable", []


def load_cron_issues(config: dict):
    runtime = config.get("runtime", {})
    cron_jobs_file = runtime.get("cron_jobs_file")
    owner_key = config.get("delivery", {}).get("owner_session_key", "")

    if cron_jobs_file:
        try:
            payload = load_json(Path(cron_jobs_file), {}) or {}
            jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
            issues = []
            for job in jobs:
                name = job.get("name", "")
                if not name.startswith("companion-"):
                    continue
                session_key = job.get("sessionKey", "")
                if owner_key and session_key and session_key != owner_key:
                    continue
                state = job.get("state") or {}
                if state.get("lastStatus") == "error" or state.get("consecutiveErrors", 0) > 0:
                    detail = state.get("lastError") or state.get("lastRunStatus") or "error"
                    issues.append(f"{name}: {detail}")
            return issues[:3]
        except Exception:
            pass

    jobs_command = runtime.get("jobs_list_command")
    if not jobs_command:
        return []
    try:
        jobs_output = run_shell(jobs_command, {}, expect_json=False, timeout_sec=8)
    except Exception:
        return []
    issues = []
    for line in jobs_output.splitlines():
        if any(tag in line.lower() for tag in [" fail", " error", " timeout"]):
            issues.append(line.strip())
    return issues[:3]


def resolve_mode_profile(config: dict, mode: str):
    behavior = config.get("behavior", {}) if isinstance(config, dict) else {}
    mode_profiles = behavior.get("mode_profiles", {}) if isinstance(behavior, dict) else {}
    profile = mode_profiles.get(mode, {}) if isinstance(mode_profiles, dict) else {}
    style_variants = profile.get("style_variants") or MODE_STYLE_VARIANTS.get(mode) or DEFAULT_STYLE_VARIANTS
    content_types = profile.get("content_types") or MODE_CONTENT_TYPES.get(mode) or DEFAULT_CONTENT_TYPES
    return style_variants, content_types


def choose_style(mode: str, state: dict, idle_sec: int, config: dict):
    pref = state["preference_profile"]
    last_style = state.get("last_style") or ""
    variants, _ = resolve_mode_profile(config, mode)
    variants = variants[:]
    idx = int(time.time()) % len(variants)
    style = variants[idx]
    if pref["service"] > pref["clingy"] and pref["service"] > pref["curious"]:
        style = "service_nudge"
    elif pref["clingy"] > pref["service"] and pref["clingy"] > pref["curious"] and mode != "evening":
        style = "gentle_clingy" if mode in {"night", "heartbeat"} else "soft_curious"
    elif pref["teasing"] >= 3 and mode in {"afternoon", "heartbeat"}:
        style = "teasing_checkin"
    elif pref["wrapup"] >= 2 and mode == "night":
        style = "soft_wrapup"
    if style == last_style:
        for candidate in variants:
            if candidate != last_style:
                style = candidate
                break
    return style


def classify_operational_signal(gateway_healthy: bool, issues: list[str]):
    if not gateway_healthy:
        return {
            "level": "high",
            "kind": "gateway_unhealthy",
            "blend": "service_report",
            "should_mention": True,
        }
    if issues:
        return {
            "level": "medium",
            "kind": "cron_issue",
            "blend": "soft_service_note",
            "should_mention": True,
        }
    return {
        "level": "none",
        "kind": "none",
        "blend": "none",
        "should_mention": False,
    }


def choose_content(mode: str, state: dict, operational_signal: dict, emotion_level: str, config: dict, hotspot_status: str = "unavailable"):
    _, options = resolve_mode_profile(config, mode)
    options = options[:]
    last_content = state.get("last_content_type") or ""
    idx = int(time.time() / 3) % len(options)
    content = options[idx]
    pref = state["preference_profile"]
    if content == last_content:
        for candidate in options:
            if candidate != last_content:
                content = candidate
                break
    if operational_signal.get("level") == "high":
        return "micro_report"
    if mode == "heartbeat":
        if (
            hotspot_status == "available"
            and emotion_level != "misses_him"
            and last_content != "small_share"
            and (pref["curious"] > pref["service"] or pref["teasing"] >= 4)
        ):
            return "small_share"
        if emotion_level == "misses_him":
            return "gentle_miss"
        return "checkin_question"
    if mode == "night" and emotion_level == "misses_him":
        return "gentle_miss"
    if mode == "evening" and pref["service"] >= pref["clingy"]:
        return "task_invite"
    if mode == "afternoon" and pref["teasing"] >= 2:
        return "playful_poke"
    if operational_signal.get("level") == "medium" and mode in {"evening", "night"}:
        return "task_invite"
    return content


def cooldown_anchor_for_mode(state: dict, mode: str) -> int:
    if mode == "heartbeat":
        return max(int(state.get("last_proactive_at", 0) or 0), int(state.get("last_heartbeat_at", 0) or 0))
    return int(state.get("last_proactive_at", 0) or 0)


def record_pending_send(state: dict, mode: str, now_epoch: int, style_variant: str, content_type: str, emotion_level: str):
    state["pending_send"] = {
        "mode": mode,
        "generated_at": now_epoch,
        "style": style_variant,
        "content_type": content_type,
        "emotion_level": emotion_level,
    }


def clear_pending_send(state: dict, mode: str):
    pending = state.get("pending_send", {}) or {}
    if pending.get("mode") == mode:
        state["pending_send"] = {
            "mode": "",
            "generated_at": 0,
            "style": "",
            "content_type": "",
            "emotion_level": "",
        }


def mark_send_success(state: dict, mode: str, now_epoch: int, today: str):
    pending = state.get("pending_send", {}) or {}
    if mode == "heartbeat":
        state["last_heartbeat_at"] = now_epoch
    else:
        state["last_proactive_at"] = now_epoch
    state["daily_count"] += 1
    state["last_mode"] = mode
    if pending.get("mode") == mode:
        if pending.get("style"):
            state["last_style"] = pending["style"]
        if pending.get("content_type"):
            state["last_content_type"] = pending["content_type"]
    state.setdefault("mode_days", {})[mode] = today
    clear_pending_send(state, mode)


def now_parts(timezone: str):
    if timezone:
        os.environ["TZ"] = timezone
        time.tzset()
    now_epoch = int(time.time())
    local = datetime.fromtimestamp(now_epoch)
    return now_epoch, local.strftime("%Y-%m-%d"), int(local.strftime("%H%M"))


def main():
    parser = argparse.ArgumentParser(description="Companion state manager — outputs context JSON for the agent.")
    parser.add_argument("mode", help="Scheduled task name. May be any cron label configured by the user.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--mark-sent", action="store_true", help="Commit pacing state only after the user-visible message was actually delivered.")
    args = parser.parse_args()

    config = load_json(Path(args.config))
    state_file = Path(config["runtime"]["state_file"])
    sessions_store = Path(config["runtime"]["sessions_store_path"])

    # Dynamically resolve session file instead of using hardcoded path
    owner_key = config["delivery"]["owner_session_key"]
    recent_messages_path = resolve_session_file(sessions_store, owner_key)

    state = ensure_state(state_file)
    state = learn_from_replies(state, recent_messages_path)

    now_epoch, today, hour_min = now_parts(config.get("timezone", ""))
    if state.get("day") != today:
        state["day"] = today
        state["daily_count"] = 0

    if args.mark_sent:
        mark_send_success(state, args.mode, now_epoch, today)
        save_json(state_file, state)
        print(
            json.dumps(
                {
                    "status": "recorded",
                    "mode": args.mode,
                    "recorded_at": now_epoch,
                    "cooldown_bucket": "heartbeat" if args.mode == "heartbeat" else "proactive",
                },
                ensure_ascii=False,
            )
        )
        return

    if not args.force:
        quiet_start = parse_hhmm(config["schedule"]["quiet_hours_start"])
        quiet_end = parse_hhmm(config["schedule"]["quiet_hours_end"])
        if is_in_quiet_hours(hour_min, quiet_start, quiet_end):
            save_json(state_file, state)
            print(json.dumps({"status": "skip", "reason": "quiet_hours"}))
            return
        if state["daily_count"] >= config["schedule"]["daily_limit"]:
            save_json(state_file, state)
            print(json.dumps({"status": "skip", "reason": "daily_limit"}))
            return
        if now_epoch - cooldown_anchor_for_mode(state, args.mode) < config["schedule"]["cooldown_sec"]:
            save_json(state_file, state)
            print(json.dumps({"status": "skip", "reason": "cooldown"}))
            return
        if args.mode != "heartbeat" and state.get("mode_days", {}).get(args.mode) == today:
            save_json(state_file, state)
            print(json.dumps({"status": "skip", "reason": "mode_already_sent_today"}))
            return

    owner_session_entry = resolve_session_entry(sessions_store, owner_key)
    owner_updated_ms = owner_session_entry.get("updatedAt", 0)
    owner_updated_sec = owner_updated_ms // 1000
    idle_sec = now_epoch - owner_updated_sec
    idle_hours = idle_sec / 3600.0

    thresholds = config["behavior"]["emotion_thresholds"]
    emotion = infer_emotion(idle_sec, state["relationship_state"].get("attention_balance", "steady"), thresholds)

    # Operational health check
    try:
        health_output = run_shell(config["runtime"]["healthcheck_command"], {}, expect_json=False)
        runtime_ok = "Runtime: running" in health_output
        probe_ok = any(
            marker in health_output
            for marker in ("RPC probe: ok", "Connectivity probe: ok")
        )
        gateway_healthy = runtime_ok and probe_ok
    except Exception:
        gateway_healthy = True
    issues = load_cron_issues(config)
    operational_signal = classify_operational_signal(gateway_healthy, issues)

    style_variant = choose_style(args.mode, state, idle_sec, config)
    hotspot_status, hotspot_items = hotspot_snippet(config, now_epoch)
    content_type = choose_content(args.mode, state, operational_signal, emotion, config, hotspot_status)
    recent_lines = recent_context(recent_messages_path)

    record_pending_send(state, args.mode, now_epoch, style_variant, content_type, emotion)
    save_json(state_file, state)

    # Output context JSON for the agent
    persona = config["persona"]
    output = {
        "status": "ok",
        "mode": args.mode,
        "persona": {
            "name": persona["name"],
            "owner_nickname": persona["owner_nickname"],
            "tone": persona["tone"],
            "relationship_style": persona.get("relationship_style", ""),
        },
        "style_variant": style_variant,
        "content_type": content_type,
        "emotion_level": emotion,
        "idle_hours": round(idle_hours, 1),
        "preference_profile": state["preference_profile"],
        "relationship_state": {
            "attention_balance": state["relationship_state"].get("attention_balance", "steady"),
            "last_response_delay_sec": state["relationship_state"].get("last_response_delay_sec", 0),
        },
        "hotspot_status": hotspot_status,
        "hotspot_items": hotspot_items,
        "operational": {
            "gateway_healthy": gateway_healthy,
            "cron_issues": issues[:3],
            "signal": operational_signal,
            "guidance": {
                "mention_briefly": operational_signal.get("should_mention", False),
                "blend": operational_signal.get("blend", "none"),
                "avoid_alarmist_tone": True,
            },
        },
        "recent_owner_messages": recent_lines,
        "history": {
            "last_mode": state.get("last_mode", ""),
            "last_style": state.get("last_style", ""),
            "last_content_type": state.get("last_content_type", ""),
            "daily_count": state["daily_count"],
            "last_heartbeat_at": state.get("last_heartbeat_at", 0),
        },
        "delivery_tracking": {
            "mark_sent_required": True,
            "mark_sent_command": f"python3 {Path(__file__).resolve()} {args.mode} --config {Path(args.config).resolve()} --mark-sent",
            "cooldown_bucket": "heartbeat" if args.mode == "heartbeat" else "proactive",
        },
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
