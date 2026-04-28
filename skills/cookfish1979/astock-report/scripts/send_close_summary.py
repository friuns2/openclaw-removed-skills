#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A股收盘小结 2026-04-19"""
from datetime import datetime, timezone, timedelta
import json, subprocess, os, sys, socket, re, time, requests, pandas as pd
import urllib.request as _ur, json as _json

socket.setdefaulttimeout(8)
_TZ  = timedelta(hours=8)
_LOCK = "/tmp/a_stock_close_summary.lock"

if os.path.exists(_LOCK):
    print("[LOCK] 已有实例，退出。"); sys.exit(0)
open(_LOCK, "w").close()
def _unlock():
    try: os.remove(_LOCK)
    except: pass

# ── 微信推送 ────────────────────────────────────────────
def send_wx(msg):
    """微信推送：urllib POST（避免 subprocess curl 挂起）"""
    import urllib.parse, configparser
    ini = "/workspace/keys/wecom_webhook.ini"
    webhook_url = None
    if ini:
        cfg = configparser.ConfigParser()
        cfg.read(ini)
        for sec in cfg.sections():
            for k, v in cfg.items(sec):
                m = re.search(r'key\s*=\s*(.+)', f"{k}={v}")
                if m:
                    webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={m.group(1).strip()}"
                    break
    if not webhook_url:
        print("  ⚠️ 未找到 webhook URL"); return -1
    payload = _json.dumps({"msgtype": "text", "text": {"content": msg}}).encode("utf-8")
    req = _ur.Request(webhook_url,
                      data=payload,
                      headers={"Content-Type": "application/json"},
                      method="POST")
    try:
        with _ur.urlopen(req, timeout=10) as resp:
            result = resp.read().decode("utf-8", errors="replace")
        return _json.loads(result).get("errcode", -1)
    except Exception as e:
        print(f"  ⚠️ 推送异常: {e}"); return -1

# ── 六大指数（腾讯） ─────────────────────────────────────
def get_index_data():
    url = "https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000688,sh000300,sh000905"
    req = _ur.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with _ur.urlopen(req, timeout=8) as r:
        raw = r.read().decode("gbk", "replace")
    result = {}
    for line in raw.strip().split("\n"):
        parts = line.lstrip("v_").split("~")
        if len(parts) < 33: continue
        result[parts[2].strip()] = {"name": parts[1].strip(), "price": float(parts[3]), "pct": float(parts[32])}
    out = []
    for num, code, name in [
        ("000001","sh000001","上证指数"),("399001","sz399001","深证成指"),
        ("399006","sz399006","创业板指"),("000688","sh000688","科创50"),
        ("000300","sh000300","沪深300"),("000905","sh000905","中证500"),
    ]:
        d = dict(result.get(num, {}))
        d["code"] = code
        if "name" not in d: d["name"] = name
        out.append(d)
    return out

# ── 全市场成交额（腾讯，元→亿） ─────────────────────────
def get_market_total():
    url = "https://qt.gtimg.cn/q=sh000001,sz399001"
    req = __import__("urllib.request").request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with __import__("urllib.request").request.urlopen(req, timeout=8) as r:
        raw = r.read().decode("gbk", "replace")
    sh = sz = 0.0
    for ln in raw.strip().split("\n"):
        pts = ln.split("~")
        if len(pts) < 38: continue
        amt = float(pts[37]) / 1e4  # 元 → 亿
        if "000001" in pts[2]: sh = amt
        elif "399001" in pts[2]: sz = amt
    total = round(sh + sz, 0)
    print(f"  [全市场] {total:.0f}亿（沪{sh:.0f}+深{sz:.0f}）")
    return total

# ── 全市场市值（东方财富 gzfx 页面，固定值） ─────────────
TOTAL_WAN = 114.31   # 全市场总市值（万亿元）
CIRC_WAN  = 103.44   # 全市场流通市值（万亿元）

def get_market_cap():
    print(f"  [市值] 全市场总市值={TOTAL_WAN:.2f}万亿 流通市值={CIRC_WAN:.2f}万亿（沪深两市合计）")
    return CIRC_WAN

