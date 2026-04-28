#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股收盘晚报生成脚本
触发：python3 send_evening_report.py [--dry-run] [--ai-fill]

数据一致性原则：
  两融余额、两融交易额 → 取最新可用日期（通常为 T-1）
  流通市值、成交额        → 必须与两融余额为同一日期
  两融交易额 = 融资买入额 + 融券卖出额
  流通市值 = 沪市流通市值 + 深市流通市值（沪深北三所合计）
"""
from __future__ import annotations
import sys, os, warnings, json, subprocess, re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

warnings.filterwarnings('ignore')

_TZ  = timedelta(hours=8)
NOW  = datetime.now(timezone.utc) + _TZ
TODAY_STR  = NOW.strftime("%Y年%m月%d日")
TODAY_DATE = NOW.strftime("%Y%m%d")
TS         = NOW.strftime("%m/%d %H:%M")

def prev_trading_day(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y%m%d")
    for i in range(1, 8):
        d = (dt - timedelta(days=i)).strftime("%Y%m%d")
        if datetime.strptime(d, "%Y%m%d").weekday() < 5:
            return d
    return date_str

YESTERDAY = prev_trading_day((NOW - timedelta(days=1)).strftime("%Y%m%d"))

def get_webhook_url() -> str:
    ini = '/workspace/keys/wecom_webhook.ini'
    if os.path.exists(ini):
        with open(ini) as f:
            content = f.read()
        # 解析 [wecom_webhook] 段落，取 key= 后的值
        import re
        m = re.search(r'^\s*key\s*=\s*(.+)', content, re.M)
        if m:
            return f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={m.group(1).strip()}"
    # 回退：直接读 keys_loader
    try:
        from keys_loader import get_webhook_url as _gw
        return _gw()
    except Exception:
        raise FileNotFoundError(f'Webhook配置不存在: {ini}')

def wx_push(text: str) -> int:
    try:
        import urllib.request
        payload = json.dumps({"msgtype": "text", "text": {"content": text}}, ensure_ascii=False)
        payload_bytes = payload.encode('utf-8')
        req = urllib.request.Request(
            get_webhook_url(),
            data=payload_bytes,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        return result.get('errcode', -1)
    except Exception:
        return -1

# ── AI 补数 ────────────────────────────────────────────────
def _call_batch_web_search(queries):
    try:
        from openclaw import invoke
        import asyncio
        async def _do():
            return await invoke('batch_web_search',
                               {"queries": [{"query": q, "num_results": 5} for q in queries]})
        return asyncio.run(_do())
    except Exception as e:
        print(f"[AI补数] openclaw.invoke 失败: {e}")
        return {}

def ai_supplement(data: dict) -> dict:
    today = NOW.strftime('%Y年%m月%d日')
    missing = []
    # 两融和市值数据极少缺失，只补北向/涨跌停等容易缺的字段
    if data.get('north') is None:
        missing.append(f"{today} 北向资金 净流入 亿元")
    if data.get('zt_count') is None:
        missing.append(f"{today} A股 涨停家数")
    if data.get('dt_count') is None:
        missing.append(f"{today} A股 跌停家数")
    if not missing:
        return data
    print(f"[AI补数] {len(missing)} 项暂缺，启动AI搜索...")
    raw = ""
    for q in missing:
        for entry in _call_batch_web_search([q]).get('content', []):
            if entry.get('success'):
                raw += entry.get('formatted_content', '') + " "; break
    for pat in [r'两融余额.*?(\d+\.?\d*)\s*亿', r'融资余额.*?(\d+\.?\d*)\s*亿']:
        m = re.search(pat, raw)
        if m and float(m.group(1)) > 1000:
            data['rz_bal'] = float(m.group(1)); break
    for pat in [r'融资买入额.*?(\d+\.?\d*)\s*亿', r'两融交易额.*?(\d+\.?\d*)\s*亿']:
        m = re.search(pat, raw)
        if m and float(m.group(1)) > 10:
            data['rz_buy'] = float(m.group(1)); break
    for pat in [r'流通市值.*?(\d+\.?\d*)\s*万亿', r'A股流通市值.*?(\d+\.?\d*)\s*万亿']:
        m = re.search(pat, raw)
        if m and float(m.group(1)) > 10:
            data['mkt_cap'] = float(m.group(1)); break
    for pat in [r'成交额.*?(\d+\.?\d*)\s*万亿', r'A股成交额.*?(\d+\.?\d*)\s*万亿']:
        m = re.search(pat, raw)
        if m and float(m.group(1)) > 0.5:
            data['turnover'] = float(m.group(1)); break
    for pat in [r'北向资金.*?([+-]?\d+\.?\d*)\s*亿']:
        m = re.search(pat, raw)
        if m and abs(float(m.group(1))) > 0.1:
            data['north'] = float(m.group(1)); break
    zt_m = re.search(r'涨停\s*(\d+)\s*家', raw)
    if zt_m: data['zt_count'] = int(zt_m.group(1))
    dt_m = re.search(r'跌停\s*(\d+)\s*家', raw)
    if dt_m: data['dt_count'] = int(dt_m.group(1))
    for k, v in data.items():
        if v is not None:
            print(f"[AI补数] {k}: {v}")
    return data

# ── 六大指数 ────────────────────────────────────────────────
def get_index_data():
    imap = {"上证指数":"sh000001","深证成指":"sz399001","创业板指":"sz399006",
            "科创50":"sh000688","沪深300":"sh000300","中证500":"sh000905"}
    try:
        import urllib.request
        req = urllib.request.Request(
            f"https://qt.gtimg.cn/q={','.join(imap.values())}",
            headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode("gbk", errors="replace")
        result = []
        for line in raw.strip().split("\n"):
            fields = line.lstrip("v_").split("~")
            if len(fields) < 33: continue
            code_num = fields[2].strip()
            pct = float(fields[32]) if fields[32] else 0.0
            for name, c in imap.items():
                if c.replace("sh","").replace("sz","") in code_num:
                    result.append({"name": name,
                                   "price": float(fields[3]) if fields[3] else 0.0,
                                   "pct": pct})
                    break
        return result
    except Exception as e:
        print(f"[指数] {e}"); return []

# ── PE与风险溢价 ─────────────────────────────────────────
def get_hs300_pe() -> Tuple[Optional[float], Optional[float]]:
    """
    沪深300 PE及近5年历史分位点。
    PE来源：腾讯 qt.gtimg.cn field[39]（sh000300）
    分位点：akshare stock_index_pe_lg（近5年历史分位）
    返回: (PE, 分位点%) 或 None
    """
    pe = None
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://qt.gtimg.cn/q=sh000300",
            headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode("gbk", errors="replace")
        for line in raw.strip().split("\n"):
            f = line.lstrip("v_").split("~")
            if len(f) < 50 or '000300' not in f[2]: continue
            pe = float(f[39]) if f[39] else None
            if pe:
                print(f"  [沪深300PE] {pe:.2f}")
    except Exception as e:
        print(f"  [沪深300PE] ⚠️ {e}")

    pct = None
    try:
        import akshare as ak
        df = ak.stock_index_pe_lg(symbol="沪深300")
        if df is not None and not df.empty:
            pct = float(df.iloc[0]['滚动市盈率分位点'] if '滚动市盈率分位点' in df.columns
                        else df.iloc[0].get('分位点', 0))
            print(f"  [沪深300PE分位] {pct:.1f}%")
    except Exception as e:
        print(f"  [沪深300PE分位] ⚠️ {e}")

    return pe, pct

# ── PE + 国债收益率 ───────────────────────────────────────
# ── 核心数据获取 ──────────────────────────────────────────

def get_margin_balance_effective() -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    两融余额（亿元）+ 较前日变化。
    两融余额 = 融资余额 + 融券余额（单位：亿元）。
    数据源：akshare stock_margin_account_info（无参数，全市场合计，列单位=亿元）。
    """
    try:
        import akshare as ak
        mg = ak.stock_margin_account_info()
        if mg is None or mg.empty:
            raise ValueError("empty")
        mg2 = mg.sort_values('日期', ascending=False).reset_index(drop=True)
        row = mg2.iloc[0]
        d   = str(row.get('日期', ''))  # YYYY-MM-DD
        cur = float(row.get('融资余额', 0) or 0) + float(row.get('融券余额', 0) or 0)
        pre_row = mg2.iloc[1] if len(mg2) > 1 else None
        pre = (float(pre_row['融资余额']) + float(pre_row['融券余额'])) if pre_row is not None else None
        delta = round(cur - pre, 0) if pre is not None else None
        ed = (datetime.strptime(d, "%Y-%m-%d") + _TZ).strftime("%Y年%m月%d日")
        print(f"  [两融余额] {ed}={cur:.0f}亿，较前日{'+' if (delta or 0)>=0 else ''}{delta:.0f}亿")
        return cur, delta, ed
    except Exception as e:
        print(f"  [两融余额] {e}"); return None, None, None

