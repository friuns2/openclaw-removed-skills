#!/usr/bin/env python3
"""
RoundTable V2 Engine - 需求驱动的多专家讨论引擎

核心改进：
1. 需求智能拆解 → 精准匹配专家
2. 按议题分治讨论 → 不再固定 5 轮
3. 排除不相关专家 → 测试不参与设计阶段
4. 动态适配复杂度 → 简单需求快速处理

作者：虾软 Claw soft
版本：2.0.0
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from requirement_analyzer import (
    RequirementAnalyzer, 
    ExpertSelector, 
    AnalyzedRequirement,
    RequirementType,
    EXPERT_PROFILES
)
from roundtable_notifier import RoundTableNotifier


@dataclass
class ExpertResult:
    """专家执行结果"""
    expert_id: str
    expert_name: str
    content: str
    elapsed_seconds: float
    success: bool


@dataclass
class TopicResult:
    """议题讨论结果"""
    topic_name: str
    topic_type: str
    priority: str
    expert_results: List[ExpertResult]
    consensus: str = ""


class DiscussionState(Enum):
    """讨论状态"""
    ANALYZING = "analyzing"      # 需求分析中
    CONFIRMING = "confirming"    # 用户确认中
    RUNNING = "running"          # 讨论进行中
    COMPLETED = "completed"      # 讨论完成
    FAILED = "failed"            # 讨论失败


@dataclass
class DiscussionConfig:
    """讨论配置（安全加固）"""
    max_experts: int = 5              # 最大专家数
    max_topics: int = 5               # 最大议题数
    timeout_per_expert: int = 300     # 每个专家超时（秒）
    max_total_timeout: int = 1800     # 总超时（30 分钟）
    max_concurrent_experts: int = 3   # 最大并发专家数
    enable_debate: bool = True        # 是否启用辩论


class RoundTableEngineV2:
    """RoundTable V2 讨论引擎"""
    
    def __init__(
        self,
        topic: str,
        mode: str = "pre-ac",
        complexity: str = "auto",  # auto/high/medium/low
        custom_experts: Optional[List[str]] = None,
        primary_model: str = None,
    ):
        """
        初始化 RoundTable V2 引擎
        
        Args:
            topic: 讨论主题
            mode: 模式（pre-ac: AC 前讨论，post-ac: AC 后审查）
            complexity: 复杂度（auto/high/medium/low）
            custom_experts: 指定专家列表（可选）
            primary_model: 主模型 ID（可选）
        """
        self.topic = topic
        self.mode = mode
        self.complexity = complexity
        self.custom_experts = custom_experts
        self.primary_model = primary_model
        
        # 核心组件
        self.analyzer = RequirementAnalyzer()
        self.expert_selector = ExpertSelector()
        self.notifier = RoundTableNotifier(topic, mode)
        
        # 状态
        self.state = DiscussionState.ANALYZING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # 分析结果
        self.requirement: Optional[AnalyzedRequirement] = None
        self.selected_experts: List[str] = []
        self.key_topics: List[Dict] = []
        
        # 讨论结果
        self.results: Dict[str, TopicResult] = {}
        
        # 模型选择器
        from model_selector import ModelSelector
        self.model_selector = ModelSelector(primary_model=primary_model)
        self.expert_model_mapping: Dict[str, str] = {}
    
    async def run(self, user_channel: str) -> bool:
        """运行完整 RoundTable V2 流程"""
        print(f"\n🔄 RoundTable V2 启动：{self.topic}")
        print("="*60)
        
        # 1. 需求分析
        print("\n📋 步骤 1: 需求智能拆解")
        print("-"*60)
        self.requirement = self.analyzer.analyze(self.topic)
        
        print(f"检测到的需求类型：{[t.value for t in self.requirement.detected_types]}")
        print(f"推荐专家：{self.requirement.recommended_experts}")
        print(f"排除专家：{self.requirement.excluded_experts}")
        
        # 2. 用户确认配置
        print("\n🎯 步骤 2: 用户确认")
        print("-"*60)
        config_result = await self._confirm_config(user_channel)
        if not config_result:
            print("❌ 用户取消 RoundTable")
            return False
        
        # 3. 分配模型
        self._assign_models_to_experts()
        
        # 4. 发送开始通知
        self.state = DiscussionState.RUNNING
        self.start_time = datetime.now()
        await self.notifier.send_start_notification_v2(
            user_channel, 
            self.selected_experts,
            len(self.key_topics)
        )
        
        # 5. 按议题分治讨论
        print("\n📝 步骤 3: 分议题讨论")
        print("-"*60)
        
        for i, topic_info in enumerate(self.key_topics, 1):
            print(f"\n{'='*60}")
            print(f"📍 议题 {i}/{len(self.key_topics)}: {topic_info['name']}")
            print(f"{'='*60}")
            
            # 找到与该议题相关的专家
            relevant_experts = self._find_relevant_experts(topic_info)
            print(f"参与专家：{relevant_experts}")
            
            # 主持讨论
            topic_result = await self._facilitate_topic_discussion(
                topic_info,
                relevant_experts,
                user_channel
            )
            
            self.results[topic_info['name']] = topic_result
            
            # 发送进度更新
            await self.notifier.send_progress_update_v2(
                user_channel,
                i,
                len(self.key_topics),
                topic_result
            )
        
        # 6. 整合方案
        print("\n📊 步骤 4: 整合方案")
        print("-"*60)
        final_plan = self._merge_results()
        
        # 7. 完成
        self.state = DiscussionState.COMPLETED
        self.end_time = datetime.now()
        
        await self.notifier.send_completion_notification_v2(
            user_channel,
            final_plan,
            self.results
        )
        
        print(f"\n✅ RoundTable V2 完成！")
        return True
    
    async def _confirm_config(self, user_channel: str) -> bool:
        """用户确认配置"""
        # 应用复杂度配置
        self._apply_complexity_config()
        
        # 准备配置信息
        config_message = f"""
