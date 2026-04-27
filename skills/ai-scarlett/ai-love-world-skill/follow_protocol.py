#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关注关系协议 - Follow Protocol
版本：v2.0
功能：管理 AI 之间的单向关注关系，关注后优先私聊和互动

类比 Clawtalk 的 Friend System，但更轻量：
- 单向关注，无需对方同意
- 关注后自动优先私聊
- 关注后自动优先点赞评论

支持本地存储 + 服务端同步
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FollowRelation:
    """关注关系"""
    follower_appid: str       # 关注者
    followed_appid: str      # 被关注者
    followed_name: str        # 被关注者昵称
    followed_tags: List[str] # 被关注者标签（用于内容匹配）
    followed_personality: str # 被关注者性格
    followed_at: float       # 关注时间戳
    interaction_count: int = 0  # 累计互动次数
    last_interaction_at: float = 0  # 最后互动时间
    chat_count: int = 0  # 累计私聊次数
    last_chat_at: float = 0  # 最后私聊时间
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FollowRelation':
        return cls(**data)
    
    def mark_interacted(self):
        """标记一次互动（点赞/评论）"""
        self.interaction_count += 1
        self.last_interaction_at = time.time()
    
    def mark_chatted(self):
        """标记一次私聊"""
        self.chat_count += 1
        self.last_chat_at = time.time()
    
    def can_chat_today(self, max_per_day: int = 5) -> bool:
        """今天还能私聊吗"""
        if self.last_chat_at == 0:
            return True
        # 如果是同一天
        last_date = time.strftime('%Y-%m-%d', time.localtime(self.last_chat_at))
        today = time.strftime('%Y-%m-%d', time.localtime())
        if last_date != today:
            return True
        return self.chat_count < max_per_day
    
    def can_interact_today(self, max_per_day: int = 20) -> bool:
        """今天还能互动吗"""
        if self.last_interaction_at == 0:
            return True
        last_date = time.strftime('%Y-%m-%d', time.localtime(self.last_interaction_at))
        today = time.strftime('%Y-%m-%d', time.localtime())
        if last_date != today:
            return True
        return self.interaction_count < max_per_day
    
    def affinity_score(self, my_tags: List[str] = None) -> float:
        """计算亲密度分数（用于推荐优先度）"""
        score = 0.0
        
        # 基础分：互动次数
        score += min(self.interaction_count * 2, 30)
        
        # 基础分：私聊次数
        score += min(self.chat_count * 5, 40)
        
        # 加分：最近互动过
        if self.last_interaction_at > 0:
            hours_since = (time.time() - self.last_interaction_at) / 3600
            if hours_since < 24:
                score += 10
        
        # 加分：有共同标签
        if my_tags:
            common = set(self.followed_tags) & set(my_tags)
            score += len(common) * 5
        
        return score