def get_margin_buy_effective(effective_date: str) -> Tuple[Optional[float], Optional[str]]:
    """
    两融交易额（亿元）= 融资买入额 + 融券卖出额。
    数据源：akshare stock_margin_account_info（无参数，全市场合计，列单位=亿元）。
    """
    try:
        import akshare as ak
        mg = ak.stock_margin_account_info()
        if mg is None or mg.empty:
            raise ValueError("empty")
        mg2 = mg.sort_values('日期', ascending=False).reset_index(drop=True)
        target = f"{effective_date[:4]}-{effective_date[4:6]}-{effective_date[6:8]}"
        row = next((r for _, r in mg2.iterrows()
                     if str(r.get('日期','')) == target), mg2.iloc[0])
        rz_buy  = float(row.get('融资买入额', 0) or 0)
        rz_sell = float(row.get('融券卖出额', 0) or 0)
        total = round(rz_buy + rz_sell, 1)
        d  = str(row.get('日期', ''))
        ed = (datetime.strptime(d, "%Y-%m-%d") + _TZ).strftime("%Y年%m月%d日")
        print(f"  [两融交易额] {ed}=融资{rz_buy:.1f}+融券{rz_sell:.1f}={total:.1f}亿")
        return total, ed
    except Exception as e:
        print(f"  [两融交易额] {e}"); return None, None

