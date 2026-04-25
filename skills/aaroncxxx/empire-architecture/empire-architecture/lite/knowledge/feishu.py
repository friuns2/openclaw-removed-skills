"""
飞书知识库 (Feishu/Lark Wiki)
API: open.feishu.cn
Wiki Search: /open-apis/wiki/v2/spaces/search
"""

import json
import urllib.request
import urllib.error
from .base import KnowledgeProvider, KnowledgeResult


class FeishuKnowledge(KnowledgeProvider):
    """飞书知识库连接器"""

    name = "feishu"

    def __init__(self, app_id: str, app_secret: str, space_id: str = ""):
        self.app_id = app_id
        self.app_secret = app_secret
        self.space_id = space_id  # 知识空间 ID，留空则搜索全部
        self._tenant_token = ""
        self._token_expire = 0

    def _get_tenant_token(self) -> str:
        """获取 tenant_access_token"""
        import time
        now = int(time.time())
        if self._tenant_token and now < self._token_expire - 60:
            return self._tenant_token

        payload = json.dumps({
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }).encode()

        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        self._tenant_token = data.get("tenant_access_token", "")
        self._token_expire = now + data.get("expire", 7200)
        return self._tenant_token

    async def search(self, query: str, top_k: int = 3) -> list[KnowledgeResult]:
        token = self._get_tenant_token()

        # 搜索知识库节点
        url = "https://open.feishu.cn/open-apis/wiki/v2/nodes/search"
        params = f"search_key={query}&page_size={top_k}"
        if self.space_id:
            url = f"https://open.feishu.cn/open-apis/wiki/v2/spaces/{self.space_id}/nodes/search"
            params = f"search_key={query}&page_size={top_k}"

        req = urllib.request.Request(
            f"{url}?{params}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            items = data.get("data", {}).get("items", [])
            results = []
            for item in items:
                node = item.get("node", item)
                results.append(KnowledgeResult(
                    title=node.get("title", ""),
                    content=node.get("snippet", node.get("title", "")),
                    source="feishu",
                    score=0.8,  # 飞书不返回分数
                    metadata={
                        "node_token": node.get("node_token", ""),
                        "obj_token": node.get("obj_token", ""),
                        "obj_type": node.get("obj_type", ""),
                    },
                ))
            return results[:top_k]

        except Exception as e:
            return [KnowledgeResult(
                title="ERROR",
                content=f"飞书知识库检索失败: {e}",
                source="feishu",
                score=0.0,
            )]

    async def health_check(self) -> bool:
        try:
            self._get_tenant_token()
            return bool(self._tenant_token)
        except Exception:
            return False
