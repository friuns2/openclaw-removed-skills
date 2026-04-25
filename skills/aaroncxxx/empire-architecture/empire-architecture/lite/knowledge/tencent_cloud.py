"""
腾讯云知识引擎 (Tencent Cloud Knowledge Engine)
API: lkeap.tencentcloudapi.com
接口: RetrieveKnowledge
"""

import json
import urllib.request
import urllib.error
import hashlib
import hmac
import time
import datetime
from .base import KnowledgeProvider, KnowledgeResult


class TencentCloudKnowledge(KnowledgeProvider):
    """腾讯云知识引擎连接器"""

    name = "tencent_cloud"

    def __init__(self, secret_id: str, secret_key: str,
                 knowledge_base_id: str, region: str = "ap-guangzhou"):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.knowledge_base_id = knowledge_base_id
        self.region = region
        self.host = "lkeap.tencentcloudapi.com"
        self.service = "lkeap"
        self.version = "2024-05-22"

    def _sign(self, method: str, uri: str, query: str, headers: dict,
              payload: bytes, timestamp: int) -> dict:
        """腾讯云 API 3.0 签名"""
        date = datetime.datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        credential_scope = f"{date}/{self.service}/tc3_request"

        # Canonical request
        canonical_headers = ""
        signed_headers = ""
        sorted_headers = sorted(headers.items())
        for k, v in sorted_headers:
            canonical_headers += f"{k.lower()}:{v.strip()}\n"
            signed_headers += f"{k.lower()};"
        signed_headers = signed_headers.rstrip(";")

        canonical_request = (
            f"{method}\n{uri}\n{query}\n"
            f"{canonical_headers}\n{signed_headers}\n"
            f"{hashlib.sha256(payload).hexdigest()}"
        )

        # String to sign
        string_to_sign = (
            f"TC3-HMAC-SHA256\n{timestamp}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode()).hexdigest()}"
        )

        # Signing key
        def _hmac_sha256(key, msg):
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()

        secret_date = _hmac_sha256(f"TC3{self.secret_key}".encode(), date)
        secret_service = _hmac_sha256(secret_date, self.service)
        secret_signing = _hmac_sha256(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode(),
                             hashlib.sha256).hexdigest()

        auth = (
            f"TC3-HMAC-SHA256 "
            f"Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )
        return {"Authorization": auth}

    async def search(self, query: str, top_k: int = 3) -> list[KnowledgeResult]:
        payload = json.dumps({
            "KnowledgeBaseId": self.knowledge_base_id,
            "Query": query,
            "RetrievalMethod": "HYBRID",
            "RetrievalSetting": {
                "TopK": top_k,
                "ScoreThreshold": 0.5,
            },
        }).encode()

        timestamp = int(time.time())
        headers = {
            "Content-Type": "application/json",
            "Host": self.host,
            "X-TC-Action": "RetrieveKnowledge",
            "X-TC-Version": self.version,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Region": self.region,
        }

        auth_headers = self._sign("POST", "/", "", headers, payload, timestamp)
        headers.update(auth_headers)

        req = urllib.request.Request(
            f"https://{self.host}/",
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            records = data.get("Response", {}).get("Records", [])
            return [
                KnowledgeResult(
                    title=r.get("Title", ""),
                    content=r.get("Content", ""),
                    source="tencent_cloud",
                    score=r.get("Metadata", {}).get("Score", 0.0),
                    metadata=r.get("Metadata", {}),
                )
                for r in records
            ]
        except Exception as e:
            return [KnowledgeResult(
                title="ERROR",
                content=f"腾讯云知识引擎检索失败: {e}",
                source="tencent_cloud",
                score=0.0,
            )]

    async def health_check(self) -> bool:
        try:
            results = await self.search("test", top_k=1)
            return results[0].title != "ERROR" if results else True
        except Exception:
            return False
