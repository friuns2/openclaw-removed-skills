#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEMO_EVENT = ROOT / "demo" / "local_history_event.json"


def run_command(args: list[str], *, stdin: str | None = None) -> tuple[int, str]:
    proc = subprocess.run(args, input=stdin, capture_output=True, text=True, cwd=ROOT)
    raw = proc.stdout.strip() or proc.stderr.strip()
    return proc.returncode, raw


def parse_json(raw: str) -> Any:
    return json.loads(raw) if raw else None


def record(checks: list[dict[str, Any]], name: str, ok: bool, detail: dict[str, Any]) -> None:
    checks.append({"name": name, "ok": ok, "detail": detail})


def main() -> int:
    checks: list[dict[str, Any]] = []

    host_code, host_raw = run_command(
        [sys.executable, "scripts/emotion_engine.py", "host", "--input", str(DEMO_EVENT), "--pretty"]
    )
    try:
        host_result = parse_json(host_raw)
    except json.JSONDecodeError:
        host_result = None
    record(
        checks,
        "host_contract",
        host_code == 0
        and isinstance(host_result, dict)
        and isinstance(host_result.get("schema_version"), str)
        and isinstance(host_result.get("mode"), str)
        and "labels" not in host_result
        and isinstance(host_result.get("routing"), dict)
        and isinstance((host_result.get("guidance") or {}).get("system_prompt_addendum"), str)
        and isinstance(host_result.get("route_reasons"), list)
        and isinstance(host_result.get("response_constraints"), list)
        and "emotion_vector" not in (host_result.get("state") or {}),
        {"exit_code": host_code, "raw": host_raw[:300]},
    )

    with tempfile.TemporaryDirectory(prefix="emotion-skill-download-smoke-") as tmp_dir:
        tmp_path = Path(tmp_dir)

        adapter_code, adapter_raw = run_command(
            [
                sys.executable,
                "scripts/minimal_host_adapter.py",
                "--event",
                str(DEMO_EVENT),
                "--store-dir",
                str(tmp_path / "store-preview"),
                "--view",
                "host",
                "--no-persist",
                "--pretty",
            ]
        )
        try:
            adapter_result = parse_json(adapter_raw)
        except json.JSONDecodeError:
            adapter_result = None
        adapter_payload = adapter_result if isinstance(adapter_result, dict) else {}
        record(
            checks,
            "adapter_preview",
            adapter_code == 0
            and adapter_payload.get("persist_enabled") is False
            and adapter_payload.get("persisted") == {}
            and isinstance((adapter_payload.get("result") or {}).get("routing"), dict),
            {"exit_code": adapter_code, "raw": adapter_raw[:300]},
        )

        output_path = tmp_path / "nested" / "out" / "emotion.json"
        output_code, output_raw = run_command(
            [
                sys.executable,
                "scripts/emotion_engine.py",
                "host",
                "--message",
                "Show me the basis before changing more files.",
                "--output",
                str(output_path),
            ]
        )
        try:
            output_result = parse_json(output_path.read_text(encoding="utf-8")) if output_path.exists() else None
        except json.JSONDecodeError:
            output_result = None
        record(
            checks,
            "nested_output_write",
            output_code == 0 and isinstance(output_result, dict) and isinstance(output_result.get("mode"), str),
            {"exit_code": output_code, "raw": output_raw[:300], "exists": output_path.exists()},
        )

        bad_stdin_code, bad_stdin_raw = run_command(
            [sys.executable, "scripts/emotion_engine.py", "host", "--pretty"],
            stdin="[1,2]",
        )
        record(
            checks,
            "bad_stdin_is_friendly",
            bad_stdin_code == 2 and "Top-level JSON object required" in bad_stdin_raw and "Traceback" not in bad_stdin_raw,
            {"exit_code": bad_stdin_code, "raw": bad_stdin_raw[:300]},
        )

        bad_event = tmp_path / "bad-event.json"
        bad_event.write_text("[1,2]", encoding="utf-8")
        bad_event_code, bad_event_raw = run_command(
            [
                sys.executable,
                "scripts/minimal_host_adapter.py",
                "--event",
                str(bad_event),
                "--store-dir",
                str(tmp_path / "bad-store"),
                "--view",
                "host",
                "--no-persist",
                "--pretty",
            ]
        )
        record(
            checks,
            "bad_event_is_friendly",
            bad_event_code == 2 and "Top-level JSON object required" in bad_event_raw and "Traceback" not in bad_event_raw,
            {"exit_code": bad_event_code, "raw": bad_event_raw[:300]},
        )

    ok = all(item["ok"] for item in checks)
    print(json.dumps({"ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
