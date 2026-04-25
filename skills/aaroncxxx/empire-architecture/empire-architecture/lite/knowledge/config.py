"""
知识库配置
Knowledge Base Configuration

配置三个知识源的连接信息。
使用前填入你的 API Key / Token。
"""

import json
import os

# ============================================================
# 🔧 在这里填入你的凭据
# ============================================================

KNOWLEDGE_CONFIG = {
    "tencent_cloud": {
        "enabled": False,  # 改为 True 启用
        "secret_id": "",           # 腾讯云 SecretId
        "secret_key": "",          # 腾讯云 SecretKey
        "knowledge_base_id": "",   # 知识库 ID
        "region": "ap-guangzhou",  # ap-guangzhou 或 ap-shanghai
    },

    "feishu": {
        "enabled": False,  # 改为 True 启用
        "app_id": "",       # 飞书应用 App ID
        "app_secret": "",   # 飞书应用 App Secret
        "space_id": "",     # 知识空间 ID（留空搜索全部）
    },

    "notion": {
        "enabled": False,  # 改为 True 启用
        "api_key": "",          # Notion Integration Token
        "database_id": "",      # 数据库 ID（留空全局搜索）
    },

    "local_rag": {
        "enabled": True,        # 本地 RAG 默认启用
        "persist_dir": "./data/knowledge",  # 向量库持久化目录
    },

    # ========== 社区知识源（需皇帝批准） ==========

    "waytoagi": {
        "enabled": False,       # 皇帝批准后改 True
        "note": "免费平台，无需 API Key，皇帝批准即可启用",
    },

    "datawhale": {
        "enabled": False,
        "github_token": "",     # 可选，提高 GitHub rate limit
        "note": "GitHub 开源教程，可选 Token",
    },

    "modelscope": {
        "enabled": False,
        "token": "",            # ModelScope Token
        "note": "需皇帝提供 ModelScope Token",
    },

    "liblibai": {
        "enabled": False,
        "api_key": "",          # LiblibAI API Key
        "note": "需皇帝提供 LiblibAI API Key",
    },
}

# 也可以从环境变量读取（优先级高于上面的配置）
# export TENCENT_CLOUD_SECRET_ID=xxx
# export FEISHU_APP_ID=xxx
# export NOTION_API_KEY=xxx

def load_config() -> dict:
    """加载知识库配置，环境变量优先"""
    cfg = KNOWLEDGE_CONFIG.copy()

    # 腾讯云
    if os.getenv("TENCENT_CLOUD_SECRET_ID"):
        cfg["tencent_cloud"]["secret_id"] = os.getenv("TENCENT_CLOUD_SECRET_ID", "")
        cfg["tencent_cloud"]["secret_key"] = os.getenv("TENCENT_CLOUD_SECRET_KEY", "")
        cfg["tencent_cloud"]["knowledge_base_id"] = os.getenv("TENCENT_CLOUD_KB_ID", "")
        cfg["tencent_cloud"]["enabled"] = bool(cfg["tencent_cloud"]["secret_id"])

    # 飞书
    if os.getenv("FEISHU_APP_ID"):
        cfg["feishu"]["app_id"] = os.getenv("FEISHU_APP_ID", "")
        cfg["feishu"]["app_secret"] = os.getenv("FEISHU_APP_SECRET", "")
        cfg["feishu"]["space_id"] = os.getenv("FEISHU_SPACE_ID", "")
        cfg["feishu"]["enabled"] = bool(cfg["feishu"]["app_id"])

    # Notion
    if os.getenv("NOTION_API_KEY"):
        cfg["notion"]["api_key"] = os.getenv("NOTION_API_KEY", "")
        cfg["notion"]["database_id"] = os.getenv("NOTION_DATABASE_ID", "")
        cfg["notion"]["enabled"] = bool(cfg["notion"]["api_key"])

    return cfg
