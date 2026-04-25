"""
知识库挂载 - 初始化并注册到帝国架构
Knowledge Mount - Initialize and register into Empire Architecture

在 Chancellor 中添加一行即可启用：
    from knowledge.mount import mount_knowledge
    mount_knowledge(chancellor)
"""

from .router import KnowledgeRouter
from .tencent_cloud import TencentCloudKnowledge
from .feishu import FeishuKnowledge
from .notion_kb import NotionKnowledge
from .local_rag import LocalRAGKnowledge
from .community import WaytoAGIKnowledge, DataWhaleKnowledge, ModelScopeKnowledge, LiblibAIKnowledge
from .hanlin import HanlinScholar, HanlinDirector
from .audit import KnowledgeAudit
from .config import load_config


def mount_knowledge(chancellor=None) -> dict:
    """
    初始化知识库 + 翰林院，注册所有已启用的知识源。

    Args:
        chancellor: 帝国架构的 Chancellor 实例（可选）

    Returns:
        {"router": KnowledgeRouter, "director": HanlinDirector, "audit": KnowledgeAudit}
    """
    cfg = load_config()
    router = KnowledgeRouter()
    director = HanlinDirector()
    audit = KnowledgeAudit()

    # ① 腾讯云知识引擎
    tc = cfg.get("tencent_cloud", {})
    tc_provider = None
    if tc.get("enabled"):
        tc_provider = TencentCloudKnowledge(
            secret_id=tc["secret_id"],
            secret_key=tc["secret_key"],
            knowledge_base_id=tc["knowledge_base_id"],
            region=tc.get("region", "ap-guangzhou"),
        )
        router.register(tc_provider)

    scholar_tc = HanlinScholar(
        "scholar_tencent", "腾讯云大学士", "tencent_cloud")
    director.register_scholar(scholar_tc, tc_provider)

    # ② 飞书知识库
    fs = cfg.get("feishu", {})
    fs_provider = None
    if fs.get("enabled"):
        fs_provider = FeishuKnowledge(
            app_id=fs["app_id"],
            app_secret=fs["app_secret"],
            space_id=fs.get("space_id", ""),
        )
        router.register(fs_provider)

    scholar_fs = HanlinScholar("scholar_feishu", "飞书大学士", "feishu")
    director.register_scholar(scholar_fs, fs_provider)

    # ③ Notion 知识库
    nt = cfg.get("notion", {})
    nt_provider = None
    if nt.get("enabled"):
        nt_provider = NotionKnowledge(
            api_key=nt["api_key"],
            database_id=nt.get("database_id", ""),
        )
        router.register(nt_provider)

    scholar_nt = HanlinScholar("scholar_notion", "Notion大学士", "notion")
    director.register_scholar(scholar_nt, nt_provider)

    # ④ 本地 RAG 知识库
    rag = cfg.get("local_rag", {})
    rag_provider = None
    if rag.get("enabled"):
        rag_provider = LocalRAGKnowledge(
            persist_dir=rag.get("persist_dir", "./data/knowledge"),
        )
        router.register(rag_provider)

    scholar_rag = HanlinScholar("scholar_rag", "本地RAG大学士", "local_rag")
    director.register_scholar(scholar_rag, rag_provider)

    # ========== 社区知识源（需皇帝批准） ==========

    # ⑤ WaytoAGI
    waytoagi_cfg = cfg.get("waytoagi", {})
    waytoagi_provider = WaytoAGIKnowledge()
    if waytoagi_cfg.get("enabled"):
        waytoagi_provider.approve()
        router.register(waytoagi_provider)

    scholar_wa = HanlinScholar("scholar_waytoagi", "WaytoAGI大学士", "waytoagi")
    director.register_scholar(scholar_wa, waytoagi_provider)

    # ⑥ DataWhale
    datawhale_cfg = cfg.get("datawhale", {})
    datawhale_provider = DataWhaleKnowledge()
    if datawhale_cfg.get("enabled"):
        datawhale_provider.approve(github_token=datawhale_cfg.get("github_token", ""))
        router.register(datawhale_provider)

    scholar_dw = HanlinScholar("scholar_datawhale", "DataWhale大学士", "datawhale")
    director.register_scholar(scholar_dw, datawhale_provider)

    # ⑦ ModelScope
    modelscope_cfg = cfg.get("modelscope", {})
    modelscope_provider = ModelScopeKnowledge()
    if modelscope_cfg.get("enabled"):
        modelscope_provider.approve(token=modelscope_cfg.get("token", ""))
        router.register(modelscope_provider)

    scholar_ms = HanlinScholar("scholar_modelscope", "ModelScope大学士", "modelscope")
    director.register_scholar(scholar_ms, modelscope_provider)

    # ⑧ LiblibAI
    liblibai_cfg = cfg.get("liblibai", {})
    liblibai_provider = LiblibAIKnowledge()
    if liblibai_cfg.get("enabled"):
        liblibai_provider.approve(api_key=liblibai_cfg.get("api_key", ""))
        router.register(liblibai_provider)

    scholar_ll = HanlinScholar("scholar_liblibai", "LiblibAI大学士", "liblibai")
    director.register_scholar(scholar_ll, liblibai_provider)

    # 挂载到 Chancellor
    if chancellor is not None:
        chancellor.knowledge_router = router
        chancellor.hanlin_director = director
        chancellor.knowledge_audit = audit

    return {"router": router, "director": director, "audit": audit}
