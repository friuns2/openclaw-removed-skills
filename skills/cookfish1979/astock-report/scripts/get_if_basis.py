#!/usr/bin/env python3
"""
获取沪深300价格指数 & IF期货主力合约，计算贴水/升水
数据源：
  - IF期货：东方财富 wap 页面（220.IFM）
  - 沪深300现货：新浪财经 sh000300
"""
import requests
import re
import sys
import json

# ── IF期货：东方财富 wap 页面 ──────────────────────────────────────
def get_if_futures():
    """
    东方财富 IF 期货主连（220.IFM）
    页面嵌入了 quotedata，price 需 ÷10 换算为真实点位
    """
    try:
        r = requests.get(
            "https://wap.eastmoney.com/quote/stock/220.IFM.html",
            headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                "Accept": "text/html",
            },
            timeout=8,
        )
        text = r.text
        m = re.search(r'var quotedata\s*=\s*(\{.*?\});', text, re.DOTALL)
        if not m:
            return None
        d = json.loads(m.group(1))
        price = d.get("price")
        if not price:
            return None
        return {
            "name": d.get("name", "沪深主连"),
            "price": price / 10.0,          # 东方财富报价 ×10
            "zde": d.get("zde", 0) / 10.0, # 涨跌额
            "zdf": d.get("zdf", 0) / 100,  # 涨跌幅（%）
            "source": "东方财富(IFM)",
        }
    except Exception as e:
        print(f"IF期货获取失败: {e}", file=sys.stderr)
        return None

# ── 沪深300现货：东方财富 wap ────────────────────────────────────
def get_hs300():
    """获取沪深300现货价格（东方财富 1.000300）"""
    try:
        r = requests.get(
            "https://wap.eastmoney.com/quote/stock/1.000300.html",
            headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                "Accept": "text/html",
            },
            timeout=8,
        )
        text = r.text
        m = re.search(r'var quotedata\s*=\s*(\{.*?\});', text, re.DOTALL)
        if not m:
            return None
        d = json.loads(m.group(1))
        price = d.get("price")
        if not price:
            return None
        return {
            "name": d.get("name", "沪深300"),
            "price": price / 100,            # 东方财富报价 ÷100
            "zdf": d.get("zdf", 0) / 100,  # 涨跌幅（%）
            "source": "东方财富(000300)",
        }
    except Exception as e:
        print(f"沪深300获取失败: {e}", file=sys.stderr)
        return None

def calc_basis(hs300, if_fut):
    """计算基差、年化升贴水率和情绪打分"""
    if not hs300 or not if_fut:
        return None
    basis = if_fut["price"] - hs300["price"]
    annual_days, fut_days = 365, 90
    annual_rate = (basis / hs300["price"]) * (annual_days / fut_days) * 100

    # IF情绪打分（0-20分）
    rate = annual_rate  # 升水为正，贴水为负
    if rate > 2:        score = 20  # 最强升水，最乐观
    elif rate > 0:       score = 18  # 轻微升水
    elif rate >= -3:     score = 15  # 轻微贴水 0~-3%
    elif rate >= -4:      score = 10  # 正常贴水 3-4%
    elif rate >= -8:     score = 5   # 较深贴水 4-8%
    else:                score = 0   # 深贴水 >8%

    return {
        "hs300_price":   hs300["price"],
        "if_price":      if_fut["price"],
        "if_zdf":        if_fut.get("zdf"),
        "basis":         round(basis, 2),
        "basis_rate_pct": round(basis / hs300["price"] * 100, 3),
        "annual_rate_pct": round(annual_rate, 2),
        "direction":     "升水" if basis > 0 else "贴水",
        "score":         score,
        "score_max":     20,
        "source":        f"IF期货={if_fut.get('source')} / 沪深300={hs300.get('source')}",
    }

def format_output(result):
    """格式化为可读文本"""
    if not result:
        return "⚠️ IF升贴水数据暂缺"
    d = result
    direction = d["direction"]
    level = "🟢升水" if direction == "升水" else ("🟡轻微贴水" if abs(d["basis_rate_pct"]) < 3 else ("🔴较深贴水" if abs(d["basis_rate_pct"]) < 8 else "⚫深贴水"))
    text = (
        f"IF年化{direction}：{d['annual_rate_pct']}% | "
        f"基差：{d['basis']}点 | "
        f"IF={d['if_price']} ({d.get('if_zdf',0):.2%}) / "
        f"沪深300={d['hs300_price']} | "
        f"打分：{d['score']}/{d['score_max']} {level}"
    )
    return text

if __name__ == "__main__":
    hs300   = get_hs300()
    if_fut  = get_if_futures()
    result  = calc_basis(hs300, if_fut)
    text    = format_output(result)
    print(text)
    if result:
        print(f"数据来源：{result['source']}")
    print("---JSON---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
