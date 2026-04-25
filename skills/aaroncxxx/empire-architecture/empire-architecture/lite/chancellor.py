"""帝国架构 - 丞相协调器"""
import asyncio
import uuid
import time
from core.bus import MessageBus, Message, MessageType
from core.tokens import TokenTracker
from core.security import SecuritySystem, ViolationLevel
from agents.base import Agent
from core.config import load_empire_config


class Chancellor:
    """丞相 - 总协调器"""

    def __init__(self):
        self.config = load_empire_config()
        self.bus = MessageBus()
        self.tracker = TokenTracker()
        self.security = SecuritySystem()
        self.agents: dict[str, Agent] = {}
        self._init_agents()

    def _init_agents(self):
        """初始化所有24个节点"""
        cfg = self.config["agents"]

        # 丞相
        c = cfg["chancellor"]
        self.agents["chancellor"] = Agent(
            "chancellor", c["name"], c["role"], c["system_prompt"],
            self.bus, self.tracker,
        )

        # 参谋 (3)
        for a in cfg.get("advisors", []):
            self.agents[a["id"]] = Agent(
                a["id"], a["name"], a["role"], a["system_prompt"],
                self.bus, self.tracker,
            )

        # 执行层 (3)
        for a in cfg.get("executors", []):
            self.agents[a["id"]] = Agent(
                a["id"], a["name"], a["role"], a["system_prompt"],
                self.bus, self.tracker,
            )

        # 六部 (6)
        for a in cfg.get("ministries", []):
            self.agents[a["id"]] = Agent(
                a["id"], a["name"], a["role"], a["system_prompt"],
                self.bus, self.tracker,
            )

        # 翰林院 (2)
        for a in cfg.get("scholars", []):
            self.agents[a["id"]] = Agent(
                a["id"], a["name"], a["role"], a["system_prompt"],
                self.bus, self.tracker,
            )

        # 特殊职能 (3)
        for a in cfg.get("special", []):
            self.agents[a["id"]] = Agent(
                a["id"], a["name"], a["role"], a["system_prompt"],
                self.bus, self.tracker,
            )

        # 监察 (2)
        for a in cfg.get("overseers", []):
            self.agents[a["id"]] = Agent(
                a["id"], a["name"], a["role"], a["system_prompt"],
                self.bus, self.tracker,
            )

        # 扩展 (3)
        for a in cfg.get("extra", []):
            self.agents[a["id"]] = Agent(
                a["id"], a["name"], a["role"], a["system_prompt"],
                self.bus, self.tracker,
            )

        # 锦衣卫
        s = cfg["security"]
        self.agents[s["id"]] = Agent(
            s["id"], s["name"], s["role"], s["system_prompt"],
            self.bus, self.tracker,
        )

    async def receive_command(self, command: str) -> dict:
        """接收皇帝指令并编排执行"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        start = time.time()

        # Step 1: 丞相分析指令，决定需要哪些节点
        plan = await self._plan(task_id, command)

        # Step 2: 并行执行
        results = await self._execute_plan(task_id, command, plan)

        # Step 3: 锦衣卫审计
        audit = await self._audit(task_id, command, results)

        elapsed = round(time.time() - start, 1)

        return {
            "task_id": task_id,
            "command": command,
            "plan": plan,
            "results": results,
            "audit": audit,
            "elapsed_seconds": elapsed,
            "tokens_used": self.tracker.get_total_today(),
        }

    async def _plan(self, task_id: str, command: str) -> dict:
        """丞相规划任务 - 24节点调度"""
        chancellor = self.agents["chancellor"]

        # 构建所有可用节点列表
        agent_list = []
        for aid, agent in self.agents.items():
            if aid == "chancellor":
                continue
            agent_list.append(f"- {agent.state.name} ({aid})：{agent.state.role}")

        agents_text = "\n".join(agent_list)

        plan_prompt = f"""皇帝下达指令：{command}

