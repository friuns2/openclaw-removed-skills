#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import emotion_engine as ee


STORE_FILES = {
    "user_profile": "user_profile.json",
    "last_state": "last_state.json",
    "calibration_state": "calibration_state.json",
}
PROFILE_MAPPING_FIELDS = ("baseline", "persona_traits", "big5", "affective_prior")


def load_json(path: Path, default: Any, *, ignore_errors: bool = False) -> tuple[Any, str]:
    if not path.exists():
        return default, ""
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except json.JSONDecodeError as exc:
        message = f"Invalid JSON in {path}: {exc}"
        if ignore_errors:
            return default, message
        raise ValueError(message) from exc


def require_json_object(value: Any, source: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    value_type = type(value).__name__
    raise ValueError(f"Top-level JSON object required: {source} got {value_type}")


def dump_json(data: Any, pretty: bool) -> str:
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = merge_dict(base[key], value)
        else:
            merged[key] = value
    return merged


def load_store(store_dir: Path, ignore_bad_store: bool) -> tuple[dict[str, Any], dict[str, str]]:
    store: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for key, filename in STORE_FILES.items():
        value, error = load_json(store_dir / filename, {}, ignore_errors=ignore_bad_store)
        if error:
            errors[key] = error
        store[key] = value if isinstance(value, dict) else {}
    return store, errors


def build_payload(event: dict[str, Any], store: dict[str, Any], adapter_warnings: list[str]) -> dict[str, Any]:
    payload = dict(event)
    event_profile = payload.get("user_profile")
    store_profile = store.get("user_profile", {})
    if isinstance(event_profile, dict):
        for key in PROFILE_MAPPING_FIELDS:
            if key in event_profile and not isinstance(event_profile.get(key), dict):
                adapter_warnings.append(f"user_profile.{key}_not_mapping.forwarded_to_engine")
        payload["user_profile"] = merge_dict(store_profile, event_profile)
    elif "user_profile" in payload:
        adapter_warnings.append("user_profile_not_mapping.forwarded_to_engine")
    else:
        payload["user_profile"] = store_profile
    if store.get("last_state") and "last_state" not in payload:
        payload["last_state"] = store["last_state"]
    if store.get("calibration_state") and "calibration_state" not in payload:
        payload["calibration_state"] = store["calibration_state"]
    return payload


def build_persisted_profile(payload: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    payload_profile = payload.get("user_profile") or {}
    base_profile = dict(payload_profile) if isinstance(payload_profile, dict) else {}
    memory_update = result["memory_update"]
    base_profile["baseline"] = memory_update["proposed_baseline"]
    base_profile["persona_traits"] = memory_update["proposed_persona_traits"]
    base_profile["affective_prior"] = memory_update["proposed_affective_prior"]
    if "timezone" not in base_profile and result["profile_state"]["timezone"]:
        base_profile["timezone"] = result["profile_state"]["timezone"]
    if "work_hours_local" not in base_profile and result["profile_state"]["work_hours_local"]:
        base_profile["work_hours_local"] = result["profile_state"]["work_hours_local"]
    return base_profile


def build_persisted_state(result: dict[str, Any]) -> dict[str, Any]:
    confirmed = result["confirmed_state"]
    return {
        "vector": confirmed["vector"],
        "emotion_vector": confirmed["emotion_vector"],
        "ttl_seconds": confirmed["ttl_seconds"],
    }


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(text)
            tmp_path = Path(handle.name)
        os.replace(tmp_path, path)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def persist_store(store_dir: Path, payload: dict[str, Any], result: dict[str, Any]) -> dict[str, str]:
    store_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: store_dir / filename for key, filename in STORE_FILES.items()}
    atomic_write_text(paths["user_profile"], dump_json(build_persisted_profile(payload, result), pretty=True))
    atomic_write_text(paths["last_state"], dump_json(build_persisted_state(result), pretty=True))
    atomic_write_text(paths["calibration_state"], dump_json(result["memory_update"]["proposed_calibration_state"], pretty=True))
    return {key: str(path) for key, path in paths.items()}


def run_event(event_path: Path, store_dir: Path, pretty: bool, persist: bool, view: str, ignore_bad_store: bool) -> dict[str, Any]:
    event_raw, _ = load_json(event_path, {})
    event = require_json_object(event_raw, f"host event {event_path}")
    if not event:
        raise ValueError(f"Event payload is empty: {event_path}")
    store, store_errors = load_store(store_dir, ignore_bad_store)
    adapter_warnings: list[str] = []
    for key in store_errors:
        adapter_warnings.append(f"corrupt_store_ignored.{key}")
    payload = build_payload(event, store, adapter_warnings)
    result = ee.run_pipeline(payload)
    persisted = persist_store(store_dir, payload, result) if persist else {}
    return {
        "adapter": "minimal_host_adapter",
        "adapter_warnings": adapter_warnings,
        "event_path": str(event_path),
        "store_dir": str(store_dir),
        "store_errors": store_errors,
        "loaded_store": {key: bool(value) for key, value in store.items()},
        "persist_enabled": persist,
        "persisted": persisted,
        "result": ee.build_host_output(result) if view == "host" else result,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Minimal host adapter for the emotion skill.")
    parser.add_argument("--event", required=True, help="Path to a host event JSON payload.")
    parser.add_argument("--store-dir", required=True, help="Directory for persisted profile, state, and calibration files.")
    parser.add_argument("--view", choices=("full", "host"), default="full", help="Output the full engine result or the compact host contract.")
    parser.add_argument("--no-persist", action="store_true", help="Run without writing profile, state, or calibration files.")
    parser.add_argument("--ignore-bad-store", action="store_true", help="Skip corrupt store files and continue with empty store values.")
    parser.add_argument("--output", help="Optional path for the rendered output JSON.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    event_path = Path(args.event)
    store_dir = Path(args.store_dir)
    if not event_path.exists():
        parser.exit(2, f"Host event file not found: {event_path}\n")
    try:
        rendered_obj = run_event(event_path, store_dir, args.pretty, persist=not args.no_persist, view=args.view, ignore_bad_store=args.ignore_bad_store)
    except json.JSONDecodeError as exc:
        parser.exit(2, f"Invalid JSON input: {exc}\n")
    except ValueError as exc:
        parser.exit(2, f"{exc}\n")
    rendered = dump_json(rendered_obj, args.pretty)
    if args.output:
        try:
            atomic_write_text(Path(args.output), rendered)
        except OSError as exc:
            parser.exit(2, f"Could not write output {args.output}: {exc}\n")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
