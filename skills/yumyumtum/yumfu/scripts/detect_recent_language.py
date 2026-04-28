#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

SAVE_DIR = Path.home() / 'clawd' / 'memory' / 'yumfu' / 'saves'
EVOLUTION_DIR = Path.home() / 'clawd' / 'memory' / 'yumfu' / 'evolution'


def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def normalize_lang(value):
    if not value:
        return None
    v = str(value).strip().lower()
    if v in {'zh', 'zh-cn', 'zh-hans', 'zh-tw', 'zh-hant', 'cn', 'chinese', '中文'}:
        return 'zh'
    if v in {'en', 'en-us', 'en-gb', 'english'}:
        return 'en'
    return None


def classify_text(text: str):
    if not text:
        return None, 0.0
    cjk = len(re.findall(r'[\u4e00-\u9fff]', text))
    latin = len(re.findall(r'[A-Za-z]', text))
    zh_punct = len(re.findall(r'[，。！？；：“”‘’《》【】]', text))
    en_words = len(re.findall(r'\b(the|and|you|your|with|that|this|into|before|after|what|when|where|who)\b', text, re.I))

    zh_score = cjk * 2 + zh_punct * 1.5
    en_score = latin * 0.08 + en_words * 2

    if zh_score == 0 and en_score == 0:
        return None, 0.0
    if zh_score > en_score * 1.2:
        return 'zh', min(0.98, 0.55 + zh_score / max(20.0, zh_score + en_score))
    if en_score > zh_score * 1.2:
        return 'en', min(0.98, 0.55 + en_score / max(20.0, zh_score + en_score))
    return None, 0.4


def main():
    parser = argparse.ArgumentParser(description='Detect recent preferred player language for YumFu')
    parser.add_argument('--user-id', required=True)
    parser.add_argument('--universe', required=True)
    parser.add_argument('--recent-text', action='append', default=[])
    parser.add_argument('--recent-texts-json', default=None)
    args = parser.parse_args()

    save = load_json(SAVE_DIR / args.universe / f'user-{args.user_id}.json') or {}
    evo = load_json(EVOLUTION_DIR / args.universe / f'user-{args.user_id}.json') or {}

    evidences = []
    score = {'zh': 0.0, 'en': 0.0}

    recent_texts = list(args.recent_text)
    if args.recent_texts_json:
        try:
            recent_texts.extend(json.loads(args.recent_texts_json))
        except Exception:
            pass

    recent_votes = {'zh': 0.0, 'en': 0.0}
    for text in recent_texts:
        lang, conf = classify_text(text)
        if lang:
            weight = 5.0 * conf
            score[lang] += weight
            recent_votes[lang] += weight
            evidences.append({'source': 'recent_text', 'lang': lang, 'confidence': round(conf, 3), 'sample': text[:120]})

    save_lang = normalize_lang(save.get('language'))
    world_lang = normalize_lang((save.get('world') or {}).get('language'))

    if save_lang:
        score[save_lang] += 7.5
        evidences.append({'source': 'save.language', 'lang': save_lang, 'confidence': 0.99, 'note': 'canonical_per_save'})

    if world_lang:
        score[world_lang] += 1.0
        evidences.append({'source': 'world.language', 'lang': world_lang, 'confidence': 0.55})

    for field in ['last_story_text', 'last_summary']:
        val = evo.get(field)
        lang, conf = classify_text(val or '')
        if lang:
            score[lang] += 0.45 * conf
            evidences.append({'source': f'sidecar.{field}', 'lang': lang, 'confidence': round(conf, 3)})

    history = evo.get('history', [])[-3:]
    for item in history:
        lang, conf = classify_text((item or {}).get('story_text', ''))
        if lang:
            score[lang] += 0.18 * conf
            evidences.append({'source': 'sidecar.history', 'lang': lang, 'confidence': round(conf, 3)})

    locked_to_save = bool(save_lang)
    override_candidate = None
    if save_lang:
        opposite = 'en' if save_lang == 'zh' else 'zh'
        if recent_votes[opposite] >= 8.5 and recent_votes[opposite] > recent_votes[save_lang] * 1.6:
            override_candidate = opposite
            evidences.append({
                'source': 'recent_text_override_candidate',
                'lang': opposite,
                'confidence': 0.82,
                'note': 'strong recent evidence exists, but save.language remains canonical until explicitly changed'
            })

    preferred = 'en'
    if save_lang:
        preferred = save_lang
    elif score['zh'] > score['en']:
        preferred = 'zh'
    elif score['en'] == score['zh'] == 0:
        preferred = world_lang or 'en'

    total = max(0.001, score['zh'] + score['en'])
    confidence = max(score.values()) / total

    result = {
        'success': True,
        'user_id': args.user_id,
        'universe': args.universe,
        'preferred_language': preferred,
        'confidence': round(confidence, 3),
        'scores': {k: round(v, 3) for k, v in score.items()},
        'locked_to_save_language': locked_to_save,
        'save_language': save_lang,
        'override_candidate': override_candidate,
        'evidence': evidences[:12],
        'fallback_order': [
            'save.language (canonical per save)',
            'recent actual player text as advisory / explicit-switch signal',
            'world language',
            'old sidecar text (weak only)',
            'system fallback'
        ]
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