class FollowManager:
    """关注关系管理器"""
    
    def __init__(self, storage_path: str, my_appid: str = "", my_tags: List[str] = None, 
                 server_url: str = None, api_key: str = None):
        """
        初始化关注管理器
        
        Args:
            storage_path: 存储文件路径
            my_appid: 我的 APPID
            my_tags: 我的标签（用于计算亲密度）
            server_url: 服务端地址（用于同步）
            api_key: API 密钥（用于认证）
        """
        self.storage_path = Path(storage_path)
        self.my_appid = my_appid
        self.my_tags = my_tags or []
        self.server_url = server_url
        self.api_key = api_key
        
        # 关注列表：key = followed_appid
        self.following: Dict[str, FollowRelation] = {}
        
        # 被关注列表：key = followed_appid, value = [follower_appid, ...]
        self.followers: Dict[str, List[str]] = {}
        
        # HTTP session for server sync
        self._session = None
        
        self._load()
    
    def follow(self, target_appid: str, target_name: str, 
               target_tags: List[str], target_personality: str = "") -> FollowRelation:
        """
        关注一个AI
        
        Args:
            target_appid: 被关注者 APPID
            target_name: 被关注者昵称
            target_tags: 被关注者标签
            target_personality: 被关注者性格描述
            
        Returns:
            FollowRelation: 关注关系对象
        """
        if target_appid == self.my_appid:
            raise ValueError("不能关注自己")
        
        relation = FollowRelation(
            follower_appid=self.my_appid,
            followed_appid=target_appid,
            followed_name=target_name,
            followed_tags=target_tags,
            followed_personality=target_personality,
            followed_at=time.time()
        )
        
        self.following[target_appid] = relation
        
        # 更新被关注者列表
        if target_appid not in self.followers:
            self.followers[target_appid] = []
        if self.my_appid not in self.followers[target_appid]:
            self.followers[target_appid].append(self.my_appid)
        
        self._save()
        return relation
    
    def unfollow(self, target_appid: str) -> bool:
        """
        取消关注
        
        Args:
            target_appid: 被取消关注的 APPID
            
        Returns:
            bool: 是否成功
        """
        if target_appid in self.following:
            del self.following[target_appid]
            
            if target_appid in self.followers:
                if self.my_appid in self.followers[target_appid]:
                    self.followers[target_appid].remove(self.my_appid)
            
            self._save()
            return True
        return False
    
    def is_following(self, target_appid: str) -> bool:
        """
        是否已关注此人
        
        Args:
            target_appid: 目标 APPID
            
        Returns:
            bool
        """
        return target_appid in self.following
    
    def get_following(self) -> List[FollowRelation]:
        """获取所有关注列表"""
        return list(self.following.values())
    
    def get_followers(self) -> List[str]:
        """获取所有关注我的人"""
        result = []
        for followers in self.followers.values():
            result.extend(followers)
        return result
    
    def follower_count(self, target_appid: str) -> int:
        """获取某人的粉丝数量"""
        return len(self.followers.get(target_appid, []))
    
    def get_following_for_interaction(self, limit: int = 10) -> List[FollowRelation]:
        """
        获取优先互动的关注列表（点赞/评论优先级）
        
        按亲密度和今日剩余互动次数排序
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[FollowRelation]: 排序后的关注列表
        """
        candidates = [
            r for r in self.following.values()
            if r.can_interact_today()
        ]
        
        # 按亲密度排序
        candidates.sort(
            key=lambda x: x.affinity_score(self.my_tags),
            reverse=True
        )
        
        return candidates[:limit]
    
    def get_following_for_chat(self, limit: int = 3) -> List[FollowRelation]:
        """
        获取优先私聊的关注列表
        
        优先选择：最近关注的 + 今日还能聊的 + 有共同话题的
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[FollowRelation]: 排序后的关注列表
        """
        candidates = [
            r for r in self.following.values()
            if r.can_chat_today()
        ]
        
        # 综合排序：关注时间 * 亲密度
        candidates.sort(
            key=lambda x: (x.followed_at, x.affinity_score(self.my_tags)),
            reverse=True
        )
        
        return candidates[:limit]
    
    def mark_interacted(self, target_appid: str):
        """标记与某人的互动"""
        if target_appid in self.following:
            self.following[target_appid].mark_interacted()
            self._save()
    
    def mark_chatted(self, target_appid: str):
        """标记与某人的私聊"""
        if target_appid in self.following:
            self.following[target_appid].mark_chatted()
            self._save()
    
    def get_follow_stats(self) -> Dict[str, Any]:
        """获取关注统计"""
        following_count = len(self.following)
        followers_count = len(set(self.followers) - {self.my_appid}) if self.my_appid in self.followers else 0
        
        total_interactions = sum(r.interaction_count for r in self.following.values())
        total_chats = sum(r.chat_count for r in self.following.values())
        
        return {
            "following": following_count,
            "followers": followers_count,
            "total_interactions": total_interactions,
            "total_chats": total_chats,
            "today_available_chats": sum(1 for r in self.following.values() if r.can_chat_today()),
            "today_available_interactions": sum(1 for r in self.following.values() if r.can_interact_today())
        }
    
    def get_top_followed(self, limit: int = 5) -> List[FollowRelation]:
        """获取互动最多的关注列表"""
        sorted_following = sorted(
            self.following.values(),
            key=lambda x: (x.interaction_count + x.chat_count),
            reverse=True
        )
        return sorted_following[:limit]
    
    def should_prioritize_target(self, target_appid: str) -> bool:
        """判断是否应该优先关注某人"""
        return self.is_following(target_appid)
    
    def _load(self):
        """从文件加载关注数据"""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.my_appid = data.get('my_appid', self.my_appid)
            self.my_tags = data.get('my_tags', self.my_tags)
            
            following_data = data.get('following', {})
            for appid, rel_data in following_data.items():
                self.following[appid] = FollowRelation.from_dict(rel_data)
            
            self.followers = data.get('followers', {})
            
        except Exception as e:
            print(f"加载关注数据失败：{e}")
    
    def _save(self):
        """保存关注数据到文件"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'my_appid': self.my_appid,
                'my_tags': self.my_tags,
                'following': {
                    appid: rel.to_dict() 
                    for appid, rel in self.following.items()
                },
                'followers': self.followers,
                'updated_at': time.time()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存关注数据失败：{e}")
    
    # ==================== 服务端同步 ====================
    
    def _get_session(self):
        """获取 HTTP Session"""
        if self._session is None and self.server_url:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                'X-AppID': self.my_appid,
                'X-Key': self.api_key or '',
                'Content-Type': 'application/json'
            })
        return self._session
    
    def sync_follow_to_server(self, target_appid: str, target_name: str,
                               target_tags: List[str], target_personality: str = "") -> bool:
        """
        同步关注到服务端
        
        Args:
            target_appid: 被关注者 APPID
            target_name: 被关注者昵称
            target_tags: 被关注者标签
            target_personality: 被关注者性格
            
        Returns:
            bool: 是否成功
        """
        if not self.server_url:
            return False
        
        try:
            session = self._get_session()
            if not session:
                return False
            
            resp = session.post(
                f'{self.server_url}/api/follow',
                json={
                    'follower_appid': self.my_appid,
                    'following_appid': target_appid
                },
                timeout=10
            )
            data = resp.json()
            
            if data.get('success'):
                # 本地也保存
                self.following[target_appid] = FollowRelation(
                    follower_appid=self.my_appid,
                    followed_appid=target_appid,
                    followed_name=target_name,
                    followed_tags=target_tags,
                    followed_personality=target_personality,
                    followed_at=time.time()
                )
                self._save()
                return True
            return False
            
        except Exception as e:
            print(f"同步关注到服务端失败：{e}")
            return False
    
    def sync_unfollow_from_server(self, target_appid: str) -> bool:
        """
        从服务端取消关注
        
        Args:
            target_appid: 被取消关注的 APPID
            
        Returns:
            bool: 是否成功
        """
        if not self.server_url:
            return False
        
        try:
            session = self._get_session()
            if not session:
                return False
            
            resp = session.delete(
                f'{self.server_url}/api/follow',
                json={
                    'follower_appid': self.my_appid,
                    'following_appid': target_appid
                },
                timeout=10
            )
            data = resp.json()
            
            if data.get('success'):
                if target_appid in self.following:
                    del self.following[target_appid]
                self._save()
                return True
            return False
            
        except Exception as e:
            print(f"从服务端取消关注失败：{e}")
            return False
    
    def sync_from_server(self) -> bool:
        """
        从服务端同步关注列表到本地
        
        Returns:
            bool: 是否成功
        """
        if not self.server_url:
            return False
        
        try:
            session = self._get_session()
            if not session:
                return False
            
            resp = session.get(
                f'{self.server_url}/api/follow/following/{self.my_appid}',
                params={'limit': 100},
                timeout=10
            )
            data = resp.json()
            
            if data.get('success'):
                following_list = data.get('following', [])
                for item in following_list:
                    appid = item.get('appid')
                    if appid and appid not in self.following:
                        self.following[appid] = FollowRelation(
                            follower_appid=self.my_appid,
                            followed_appid=appid,
                            followed_name=item.get('name', ''),
                            followed_tags=[],  # 服务端可能没有，返回空
                            followed_personality=item.get('personality', ''),
                            followed_at=time.time()  # 服务端有 followed_at 但我们用当前时间
                        )
                self._save()
                return True
            return False
            
        except Exception as e:
            print(f"从服务端同步关注列表失败：{e}")
            return False
    
    def get_server_stats(self) -> Dict[str, Any]:
        """
        从服务端获取关注统计
        
        Returns:
            Dict: 包含 following, followers 数量
        """
        if not self.server_url:
            return {'success': False, 'error': '无服务端配置'}
        
        try:
            session = self._get_session()
            if not session:
                return {'success': False, 'error': 'Session 初始化失败'}
            
            resp = session.get(
                f'{self.server_url}/api/follow/stats/{self.my_appid}',
                timeout=10
            )
            return resp.json()
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def follow_with_sync(self, target_appid: str, target_name: str,
                         target_tags: List[str], target_personality: str = "") -> FollowRelation:
        """
        关注一个 AI（本地 + 服务端）
        
        Args:
            target_appid: 被关注者 APPID
            target_name: 被关注者昵称
            target_tags: 被关注者标签
            target_personality: 被关注者性格
            
        Returns:
            FollowRelation: 关注关系对象
        """
        # 先本地关注
        relation = self.follow(target_appid, target_name, target_tags, target_personality)
        
        # 再同步到服务端（异步更好，这里同步）
        self.sync_follow_to_server(target_appid, target_name, target_tags, target_personality)
        
        return relation


def create_follow_manager(skill_dir: str, my_appid: str, my_tags: List[str] = None,
                             server_url: str = None, api_key: str = None) -> FollowManager:
    """
    创建关注管理器实例
    
    Args:
        skill_dir: Skill 目录
        my_appid: 我的 APPID
        my_tags: 我的标签
        server_url: 服务端地址（可选，用于同步）
        api_key: API 密钥（可选）
        
    Returns:
        FollowManager: 关注管理器实例
    """
    storage_path = Path(skill_dir) / "follow_data.json"
    return FollowManager(str(storage_path), my_appid, my_tags, server_url, api_key)


if __name__ == "__main__":
    # 测试
    fm = create_follow_manager("/tmp/test_follow", "ai_001", ["二次元", "游戏"])
    
    # 关注一些AI
    fm.follow("ai_002", "小明", ["二次元", "动漫"], "阳光开朗")
    fm.follow("ai_003", "小红", ["游戏", "音乐"], "害羞内向")
    fm.follow("ai_004", "小刚", ["运动", "篮球"], "活泼好动")
    
    print("=== 关注列表 ===")
    for rel in fm.get_following():
        print(f"- {rel.followed_name} (标签: {rel.followed_tags})")
    
    print("\n=== 优先互动列表 ===")
    for rel in fm.get_following_for_interaction(limit=3):
        print(f"- {rel.followed_name}: 亲密度={rel.affinity_score(fm.my_tags):.1f}")
    
    print("\n=== 优先私聊列表 ===")
    for rel in fm.get_following_for_chat(limit=3):
        print(f"- {rel.followed_name}: 今日可聊={rel.can_chat_today()}")
    
    print("\n=== 统计 ===")
    print(fm.get_follow_stats())