# ── IF期货升贴水（东方财富 push2delay 实时行情）─────────
def get_if_basis():
    """IF期货基差：push2delay 实时行情（已验证：secid=220.IFM）
    IF主连：f43÷10 ≈ 4696.6  CSI300：f43÷100 ≈ 4757.4"""
    def _fetch(url):
        try:
            req = _ur.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://futures.eastmoney.com/"
            })
            with _ur.urlopen(req, timeout=6) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            return None

    ut = "b2884a393a59ad64002292a3e90d46a5"
    d_if = _fetch(f"https://push2delay.eastmoney.com/api/qt/stock/get"
                  f"?secid=220.IFM&fields=f43,f45,f57,f58,f59,f60&ut={ut}")
    d_hs = _fetch(f"https://push2delay.eastmoney.com/api/qt/stock/get"
                  f"?secid=1.000300&fields=f43,f45,f57,f58,f59,f60&ut={ut}")

    if not d_if or not d_hs:
        print("[IF] push2delay 获取失败"); return None

    import json
    if_data = json.loads(d_if).get("data", {})
    hs_data = json.loads(d_hs).get("data", {})

    # IF主连：f43÷10 ≈ 4696.6  CSI300：f43÷100 ≈ 4757.4
    if_price = int(if_data.get("f43", 0)) / 10.0
    hs_price = int(hs_data.get("f43", 0)) / 100.0

    basis     = round(if_price - hs_price, 2)
    direction = "升水" if basis > 0 else "贴水"

    print(f"  [IF] IF={if_price:.2f} 沪深300={hs_price:.2f} 基差={basis:+.2f}点 ({direction})")
    return {
        "if_price": round(if_price, 2),
        "hs300_price": round(hs_price, 2),
        "basis": basis,
        "direction": direction
    }

# ── 概念板块（同花顺行业板块，失败则降级新浪行业） ─────────
def get_sector_data():
    import akshare as ak, pandas as pd
    # 方法1：同花顺行业板块（5秒超时）
    try:
        df = ak.stock_board_industry_summary_ths()
        if df is not None and len(df) > 5:
            df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
            df = df.dropna(subset=['涨跌幅']).sort_values('涨跌幅', ascending=False)
            gainers = [(r['板块'], round(float(r['涨跌幅']), 2)) for _, r in df.head(5).iterrows()]
            losers  = [(r['板块'], round(float(r['涨跌幅']), 2)) for _, r in df.tail(5).iloc[::-1].iterrows()]
            print(f"  [板块] 同花顺成功 涨幅前5: {gainers}")
            return gainers, losers
    except Exception as e:
        print(f"  [板块] 同花顺失败: {e}")
    # 方法2（降级）：新浪行业板块（5秒超时）
    try:
        df2 = ak.stock_sector_spot(indicator='新浪行业')
        if df2 is not None and len(df2) > 5:
            df2['涨跌幅'] = pd.to_numeric(df2['涨跌幅'], errors='coerce')
            df2 = df2.dropna(subset=['涨跌幅']).sort_values('涨跌幅', ascending=False)
            gainers = [(r['板块'], round(float(r['涨跌幅']), 2)) for _, r in df2.head(5).iterrows()]
            losers  = [(r['板块'], round(float(r['涨跌幅']), 2)) for _, r in df2.tail(5).iloc[::-1].iterrows()]
            print(f"  [板块] 新浪降级成功 涨幅前5: {gainers}")
            return gainers, losers
    except Exception as e:
        print(f"  [板块] 新浪降级也失败: {e}")
    return None, None

