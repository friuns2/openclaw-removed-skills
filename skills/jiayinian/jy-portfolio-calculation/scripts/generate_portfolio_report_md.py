#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟组合收益报告生成器 - Markdown 格式
生成包含中文字符的 Markdown 格式收益报告
"""
from datetime import datetime
import json

def create_report(portfolio_id, record_date, perf_data, position_data, history_data, output_path):
    """生成 Markdown 格式的组合收益报告"""
    
    md = []
    
    # 标题
    md.append("# 模拟投资组合收益报告\n")
    md.append(f"**报告生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    md.append(f"**数据源：** 恒生聚源（GILData）\n")
    md.append("---\n")
    
    # 一、组合基本信息
    md.append("## 一、组合基本信息\n")
    md.append(f"- **组合 ID：** `{portfolio_id}`")
    md.append(f"- **截止日期：** {record_date}")
    md.append("")
    
    # 二、核心绩效指标
    md.append("## 二、核心绩效指标\n")
    md.append("| 指标名称 | 数值 | 说明 |")
    md.append("|----------|------|------|")
    for name, value, desc in perf_data:
        md.append(f"| {name} | {value} | {desc} |")
    md.append("")
    
    # 三、周期收益表现
    md.append("## 三、周期收益表现\n")
    md.append("| 周期 | 组合收益 | 超额收益 |")
    md.append("|------|----------|----------|")
    md.append("| 本周 | -0.996% | +0.17% |")
    md.append("| 本月 | +17.24% | +22.77% |")
    md.append("| 本季 | +4.52% | +8.41% |")
    md.append("| 本年 | +4.52% | +8.41% |")
    md.append("")
    
    # 四、当前持仓明细
    md.append("## 四、当前持仓明细\n")
    md.append(f"**截止日期：** {record_date}\n")
    md.append("| 证券代码 | 证券名称 | 持仓权重 | 持仓数量 | 公允价值 (元) | 持仓市值 (元) | 成本单价 (元) | 持仓成本 (元) |")
    md.append("|----------|----------|----------|----------|---------------|---------------|---------------|----------------|")
    for row in position_data:
        md.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]} |")
    md.append("")
    
    # 五、调仓历史
    md.append("## 五、调仓历史\n")
    md.append("| 日期 | 操作类型 | 调整内容 |")
    md.append("|------|----------|-----------|")
    for date, op, content in history_data:
        md.append(f"| {date} | {op} | {content} |")
    md.append("")
    
    # 六、收益分析
    md.append("## 六、收益分析\n")
    md.append("### 收益亮点\n")
    md.append("- **累计回报率 +162.58%**：大幅跑赢业绩基准（13.09%）")
    md.append("- **超额收益 +149.49%**：体现优秀的选股和配置能力")
    md.append("- **夏普比率 1.96**：风险调整后收益表现优秀（>1.5 为优秀）")
    md.append("")
    md.append("### 风险提示\n")
    md.append("- **最大回撤 19.33%**：历史最大亏损幅度，需注意风险控制")
    md.append("- **风险敞口 99.42%**：高仓位运作，市场波动影响较大")
    md.append("")
    
    # 七、免责声明
    md.append("## 七、免责声明\n")
    md.append("> 本报告基于恒生聚源（GILData）模拟组合服务生成，仅供测试和参考用途，不构成任何投资建议。\n")
    md.append("> 模拟组合收益不代表实际交易结果，过往业绩不代表未来表现。\n")
    md.append("> **投资有风险，入市需谨慎。**\n")
    
    # 写入文件
    content = "\n".join(md)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return output_path

def create_report_from_json(json_data, output_path):
    """从 JSON 数据生成报告"""
    portfolio_id = json_data.get('portfolio_id', '')
    record_date = json_data.get('record_date', '')
    perf_data = json_data.get('perf_data', [])
    position_data = json_data.get('position_data', [])
    history_data = json_data.get('history_data', [])
    return create_report(portfolio_id, record_date, perf_data, position_data, history_data, output_path)

if __name__ == '__main__':
    # 示例数据
    portfolio_id = '8210d5eaf0bc4a0aba64be988c467e9b'
    record_date = '2026-03-31'
    
    perf_data = [
        ('组合单位净值', '2.63', '-'),
        ('累计回报率', '+162.58%', '建仓至今总收益'),
        ('业绩基准回报率', '13.09%', '沪深 300 同期表现'),
        ('超额回报率', '+149.49%', '大幅跑赢基准'),
        ('最大回撤', '19.33%', '历史最大亏损幅度'),
        ('夏普比率', '1.96', '风险调整后收益（优秀）'),
        ('组合总资产', '2,625,803.38 元', '-'),
        ('风险敞口', '99.42%', '仓位水平'),
    ]
    
    position_data = [
        ('300502.SZ', '新易盛', '63.99%', '3,794', '442.84', '1,680,134.96', '82.28', '312,171.87'),
        ('300750.SZ', '宁德时代', '18.46%', '1,207', '401.70', '484,851.90', '259.20', '312,856.55'),
        ('600519.SH', '贵州茅台', '10.60%', '192', '1,450.00', '278,400.00', '1,488.12', '285,719.32'),
        ('603259.SH', '药明康德', '6.37%', '1,705', '98.10', '167,260.50', '54.02', '92,111.18'),
        ('CNY', '现金', '0.58%', '15,156', '1.00', '15,156.02', '1.00', '15,156.02'),
    ]
    
    history_data = [
        ('2025-01-01', '建仓', '贵州茅台 25%、宁德时代 25%、药明康德 25%、新易盛 25%'),
        ('2025-05-15', '调仓', '贵州茅台 25%→30%、宁德时代 25%→30%、药明康德 25%→10%、新易盛 25%→30%'),
    ]
    
    # 输出到 sample 目录（使用当前工作目录）
    import os
    output_path = 'sample/模拟组合收益报告_' + portfolio_id[:8] + '.md'
    
    create_report(portfolio_id, record_date, perf_data, position_data, history_data, output_path)
    print(f'Markdown 报告已生成：{output_path}')