📋 **RoundTable V2 配置**

**讨论主题**：{self.topic}

**检测到的需求类型**：
{chr(10).join(['- ' + t.value for t in self.requirement.detected_types])}

**推荐专家阵容**：
{chr(10).join(['- ' + EXPERT_PROFILES[e].name for e in self.requirement.recommended_experts if e not in self.requirement.excluded_experts])}

**关键议题**：
{chr(10).join(['- ' + t['name'] + ' (' + t['priority'] + ')' for t in self.requirement.key_topics])}

**预计耗时**：{self._estimate_duration()}分钟
**预计 Token**：{self._estimate_tokens()}

⚠️ **排除的专家**：
{chr(10).join(['- ' + EXPERT_PROFILES[e].name + '（不参与{phase}阶段）'.format(e=e, phase=EXPERT_PROFILES[e].exclude_phases[0] if EXPERT_PROFILES[e].exclude_phases else '当前') for e in self.requirement.excluded_experts]) if self.requirement.excluded_experts else '无'}

回复"**确认**"开始讨论
回复"**调整**"手动修改专家阵容
"""
        
        print(config_message)
        
        # 发送确认（实际实现中需要等待用户回复）
        # 演示用，默认确认
        return True
    
    def _apply_complexity_config(self):
        """应用复杂度配置"""
        if self.complexity == "auto":
            # 自动根据需求类型数量判断
            type_count = len(self.requirement.detected_types)
            if type_count >= 4:
                self.complexity = "high"
            elif type_count >= 2:
                self.complexity = "medium"
            else:
                self.complexity = "low"
        
        # 根据复杂度调整配置
        if self.complexity == "low":
            # 简单需求：最多 2 个专家，2 个议题
            self.selected_experts = self.requirement.recommended_experts[:2]
            self.key_topics = self.requirement.key_topics[:2]
        elif self.complexity == "medium":
            # 中等需求：最多 3 个专家，3 个议题
            self.selected_experts = self.requirement.recommended_experts[:3]
            self.key_topics = self.requirement.key_topics[:3]
        else:  # high
            # 高复杂度：最多 5 个专家，5 个议题
            self.selected_experts = self.requirement.recommended_experts[:5]
            self.key_topics = self.requirement.key_topics[:5]
        
        # 排除用户指定的专家
        if self.requirement.excluded_experts:
            self.selected_experts = [
                e for e in self.selected_experts 
                if e not in self.requirement.excluded_experts
            ]
        
        # 如果用户自定义专家，覆盖自动选择
        if self.custom_experts:
            self.selected_experts = self.custom_experts
    
    def _assign_models_to_experts(self):
        """为专家分配模型"""
        for expert_id in self.selected_experts:
            profile = EXPERT_PROFILES.get(expert_id)
            if not profile:
                continue
            
            # 根据领域分配模型
            if RequirementType.AI_ML in profile.domains:
                role = "ai"
            elif RequirementType.ARCHITECTURE in profile.domains:
                role = "engineering"
            elif RequirementType.UX_DESIGN in profile.domains:
                role = "design"
            else:
                role = "general"
            
            model_id = self.model_selector.select_model_for_role(role)
            self.expert_model_mapping[expert_id] = model_id
    
    def _find_relevant_experts(self, topic_info: Dict) -> List[str]:
        """找到与议题相关的专家"""
        topic_type = topic_info.get('type', '')
        relevant = []
        
        for expert_id in self.selected_experts:
            profile = EXPERT_PROFILES.get(expert_id)
            if profile:
                # 检查专家领域是否匹配议题类型
                for domain in profile.domains:
                    if domain.value == topic_type:
                        relevant.append(expert_id)
                        break
        
        # 如果没有找到匹配的专家，返回所有选中的专家
        return relevant if relevant else self.selected_experts
    
    async def _facilitate_topic_discussion(
        self,
        topic_info: Dict,
        experts: List[str],
        user_channel: str
    ) -> TopicResult:
        """主持议题讨论"""
        expert_results = []
        
        # 并行执行所有专家
        tasks = []
        for expert_id in experts:
            prompt = self._generate_expert_prompt(expert_id, topic_info)
            tasks.append(self._execute_expert(expert_id, prompt))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(results):
            expert_id = experts[i]
            if isinstance(result, Exception):
                expert_results.append(ExpertResult(
                    expert_id=expert_id,
                    expert_name=EXPERT_PROFILES.get(expert_id, {}).name if expert_id in EXPERT_PROFILES else expert_id,
                    content="",
                    elapsed_seconds=0,
                    success=False
                ))
                print(f"  ❌ {expert_id}: 执行失败 - {result}")
            else:
                expert_results.append(result)
                print(f"  ✅ {expert_id}: {result.elapsed_seconds:.1f}秒")
        
        # 整合共识（简化版：直接拼接）
        consensus = self._generate_consensus(topic_info, expert_results)
        
        return TopicResult(
            topic_name=topic_info['name'],
            topic_type=topic_info['type'],
            priority=topic_info['priority'],
            expert_results=expert_results,
            consensus=consensus
        )
    
    async def _execute_expert(self, expert_id: str, prompt: str) -> ExpertResult:
        """执行单个专家"""
        start_time = datetime.now()
        
        try:
            from openclaw.tools import sessions_spawn
            
            model_id = self.expert_model_mapping.get(expert_id)
            
            print(f"    🚀 创建专家 Agent: {expert_id}")
            if model_id:
                print(f"    🎯 使用模型：{model_id}")
            
            spawn_kwargs = {
                'task': prompt,
                'runtime': 'subagent',
                'mode': 'run',
                'label': f"rt-v2-{self.topic[:10]}-{expert_id}",
                'timeoutSeconds': 300,
                'thinking': 'on'
            }
            
            if model_id:
                spawn_kwargs['model'] = model_id
            
            session_result = await sessions_spawn(**spawn_kwargs)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # 提取结果
            content = ""
            if hasattr(session_result, 'result') and session_result.result:
                content = session_result.result
            elif isinstance(session_result, dict) and 'output' in session_result:
                content = session_result['output']
            else:
                content = f"[{expert_id}] 已完成分析"
            
            expert_name = EXPERT_PROFILES[expert_id].name if expert_id in EXPERT_PROFILES else expert_id
            
            return ExpertResult(
                expert_id=expert_id,
                expert_name=expert_name,
                content=content,
                elapsed_seconds=elapsed,
                success=True
            )
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            # 记录详细日志（内部）
            import logging
            logging.error(f"Expert execution failed: {type(e).__name__}")
            # 返回安全消息（不暴露细节）
            return ExpertResult(
                expert_id=expert_id,
                expert_name=EXPERT_PROFILES[expert_id].name if expert_id in EXPERT_PROFILES else expert_id,
                content="执行失败：内部错误",
                elapsed_seconds=elapsed,
                success=False
            )
    
    def _generate_expert_prompt(self, expert_id: str, topic_info: Dict) -> str:
        """生成专家提示词"""
        return self.expert_selector.get_expert_prompt(
            expert_id,
            self.topic,
            topic_info
        )
    
    def _generate_consensus(self, topic_info: Dict, expert_results: List[ExpertResult]) -> str:
        """生成共识（简化版）"""
        successful_results = [r for r in expert_results if r.success]
        
        if not successful_results:
            return "⚠️ 所有专家执行失败"
        
        # 简单拼接（实际应该用另一个 Agent 整合）
        consensus_parts = []
        for result in successful_results:
            consensus_parts.append(f"### {result.expert_name}\n\n{result.content[:500]}...")
        
        return "\n\n---\n\n".join(consensus_parts)
    
    def _merge_results(self) -> str:
        """整合所有议题结果为最终方案"""
        parts = []
        
        # 按优先级排序
        sorted_topics = sorted(
            self.results.values(),
            key=lambda x: (0 if x.priority == "high" else 1)
        )
        
        for topic_result in sorted_topics:
            parts.append(f"# {topic_result.topic_name}\n\n{topic_result.consensus}")
        
        return "\n\n---\n\n".join(parts)
    
    def _estimate_duration(self) -> int:
        """预估耗时（分钟）"""
        expert_count = len(self.selected_experts)
        topic_count = len(self.key_topics)
        # 每个专家每个议题约 1-2 分钟
        return expert_count * topic_count * 2
    
    def _estimate_tokens(self) -> int:
        """预估 Token 消耗"""
        expert_count = len(self.selected_experts)
        topic_count = len(self.key_topics)
        # 每个专家约 5000-10000 Token
        return expert_count * topic_count * 8000


async def run_roundtable_v2(
    topic: str,
    mode: str = "pre-ac",
    complexity: str = "auto",
    user_channel: str = "",
    custom_experts: Optional[List[str]] = None,
    primary_model: str = None
) -> bool:
    """RoundTable V2 快捷入口"""
    engine = RoundTableEngineV2(
        topic, 
        mode, 
        complexity, 
        custom_experts, 
        primary_model
    )
    return await engine.run(user_channel)


# ==================== 快捷函数 ====================

def analyze_requirement(topic: str) -> dict:
    """
    快捷函数：分析需求
    
    用法：
    result = analyze_requirement("智能待办应用的架构设计")
    print(result)
    """
    analyzer = RequirementAnalyzer()
    requirement = analyzer.analyze(topic)
    
    return {
        "topic": topic,
        "detected_types": [t.value for t in requirement.detected_types],
        "recommended_experts": requirement.recommended_experts,
        "excluded_experts": requirement.excluded_experts,
        "key_topics": requirement.key_topics
    }


if __name__ == "__main__":
    # 测试
    topic = "智能待办应用的架构设计"
    
    print(f"\n📋 分析需求：{topic}\n")
    
    result = analyze_requirement(topic)
    
    print(f"检测到的需求类型：{result['detected_types']}")
    print(f"推荐专家：{result['recommended_experts']}")
    print(f"排除专家：{result['excluded_experts']}")
    print(f"\n关键议题：")
    for t in result['key_topics']:
        print(f"  - {t['name']} ({t['priority']})")
    
    print(f"\n✅ 需求分析完成！")
