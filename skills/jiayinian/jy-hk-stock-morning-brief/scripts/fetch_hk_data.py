#!/usr/bin/env python3
"""
港股资讯早报数据获取脚本
通过 mcporter call 命令调用聚源数据 MCP 接口获取港股市场数据

功能：
- 获取指数行情（含时序数据，用于 echarts 图表）
- 获取板块/个股排行
- 获取南向资金流向
- 获取港股通活跃成交股
- 输出 JSON 数据 + echarts 配置

依赖：
- mcporter 已安装并配置
- jy-financedata-api 和 jy-financedata-tool 服务已配置

Usage:
    python fetch_hk_data.py --date 2026-03-25 --output /tmp/hk_data.json
    python fetch_hk_data.py --date 2026-03-25 --output /tmp/hk_data.json --charts
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


def get_previous_trading_day(date_str: Optional[str] = None) -> str:
    """
    获取前一个港股交易日
    简化处理：周末返回周五，不考虑港股假期
    """
    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        target_date = datetime.now()
    
    # 如果是周一，返回上周五
    if target_date.weekday() == 0:
        return (target_date - timedelta(days=3)).strftime("%Y-%m-%d")
    # 如果是周日，返回周五
    elif target_date.weekday() == 6:
        return (target_date - timedelta(days=2)).strftime("%Y-%m-%d")
    # 其他情况返回前一天
    else:
        return (target_date - timedelta(days=1)).strftime("%Y-%m-%d")


def mcporter_call(service: str, tool: str, query: str) -> Dict[str, Any]:
    """
    通过 mcporter call 命令调用 MCP 服务工具
    
    Args:
        service: 服务名称 (jy-financedata-api 或 jy-financedata-tool)
        tool: 工具名称
        query: 查询语句（所有工具入参均为 query）
    
    Returns:
        工具调用结果（JSON 格式）
    """
    cmd = f"mcporter call {service}.{tool} query=\"{query}\""
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"[ERROR] mcporter call failed: {result.stderr}")
            return {}
        
        # 尝试解析 JSON 输出
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"[WARN] Non-JSON output: {result.stdout}")
            return {"raw": result.stdout}
    
    except subprocess.TimeoutExpired:
        print(f"[ERROR] mcporter call timeout: {cmd}")
        return {}
    except Exception as e:
        print(f"[ERROR] mcporter call exception: {e}")
        return {}


def fetch_index_data(date: str) -> Dict[str, Any]:
    """
    获取指数数据（恒指、国指、科指）
    """
    query = f"查询以下港股指数在 {date} 的交易数据：恒生指数 (HSI)、恒生国企指数 (HSCEI)、恒生科技指数 (HSTECH)。返回字段：开盘价、收盘价、最高价、最低价、涨跌幅、成交量、成交额"
    
    print(f"[INFO] 查询指数数据：{date}")
    return mcporter_call("jy-financedata-api", "IndexMarket", query)


def fetch_index_timeseries(date: str) -> Dict[str, Any]:
    """
    获取指数时序数据（用于 echarts 图表）
    """
    query = f"查询恒生指数在 {date} 的分时数据，1 分钟频率，返回时间点、开盘价、收盘价、最高价、最低价"
    
    print(f"[INFO] 查询指数时序数据：{date}")
    return mcporter_call("jy-financedata-api", "IndexTimeseries", query)


def fetch_sector_performance(date: str) -> Dict[str, Any]:
    """
    获取板块涨跌幅排行
    """
    query = f"查询港股板块在 {date} 的涨跌幅排行：领涨板块前 10、领跌板块前 10。返回字段：板块名称、涨跌幅、成交量变化"
    
    print(f"[INFO] 查询板块表现：{date}")
    return mcporter_call("jy-financedata-api", "SectorPerformance", query)


def fetch_stock_rankings(date: str) -> Dict[str, Any]:
    """
    获取个股排行（涨跌幅、成交额、换手率）
    """
    query = f"查询港股个股在 {date} 的排行数据：1. 涨跌幅排行（前 20）2. 成交额排行（前 20）3. 换手率排行（前 20）。返回字段：股票代码、名称、价格、涨跌幅、成交额、换手率"
    
    print(f"[INFO] 查询个股排行：{date}")
    return mcporter_call("jy-financedata-api", "StockRanking", query)


def fetch_southbound_flow(date: str) -> Dict[str, Any]:
    """
    获取南向资金流向
    """
    query = f"查询 {date} 南向资金流向数据：港股通（沪）净流入/出、港股通（深）净流入/出、合计净流入/出。返回字段：通道、净流入金额（亿港元）"
    
    print(f"[INFO] 查询南向资金：{date}")
    return mcporter_call("jy-financedata-api", "SouthboundFlow", query)


def fetch_southbound_history(date: str) -> Dict[str, Any]:
    """
    获取南向资金近 5 日流向（用于图表）
    """
    query = f"查询南向资金近 5 日每日净流入金额，返回日期和净流入（亿港元）"
    
    print(f"[INFO] 查询南向资金历史：{date}")
    return mcporter_call("jy-financedata-api", "SouthboundHistory", query)


def fetch_active_stocks(date: str) -> Dict[str, Any]:
    """
    获取港股通十大活跃成交股
    """
    query = f"查询 {date} 港股通十大活跃成交股。返回字段：股票代码、名称、买入金额、卖出金额、净买入、总成交额（单位：亿港元）"
    
    print(f"[INFO] 查询活跃成交股：{date}")
    return mcporter_call("jy-financedata-api", "ActiveStocks", query)


def fetch_company_announcements(date: str, stock_code: Optional[str] = None) -> Dict[str, Any]:
    """
    获取上市公司公告
    """
    if stock_code:
        query = f"查询 {stock_code} 在 {date} 收盘后至今日的公司公告：类型包括财报、盈利预警、并购重组、股份回购、重大合同、高管变动"
    else:
        query = f"查询港股上市公司在 {date} 收盘后至今日的重要公告：类型包括财报、盈利预警、并购重组、股份回购、重大合同、高管变动。筛选标准：对市场或个股有潜在重大影响。返回字段：公司名称、股票代码、公告类型、公告摘要、发布时间"
    
    print(f"[INFO] 查询公司公告：{date}")
    return mcporter_call("jy-financedata-tool", "CompanyAnnouncement", query)


def fetch_market_news(date: str) -> Dict[str, Any]:
    """
    获取市场重要新闻
    """
    query = f"查询港股市场在 {date} 的重要新闻：政策、行业、宏观。返回字段：新闻标题、摘要、来源、发布时间"
    
    print(f"[INFO] 查询市场新闻：{date}")
    return mcporter_call("jy-financedata-tool", "MarketNews", query)


def fetch_research_reports(date: str, keyword: Optional[str] = None) -> Dict[str, Any]:
    """
    获取券商研究报告
    """
    if keyword:
        query = f"查询关于\"{keyword}\"的最新券商研究报告：时间范围 {date} 至今日。返回字段：机构名称、研究员、评级、目标价、核心观点、发布时间"
    else:
        query = f"查询港股大市、重点行业或个股的最新券商研究报告：时间范围 {date} 至今日。优先选取：评级变动、目标价调整、首次覆盖。返回字段：标的公司、机构名称、评级、目标价、核心观点摘要、发布时间"
    
    print(f"[INFO] 查询研报观点")
    return mcporter_call("jy-financedata-tool", "ResearchReport", query)


def fetch_global_markets(date: str) -> Dict[str, Any]:
    """
    获取外围市场数据
    """
    query = f"查询外围市场数据：1. 美股隔夜表现：道琼斯、纳斯达克、标普 500 涨跌幅 2. 欧股：英国富时 100、德国 DAX 涨跌幅 3. 亚太市场（{date} 收盘）：日经 225、韩国 KOSPI 涨跌幅。返回字段：市场名称、指数名称、收盘价、涨跌幅"
    
    print(f"[INFO] 查询外围市场")
    return mcporter_call("jy-financedata-api", "GlobalMarkets", query)


def fetch_economic_calendar(date: str) -> Dict[str, Any]:
    """
    获取经济数据日历
    """
    query = f"查询 {date} 及本周即将公布的重要经济数据/事件：中国（GDP、CPI、PMI、社融等）、美国（CPI、非农、零售销售等）、央行会议（美联储、欧央行、中国人民银行等）。返回字段：日期、国家/地区、数据/事件名称、预期值、前值、重要性"
    
    print(f"[INFO] 查询经济日历")
    return mcporter_call("jy-financedata-tool", "EconomicCalendar", query)


def generate_echarts_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据获取的数据生成 echarts 图表配置
    
    生成图表：
    1. 恒指昨日分时走势图（如有时序数据）
    2. 南向资金近 5 日流向图
    3. 板块涨跌幅对比图
    """
    charts = {}
    
    # 图表 1: 恒指分时走势（需要时序数据）
    if "index_timeseries" in data and data["index_timeseries"]:
        times = data["index_timeseries"].get("times", [])
        prices = data["index_timeseries"].get("prices", [])
        if times and prices:
            charts["hsi_intraday"] = {
                "title": {"text": "恒生指数分时走势"},
                "xAxis": {"type": "category", "data": times},
                "yAxis": {"type": "value"},
                "series": [{
                    "data": prices,
                    "type": "line",
                    "smooth": True
                }]
            }
    
    # 图表 2: 南向资金流向
    if "southbound_history" in data and data["southbound_history"]:
        dates = data["southbound_history"].get("dates", [])
        net_flow = data["southbound_history"].get("net_flow", [])
        if dates and net_flow:
            charts["southbound_flow"] = {
                "title": {"text": "南向资金近 5 日流向"},
                "xAxis": {"type": "category", "data": dates},
                "yAxis": {"type": "value"},
                "series": [{
                    "data": net_flow,
                    "type": "bar",
                    "itemStyle": {
                        "color": "#ef232a" if sum(net_flow) > 0 else "#14b143"
                    }
                }]
            }
    
    # 图表 3: 板块涨跌幅
    if "sector_performance" in data and data["sector_performance"]:
        names = data["sector_performance"].get("names", [])
        changes = data["sector_performance"].get("changes", [])
        if names and changes:
            charts["sector_change"] = {
                "title": {"text": "板块涨跌幅排行"},
                "xAxis": {
                    "type": "category",
                    "data": names,
                    "axisLabel": {"rotate": 45}
                },
                "yAxis": {"type": "value"},
                "series": [{
                    "data": changes,
                    "type": "bar",
                    "itemStyle": {
                        "color": lambda x: "#ef232a" if x > 0 else "#14b143"
                    }
                }]
            }
    
    return charts


