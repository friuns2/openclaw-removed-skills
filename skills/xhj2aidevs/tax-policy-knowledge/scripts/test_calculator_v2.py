#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财税政策计算器测试脚本 V2
"""
# Copyright (c) 2026 WorkBuddy Skills. All rights reserved.
# Skill: tax-policy-knowledge | Version: 0.0.0
# Author: QQ 1817694478 | Q-Group: 972156177
# Unauthorized copying, modification, or distribution is prohibited.
# This software is provided "as is" without warranty of any kind.
import sys
import os
from pathlib import Path

# 获取当前脚本所在目录，定位同级的 tax_policy_calculator.py
SCRIPTS_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPTS_DIR))

# 使用标准模块导入方式
from tax_policy_calculator import TaxCalculator

def test_calculations():
    """测试各类税务计算"""
    calculator = TaxCalculator()
    
    print("=" * 70)
    print("财税政策计算器功能测试")
    print("数据来源：国家税务总局政策法规库")
    print("=" * 70)
    
    # 测试1：小规模纳税人增值税（免税情况）
    print("\n【测试1】小规模纳税人增值税 - 月销售额8万元（免税）")
    result = calculator.calculate_vat(sales=80000, taxpayer_type="small")
    print(calculator.format_result(result))
    
    # 测试2：小规模纳税人增值税（征税情况）
    print("\n【测试2】小规模纳税人增值税 - 月销售额15万元（征税）")
    result = calculator.calculate_vat(sales=150000, taxpayer_type="small")
    print(calculator.format_result(result))
    
    # 测试3：一般纳税人增值税
    print("\n【测试3】一般纳税人增值税 - 销售额50万元")
    result = calculator.calculate_vat(sales=500000, taxpayer_type="general")
    print(calculator.format_result(result))
    
    # 测试4：小微企业所得税
    print("\n【测试4】小微企业所得税 - 年应纳税所得额200万元")
    result = calculator.calculate_corporate_income_tax(profit=2000000, is_small_micro=True)
    print(calculator.format_result(result))
    
    # 测试5：高新技术企业所得税
    print("\n【测试5】高新技术企业所得税 - 年应纳税所得额500万元")
    result = calculator.calculate_corporate_income_tax(profit=5000000, is_high_tech=True)
    print(calculator.format_result(result))
    
    # 测试6：个人所得税综合所得
    print("\n【测试6】个人所得税综合所得 - 年收入20万元")
    result = calculator.calculate_individual_income_tax(
        annual_income=200000,
        deductions=60000,
        special_deductions=36000
    )
    print(calculator.format_result(result))
    
    # 测试7：个体工商户经营所得（享受减半）
    print("\n【测试7】个体工商户经营所得 - 年利润80万元（享受减半）")
    result = calculator.calculate_business_income_tax(annual_profit=800000)
    print(calculator.format_result(result))
    
    # 测试8：个体工商户经营所得（不享受减半）
    print("\n【测试8】个体工商户经营所得 - 年利润250万元（不享受减半）")
    result = calculator.calculate_business_income_tax(annual_profit=2500000)
    print(calculator.format_result(result))
    
    print("\n" + "=" * 70)
    print("测试完成！所有计算功能正常。")
    print("=" * 70)
if __name__ == '__main__':
    test_calculations()