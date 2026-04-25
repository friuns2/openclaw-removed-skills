"""
帝国架构 - 知识库挂载层
Empire Architecture - Knowledge Base Connectors

支持：
  1. 腾讯云知识引擎 (Tencent Cloud Knowledge Engine)
  2. 飞书知识库 (Feishu/Lark Wiki)
  3. Notion

用法：
  from knowledge import KnowledgeRouter
  router = KnowledgeRouter()
  results = await router.search("查询内容")
"""

from .base import KnowledgeProvider, KnowledgeResult
from .tencent_cloud import TencentCloudKnowledge
from .feishu import FeishuKnowledge
from .notion_kb import NotionKnowledge
from .local_rag import LocalRAGKnowledge
from .router import KnowledgeRouter
from .hanlin import HanlinScholar, HanlinDirector
from .audit import KnowledgeAudit
from .community import WaytoAGIKnowledge, DataWhaleKnowledge, ModelScopeKnowledge, LiblibAIKnowledge

__all__ = [
    "KnowledgeProvider",
    "KnowledgeResult",
    "TencentCloudKnowledge",
    "FeishuKnowledge",
    "NotionKnowledge",
    "LocalRAGKnowledge",
    "WaytoAGIKnowledge",
    "DataWhaleKnowledge",
    "ModelScopeKnowledge",
    "LiblibAIKnowledge",
    "KnowledgeRouter",
    "HanlinScholar",
    "HanlinDirector",
    "KnowledgeAudit",
]
