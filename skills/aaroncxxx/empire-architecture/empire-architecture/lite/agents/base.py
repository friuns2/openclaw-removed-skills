"""帝国架构 - Agent 基类"""
import asyncio
import json
import time
import uuid
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional
from core.bus import MessageBus, Message, MessageType
from core.tokens import TokenTracker
from core.config import load_llm_credentials, load_empire_config


@dataclass
class AgentState:
    agent_id: str
    name: str
    role: str
    status: str = "idle"       # idle, busy, error, terminated
    current_task: str = ""
    tasks_completed: int = 0
    uptime_start: float = field(default_factory=time.time)


class Agent:
    """Agent 基类"""

    def __init__(self, agent_id: str, name: str, role: str,
                 system_prompt: str, bus: MessageBus, tracker: TokenTracker):
        self.state = AgentState(agent_id=agent_id, name=name, role=role)
        self.system_prompt = system_prompt
        self.bus = bus
        self.tracker = tracker
        self.bus.register(agent_id)
        self._credentials = None
        self._config = None

    def _get_credentials(self):
        if self._credentials is None:
            self._credentials = load_llm_credentials()
            self._config = load_empire_config()
        return self._credentials, self._config

    async def call_llm(self, prompt: str, context: str = "") -> str:
        """调用 LLM"""
        creds, cfg = self._get_credentials()
        if not creds:
            return "[ERROR] 无可用的 LLM 凭据"

        # 检查 token 预算
        if not self.tracker.check_budget(self.state.agent_id):
            return "[ERROR] Token 额度已用完"

        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.append({"role": "user", "content": f"背景信息：\n{context}"})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": cfg["llm"]["model"],
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.7,
        }).encode()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {creds['api_key']}",
        }

        url = creds['base_url']
        # 如果 base_url 已经包含完整路径，直接用；否则拼接
        if not url.endswith("/chat/completions"):
            url = url.rstrip("/") + "/chat/completions"

        try:
            req = urllib.request.Request(url, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=cfg["llm"]["timeout_seconds"]) as resp:
                data = json.loads(resp.read())

            # 提取 token 使用
            usage = data.get("usage", {})
            self.tracker.log_usage(
                self.state.agent_id,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
                model=cfg["llm"]["model"],
            )

            content = data["choices"][0]["message"]["content"]
            self.state.tasks_completed += 1
            return content

        except urllib.error.HTTPError as e:
            return f"[ERROR] API 调用失败: {e.code} {e.reason}"
        except Exception as e:
            return f"[ERROR] {str(e)}"

    async def process_task(self, task_id: str, prompt: str, context: str = "") -> str:
        """处理任务"""
        self.state.status = "busy"
        self.state.current_task = task_id
        try:
            result = await self.call_llm(prompt, context)
            self.state.status = "idle"
            self.state.current_task = ""
            return result
        except Exception as e:
            self.state.status = "error"
            return f"[ERROR] {self.state.name} 处理失败: {e}"

    def get_status(self) -> dict:
        return {
            "id": self.state.agent_id,
            "name": self.state.name,
            "role": self.state.role,
            "status": self.state.status,
            "current_task": self.state.current_task,
            "tasks_completed": self.state.tasks_completed,
            "uptime": round(time.time() - self.state.uptime_start, 0),
        }
