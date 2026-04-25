"""
帝国架构 - 翰林院（知识管理层）
Hanlin Academy - Knowledge Management Layer

祭酒 x1：翰林院总管，统筹所有知识库
大学士 x3：各管一路知识源
  - 腾讯云大学士
  - 飞书大学士
  - Notion / 本地 RAG 大学士
"""

import time
from dataclasses import dataclass, field


@dataclass
class ScholarState:
    """大学士状态"""
    scholar_id: str
    name: str
    knowledge_source: str
    status: str = "idle"       # idle / busy / error
    docs_indexed: int = 0
    queries_served: int = 0
    last_active: float = field(default_factory=time.time)


class HanlinScholar:
    """翰林院大学士 - 知识库管理者"""

    def __init__(self, scholar_id: str, name: str, knowledge_source: str):
        self.state = ScholarState(
            scholar_id=scholar_id,
            name=name,
            knowledge_source=knowledge_source,
        )

    async def index(self, provider, **kwargs) -> dict:
        """索引知识（调用 provider 的 ingest 方法）"""
        self.state.status = "busy"
        self.state.last_active = time.time()
        try:
            if hasattr(provider, 'ingest_url'):
                doc_id = provider.ingest_url(kwargs.get('url', ''))
            elif hasattr(provider, 'ingest_file'):
                doc_id = provider.ingest_file(kwargs.get('file_path', ''))
            elif hasattr(provider, 'ingest_text'):
                doc_id = provider.ingest_text(
                    kwargs.get('title', ''),
                    kwargs.get('content', ''),
                )
            else:
                doc_id = None
            self.state.docs_indexed += 1
            self.state.status = "idle"
            return {"status": "ok", "doc_id": doc_id}
        except Exception as e:
            self.state.status = "error"
            return {"status": "error", "error": str(e)}

    async def query(self, provider, query: str, top_k: int = 3) -> list:
        """检索知识"""
        self.state.status = "busy"
        self.state.last_active = time.time()
        try:
            results = await provider.search(query, top_k)
            self.state.queries_served += 1
            self.state.status = "idle"
            return results
        except Exception as e:
            self.state.status = "error"
            return []

    def get_status(self) -> dict:
        return {
            "id": self.state.scholar_id,
            "name": self.state.name,
            "source": self.state.knowledge_source,
            "status": self.state.status,
            "docs_indexed": self.state.docs_indexed,
            "queries_served": self.state.queries_served,
        }


class HanlinDirector:
    """翰林院祭酒 - 知识管理总管"""

    def __init__(self):
        self.scholars: dict[str, HanlinScholar] = {}
        self.providers = {}  # reference to KnowledgeRouter providers

    def register_scholar(self, scholar: HanlinScholar, provider=None):
        """注册大学士"""
        self.scholars[scholar.state.scholar_id] = scholar
        if provider:
            self.providers[scholar.state.scholar_id] = provider

    async def unified_search(self, query: str, top_k: int = 3,
                             sources: list[str] = None) -> list:
        """祭酒统一调度检索 - 跨所有知识源"""
        from .base import KnowledgeResult

        targets = sources or list(self.providers.keys())
        all_results = []

        for scholar_id in targets:
            if scholar_id in self.scholars and scholar_id in self.providers:
                scholar = self.scholars[scholar_id]
                provider = self.providers[scholar_id]
                results = await scholar.query(provider, query, top_k)
                all_results.extend(results)

        # 去重 + 按分数排序
        seen = set()
        unique = []
        for r in all_results:
            key = hash(r.title + r.content[:100])
            if key not in seen:
                seen.add(key)
                unique.append(r)
        unique.sort(key=lambda x: x.score, reverse=True)
        return unique[:top_k]

    async def unified_index(self, scholar_id: str, **kwargs) -> dict:
        """祭酒统一调度索引"""
        if scholar_id not in self.scholars:
            return {"status": "error", "error": f"未知大学士: {scholar_id}"}
        scholar = self.scholars[scholar_id]
        provider = self.providers.get(scholar_id)
        if not provider:
            return {"status": "error", "error": f"未挂载知识源: {scholar_id}"}
        return await scholar.index(provider, **kwargs)

    def get_status(self) -> dict:
        return {
            "director": "翰林院祭酒",
            "scholars": {sid: s.get_status()
                         for sid, s in self.scholars.items()},
            "total_docs": sum(s.state.docs_indexed for s in self.scholars.values()),
            "total_queries": sum(s.state.queries_served for s in self.scholars.values()),
        }
