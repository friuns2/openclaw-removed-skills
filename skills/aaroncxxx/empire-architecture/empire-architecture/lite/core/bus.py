"""帝国架构 - 消息总线"""
import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


class MessageType(Enum):
    COMMAND = "command"        # 皇帝→丞相 指令
    TASK = "task"              # 丞相→执行层 任务
    RESULT = "result"          # 执行层→丞相 结果
    REPORT = "report"          # 丞相→皇帝 汇报
    ALERT = "alert"            # 锦衣卫→皇帝 告警
    VOTE = "vote"              # 锦衣卫投票
    SYNC = "sync"              # 节点间同步
    HEARTBEAT = "heartbeat"    # 心跳


@dataclass
class Message:
    msg_type: MessageType
    sender: str
    receiver: str
    content: str
    task_id: Optional[str] = None
    priority: int = 5          # 1最高，10最低
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d["msg_type"] = self.msg_type.value
        return d

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False)


class MessageBus:
    """异步消息总线 - 节点间通信"""

    def __init__(self):
        self.queues: dict[str, asyncio.PriorityQueue] = {}
        self.history: list[Message] = []
        self._subscribers: dict[str, list] = {}

    def register(self, agent_id: str):
        if agent_id not in self.queues:
            self.queues[agent_id] = asyncio.PriorityQueue()

    async def send(self, msg: Message):
        """发送消息"""
        self.history.append(msg)
        if msg.receiver in self.queues:
            # 用 priority 排序
            await self.queues[msg.receiver].put((msg.priority, msg.timestamp, msg))
        # 广播给订阅者
        for sub_id in self._subscribers.get(msg.msg_type.value, []):
            if sub_id in self.queues and sub_id != msg.receiver:
                await self.queues[sub_id].put((msg.priority, msg.timestamp, msg))

    async def receive(self, agent_id: str, timeout: float = 30) -> Optional[Message]:
        """接收消息"""
        if agent_id not in self.queues:
            return None
        try:
            _, _, msg = await asyncio.wait_for(
                self.queues[agent_id].get(), timeout=timeout
            )
            return msg
        except asyncio.TimeoutError:
            return None

    def subscribe(self, agent_id: str, msg_type: str):
        """订阅特定类型消息"""
        self._subscribers.setdefault(msg_type, []).append(agent_id)

    def get_history(self, limit: int = 50) -> list[Message]:
        return self.history[-limit:]
