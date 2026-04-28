#!/usr/bin/env python3
"""盘中预警验证脚本 — 修复字段索引后测试"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from keys_loader import wx_push, is_trading_window, now_bj, ts

INDICES = {
    "上证指数": "sh000001",
    "深证成指": "sz399001",
    "创业板指": "sz399006",
    "科创50": "sh000688",
    "沪深300": "sh000300",
    "中证500": "sh000905",
}
ALERT_THRESHOLD = 2.0

now = now_bj()
print(f"[{ts()}] 盘中预警检查...")
print(f"  北京时间: {now}")
print(f"  交易时段: {is_trading_window()}")
print()

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
    change_abs = float(parts[31]) if parts[31] else 0   # 正确: 涨跌额
    change_pct = float(parts[32]) if parts[32] else 0    # 正确: 涨跌幅%
    high = float(parts[33]) if parts[33] else 0
    low = float(parts[34]) if parts[34] else 0
    triggered = abs(change_pct) >= ALERT_THRESHOLD
    flag = " ✅ 触发" if triggered else ""
    print(f"  {name:<8} {price:>10.2f}  {change_pct:>+7.2f}%  {change_abs:>+8.2f}{flag}")
    if triggered:
        alerts.append((name, price, change_pct, change_abs, high, low))

print()
if not alerts:
    print("  ✅ 无指数触发阈值，正常退出")
else:
    print(f"  🚨 触发 {len(alerts)} 条，准备推送...")
    date_str = now.strftime("%Y年%m月%d日")
    time_str = now.strftime("%H:%M")
    lines_msg = [f"📊 **六大指数盘中预警**", f"🕐 {date_str} {time_str}", ""]
    for name, price, pct, chg, high, low in alerts:
        emoji = "🔴" if pct > 0 else "🟢"
        direction = "暴涨" if pct > 0 else "暴跌"
        lines_msg.append(f"{emoji} **{name}** {direction} {pct:+.2f}%")
        lines_msg.append(f"   最新: {price:.2f}  最高: {high:.2f}  最低: {low:.2f}  涨跌: {chg:+.2f}")
        lines_msg.append("")
    msg = "\n".join(lines_msg)
    print(msg)
    print()
    ok = wx_push(msg)
    print(f"  {'✅ 推送成功' if ok == 0 else f'❌ 推送失败 errcode={ok}'}")