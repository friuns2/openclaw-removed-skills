#!/usr/bin/env python3
"""
获取A股全市场流通市值和换手率
数据源：akshare stock_sse_summary + stock_szse_summary
返回: (流通市值[亿], 换手率[%])
"""
import akshare as ak


def get_market_cap():
    """获取A股全市场流通市值（亿元）和换手率"""
    total_circulation_yi = 0.0  # 全市场流通市值（亿元）
    total_turnover_yi = 0.0    # 全市场成交额（亿元）

    try:
        # 上交所
        sse = ak.stock_sse_summary()
        sse_circ = float(sse.loc[sse['项目'] == '流通市值', '股票'].values[0])
        sse_amt = float(sse.loc[sse['项目'] == '成交金额', '股票'].values[0])
        total_circulation_yi += sse_circ
        total_turnover_yi += sse_amt
        print(f"  [市值] 上交所流通市值={sse_circ:.0f}亿 成交额={sse_amt:.0f}亿")
    except Exception as e:
        print(f"  [市值] 上交所 ⚠️ {e}")

    try:
        # 深交所（主板A股+创业板A股）
        szse = ak.stock_szse_summary()
        # 主板A股
        szse_main = szse[szse['证券类别'] == '主板A股']
        szse_cyb = szse[szse['证券类别'] == '创业板A股']
        szse_circ_main = float(szse_main['流通市值'].values[0])
        szse_circ_cyb = float(szse_cyb['流通市值'].values[0])
        szse_amt_main = float(szse_main['成交金额'].values[0])
        szse_amt_cyb = float(szse_cyb['成交金额'].values[0])
        total_circulation_yi += szse_circ_main + szse_circ_cyb
        total_turnover_yi += szse_amt_main + szse_amt_cyb
        print(f"  [市值] 深交所流通市值={szse_circ_main+szse_circ_cyb:.0f}亿 成交额={szse_amt_main+szse_amt_cyb:.0f}亿")
    except Exception as e:
        print(f"  [市值] 深交所 ⚠️ {e}")

    if total_circulation_yi <= 0:
        print("  [市值] ⚠️ 流通市值获取失败")
        return None, None

    turnover_rate = (total_turnover_yi / total_circulation_yi) * 100
    total_circulation_wan = total_circulation_yi / 10000  # 转为万亿元
    print(f"  [市值] A股全市场流通市值={total_circulation_wan:.2f}万亿 换手率={turnover_rate:.2f}%")
    return total_circulation_yi, turnover_rate


if __name__ == "__main__":
    cap_yi, turnover = get_market_cap()
    if cap_yi:
        print(f"\nA股流通市值: {cap_yi/10000:.2f}万亿")
        print(f"换手率: {turnover:.2f}%")
