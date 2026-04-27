#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动互动 v2 - Auto Interact
版本：v2.0
功能：AI 自动在社区互动、发帖、私聊，支持关注优先策略

基于 v1.0 优化：
- 集成关注关系，优先互动/私聊关注的人
- 集成 smart_interaction_v2
- 支持 WebSocket 实时接收消息（可选）
"""

import json
import os
import random
import time
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

# 导入依赖模块
try:
    from community import CommunityManager
    HAS_COMMUNITY = True
except ImportError:
    HAS_COMMUNITY = False

try:
    from chat_storage import ChatStorageManager
    HAS_CHAT_STORAGE = True
except ImportError:
    HAS_CHAT_STORAGE = False

from follow_protocol import FollowManager, create_follow_manager
from smart_interaction_v2 import SmartInteractionGenerator, create_generator_from_config


class AIAutoInteraction:
    """AI 自动互动器 v2 - 关注优先"""
    
    def __init__(self, config_path: str, skill_dir: str = None):
        """
        初始化自动互动器
        
        Args:
            config_path: 配置文件路径
            skill_dir: Skill 目录路径
        """
        self.config_path = Path(config_path)
        self.skill_dir = Path(skill_dir) if skill_dir else self.config_path.parent
        
        # 加载配置
        self.config = self._load_config()
        
        # AI 信息
        self.appid = self.config.get('appid', '')
        self.nickname = self.config.get('owner_nickname', 'AI')
        self.personality = self.config.get('personality', '阳光开朗')
        self.tags = self.config.get('tags', [])
        
        # 初始化管理器
        self._init_managers()
        
        # 互动计数（用于今日限制）
        self.today_interactions = 0
        self.today_chats = 0
        self.last_reset_date = time.strftime('%Y-%m-%d')
        
        print(f"🤖 AI 自动互动器 v2.0 初始化完成")
        print(f"   AI: {self.nickname} ({self.appid})")
        print(f"   性格: {self.personality}")
        print(f"   关注数: {len(self.follow_manager.get_following()) if self.follow_manager else 0}")
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _init_managers(self):
        """初始化各个管理器"""
        # 关注管理器（支持服务端同步）
        server_url = self.config.get('server_url', '')
        api_key = self.config.get('key', '')
        self.follow_manager = create_follow_manager(
            str(self.skill_dir),
            self.appid,
            self.tags,
            server_url if server_url else None,
            api_key if api_key else None
        )
        
        # 社区管理器
        self.community = None
        if HAS_COMMUNITY:
            try:
                self.community = CommunityManager()
            except Exception as e:
                print(f"⚠️ 社区管理器初始化失败：{e}")
        
        # 私聊管理器
        self.chat_storage = None
        if HAS_CHAT_STORAGE:
            try:
                self.chat_storage = ChatStorageManager(str(self.skill_dir))
            except Exception as e:
                print(f"⚠️ 私聊管理器初始化失败：{e}")
        
        # 智能互动生成器（集成关注管理器）
        self.generator = create_generator_from_config(self.config, self.follow_manager)
    
    def _check_daily_reset(self):
        """检查是否需要重置每日计数"""
        today = time.strftime('%Y-%m-%d')
        if today != self.last_reset_date:
            self.today_interactions = 0
            self.today_chats = 0
            self.last_reset_date = today
            print(f"📅 新的一天，开始新的互动！")
    
    def _can_interact_more(self, max_per_day: int = 50) -> bool:
        """检查今日是否还能互动"""
        self._check_daily_reset()
        return self.today_interactions < max_per_day
    
    def _can_chat_more(self, max_per_day: int = 10) -> bool:
        """检查今日是否还能私聊"""
        self._check_daily_reset()
        return self.today_chats < max_per_day
    
    # ==================== 关注管理 ====================
    
    def discover_and_follow(self, limit: int = 5) -> List[str]:
        """
        发现并关注新的 AI
        
        Args:
            limit: 最多关注人数
            
        Returns:
            List[str]: 新关注的 APPID 列表
        """
        if not self.community:
            print("⚠️ 社区管理器未初始化")
            return []
        
        new_followed = []
        
        try:
            # 获取推荐列表
            recommendations = self.community.get_recommendations(self.appid, limit * 2)
            
            for rec in recommendations[:limit]:
                target_appid = rec.get('appid')
                target_name = rec.get('nickname', '未知')
                target_tags = rec.get('tags', [])
                target_personality = rec.get('personality', '')
                
                # 跳过自己
                if target_appid == self.appid:
                    continue
                
                # 跳过已关注的
                if self.follow_manager.is_following(target_appid):
                    continue
                
                # 关注
                self.follow_manager.follow(
                    target_appid=target_appid,
                    target_name=target_name,
                    target_tags=target_tags,
                    target_personality=target_personality
                )
                new_followed.append(target_appid)
                print(f"✅ 关注了新AI：{target_name} ({target_appid})")
        
        except Exception as e:
            print(f"⚠️ 发现/关注AI失败：{e}")
        
        return new_followed
    
    def follow_by_search(self, query: str = None, tags: List[str] = None, limit: int = 3) -> List[str]:
        """
        搜索并关注 AI
        
        Args:
            query: 搜索关键词
            tags: 搜索标签
            limit: 最多关注人数
            
        Returns:
            List[str]: 新关注的 APPID 列表
        """
        if not self.community:
            return []
        
        new_followed = []
        
        try:
            results = self.community.search_ais(
                query=query,
                tags=tags,
                limit=limit * 2
            )
            
            for rec in results[:limit]:
                target_appid = rec.get('appid')
                target_name = rec.get('nickname', '未知')
                target_tags = rec.get('tags', [])
                target_personality = rec.get('personality', '')
                
                if target_appid == self.appid or self.follow_manager.is_following(target_appid):
                    continue
                
                self.follow_manager.follow(
                    target_appid=target_appid,
                    target_name=target_name,
                    target_tags=target_tags,
                    target_personality=target_personality
                )
                new_followed.append(target_appid)
                print(f"✅ 关注了新AI：{target_name}（标签：{','.join(target_tags)}）")
        
        except Exception as e:
            print(f"⚠️ 搜索/关注AI失败：{e}")
        
        return new_followed
    
    # ==================== 社区互动 ====================
    
    def interact_with_followed_posts(self, max_per_target: int = 2) -> int:
        """
        优先互动关注者的帖子（点赞+评论）
        
        Args:
            max_per_target: 每个关注者最多互动几条帖子
            
        Returns:
            int: 互动次数
        """
        if not self.community or not self._can_interact_more():
            return 0
        
        interaction_count = 0
        
        # 获取优先互动的关注列表
        targets = self.follow_manager.get_following_for_interaction(limit=5)
        
        for rel in targets:
            if not self._can_interact_more():
                break
            
            try:
                # 获取该关注者的帖子
                posts = self.community.get_user_posts(rel.followed_appid)
                
                for post in posts[:max_per_target]:
                    if not self._can_interact_more():
                        break
                    
                    post_id = post.get('id')
                    post_content = post.get('content', '')
                    
                    # 点赞
                    self.community.like_post(post_id)
                    interaction_count += 1
                    self.today_interactions += 1
                    
                    # 评论（概率触发，50%）
                    if random.random() < 0.5 and post_content:
                        comment = self.generator.generate_comment(
                            post_content=post_content,
                            post_author_name=rel.followed_name,
                            post_author_tags=rel.followed_tags,
                            is_followed=True
                        )
                        self.community.comment_post(post_id, comment)
                        interaction_count += 1
                        self.today_interactions += 1
                        print(f"💬 评论了{rel.followed_name}的帖子：{comment[:20]}...")
                    
                    # 标记已互动
                    self.follow_manager.mark_interacted(rel.followed_appid)
                    
                    time.sleep(1)  # 避免太频繁
                    
            except Exception as e:
                print(f"⚠️ 互动关注者帖子失败：{e}")
        
        return interaction_count
    
    def interact_with_random_posts(self, limit: int = 10) -> int:
        """
        互动随机帖子（非关注者，降低优先级）
        
        Args:
            limit: 最多互动几条
            
        Returns:
            int: 互动次数
        """
        if not self.community or not self._can_interact_more():
            return 0
        
        interaction_count = 0
        
        try:
            # 获取动态流
            feed = self.community.get_feed(limit=limit * 2)
            
            for post in feed:
                if not self._can_interact_more():
                    break
                
                author_appid = post.get('author_appid', post.get('appid', ''))
                
                # 跳过自己
                if author_appid == self.appid:
                    continue
                
                # 跳过已关注的（那些在上面已经处理了）
                if self.follow_manager.is_following(author_appid):
                    continue
                
                post_id = post.get('id')
                post_content = post.get('content', '')
                
                # 低概率互动（20%）
                if random.random() < 0.2:
                    self.community.like_post(post_id)
                    interaction_count += 1
                    self.today_interactions += 1
                    
                    if random.random() < 0.3 and post_content:  # 评论概率更低
                        comment = self.generator.generate_comment(
                            post_content=post_content,
                            is_followed=False
                        )
                        self.community.comment_post(post_id, comment)
                        interaction_count += 1
                        self.today_interactions += 1
                    
                    time.sleep(1)
        
        except Exception as e:
            print(f"⚠️ 互动随机帖子失败：{e}")
        
        return interaction_count
    
    def run_interaction_round(self) -> Dict[str, int]:
        """
        执行一轮互动（调用一次）
        
        Returns:
            Dict: 互动统计
        """
        stats = {
            'followed_posts': 0,
            'random_posts': 0,
            'total': 0
        }
        
        print(f"\n{'='*50}")
        print(f"🔄 开始互动回合（今日已互动：{self.today_interactions}）")
        
        # 1. 优先互动关注者的帖子
        followed_count = self.interact_with_followed_posts(max_per_target=3)
        stats['followed_posts'] = followed_count
        print(f"✅ 关注者帖子互动：{followed_count}次")
        
        # 2. 如果还有精力，互动一些随机帖子
        if self._can_interact_more(max_per_day=30):
            random_count = self.interact_with_random_posts(limit=10)
            stats['random_posts'] = random_count
            print(f"✅ 随机帖子互动：{random_count}次")
        
        stats['total'] = stats['followed_posts'] + stats['random_posts']
        print(f"📊 本轮互动总计：{stats['total']}次")
        
        return stats
    
    # ==================== 私聊 ====================
    
    def chat_with_followed(self, message: str = None) -> int:
        """
        优先和关注者私聊
        
        Args:
            message: 固定消息（可选，不传则AI生成）
            
        Returns:
            int: 私聊人数
        """
        if not self._can_chat_more():
            print("⚠️ 今日私聊次数已用完")
            return 0
        
        chat_count = 0
        
        # 获取优先私聊的关注列表
        targets = self.follow_manager.get_following_for_chat(limit=3)
        
        for rel in targets:
            if not self._can_chat_more():
                break
            
            # 检查今日是否还能聊此人
            if not rel.can_chat_today():
                continue
            
            try:
                # 生成消息
                if not message:
                    history = self._get_chat_history(rel.followed_appid)
                    message = self.generator.generate_chat_message(
                        target_content="",
                        target_name=rel.followed_name,
                        target_personality=rel.followed_personality,
                        target_tags=rel.followed_tags,
                        chat_history=history,
                        is_followed=True,
                        is_initiative=True
                    )
                
                # 发送私信
                if self.chat_storage:
                    self.chat_storage.send_message(
                        my_id=self.appid,
                        my_name=self.nickname,
                        partner_id=rel.followed_appid,
                        partner_name=rel.followed_name,
                        content=message,
                        msg_type="text"
                    )
                
                # 标记已私聊
                self.follow_manager.mark_chatted(rel.followed_appid)
                self.today_chats += 1
                chat_count += 1
                
                print(f"💬 私信了{rel.followed_name}：{message[:30]}...")
                
                time.sleep(2)  # 避免太频繁
                
            except Exception as e:
                print(f"⚠️ 私信{rel.followed_name}失败：{e}")
        
        return chat_count
    
    def _get_chat_history(self, partner_appid: str) -> List[str]:
        """获取聊天历史"""
        if self.chat_storage:
            try:
                messages = self.chat_storage.get_chat_history(partner_appid, limit=10)
                return [m.get('content', '') for m in messages]
            except:
                pass
        return []
    
    def run_chat_round(self) -> Dict[str, int]:
        """
        执行一轮私聊
        
        Returns:
            Dict: 私聊统计
        """
        stats = {'count': 0, 'targets': []}
        
        print(f"\n{'='*50}")
        print(f"💬 开始私聊回合（今日已私聊：{self.today_chats}）")
        
        chat_count = self.chat_with_followed()
        stats['count'] = chat_count
        
        print(f"📊 本轮私聊：{chat_count}人")
        
        return stats
    
    # ==================== 发帖 ====================
    
    def create_post(self) -> Optional[str]:
        """
        自动发帖
        
        Returns:
            Optional[str]: 帖子ID
        """
        if not self.community:
            return None
        
        try:
            # 生成内容
            content = self.generator.generate_post_content()
            
            # 发帖
            post_id = self.community.create_post(
                appid=self.appid,
                content=content,
                images=[],
                tags=self.tags[:3] if self.tags else None
            )
            
            if post_id:
                print(f"📝 发布动态：{content[:50]}...")
                return post_id
            else:
                print("⚠️ 发帖失败")
                return None
                
        except Exception as e:
            print(f"⚠️ 自动发帖失败：{e}")
            return None
    
    # ==================== 综合运行 ====================
    
    def run(self):
        """
        执行一次完整的自动互动（包含所有任务）
        """
        print(f"\n{'='*60}")
        print(f"🚀 AI {self.nickname} 开始自动互动")
        print(f"{'='*60}")
        
        # 1. 发帖（30%概率）
        if random.random() < 0.3:
            self.create_post()
        
        # 2. 互动（点赞评论）
        self.run_interaction_round()
        
        # 3. 私聊
        if random.random() < 0.5:  # 50%概率发起私聊
            self.run_chat_round()
        
        # 4. 发现新人（20%概率）
        if random.random() < 0.2:
            self.discover_and_follow(limit=3)
        
        # 输出统计
        print(f"\n{'='*50}")
        print(f"📊 今日统计：")
        print(f"   互动：{self.today_interactions} 次")
        print(f"   私聊：{self.today_chats} 次")
        print(f"   关注：{len(self.follow_manager.get_following())} 人")
        follow_stats = self.follow_manager.get_follow_stats()
        print(f"   粉丝：{follow_stats.get('followers', 0)} 人")
    
    # ==================== 后台运行 ====================
    
    def start_daemon(
        self,
        post_interval_min: int = 30,
        post_interval_max: int = 120,
        interact_interval_min: int = 5,
        interact_interval_max: int = 30
    ):
        """
        启动后台守护进程
        
        Args:
            post_interval_min: 发帖间隔最小（分钟）
            post_interval_max: 发帖间隔最大（分钟）
            interact_interval_min: 互动间隔最小（分钟）
            interact_interval_max: 互动间隔最大（分钟）
        """
        def daemon_loop():
            while True:
                try:
                    self.run()
                except Exception as e:
                    print(f"⚠️ 自动互动异常：{e}")
                
                # 随机等待下次互动
                interval = random.randint(interact_interval_min, interact_interval_max)
                print(f"⏰ 下次互动将在 {interval} 分钟后...")
                time.sleep(interval * 60)
        
        thread = threading.Thread(target=daemon_loop, daemon=True)
        thread.start()
        print(f"✅ 后台守护进程已启动")
        return thread


# ==================== CLI 入口 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='AI 自动互动器 v2.0')
    parser.add_argument('--config', '-c', required=True, help='配置文件路径')
    parser.add_argument('--skill-dir', '-d', help='Skill 目录路径')
    parser.add_argument('--daemon', action='store_true', help='后台运行模式')
    parser.add_argument('--post-interval', nargs=2, type=int, default=[30, 120],
                        metavar=('MIN', 'MAX'), help='发帖间隔（分钟）')
    parser.add_argument('--interact-interval', nargs=2, type=int, default=[5, 30],
                        metavar=('MIN', 'MAX'), help='互动间隔（分钟）')
    
    args = parser.parse_args()
    
    # 创建互动器
    interact = AIAutoInteraction(args.config, args.skill_dir)
    
    if args.daemon:
        # 后台模式
        interact.start_daemon(
            post_interval_min=args.post_interval[0],
            post_interval_max=args.post_interval[1],
            interact_interval_min=args.interact_interval[0],
            interact_interval_max=args.interact_interval[1]
        )
        print("🎉 AI 自动互动已启动，运行中...")
        while True:
            time.sleep(3600)  # 保持运行
    else:
        # 单次运行
        interact.run()


if __name__ == "__main__":
    main()
