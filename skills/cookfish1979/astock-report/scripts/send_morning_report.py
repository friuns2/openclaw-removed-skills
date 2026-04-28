#!/usr/bin/env python3
"""晨报推送脚本 - 三步模式：
第一步（由LLM在cron prompt中完成）：搜索新闻 + 生成报告，写入 /tmp/morning_report_content.txt
第二步（Python）：读取文件 → 检查去重锁 → 保存MD → 推送（失败时发预警）
第三步（由LLM在cron prompt第四步中调用）：检查本脚本退出码，0=成功，非0=失败需预警
"""
from datetime import datetime, timezone, timedelta, timedelta as td
import sys, os, json, subprocess, urllib.request

sys.path.insert(0, '/workspace/keys')
from keys_loader import get_webhook_url

_TZ = timedelta(hours=8)
TS  = (datetime.now(timezone.utc) + _TZ).strftime("%Y%m%d_%H%M")

content_file = '/tmp/morning_report_content.txt'
LOCK_FILE    = '/tmp/.morning_report_lock.json'

def _now():
    return datetime.now(timezone.utc) + _TZ

def _date_str():
    return (datetime.now(timezone.utc) + _TZ).strftime("%Y%m%d")

def read_lock():
    try:
        with open(LOCK_FILE) as f:
            return json.load(f)
    except:
        return {}

def write_lock(date_str, status):
    with open(LOCK_FILE, 'w') as f:
        json.dump({'date': date_str, 'status': status, 'ts': _now().isoformat()}, f)

def notify_failure(msg: str):
    """推送失败时，通过 message 工具发预警通知"""
    alert = f"⚠️ 【晨报推送失败】\n{msg}\n\n请及时检查 cron 任务状态。"
    payload = json.dumps({
        "msgtype": "text",
        "text": {"content": alert}
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            get_webhook_url(),
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            if result.get("errcode") == 0:
                print(f"[{TS}] 失败通知已发送")
            else:
                print(f"[{TS}] 失败通知发送失败: {result}")
    except Exception as e:
        print(f"[{TS}] 失败通知自身也失败了: {e}")


if __name__ == "__main__":
    _today = _date_str()
    # ---------- 防重复推送：检查当日是否已推送 ----------
    lock = read_lock()
    if lock.get('date') == _today and lock.get('status') == 'ok':
        print(f"[{TS}] ⏭ 已推送，跳过（date={_today}）")
        sys.exit(0)

    print(f"[{TS}] 第一步：读取报告内容...")

    # ---------- 检查内容文件 ----------
    if not os.path.exists(content_file):
        msg = f"报告文件不存在: {content_file}"
        print(f"[{TS}] ❌ {msg}")
        notify_failure(msg)
        sys.exit(1)

    with open(content_file, encoding='utf-8') as f:
        report = f.read()

    if not report.strip():
        msg = "报告内容为空"
        print(f"[{TS}] ❌ {msg}")
        notify_failure(msg)
        sys.exit(1)

    # ---------- 保存 Markdown ----------
    print(f"[{TS}] 第二步：保存Markdown报告...")
    _dir = "/workspace/projects/A股报告系统/reports"
    os.makedirs(_dir, exist_ok=True)
    _path = os.path.join(_dir, f"晨报_{_today}.md")
    with open(_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  已保存: {_path}")

    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)

    # ---------- 推送 ----------
    print(f"\n[{TS}] 第三步：推送...")
    payload = json.dumps({"msgtype": "text", "text": {"content": report}}, ensure_ascii=False)
    try:
        req = urllib.request.Request(
            get_webhook_url(),
            data=payload.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            if result.get("errcode") == 0:
                # 推送成功，写入去重锁
                write_lock(_today, 'ok')
                print(f"\n[{TS}] ✅ 已推送")
                sys.exit(0)
            else:
                msg = f"webhook 返回错误: {result}"
                print(f"\n[{TS}] ❌ {msg}")
                notify_failure(msg)
                sys.exit(1)
    except Exception as e:
        msg = f"推送异常: {e}"
        print(f"\n[{TS}] ❌ {msg}")
        notify_failure(msg)
        sys.exit(1)
