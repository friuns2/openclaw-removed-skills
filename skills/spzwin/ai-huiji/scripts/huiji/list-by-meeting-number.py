#!/usr/bin/env python3
"""
huiji / list-by-meeting-number 脚本

用途：按视频会议号查询慧记列表（会议维度，含他人录制但本人参会的记录）

使用方式：
  python3 scripts/huiji/list-by-meeting-number.py [--human] [--body '<json>'] <meeting_number>

  # 基本用法
  python3 list-by-meeting-number.py 103760

  # 人类可读格式
  python3 list-by-meeting-number.py --human 103760

  # 带增量时间戳
  python3 list-by-meeting-number.py --body '{"meetingNumber":"MTG-001","lastTs":1716345600000}'

环境变量：
  XG_BIZ_API_KEY   — appKey（必须）
  XG_USER_TOKEN    — access-token（可选，增强鉴权）
"""

import sys
import os
import json
import time
from datetime import datetime, timezone, timedelta
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


API_URL = "https://sg-al-ai-voice-assistant.mediportal.com.cn/api/open-api/ai-huiji/meetingChat/listHuiJiIdsByMeetingNumberV2"
MAX_RETRIES = 3
RETRY_DELAY = 1

TZ = timezone(timedelta(hours=8))  # Asia/Shanghai


def ts_to_str(ts_ms):
    """毫秒时间戳 → 人类可读时间"""
    if ts_ms is None:
        return "-"
    try:
        dt = datetime.fromtimestamp(ts_ms / 1000, tz=TZ)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return str(ts_ms)


def duration_to_str(ms):
    """毫秒时长 → 人类可读"""
    if ms is None:
        return "-"
    try:
        total_sec = int(ms / 1000)
        h, remainder = divmod(total_sec, 3600)
        m, s = divmod(remainder, 60)
        if h > 0:
            return f"{h}小时{m}分钟"
        elif m > 0:
            return f"{m}分钟{s}秒"
        else:
            return f"{s}秒"
    except (TypeError, ValueError):
        return "-"


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


def format_human(result: dict) -> str:
    """将结果转换为人类可读格式"""
    if result.get("resultCode") != 1:
        return f"❌ 请求失败: {result.get('resultMsg', '未知错误')}"

    data = result.get("data", [])
    if not data:
        return "未找到相关记录"

    lines = [f"共 {len(data)} 条记录：\n"]

    # recordState 映射
    RECORD_STATE = {0: ("🟢", "进行中"), 1: ("⏳", "处理中"), 2: ("✅", "已完成"), 3: ("❌", "失败")}

    for i, item in enumerate(data, 1):
        chat_id = item.get("_id", "")
        name = item.get("name", "（无名称）")
        record_state = item.get("recordState", -1)
        create = ts_to_str(item.get("createTime"))
        finish = ts_to_str(item.get("finishTime"))
        length = duration_to_str(item.get("meetingLength"))

        icon, state_label = RECORD_STATE.get(record_state, ("❓", "未知"))

        lines.append(f"{i}. {icon} **{name}** ({state_label})")
        lines.append(f"   开始: {create} | 结束: {finish} | 时长: {length}")
        lines.append(f"   ID: {chat_id}")
        lines.append("")

    return "\n".join(lines)


def default_last_ts() -> int:
    """默认 lastTs：最近 10 天前的毫秒时间戳"""
    return int((datetime.now(tz=TZ) - timedelta(days=10)).timestamp() * 1000)


def main():
    human = "--human" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--human"]

    if len(args) >= 2 and args[0] == "--body":
        if len(args) < 2:
            print("用法: list-by-meeting-number.py [--human] --body '<json>'", file=sys.stderr)
            sys.exit(1)
        body = json.loads(args[1])
    elif len(args) >= 1:
        raw = args[0].strip()
        # 会议号：纯数字字符串转整数，避免后端解析为 null
        if raw.isdigit():
            body = {"meetingNumber": int(raw)}
        else:
            body = {"meetingNumber": raw}
    else:
        print("用法: list-by-meeting-number.py [--human] [--body '<json>'] <meeting_number>", file=sys.stderr)
        print("  --human: 时间戳自动转换为可读格式", file=sys.stderr)
        sys.exit(1)

    # 自动补 lastTs（默认最近 10 天）
    if "lastTs" not in body:
        body["lastTs"] = default_last_ts()

    result = call_api(body)

    if human:
        print(format_human(result))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
