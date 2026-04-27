#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟组合收益报告生成器
基于 fpdf2 生成包含中文字符的 PDF 报告
"""
from fpdf import FPDF
from datetime import datetime
import sys

class PDF(FPDF):
    def header(self):
        self.set_font('NotoSans', '', 10)
        self.cell(0, 10, f'模拟投资组合收益报告 - 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'R')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('NotoSans', '', 8)
        self.cell(0, 10, f'数据源：恒生聚源（GILData） | 页码：{self.page_no()}', 0, 0, 'C')

def create_report(portfolio_id, record_date, perf_data, position_data, history_data, output_path):
    pdf = PDF()
    
    # 注册中文字体（必须在 add_page 之前）
    pdf.add_font('NotoSans', '', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    pdf.add_font('NotoSans', 'b', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
    
    pdf.add_page()
    
    # 标题
    pdf.set_font('NotoSans', 'b', 20)
    pdf.cell(0, 15, '模拟投资组合收益报告', 0, 1, 'C')
    pdf.ln(5)
    
    # 一、组合基本信息
    pdf.set_font('NotoSans', 'b', 14)
    pdf.cell(0, 10, '一、组合基本信息', 0, 1)
    pdf.ln(2)
    
    pdf.set_font('NotoSans', '', 11)
    info = [
        ('组合 ID', portfolio_id),
        ('截止日期', record_date),
    ]
    for label, value in info:
        pdf.cell(40, 8, f'{label}：', 0, 0)
        pdf.cell(0, 8, value, 0, 1)
    pdf.ln(5)
    
    # 二、核心绩效指标
    pdf.set_font('NotoSans', 'b', 14)
    pdf.cell(0, 10, '二、核心绩效指标', 0, 1)
    pdf.ln(2)
    
    pdf.set_font('NotoSans', 'b', 10)
    col_widths = [50, 45, 45]
    
    # 表头
    pdf.set_fill_color(30, 60, 120)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(col_widths[0], 8, '指标名称', 1, 0, 'C', fill=True)
    pdf.cell(col_widths[1], 8, '数值', 1, 0, 'C', fill=True)
    pdf.cell(col_widths[2], 8, '说明', 1, 1, 'C', fill=True)
    
    # 数据行
    pdf.set_text_color(0, 0, 0)
    for i, (name, value, desc) in enumerate(perf_data):
        pdf.set_fill_color(245, 245, 245 if i % 2 == 1 else 255)
        pdf.cell(col_widths[0], 8, name, 1, 0, 'C', fill=i % 2 == 1)
        pdf.cell(col_widths[1], 8, value, 1, 0, 'C', fill=i % 2 == 1)
        pdf.cell(col_widths[2], 8, desc, 1, 1, 'C', fill=i % 2 == 1)
    pdf.ln(5)
    
    # 三、当前持仓明细
    pdf.set_font('NotoSans', 'b', 14)
    pdf.cell(0, 10, '三、当前持仓明细', 0, 1)
    pdf.ln(2)
    
    pdf.set_font('NotoSans', 'b', 9)
    col_widths = [22, 22, 20, 22, 22, 25, 22, 25]
    
    # 表头
    pdf.set_fill_color(30, 60, 120)
    pdf.set_text_color(255, 255, 255)
    headers = ['证券代码', '证券名称', '持仓权重', '持仓数量', '公允价值', '持仓市值', '成本单价', '持仓成本']
    for j, h in enumerate(headers):
        pdf.cell(col_widths[j], 7, h, 1, 0, 'C', fill=True)
    pdf.ln(7)
    
    # 数据行
    pdf.set_text_color(0, 0, 0)
    for i, row in enumerate(position_data):
        pdf.set_fill_color(245, 245, 245 if i % 2 == 1 else 255)
        for j, cell in enumerate(row):
            pdf.cell(col_widths[j], 7, str(cell), 1, 0, 'C', fill=i % 2 == 1)
        pdf.ln(7)
    pdf.ln(5)
    
    # 四、调仓历史
    pdf.set_font('NotoSans', 'b', 14)
    pdf.cell(0, 10, '四、调仓历史', 0, 1)
    pdf.ln(2)
    
    pdf.set_font('NotoSans', 'b', 10)
    col_widths = [35, 35, 110]
    
    # 表头
    pdf.set_fill_color(30, 60, 120)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(col_widths[0], 8, '日期', 1, 0, 'C', fill=True)
    pdf.cell(col_widths[1], 8, '操作类型', 1, 0, 'C', fill=True)
    pdf.cell(col_widths[2], 8, '调整内容', 1, 1, 'C', fill=True)
    
    # 数据行
    pdf.set_text_color(0, 0, 0)
    for i, (date, op, content) in enumerate(history_data):
        pdf.set_fill_color(245, 245, 245 if i % 2 == 1 else 255)
        pdf.cell(col_widths[0], 8, date, 1, 0, 'C', fill=i % 2 == 1)
        pdf.cell(col_widths[1], 8, op, 1, 0, 'C', fill=i % 2 == 1)
        pdf.cell(col_widths[2], 8, content, 1, 1, 'L', fill=i % 2 == 1)
    pdf.ln(5)
    
    # 五、免责声明
    pdf.set_font('NotoSans', 'b', 14)
    pdf.cell(0, 10, '五、免责声明', 0, 1)
    pdf.ln(2)
    
    pdf.set_font('NotoSans', '', 10)
    disclaimer = '''本报告基于恒生聚源（GILData）模拟组合服务生成，仅供测试和参考用途，不构成任何投资建议。
模拟组合收益不代表实际交易结果，过往业绩不代表未来表现。
投资有风险，入市需谨慎。'''
    pdf.multi_cell(0, 6, disclaimer)
    pdf.ln(10)
    
    # 保存 PDF
    pdf.output(output_path)
    return output_path

if __name__ == '__main__':
    # 示例调用
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
    ]
    
    position_data = [
        ('300502.SZ', '新易盛', '19.00%', '3,815', '130.88', '499,135.00', '78.05', '297,741.73'),
        ('300750.SZ', '宁德时代', '18.46%', '1,207', '401.70', '484,851.90', '259.20', '312,856.55'),
        ('600519.SH', '贵州茅台', '10.60%', '192', '1,450.00', '278,400.00', '1,488.12', '285,719.32'),
        ('603259.SH', '药明康德', '6.37%', '1,705', '98.10', '167,260.50', '54.02', '92,111.18'),
    ]
    
    history_data = [
        ('2025-01-01', '建仓', '贵州茅台 25%、宁德时代 25%、药明康德 25%、新易盛 25%'),
        ('2025-05-15', '调仓', '贵州茅台 25%→30%、宁德时代 25%→30%、药明康德 25%→10%、新易盛 25%→30%')
    ]
    
    # 输出到 sample 目录
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(os.path.dirname(script_dir), 'sample')
    os.makedirs(sample_dir, exist_ok=True)
    output_path = os.path.join(sample_dir, f'模拟组合收益报告_{portfolio_id[:8]}.pdf')
    
    create_report(portfolio_id, record_date, perf_data, position_data, history_data, output_path)
    print(f'PDF 报告已生成：{output_path}')
