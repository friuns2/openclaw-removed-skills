#!/usr/bin/env python3
"""
huiji / split-record-list-v2 脚本

用途：增量查询指定慧记的分片转写原文（传入 lastStartTime 仅返回更新的分片）

使用方式：
  python3 scripts/huiji/split-record-list-v2.py [--body '<json>'] <meetingChatId> [lastStartTime]

  # 基本用法（全量，等同于 splitRecordList）
  python3 split-record-list-v2.py abc123

  # 增量（只拉 startTime > 120034 的分片）
  python3 split-record-list-v2.py abc123 120034

  # JSON body
  python3 split-record-list-v2.py --body '{"meetingChatId":"abc123","lastStartTime":120034}'

环境变量：
  XG_BIZ_API_KEY   — appKey（必须）
  XG_USER_TOKEN    — access-token（可选，增强鉴权）
"""

import sys
import os
import json
import time
import requests
import warnings

# 禁用 InsecureRequestWarning (因为 verify=False)
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)


def setup_utf8_stdio():
    """Best-effort UTF-8 stdio for Windows console display."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


setup_utf8_stdio()


API_URL = "https://sg-al-ai-voice-assistant.mediportal.com.cn/api/open-api/ai-huiji/meetingChat/splitRecordListV2"
MAX_RETRIES = 3
RETRY_DELAY = 1


def build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("XG_USER_TOKEN")
    app_key = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if token:
        headers["access-token"] = token
    if app_key:
        headers["appKey"] = app_key
    if not token and not app_key:
        print("错误: 请至少设置 XG_USER_TOKEN 或 XG_BIZ_API_KEY", file=sys.stderr)
        sys.exit(1)
    return headers


def call_api(body: dict) -> dict:
    headers = build_headers()
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                API_URL,
                json=body,
                headers=headers,
                verify=False,
                allow_redirects=True,
                timeout=60,
            )
            response.raise_for_status()
            return json.loads(response.content.decode("utf-8"))
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    print(f"错误: 请求失败（重试{MAX_RETRIES}次）: {last_err}", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--body":
        if len(sys.argv) < 3:
            print("用法: split-record-list-v2.py --body '<json>'", file=sys.stderr)
            sys.exit(1)
        body = json.loads(sys.argv[2])
    elif len(sys.argv) >= 3:
        body = {"meetingChatId": sys.argv[1], "lastStartTime": int(sys.argv[2])}
    elif len(sys.argv) >= 2:
        body = {"meetingChatId": sys.argv[1]}
    else:
        print("用法: split-record-list-v2.py [--body '<json>'] <meetingChatId> [lastStartTime]", file=sys.stderr)
        sys.exit(1)
    result = call_api(body)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
