#!/usr/bin/env python3
"""
RoundTable V2 - 需求驱动的多专家讨论系统

使用 146 个专家库（agency-agents-zh）

作者：虾软 Claw soft
版本：2.0.0
"""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from model_selector import ModelSelector
from agency_agents_loader import AgencyAgentsLoader, AgentProfile


# ==================== 需求类型定义 ====================

class RequirementType(Enum):
    """需求类型"""
    PRODUCT = "product"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    UX_DESIGN = "ux_design"
    AI_ML = "ai_ml"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    DATA = "data"


REQUIREMENT_CONFIGS = {
    RequirementType.PRODUCT: {
        "keywords": ["产品", "功能", "用户", "需求", "定位", "目标", "场景", "痛点"],
        "categories": ["product", "marketing"],
    },
    RequirementType.ARCHITECTURE: {
        "keywords": ["架构", "技术栈", "后端", "前端", "数据库", "部署", "微服务", "API", "系统", "开发"],
        "categories": ["engineering"],
    },
    RequirementType.SECURITY: {
        "keywords": ["安全", "认证", "授权", "加密", "隐私", "合规", "权限", "审计", "风控"],
        "categories": ["specialized", "engineering"],
    },
    RequirementType.UX_DESIGN: {
        "keywords": ["体验", "界面", "交互", "设计", "UI", "用户流程", "视觉", "UX", "美观"],
        "categories": ["design"],
    },
    RequirementType.AI_ML: {
        "keywords": ["AI", "智能", "算法", "模型", "推荐", "NLP", "机器学习", "深度学习", "预测", "大模型"],
        "categories": ["engineering", "specialized"],
    },
    RequirementType.PERFORMANCE: {
        "keywords": ["性能", "并发", "延迟", "优化", "缓存", "QPS", "响应时间", "吞吐量"],
        "categories": ["engineering", "testing"],
    },
    RequirementType.BUSINESS: {
        "keywords": ["商业", "营销", "运营", "推广", "策略", "增长", "小红书", "抖音", "微信", "B 站", "电商", "直播"],
        "categories": ["marketing", "sales"],
    },
    RequirementType.DATA: {
        "keywords": ["数据", "数据库", "表结构", "字段", "索引", "查询", "ETL", "数仓"],
        "categories": ["engineering"],
    }
}


@dataclass
class AnalyzedRequirement:
    """分析后的需求"""
    original_topic: str
    detected_types: List[RequirementType]
    confidence_scores: Dict[RequirementType, float]
    key_topics: List[Dict]
    recommended_experts: List[str]
    excluded_experts: List[str]


class RequirementAnalyzer:
    """需求分析器（带输入验证）"""
    
    def __init__(self):
        self.configs = REQUIREMENT_CONFIGS
    
    def analyze(self, topic: str) -> AnalyzedRequirement:
        """分析需求（带输入验证）"""
        # 输入验证
        if not topic or not isinstance(topic, str):
            raise ValueError("Invalid topic: must be a non-empty string")
        
        # 长度限制（1000 字符）
        if len(topic) > 1000:
            topic = topic[:1000]
        
        # 移除危险字符
        topic = re.sub(r'[<>{}|\\^`]', '', topic)
        topic = topic.strip()
        
        type_scores = self._match_keywords(topic)
        detected_types = self._detect_types(type_scores)
        recommended_experts = self._recommend_experts(detected_types)
        excluded_experts = self._exclude_experts(recommended_experts, detected_types)
        key_topics = self._identify_key_topics(topic, detected_types)
        
        return AnalyzedRequirement(
            original_topic=topic,
            detected_types=detected_types,
            confidence_scores=type_scores,
            key_topics=key_topics,
            recommended_experts=recommended_experts,
            excluded_experts=excluded_experts
        )
    
    def _match_keywords(self, topic: str) -> Dict[RequirementType, float]:
        """关键词匹配"""
        scores = {}
        topic_lower = topic.lower()
        
        for req_type, config in self.configs.items():
            match_count = 0
            for keyword in config["keywords"]:
                if keyword.lower() in topic_lower:
                    match_count += 1
            
            scores[req_type] = match_count / len(config["keywords"]) if config["keywords"] else 0
        
        return scores
    
    def _detect_types(self, scores: Dict[RequirementType, float]) -> List[RequirementType]:
        """识别需求类型"""
        threshold = 0.15
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        detected = [
            req_type for req_type, score in sorted_types[:3]
            if score >= threshold
        ]
        
        return detected if detected else [RequirementType.ARCHITECTURE]
    
    def _recommend_experts(self, types: List[RequirementType]) -> List[str]:
        """推荐专家"""
        from requirement_analyzer import expert_pool
        pool = expert_pool
        pool.initialize()
        
        categories = set()
        all_keywords = []
        
        for req_type in types:
            config = self.configs.get(req_type, {})
            categories.update(config.get("categories", []))
            all_keywords.extend(config.get("expert_keywords", []))
        
        experts = []
        for category in categories:
            category_experts = pool.get_agents_by_category(category)
            experts.extend(category_experts)
        
        def score_expert(expert):
            text = f"{expert.agent_id} {expert.name} {expert.description}".lower()
            return sum(1 for kw in all_keywords if kw.lower() in text)
        
        experts.sort(key=score_expert, reverse=True)
        
        seen_ids = set()
        expert_ids = []
        for expert in experts:
            if expert.agent_id not in seen_ids:
                seen_ids.add(expert.agent_id)
                expert_ids.append(expert.agent_id)
                if len(expert_ids) >= 5:
                    break
        
        return expert_ids
    
    def _exclude_experts(self, recommended: List[str], types: List[RequirementType]) -> List[str]:
        """排除不相关专家"""
        if RequirementType.ARCHITECTURE not in types and RequirementType.PRODUCT not in types:
            return []
        
        testing_keywords = ["test", "qa", "testing"]
        excluded = []
        
        from requirement_analyzer import expert_pool
        pool = expert_pool
        pool.initialize()
        
        for expert_id in recommended:
            expert = pool.get_agent(expert_id)
            if expert:
                if any(kw in expert.agent_id.lower() or kw in expert.name.lower() for kw in testing_keywords):
                    excluded.append(expert_id)
        
        return excluded
    
    def _identify_key_topics(self, topic: str, types: List[RequirementType]) -> List[Dict]:
        """识别关键议题"""
        key_topics = []
        
        questions = {
            RequirementType.PRODUCT: ["目标用户是谁？", "核心痛点是什么？"],
            RequirementType.ARCHITECTURE: ["技术选型理由？", "扩展性如何保证？"],
            RequirementType.SECURITY: ["有哪些安全风险？", "如何保护用户隐私？"],
            RequirementType.UX_DESIGN: ["用户操作流程是否顺畅？", "界面是否直观？"],
            RequirementType.AI_ML: ["AI 功能的核心价值？", "模型准确率如何保证？"],
            RequirementType.PERFORMANCE: ["性能指标是多少？", "瓶颈在哪里？"],
            RequirementType.BUSINESS: ["商业模式是什么？", "目标市场规模？"],
            RequirementType.DATA: ["数据模型设计？", "查询性能如何？"],
        }
        
        for req_type in types:
            key_topics.append({
                "name": req_type.value.replace("_", " ").title(),
                "type": req_type.value,
                "priority": "high" if req_type in types[:2] else "medium",
                "focus_questions": questions.get(req_type, [])
            })
        
        key_topics.sort(key=lambda x: (0 if x["priority"] == "high" else 1))
        return key_topics


