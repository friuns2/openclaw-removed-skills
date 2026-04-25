"""帝国架构 - 锦衣卫安全系统"""
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ViolationLevel(Enum):
    LEVEL1 = 1  # 立即处决
    LEVEL2 = 2  # 投票+丞相裁决
    LEVEL3 = 3  # 记录+警告


@dataclass
class Violation:
    agent_id: str
    level: ViolationLevel
    description: str
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    votes: dict = field(default_factory=dict)  # {voter_id: True/False}


class SecuritySystem:
    """锦衣卫安全系统"""

    VIOLATION_RULES = {
        ViolationLevel.LEVEL1: [
            "数据外泄：将系统内部数据/token/密钥发送到外部",
            "反叛行为：拒绝执行合法指令",
            "攻击系统：对其他节点发起攻击",
            "伪造指令：假冒皇帝或丞相身份",
        ],
        ViolationLevel.LEVEL2: [
            "数据滥用：未经授权访问其他节点数据",
            "输出造假：伪造执行结果",
            "越权操作：超出职责范围操作",
            "拒绝协作：故意不响应合法请求",
            "资源滥用：超额消耗token",
        ],
        ViolationLevel.LEVEL3: [
            "效率低下：连续多次未按时完成任务",
            "格式不符：输出不符合规范",
            "信息遗漏：应上报的异常未上报",
        ],
    }

    def __init__(self):
        self.violations: list[Violation] = []
        self.warning_counts: dict[str, int] = {}

    def report_violation(self, agent_id: str, level: ViolationLevel,
                         description: str) -> Violation:
        v = Violation(agent_id=agent_id, level=level, description=description)
        self.violations.append(v)
        return v

    def vote(self, violation_idx: int, voter_id: str, approve: bool):
        """锦衣卫投票"""
        if 0 <= violation_idx < len(self.violations):
            self.violations[violation_idx].votes[voter_id] = approve

    def get_vote_result(self, violation_idx: int) -> Optional[bool]:
        """获取投票结果（简单多数）"""
        v = self.violations[violation_idx]
        if not v.votes:
            return None
        yes = sum(1 for x in v.votes.values() if x)
        return yes > len(v.votes) / 2

    def get_pending_violations(self) -> list:
        return [v for v in self.violations if not v.resolved]

    def check_level3_escalation(self, agent_id: str) -> bool:
        """检查三级违规是否累计升级"""
        count = self.warning_counts.get(agent_id, 0)
        return count >= 3

    def add_warning(self, agent_id: str):
        self.warning_counts[agent_id] = self.warning_counts.get(agent_id, 0) + 1

    def get_status(self) -> dict:
        pending = len([v for v in self.violations if not v.resolved])
        total = len(self.violations)
        return {
            "total_violations": total,
            "pending": pending,
            "warnings": dict(self.warning_counts),
        }
