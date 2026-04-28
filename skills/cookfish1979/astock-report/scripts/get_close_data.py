#!/usr/bin/env python3
"""补全收盘小结数据（涨停/跌停/炸板率/申万行业），用于推送完整版"""
from datetime import datetime, timezone, timedelta
import warnings, json, sys, argparse

warnings.filterwarnings('ignore')
_TZ = timedelta(hours=8)

def get_full_data(trade_date=None):
    """
    采集完整收盘数据。
    trade_date: YYYYMMDD 格式，默认昨天
    """
    import akshare as ak

    if trade_date is None:
        now = datetime.now(_TZ)
        # 默认取前一交易日（简单逻辑：若是周末往前推）
        day = now - timedelta(days=1)
        if day.weekday() >= 5:  # 周末
            day -= timedelta(days=day.weekday() - 4)
        trade_date = day.strftime('%Y%m%d')

    result = {'trade_date': trade_date}

    # ── 涨跌停 ───────────────────────────────────────────
    try:
        zt = ak.stock_zt_pool_em(date=trade_date)
        zn = len(zt)
        dn = len([x for x in zt['涨跌幅'].tolist() if float(x) <= -9.5])
        result['涨停'] = zn
        result['跌停'] = dn
        print(f"[涨跌停] 涨停={zn} 跌停={dn}")
    except Exception as e:
        result['涨停'] = 0; result['跌停'] = 0
        print(f"[涨跌停] 错: {e}")

    # ── 炸板率：炸板池 / (炸板池 + 涨停池) ────────────────────
    try:
        zb = ak.stock_zt_pool_zbgc_em(date=trade_date)   # 炸板股池
        zn_zt = ak.stock_zt_pool_em(date=trade_date)       # 涨停股池
        zb_n = len(zb); zn_n = len(zn_zt)
        exp_rate = round(zb_n / (zb_n + zn_n) * 100, 1) if (zb_n + zn_n) > 0 else 0.0
        result['炸板率'] = exp_rate
        result['炸板数'] = zb_n
        print(f"[炸板率] 涨停={zn_n} 炸板={zb_n} 炸板率={exp_rate}%")
    except Exception as e:
        result['炸板率'] = 0; result['炸板数'] = 0
        print(f"[炸板率] 错: {e}")

    # ── 申万行业（新浪财经） ─────────────────────────────
    try:
        import requests, re, json
        r = requests.get(
            'https://vip.stock.finance.sina.com.cn/q/view/newFLJK.php',
            params={'param': 'sw'},
            headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn'},
            timeout=8
        )
        r.encoding = 'gbk'
        text = r.text.strip()
        # 接口返回格式：var S_Finance_bankuai_sw = {"key":"code,name,num,price,...", ...}
        m = re.search(r'\{.+\}', text, re.DOTALL)
        if not m:
            raise ValueError('无法提取 JSON 块')
        obj = json.loads(m.group())
        hy_data = []
        for v in obj.values():
            parts = v.split(',')
            if len(parts) >= 4:
                try:
                    hy_data.append({'name': parts[1].strip(), 'pct': float(parts[3].strip())})
                except:
                    pass
        hy_data.sort(key=lambda x: x['pct'], reverse=True)
        result['行业数'] = len(hy_data)
        result['涨幅前5'] = [(x['name'], round(x['pct'], 2)) for x in hy_data[:5]]
        result['跌幅前5'] = [(x['name'], round(x['pct'], 2)) for x in hy_data[-5:]]
        print(f"[申万行业] {len(hy_data)}个, 涨幅前3: {result['涨幅前5'][:3]}")
    except Exception as e:
        result['行业_错'] = str(e)[:80]
        print(f"[申万行业] 错: {e}")

    # ── 主力净流入（东方财富数据中心） ──────────────────────
    try:
        import requests
        params = {
            'reportName': 'RPT_MARKET_CAPITALFLOW',
            'columns': 'TRADE_DATE,MAIN_INFLOW,MAIN_OUTFLOW,NET_INFLOW',
            'filter': '(PLATE="沪深两市")(BONDTYPE="A股")',
            'sortColumns': 'TRADE_DATE',
            'sortTypes': '-1',
            'pageSize': '1',
        }
        r = requests.get(
            'https://datacenter-web.eastmoney.com/api/data/v1/get',
            params=params,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://data.eastmoney.com',
            },
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        rows = data.get('result', {}).get('data', [])
        if rows:
            row = rows[0]
            net = float(row.get('NET_INFLOW', 0) or 0) / 1e8   # 转为亿元
            main = float(row.get('MAIN_INFLOW', 0) or 0) / 1e8
            main_pct = round(main / 26419 * 100, 2) if main else 0.0
            result['主力净额'] = round(net, 2)
            result['主力占比'] = main_pct
            print(f"[主力净流入] {round(net,2)}亿, 占比{main_pct}%")
        else:
            raise ValueError('结果为空')
    except Exception as e:
        result['主力净额'] = None
        result['主力占比'] = None
        print(f"[主力净流入] 错: {e}")

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='采集收盘数据')
    parser.add_argument('--date', '-d', type=str, help='交易日期 YYYYMMDD')
    args = parser.parse_args()

    d = get_full_data(args.date)
    print('\n=== 完整数据 ===')
    print(json.dumps(d, ensure_ascii=False, indent=2))
