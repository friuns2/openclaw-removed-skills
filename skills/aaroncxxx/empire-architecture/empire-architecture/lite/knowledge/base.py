"""知识库基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KnowledgeResult:
    """知识检索结果"""
    title: str
    content: str
    source: str           # 来源标识：tencent / feishu / notion
    score: float = 0.0    # 相关度 0~1
    metadata: dict = field(default_factory=dict)


class KnowledgeProvider(ABC):
    """知识库提供者基类"""

    name: str = "base"

    @abstractmethod
    async def search(self, query: str, top_k: int = 3) -> list[KnowledgeResult]:
        """检索知识库"""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """检查连接是否正常"""
        ...