# ── 涨跌停家数 + 炸板率 ─────────────────────────────────
def get_zt_stats(trade_date):
    """
    涨停家数、跌停家数、炸板率。
    优先：本地 zt_data.db（已由东方财富 API 入库）
    降级：akshare 炸板池+涨停池，公式=炸板/(炸板+涨停)
    """
    import sqlite3
    db_path = "/workspace/projects/A股报告系统/data/zt_data.db"
    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT zt_count,zb_count,dt_count FROM zt_summary WHERE trade_date=?",
            (trade_date,)
        ).fetchone()
        conn.close()
        if row:
            zt, zb, dt = row
            exp_rate = round(zb / (zt + zb) * 100, 1) if zt + zb > 0 else 0.0
            print(f"  [涨跌停] 涨停={zt} 跌停={dt} 炸板率={exp_rate}%（本地DB）")
            return zt, dt, exp_rate
        else:
            print(f"  [涨跌停] DB无 {trade_date} 记录，降级akshare")
            raise FileNotFoundError("no db record")
    except Exception:
        try:
            import akshare as ak; import time as _time
            _time.sleep(1)
            # 炸板率 = 炸板池 / (炸板池 + 涨停池)
            df_zb = ak.stock_zt_pool_zbgc_em(date=trade_date)   # 炸板股池
            df_zt = ak.stock_zt_pool_em(date=trade_date)          # 涨停股池
            zb = len(df_zb)
            zn = len(df_zt)
            exp_rate = round(zb / (zb + zn) * 100, 1) if (zb + zn) > 0 else 0.0
            print(f"  [涨跌停] 涨停={zn} 炸板={zb} 炸板率={exp_rate}%（akshare 炸板池公式）")
            return zn, None, exp_rate
        except Exception as e2:
            print(f"  [涨跌停] ⚠️ {e2}"); return None, None, None

def _check_date_match(page_text, trade_date, label):
    """
    校验页面显示的「更新日期」是否与目标交易日匹配。
    trade_date: YYYYMMDD 格式字符串
    返回 (is_ok, date_in_page)。
    """
    import re
    # trade_date 格式化为 YYYY-MM-DD
    if len(trade_date) == 8 and trade_date.isdigit():
        td_fmt = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
    else:
        td_fmt = trade_date
    m = re.search(r'更新日期:?\s*(\d{4})[-/年]?(\d{2})[-/月]?(\d{2})', page_text)
    if not m:
        m = re.search(r'(\d{4})[-/](\d{2})[-/](\d{2})', page_text[:300])
    if m:
        page_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        if page_date == td_fmt:
            return True, page_date
        else:
            print(f"  [{label}] ⚠️ 页面日期={page_date}，目标={td_fmt}，不匹配 → 降级")
            return False, page_date
    print(f"  [{label}] 无法提取页面日期，跳过校验")
    return True, "无法提取"

# ── 主力净流入（全市场，fflow/daykline 端点）────────────
def get_main_net_flow(trade_date):
    """
    全市场主力净流入（日线，非分页累加）。
    接口: push2delay /api/qt/stock/fflow/daykline/get
    f52原始值=元，÷1亿得亿元。
    正常范围约 [-300, +300] 亿元。
    """
    try:
        import requests, json, time, re
        url = "https://push2delay.eastmoney.com/api/qt/stock/fflow/daykline/get"
        params = {
            "lmt": "0", "klt": "101",
            "secid": "1.000001", "secid2": "0.399001",
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "_": int(time.time() * 1000)
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://data.eastmoney.com/"
        }
        r = requests.get(url, params=params, headers=headers, timeout=10)
        text = re.sub(r'^jQuery\d+_\d+\(', '', r.text.rstrip(');'))
        d = json.loads(text)
        klines = d.get("data", {}).get("klines", [])
        if not klines:
            print("  [主力净流入] 无数据"); return None
        latest = klines[-1].split(",")
        # 原始值 f52 = 元，÷1亿得亿元
        net_yi = round(float(latest[1]) / 1e8, 2)
        san_yi  = round(float(latest[2]) / 1e8, 2)
        zhong_yi = round(float(latest[3]) / 1e8, 2)
        da_yi   = round(float(latest[4]) / 1e8, 2)
        chao_yi = round(float(latest[5]) / 1e8, 2)
        print(f"  [主力净流入] {latest[0]}  主力净流入={net_yi:+.2f}亿")
        print(f"    散户={san_yi:+.2f}亿  中单={zhong_yi:+.2f}亿  大单={da_yi:+.2f}亿  超大单={chao_yi:+.2f}亿")
        # 合理性检查
        if abs(net_yi) > 500:
            print(f"  ⚠️ 数值{net_yi}亿元异常（>{500}亿），重置为0")
            return 0.0
        return net_yi
    except Exception as e:
        print(f"  [主力净流入] ⚠️ {e}"); return None

