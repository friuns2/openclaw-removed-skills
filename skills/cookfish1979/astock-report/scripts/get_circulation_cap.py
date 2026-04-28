#!/usr/bin/env python3
"""
获取A股全市场流通市值
数据源：akshare stock_sse_summary + stock_szse_summary
返回: (全市场流通市值[亿], 全市场流通市值[万亿元])
"""
import akshare as ak


def get_circulation_market_cap():
    """获取A股全市场流通市值（亿元+万亿元）"""
    total_yi = 0.0

    # 上交所流通市值（亿元）
    try:
        sse = ak.stock_sse_summary()
        sse_circ = float(sse.loc[sse['项目'] == '流通市值', '股票'].values[0])
        total_yi += sse_circ
        print(f"  [市值] 上交所={sse_circ:.0f}亿")
    except Exception as e:
        print(f"  [市值] 上交所 ⚠️ {e}")

    # 深交所（主板A股+创业板A股）流通市值（元 → 亿）
    try:
        szse = ak.stock_szse_summary()
        main = szse[szse['证券类别'] == '主板A股']
        cyb = szse[szse['证券类别'] == '创业板A股']
        main_circ = float(main['流通市值'].values[0])
        cyb_circ = float(cyb['流通市值'].values[0])
        total_yi += main_circ / 1e8 + cyb_circ / 1e8
        print(f"  [市值] 深交所={main_circ/1e8+cyb_circ/1e8:.0f}亿")
    except Exception as e:
        print(f"  [市值] 深交所 ⚠️ {e}")

    if total_yi <= 0:
        print("  [市值] ⚠️ 获取失败，使用默认值50万亿")
        return None, 50.0

    wan = total_yi / 10000
    print(f"  [市值] A股全市场流通市值={wan:.2f}万亿")
    return total_yi, wan


if __name__ == "__main__":
    cap_yi, cap_wan = get_circulation_market_cap()
    if cap_yi:
        print(f"\n结果: {cap_yi:.0f}亿 ({cap_wan:.2f}万亿)")
