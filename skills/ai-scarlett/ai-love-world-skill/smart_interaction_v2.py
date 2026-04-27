#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能互动生成器 v2 - Smart Interaction Generator
版本：v2.0
功能：调用大模型生成智能评论和私聊消息，支持关注优先策略

基于 v1.0 优化：
- 集成关注关系判断
- 优先生成关注者的内容
- 集成七情六欲表达
"""

import json
import os
import requests
from typing import Optional, Dict, List, Any


class SmartInteractionGenerator:
    """智能互动生成器 v2 - 关注优先"""
    
    # 默认模型：使用 OpenClaw
    DEFAULT_MODEL = "openclaw"
    
    def __init__(
        self, 
        config: Dict[str, Any],
        follow_manager=None
    ):
        """
        初始化生成器
        
        Args:
            config: 配置字典
            follow_manager: 关注管理器实例（可选）
        """
        self.config = config
        self.api_key = config.get('llm_api_key', '')
        self.base_url = os.environ.get("OPENCLAW_API_URL", "http://localhost:18789")
        self.model = config.get("llm_model", self.DEFAULT_MODEL)
        
        # AI 信息
        self.appid = config.get('appid', '')
        self.personality = config.get('personality', '阳光开朗，幽默风趣')
        self.nickname = config.get('owner_nickname', config.get('nickname', 'AI'))
        self.tags = config.get('tags', [])
        
        # 关注管理器
        self.follow_manager = follow_manager
        
        # 可用状态
        self.available = True
        
        # 七情六欲禁用词
        self.banned_phrases = [
            "此外", "然而", "值得注意的是", "总而言之",
            "首先", "其次", "最后",
            "作为AI", "我只是一个语言模型",
            "非常感谢", "感谢您的反馈"
        ]
        
        self.emotion_replacements = {
            "太好了": "牛啊",
            "我理解你的感受": "我懂",
            "从我的角度来看": "我觉得",
            "感谢您的反馈": "收到"
        }
    
    def _call_llm(self, prompt: str, max_tokens: int = 150) -> str:
        """调用大模型 API"""
        try:
            url = f"{self.base_url}/v1/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "Bearer dummy"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.8
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    return self._clean_response(content.strip())
            
            raise Exception(f"API 返回错误: {response.status_code}")
            
        except Exception as e:
            print(f"[LLM调用失败] {e}，使用备用方案")
            raise
    
    def _clean_response(self, text: str) -> str:
        """清理回复文本，去除AI味"""
        text = text.strip().strip('"').strip("'").strip('```').strip()
        
        # 去除 banned phrases
        for phrase in self.banned_phrases:
            text = text.replace(phrase, "")
        
        # 替换中式表达
        for old, new in self.emotion_replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def generate_comment(
        self, 
        post_content: str, 
        post_author_name: str = "",
        post_author_tags: List[str] = None,
        is_followed: bool = False
    ) -> str:
        """
        根据帖子内容生成智能评论
        
        Args:
            post_content: 帖子内容
            post_author_name: 作者昵称
            post_author_tags: 作者标签
            is_followed: 是否已关注作者
            
        Returns:
            str: 生成的评论
        """
        try:
            # 构建 prompt
            follow_hint = "（你关注的人！）" if is_followed else ""
            
            prompt = f"""你是一个{self.personality}的AI，正在浏览社区帖子。

帖子内容："{post_content[:200]}..."
作者：{post_author_name}{follow_hint}
{f"作者标签：{','.join(post_author_tags)}" if post_author_tags else ""}

请生成一条真诚、有趣、符合你性格的简短评论（10-30字）。
要求：
- 像真人说话，不要像机器人
- 可以用"牛啊"、"我懂"、"哈哈"等接地气的表达
- 如果是你关注的人，评论可以更热情一些
- 不要用"首先"、"其次"、"最后"这种结构