class ExpertSelector:
    """专家选择器"""
    
    def __init__(self):
        from requirement_analyzer import expert_pool
        self.pool = expert_pool
        self.pool.initialize()
    
    def select_experts(self, requirement: AnalyzedRequirement) -> List[AgentProfile]:
        """选择专家"""
        selected = []
        for agent_id in requirement.recommended_experts:
            if agent_id not in requirement.excluded_experts:
                agent = self.pool.get_agent(agent_id)
                if agent:
                    selected.append(agent)
        return selected
    
    def get_expert_prompt(self, expert_id: str, topic: str, focus: Dict) -> str:
        """生成专家提示词"""
        return self.pool.get_expert_prompt(expert_id, topic, focus)


class ExpertPool:
    """专家池"""
    
    _instance = None
    _loader = None
    _agents = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self):
        if self._loader is None:
            self._loader = AgencyAgentsLoader()
            self._agents = self._loader.load_all()
    
    def get_all_agents(self) -> Dict[str, AgentProfile]:
        return self._agents if self._agents else {}
    
    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        self.initialize()
        return self._agents.get(agent_id)
    
    def get_agents_by_category(self, category: str) -> List[AgentProfile]:
        self.initialize()
        return self._loader.get_agents_by_category(category)
    
    def get_agents_by_keywords(self, keywords: List[str]) -> List[AgentProfile]:
        self.initialize()
        return self._loader.get_agents_by_keywords(keywords)
    
    def get_expert_prompt(self, agent_id: str, topic: str, focus: Dict) -> str:
        self.initialize()
        return self._loader.get_expert_prompt(agent_id, topic, focus)
    
    def list_all_agents(self) -> str:
        self.initialize()
        return self._loader.list_all_agents()


expert_pool = ExpertPool()


def select_experts_for_topic(topic: str) -> List[str]:
    """快捷函数：选择专家"""
    analyzer = RequirementAnalyzer()
    selector = ExpertSelector()
    requirement = analyzer.analyze(topic)
    experts = selector.select_experts(requirement)
    return [e.agent_id for e in experts]


def get_expert_prompt(expert_id: str, topic: str, focus: Dict = None) -> str:
    """快捷函数：获取专家提示词"""
    selector = ExpertSelector()
    return selector.get_expert_prompt(expert_id, topic, focus or {})


def list_all_146_agents() -> str:
    """快捷函数：列出所有专家"""
    return expert_pool.list_all_agents()


if __name__ == "__main__":
    analyzer = RequirementAnalyzer()
    topic = "智能待办应用的架构设计"
    
    print(f"\n📋 分析需求：{topic}\n")
    requirement = analyzer.analyze(topic)
    
    print(f"检测类型：{[t.value for t in requirement.detected_types]}")
    print(f"推荐专家：{requirement.recommended_experts[:5]}")
    
    for expert_id in requirement.recommended_experts[:3]:
        agent = expert_pool.get_agent(expert_id)
        if agent:
            print(f"  - {agent.name} ({agent.category})")
    
    print(f"\n✅ 完成！")