可用节点（共{len(self.agents)}个）：
{agents_text}

请根据任务需求，选择最合适的节点组合。返回 JSON 格式：
1. tasks: 列表，每个任务包含 agent_id, prompt, priority
2. parallel: 是否并行执行

只返回 JSON，不要其他内容。"""

        result = await chancellor.call_llm(plan_prompt)

        # 解析 JSON
        try:
            import json
            if "```" in result:
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            plan = json.loads(result.strip())
        except Exception:
            # 默认方案：参谋+六部并行分析
            plan = {
                "tasks": [
                    {"agent_id": "advisor_strategy", "prompt": f"战略分析：{command}", "priority": 3},
                    {"agent_id": "advisor_tech", "prompt": f"技术评估：{command}", "priority": 3},
                    {"agent_id": "advisor_intel", "prompt": f"情报收集：{command}", "priority": 3},
                    {"agent_id": "minister_personnel", "prompt": f"人员配置分析：{command}", "priority": 2},
                    {"agent_id": "minister_finance", "prompt": f"资源成本分析：{command}", "priority": 2},
                ],
                "parallel": True,
            }

        return plan

    async def _execute_plan(self, task_id: str, command: str, plan: dict) -> dict:
        """执行计划"""
        results = {}
        tasks = plan.get("tasks", [])

        if plan.get("parallel", True):
            # 并行执行
            async def run_task(t):
                agent_id = t.get("agent_id", "")
                if agent_id in self.agents:
                    prompt = t.get("prompt", command)
                    r = await self.agents[agent_id].process_task(task_id, prompt)
                    return agent_id, r
                return agent_id, f"[ERROR] 未知节点: {agent_id}"

            coros = [run_task(t) for t in tasks]
            done = await asyncio.gather(*coros, return_exceptions=True)
            for item in done:
                if isinstance(item, Exception):
                    results["error"] = str(item)
                else:
                    results[item[0]] = item[1]
        else:
            # 串行执行
            for t in tasks:
                agent_id = t.get("agent_id", "")
                if agent_id in self.agents:
                    prompt = t.get("prompt", command)
                    r = await self.agents[agent_id].process_task(task_id, prompt)
                    results[agent_id] = r

        # 丞相汇总
        summary_prompt = f"""皇帝指令：{command}

各节点执行结果：
"""
        for aid, r in results.items():
            name = self.agents[aid].state.name if aid in self.agents else aid
            summary_prompt += f"\n【{name}】\n{r}\n"

        summary_prompt += "\n请汇总以上结果，给皇帝一份简洁的汇报。"

        summary = await self.agents["chancellor"].call_llm(summary_prompt)
        results["chancellor_summary"] = summary

        return results

    async def _audit(self, task_id: str, command: str, results: dict) -> dict:
        """锦衣卫审计"""
        jw = self.agents["jinyiwei"]
        audit_prompt = f"""安全审计：
皇帝指令：{command}
执行结果摘要：{str(results)[:2000]}

请检查：
1. 是否有数据外泄风险
2. 输出是否包含敏感信息
3. 是否有越权操作

返回 JSON：{{"safe": true/false, "issues": [], "level": 0}}"""

        audit_result = await jw.call_llm(audit_prompt)

        try:
            import json
            if "```" in audit_result:
                audit_result = audit_result.split("```")[1]
                if audit_result.startswith("json"):
                    audit_result = audit_result[4:]
            audit = json.loads(audit_result.strip())
        except Exception:
            audit = {"safe": True, "issues": ["审计解析失败，默认通过"], "level": 0}

        return audit

    def get_status(self) -> dict:
        """获取帝国状态"""
        return {
            "agents": {aid: a.get_status() for aid, a in self.agents.items()},
            "tokens": self.tracker.get_usage(),
            "security": self.security.get_status(),
            "message_history": len(self.bus.history),
        }
