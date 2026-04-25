"""
知识路由器 - 统一检索多个知识源
Knowledge Router - Search across multiple providers
"""

import asyncio
import time
from .base import KnowledgeProvider, KnowledgeResult


class KnowledgeRouter:
    """多知识源统一路由"""

    def __init__(self):
        self.providers: dict[str, KnowledgeProvider] = {}

    def register(self, provider: KnowledgeProvider):
        """注册知识源"""
        self.providers[provider.name] = provider

    def unregister(self, name: str):
        """移除知识源"""
        self.providers.pop(name, None)

    async def search(self, query: str, top_k: int = 3,
                     sources: list[str] = None) -> list[KnowledgeResult]:
        """
        检索所有（或指定）知识源，合并去重按分数排序
        """
        targets = sources or list(self.providers.keys())
        tasks = []
        for name in targets:
            if name in self.providers:
                tasks.append(self._safe_search(name, query, top_k))

        results_nested = await asyncio.gather(*tasks)
        all_results = []
        for batch in results_nested:
            all_results.extend(batch)

        # 去重（按 title + content）
        seen = set()
        unique = []
        for r in all_results:
            key = hash(r.title + r.content[:100])
            if key not in seen:
                seen.add(key)
                unique.append(r)

        # 按分数降序
        unique.sort(key=lambda x: x.score, reverse=True)
        return unique[:top_k]

    async def search_one(self, source: str, query: str,
                         top_k: int = 3) -> list[KnowledgeResult]:
        """指定单个知识源检索"""
        if source not in self.providers:
            return [KnowledgeResult(
                title="ERROR",
                content=f"未知知识源: {source}",
                source=source,
                score=0.0,
            )]
        return await self._safe_search(source, query, top_k)

    async def _safe_search(self, name: str, query: str,
                           top_k: int) -> list[KnowledgeResult]:
        try:
            return await self.providers[name].search(query, top_k)
        except Exception as e:
            return [KnowledgeResult(
                title="ERROR",
                content=f"{name} 检索异常: {e}",
                source=name,
                score=0.0,
            )]

    async def health_all(self) -> dict[str, bool]:
        """检查所有知识源状态"""
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception:
                results[name] = False
        return results

    def list_sources(self) -> list[str]:
        return list(self.providers.keys())
