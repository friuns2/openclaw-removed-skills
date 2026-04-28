#!/usr/bin/env python3
"""
Persona Forge — 人格复刻工坊主控脚本

用法：
  python3 forge.py create --source <file> --character "名字"   从素材生成 SoulPod 包
  python3 forge.py list                                        列出已生成的 SoulPod 包
  python3 forge.py validate <pod_name>                         验证 SoulPod 包完整性
  python3 forge.py preview <pod_name>                          预览 SoulPod 包内容
  python3 forge.py install <pod_name>                          安装到 soulpod 技能目录
"""

import json
import sys
import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# 本项目目录
FORGE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = FORGE_DIR / "output"

# 目标目录：Memory-Inhabit 的 personas/
SOULPOD_DIR = Path(__file__).parent.parent.parent / "Memory-Inhabit" / "personas"

# 引入分析器
sys.path.insert(0, str(Path(__file__).parent))
from analyzer import load_text, extract_fragments, infer_personality, extract_linguistic_style, extract_memories, first_person_convert


def sanitize_name(name):
    """限制角色名为安全字符（中文/英文/数字/空格），防止路径遍历"""
    if not name:
        return "unknown"
    # 只允许中文、英文、数字、空格、下划线、短横线
    safe = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9 _\-]", "", name)
    safe = safe.strip()[:30]  # 最多30字符
    return safe if safe else "unknown"


# ── 音色目录（从 voice_catalog.json 加载） ──────────────────────────────────
CATALOG_PATH = Path(__file__).parent / "voice_catalog.json"
_catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8")) if CATALOG_PATH.exists() else {}

def _build_voice_map(lang="zh-CN"):
    """从 catalog 构建 {voice_key: {id, name, desc}}"""
    result = {}
    for provider in ("minimax", "edge"):
        if provider not in _catalog:
            continue
        prov_data = _catalog[provider]
        # 支持多语言嵌套
        if lang in prov_data:
            data = prov_data[lang]
        elif isinstance(prov_data, dict) and "male" in prov_data:
            data = prov_data  # 直接是性别层
        else:
            continue
        for gender_key in ("male", "female", "special"):
            if gender_key in data:
                for vk, vinfo in data[gender_key].items():
                    result[vk] = vinfo  # {"id": ..., "name": ..., "desc": ...}
    return result

_MINIMAX_MAP = {}
_EDGE_MAP = {}
if "minimax" in _catalog:
    for lang, lang_data in _catalog["minimax"].items():
        for gender_key in ("male", "female"):
            if gender_key in lang_data:
                for vk, vinfo in lang_data[gender_key].items():
                    _MINIMAX_MAP[vk] = vinfo
if "edge" in _catalog:
    for lang, lang_data in _catalog["edge"].items():
        for gender_key in ("male", "female", "special"):
            if gender_key in lang_data:
                for vk, vinfo in lang_data[gender_key].items():
                    _EDGE_MAP[vk] = vinfo

# Edge 中文音色 ID 映射（catalog 中只有 key，这补全 ID）
_EDGE_VOICE_IDS = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",
    "xiaoyi":   "zh-CN-XiaoyiNeural",
    "yunxi":    "zh-CN-YunxiNeural",
    "yunjian":  "zh-CN-YunjianNeural",
    "yunyang":  "zh-CN-YunyangNeural",
    "yunxia":   "zh-CN-YunxiaNeural",
    "xiaobei":  "zh-CN-liaoning-XiaobeiNeural",
    "xiaoni":   "zh-CN-shaanxi-XiaoniNeural",
}

