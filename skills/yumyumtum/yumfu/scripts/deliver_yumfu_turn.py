#!/usr/bin/env python3
"""
Prepare a YumFu gameplay turn for delivery.

This helper centralizes the default turn-delivery pipeline so YumFu turns stop
handling image/TTS/state ad hoc.

What this script DOES:
- prepares a stable per-turn delivery state record
- tries local image generation first via `uv run generate_image.py`
- generates turn TTS via `generate_turn_tts.py`
- builds Telegram-safe caption / follow-up text planning
- returns structured JSON the caller can use to perform the actual sends

What this script DOES NOT do:
- it does not call OpenClaw tools directly
- it does not send messages by itself

Why not? OpenClaw tool delivery (`message`, `image_generate`) is controlled by the
agent runtime, not plain Python scripts. The caller should:
1. run this helper
2. if local image failed, use OpenClaw `image_generate` as fallback
3. send image/text/TTS via `message`
4. mark delivery state after successful sends
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from turn_delivery_state import load as load_state
from turn_delivery_state import save as save_state

SCRIPT_DIR = Path(__file__).resolve().parent
GENERATE_IMAGE = SCRIPT_DIR / "generate_image.py"
GENERATE_TTS = SCRIPT_DIR / "generate_turn_tts.py"
PREPARE_END_STORYBOOK = SCRIPT_DIR / "prepare_end_storybook.py"
OUTBOUND_YUMFU = Path.home() / ".openclaw" / "media" / "outbound" / "yumfu"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "turn"


def run_json(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return {
            "success": False,
            "error": proc.stderr.strip() or proc.stdout.strip() or f"command failed ({proc.returncode})",
            "command": cmd,
        }
    stdout = proc.stdout.strip()
    if not stdout:
        return {"success": False, "error": "empty stdout", "command": cmd}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "stdout was not valid JSON",
            "stdout": stdout,
            "command": cmd,
        }


def run_proc(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "command": cmd,
    }


def plan_caption(story_text: str) -> tuple[str, str | None, str]:
    clean = " ".join(story_text.split())
    if len(clean) <= 900:
        return clean, None, "caption-only"
    short = clean[:220]
    if " " in short:
        short = short.rsplit(" ", 1)[0]
    short = short.rstrip(".,;:!?") + "…"
    return short, story_text.strip(), "caption+followup"


def prepare_image(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    if state.get("image_sent"):
        return {
            "generated": False,
            "skipped": True,
            "reason": "image_already_sent",
            "needs_fallback": False,
        }
    if not args.image_prompt:
        return {
            "generated": False,
            "skipped": True,
            "reason": "no_image_prompt",
            "needs_fallback": False,
        }

    OUTBOUND_YUMFU.mkdir(parents=True, exist_ok=True)
    filename = OUTBOUND_YUMFU / f"{args.universe}-user-{args.user_id}-{slugify(args.turn_id)}.png"
    result = run_proc([
        "uv",
        "run",
        str(GENERATE_IMAGE),
        "--prompt",
        args.image_prompt,
        "--filename",
        str(filename),
        "--resolution",
        args.image_resolution,
        "--aspect-ratio",
        args.aspect_ratio,
    ])
    if result["success"] and filename.exists():
        return {
            "generated": True,
            "path": str(filename),
            "provider": "local-yumfu",
            "needs_fallback": False,
            "stdout": result["stdout"],
        }
    return {
        "generated": False,
        "path": str(filename),
        "provider": "local-yumfu",
        "needs_fallback": True,
        "error": result["stderr"] or result["stdout"] or "local image generation failed",
    }


def prepare_tts(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    if state.get("tts_sent"):
        return {
            "generated": False,
            "skipped": True,
            "reason": "tts_already_sent",
        }
    if not args.story_text.strip():
        return {
            "generated": False,
            "skipped": True,
            "reason": "no_story_text",
        }
    return run_json([
        "uv",
        "run",
        str(GENERATE_TTS),
        "--user-id",
        args.user_id,
        "--universe",
        args.universe,
        "--language",
        args.language,
        "--text",
        args.story_text,
    ])


def prepare_end_storybook(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    if not args.ending_storybook:
        return {
            "generated": False,
            "skipped": True,
            "reason": "ending_storybook_not_requested",
        }
    if state.get("storybook_sent"):
        return {
            "generated": False,
            "skipped": True,
            "reason": "storybook_already_sent",
        }
    cmd = [
        "uv",
        "run",
        str(PREPARE_END_STORYBOOK),
        "--user-id",
        args.user_id,
        "--universe",
        args.universe,
    ]
    if args.session_id:
        cmd += ["--session-id", args.session_id]
    return run_json(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare YumFu turn delivery assets")
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--universe", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--turn-id", required=True)
    parser.add_argument("--chat-id")
    parser.add_argument("--story-text", required=True)
    parser.add_argument("--image-prompt")
    parser.add_argument("--image-resolution", choices=["1K", "2K", "4K"], default="1K")
    parser.add_argument("--aspect-ratio", default="4:5")
    parser.add_argument("--ending-storybook", action="store_true", help="Also prepare final HTML storybook for end-of-journey delivery")
    parser.add_argument("--session-id", help="Optional session id to pin end-storybook generation")
    args = parser.parse_args()

    state = load_state(args.user_id, args.universe, args.turn_id)
    if args.chat_id:
        state["chat_id"] = args.chat_id
        state["updated_at"] = state.get("updated_at")
        save_state(state)

    caption, followup_text, text_mode = plan_caption(args.story_text)
    image = prepare_image(args, state)
    tts = prepare_tts(args, state)
    end_storybook = prepare_end_storybook(args, state)

    payload = {
        "success": True,
        "turn_id": args.turn_id,
        "user_id": args.user_id,
        "universe": args.universe,
        "chat_id": args.chat_id,
        "delivery_state": state,
        "story": {
            "caption": caption,
            "followup_text": followup_text,
            "mode": text_mode,
            "full_text": args.story_text,
        },
        "image": image,
        "tts": tts,
        "end_storybook": end_storybook,
        "next_actions": {
            "send_image_with_caption": bool(image.get("generated")),
            "fallback_to_openclaw_image_generate": bool(image.get("needs_fallback")),
            "send_text_followup": bool(followup_text),
            "send_tts_voice": bool(tts.get("success") and tts.get("generated")),
            "send_end_storybook_html": bool(end_storybook.get("success") and end_storybook.get("generated") and end_storybook.get("send_back_to_chat")),
            "mark_main_text_sent_after_success": True,
            "mark_image_sent_after_success": bool(image.get("generated")),
            "mark_tts_sent_after_success": bool(tts.get("success") and tts.get("generated")),
            "mark_storybook_sent_after_success": bool(end_storybook.get("success") and end_storybook.get("generated") and end_storybook.get("send_back_to_chat")),
        },
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
