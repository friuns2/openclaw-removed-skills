#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LOAD_GAME = Path.home() / 'clawd' / 'skills' / 'yumfu' / 'scripts' / 'load_game.py'
DETECT_LANGUAGE = Path.home() / 'clawd' / 'skills' / 'yumfu' / 'scripts' / 'detect_recent_language.py'
WORLD_DIR = Path.home() / 'clawd' / 'skills' / 'yumfu' / 'worlds'


def load_world(universe: str):
    direct = WORLD_DIR / f'{universe}.json'
    nested = WORLD_DIR / universe / 'world.json'
    path = direct if direct.exists() else nested
    if not path.exists():
        raise FileNotFoundError(f'World config not found for {universe}')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f), str(path)


def main():
    parser = argparse.ArgumentParser(description='Prepare dynamic YumFu daily evolution context')
    parser.add_argument('--user-id', required=True)
    parser.add_argument('--universe', required=True)
    args = parser.parse_args()

    load = subprocess.run(
        ['python3', str(LOAD_GAME), '--user-id', args.user_id, '--universe', args.universe, '--quiet'],
        capture_output=True, text=True
    )
    if load.returncode != 0:
        print(load.stderr.strip() or load.stdout.strip(), file=sys.stderr)
        sys.exit(load.returncode)

    payload = json.loads(load.stdout)
    if not payload.get('exists') or not payload.get('data'):
        print(json.dumps({'success': False, 'error': 'Save not found'}))
        sys.exit(1)

    save = payload['data']
    world, world_path = load_world(args.universe)

    character = save.get('character', {})
    relationships = save.get('relationships', {})
    quests = save.get('quests', [])
    active_quests = [q for q in quests if q.get('status') == 'active']
    de = save.get('daily_evolution', {})

    system_goal = (
        'Generate one plausible daily world-evolution update grounded in the player save and world setting. '
        'Do not hardcode canned events. Infer what happened while the player was offline. '
        'The update should create intrigue, pressure, or momentum, but must not auto-finish the main story or kill the player arbitrarily. '
        'Treat the player main save as canonical and read-only for this daily evolution run; write soft outcomes to sidecar state only.'
    )

    mutation_guardrails = [
        'Allowed: rumor flags, faction pressure, npc movement, relationship shifts, leads, patrol changes, route pressure, local losses/gains.',
        'Avoid: killing the player offline, auto-finishing the main story, removing critical items without explanation, giant irreversible choices every day.',
        'Return structured save mutations that are bounded and plausible.'
    ]

    preferred_language = save.get('language') or world.get('language') or 'en'
    language_confidence = 0.0
    try:
        lang_proc = subprocess.run(
            ['python3', str(DETECT_LANGUAGE), '--user-id', args.user_id, '--universe', args.universe],
            capture_output=True, text=True
        )
        if lang_proc.returncode == 0 and lang_proc.stdout.strip():
            lang_payload = json.loads(lang_proc.stdout)
            preferred_language = lang_payload.get('preferred_language') or preferred_language
            language_confidence = lang_payload.get('confidence') or 0.0
    except Exception:
        pass
@@
         'language_policy': {
             'priority': [
-                'recent actual player conversation language',
-                'save.language',
+                'save.language (canonical per save)',
+                'recent actual player conversation language (advisory unless explicit switch)',
                 'world default language',
                 'system fallback'
             ],
             'preferred_language_hint': preferred_language,
             'confidence': language_confidence,
-            'instruction': 'Write the daily evolution in the same language the player has been naturally using most recently, unless there is a strong world-specific reason not to.'
+            'instruction': 'Write the daily evolution in the save\'s canonical language first. Do not drift languages just because old sidecar text or weak recent evidence points elsewhere. Only switch languages when the player clearly and explicitly changes play language.'
         },

    prompt = {
        'goal': system_goal,
        'world': {
            'id': world.get('id', args.universe),
            'name_en': world.get('name_en') or world.get('name') or args.universe,
            'name_zh': world.get('name_zh'),
            'genre': world.get('genre'),
            'themes': world.get('themes', []),
            'description_en': world.get('description_en'),
            'description_zh': world.get('description_zh'),
            'world_path': world_path,
        },
        'player': {
            'user_id': args.user_id,
            'character_name': character.get('name'),
            'role': character.get('role'),
            'house': character.get('house'),
            'traits': character.get('trait') or character.get('traits'),
            'location': save.get('location'),
            'inventory': save.get('inventory', []),
            'relationships': relationships,
            'active_quests': active_quests,
            'flags': save.get('flags', {}),
            'save_language': save.get('language'),
            'preferred_language_hint': preferred_language,
            'daily_evolution': de,
        },
        'language_policy': {
            'priority': [
                'recent actual player conversation language',
                'save.language',
                'world default language',
                'system fallback'
            ],
            'preferred_language_hint': preferred_language,
            'confidence': language_confidence,
            'instruction': 'Write the daily evolution in the same language the player has been naturally using most recently, unless there is a strong world-specific reason not to.'
        },
        'sidecar_policy': {
            'main_save_mutation': 'forbidden in MVP',
            'write_target': '~/clawd/memory/yumfu/evolution/{universe}/user-{id}.json',
            'allowed_outputs': ['summary', 'story_text', 'image_prompt', 'severity', 'pending_hooks', 'soft world pressure', 'rumor threads']
        },
        'output_requirements': {
            'story_words': '100-220 words',
            'must_include': [
                'one meaningful world development',
                'one player-relevant consequence or pressure signal',
                'one hook inviting the player back into active play',
                'one image prompt matched to the update'
            ],
            'response_json_schema': {
                'summary': 'short summary string',
                'story_text': 'daily evolution notification text',
                'image_prompt': 'scene image prompt',
                'severity': 'minor|medium|major',
                'pending_hooks': ['list of non-destructive hooks to surface next time the player actively plays'],
                'sidecar_meta': {
                    'rumor_threads': 'list of rumor/pressure threads',
                    'faction_movements': 'list of soft world changes',
                    'npc_watchlist': 'list of names or unknown actors to watch'
                }
            }
        },
        'guardrails': mutation_guardrails,
        'generated_at': datetime.now().isoformat()
    }

    print(json.dumps({'success': True, 'context': prompt}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
