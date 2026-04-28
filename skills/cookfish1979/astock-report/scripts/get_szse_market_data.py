#!/usr/bin/env python3
"""深交所市场概况数据 - 东方财富API"""
import requests, json


def fetch_szse_market_data():
    """返回 (总市值[亿元], 流通市值[亿元], 数据日期)"""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://data.eastmoney.com/"
    }

    def _fetch(mkt):
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        params = {
            "reportName": "RPT_MARKET_OVERVIEW",
            "columns": "ALL",
            "MKTCODE": mkt,
            "client": "web"
        }
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        result = data.get("result", {})
        rows = result.get("data", []) if result else []
        return rows[0] if rows else None

    # 深交所=000001，上交所=000002
    szse = _fetch("000001")
    sse  = _fetch("000002")

    szse_total = szse.get("TOTAL_MARKET_CAP", 0)   # 元
    szse_circ  = szse.get("CIRC_MARKET_CAP", 0)    # 元
    sse_total  = sse.get("TOTAL_MARKET_CAP", 0)
    sse_circ    = sse.get("CIRC_MARKET_CAP", 0)
    date        = szse.get("TRADE_DATE", "")

    total_yi = round((szse_total + sse_total) / 1e8, 2)   # 亿元
    circ_yi  = round((szse_circ  + sse_circ)  / 1e8, 2)
    total_wan = round(total_yi / 10000, 2)
    circ_wan  = round(circ_yi  / 10000, 2)

    print(f"  [市值] 深交所总市值={szse_total/1e8/10000:.2f}万亿 流通市值={szse_circ/1e8/10000:.2f}万亿")
    print(f"  [市值] 上交所总市值={sse_total/1e8/10000:.2f}万亿 流通市值={sse_circ/1e8/10000:.2f}万亿")
    print(f"  [市值] 全市场总市值={total_wan:.2f}万亿 流通市值={circ_wan:.2f}万亿（{date}）")
    return total_yi, total_wan, circ_yi, circ_wan, date


if __name__ == "__main__":
    total_yi, total_wan, circ_yi, circ_wan, date = fetch_szse_market_data()
    print(f"\n结果: 总市值={total_wan:.2f}万亿 流通市值={circ_wan:.2f}万亿")
