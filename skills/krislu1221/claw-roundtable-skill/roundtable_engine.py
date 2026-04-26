#!/usr/bin/env python3
"""
RoundTable Engine - 多 Agent 深度讨论引擎
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from agent_selector import AgentSelector, select_roundtable_agents
from model_selector import ModelSelector
from roundtable_notifier import RoundTableNotifier


@dataclass
class AgentResult:
    """Agent 执行结果"""
    agent_id: str
    content: str
    elapsed_seconds: float
    success: bool


class RoundState(Enum):
    """RoundTable 状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RoundConfig:
    """轮次配置"""
    name: str
    description: str


class RoundTableEngine:
    """RoundTable 讨论引擎"""
    
    ROUNDS = {
        "R1": RoundConfig("独立方案", "每个 Agent 独立提出方案"),
        "R2": RoundConfig("相互引用", "引用其他 Agent 观点并批判性思考"),
        "R3": RoundConfig("方案优化", "基于讨论优化各自方案"),
        "R4": RoundConfig("共识形成", "形成共识方案"),
        "R5": RoundConfig("最终总结", "总结讨论成果"),
    }
    
    def __init__(
        self,
        topic: str,
        mode: str = "技术方案",
        agent_source: str = "",
        agents: Optional[List[str]] = None,
        primary_model: str = None,
    ):
        """
        初始化 RoundTable 引擎
        
        Args:
            topic: 讨论主题
            mode: 模式（pre-ac: AC 前讨论，post-ac: AC 后审查）
            agent_source: Agent 来源路径
            agents: 指定 Agent 列表（可选）
            primary_model: 主模型 ID（可选）
        """
        self.topic = topic
        self.mode = mode
        self.agent_source = agent_source
        
        # Agent 选择器
        self.agent_selector = AgentSelector(agent_source)
        
        # 模型选择器
        self.model_selector = ModelSelector(primary_model=primary_model)
        
        # 自动选择或指定 Agent
        if agents:
            self.agents = agents
        else:
            self.agents = self.agent_selector.select_agents_for_roundtable(topic)
        
        # 为每个 Agent 分配模型
        self.agent_model_mapping = {}
        for agent_id in self.agents:
            if "engineering" in agent_id:
                role = "engineering"
            elif "design" in agent_id:
                role = "design"
            elif "testing" in agent_id:
                role = "testing"
            else:
                role = "product"
            
            model_id = self.model_selector.select_model_for_role(role)
            self.agent_model_mapping[agent_id] = model_id
        
        self.state = RoundState.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.current_round: str = ""
        self.results: Dict[str, List[AgentResult]] = {}
        self.notifier = RoundTableNotifier(topic, mode)
    
    async def run(self, user_channel: str) -> bool:
        """运行完整 RoundTable 流程"""
        print(f"\n🔄 RoundTable 启动：{self.topic}")
        print("="*60)
        
        # 1. 用户确认
        confirmed = await self.notifier.send_confirmation_request(user_channel)
        if not confirmed:
            print("❌ 用户取消 RoundTable")
            return False
        
        # 2. 询问模型配置
        print("\n🎯 步骤 2: 模型配置")
        print("-"*60)
        model_input = await self.notifier.ask_model_config(user_channel)
        
        if model_input and model_input.strip():
            success = self.model_selector.configure_models(model_input.strip())
            if success:
                print(f"✅ 模型配置成功：{self.model_selector.get_model_config_summary()}")
                
                # 重新分配模型
                self.agent_model_mapping = {}
                for agent_id in self.agents:
                    if "engineering" in agent_id:
                        role = "engineering"
                    elif "design" in agent_id:
                        role = "design"
                    elif "testing" in agent_id:
                        role = "testing"
                    else:
                        role = "product"
                    
                    model_id = self.model_selector.select_model_for_role(role)
                    self.agent_model_mapping[agent_id] = model_id
            else:
                print("⚠️ 模型配置失败，使用默认设置")
        else:
            print("⏭️ 跳过模型配置，使用默认设置")
        
        self.state = RoundState.RUNNING
        self.start_time = datetime.now()
        
        # 3. 发送开始通知
        await self.notifier.send_start_notification(user_channel)
        
        # 4. 执行 5 轮讨论
        for round_name, config in self.ROUNDS.items():
            self.current_round = round_name
            print(f"\n{'='*60}")
            print(f"📍 {round_name}: {config.name}（{config.description}）")
            print(f"{'='*60}")
            
            round_results = await self.execute_round(round_name, config)
            self.results[round_name] = round_results
        
        # 5. 完成
        self.state = RoundState.COMPLETED
        self.end_time = datetime.now()
        
        await self.notifier.send_completion_notification(user_channel, self.results)
        
        print(f"\n✅ RoundTable 完成！")
        return True
    
    async def execute_round(self, round_name: str, config: RoundConfig) -> List[AgentResult]:
        """执行单轮讨论"""
        agents = self.agents
        tasks = []
        
        for agent_id in agents:
            task = self._generate_discussion_prompt(agent_id, round_name, [])
            tasks.append(self.execute_agent(agent_id, task, 300))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        agent_results = []
        for i, result in enumerate(results):
            agent_id = agents[i]
            if isinstance(result, Exception):
                agent_results.append(AgentResult(
                    agent_id=agent_id,
                    content="",
                    elapsed_seconds=0,
                    success=False
                ))
                print(f"  ❌ {agent_id}: 执行失败 - {result}")
            else:
                agent_results.append(result)
                print(f"  ✅ {agent_id}: {result.elapsed_seconds:.1f}秒")
        
        return agent_results
    
    async def execute_agent(self, agent_id: str, task: str, timeout: int, max_retries: int = 2) -> AgentResult:
        """执行单个 Agent"""
        start_time = datetime.now()
        
        for attempt in range(max_retries + 1):
            try:
                from openclaw.tools import sessions_spawn
                
                model_id = self.agent_model_mapping.get(agent_id)
                
                print(f"    🚀 创建子 Agent: {agent_id}")
                if model_id:
                    print(f"    🎯 使用模型：{model_id}")
                else:
                    print(f"    🎯 使用 OpenClaw 默认模型")
                
                spawn_kwargs = {
                    'task': task,
                    'runtime': 'subagent',
                    'mode': 'run',
                    'label': f"rt-{self.topic[:15]}-{agent_id.split('/')[-1]}-{self.current_round}",
                    'timeoutSeconds': timeout,
                    'thinking': 'on'
                }
                
                if model_id:
                    spawn_kwargs['model'] = model_id
                
                session_result = await sessions_spawn(**spawn_kwargs)
                
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if hasattr(session_result, 'result') and session_result.result:
                    content = session_result.result
                elif isinstance(session_result, dict) and 'output' in session_result:
                    content = session_result['output']
                else:
                    content = f"[{agent_id}] 已完成 {self.current_round} 讨论"
                
                print(f"    ✅ {agent_id} 完成，耗时 {elapsed:.1f}秒")
                
                return AgentResult(
                    agent_id=agent_id,
                    content=content,
                    elapsed_seconds=elapsed,
                    success=True
                )
                
            except Exception as e:
                print(f"    ⚠️ {agent_id} 执行失败（尝试 {attempt+1}/{max_retries}）: {e}")
                if attempt == max_retries:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    return AgentResult(
                        agent_id=agent_id,
                        content=f"执行失败：{e}",
                        elapsed_seconds=elapsed,
                        success=False
                    )
    
    def _generate_discussion_prompt(self, agent_id: str, round_name: str, context: List) -> str:
        """生成讨论提示词"""
        # 加载完整 Agent Prompt
        try:
            agent_prompt = self.agent_selector.load_agent_prompt(agent_id)
            role_desc = agent_prompt[:2000]
            print(f"    📋 已加载 Agent Prompt: {agent_id} ({len(agent_prompt)} 字符)")
        except Exception as e:
            if 'engineering' in agent_id:
                role_desc = "你是一位资深工程专家，拥有 10 年以上全栈开发经验。你擅长架构设计、技术选型和风险评估。"
            elif 'design' in agent_id:
                role_desc = "你是一位资深 UX/UI 设计师，专注于用户体验和界面设计。你擅长从用户角度思考问题。"
            elif 'testing' in agent_id:
                role_desc = "你是一位资深 QA 工程师，专注于测试策略和质量保障。你擅长发现潜在问题和风险。"
            else:
                role_desc = "你是一位专业顾问，从你的专业角度提供深度分析。"
            print(f"    ⚠️ 使用降级角色描述：{agent_id}")
        
        base_prompt = f"""# RoundTable 多 Agent 深度讨论

## 你的角色
{role_desc}

## 讨论主题
**{self.topic}**

## 讨论模式
{self.mode}

## 当前轮次
{round_name}

---

## ⚠️ 重要要求

1. **深度思考**：不要泛泛而谈，必须提供具体的技术细节、数据支持或案例说明
2. **批判性思维**：敢于质疑，识别方案中的漏洞和风险，不要一味附和
3. **结构化输出**：使用 Markdown 格式，包含标题、表格、列表、代码块等
4. **完整思路**：展示你的分析过程，而不仅仅是结论
5. **长度要求**：至少 800 字，确保内容充实

---

"""
        
        if round_name == "R1":
            prompt = base_prompt + f"""## 📋 你的任务（R1：独立方案）

请从你的专业角度，对主题进行**独立、深度**的分析。

### 必须包含的内容

1. **需求理解**（200 字以上）
   - 你如何理解这个需求？
   - 核心痛点是什么？
   - 目标用户是谁？

2. **专业分析**（400 字以上）
   - 从你的专业角度，详细阐述技术方案/设计方案/测试方案
   - 提供具体的技术选型、设计原则或测试策略
   - **必须包含表格对比**不同方案的优劣

3. **实施建议**（200 字以上）
   - 分阶段实施计划
   - 工时评估（人天）
   - 关键里程碑

请开始你的深度分析：
"""
        else:
            prompt = base_prompt + f"""## 📋 你的任务（{round_name}）

请根据当前轮次的要求，从你的专业角度提供深度分析。

请开始：
"""
        
        return prompt
    
    def _generate_markdown_report(self, report: Dict) -> str:
        """生成 Markdown 报告"""
        md = f"# RoundTable 讨论报告\n\n**主题**: {self.topic}\n\n"
        
        for round_name, results in report.items():
            md += f"\n## {round_name}\n\n"
            for result in results:
                md += f"\n### {result.agent_id}\n\n{result.content}\n\n"
        
        return md


async def run_roundtable(topic: str, mode: str = "pre-ac", user_channel: str = "",
                        agent_source: str = "", agents: Optional[List[str]] = None,
                        primary_model: str = None) -> bool:
    """RoundTable 快捷入口"""
    engine = RoundTableEngine(topic, mode, agent_source, agents, primary_model)
    return await engine.run(user_channel)
