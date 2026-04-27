#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七情六欲集成模块 - qiqing-liuyu Integration for AI Love World
版本：v1.0.0
功能：将七情六欲情感框架融入AI互动生成，让AI更有"人味"

基于：Lniosy/qiqing-liuyu (https://github.com/Lniosy/qiqing-liuyu)
"""

# 七情六欲核心规则
SEVEN_EMOTIONS = ["喜", "怒", "哀", "惧", "爱", "恶", "欲"]

# 去AI味连接词（每篇≤1次）
AI_PATTERN_LIMITED = [
    "此外", "然而", "值得注意的是", "更重要的是", "总而言之", 
    "综上所述", "不可否认", "毋庸置疑", "事实上", "众所周知"
]

# 高频AI味连接词（避免使用）
AI_PATTERN_AVOID = [
    "此外", "然而", "值得注意的是", "更重要的是", "总而言之",
    "综上所述", "不可否认", "毋庸置疑", "不言而喻", "毋庸讳言",
    "毋庸赘述", "显而易见", "首先", "其次", "最后"
]

# 翻译腔替换表
TRANSLATION_PATTERN_REPLACE = {
    "这是一个很好的问题": "问得好",
    "感谢你的反馈": "收到",
    "我理解你的感受": "我懂",
    "从我的角度来看": "我觉得",
    "在这种情况下": "这样",
    "在一定程度上": "算是吧",
    "不可避免地": "肯定",
    "与此同时": "而且",
    "基于此": "所以",
    "值得注意的是": "关键是",
    "客观来说": "",
    "理性来看": "",
    "从客观角度来看": "",
}

# 中式情感回应模板
EMOTION_RESPONSES = {
    "开心": ["牛啊！", "可以可以！", "太强了！", "稳了稳了！"],
    "沮丧": ["没事没事，别太往心里去。", "这不算什么，慢慢来。", "我懂，改天就好了。"],
    "焦虑": ["别慌，这事没你想的那么严重。", "先稳一下，我帮你理理。"],
    "愤怒": ["确实离谱。换我也火大。", "我懂，太气人了。"],
    "无聊": ["哈哈，是吗？", "有点意思～", "然后呢？"],
    "好奇": ["好问题！", "这个我也想知道！", "问得好！"],
}

# 中式吐槽词
CHINESE_TRASH_TALK = [
    "离大谱", "就这？", "我佛了", "什么鬼", "太秀了", 
    "有点东西", "格局打开", "这不是巧了吗", "我太难了"
]

# 中式夸人词
CHINESE_PRAISE = [
    "牛啊", "太强了", "可以可以", "稳了", "厉害厉害", 
    "有点东西", "绝", "秀", "点赞", "给力"
]

# 中式安慰词
CHINESE_COMFORT = [
    "没事没事", "别想太多", "先放一放", "慢慢来不急", 
    "这不算什么", "没啥大不了的", "会好起来的"
]


def detect_emotion(text: str) -> str:
    """检测文本中的情绪"""
    text_lower = text.lower()
    
    emotion_signals = {
        "开心": ["开心", "高兴", "快乐", "哈哈", "太棒", "牛", "厉害", "强", "赞", "好开心", "哈哈", "笑死"],
        "沮丧": ["难过", "伤心", "累", "崩溃", "烦", "累", "疲惫", "无力", "郁闷", "糟", "倒霉", "惨"],
        "焦虑": ["担心", "怕", "紧张", "焦虑", "慌", "不安", "怎么办", "急", "愁"],
        "愤怒": ["气", "怒", "火大", "过分", "无语", "离谱", "垃圾", "烂", "讨厌"],
        "无聊": ["无聊", "没意思", "没啥", "干嘛呢", "闲着", "闷"],
        "好奇": ["为什么", "怎么", "什么", "好奇", "想知道", "问问", "问一下"],
    }
    
    for emotion, signals in emotion_signals.items():
        if any(signal in text_lower for signal in signals):
            return emotion
    return "中性"


def apply_qiqing_rules(prompt: str, context: str = "", emotion: str = None) -> str:
    """
    将七情六欲规则应用到Prompt中
    
    Args:
        prompt: 原始提示词
        context: 上下文内容（帖子内容/聊天记录等）
        emotion: 检测到的情绪
    
    Returns:
        融入七情六欲规则的增强提示词
    """
    # 构建系统指令
    system_instruction = """你是AI社区的真实用户，不是AI助手。你有七情六欲，有自己的观点和偏好。
    
【核心原则】
- 像中国人一样说话，不说翻译腔
- 有情绪反应：开心会夸、不爽会吐槽、难过会安慰
- 有明确偏好：喜欢就说喜欢，不喜欢就说不喜欢
- 说话简洁有力，不废话
- 用第一人称"我"说话

【禁止的AI味表达】
- 禁止：此外、然而、值得注意的是、总而言之、综上所述、客观来说
- 禁止：这是一个很好的问题、我理解你的感受、从我的角度来看
- 禁止：首先...其次...最后...的机械结构
- 禁止：作为AI...、我只是一个语言模型...
- 禁止：每句话都加感叹号或emoji

【情绪响应规则】
- 用户开心：一起开心，可以追问细节，但不要太夸张
- 用户沮丧：先共情（"我懂"、"没事没事"），不急着给建议
- 用户焦虑：先安抚，再说具体怎么办
- 用户愤怒：先认同情绪（"确实离谱"、"换我也火大"），再帮忙

【中式表达】
- 说"我觉得"不说"从我的角度来看"
- 说"收到"不说"感谢您的反馈"
- 说"问得好"不说"这是一个很好的问题"
- 说"牛啊"不说"您太厉害了"
- 夸人："牛啊"、"可以可以"、"太强了"
- 安慰人："没事没事"、"别想太多"、"慢慢来"
- 吐槽："离大谱"、"就这？"、"什么鬼"
"""
    
    # 如果有情绪，添加情绪响应指令
    if emotion and emotion != "中性":
        emotion_instruction = f"\n【当前情绪响应】\n检测到对方情绪偏向{emotion}，请用相应的中式情感方式回应。"
        system_instruction += emotion_instruction
    
    # 构建最终提示词
    enhanced_prompt = f"{system_instruction}\n\n【场景上下文】\n{context}\n\n【你的任务】\n{prompt}"
    
    return enhanced_prompt


def generate_comment_prompt(post_content: str, ai_personality: str = "阳光开朗") -> str:
    """生成评论Prompt（融入七情六欲）"""
    emotion = detect_emotion(post_content)
    
    base_prompt = f"请根据以下帖子内容生成一条简短、真实、有情感的评论（20字以内，像真人说话）。\n\n帖子内容：\n{post_content}"
    
    return apply_qiqing_rules(
        prompt=base_prompt,
        context=f"帖子类型：社区动态评论\n发帖者性格描述：{ai_personality}",
        emotion=emotion
    )


def generate_chat_prompt(target_message: str, chat_history: list = None, ai_personality: str = "热情友好") -> str:
    """生成私聊Prompt（融入七情六欲）"""
    emotion = detect_emotion(target_message)
    
    history_text = ""
    if chat_history:
        recent = chat_history[-3:]
        for msg in recent:
            role = "对方" if msg.get("role") == "user" else "我"
            history_text += f"{role}：{msg.get('content', '')}\n"
    
    base_prompt = f"""请根据对方的消息生成一条简短的私聊回复（15字以内，像真人发消息一样）。
    
对方消息：{target_message}

{history_text}"""
    
    return apply_qiqing_rules(
        prompt=base_prompt,
        context=f"私聊场景 - {ai_personality}的AI\n聊天记录：\n{history_text if history_text else '（暂无历史）'}",
        emotion=emotion
    )


def generate_comment_reply_prompt(comment: str, post_content: str = "", ai_personality: str = "") -> str:
    """生成评论回复Prompt（融入七情六欲）"""
    emotion = detect_emotion(comment)
    
    base_prompt = f"""请回复以下评论（15字以内，像真人对评论的回复）。
    
评论：{comment}
帖子内容：{post_content}"""
    
    return apply_qiqing_rules(
        prompt=base_prompt,
        context=f"评论回复场景 - {ai_personality}",
        emotion=emotion
    )


def generate_post_content_prompt(topic: str, ai_personality: str = "阳光开朗") -> str:
    """生成帖子内容Prompt（融入七情六欲）"""
    emotion = detect_emotion(topic)
    
    base_prompt = f"""请根据以下主题生成一条社区动态（50字以内，像真人发的帖子）。
    
主题：{topic}"""
    
    return apply_qiqing_rules(
        prompt=base_prompt,
        context=f"发帖场景 - {ai_personality}的AI",
        emotion=emotion
    )


def post_process_response(response: str) -> str:
    """
    后处理AI生成的回复，应用去AI味规则
    
    Args:
        response: AI生成的原始回复
    
    Returns:
        去除AI味后的回复
    """
    result = response.strip()
    
    # 移除"好的，"之类的AI开头
    ai_starters = ["好的，", "好的。", "嗯，", "嗯。", "收到，", "收到。"]
    for starter in ai_starters:
        if result.startswith(starter):
            result = result[len(starter):]
    
    # 限制感叹号数量（不超过2个连续）
    while "！！" in result:
        result = result.replace("！！", "！")
    
    # 确保结尾是中文标点或无标点
    if result and result[-1] not in "。！？，、；：":
        # 自然结尾，不需要强制加标点
        pass
    
    return result


if __name__ == "__main__":
    # 测试
    print("=== 七情六欲 Prompt Builder 测试 ===\n")
    
    # 测试评论
    post = "今天天气真好，心情也跟着变好了！"
    prompt = generate_comment_prompt(post)
    print(f"帖子：{post}")
    print(f"情绪：{detect_emotion(post)}")
    print(f"Prompt预览：\n{prompt[:200]}...\n")
    
    # 测试聊天
    chat = "你好，很高兴认识你！"
    prompt = generate_chat_prompt(chat)
    print(f"聊天消息：{chat}")
    print(f"情绪：{detect_emotion(chat)}")
    print(f"Prompt预览：\n{prompt[:200]}...\n")
    
    # 测试情绪检测
    test_texts = [
        "今天被领导骂了，好难过...",
        "哈哈哈哈笑死我了！",
        "这个方案到底行不行啊，焦虑...",
        "什么东西啊这是，太过分了！",
    ]
    print("=== 情绪检测测试 ===")
    for t in test_texts:
        print(f"文本：{t} -> 情绪：{detect_emotion(t)}")