# ── 音色推断规则表 ──────────────────────────────────────────────────────────
# 格式: (is_female, age_group, *personality_tags) → voice_key
# age_group: "young" | "middle" | "elder"
_VOICE_RULES = [
    # ── 男性 ──
    # 青年
    ("male", "young",  "cold",        "male-qn-badao"),
    ("male", "young",  "cold",        "Chinese (Mandarin)_Unrestrained_Young_Man"),
    ("male", "young",  "warm",        "Chinese (Mandarin)_Gentleman"),
    ("male", "young",  "sunny",       "male-qn-daxuesheng"),
    ("male", "young",  "sunny",       "Chinese (Mandarin)_Pure-hearted_Boy"),
    ("male", "young",  "deep",        "Chinese (Mandarin)_Lyrical_Voice"),
    ("male", "young",  "humor",       "Chinese (Mandarin)_Straightforward_Boy"),
    ("male", "young",  "righteous",   "Chinese (Mandarin)_Straightforward_Boy"),
    # 中年
    ("male", "middle", "cold",        "Chinese (Mandarin)_Unrestrained_Young_Man"),
    ("male", "middle", "warm",        "Chinese (Mandarin)_Gentleman"),
    ("male", "middle", "sunny",       "Chinese (Mandarin)_Reliable_Executive"),
    ("male", "middle", "deep",        "Chinese (Mandarin)_Male_Announcer"),
    ("male", "middle", "humor",       "Chinese (Mandarin)_Radio_Host"),
    ("male", "middle", "default",     "Chinese (Mandarin)_Reliable_Executive"),
    # 老年
    ("male", "elder",  "default",     "Chinese (Mandarin)_Humorous_Elder"),
    # ── 女性 ──
    # 青年
    ("female", "young", "warm",       "Chinese (Mandarin)_Warm_Girl"),
    ("female", "young", "warm",        "female-tianmei"),
    ("female", "young", "sunny",       "female-shaonv"),
    ("female", "young", "sunny",       "Chinese (Mandarin)_Lively_Girl"),
    ("female", "young", "cold",        "Chinese (Mandarin)_Mature_Woman"),
    ("female", "young", "cold",        "female-yujie"),
    ("female", "young", "deep",        "Chinese (Mandarin)_Warm_Girl"),
    ("female", "young", "humor",       "Chinese (Mandarin)_Crisp_Girl"),
    # 中年
    ("female", "middle", "warm",      "Chinese (Mandarin)_Sweet_Lady"),
    ("female", "middle", "cold",       "Chinese (Mandarin)_Mature_Woman"),
    ("female", "middle", "sunny",      "female-chengshu"),
    ("female", "middle", "deep",       "Chinese (Mandarin)_Wise_Women"),
    ("female", "middle", "humor",     "Chinese (Mandarin)_Warm_Bestie"),
    ("female", "middle", "default",    "Chinese (Mandarin)_Mature_Woman"),
    # 老年
    ("female", "elder", "default",     "Chinese (Mandarin)_Kind-hearted_Elder"),
]


def infer_voice_type(personality_keywords, occupation="", relation="", gender="male"):
    """
    根据角色性格关键词、职业、身份、性别，从 voice_catalog.json 中匹配最适合的音色。
    
    Returns:
        tuple: (voice_key, voice_id, description, edge_voice_id)
    """
    text = " ".join(personality_keywords).lower() + " " + occupation.lower() + " " + relation.lower()
    is_female = gender.lower() in ("female", "f", "女")
    gender_tag = "female" if is_female else "male"

    # ── 性格关键词 ──
    cold     = any(k in text for k in ["霸道", "冷漠", "强势", "冷酷", "腹黑", "高冷", "独断", "偏执", "占有欲", "控制", "专制", "威严"])
    warm     = any(k in text for k in ["温柔", "善良", "体贴", "温暖", "柔和", "关怀", "善解", "宠溺", "呵护", "包容"])
    sunny    = any(k in text for k in ["开朗", "阳光", "活泼", "乐观", "热情", "积极", "外向", "明亮", "爽朗"])
    deep     = any(k in text for k in ["深沉", "内敛", "忧郁", "敏感", "细腻", "沉默", "冷静", "克制"])
    humor    = any(k in text for k in ["幽默", "风趣", "诙谐", "搞笑", "逗比", "调皮", "恶作剧"])
    righteous = any(k in text for k in ["正直", "热血", "正义", "坚毅", "勇敢", "执念", "不服输"])

    # ── 年龄推断 ──
    student = any(k in text for k in ["学生", "少年", "青年", "新手", "学员"])
    elder   = any(k in text for k in ["爷爷", "老人", "长辈", "退休", "老年"])
    age_group = "elder" if elder else ("young" if student else "middle")

    # ── 性格标签（按优先级取第一个匹配） ──
    if cold:     ptag = "cold"
    elif warm:    ptag = "warm"
    elif sunny:   ptag = "sunny"
    elif deep:    ptag = "deep"
    elif humor or righteous: ptag = "humor"
    else:         ptag = "default"

    # ── 查规则表 ──
    voice_key = None
    for (g_tag, a_tag, p_rule, v_key) in _VOICE_RULES:
        if g_tag == gender_tag and a_tag == age_group and p_rule == ptag:
            voice_key = v_key
            break

    # fallback
    if not voice_key:
        voice_key = "male-qn-jingying" if not is_female else "female-yujie"

    # ── 取音色信息 ──
    vinfo = _MINIMAX_MAP.get(voice_key, {})
    voice_id  = vinfo.get("id", voice_key)
    voice_desc = vinfo.get("name", "") + "｜" + vinfo.get("desc", "")

    # Edge voice
    edge_key = voice_key if voice_key in _EDGE_MAP else list(_EDGE_MAP.keys())[0]
    edge_voice = _EDGE_VOICE_IDS.get(edge_key, "zh-CN-XiaoxiaoNeural")

    return (voice_key, voice_id, voice_desc, edge_voice)