def check_mcporter_config() -> bool:
    """
    检查 mcporter 是否已安装并配置
    """
    try:
        # 检查 mcporter 是否安装
        result = subprocess.run(
            "mcporter --version",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("[ERROR] mcporter 未安装，请先运行：npm install -g mcporter")
            return False
        
        print(f"[INFO] mcporter 版本：{result.stdout.strip()}")
        
        # 检查服务配置
        result = subprocess.run(
            "mcporter list",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "jy-financedata-api" not in result.stdout or "jy-financedata-tool" not in result.stdout:
            print("[ERROR] MCP 服务未配置，请先运行 mcporter config add 配置 jy-financedata-api 和 jy-financedata-tool")
            print("[INFO] 配置命令示例:")
            print('  mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"')
            print('  mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"')
            return False
        
        print("[INFO] MCP 服务配置正常")
        return True
    
    except Exception as e:
        print(f"[ERROR] 检查配置失败：{e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="港股资讯早报数据获取")
    parser.add_argument("--date", type=str, help="目标日期 (YYYY-MM-DD)，默认前一个交易日")
    parser.add_argument("--output", type=str, help="输出文件路径", default="hk_data.json")
    parser.add_argument("--charts", action="store_true", help="同时生成 echarts 图表配置")
    parser.add_argument("--charts-output", type=str, help="echarts 配置输出路径", default="charts_config.json")
    parser.add_argument("--skip-check", action="store_true", help="跳过配置检查")
    
    args = parser.parse_args()
    
    # 检查配置
    if not args.skip_check:
        if not check_mcporter_config():
            print("[ERROR] 配置检查失败，请先完成 mcporter 安装和 MCP 服务配置")
            sys.