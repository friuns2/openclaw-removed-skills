#!/usr/bin/env python3
"""盘中预警调试脚本"""
import sys, os, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))

from keys_loader import wx_push, get_webhook_url, already_sent, mark_sent, is_trading_window, now_bj

INDICES = {
    "上证指数": "sh000001",
    "深证成指": "sz399001",
    "创业板指": "sz399006",
    "科创50": "sh000688",
    "沪深300": "sh000300",
    "中证500": "sh000905",
}
ALERT_THRESHOLD = 2.0
STATE_FILE = "/workspace/.alert_sent"

now = now_bj()
print(f"[{now.strftime('%H:%M:%S')}] 检查盘中预警...")
print(f"  当前北京时间: {now}")
print(f"  交易时段: {is_trading_window()}")

# 获取指数数据
import requests
codes = ",".join(INDICES.values())
url = f"https://qt.gtimg.cn/q={codes}"
r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
raw = r.content.decode("gbk", errors="replace")
lines = raw.strip().split("\n")

alerts = []
for line in lines:
    content = line.lstrip("v_")
    parts = content.split("~")
    if len(parts) < 35:
        continue
    code = parts[2].strip().lstrip("sh").lstrip("sz")
    name = parts[1].strip()
    price = float(parts[3]) if parts[3] else 0
    prev_close = float(parts[4]) if parts[4] else price
    change_pct = float(parts[33]) if parts[33] else 0  # 涨跌幅%
    change_abs = float(parts[32]) if parts[32] else 0
    flag = " *** 触发 ***" if abs(change_pct) >= ALERT_THRESHOLD else ""
    print(f"  {name:<8} {price:>10.2f}  {change_pct:>+7.2f}%  {change_abs:>+8.2f}{flag}")
    if abs(change_pct) >= ALERT_THRESHOLD:
        alerts.append((name, price, change_pct, change_abs))

print(f"\n  触发预警数量: {len(alerts)}")
if not alerts:
    print("  无触发，退出")
    sys.exit(0)

# 读取已发送记录
sent_today = {}
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) >= 3 and parts[0] == now.strftime("%Y%m%d"):
                sent_today[parts[1]] = float(parts[2])

# 去重判断
new_alerts = []
for name, price, pct, chg in alerts:
    key = name
    if key in sent_today:
        print(f"  [去重] {name} 今日已推送({sent_today[key]:+.2f}%)，跳过")
    else:
        new_alerts.append((name, price, pct, chg))

if not new_alerts:
    print("  全部去重，退出")
else:
    print(f"\n  实际推送 {len(new_alerts)} 条:")
    for name, price, pct, chg in new_alerts:
        print(f"  - {name} {pct:+.2f}%")

    # 发送消息
    webhook = get_webhook_url()
    if not webhook:
        print("  [错误] 未配置企业微信 webhook")
        sys.exit(1)

    date_str = now.strftime("%Y年%m月%d日")
    time_str = now.strftime("%H:%M")
    lines_out = [
        f"📊 **六大指数盘中预警**",
        f"🕐 {date_str} {time_str}",
        "",
    ]
    for name, price, pct, chg in new_alerts:
        emoji = "🔴" if pct > 0 else "🟢"
        lines_out.append(f"{emoji} **{name}** {pct:+.2f}% ({(pct > 0).sign if hasattr(pct,'sign') else '涨' if pct>0 else '跌'})")
        lines_out.append(f"   当前: {price:.2f}  涨跌: {chg:+.2f}")
        lines_out.append("")

    msg = "\n".join(lines_out)
    print(f"\n  发送内容:\n{msg}")
    ok = wx_push(msg)
    print(f"  推送结果: {'成功' if ok else '失败'}")

    if ok:
        for name, price, pct, chg in new_alerts:
            key = name
            with open(STATE_FILE, "a") as f:
                f.write(f"{now.strftime('%Y%m%d')},{key},{pct:.2f}\n")
        print("  已标记发送")