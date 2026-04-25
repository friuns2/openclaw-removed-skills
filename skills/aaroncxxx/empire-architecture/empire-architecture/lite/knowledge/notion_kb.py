"""
Notion 知识库
API: api.notion.com
搜索: POST /v1/search
查询数据库: POST /v1/databases/{id}/query
"""

import json
import urllib.request
import urllib.error
from .base import KnowledgeProvider, KnowledgeResult


class NotionKnowledge(KnowledgeProvider):
    """Notion 知识库连接器"""

    name = "notion"

    def __init__(self, api_key: str, database_id: str = ""):
        self.api_key = api_key
        self.database_id = database_id  # 留空则全局搜索
        self.api_version = "2022-06-28"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": self.api_version,
            "Content-Type": "application/json",
        }

    def _extract_text(self, rich_text: list) -> str:
        """提取 Notion rich_text 内容"""
        return "".join(t.get("plain_text", "") for t in rich_text)

    async def search(self, query: str, top_k: int = 3) -> list[KnowledgeResult]:
        results = []

        if self.database_id:
            # 查询指定数据库
            payload = json.dumps({
                "filter": {
                    "or": [
                        {"property": "title", "title": {"contains": query}},
                    ],
                },
                "page_size": top_k,
            }).encode()
            url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        else:
            # 全局搜索
            payload = json.dumps({
                "query": query,
                "page_size": top_k,
            }).encode()
            url = "https://api.notion.com/v1/search"

        req = urllib.request.Request(
            url,
            data=payload,
            headers=self._headers(),
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            for page in data.get("results", []):
                # 提取标题
                title = ""
                props = page.get("properties", {})
                for prop in props.values():
                    if prop.get("type") == "title":
                        title = self._extract_text(prop.get("title", []))
                        break

                # 提取内容预览
                content = ""
                children = page.get("children", [])
                for child in children[:3]:
                    block_type = child.get("type", "")
                    block = child.get(block_type, {})
                    if "rich_text" in block:
                        content += self._extract_text(block["rich_text"]) + "\n"

                results.append(KnowledgeResult(
                    title=title or "Untitled",
                    content=content.strip()[:500] or title,
                    source="notion",
                    score=0.8,
                    metadata={
                        "page_id": page.get("id", ""),
                        "url": page.get("url", ""),
                        "last_edited": page.get("last_edited_time", ""),
                    },
                ))

            return results[:top_k]

        except Exception as e:
            return [KnowledgeResult(
                title="ERROR",
                content=f"Notion 知识库检索失败: {e}",
                source="notion",
                score=0.0,
            )]

    async def health_check(self) -> bool:
        try:
            req = urllib.request.Request(
                "https://api.notion.com/v1/users/me",
                headers=self._headers(),
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            return data.get("object") == "user"
        except Exception:
            return False
