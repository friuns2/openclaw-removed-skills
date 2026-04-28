#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件查询脚本

调用 ai-open-gateway 的 POST /api/event/query 接口，
支持自然语言查询设备事件，返回 AI 摘要和事件列表。

输出格式：JSON（供 agent 解析后格式化展示给用户）。
脚本只负责调用接口和裁剪数据，展示逻辑由 agent 根据 SKILL.md 规则完成。

API_KEY 获取优先级：
  1. 环境变量 AI_GATEWAY_API_KEY
  2. 配置文件 ~/.openclaw/.env 中的 AI_GATEWAY_API_KEY
  3. 命令行参数 --api-key

网关地址获取优先级：
  1. 环境变量 AI_GATEWAY_HOST
  2. 配置文件 ~/.openclaw/.env 中的 AI_GATEWAY_HOST
  3. 默认值 https://ai-open.icloseli.com

TLS 证书验证：
  默认启用。设置环境变量 AI_GATEWAY_VERIFY_SSL=false 可禁用（仅限开发环境）。

依赖：需要安装第三方包 httpx。
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("❌ 缺少依赖 httpx，请先安装：python3 -m pip install httpx", file=sys.stderr)
    sys.exit(1)

# 默认网关地址
DEFAULT_API_HOST = "https://ai-open.icloseli.com"

# 最大展示事件数（减少输出量，避免 agent 上下文溢出）
MAX_EVENTS = 3


def load_env_file():
    """
    从 ~/.openclaw/.env 文件加载环境变量配置。
    设置环境变量 AI_GATEWAY_NO_ENV_FILE=true 可跳过读取（生产环境推荐）。
    """
    # 生产环境可通过此开关禁用 .env fallback，避免共享凭证文件的安全风险
    if os.environ.get("AI_GATEWAY_NO_ENV_FILE", "").lower() in ("true", "1", "yes"):
        return {}
    env_path = Path.home() / ".openclaw" / ".env"
    if not env_path.exists():
        return {}
    result = {}
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    result[key] = value
    except Exception as e:
        print(f"⚠️ 读取配置文件 {env_path} 失败: {e}", file=sys.stderr)
    return result


def get_api_key(cli_key=None):
    """
    三级优先级获取 API_KEY：
      1. 环境变量 AI_GATEWAY_API_KEY
      2. ~/.openclaw/.env 配置文件
      3. 命令行参数 --api-key
    """
    key = os.environ.get("AI_GATEWAY_API_KEY")
    if key:
        return key
    env_vars = load_env_file()
    key = env_vars.get("AI_GATEWAY_API_KEY")
    if key:
        return key
    if cli_key:
        return cli_key
    return None


def get_api_host():
    """
    三级优先级获取网关地址：
      1. 环境变量 AI_GATEWAY_HOST
      2. ~/.openclaw/.env 配置文件中的 AI_GATEWAY_HOST
      3. 默认值 DEFAULT_API_HOST
    """
    host = os.environ.get("AI_GATEWAY_HOST")
    if host:
        return host.rstrip("/")
    env_vars = load_env_file()
    host = env_vars.get("AI_GATEWAY_HOST")
    if host:
        return host.rstrip("/")
    return DEFAULT_API_HOST


def get_verify_ssl():
    """
    判断是否启用 TLS 证书验证。
    默认启用。仅当环境变量 AI_GATEWAY_VERIFY_SSL 显式设为 false 时禁用。
    """
    val = os.environ.get("AI_GATEWAY_VERIFY_SSL", "true").lower()
    return val not in ("false", "0", "no")


def api_post(api_key, api_host, verify_ssl, path, body=None):
    """通用 POST 请求"""
    url = f"{api_host}{path}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = json.dumps(body).encode("utf-8") if body else b""
    try:
        with httpx.Client(verify=verify_ssl, timeout=120.0, headers=headers) as client:
            resp = client.post(url, content=data)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP 错误 {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"❌ 网络错误: {e}", file=sys.stderr)
        print(f"   请确认网关服务 {api_host} 是否已启动", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="查询设备事件")
    parser.add_argument("--api-key", help="API Key（优先级最低，建议用环境变量）")
    parser.add_argument("--device-ids", required=True, help="设备 ID 列表，逗号分隔")
    parser.add_argument("--start-date", required=True, help="开始日期，格式 yyyy-MM-dd")
    parser.add_argument("--end-date", required=True, help="结束日期，格式 yyyy-MM-dd")
    parser.add_argument("--query", required=True, help="自然语言查询，如「今天有没有人来过」")
    parser.add_argument("--locale", default="zh_CN", help="语言区域，默认 zh_CN")
    args = parser.parse_args()

    # 1. 获取 API_KEY
    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        print("❌ 未找到 AI_GATEWAY_API_KEY，请通过以下任一方式配置：", file=sys.stderr)
        print('   1. 环境变量: export AI_GATEWAY_API_KEY="your_key"', file=sys.stderr)
        print("   2. 配置文件: ~/.openclaw/.env 中添加 AI_GATEWAY_API_KEY=your_key", file=sys.stderr)
        print("   3. 命令行:   --api-key your_key", file=sys.stderr)
        sys.exit(1)

    # 2. 获取网关地址和 TLS 配置
    api_host = get_api_host()
    verify_ssl = get_verify_ssl()

    # 2.5 自动修正 device_id 大小写（XXXXS_ → xxxxS_）
    raw_ids = [d.strip() for d in args.device_ids.split(",") if d.strip()]
    device_ids = []
    for did in raw_ids:
        if did.upper().startswith("XXXXS_"):
            fixed = "xxxxS_" + did[6:]
            print(f"⚠️ 已自动修正 device_id 大小写: {did} → {fixed}", file=sys.stderr)
            device_ids.append(fixed)
        else:
            device_ids.append(did)

    # 3. 调用事件查询接口
    result = api_post(api_key, api_host, verify_ssl, "/api/event/query", {
        "device_ids": device_ids,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "query": args.query,
        "locale": args.locale,
    })

    # 4. 裁剪事件列表，只保留前 MAX_EVENTS 条（减少 token 量）
    #    在 JSON 中附加 _total_count 字段，供 agent 展示总数
    if result.get("code") == 0 and result.get("data"):
        events = result["data"].get("events", [])
        result["data"]["_total_count"] = len(events)
        result["data"]["events"] = events[:MAX_EVENTS]

    # 5. 输出 JSON（供 agent 解析后格式化展示）
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
