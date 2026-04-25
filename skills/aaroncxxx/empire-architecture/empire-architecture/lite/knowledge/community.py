"""
帝国架构 - 社区知识源
Community Knowledge Sources

四大社区挂载：
  1. WaytoAGI — AI 知识库 + 工具导航
  2. DataWhale — 开源学习社区
  3. ModelScope — 阿里模型平台
  4. LiblibAI — AI 绘画模型平台

皇帝批准流程：
  - 默认 disabled，需皇帝提供凭据后启用
  - 未启用时返回 "待皇帝批准" 提示
"""

import json
import urllib.request
import urllib.error
from .base import KnowledgeProvider, KnowledgeResult


# ============================================================
# 社区连接器基类
# ============================================================

class CommunityProvider(KnowledgeProvider):
    """社区知识源基类 - 带皇帝审批流程"""

    def __init__(self):
        self._approved = False
        self._credentials = {}

    def approve(self, **credentials):
        """皇帝批准：提供凭据启用"""
        self._credentials = credentials
        self._approved = True

    def revoke(self):
        """皇帝撤销：禁用此源"""
        self._approved = False
        self._credentials = {}

    async def search(self, query: str, top_k: int = 3) -> list[KnowledgeResult]:
        if not self._approved:
            return [KnowledgeResult(
                title="⏳ 待皇帝批准",
                content=f"{self.name} 尚未启用，需皇帝提供凭据后方可访问。",
                source=self.name,
                score=0.0,
                metadata={"status": "pending_approval"},
            )]
        return await self._search_impl(query, top_k)

    async def _search_impl(self, query: str, top_k: int) -> list[KnowledgeResult]:
        raise NotImplementedError

    async def health_check(self) -> bool:
        return self._approved


# ============================================================
# 1. WaytoAGI — AI 知识库
# ============================================================

