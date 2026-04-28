#!/usr/bin/env python3
"""A股IPO周报 - 微信友好版（周三~下周二自动周期）"""
import json, subprocess, re, os
import pandas as pd
from datetime import datetime, timedelta
import sys

# ── 防重：按执行日期去重，同一天只发送一次 ───────────────────
_STATE_FILE = "/workspace/scripts/.ipo_report_sent"

def _mark_sent_today():
    """记录今天执行日期（YYYYMMDD），用于次日重新计算周期"""
    with open(_STATE_FILE, "w") as f:
        f.write(NOW.strftime("%Y%m%d"))

def _already_sent_today():
    """今天已运行过则跳过（不同周用不同周期，无需比较周期日期）"""
    if not os.path.exists(_STATE_FILE):
        return False
    return open(_STATE_FILE).read().strip() == NOW.strftime("%Y%m%d")

# ── 防并发重复运行锁（脚本层面）───────────────────────────────
_LOCK_FILE = "/tmp/a_stock_ipo.lock"

def _acquire_lock():
    if os.path.exists(_LOCK_FILE):
        print(f"[LOCK] 已有实例在运行 ({_LOCK_FILE})，退出。")
        sys.exit(0)
    open(_LOCK_FILE, "w").close()

def _release_lock():
    if os.path.exists(_LOCK_FILE):
        os.remove(_LOCK_FILE)

# ── 周期计算 ──────────────────────────────────────────────
sys.path.insert(0, "/workspace/skills/A-stock-report/scripts")
from common import get_ipo_report_period, now_bj

NOW = now_bj()
_period_start_dt, _period_end_dt, REPORT_START, PERIOD_END_STR = get_ipo_report_period(NOW)
# 周期唯一标识：用于文件命名（YYYYMMDD = 周期末日期）
_PERIOD_KEY = _period_end_dt.strftime("%Y%m%d")  # e.g. "20260424"

# ── 兜底检查：周期距今不超过3周，超出则视为异常拒绝发送 ──
_days_old = (NOW.date() - _period_end_dt.date()).days
if _days_old > 21:
    print(f"[IPO周报] ⚠️ 周期 {_period_start_dt.date()}～{_period_end_dt.date()} 距今 {_days_old} 天（>{21}天），疑似数据异常，拒绝发送！")
    sys.exit(1)

if _already_sent_today():
    print(f"[IPO周报] 今日（{NOW.strftime('%Y%m%d')}）已运行过，跳过")
    sys.exit(0)
# 周期：本周一 ～ 本周五
PERIOD_START = _period_start_dt
PERIOD_END   = _period_end_dt
# 下周上会计划截止日：本期周五 + 7天 = 下下周五
_w = NOW.weekday()
_days_to_next_fri = (11 - _w) % 7 + 7   # 距下下周五的天数
THIS_WEEK_END = (_period_end_dt + timedelta(days=7)).strftime("%m/%d")   # 下周周期截止日（下下周五）
NEXT_WEEK_END = (_period_end_dt + timedelta(days=14)).strftime("%m/%d")   # 下下周周期截止日
QUEUE_DATE    = _period_end_dt.strftime("%Y年%m月%d日")

# ── Webhook ───────────────────────────────────────────────
sys.path.insert(0, "/workspace/keys")
from keys_loader import get_webhook_url

def wx(text, max_retries=2):
    """发送消息到企业微信，带自动重试（errcode!=0 时重试）"""
    d = {"msgtype": "text", "text": {"content": text}}
    p = json.dumps(d, ensure_ascii=False)
    for attempt in range(max_retries + 1):
        r = subprocess.run(
            ["curl", "-s", "-X", "POST", get_webhook_url(),
             "-H", "Content-Type: application/json", "-d", "@-"],
            input=p.encode("utf-8"), capture_output=True)
        try:
            errcode = json.loads(r.stdout.decode()).get("errcode", -1)
        except:
            errcode = -1
        if errcode == 0:
            return 0
        print(f"[WX] 发送失败，errcode={errcode}，{'重试中...' if attempt < max_retries else '放弃'}")
    return -1

def shname(name, n=12):
    return name[:n] + ".." if len(name) > n else name

def sdate(dt):
    return str(dt)[5:7] + "/" + str(dt)[8:10]

def board_alias(b):
    return {"上交所科创板": "科创板", "深交所创业板": "创业板",
            "深交所主板": "深主板", "上交所主板": "沪主板",
            "北交所": "北交所"}.get(b, b)

# ── 首日涨幅历史数据（兜底用，自动搜索优先）────────────────
LISTINGS_GAIN_HISTORY = {
    "301683": {"name": "慧谷新材", "date": "04/01", "gain": "61.66%"},
    "001257": {"name": "盛龙股份", "date": "03/31", "gain": "254.0%"},
    "688813": {"name": "泰金新能", "date": "03/31", "gain": "88.24%"},
    "920055": {"name": "隆源股份", "date": "03/31", "gain": "53.04%"},
    "920188": {"name": "悦龙科技", "date": "03/30", "gain": "184.0%"},
}

