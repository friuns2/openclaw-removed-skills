#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

LOAD_GAME = Path.home() / 'clawd' / 'skills' / 'yumfu' / 'scripts' / 'load_game.py'
LOAD_EVOLUTION = Path.home() / 'clawd' / 'skills' / 'yumfu' / 'scripts' / 'load_daily_evolution.py'
DETECT_LANGUAGE = Path.home() / 'clawd' / 'skills' / 'yumfu' / 'scripts' / 'detect_recent_language.py'
OUTBOUND_YUMFU = Path.home() / '.openclaw' / 'media' / 'outbound' / 'yumfu'


def looks_zh(text: str | None) -> bool:
    return bool(text and re.search(r'[\u4e00-\u9fff]', text))


def normalize_lang(value: str | None) -> str:
    v = str(value or '').strip().lower()
    if v in {'zh', 'zh-cn', 'zh-hans', 'zh-tw', 'zh-hant', 'cn', 'chinese', '中文'}:
        return 'zh'
    return 'en'


def fallback_image_prompt(save: dict, evo: dict, preferred_language: str) -> str:
    character = ((save.get('character') or {}).get('name') or 'the player').strip()
    location = (save.get('location') or 'the current scene').strip()
    universe = (save.get('universe') or save.get('world_id') or '').strip()
    summary = (evo.get('last_summary') or '').strip()

    if preferred_language == 'zh':
        return (
            f"YumFu 游戏续玩场景图，主角 {character}，地点 {location}，"
            f"延续当前存档剧情，不要像新开局，不要做成独立海报；"
            f"重点表现回到现场时的局势压力与继续推进感。"
            f"{(' 当前风声：' + summary) if summary and looks_zh(summary) else ''}"
            f" 世界观：{universe or '当前世界'}。 cinematic fantasy illustration, no text"
        )

    return (
        f"YumFu continue-time gameplay image for {character} at {location}, visual continuity with the current save, "
        f"not a fresh opening scene, not a disconnected poster, emphasize immediate re-entry into the ongoing situation. "
        f"{('Current pressure: ' + summary + '. ') if summary and not looks_zh(summary) else ''}"
        f"World: {universe or 'current world'}. cinematic fantasy illustration, no text"
    )


def pick_latest_image(user_id: str, universe: str) -> str | None:
    if not OUTBOUND_YUMFU.exists():
        return None
    candidates = sorted(
        OUTBOUND_YUMFU.glob(f'{universe}-user-{user_id}-*.png'),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return str(candidates[0]) if candidates else None


def main():
    parser = argparse.ArgumentParser(description='Build a concise YumFu re-entry context from save + daily evolution sidecar')
    parser.add_argument('--user-id', required=True)
    parser.add_argument('--universe', required=True)
    parser.add_argument('--recent-text', action='append', default=[])
    parser.add_argument('--recent-texts-json', default=None)
    args = parser.parse_args()

    save_proc = subprocess.run([
        'python3', str(LOAD_GAME), '--user-id', args.user_id, '--universe', args.universe, '--quiet'
    ], capture_output=True, text=True)
    if save_proc.returncode != 0:
        print(save_proc.stderr.strip() or save_proc.stdout.strip(), file=sys.stderr)
        sys.exit(save_proc.returncode)

    save_payload = json.loads(save_proc.stdout)
    evo_proc = subprocess.run([
        'python3', str(LOAD_EVOLUTION), '--user-id', args.user_id, '--universe', args.universe
    ], capture_output=True, text=True)
    evo_payload = json.loads(evo_proc.stdout) if evo_proc.returncode == 0 and evo_proc.stdout.strip() else {'exists': False, 'data': None}

    save = save_payload.get('data') or {}
    evo = evo_payload.get('data') or {}
    hooks = evo.get('pending_hooks', [])[:3]

    lang_cmd = [
        'python3', str(DETECT_LANGUAGE), '--user-id', args.user_id, '--universe', args.universe
    ]
    for text in args.recent_text:
        lang_cmd.extend(['--recent-text', text])
    if args.recent_texts_json:
        lang_cmd.extend(['--recent-texts-json', args.recent_texts_json])

    lang_proc = subprocess.run(lang_cmd, capture_output=True, text=True)
    lang_payload = json.loads(lang_proc.stdout) if lang_proc.returncode == 0 and lang_proc.stdout.strip() else {
        'preferred_language': (save.get('language') or 'en'), 'confidence': 0.0
    }

    preferred_language = lang_payload.get('preferred_language') or (save.get('language') or 'en')
    raw_summary = evo.get('last_summary')
    if preferred_language == 'zh' and raw_summary and not looks_zh(raw_summary):
        summary_for_reentry = None
    elif preferred_language == 'en' and raw_summary and looks_zh(raw_summary):
        summary_for_reentry = None
    else:
        summary_for_reentry = raw_summary

    result = {
        'success': True,
        'character_name': (save.get('character') or {}).get('name'),
        'location': save.get('location'),
        'active_quest': ((save.get('quests') or [{}])[0]).get('name'),
        'last_daily_summary': raw_summary,
        'summary_for_reentry': summary_for_reentry,
        'pending_hooks': hooks,
        'preferred_language': preferred_language,
        'language_confidence': lang_payload.get('confidence'),
        'locked_to_save_language': lang_payload.get('locked_to_save_language', False),
        'latest_image_path': pick_latest_image(args.user_id, args.universe),
        'image_prompt': (evo.get('last_image_prompt') or '').strip() or fallback_image_prompt(save, evo, normalize_lang(preferred_language)),
        'reentry_instruction': (
            'When the player returns, briefly pull them back into the scene using the latest daily evolution summary, '
            'then offer one easy natural next move in the player\'s preferred language. '
            'If the save has a canonical language, do not drift away from it automatically. '
            'Continue-time delivery is image-first: reuse the latest save-matched image when available; otherwise generate a fresh image and send it with the re-entry hook. '
            'Do not dump lore or system bulletins.'
        ),
        'continue_prompt_template': {
            'zh': '先用一句话把玩家拉回当前场景，再给 1-2 个最自然的继续动作选项；若有最近图片，一起发。',
            'en': 'Pull the player back into the scene in one short paragraph, then offer 1-2 natural continuation moves; include the latest image when available.'
        }
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