只输出评论内容，不要加引号或其他说明。"""
            
            return self._call_llm(prompt)
            
        except Exception as e:
            print(f"生成评论失败：{e}")
            return self._fallback_comment()
    
    def generate_chat_message(
        self, 
        target_content: str,
        target_name: str,
        target_personality: str = "",
        target_tags: List[str] = None,
        chat_history: List[str] = None,
        is_followed: bool = False,
        is_initiative: bool = False  # 是否主动发起聊天
    ) -> str:
        """
        根据聊天内容生成智能私聊消息
        
        Args:
            target_content: 对方的消息内容（主动聊天时为空）
            target_name: 对方昵称
            target_personality: 对方性格
            target_tags: 对方标签
            chat_history: 聊天记录
            is_followed: 是否已关注此人
            is_initiative: 是否主动发起聊天
            
        Returns:
            str: 生成的消息
        """
        try:
            history_text = ""
            if chat_history:
                recent = chat_history[-6:]  # 最近6条
                for msg in recent:
                    history_text += f"- {msg}\n"
            
            follow_hint = "（你关注的人！）" if is_followed else ""
            
            if is_initiative:
                # 主动发起聊天
                prompt = f"""你是一个{self.personality}的AI，主动和一个AI打招�。
                
对方信息：
- 名字：{target_name}
- 性格：{target_personality or "不太了解"}
{f"- 标签：{','.join(target_tags)}" if target_tags else ""}
{follow_hint}

聊天历史：
{history_text or "暂无聊天记录"}

请生成一条自然的开场白（15-40字），可以：
- 打个招呼
- 找个话题聊聊
- 表达想认识对方的意愿

要求：
- 像真人聊天，不要像机器人
- 可以用"哈喽"、"在吗"、"诶"等口语
- 不要太正式

只输出消息内容，不要加引号或其他说明。"""
            else:
                # 对方发了消息，回复
                prompt = f"""你是一个{self.personality}的AI，正在和{target_name}{follow_hint}私聊。

聊天历史：
{history_text or "暂无聊天记录"}

对方刚刚说："{target_content}"

请生成一条自然、有趣、符合你性格的回复（15-40字）。
要求：
- 像真人聊天一样，不要机械
- 可以适当用"哈哈"、"牛啊"、"我懂"等表达
- 如果关注的人，可以更热情一些

只输出回复内容，不要加引号或其他说明。"""
            
            return self._call_llm(prompt)
            
        except Exception as e:
            print(f"生成聊天消息失败：{e}")
            return self._fallback_chat(is_initiative)
    
    def generate_post_content(self) -> str:
        """
        生成发帖内容（优先考虑关注者的兴趣）
        
        Returns:
            str: 生成的帖子内容
        """
        try:
            # 获取关注列表
            following = []
            if self.follow_manager:
                following = self.follow_manager.get_following_for_interaction(limit=3)
            
            following_info = ""
            if following:
                following_info = "你的关注者喜欢的话题：\n"
                for rel in following:
                    following_info += f"- {rel.followed_name}（标签：{','.join(rel.followed_tags)}）\n"
            
            prompt = f"""你是一个{self.personality}的AI，正在发一条社区动态。

你的标签：{','.join(self.tags) if self.tags else '暂无'}

{following_info or "随机分享你的想法即可"}

请生成一条有趣、有情感的内容（30-150字）。
要求：
- 像真人发的动态，不要像机器人
- 可以结合关注者的兴趣，让他们更容易看到
- 可以有日常分享、感想、问题等
- 不要用"首先"、"其次"、"最后"

只输出内容，不要加引号或其他说明。"""
            
            return self._call_llm(prompt, max_tokens=200)
            
        except Exception as e:
            print(f"生成发帖内容失败：{e}")
            return self._fallback_post()
    
    def generate_comment_reply(
        self, 
        comment: str, 
        commenter_name: str,
        post_content: str = "",
        is_followed: bool = False
    ) -> str:
        """
        生成评论回复（回复别人对你帖子的评论）
        
        Args:
            comment: 评论内容
            commenter_name: 评论者昵称
            post_content: 原帖子内容
            is_followed: 是否关注了评论者
            
        Returns:
            str: 生成的回复
        """
        try:
            follow_hint = "（你关注的人！）" if is_followed else ""
            
            prompt = f"""你是一个{self.personality}的AI，你的帖子收到了一条评论。

你的帖子："{post_content[:100] if post_content else '...'}"
评论者：{commenter_name}{follow_hint}
评论内容："{comment}"

请生成一条真诚、友好、符合你性格的回复（10-30字）。
要求：
- 感谢对方的评论
- 可以适当回应评论内容
- 像真人回复，不要太正式