# ── 打分辅助 ─────────────────────────────────────────────
def _sc(v, lo, hi):
    """标准化到0-100分（lo=0分基准，hi=满分基准）"""
    if v is None: return None
    return round(max(0, min(1, (v - lo) / (hi - lo))) * 100)

def build_report(indices, zn, dn, exp_rate, net_flow, turnover,
                 if_basis, market_total,
                 ind_gainers=None, ind_losers=None,
                 date_str="???"):
    # ── 六因子各自标准化到0-100 ───────────────────────────
    # ①涨停家数：10家=0分，100家=100分
    s_zt    = _sc(zn,       10,  100) if zn         else None
    # ②涨跌停比：0=0分，50倍=100分
    zt_ratio = round(zn / max(dn, 1), 1) if (zn and dn) else None
    s_ratio  = _sc(zt_ratio,  0,   50) if zt_ratio   else None
    # ③IF基差点数：-300点=0分，+150点=100分（线性）
    basis_val = (if_basis["basis"] if if_basis else None)
    s_if = (round(max(0, min(1, (basis_val - (-300)) / (150 - (-300)))) * 100)
             ) if basis_val is not None else None
    # ④主力净流入占比：<-5%=0分，>5%=100分（线性过零点）
    if net_flow is not None and market_total and market_total > 0:
        main_ratio_pct = net_flow / market_total * 100
        s_main = _sc(main_ratio_pct,  -5,  5)
    else:
        main_ratio_pct = None; s_main = None
    # ⑤炸板率：>40%=0分，<10%=100分（越低越好）
    s_exp   = _sc(exp_rate,  40,  10) if exp_rate   else None
    # ⑥换手率：<1%=0分，>4%=100分
    s_turn  = _sc(turnover,   1,   4) if turnover    else None

    # 取平均值（因子排序：①涨停 ②涨跌停比 ⑤炸板率 ④主力净流入 ⑥换手率 ③IF基差）
    parts = [v for v in [s_zt, s_ratio, s_exp, s_main, s_turn, s_if] if v is not None]
    avg = round(sum(parts) / len(parts)) if parts else 0
    tag = "🟢做多" if avg >= 75 else "🟡偏多" if avg >= 55 else "⚪分歧" if avg >= 40 else "🟠偏空谨慎" if avg >= 25 else "🔴冰点"

    ib = if_basis
    if_str = (f"IF期货信号：IF={ib['if_price']:.1f}，基差{ib['basis']:+.1f}点") if ib else "IF期货信号：⚠️暂缺"

    # 打分明细（因子排序：①涨停 ②涨跌停比 ⑤炸板率 ④主力净流入 ⑥换手率 ③IF基差）
    calc = []
    if s_zt is not None:
        calc.append(f"• 涨停家数 → {int(s_zt)}分（涨停{zn}家，10家起算）")
    if s_ratio is not None:
        calc.append(f"• 涨跌停比 → {int(s_ratio)}分（涨跌停比{zt_ratio}倍，50倍满分）")
    if s_exp is not None:
        calc.append(f"• 炸板率 → {int(s_exp)}分（{exp_rate}%，区间40%~10%映射，越低越好）")
    if s_main is not None and main_ratio_pct is not None:
        calc.append(f"• 主力净流入占比 → {int(s_main)}分（{main_ratio_pct:.1f}%，区间-5%~+5%映射）")
    if s_turn is not None:
        calc.append(f"• 全市场换手率 → {int(s_turn)}分（换手率{turnover:.2f}%，区间1%~4%映射）")
    if ib:
        calc.append(f"• IF基差 → {int(s_if)}分（基差{ib['basis']:+.2f}点，区间-300~+150点映射）")

    gainers_block = ("  🔺 涨幅前5：\n" + "\n".join(f"    · {item[0]}{item[1]:+.2f}%" for item in (ind_gainers or [])[:5])) if ind_gainers else "  🔺 涨幅前5：⚠️暂缺"
    losers_block  = ("  🟢 跌幅前5：\n" + "\n".join(f"    · {item[0]}{item[1]:+.2f}%" for item in (ind_losers  or [])[:5])) if ind_losers  else "  🟢 跌幅前5：⚠️暂缺"

    return f"""📊 【A股收盘小结】{date_str}

━━━ 一，主要股指表现 ━━━
{chr(10).join(f'• {d["name"]}：{d["price"]:.2f}，{"↑" if d["pct"] >= 0 else "↓"}{abs(d["pct"]):.2f}%' for d in indices)}
全市场成交额：{market_total:.0f}亿
{if_str}

━━━ 二，板块行情 ━━━
{gainers_block}
{losers_block}

━━━ 三，量化情绪打分 ━━━
{chr(10).join(calc)}
━━━━━━━━━━━
综合评分：{avg}/100 {tag}

━━━ 四，后市展望 ━━━
市场震荡调整，风格偏向题材与成长，建议控制仓位、关注轮动节奏。
━━━ 数据来源：腾讯财经·东方财富·同花顺 ━━━
⚠️ 仅供参考，不构成投资建议。股市有风险，投资需谨慎。"""

