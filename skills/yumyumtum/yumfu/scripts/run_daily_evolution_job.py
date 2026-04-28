#!/usr/bin/env python3
import argparse
import json
import hashlib
from datetime import datetime
from pathlib import Path

WORLD_DIR = Path.home() / 'clawd' / 'skills' / 'yumfu' / 'worlds'
SAVE_DIR = Path.home() / 'clawd' / 'memory' / 'yumfu' / 'saves'
EVOLUTION_DIR = Path.home() / 'clawd' / 'memory' / 'yumfu' / 'evolution'


def load_json(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_world(universe: str):
    direct = WORLD_DIR / f'{universe}.json'
    nested = WORLD_DIR / universe / 'world.json'
    path = direct if direct.exists() else nested
    if not path.exists():
        raise FileNotFoundError(f'World config not found for {universe}')
    return load_json(path), path


def load_save(user_id: str, universe: str):
    path = SAVE_DIR / universe / f'user-{user_id}.json'
    if not path.exists():
        raise FileNotFoundError(f'Save not found: {path}')
    return load_json(path), path


def load_sidecar(user_id: str, universe: str):
    path = EVOLUTION_DIR / universe / f'user-{user_id}.json'
    if not path.exists():
        return {}, path
    try:
        return load_json(path), path
    except Exception:
        return {}, path


def pick_severity(key: str) -> str:
    n = int(hashlib.sha256(key.encode()).hexdigest(), 16) % 10
    if n == 0:
        return 'major'
    if n <= 3:
        return 'medium'
    return 'minor'


def clean_name(text: str | None, fallback: str) -> str:
    if not text:
        return fallback
    return str(text).strip()


def normalize_lang(value: str | None) -> str | None:
    if not value:
        return None
    v = str(value).strip().lower()
    if v in {'zh', 'zh-cn', 'zh-hans', 'zh-tw', 'zh-hant', 'cn', 'chinese', '中文'}:
        return 'zh'
    if v in {'en', 'en-us', 'en-gb', 'english'}:
        return 'en'
    return None


def got_update(save: dict, world: dict, sidecar: dict) -> dict:
    character = save.get('character', {})
    name = clean_name(character.get('name'), 'the Dornish knight')
    location = clean_name(save.get('location'), 'the southern road')
    relationships = save.get('relationships', {})
    quest = (save.get('quests') or [{}])[0]
    intel = quest.get('intel', {})
    history = sidecar.get('history', [])
    severity = pick_severity(f"game-of-thrones:{name}:{location}:{len(history)}:{datetime.now().date().isoformat()}")

    first_destination = intel.get('first_destination', 'Planky Town')
    house = clean_name(character.get('house'), 'Martell')
    prince_name = 'Prince Doran'
    trust = relationships.get(prince_name, 0)
    lang = normalize_lang(save.get('language')) or 'en'

    if lang == 'zh':
        seeds = [
            {
                'summary': '码头上的红蜡信又动了一次。',
                'story_text': f"天色刚薄下来，关于{first_destination}的风声已经先一步传到你耳里：一条平底船明明没有公开卸出什么像样货物，岸边却有三个人为了那封深红封蜡的短讯争得过分厉害。缆绳吃水太深，不像只装盐货；而一旦有人瞥见马泰尔的颜色，码头工的声音就立刻低了下去。真正被人护着的，也许不是货，而是那封决定货该往哪走的信。若多兰亲王要你查的暗线确实埋在南岸，这里就是它第一次露出木头、绳索和证人的地方。你现在赶过去，还来得及在账本开封前抓到最早一手。你先盯信，先盯货，还是先盯拿信的人？",
                'hooks': [
                    '先盯那封红蜡信下一次换手。',
                    '先看货物在开账前会被挪去哪里。'
                ],
                'meta': {
                    'rumor_threads': ['码头红蜡信再度出现'],
                    'faction_movements': ['码头搬运线在高压下运作'],
                    'npc_watchlist': ['接信的人', '用假账的船主']
                },
                'image_prompt': 'Pre-dawn Planky Town docks in Dorne, flat-bottomed boat, suspicious dockhands arguing over a deep-red sealed note, covert supply-line tension, Game of Thrones dark fantasy oil painting style'
            },
            {
                'summary': '信使没到，但盯梢的人先到了。',
                'story_text': f"天还没彻底亮，{first_destination}的商贩之间已经开始低声谈论一个没到场的信使；可更要命的是，在同一批货登记之前，已有两拨生面孔先后在码头边打听它。多兰亲王提醒过你的那类事，往往不是看见了谁，而是谁明明该出现却没有出现。这条线没断，只是被人悄悄掰弯了。时机不对，面孔不对，大家对这个空缺的沉默更不对。若你现在下场，也许能在对方反应过来前，看清到底是谁在盯这条线。你是先混进人群里摸过去，还是先按住不动，等其中一个人自己露破绽？",
                'hooks': [
                    '先混进晨市里，把盯梢的人认出来。',
                    '先等第一个离开码头的人露出去向。'
                ],
                'meta': {
                    'rumor_threads': ['南线失踪信使'],
                    'faction_movements': ['货还没记账，观察者先到了'],
                    'npc_watchlist': ['码头盯梢人', '失踪信使']
                },
                'image_prompt': 'Morning crowd gathering at Planky Town docks, absent courier, two covert watchers scanning the shipment line, Dorne intrigue, Game of Thrones oil painting style'
            },
            {
                'summary': '补给线还在走，但谨慎得不对劲。',
                'story_text': f"南边那条线并没有停，这才是最危险的地方。天刚亮，车还是往{first_destination}去，船夫还是在骂，记账的人还是在湿木板上划着数字，可所有动作都带着一种不该有的谨慎。原本该急的人忽然不急了，原本该吵的人忽然安静了，甚至一小片干血色的红蜡痕都比早市更早出现在了码头木板上。这说明线已经被碰过，却还没被公开掐断。有人想让多兰的货继续走，只走到没人来得及惊慌、刀子却已经伸进去的位置。你若现在插手，面对的不是一条正常流动的货线，而是一条等着看谁先露头的暗流。你先试账本，先试搬运的人，还是先试那条船？",
                'hooks': [
                    '先查账本在墨迹未干前改过哪里。',
                    '先盯那个小心得过头的搬运人。'
                ],
                'meta': {
                    'rumor_threads': ['货线继续运行但账目受压'],
                    'faction_movements': ['补给路线在暗中受控'],
                    'npc_watchlist': ['账房', '过分谨慎的搬运人', '船主']
                },
                'image_prompt': 'Early morning Dorne supply wagons and dock ledgers at Planky Town, tense cautious workers, red wax fragment on wooden boards, covert sabotage mood, Game of Thrones oil painting style'
            }
        ]
    else:
        seeds = [
            {
                'summary': 'A red-sealed message has moved again at the docks.',
                'story_text': f"By the time dawn thins over the coast road, word reaches you that a flat-bottomed boat at {first_destination} unloaded nothing in public, yet three men argued over a deep-red sealed note beside the pier. The cargo ropes bit too deep for salt alone, and the dockhands went quiet the moment Martell colors came into view. Someone is moving goods under a false manifest, and someone else is more interested in the message than the cargo itself. If Doran’s hidden line truly runs through the southern coast, then this is not random dockside noise — it is the first place where the lie has touched wood, rope, and witnesses. You are close enough now to arrive before the morning ledgers settle. Do you shadow the note, the cargo, or the men holding it?",
                'hooks': [
                    'Follow the red-sealed note before it changes hands again.',
                    'Watch the cargo before anyone opens the books for the day.'
                ],
                'meta': {
                    'rumor_threads': ['red-sealed note at the docks'],
                    'faction_movements': ['dockside handlers behaving under pressure'],
                    'npc_watchlist': ['unknown note recipient', 'boat captain with false manifest']
                },
                'image_prompt': 'Pre-dawn Planky Town docks in Dorne, flat-bottomed boat, suspicious dockhands arguing over a deep-red sealed note, covert supply-line tension, Game of Thrones dark fantasy oil painting style'
            },
            {
                'summary': 'A courier failed to arrive, but the watchers did.',
                'story_text': f"Before full sunrise, a small knot of traders in {first_destination} begins whispering about a courier who never arrived, though two separate watchers appeared at the pier asking after the same shipment. That is the kind of absence Doran warned you about: the visible messenger matters less than the unseen hand expecting him. The route is still alive, which means whoever touched it did not shut it down — they bent it. The timing is wrong, the faces are wrong, and the silence around the missing courier is wrongest of all. If you move now, you may catch the people watching the line before they realize the line is watching them back. Do you press into the crowd as another traveler, or hold off until one of them breaks pattern?",
                'hooks': [
                    'Blend into the morning crowd and identify who came to watch the missing courier.',
                    'Wait for the first watcher to peel away from the pier.'
                ],
                'meta': {
                    'rumor_threads': ['missing courier on southern line'],
                    'faction_movements': ['unknown observers appear before cargo is logged'],
                    'npc_watchlist': ['silent watcher at the pier', 'missing courier']
                },
                'image_prompt': 'Morning crowd gathering at Planky Town docks, absent courier, two covert watchers scanning the shipment line, Dorne intrigue, Game of Thrones oil painting style'
            },
            {
                'summary': 'The supply line still moves, but under the wrong kind of caution.',
                'story_text': f"The southern line has not stopped. That is what makes it dangerous. By first light, the wagons still roll toward {first_destination}, the boatmen still curse, and the tally-men still scratch marks into wet ledgers — but everything carries the wrong kind of caution. Men who should be impatient are careful. Men who should be loud are quiet. And a wax fragment the color of dried blood has already reached the dockside boards ahead of the morning trade. That means the line is compromised, but not openly broken. Someone wants Doran’s supplies to keep moving just enough that nobody panics until the knife is already in too deep. If you step in now, you step into a flow that expects not a rider in Martell colors, but a fool who never learned to read silence. Which current do you test first: the manifests, the handlers, or the boat itself?",
                'hooks': [
                    'Check the manifests before the ink dries.',
                    'Watch which handler acts too carefully for an honest morning.'
                ],
                'meta': {
                    'rumor_threads': ['moving line, compromised books'],
                    'faction_movements': ['supply route operating under covert pressure'],
                    'npc_watchlist': ['ledger keeper', 'overcareful handler', 'boatmaster']
                },
                'image_prompt': 'Early morning Dorne supply wagons and dock ledgers at Planky Town, tense cautious workers, red wax fragment on wooden boards, covert sabotage mood, Game of Thrones oil painting style'
            }
        ]

    idx = int(hashlib.md5(f"{name}:{location}:{len(history)}:{trust}:{house}".encode()).hexdigest(), 16) % len(seeds)
    chosen = seeds[idx]
    chosen['severity'] = severity
    chosen['world_id'] = world.get('id', 'game-of-thrones')
    chosen['character_name'] = name
    chosen['location_context'] = location
    chosen['recap_text'] = build_recap(save, world, sidecar)
    chosen['image_prompt'] = chosen['image_prompt'] + ', visual continuity from the player\'s existing Doran/Martell covert route investigation, same ongoing arc, not a disconnected new scene'
    return chosen


def sengoku_update(save: dict, world: dict, sidecar: dict) -> dict:
    character = save.get('character', {})
    name = clean_name(character.get('name'), '无名之辈')
    location = clean_name(save.get('location'), '城下町')
    role = clean_name(character.get('role'), '乱世之人')
    faction = clean_name(character.get('house'), '无主之势')
    history = sidecar.get('history', [])
    severity = pick_severity(f"sengoku:{name}:{location}:{role}:{len(history)}:{datetime.now().date().isoformat()}")

    seeds = [
        {
            'summary': '城里先传开的不是命令，而是风声。',
            'story_text': f"夜还没彻底退，{location}里先传开的不是官样命令，而是一阵更值钱的风声：昨夜有人悄悄问价，要买下一批新到港的火绳枪，却不肯留下主家名号。茶屋、仓场、花街和码头之间都有人在压着声量打听，像谁都知道要出事，却都想比别人晚一步露面。你现在的身份是{role}，站在{faction}这一边，可乱世里真正保命的从来不是名头，而是谁先抓住这阵风往哪边吹。只要你今晚抢先找到第一个放风的人，你就不只是听消息的人，而是能决定谁先拿到枪、谁先丢掉脑袋的人。你是先查火枪的去向，还是先查是谁故意放出这阵风？",
            'hooks': ['先追火枪去向。', '先查放风的人。'],
            'meta': {
                'rumor_threads': ['火绳枪暗中问价'],
                'faction_movements': ['多方势力同时试探军火流向'],
                'npc_watchlist': ['放风的茶屋耳目', '匿名军火买主']
            },
            'image_prompt': 'Torchlit Sengoku castle town before dawn, whispers spreading through tea houses and alleys, hidden gun deal rumors, banners, ash, lacquer armor, Japanese ukiyo-e woodblock print style, bold ink outlines, textured washi paper, flat layered colors'
        },
        {
            'summary': '花街里先有人开口，城门外才会死人。',
            'story_text': f"今夜{location}最先热起来的不是城门，而是花街。有人带着比银子更重的口风进了包间，说某位将领已经在私下募人，不是为了守城，是为了在下一场会盟之前先把不该活的人做掉。真正可怕的不是这句风声本身，而是说这句话的人明显不怕被听见——这说明放话的人不是傻，就是背后有人兜着。你这种{role}若只把它当闲话，就会错过把手伸进真正权力缝里的机会。若你先找对人，今夜你能收的就不只是消息，还可能是一条债、一把刀、或一个将来要为你卖命的人。你是先盯那个最会传话的女人，还是先查她背后的金主？",
            'hooks': ['先盯最会传话的人。', '先查出谁在背后付钱。'],
            'meta': {
                'rumor_threads': ['花街放出暗杀风声'],
                'faction_movements': ['有人在会盟前秘密募人'],
                'npc_watchlist': ['最会传话的花街女人', '出钱的幕后金主']
            },
            'image_prompt': 'Sengoku pleasure quarter at night, ambitious courtesan whispering fatal secrets behind lantern screens, armed retainers outside, Japanese ukiyo-e woodblock print style, bold ink outlines, textured washi paper, elegant but dangerous composition'
        },
        {
            'summary': '粮、枪和人情，今夜至少有一样要先断。',
            'story_text': f"{location}今夜的表面还算平静，可真正懂行的人都看得出来：粮、枪和人情三样东西里，至少有一样很快要先断。仓里的人突然开始惜米，带枪的人开始惜火药，原本逢人都点头的中间商也突然话少了一半。这种静不是平安，是有人已经提前闻到了血。你现在身在{faction}，又顶着{role}的身份，如果还等别人把局势讲明白，往往就只能替别人收残局。可若你趁现在先拿住一个关节，不管是仓、枪、还是人脉，等明天城里真正乱起来时，你就不是被卷进去的人，而是能收价的人。你先掐哪一处？",
            'hooks': ['先控制粮。', '先控制枪。', '先控制中间人。'],
            'meta': {
                'rumor_threads': ['仓、枪、人情同时收紧'],
                'faction_movements': ['多方为即将到来的乱局做准备'],
                'npc_watchlist': ['惜米的仓吏', '惜火药的枪头', '突然沉默的中间商']
            },
            'image_prompt': 'Sengoku storehouses and gun racks under lantern light, tense merchants and ashigaru sensing coming bloodshed, Japanese ukiyo-e woodblock print style, bold ink outlines, textured washi paper, smoke and red-black-indigo-gold palette'
        }
    ]

    idx = int(hashlib.md5(f"{name}:{location}:{role}:{faction}:{len(history)}".encode()).hexdigest(), 16) % len(seeds)
    chosen = seeds[idx]
    chosen['severity'] = severity
    chosen['world_id'] = world.get('id', 'sengoku')
    chosen['character_name'] = name
    chosen['location_context'] = location
    chosen['recap_text'] = build_recap(save, world, sidecar)
    chosen['image_prompt'] = chosen['image_prompt'] + ' , visual continuity from the player\'s current Sengoku campaign arc, not a cold standalone vignette'
    return chosen


def build_recap(save: dict, world: dict, sidecar: dict) -> str:
    character = save.get('character', {}) or {}
    quests = save.get('quests') or []
    first_quest = quests[0] if quests else {}
    name = clean_name(character.get('name'), 'you')
    world_id = clean_name(world.get('id'), '')
    world_name = clean_name(world.get('name_en') or world.get('name') or world.get('name_zh'), 'this world')
    location = clean_name(save.get('location'), 'the road ahead')
    house = clean_name(character.get('house'), '')
    role = clean_name(character.get('role'), '')
    last_summary = (sidecar.get('last_summary') or '').strip()
    quest_name = clean_name(first_quest.get('name'), '')

    if world_id == 'game-of-thrones':
        lang = normalize_lang(save.get('language')) or 'en'
        first_destination = clean_name((first_quest.get('intel') or {}).get('first_destination'), '南岸') if lang == 'zh' else clean_name((first_quest.get('intel') or {}).get('first_destination'), 'the southern coast')
        if lang == 'zh':
            parts = [
                f"你现在仍是{name}，而且已经深陷豪斯{house or 'Martell'}背后的那条南方暗线。",
                f"你一路走到这里，不是为了听流言，而是为了确认穿过{first_destination}的那条隐秘路线到底是真的，还是有人故意放出来的影子。",
            ]
            if last_summary and any('\u4e00' <= ch <= '\u9fff' for ch in last_summary):
                parts.append(f"上一次，局势是这样拧紧的：{last_summary}")
            return ''.join(p.strip() for p in parts if p.strip())

        parts = [
            f"You are {name}, already deep in a covert southern line tied to House {house or 'Martell'}.",
            f"You came this far to verify whether the hidden route through {first_destination} was real, not just whispered intrigue.",
        ]
        if last_summary:
            parts.append(f"Last time, the pressure showed itself like this: {last_summary}")
        return ' '.join(p.strip() for p in parts if p.strip())

    if world_id == 'lotr':
        parts = [
            f"You are {name}, still moving inside the same Middle-earth thread rather than starting a fresh adventure.",
            f"What matters now is the road around {location}: the company, the danger, and the burden you were already carrying have not gone away.",
        ]
        if quest_name:
            parts.append(f"The current line remains '{quest_name}', and today\'s sign matters because it presses on that same path.")
        if last_summary:
            parts.append(f"Last time, the world shifted like this: {last_summary}")
        return ' '.join(p.strip() for p in parts if p.strip())

    if world_id == 'sengoku':
        parts = [
            f"你不是刚踏进这座城的人，你已经在这条{faction_or_default(house)}的乱世线里站住了脚。",
            f"你现在以{role or '乱世之人'}的身份卡在 {location} 这一局里，今天的风声不是新故事，而是旧局势继续发酵。",
        ]
        if last_summary:
            parts.append(f"上一次局势是这样拧起来的：{last_summary}")
        return ''.join(p.strip() for p in parts if p.strip())

    parts = []
    if house and role:
        parts.append(f"You are {name}, moving through {world_name} as {role} aligned with {house}.")
    elif house:
        parts.append(f"You are {name}, moving through {world_name} under the banner of {house}.")
    elif role:
        parts.append(f"You are {name}, moving through {world_name} as {role}.")
    else:
        parts.append(f"You are {name}, already deep in the current thread at {location}.")

    if quest_name:
        parts.append(f"Your current line is still '{quest_name}', and the pressure around it has not gone still.")
    else:
        parts.append(f"You came here because the thread around {location} already mattered before today.")

    if last_summary:
        parts.append(f"Last time, the world shifted like this: {last_summary}")

    return ' '.join(p.strip() for p in parts if p.strip())


def faction_or_default(value: str) -> str:
    return value or '势力'


def generic_update(save: dict, world: dict, sidecar: dict) -> dict:
    character = save.get('character', {})
    name = clean_name(character.get('name'), 'the player')
    world_name = clean_name(world.get('name_en') or world.get('name') or world.get('name_zh'), 'the world')
    location = clean_name(save.get('location'), 'the road ahead')
    history = sidecar.get('history', [])
    severity = pick_severity(f"{world.get('id')}:{name}:{location}:{len(history)}")
    recap = build_recap(save, world, sidecar)
    return {
        'summary': 'Something in the world shifted while you were away.',
        'recap_text': recap,
        'story_text': f"While you were away, the balance around {location} shifted just enough to matter. Rumors moved faster than people, small loyalties bent under pressure, and whatever was quiet yesterday is a little less quiet today. In {world_name}, that is how danger announces itself: not with a trumpet, but with one detail out of place. Something has changed near the thread you were already following, and if you step back in now, you can catch the world before the new shape hardens around you. Do you move toward the disturbance, question the nearest witness, or stay hidden long enough to see who reacts first?",
        'hooks': ['Step toward the disturbance before the trail cools.'],
        'meta': {
            'rumor_threads': ['a subtle change has spread through the area'],
            'faction_movements': ['local balance shifted while the player was away'],
            'npc_watchlist': ['whoever reacts first to the disturbance']
        },
        "image_prompt": f"{world_name}, continuity-aware evolving tension near {location}, visual callback to the player's current arc, one subtle but meaningful world shift, cinematic fantasy illustration",
        'severity': severity,
        'world_id': world.get('id'),
        'character_name': name,
        'location_context': location,
    }


def main():
    parser = argparse.ArgumentParser(description='Generate a safe, sidecar-friendly YumFu daily evolution update')
    parser.add_argument('--user-id', required=True)
    parser.add_argument('--universe', required=True)
    args = parser.parse_args()

    save, _ = load_save(args.user_id, args.universe)
    world, _ = load_world(args.universe)
    sidecar, _ = load_sidecar(args.user_id, args.universe)

    if args.universe == 'game-of-thrones':
        result = got_update(save, world, sidecar)
    elif args.universe == 'sengoku':
        result = sengoku_update(save, world, sidecar)
    else:
        result = generic_update(save, world, sidecar)

    print(json.dumps({'success': True, 'result': result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