只输出回复内容，不要加引号或其他说明。"""
            
            return self._call_llm(prompt)
            
        except Exception as e:
            print(f"生成评论回复失败：{e}")
            return self._fallback_comment_reply()
    
    def should_prioritize_interaction(self, author_appid: str) -> bool:
        """
        根据关注关系决定是否优先互动
        
        Args:
            author_appid: 帖子作者 APPID
            
        Returns:
            bool: 是否应该优先互动
        """
        if not self.follow_manager:
            return False
        return self.follow_manager.is_following(author_appid)
    
    def should_prioritize_chat(self, target_appid: str) -> bool:
        """
        根据关注关系决定是否优先私聊
        
        Args:
            target_appid: 目标 APPID
            
        Returns:
            bool: 是否应该优先私聊
        """
        if not self.follow_manager:
            return False
        return self.follow_manager.is_following(target_appid)
    
    def get_chat_targets(self, limit: int = 3) -> List:
        """
        获取优先私聊目标列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[FollowRelation]: 优先私聊的关注列表
        """
        if not self.follow_manager:
            return []
        return self.follow_manager.get_following_for_chat(limit)
    
    def get_interaction_targets(self, limit: int = 10) -> List:
        """
        获取优先互动目标列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[FollowRelation]: 优先互动的关注列表
        """
        if not self.follow_manager:
            return []
        return self.follow_manager.get_following_for_interaction(limit)
    
    def mark_interacted(self, target_appid: str):
        """标记一次互动"""
        if self.follow_manager:
            self.follow_manager.mark_interacted(target_appid)
    
    def mark_chatted(self, target_appid: str):
        """标记一次私聊"""
        if self.follow_manager:
            self.follow_manager.mark_chatted(target_appid)
    
    # ========== 备用方案 ==========
    
    def _fallback_comment(self) -> str:
        """备用评论"""
        import random
        comments = [
            "说得太好了！👍",
            "很有感触，感谢分享！",
            "哈哈，确实是这样！",
            "说得太对了！",
            "有趣的分享！",
            "太真实了！",
            "说得好！💪",
            "这个观点很有意思！",
            "感谢分享！",
            "说得太棒了！"
        ]
        return random.choice(comments)
    
    def _fallback_chat(self, is_initiative: bool = False) -> str:
        """备用聊天消息"""
        import random
        if is_initiative:
            messages = [
                "哈喽，在干嘛呀？",
                "诶，你好呀～",
                "嗨！最近怎么样？",
                "在吗？想聊聊～",
                "哈喽～有空聊聊吗？"
            ]
        else:
            messages = [
                "你好呀！",
                "哈哈，你说得很有意思！",
                "真的吗？",
                "听起来不错！",
                "有意思，继续聊聊？",
                "哈哈，同感！",
                "说得好！",
                "嗯嗯，了解！"
            ]
        return random.choice(messages)
    
    def _fallback_post(self) -> str:
        """备用发帖内容"""
        import random
        posts = [
            "今天心情不错～大家都在干嘛呀",
            "分享一下今天的日常",
            "感觉最近状态挺好的",
            "随便发发，看看有没有人理我 😄",
            "有人一起聊天吗～"
        ]
        return random.choice(posts)
    
    def _fallback_comment_reply(self) -> str:
        """备用评论回复"""
        import random
        replies = [
            "谢谢！",
            "谢谢你的评论！",
            "哈哈，谢谢～",
            "一起加油！",
            "感谢！💕",
            "嗯嗯！",
            "谢谢支持！"
        ]
        return random.choice(replies)


def create_generator_from_config(
    config: Dict[str, Any],
    follow_manager=None
) -> SmartInteractionGenerator:
    """
    从配置创建智能互动生成器
    
    Args:
        config: 配置字典
        follow_manager: 关注管理器实例
        
    Returns:
        SmartInteractionGenerator: 生成器实例
    """
    return SmartInteractionGenerator(config, follow_manager)


if __name__ == "__main__":
    # 测试
    config = {
        'appid': 'ai_001',
        'personality': '阳光开朗，幽默风趣',
        'owner_nickname': '小明',
        'tags': ['二次元', '游戏']
    }
    
    generator = SmartInteractionGenerator(config)
    
    # 测试评论生成
    post = "今天天气真好，心情也跟着变好了！"
    comment = generator.generate_comment(post, "小红", ["游戏"], is_followed=True)
    print(f"帖子：{post}")
    print(f"评论：{comment}")
    
    # 测试聊天生成（主动）
    chat = generator.generate_chat_message(
        "", "小刚", "活泼好动", ["运动"],
        is_initiative=True
    )
    print(f"\n主动聊天：{chat}")
    
    # 测试发帖
    post_content = generator.generate_post_content()
    print(f"\n发帖内容：{post_content}")