class WaytoAGIKnowledge(CommunityProvider):
    """WaytoAGI (通往AGI之路) 连接器"""

    name = "waytoagi"

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.waytoagi.com"

    async def _search_impl(self, query: str, top_k: int) -> list[KnowledgeResult]:
        """
        WaytoAGI 无公开 API，通过网页搜索接口抓取。
        需要皇帝提供：无（免费平台，但需确认允许抓取）
        """
        try:
            # WaytoAGI 使用飞书文档作为后端，搜索接口
            search_url = f"{self.base_url}/api/search?q={query}&limit={top_k}"
            req = urllib.request.Request(search_url, headers={
                "User-Agent": "EmpireBot/1.3",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            results = []
            items = data if isinstance(data, list) else data.get("data", data.get("results", []))
            for item in items[:top_k]:
                results.append(KnowledgeResult(
                    title=item.get("title", "WaytoAGI"),
                    content=item.get("description", item.get("content", ""))[:500],
                    source="waytoagi",
                    score=0.7,
                    metadata={
                        "url": item.get("url", ""),
                        "category": item.get("category", ""),
                    },
                ))
            return results if results else [KnowledgeResult(
                title="WaytoAGI",
                content=f"未找到「{query}」相关结果。建议直接访问 waytoagi.com 搜索。",
                source="waytoagi",
                score=0.3,
            )]
        except Exception as e:
            return [KnowledgeResult(
                title="ERROR",
                content=f"WaytoAGI 检索失败: {e}",
                source="waytoagi",
                score=0.0,
            )]


# ============================================================
# 2. DataWhale — 开源学习社区
# ============================================================

class DataWhaleKnowledge(CommunityProvider):
    """DataWhale 连接器"""

    name = "datawhale"

    def __init__(self):
        super().__init__()
        # DataWhale 开源教程在 GitHub
        self.github_org = "datawhalellm"
        self.github_api = "https://api.github.com"

    async def _search_impl(self, query: str, top_k: int) -> list[KnowledgeResult]:
        """
        DataWhale 教程主要在 GitHub 开源。
        需要皇帝提供：GitHub Token（可选，提高 rate limit）
        """
        try:
            token = self._credentials.get("github_token", "")
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "EmpireBot/1.3",
            }
            if token:
                headers["Authorization"] = f"token {token}"

            # 搜索 DataWhale 组织下的仓库
            url = f"{self.github_api}/search/repositories?q={query}+org:datawhalellm&per_page={top_k}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            results = []
            for repo in data.get("items", [])[:top_k]:
                results.append(KnowledgeResult(
                    title=repo.get("full_name", ""),
                    content=repo.get("description", "") or "无描述",
                    source="datawhale",
                    score=0.7,
                    metadata={
                        "url": repo.get("html_url", ""),
                        "stars": repo.get("stargazers_count", 0),
                        "language": repo.get("language", ""),
                    },
                ))
            return results if results else [KnowledgeResult(
                title="DataWhale",
                content=f"未找到「{query}」相关教程。建议访问 github.com/datawhalellm 浏览。",
                source="datawhale",
                score=0.3,
            )]
        except Exception as e:
            return [KnowledgeResult(
                title="ERROR",
                content=f"DataWhale 检索失败: {e}",
                source="datawhale",
                score=0.0,
            )]


# ============================================================
# 3. ModelScope — 阿里模型平台
# ============================================================

class ModelScopeKnowledge(CommunityProvider):
    """ModelScope (魔搭) 连接器"""

    name = "modelscope"

    def __init__(self):
        super().__init__()
        self.api_base = "https://api.modelscope.cn"

    async def _search_impl(self, query: str, top_k: int) -> list[KnowledgeResult]:
        """
        ModelScope 模型搜索 API。
        需要皇帝提供：ModelScope Token
        """
        try:
            token = self._credentials.get("token", "")
            headers = {
                "Accept": "application/json",
                "User-Agent": "EmpireBot/1.3",
            }
            if token:
                headers["Authorization"] = f"Bearer {token}"

            # 搜索模型
            url = f"{self.api_base}/api/v1/models?query={query}&PageSize={top_k}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            results = []
            models = data.get("Data", {}).get("Models", [])
            for m in models[:top_k]:
                results.append(KnowledgeResult(
                    title=m.get("Name", ""),
                    content=m.get("Description", "")[:500] or "无描述",
                    source="modelscope",
                    score=0.7,
                    metadata={
                        "model_id": m.get("ModelId", ""),
                        "downloads": m.get("Downloads", 0),
                        "framework": m.get("Framework", ""),
                    },
                ))
            return results if results else [KnowledgeResult(
                title="ModelScope",
                content=f"未找到「{query}」相关模型。建议访问 modelscope.cn 搜索。",
                source="modelscope",
                score=0.3,
            )]
        except Exception as e:
            return [KnowledgeResult(
                title="ERROR",
                content=f"ModelScope 检索失败: {e}",
                source="modelscope",
                score=0.0,
            )]


# ============================================================
# 4. LiblibAI — AI 绘画模型平台
# ============================================================

class LiblibAIKnowledge(CommunityProvider):
    """LiblibAI (哩布哩布) 连接器"""

    name = "liblibai"

    def __init__(self):
        super().__init__()
        self.api_base = "https://api.liblib.art"

    async def _search_impl(self, query: str, top_k: int) -> list[KnowledgeResult]:
        """
        LiblibAI 模型搜索。
        需要皇帝提供：LiblibAI API Key
        """
        try:
            api_key = self._credentials.get("api_key", "")
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "EmpireBot/1.3",
            }
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            # 搜索模型
            payload = json.dumps({
                "keyword": query,
                "page": 1,
                "pageSize": top_k,
            }).encode()
            url = f"{self.api_base}/api/model/search"
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            results = []
            models = data.get("data", {}).get("list", [])
            for m in models[:top_k]:
                results.append(KnowledgeResult(
                    title=m.get("name", ""),
                    content=m.get("description", "")[:500] or "无描述",
                    source="liblibai",
                    score=0.7,
                    metadata={
                        "model_id": m.get("id", ""),
                        "type": m.get("type", ""),
                        "downloads": m.get("downloadCount", 0),
                    },
                ))
            return results if results else [KnowledgeResult(
                title="LiblibAI",
                content=f"未找到「{query}」相关模型。建议访问 liblib.art 搜索。",
                source="liblibai",
                score=0.3,
            )]
        except Exception as e:
            return [KnowledgeResult(
                title="ERROR",
                content=f"LiblibAI 检索失败: {e}",
                source="liblibai",
                score=0.0,
            )]
