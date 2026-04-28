#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备列表查询脚本

调用 ai-open-gateway 的 POST /api/device/list 接口，
获取当前用户绑定的所有设备信息。

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


def call_device_list(api_key, api_host, verify_ssl):
    """
    调用 POST /api/device/list 获取设备列表。

    # Returns
    * dict - 接口返回的完整 JSON 响应
    """
    url = f"{api_host}/api/device/list"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    try:
        with httpx.Client(verify=verify_ssl, timeout=120.0, headers=headers) as client:
            resp = client.post(url, content=b"")
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
    parser = argparse.ArgumentParser(description="查询设备列表")
    parser.add_argument("--api-key", help="API Key（优先级最低，建议用环境变量）")
    args = parser.parse_args()

    # 1. 获取 API_KEY
    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        print("❌ 未找到 AI_GATEWAY_API_KEY，请通过以下任一方式配置：", file=sys.stderr)
        print("   1. 环境变量: export AI_GATEWAY_API_KEY=\"your_key\"", file=sys.stderr)
        print("   2. 配置文件: ~/.openclaw/.env 中添加 AI_GATEWAY_API_KEY=your_key", file=sys.stderr)
        print("   3. 命令行:   --api-key your_key", file=sys.stderr)
        sys.exit(1)

    # 2. 获取网关地址和 TLS 配置
    api_host = get_api_host()
    verify_ssl = get_verify_ssl()

    # 3. 调用设备列表接口
    result = call_device_list(api_key, api_host, verify_ssl)

    # 4. 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