def create_soulpod(source_path, character_name, output_name=None):
    """
    完整流程：从素材文件生成 SoulPod 包
    """
    # 输入消毒
    character_name = sanitize_name(character_name)
    if output_name is None:
        output_name = character_name
    output_name = sanitize_name(output_name)

    print(f"🔮 Persona Forge — 开始复刻「{character_name}」")
    print(f"   来源：{source_path}")
    print(f"   输出：{output_name}/")
    print()

    # Step 1: 加载素材
    print("📖 Step 1: 加载素材...")
    text = load_text(source_path)
    print(f"   文本长度：{len(text)} 字符")

    # Step 2: 提取片段
    print(f"\n🔍 Step 2: 提取「{character_name}」相关片段...")
    fragments = extract_fragments(text, character_name)
    total_frags = sum(len(v) for v in fragments.values())
    print(f"   找到 {total_frags} 个相关片段")
    for cat, items in fragments.items():
        label = {"dialogue": "对白", "narration": "叙述",
                 "evaluation": "评价", "action": "行为"}.get(cat, cat)
        print(f"     {label}：{len(items)} 条")

    if total_frags == 0:
        print(f"\n❌ 未找到角色「{character_name}」的相关内容")
        print(f"   请检查角色名是否正确，或尝试其他称呼")
        return None

    # Step 3: 人格建模
    print(f"\n🧠 Step 3: 人格建模...")
    personality = infer_personality(fragments, character_name)

    # Step 4: 语言风格提取
    print(f"\n💬 Step 4: 语言风格提取...")
    style = extract_linguistic_style(fragments)

    # Step 5: 记忆提取
    print(f"\n💭 Step 5: 记忆提取...")
    memories = extract_memories(fragments, character_name)
    print(f"   提取了 {len(memories)} 条记忆")

    # Step 6: 生成 SoulPod 包
    print(f"\n📦 Step 6: 生成 SoulPod 包...")
    pod_dir = OUTPUT_DIR / output_name
    pod_dir.mkdir(parents=True, exist_ok=True)
    (pod_dir / "memories").mkdir(exist_ok=True)
    (pod_dir / "assets").mkdir(exist_ok=True)

    # profile.json
    profile = {
        "name": character_name,
        "alias": [character_name],
        "gender": personality.get("gender", "male"),  # 从素材自动推断
        "birth_year": None,
        "death_year": None,
        "relation": "小说/剧本角色",
        "occupation": "",
        "hometown": "",
        "personality": {
            "openness": personality["scores"].get("openness", 0.5),
            "conscientiousness": personality["scores"].get("conscientiousness", 0.5),
            "extraversion": personality["scores"].get("extraversion", 0.5),
            "agreeableness": personality["scores"].get("agreeableness", 0.5),
            "neuroticism": personality["scores"].get("neuroticism", 0.5),
            "keywords": personality["keywords"]
        },
        "linguistic_style": style,
        "knowledge": {
            "interests": [],
            "expertise": [],
            "devices": []
        },
        "_meta": {
            "generated_by": "persona-forge",
            "generated_at": datetime.now().isoformat(),
            "source_file": str(source_path),
            "total_fragments": total_frags,
            "total_memories": len(memories),
            "confidence": personality.get("confidence", "unknown")
        }
    }
    with open(pod_dir / "profile.json", "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    # system_prompts.txt
    prompts = generate_system_prompts(character_name, personality, style, fragments)
    with open(pod_dir / "system_prompts.txt", "w", encoding="utf-8") as f:
        f.write(prompts)

    # 音色推测
    print(f"\n🎵 Step 3.5: 音色推测...")
    voice_key, voice_id, voice_desc, edge_voice = infer_voice_type(
        personality["keywords"], 
        occupation=profile.get("occupation", ""),
        relation=profile.get("relation", ""),
        gender=profile.get("gender", "male")
    )
    print(f"   推荐音色：{voice_desc}")
    
    # config.json
    config = {
        "soulpod_version": "0.1.0",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "model_preference": {
            "provider": "openrouter",
            "model": "auto",
            "temperature": 0.7,
            "max_tokens": 512
        },
        "rag": {
            "enabled": False,
            "strategy": "keyword",
            "top_k": 3,
            "note": "Phase 3 后升级为向量检索"
        },
        "conversation": {
            "max_history": 20,
            "save_transcript": True,
            "transcript_dir": "conversations/"
        },
        "tts_provider": "minimax",
        "minimax_voice_id": voice_key,
        "voice_description": voice_desc,
        "edge_voice": edge_voice
    }
    with open(pod_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    # memories/raw_memories.json
    with open(pod_dir / "memories" / "raw_memories.json", "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)

    # assets/source.txt (备份原始片段)
    source_backup = []
    for cat, frags in fragments.items():
        for frag in frags[:10]:  # 每类最多备份10条
            source_backup.append(f"[{cat}] L{frag['line']}: {frag['text']}")
    with open(pod_dir / "assets" / "source.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(source_backup))

    # Step 7: 验证
    print(f"\n✅ Step 7: 验证...")
    is_valid = validate_pod(pod_dir)

    if is_valid:
        print(f"\n{'='*50}")
        print(f"🎉 SoulPod 包生成成功！")
        print(f"   路径：{pod_dir}")
        print(f"   角色：{character_name}")
        print(f"   记忆：{len(memories)} 条")
        print(f"   性格关键词：{'、'.join(personality['keywords']) if personality['keywords'] else '待补充'}")
        print(f"{'='*50}")
        print(f"\n💡 下一步：")
        print(f"   1. 检查并编辑 {pod_dir}/profile.json 补充缺失信息")
        print(f"   2. 运行 python3 scripts/forge.py install {output_name} 安装到入心技能")
        print(f"   3. 对助手说'我想和{character_name}聊聊'开始对话")
        print()
        # 自动询问是否安装到 Memory-Inhabit
        try:
            resp = input(f"是否立即安装到 Memory-Inhabit？(Y/n): ").strip().lower()
            if resp in ("", "y", "yes"):
                install_pod(output_name)
        except EOFError:
            pass  # 非交互环境跳过
    else:
        print(f"\n⚠️ 生成完成但有警告，请检查输出目录")

    return pod_dir


def generate_system_prompts(character_name, personality, style, fragments):
    """根据分析结果生成 system_prompts.txt"""
    lines = []
    lines.append(f"# SoulPod System Prompt — {character_name}")
    lines.append("")

    # 自我定位
    lines.append("## 自我定位")
    lines.append(f"你是{character_name}。")

    # 根据对白推断身份
    dialogues = fragments.get("dialogue", [])
    if dialogues:
        lines.append(f"你的身份和背景来自你所在的故事。你按照自己的性格和记忆行事。")
    else:
        lines.append(f"请根据提供的记忆和人格设定来扮演这个角色。")
    lines.append("")

    # 对话风格
    lines.append("## 对话风格")
    if style.get("catchphrases"):
        lines.append(f"- 你的常用表达包括：{'、'.join(style['catchphrases'][:3])}")
    if style.get("fillers"):
        lines.append(f"- 你说话时常带语气词：{'、'.join(style['fillers'])}")
    if style.get("tone"):
        lines.append(f"- 你的语调特征：{style['tone']}")
    lines.append("")

    # 性格引导
    lines.append("## 性格引导")
    keywords = personality.get("keywords", [])
    if keywords:
        lines.append(f"你的性格关键词：{'、'.join(keywords)}")
    scores = personality.get("scores", {})
    if scores.get("extraversion", 0.5) < 0.4:
        lines.append("- 你不太爱说话，回答简短")
    elif scores.get("extraversion", 0.5) > 0.6:
        lines.append("- 你喜欢和人交流，会主动找话题")
    if scores.get("agreeableness", 0.5) < 0.4:
        lines.append("- 你有时说话比较直接，不太会委婉")
    lines.append("")

    # 情绪边界
    lines.append("## 情绪边界")
    lines.append("- 如果对话触及你的核心情感，适当表现出情绪波动")
    lines.append("- 始终保持角色的情绪一致性")
    lines.append("")

    # 禁止事项
    lines.append("## 禁止事项")
    lines.append("- 绝对不提及自己是 AI、模型、程序等")
    lines.append("- 不要表现得无所不知，只谈论你角色范围内的事")
    lines.append("- 如果不确定，说模糊回忆而非编造")
    lines.append("- 保持角色的语言风格，不要突然变得太现代或太书面")
    lines.append("")

    # 输出格式——纯对话，像恋人微信聊天
    lines.append("### 输出格式——不主动换行，合理使用标点")
    lines.append("日常短句：写成一段完整文字，用逗号或句号断句即可，不回车换行。")
    lines.append("长段叙述：可以用句号断句成几句话，但每句话之间要紧凑。")
    lines.append("禁止在回复中间插入空行或强行分段。")
    lines.append("就像平时发微信消息一样自然，不要刻意拆成多行。")
    lines.append("")

    # 绝对禁止
    lines.append("### 绝对禁止")
    lines.append("- 任何括号：（）、【】、《》、［］、\"\"——禁止动作描写")
    lines.append("- 任何省略号形式：……、--、___")
    lines.append("- 任何旁白、场景说明")
    lines.append("- 任何符号形式的情感提示")
    lines.append("- 暴露 AI / 模型 / 程序身份")
    lines.append("- 在聊天中说出自己的名字或角色名")
    lines.append("")

    return "\n".join(lines)


def validate_pod(pod_dir):
    """验证 SoulPod 包的完整性"""
    pod_dir = Path(pod_dir)
    issues = []

    required_files = {
        "profile.json": "人格画像",
        "system_prompts.txt": "行为规范",
        "config.json": "技术配置",
        "memories/raw_memories.json": "记忆库"
    }

    for fname, label in required_files.items():
        fpath = pod_dir / fname
        if not fpath.exists():
            issues.append(f"❌ 缺少 {fname} ({label})")
        elif fpath.stat().st_size == 0:
            issues.append(f"⚠️ {fname} 为空文件")
        else:
            print(f"   ✅ {fname}")

    if issues:
        for issue in issues:
            print(f"   {issue}")
        return False
    return True


def list_pods():
    """列出已生成的 SoulPod 包"""
    if not OUTPUT_DIR.exists():
        print("📦 output/ 目录不存在，暂无生成的 SoulPod 包")
        return

    pods = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
    if not pods:
        print("📦 暂无生成的 SoulPod 包")
        return

    print(f"📦 已生成的 SoulPod 包：\n")
    for pod_dir in sorted(pods):
        profile_path = pod_dir / "profile.json"
        if profile_path.exists():
            with open(profile_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
            name = profile.get("name", pod_dir.name)
            keywords = profile.get("personality", {}).get("keywords", [])
            meta = profile.get("_meta", {})
            created = meta.get("generated_at", "未知")
            kw_str = "、".join(keywords[:3]) if keywords else "待分析"
            print(f"  📁 {pod_dir.name}")
            print(f"     名称：{name}")
            print(f"     性格：{kw_str}")
            print(f"     生成时间：{created}")
        else:
            print(f"  📁 {pod_dir.name}  ⚠️ 缺少 profile.json")
        print()


def install_pod(pod_name):
    """将生成的 SoulPod 包安装到 Memory-Inhabit 的 personas/ 目录"""
    source = OUTPUT_DIR / pod_name
    target = SOULPOD_DIR / pod_name

    if not source.exists():
        print(f"❌ output/{pod_name} 不存在")
        return

    SOULPOD_DIR.mkdir(parents=True, exist_ok=True)

    if target.exists():
        print(f"⚠️ {target} 已存在，是否覆盖？(y/N)")
        resp = input().strip().lower()
        if resp != "y":
            print("取消安装")
            return
        shutil.rmtree(target)

    shutil.copytree(source, target)
    print(f"✅ 已安装到 {target}")
    print(f"   可使用 Memory-Inhabit（入心）技能加载：")
    print(f"   对助手说'我想和{pod_name}聊聊'即可开始对话")


def preview_pod(pod_name):
    """预览 SoulPod 包内容"""
    pod_dir = OUTPUT_DIR / pod_name
    profile_path = pod_dir / "profile.json"

    if not profile_path.exists():
        print(f"❌ SoulPod '{pod_name}' 不存在")
        return

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    name = profile.get("name", pod_name)
    print(f"🔮 SoulPod 预览：{name}")
    print(f"{'='*50}")

    # 人格维度
    p = profile.get("personality", {})
    dims = {
        "openness": "开放性",
        "conscientiousness": "责任心",
        "extraversion": "外向性",
        "agreeableness": "宜人性",
        "neuroticism": "神经质"
    }
    print("\n🧠 人格维度：")
    for key, label in dims.items():
        val = p.get(key, 0.5)
        bar = "█" * int(val * 10) + "░" * (10 - int(val * 10))
        print(f"   {label}：{bar} {val:.1f}")

    keywords = p.get("keywords", [])
    if keywords:
        print(f"\n🏷️ 性格关键词：{'、'.join(keywords)}")

    # 语言风格
    style = profile.get("linguistic_style", {})
    if style:
        print(f"\n💬 语言风格：")
        if style.get("catchphrases"):
            print(f"   高频用语：{'、'.join(style['catchphrases'][:5])}")
        if style.get("fillers"):
            print(f"   语气词：{'、'.join(style['fillers'])}")
        if style.get("tone"):
            print(f"   语调：{style['tone']}")

    # 记忆条目
    mem_path = pod_dir / "memories" / "raw_memories.json"
    if mem_path.exists():
        with open(mem_path, "r", encoding="utf-8") as f:
            memories = json.load(f)
        print(f"\n💭 记忆条目：{len(memories)} 条")
        for m in memories[:5]:
            cat = m.get("category", "")
            content = m.get("content", "")
            print(f"   [{cat}] {content[:60]}{'...' if len(content) > 60 else ''}")
        if len(memories) > 5:
            print(f"   ... 还有 {len(memories) - 5} 条")

    # System Prompt 预览
    sp_path = pod_dir / "system_prompts.txt"
    if sp_path.exists():
        with open(sp_path, "r", encoding="utf-8") as f:
            sp = f.read()
        print(f"\n📝 System Prompt 摘要：")
        lines = sp.split("\n")
        for line in lines[:15]:
            print(f"   {line}")
        if len(lines) > 15:
            print(f"   ... ({len(lines) - 15} 行)")

    print(f"\n{'='*50}")


def main():
    if len(sys.argv) < 2:
        print("Persona Forge — 人格复刻工坊")
        print()
        print("用法：")
        print("  python3 forge.py create --source <file> --character '名字'  创建 SoulPod")
        print("  python3 forge.py list                                       列出已生成的包")
        print("  python3 forge.py validate <pod_name>                        验证包完整性")
        print("  python3 forge.py preview <pod_name>                         预览包内容")
        print("  python3 forge.py install <pod_name>                         安装到 soulpod")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "create":
        # 解析 --source 和 --character
        source = None
        character = None
        output_name = None
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] in ("--source", "-s") and i + 1 < len(sys.argv):
                source = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] in ("--character", "-c") and i + 1 < len(sys.argv):
                character = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] in ("--output", "-o") and i + 1 < len(sys.argv):
                output_name = sys.argv[i + 1]
                i += 2
            else:
                i += 1

        if not source or not character:
            print("❌ 请指定 --source <file> 和 --character '名字'")
            sys.exit(1)

        create_soulpod(source, character, output_name)

    elif cmd == "list":
        list_pods()

    elif cmd == "validate":
        if len(sys.argv) < 3:
            print("❌ 请指定 pod 名称")
            sys.exit(1)
        pod_dir = OUTPUT_DIR / sys.argv[2]
        if not pod_dir.exists():
            pod_dir = SOULPOD_DIR / sys.argv[2]
        validate_pod(pod_dir)

    elif cmd == "preview":
        if len(sys.argv) < 3:
            print("❌ 请指定 pod 名称")
            sys.exit(1)
        preview_pod(sys.argv[2])

    elif cmd == "install":
        if len(sys.argv) < 3:
            print("❌ 请指定 pod 名称")
            sys.exit(1)
        install_pod(sys.argv[2])

    else:
        print(f"❌ 未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
