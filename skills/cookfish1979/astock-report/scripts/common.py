#!/usr/bin/env python3
"""
A股报告推送公共模块
提供：企业微信推送、时间判断、去重状态管理
"""
import subprocess, json, os, sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "/workspace")
from keys_loader import get_webhook_url

WEBHOOK_URL = ""

def load_config():
    global WEBHOOK_URL
    try:
        WEBHOOK_URL = get_webhook_url()
    except Exception as e:
        print(f"❌ 读取 Webhook URL 失败: {e}")
        sys.exit(1)

def wx_push(text: str) -> int:
    load_config()
    payload = json.dumps({"msgtype": "text", "text": {"content": text}}, ensure_ascii=False)
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", WEBHOOK_URL,
         "-H", "Content-Type: application/json", "-d", "@-"],
        input=payload.encode("utf-8"), capture_output=True)
    try:
        return json.loads(r.stdout.decode()).get("errcode", -1)
    except Exception:
        return -1

def wx_push_markdown(text: str) -> int:
    load_config()
    payload = json.dumps({"msgtype": "markdown", "markdown": {"content": text}}, ensure_ascii=False)
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", WEBHOOK_URL,
         "-H", "Content-Type: application/json", "-d", "@-"],
        input=payload.encode("utf-8"), capture_output=True)
    try:
        return json.loads(r.stdout.decode()).get("errcode", -1)
    except Exception:
        return -1

def is_trading_day() -> bool:
    now_bj = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8)))
    return now_bj.weekday() < 5

def is_trading_window():
    now_bj = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8)))
    w = now_bj.weekday()
    if w >= 5:
        return False
    h, m = now_bj.hour, now_bj.minute
    morning = (h == 9 and m >= 30) or (10 <= h <= 11)
    afternoon = 13 <= h <= 15
    return morning or afternoon

def already_sent(state_file: str) -> bool:
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d")
    f = os.path.join(os.path.dirname(__file__), state_file)
    return os.path.exists(f) and open(f).read().strip() == today

def mark_sent(state_file: str):
    f = os.path.join(os.path.dirname(__file__), state_file)
    with open(f, "w") as fp:
        fp.write(datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d"))

def now_bj():
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8)))

def ts():
    return now_bj().strftime("%Y-%m-%d %H:%M")


def get_ipo_report_period(ref_date=None):
    """
    周期：本周一 ~ 本周五（固定5天）。
    用于 IPO 周报，每周六触发时覆盖本周一至周五的完整交易周数据。

    Returns:
        (period_start: datetime, period_end: datetime,
         period_start_str: str, period_end_str: str)
    """
    if ref_date is None:
        ref_date = now_bj()
    # 本周一（weekday() 0=Monday）
    monday = ref_date - timedelta(days=ref_date.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday, monday.strftime("%m月%d日"), friday.strftime("%m月%d日")
