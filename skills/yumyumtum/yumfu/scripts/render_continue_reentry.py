#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

BUILD = Path.home() / 'clawd' / 'skills' / 'yumfu' / 'scripts' / 'build_reentry_context.py'


def main():
    parser = argparse.ArgumentParser(description='Render a concise continue-time re-entry prompt for YumFu')
    parser.add_argument('--user-id', required=True)
    parser.add_argument('--universe', required=True)
    parser.add_argument('--recent-text', action='append', default=[])
    parser.add_argument('--recent-texts-json', default=None)
    args = parser.parse_args()

    cmd = ['python3', str(BUILD), '--user-id', args.user_id, '--universe', args.universe]
    for text in args.recent_text:
        cmd.extend(['--recent-text', text])
    if args.recent_texts_json:
        cmd.extend(['--recent-texts-json', args.recent_texts_json])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr.strip() or proc.stdout.strip(), file=sys.stderr)
        sys.exit(proc.returncode)

    data = json.loads(proc.stdout)
    lang = data.get('preferred_language') or 'en'
    summary = data.get('summary_for_reentry')
    hooks = data.get('pending_hooks') or []
    character = data.get('character_name') or 'the player'
    location = data.get('location') or 'the current scene'
    quest = data.get('active_quest') or 'the active quest'
    quest_line = f"你现在仍在推进「{quest}」。" if lang != 'zh' or any('\u4e00' <= ch <= '\u9fff' for ch in quest) else "你现在还在推进当前主线。"

    if lang == 'zh':
        text = (
            f"你回来时，{location} 的局势已经轻轻变了。"
            f"{summary or '你离开的这段时间，暗线还在往前推，只是风声比之前更紧。'}\n\n"
            f"{quest_line}先别做功课，直接接回现场。"
        )
        if hooks:
            text += "\n\n最自然的下一步：\n" + "\n".join(f"- {h}" for h in hooks[:2])
    else:
        text = (
            f"When {character} returns to {location}, the scene has shifted slightly: "
            f"{summary or 'something nearby changed while you were away.'}\n\n"
            f"You are still in the middle of '{quest}'. Do not dump lore; pull the player straight back into the scene."
        )
        if hooks:
            text += "\n\nMost natural next moves:\n" + "\n".join(f"- {h}" for h in hooks[:2])

    print(json.dumps({
        'success': True,
        'preferred_language': lang,
        'text': text,
        'latest_image_path': data.get('latest_image_path'),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