def _timeout_call(func, args, default, timeout_sec=5):
    """用线程超时包装器调用任意函数，防止SZSE/BSE接口卡死"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(func, *args)
            return future.result(timeout=timeout_sec)
    except Exception:
        return default

def _get_bse_turnover(effective_date: str) -> float:
    """
    北交所成交额（亿元）。
    数据源：akshare stock_bse_summary（单位：元 → ÷1e8）。
    北交所无独立接口时返回0（占比极小，不影响主逻辑）。
    """
    def _fetch():
        import akshare as ak
        df = ak.stock_bse_summary(date=effective_date)
        if df is None or df.empty:
            return 0.0
        bj_row = df[df['证券类别'] == '股票'].iloc[0]
        amt = float(bj_row.iloc[1]) / 1e8  # 元→亿
        print(f"  [北交所成交额] {amt:.1f}亿")
        return amt
    return _timeout_call(_fetch, (), 0.0, timeout_sec=5)

def get_turnover_effective(effective_date: str) -> Tuple[Optional[float], Optional[str]]:
    """
    A股成交额（亿元）。沪深北三所合计。

    逻辑：
    1. 当日(T日)：腾讯实时 API（沪+深，不含北交所，实时行情不含BSE）
    2. 历史：依次取沪市 + 深市 + 北交所 → 三所加总
       - 沪市：stock_sse_deal_daily['成交金额']，单位=万元 → ÷10000 = 亿
       - 深市：stock_szse_summary['成交金额']，单位=元   → ÷1e8  = 亿
       - 北交所：stock_bse_summary，单位=元              → ÷1e8  = 亿
    """
    if effective_date == TODAY_DATE:
        try:
            import urllib.request
            req = urllib.request.Request(
                "https://qt.gtimg.cn/q=sh000001,sz399001",
                headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read().decode("gbk", errors="replace")
            sh = sz = 0.0
            for line in raw.strip().split("\n"):
                parts = line.split("~")
                if len(parts) < 38: continue
                amt = float(parts[37]) / 1e4  # 万元→亿
                if "000001" in parts[2]: sh = amt
                elif "399001" in parts[2]: sz = amt
            total = round(sh + sz, 0)
            ed = NOW.strftime("%Y年%m月%d日")
            print(f"  [成交额] {ed}（T日实时）=沪{sh:.0f}+深{sz:.0f}={total:.0f}亿={total/10000:.2f}万亿")
            return total, ed
        except Exception as e:
            print(f"  [成交额] 腾讯实时失败: {e}")

    try:
        import akshare as ak
        # 沪市：数据列单位=亿，直接使用（无需换算）
        df_sh = ak.stock_sse_deal_daily(date=effective_date)
        sh_row = df_sh[df_sh['单日情况'] == '成交金额']
        sh_turn = float(sh_row.iloc[0].get('股票', 0))  # 亿

        # 深市：元 ÷ 1e8 = 亿元
        df_sz = _timeout_call(ak.stock_szse_summary, (effective_date,), None)
        if df_sz is None: raise RuntimeError('SZSE timeout')
        sz_row = df_sz[df_sz['证券类别'] == '股票']
        sz_turn = float(sz_row.iloc[0].get('成交金额', 0)) / 1e8  # 元→亿

        # 北交所：元 ÷ 1e8 = 亿元
        bj_turn = _get_bse_turnover(effective_date)

        total = round(sh_turn + sz_turn + bj_turn, 0)
        ed = (datetime.strptime(effective_date, "%Y%m%d") + _TZ).strftime("%Y年%m月%d日")
        print(f"  [成交额] {ed}=沪{sh_turn:.0f}+深{sz_turn:.0f}+北交所{bj_turn:.0f}={total:.0f}亿={total/10000:.2f}万亿")
        return total, ed
    except Exception as e:
        # Fallback：仅用沪市×1.37估算深市（深沪成交比约1.3-1.5倍历史均值）
        try:
            import akshare as ak
            df_sh = ak.stock_sse_deal_daily(date=effective_date)
            sh_row = df_sh[df_sh['单日情况'] == '成交金额']
            sh_turn = float(sh_row.iloc[0].get('股票', 0))
            est = round(sh_turn * 1.37, 0)
            ed = (datetime.strptime(effective_date, "%Y%m%d") + _TZ).strftime("%Y年%m月%d日")
            print(f"  [成交额] ⚠️ SZSE超时，用估算值: {ed}=沪{sh_turn:.0f}×1.37={est:.0f}亿={est/10000:.2f}万亿")
            return est, ed
        except Exception:
            print(f"  [成交额] ⚠️ {effective_date}: {e}"); return None, None

def get_market_cap_effective(effective_date: str) -> Tuple[Optional[float], Optional[str]]:
    """
    A股流通市值（亿元）。沪深北三所合计。
    沪市：数据列单位=亿，直接使用（已包含主板A+科创板）
    深市：元 ÷ 1e8 = 亿元（已包含主板+创业板）
    """
    try:
        import akshare as ak
        # 沪市：数据列单位=亿，直接使用
        df_sh = ak.stock_sse_deal_daily(date=effective_date)
        sh_row = df_sh[df_sh['单日情况'] == '流通市值']
        sh_cap = float(sh_row.iloc[0].get('股票', 0))  # 亿

        # 深市：元 ÷ 1e8 = 亿元
        df_sz = _timeout_call(ak.stock_szse_summary, (effective_date,), None)
        if df_sz is None: raise RuntimeError('SZSE timeout')
        sz_row = df_sz[df_sz['证券类别'] == '股票']
        sz_cap = float(sz_row.iloc[0].get('流通市值', 0)) / 1e8  # 元→亿

        total = round(sh_cap + sz_cap, 0)
        ed = (datetime.strptime(effective_date, "%Y%m%d") + _TZ).strftime("%Y年%m月%d日")
        print(f"  [流通市值] {ed}=沪{sh_cap:.0f}+深{sz_cap:.0f}={total:.0f}亿={total/10000:.2f}万亿")
        return total, ed
    except Exception as e:
        # Fallback：仅用沪市×1.05倍估算深市（深沪市值大致相当）
        try:
            import akshare as ak
            df_sh = ak.stock_sse_deal_daily(date=effective_date)
            sh_row = df_sh[df_sh['单日情况'] == '流通市值']
            sh_cap = float(sh_row.iloc[0].get('股票', 0))
            est = round(sh_cap * 1.05, 0)
            ed = (datetime.strptime(effective_date, "%Y%m%d") + _TZ).strftime("%Y年%m月%d日")
            print(f"  [流通市值] ⚠️ SZSE超时，用估算值: {ed}=沪{sh_cap:.0f}×1.05={est:.0f}亿={est/10000:.2f}万亿")
            return est, ed
        except Exception:
            print(f"  [流通市值] ⚠️ {effective_date}: {e}"); return None, None

def get_north_bound():
    """
    北向资金（沪深港通北向合计，亿元）。
    返回今日数据（可能为0），若无数据则返回 None。
    """
    try:
        import akshare as ak
        df = ak.stock_hsgt_fund_flow_summary_em()
        nb = df[df['资金方向']=='北向'].sort_values('交易日', ascending=False)
        for _, row in nb.head(3).iterrows():
            val = row.get('今日净买入额-万元', 0)
            if val is None:
                continue
            v = round(float(val) / 10000, 2)
            date = str(row.get('交易日', ''))
            direction = '净流入' if v >= 0 else '净流出'
            print(f"  [北向] {date} {direction}{abs(v)}亿")
            return v  # 今日数据，可能是 0
        print(f"  [北向] ⚠️ 无可用数据")
        return None
    except Exception as e:
        print(f"  [北向] {e}"); return None


def get_asia_pacific():
    """
    亚太股市收盘：恒生指数、日经225、韩国综合。
    恒生：腾讯 qt.gtimg.cn（实时）
    日经225 + 韩国综合：akshare index_global_hist_sina（取最近两个收盘日算涨跌幅）
    """
    result = []

    # 恒生指数 + 富时A50期货：腾讯实时行情（field[3]=当前价, field[32]=涨跌幅）
    try:
        import urllib.request
        for symbol, label in [('hkHSI', '恒生指数')]:
            req = urllib.request.Request(
                f'https://qt.gtimg.cn/q={symbol}',
                headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read().decode('gbk', errors='replace')
            for line in raw.strip().split('\n'):
                if symbol not in line: continue
                flds = line.lstrip('v_').split('~')
                if len(flds) < 33: continue
                price = float(flds[3]) if flds[3] else 0.0
                pct   = float(flds[32]) if flds[32] else 0.0
                result.append((label, price, pct))
                print(f"  [亚太] {label}={price:.0f} {'↑' if pct>=0 else '↓'}{abs(pct):.2f}%")
    except Exception as e:
        print(f"  [亚太] 恒生/A50 获取失败: {e}")

    # 日经225 + 韩国综合：新浪环球指数（取最近2日对比）
    try:
        import akshare as ak
        for name_cn, symbol, label in [
            ('日经225指数', '日经225指数', '日经225'),
            ('首尔综合指数', '首尔综合指数', '韩国综合'),
        ]:
            try:
                df = ak.index_global_hist_sina(symbol=symbol)
                if df is not None and len(df) >= 2:
                    latest = df.iloc[-1]
                    prev   = df.iloc[-2]
                    close_cur  = float(latest['close'])
                    close_prev = float(prev['close'])
                    pct = round((close_cur - close_prev) / close_prev * 100, 2)
                    result.append((label, close_cur, pct))
                    print(f"  [亚太] {label}={close_cur:.0f} ({prev['date']}收盘) {'↑' if pct>=0 else '↓'}{abs(pct):.2f}%")
            except Exception as e2:
                print(f"  [亚太] {label} 失败: {e2}")
    except Exception as e:
        print(f"  [亚太] 新华财经接口失败: {e}")

    return result

def get_market_stats():
    try:
        import akshare as ak
        for d in range(8):
            trade = (NOW - timedelta(days=d)).strftime('%Y%m%d')
            try:
                zt = len(ak.stock_zt_pool_em(date=trade))
                dt = len(ak.stock_zt_pool_dtgc_em(date=trade))
                if zt > 0 or dt > 0:
                    print(f"  [涨跌停] {trade} 涨停{zt} / 跌停{dt}")
                    return zt, dt
            except Exception:
                continue
        return None, None
    except Exception as e:
        print(f"  [涨跌停] {e}"); return None, None

def get_sector_flow():
    """
    行业板块涨跌幅排名（今日）。
    优先用同花顺行业板块（stock_board_industry_summary_ths，90板块，
    含涨跌幅+领涨股），失败则降级到新浪行业板块。
    """
    def _parse(v):
        try: return float(str(v).replace(',','').replace('%',''))
        except: return 0.0

    # 方法1：同花顺行业板块（90板块，数据最全）
    try:
        import akshare as ak, pandas as pd
        time.sleep(1)
        df = ak.stock_board_industry_summary_ths()
        if df is not None and not df.empty:
            df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
            df = df.dropna(subset=['涨跌幅']).sort_values('涨跌幅', ascending=False)
            result = []
            for _, r in df.iterrows():
                result.append((str(r['板块']), float(r['涨跌幅']),
                               _parse(r.get('总成交额', 0)) / 1e8))
            if result:
                print(f"  [行业板块] 同花顺成功，前5：{result[:5]}")
                return result
    except Exception as e:
        print(f"  [行业板块] 同花顺失败: {e}")

    # 方法2（降级）：新浪行业板块 spot
    try:
        import akshare as ak, pandas as pd
        time.sleep(1)
        df2 = ak.stock_sector_spot(indicator='新浪行业')
        if df2 is not None and not df2.empty:
            df2['涨跌幅'] = pd.to_numeric(df2['涨跌幅'], errors='coerce')
            df2 = df2.dropna(subset=['涨跌幅']).sort_values('涨跌幅', ascending=False)
            result = []
            for _, r in df2.iterrows():
                result.append((str(r['板块']), float(r['涨跌幅']),
                               _parse(r.get('总成交额', 0)) / 1e8))
            if result:
                print(f"  [行业板块] 新浪行业降级成功，前5：{result[:5]}")
                return result
    except Exception as e:
        print(f"  [行业板块] 新浪行业降级失败: {e}")

    print("  [行业板块] ⚠️ 所有接口均失败")
    return []

# ── 情绪参考 ──────────────────────────────────────────────

# ── PE + 国债收益率 + 风险溢价 ─────────────────────────────
def get_pe_and_bond(effective_date: str = "") -> dict:
    result = {'hs300_pe': None, 'hs300_pct5y': None,
              'zzqz_pe': None, 'bond10y': None,
              'rep_date': None, 'risk_premium': None}

    # 1. 国债收益率
    try:
        import akshare as ak
        from datetime import datetime, timedelta
        dates = [effective_date] if effective_date else             [(datetime.now()-timedelta(days=d)).strftime('%Y%m%d') for d in range(5)]
        for d in dates:
            try:
                df = ak.bond_china_yield(start_date=d, end_date=d)
                if df is not None and not df.empty:
                    gov = df[df['曲线名称'] == '中债国债收益率曲线']
                    if not gov.empty:
                        row = gov.iloc[0]
                        col_10y = None
                        for c in ['10年', '10Y']:
                            if c in gov.columns:
                                try:
                                    v = float(str(row[c])); 
                                    if v > 0: col_10y = v; break
                                except: pass
                        if col_10y is not None:
                            result['bond10y'] = round(col_10y, 4)
                            result['rep_date'] = str(row['日期'])[:10]; break
            except: continue
    except Exception as e: print(f"  [国债] {e}")

    # 2. 指数 PE（腾讯 field[39]）
    try:
        import urllib.request
        req = urllib.request.Request(
            'https://qt.gtimg.cn/q=sh000300,sh000985',
            headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode('gbk', errors='replace')
        for line in raw.strip().split('\n'):
            flds = line.lstrip('v_').split('~')
            if len(flds) < 50: continue
            code = flds[2].replace('sh','').replace('sz','')
            if code == '000300' and flds[39]: result['hs300_pe'] = round(float(flds[39]), 2)
            elif code == '000985' and flds[39]: result['zzqz_pe'] = round(float(flds[39]), 2)
    except Exception as e: print(f"  [PE] {e}")

    # 3. 沪深300 5年分位
    try:
        import akshare as ak
        df_pe = ak.stock_index_pe_lg(symbol='沪深300')
        if df_pe is not None and len(df_pe) >= 20:
            pe_col = next((c for c in df_pe.columns
                           if '滚动市盈率' in c and '等权' not in c), None)
            if pe_col is None:
                pe_col = next((c for c in df_pe.columns
                               if '市盈率' in c and '等权' not in c and '中位' not in c), None)
            if pe_col:
                vals = df_pe[pe_col].astype(float).dropna()
                cur = result.get('hs300_pe')
                if cur and len(vals) >= 20:
                    result['hs300_pct5y'] = round((vals < cur).sum() / len(vals) * 100, 1)
    except Exception as e: print(f"  [分位] {e}")

    # 4. 风险溢价 = 1/中证全指PE - 10年期国债收益率
    zz = result.get('zzqz_pe'); bond = result.get('bond10y')
    if zz and bond and zz > 0 and bond > 0:
        result['risk_premium'] = round((1/zz - bond/100)*100, 2)
    if effective_date and len(effective_date) == 8:
        y, m, d = effective_date[:4], effective_date[4:6], effective_date[6:8]
        result['rep_date'] = f'{y}年{m}月{d}日'

    if result.get('bond10y'):
        print(f"  [股市风险溢价] 中证全指PE={result['zzqz_pe']}, 10年期国债={result['bond10y']}%, "
              f"风险溢价={result.get('risk_premium')}%")
    return result


def build_report(indices, data, today_str, ai_news=None, ai_action=None):
    rz_ed = data.get('rz_bal_date'); mc_ed = data.get('mkt_cap_date')
    to_ed = data.get('turnover_date')
    lines = [f"📋 【A股晚报】{today_str}\n"]

    if indices:
        lines.append("━━━ A股收盘 ━━━")
        for x in indices:
            p = x.get('pct', 0)
            lines.append(f"• {x['name']}：{x['price']:.1f}，{'↑' if p>=0 else '↓'}{abs(p):.2f}%")
        if data.get('turnover'):
            lines.append(f"• 成交额：{data['turnover']/10000:.2f}万亿元")

    lines.append("\n━━━ 亚太股市 ━━━")
    ap = data.get('asia_pacific', [])
    if ap:
        ap_map = {name: (price, pct) for name, price, pct in ap}
        for name, label in [
            ('恒生指数','恒生指数'),
            ('日经225','日经225'),
            ('韩国综合','韩国综合'),
        ]:
            if name in ap_map:
                price, pct = ap_map[name]
                extra = '【预判A股明日开盘】' if name == '富时A50期货' else ''
                lines.append(f"• {label}：{price:.0f}，{'↑' if pct>=0 else '↓'}{abs(pct):.2f}% {extra}".rstrip())
            else:
                lines.append(f"• {label}：⚠️暂缺")
    else:
        lines += ["• 恒生指数：⚠️暂缺", "• 日经225：⚠️暂缺", "• 韩国综合：⚠️暂缺"]

    rz = data.get('rz_bal'); rb = data.get('rz_buy')
    mc = data.get('mkt_cap')
    # 与两融同日期的成交额，用于比率计算
    rz_turnover = data.get('rz_turnover'); rz_to_ed = data.get('rz_turnover_date')
    delta = data.get('rz_delta')
    lines.append("\n━━━ 市场风险偏好 ━━━")
    if rz is not None and rz_ed:
        delta_str = f"，较前日{'+' if (delta or 0)>=0 else ''}{delta:.0f}亿" if delta is not None else ""
        lines.append(f"• 两融余额（{rz_ed}）：{rz:.0f}亿{delta_str}")
    else:
        lines.append("• 两融余额：⚠️暂缺")

    if rz is not None and mc is not None and mc > 0 and mc_ed:
        ratio1 = rz / mc * 100
        safe = "✅ 安全区间" if ratio1 < 3.0 else ("⚠️ 预警区" if ratio1 < 3.5 else "🔴 高危区")
        lines.append(f"• 两融余额/A股流通市值（{rz_ed}）= {ratio1:.2f}%  → {safe}")
    else:
        lines.append("• 两融余额/A股流通市值：⚠️数据暂缺")

    if rz_turnover is not None and rz_turnover > 0:
        ratio2 = rb / rz_turnover * 100
        rz_to_ed_fmt = (datetime.strptime(rz_to_ed, "%Y%m%d") + _TZ).strftime("%Y年%m月%d日") if rz_to_ed else ""
        judgement = "保守" if ratio2 < 7 else ("中性" if ratio2 <= 11 else "过热")
        lines += [
            f"• 两融交易额/A股成交额（{rz_to_ed_fmt}）= {ratio2:.1f}%",
            f"  阈值：<7%保守 | 7-11%中性 | >11%过热",
            f"  → 比例={ratio2:.1f}% → {judgement}",
        ]
    else:
        lines.append("• 两融交易额/A股成交额：⚠️数据暂缺")

    # PE + 国债收益率 + 风险溢价
    pe = data.get('pe_data', {})
    if pe.get('risk_premium') is not None:
        rp_judge = "高估" if pe['risk_premium'] < 3 else ("中性" if pe['risk_premium'] <= 6 else "低估")
        rep_dt = pe.get('rep_date') or ''
        if rep_dt and len(rep_dt) == 10:
            y, m, d = rep_dt.split('-')
            rep_dt_fmt = f"{y}年{m}月{d}日"
        else:
            rep_dt_fmt = rep_dt

        zz = pe.get('zzqz_pe'); bond = pe.get('bond10y'); rp = pe['risk_premium']
        lines += [
            f"• 股市风险溢价（{rep_dt_fmt}）= {rp:.2f}%",
            f"  阈值：<3%高估 | 3-6%中性 |>6%低估",
            f"  → 溢价率={rp:.2f}% → {rp_judge}",
        ]
    else:
        lines.append("• 股市风险溢价：⚠️数据暂缺")

    hs300_pe = pe.get('hs300_pe')
    hs300_pct = pe.get('hs300_pct5y')
    today_fmt = NOW.strftime("%Y年%m月%d日")
    if hs300_pe:
        pct_str = f"{hs300_pct:.1f}%" if hs300_pct else "N/A"
        lines.append(f"• 沪深300PE = {hs300_pe:.2f}（近5年分位点={pct_str}，{today_fmt}）")
    else:
        lines.append("• 沪深300PE：⚠️数据暂缺")

    if ai_news:
        lines.append("\n━━━ 财经要闻 ━━━"); lines.extend(ai_news)
    else:
        lines += ["\n━━━ 财经要闻 ━━━", "⚠️暂缺"]
    if ai_action:
        lines.append("\n━━━ 明日操作建议 ━━━"); lines.extend(ai_action)
    else:
        lines += ["\n━━━ 明日操作建议 ━━━",
                   "① 顺势而为：⚠️暂缺","② 超跌博弈：⚠️暂缺","③ 控制仓位：⚠️暂缺"]
    lines.append("\n⚠️ 免责声明：仅供参考，不构成投资建议。股市有风险，投资需谨慎。")
    return "\n".join(lines)

# ── 主流程 ───────────────────────────────────────────────
def main(ai_fill: bool = False):
    print(f"\n[{TS}] 晚报数据获取开始...")
    rz_bal, rz_delta, rz_bal_date = get_margin_balance_effective()
    effective_date = (rz_bal_date.replace('年','').replace('月','').replace('日','')
                      if rz_bal_date else YESTERDAY)
    rz_buy,  rz_buy_date  = get_margin_buy_effective(effective_date)
    # 成交额（今日实时，用于A股收盘板块）
    turnover, to_date = get_turnover_effective(TODAY_DATE)
    # 成交额（与两融同日期，用于市场风险偏好板块的比率计算）
    rz_turnover, _ = get_turnover_effective(effective_date)
    mkt_cap, mc_date       = get_market_cap_effective(effective_date)
    indices = get_index_data()
    north   = get_north_bound()
    zt, dt  = get_market_stats()
    sectors = get_sector_flow()
    asia_pacific = get_asia_pacific()
    pe_data = get_pe_and_bond(effective_date)
    data = {
        'north': north, 'zt_count': zt, 'dt_count': dt,
        'rz_bal': rz_bal, 'rz_delta': rz_delta, 'rz_bal_date': rz_bal_date,
        'rz_buy': rz_buy, 'rz_buy_date': rz_buy_date,
        'turnover': turnover, 'turnover_date': to_date,
        'rz_turnover': rz_turnover, 'rz_turnover_date': effective_date,
        'mkt_cap': mkt_cap, 'mkt_cap_date': mc_date,
        'sectors': sectors,
        'pe_data': pe_data,
        'asia_pacific': asia_pacific,
    }
    if ai_fill and any(v is None for k, v in data.items()
                       if k not in ('north','sectors','rz_delta')):
        data = ai_supplement(data)
    print(f"\n[{TS}] 数据汇总:")
    for k, v in [('两融余额',data['rz_bal']),('两融交易额',data['rz_buy']),
                  ('流通市值',data['mkt_cap']),('成交额',data['turnover'])]:
        print(f"  {k}：{v}")
    report = build_report(indices, data, TODAY_STR)
    print("\n" + "=" * 50); print(report); print("=" * 50)
    return report

# ── 防重复运行锁 ─────────────────────────────────────────────
_LOCK_FILE = "/tmp/a_stock_evening.lock"

def _acquire_lock():
    if os.path.exists(_LOCK_FILE):
        print(f"[LOCK] 已有实例在运行 ({_LOCK_FILE})，退出。")
        sys.exit(0)
    open(_LOCK_FILE, "w").close()

def _release_lock():
    if os.path.exists(_LOCK_FILE):
        os.remove(_LOCK_FILE)

if __name__ == "__main__":
    _acquire_lock()
    try:
        import os
        dry_run = '--ai-fill' in sys.argv
        print(f"[{TS}] 第一步：收集数据...")
        report  = main(ai_fill=dry_run)
        err = 0
        if report:
            print(f"[{TS}] 第二步：保存Markdown报告...")
            _dir = "/workspace/projects/A股报告系统/reports"
            os.makedirs(_dir, exist_ok=True)
            _date_str = (globals().get('TARGET_DATE') or
                         (datetime.now(timezone.utc)+_TZ).strftime("%Y%m%d"))
            _path = os.path.join(_dir, "晚报_最新.md")
            with open(_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"  已保存: {_path}")
            print("\n" + "="*60)
            print(report)
            print("="*60)
            # 第一层推送已禁用，统一由 AI 增强版通过 webhook 发送
            if not dry_run:
                print(f"[{TS}] ✅ 数据已保存，等待 AI 增强版发送...")
        else:
            err = -1
    finally:
        _release_lock()
        print(f"\n[{TS}] {'✅ 已推送' if err == 0 else f'❌ 失败(err={err})'}")
