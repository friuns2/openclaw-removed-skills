"""帝国架构 - 配置加载"""
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")


def load_empire_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_llm_credentials():
    """从环境变量读取 MiMo API 凭据"""
    api_key = os.environ.get("MIMO_API_KEY", "")
    endpoint = os.environ.get("MIMO_API_ENDPOINT", "")
    if not api_key or not endpoint:
        # fallback: 从 openclaw.json 读取
        try:
            with open(OPENCLAW_CONFIG) as f:
                oc = json.load(f)
            providers = oc.get("models", {}).get("providers", {})
            for name, p in providers.items():
                if "apiKey" in p:
                    api_key = api_key or p["apiKey"]
                    endpoint = endpoint or p.get("baseURL") or p.get("baseUrl", "")
        except Exception:
            pass
    # 确保 endpoint 是 chat/completions 完整路径
    if endpoint and not endpoint.endswith("/chat/completions"):
        endpoint = endpoint.rstrip("/") + "/chat/completions"
    return {
        "provider": "xiaomi",
        "base_url": endpoint,
        "api_key": api_key,
    }
