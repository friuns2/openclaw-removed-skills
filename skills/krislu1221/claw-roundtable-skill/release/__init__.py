#!/usr/bin/env python3
"""
RoundTable Skill - 多 Agent 深度讨论系统 V2

需求驱动的智能专家匹配系统，集成 146 个全领域专家。
模拟真实圆桌会议，按议题分治讨论，产生完善方案。

导出接口：
- RoundTableEngineV2: V2 执行引擎
- RequirementAnalyzer: 需求分析器
- ExpertSelector: 专家选择器
- run_roundtable_v2: 快捷入口
"""

from typing import List, Optional

from .requirement_analyzer import (
    RequirementAnalyzer,
    ExpertSelector,
    expert_pool,
    select_experts_for_topic,
    list_all_146_agents,
)
from .roundtable_engine_v2 import (
    RoundTableEngineV2,
    DiscussionState,
    TopicResult,
    run_roundtable_v2,
)
from .roundtable_notifier import RoundTableNotifier
from .agency_agents_loader import AgencyAgentsLoader, AgentProfile


async def run_roundtable(
    topic: str,
    mode: str = "pre-ac",
    complexity: str = "auto",
    user_channel: str = "",
    custom_experts: Optional[List[str]] = None,
) -> bool:
    """
    RoundTable V2 快捷入口
    
    Args:
        topic: 讨论主题
        mode: 模式（pre-ac: AC 前讨论，post-ac: AC 后审查）
        complexity: 复杂度（auto/high/medium/low）
        user_channel: 用户通知渠道
        custom_experts: 指定专家列表（可选）
        
    Returns:
        bool: 是否成功完成
    """
    return await run_roundtable_v2(
        topic=topic,
        mode=mode,
        complexity=complexity,
        user_channel=user_channel,
        custom_experts=custom_experts,
    )


__all__ = [
    # V2 核心类
    "RoundTableEngineV2",
    "RequirementAnalyzer",
    "ExpertSelector",
    "RoundTableNotifier",
    "AgencyAgentsLoader",
    # 数据类
    "DiscussionState",
    "TopicResult",
    "AgentProfile",
    # 快捷函数
    "run_roundtable",
    "run_roundtable_v2",
    "select_experts_for_topic",
    "list_all_146_agents",
    # 专家池
    "expert_pool",
]

__version__ = "0.9.1"