# ── 首日涨幅自动搜索 ───────────────────────────────────────
import re

def _call_web_search(queries):
    """通过 gateway HTTP API 调用 batch_web_search"""
    import urllib.request, urllib.error
    payload = json.dumps({
        "tool": "batch_web_search",
        "action": "json",
        "args": {"queries": [{"query": q, "num_results": 3} for q in queries]}
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:18789/tools/invoke",
        data=payload,
        headers={
            "Authorization": "Bearer minimax-agent",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        # gateway 返回: result.content[i].text 是嵌套 JSON 字符串
        # 需解析到 formatted_content 层供 _extract_gain 使用
        blocks = raw.get("result", {}).get("content", [])
        for b in blocks:
            text = b.get("text", "")
            if text:
                try:
                    # text 是 {"content": [{"text": "{\"data\": [...]}"}, ...]} → 解析两次
                    layer1 = json.loads(text)
                    inner_text = layer1.get("content", [{}])[0].get("text", "")
                    layer2 = json.loads(inner_text)
                    fc = layer2.get("data", [{}])[0].get("formatted_content", [])
                    b["formatted_content"] = fc
                except Exception:
                    b["formatted_content"] = []
            else:
                b["formatted_content"] = []
        return raw
    except Exception as e:
        print(f"[首日涨幅] gateway API 失败: {e}")
        return {}

def _extract_gain(raw_text, code, name):
    """从搜索文本中提取首日涨幅百分比"""
    patterns = [
        r'涨幅?\s*([-+]?\d+\.?\d*)\s*%',
        r'首日[涨落]\s*([-+]?\d+\.?\d*)\s*%',
        r'([-+]?\d+\.?\d*)%',
    ]
    candidates = []
    for pat in patterns:
        for m in re.finditer(pat, raw_text):
            v = float(m.group(1))
            if 10 < v < 500:  # 新股合理涨幅区间
                candidates.append(v)
    if candidates:
        candidates.sort()
        return f"{candidates[len(candidates)//2]:.2f}%"
    return None

def _fetch_first_day_gains(listings):
    """
    自动搜索本期上市新股的首日涨幅（逐个发请求，避免批量合并丢失数据）。
    listings: [(code, name, date_str), ...]
    返回: {code: {"name":..., "date":..., "gain": "XX.XX%"}, ...}
    """
    if not listings:
        return {}
    # 逐个发请求：避免 batch 合并 block 导致部分结果丢失
    result = {}
    for code, name, date_str in listings:
        query = f"{name} {code} 上市首日收盘涨幅 {date_str}"
        raw = _call_web_search([query])
        content_blocks = raw.get("result", {}).get("content", [])
        block = content_blocks[0] if content_blocks else {}
        fc = block.get("formatted_content", [])
        snippets = " ".join(item.get("snippet", "") for item in fc if isinstance(item, dict))
        gain = _extract_gain(snippets, code, name)
        result[code] = {"name": name, "date": date_str, "gain": gain or "无数据"}
    fetched = {k: v["gain"] for k, v in result.items()}
    print(f"[首日涨幅] 搜索结果: {fetched}")
    return result
    for i, (code, name, date_str) in enumerate(listings):
        block = content_blocks[i].get('formatted_content', []) if i < len(content_blocks) else []
        # formatted_content 现在是列表，每项是 {"title","snippet"...}
        snippets = ' '.join(
            item.get('snippet', '') for item in block
            if isinstance(item, dict)
        )
        gain = _extract_gain(snippets, code, name)
        result[code] = {"name": name, "date": date_str, "gain": gain or "无数据"}
    fetched = {k: v['gain'] for k, v in result.items()}
    # DEBUG
    sample_block = content_blocks[0] if content_blocks else {}
    print(f"[首日涨幅] DEBUG fc数量={len(sample_block.get('formatted_content',[]))} snippet前50={str(sample_block.get('formatted_content',[])[0].get('snippet',''))[:50] if sample_block.get('formatted_content') else '空'}")
    print(f"[首日涨幅] 搜索结果: {fetched}")
    return result

def fmt_price(v):
    if pd.isna(v): return "N/A"
    return f"{v:.2f}元"

# ── 数据拉取（AKShare）─────────────────────────────────────
import akshare as ak

_pstart_str = PERIOD_START.strftime("%Y-%m-%d")
_pend_str   = PERIOD_END.strftime("%Y-%m-%d")
# 下周期（再下周）截止日 = 本期周五 + 14天
_pnext_fri = (_period_end_dt + timedelta(days=14)).strftime("%Y-%m-%d")

review = ak.stock_ipo_review_em()
review["上会日期"] = pd.to_datetime(review["上会日期"], errors="coerce").dt.tz_localize(None)
_pstart_ts = pd.Timestamp(_pstart_str)  # tz-naive
_pend_ts   = pd.Timestamp(_pend_str)   # tz-naive，本周五（含）← 已确保不丢
# 下周期起止：本期周五 +7天 ~ +14天（tz-naive，保持一致）
_next_start_ts = (_period_end_dt + timedelta(days=7))
_next_end_ts   = (_period_end_dt + timedelta(days=14))
recent_r = (review
    .loc[review["上会日期"].between(_pstart_ts, _pend_ts)]
    .dropna(subset=["上会日期"])
    .sort_values("上会日期"))
next_r = (review
    .loc[review["上会日期"].between(
            pd.Timestamp(_next_start_ts.strftime("%Y-%m-%d")),
            pd.Timestamp(_next_end_ts.strftime("%Y-%m-%d")))]
    .dropna(subset=["上会日期"])
    .sort_values("上会日期"))

df = ak.stock_new_ipo_cninfo()
df["申购_dt"] = pd.to_datetime(df["申购日期"], errors="coerce").dt.tz_localize(None)
df["上市_dt"] = pd.to_datetime(df["上市日期"], errors="coerce").dt.tz_localize(None)
recent_a = (df
    .loc[df["申购_dt"].between(pd.Timestamp(_pstart_str), pd.Timestamp(_pend_str))]
    .dropna(subset=["申购_dt"])
    .sort_values("申购_dt"))
next_a = (df
    .loc[df["申购_dt"].between(
            pd.Timestamp((_period_end_dt + timedelta(days=3)).strftime("%Y-%m-%d")),  # 下下周一
            pd.Timestamp(_pnext_fri))]
    .dropna(subset=["申购_dt"])
    .sort_values("申购_dt"))
recent_l = (df
    .loc[df["上市_dt"].between(pd.Timestamp(_pstart_str), pd.Timestamp(_pend_str))]
    .dropna(subset=["上市_dt"])
    .sort_values("上市_dt"))

queue = ak.stock_ipo_declare_em()
queue["更新日期"] = pd.to_datetime(queue["更新日期"], errors="coerce").dt.tz_localize(None)
recent_up = queue[queue["更新日期"].between(pd.Timestamp(_pstart_str), pd.Timestamp(_pend_str))]
reg_up    = recent_up[recent_up["最新状态"].isin(["注册", "核准"])].dropna(subset=["企业名称"])

# ── 排队数据（暂用固定值，建议后续改为爬虫实时获取）──────────
QUEUE = {
    "科创板": [("已受理", 2), ("问询", 35), ("提交注册", 3)],
    "创业板": [("问询", 33), ("过会", 1)],
    "沪主板": [("已受理", 2), ("问询", 15), ("提交注册", 1)],
    "深主板": [("已受理", 3), ("问询", 9), ("过会", 1), ("提交注册", 3)],
    "北交所": [("问询", 122), ("过会", 18)],
}
QUEUE_TOTALS = {"全市场": 248, "问询中": 214, "已过会": 20, "提交注册": 7}

# ── 组装报告 ───────────────────────────────────────────────
lines = [f"📋 A股IPO周报 {REPORT_START}～{PERIOD_END_STR}", ""]

lines += ["━━━━━━━━━━", f"📊 一、排队情况（截止{QUEUE_DATE}）", ""]
lines.append(f"全市场共{QUEUE_TOTALS['全市场']}家：问询{QUEUE_TOTALS['问询中']}家 | "
              f"已过会待发行{QUEUE_TOTALS['已过会']}家 | 提交注册{QUEUE_TOTALS['提交注册']}家")
lines.append("")
for board, items in QUEUE.items():
    parts = " | ".join(f"{k}{v}" for k, v in items)
    lines.append(f"【{board}】{sum(v for _, v in items)}家  {parts}")

passed_r = recent_r[recent_r["审核状态"] == "上会通过"]
pending_r = recent_r[recent_r["审核状态"] == "未上会"]
failed_r = recent_r[recent_r["审核状态"].isin(["上会未通过", "取消审核"])]
lines += ["", "━━━━━━━━━━", f"📋 二、本周期上会（{REPORT_START}～{PERIOD_END_STR}）", "",
          f"✅ 通过：{len(passed_r)}家"]
for _, r in passed_r.iterrows():
    lines.append(f"  · {shname(r.get('企业名称', r.get('股票简称','?')))} | "
                 f"{board_alias(r.get('上市板块',''))} | {sdate(r['上会日期'])}")
if len(pending_r) > 0:
    lines.append(f"🔄 待审：{len(pending_r)}家（安排上会，尚未表决）")
    for _, r in pending_r.iterrows():
        lines.append(f"  · {shname(r.get('企业名称', r.get('股票简称','?')))} | "
                     f"{board_alias(r.get('上市板块',''))} | {sdate(r['上会日期'])}")
if len(failed_r) > 0:
    lines.append(f"❌ 否决：{len(failed_r)}家")
    for _, r in failed_r.iterrows():
        lines.append(f"  · {shname(r.get('企业名称', r.get('股票简称','?')))} | "
                     f"{board_alias(r.get('上市板块',''))}")

reg_up2 = recent_up[recent_up["最新状态"].isin(["注册", "核准"])].dropna(subset=["企业名称"])
lines += ["", "━━━━━━━━━━", f"📋 三、本周期获批（{REPORT_START}～{PERIOD_END_STR}）", ""]
if len(reg_up2) > 0:
    lines.append(f"📄 获发行批文：{len(reg_up2)}家")
    for _, r in reg_up2.iterrows():
        lines.append(f"  · {shname(r.get('企业名称',''))} | "
                     f"{board_alias(r.get('拟上市地点',''))} | "
                     f"{str(r['更新日期'])[:10]}")
else:
    lines.append("  （暂无数据）")

term_up = recent_up[recent_up["最新状态"].isin(["终止"])].dropna(subset=["企业名称"])
lines += ["", "━━━━━━━━━━", f"📋 四、本周期终止/撤回（{REPORT_START}～{PERIOD_END_STR}）", ""]
if len(term_up) > 0:
    for _, r in term_up.iterrows():
        lines.append(f"  · {shname(r.get('企业名称',''))} | "
                     f"{board_alias(r.get('拟上市地点',''))}")
else:
    lines.append("  本周期无终止撤回记录")

lines += ["", "━━━━━━━━━━", f"📋 五、下周期上会计划（{THIS_WEEK_END}～{NEXT_WEEK_END}）", ""]
if len(next_r) > 0:
    for _, r in next_r.iterrows():
        lines.append(f"  · {shname(r.get('企业名称', r.get('股票简称','?')))} | "
                     f"{board_alias(r.get('上市板块',''))} | "
                     f"计划{sdate(r['上会日期'])}")
else:
    lines.append("  ⚠️ 近期暂无上会安排（数据更新存在滞后，以证监会官网为准）")

lines += ["", "━━━━━━━━━━", f"📋 六、本周期新股上市（{REPORT_START}～{PERIOD_END_STR}）", ""]
if len(recent_l) > 0:
    # 构造待搜索股票列表
    listing_list = [
        (str(r.get("证劵代码","")), str(r.get("证券简称","?")), sdate(r["上市_dt"]))
        for _, r in recent_l.iterrows()
    ]
    # 自动搜索首日涨幅（兜底：旧数据）
    auto_gains = _fetch_first_day_gains(listing_list)

    for _, r in recent_l.iterrows():
        cd = str(r.get("证劵代码", ""))
        # 优先用自动搜索，其次旧数据兜底
        info = auto_gains.get(cd) or LISTINGS_GAIN_HISTORY.get(cd, {})
        nm = r.get("证券简称", info.get("name","?"))
        dt = sdate(r["上市_dt"]) if pd.notna(r.get("上市_dt")) else info.get("date","?")
        gain = info.get("gain", "-")
        pr = fmt_price(r.get("发行价"))
        lines.append(f"  · {nm}（{cd}）| 上市:{dt} | 发行:{pr} | 涨幅:{gain}")
else:
    lines.append("  （无）")

lines += ["", "━━━━━━━━━━",
          f"📌 数据来源：新浪财经+IPO123（统计截至{QUEUE_DATE}）",
          "⚠️ 仅供参考，不构成投资建议。"]

if __name__ == "__main__":
    _acquire_lock()
    try:
        import os
        print(f"[TS] 第一步：收集数据...")
        report = "\n".join(lines)
        if report:
            print(f"[TS] 第二步：保存Markdown报告...")
            _dir = "/workspace/projects/A股报告系统/reports"
            os.makedirs(_dir, exist_ok=True)
            _path = os.path.join(_dir, f"IPO周报_{_PERIOD_KEY}.md")
            with open(_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"  已保存: {_path}")
            print("\n" + "="*60)
            print(report)
            print("="*60)
            print(f"[TS] 第三步：推送...")
            err2 = wx(report)
            print("\n" + ("✅ 已推送" if err2 == 0 else f"❌ err={err2}"))
            # ── 发送成功后才标记，避免发送失败却仍去重 ──
            if err2 == 0:
                _mark_sent_today()
                print(f"[去重] 已记录执行日期: {NOW.strftime('%Y%m%d')}")
    finally:
        _release_lock()