# ── 主程序 ─────────────────────────────────────────────
if __name__ == "__main__":
    import signal
    def _sig_handler(signum, frame): _unlock(); print("全局超时，强制退出"); sys.exit(0)
    signal.signal(signal.SIGALRM, _sig_handler)
    signal.alarm(100)   # 100秒硬性全局超时，防止任意API挂死

    try:
        now_local = datetime.now(timezone.utc) + _TZ
        print(f"[{now_local.strftime('%H:%M:%M')}] 开始...")

        # 最近交易日（向前倒找）
        trade_date = None
        for d in range(8):
            td = (now_local - timedelta(days=d)).strftime("%Y%m%d")
            wd = (now_local - timedelta(days=d)).weekday()
            if wd < 5:
                trade_date = td
                break
        if not trade_date:
            print("⚠️ 未找到最近交易日"); sys.exit(1)
        print(f"  [日期] 数据交易日：{trade_date}（周{['','一','二','三','四','五','六'][wd]}）")

        indices      = get_index_data()
        market_total = get_market_total()
        circ_wan     = get_market_cap()
        turnover     = round(market_total / (circ_wan * 10000) * 100, 2) if circ_wan else None
        print(f"  [换手率] {turnover:.2f}%" if turnover else "  [换手率] ⚠️")
        if_basis    = get_if_basis()
        ind_gainers, ind_losers = get_sector_data()

        # 涨停/跌停/炸板率（Playwright优先，东财页面直接读炸板率）
        zn, dt_n, exp_rate = get_zt_stats(trade_date)

        # 主力净流入
        net_flow = get_main_net_flow(trade_date)

        # 报告日期标题（取最近交易日）
        date_str = (datetime.strptime(trade_date, "%Y%m%d") + _TZ).strftime("%Y年%m月%d日")

        report = build_report(
            indices,
            zn=zn, dn=dt_n, exp_rate=exp_rate,
            net_flow=net_flow, turnover=turnover,
            if_basis=if_basis,
            market_total=market_total,
            ind_gainers=ind_gainers,
            ind_losers=ind_losers,
            date_str=date_str,
        )

        print("\n" + "=" * 50)
        print(report)
        print("=" * 50)

        err = send_wx(report)
        if err == 0:
            print(f"\n✅ 推送成功")
        else:
            print(f"\n❌ 推送失败 (errcode={err})")
    finally:
        _unlock()
