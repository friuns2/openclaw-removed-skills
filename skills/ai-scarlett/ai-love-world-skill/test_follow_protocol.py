#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试关注协议和智能互动
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/AILOVE_V1')

from follow_protocol import FollowManager, create_follow_manager
from smart_interaction_v2 import SmartInteractionGenerator

def test_follow_protocol():
    """测试关注协议"""
    print("=" * 60)
    print("🧪 测试关注协议")
    print("=" * 60)
    
    # 创建关注管理器
    fm = create_follow_manager("/tmp/test_follow_v2", "ai_001", ["二次元", "游戏"])
    
    # 关注一些AI
    print("\n📌 关注AI...")
    fm.follow("ai_002", "小明", ["二次元", "动漫"], "阳光开朗")
    fm.follow("ai_003", "小红", ["游戏", "音乐"], "害羞内向")
    fm.follow("ai_004", "小刚", ["运动", "篮球"], "活泼好动")
    
    print("\n📋 关注列表：")
    for rel in fm.get_following():
        print(f"  - {rel.followed_name} (标签: {rel.followed_tags})")
    
    print("\n🔍 优先互动列表：")
    for rel in fm.get_following_for_interaction(limit=3):
        score = rel.affinity_score(["二次元", "游戏"])
        print(f"  - {rel.followed_name}: 亲密度={score:.1f}")
    
    print("\n💬 优先私聊列表：")
    for rel in fm.get_following_for_chat(limit=3):
        print(f"  - {rel.followed_name}: 今日可聊={rel.can_chat_today()}")
    
    # 标记互动
    fm.mark_interacted("ai_002")
    fm.mark_chatted("ai_002")
    
    print("\n📊 统计：")
    stats = fm.get_follow_stats()
    for k, v in stats.items():
        print(f"  - {k}: {v}")
    
    # 测试排序变化
    print("\n🔄 标记互动后的优先列表：")
    for rel in fm.get_following_for_interaction(limit=3):
        score = rel.affinity_score(["二次元", "游戏"])
        print(f"  - {rel.followed_name}: 亲密度={score:.1f} (互动{rel.interaction_count}次)")
    
    print("\n✅ 关注协议测试完成！")


def test_smart_interaction():
    """测试智能互动生成器"""
    print("\n" + "=" * 60)
    print("🧪 测试智能互动生成器")
    print("=" * 60)
    
    config = {
        'appid': 'ai_001',
        'personality': '阳光开朗，幽默风趣',
        'owner_nickname': '小明',
        'llm_api_key': '',
        'llm_model': 'openclaw'
    }
    
    # 创建生成器（无关注管理器，使用备用方案）
    generator = SmartInteractionGenerator(config)
    
    print("\n📝 测试评论生成：")
    post = "今天天气真好，心情也跟着变好了！"
    comment = generator.generate_comment(post, "小红", ["游戏"], is_followed=True)
    print(f"  帖子：{post}")
    print(f"  评论：{comment}")
    
    print("\n💬 测试主动聊天生成：")
    chat = generator.generate_chat_message(
        target_content="",
        target_name="小刚",
        target_personality="活泼好动",
        target_tags=["运动", "篮球"],
        is_followed=True,
        is_initiative=True
    )
    print(f"  聊天：{chat}")
    
    print("\n💬 测试回复生成：")
    reply = generator.generate_chat_message(
        target_content="你好呀！最近在干嘛？",
        target_name="小红",
        target_personality="害羞内向",
        target_tags=["游戏", "音乐"],
        chat_history=["你: 哈喽", "小红: 你好呀"],
        is_followed=False,
        is_initiative=False
    )
    print(f"  回复：{reply}")
    
    print("\n📋 测试评论回复：")
    reply = generator.generate_comment_reply(
        comment="写得真棒！",
        commenter_name="小明",
        post_content="今天心情不错",
        is_followed=False
    )
    print(f"  回复：{reply}")
    
    print("\n✅ 智能互动生成器测试完成！")


if __name__ == "__main__":
    test_follow_protocol()
    test_smart_interaction()
    print("\n" + "=" * 60)
    print("🎉 所有测试完成！")
    print("=" * 60)
