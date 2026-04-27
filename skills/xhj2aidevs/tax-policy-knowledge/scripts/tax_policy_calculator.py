#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财税政策计算器
支持增值税、企业所得税、个人所得税等税种的精确计算
数据来源：国家税务总局政策法规库
"""
# Copyright (c) 2026 WorkBuddy Skills. All rights reserved.
# Skill: tax-policy-knowledge | Version: 0.0.0
# Author: QQ 1817694478 | Q-Group: 972156177
# Unauthorized copying, modification, or distribution is prohibited.
# This software is provided "as is" without warranty of any kind.

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Optional

# ─────────────────────────────────────────
# Windows GBK编码兼容处理（必须放在import之后）
# ─────────────────────────────────────────
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

# Integrity check on startup
_SKILL_DIR = Path(__file__).parent.parent
try:
    sys.path.insert(0, str(_SKILL_DIR.parent))
    from integrity_guard import IntegrityGuard
    _guard = IntegrityGuard(str(_SKILL_DIR))
    _ok, _msg = _guard.startup_check_with_message()
    if not _ok:
        print(f'[ERROR] {_msg}', flush=True)
        sys.exit(1)
except ImportError:
    pass
class TaxCalculator:
    """财税政策计算器主类"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.update_date = "2026-04-01"
    
    def calculate_vat(self, sales: float, taxpayer_type: str = "small", 
                      is_special_invoice: bool = False) -> Dict:
        """
        计算增值税
        
        Args:
            sales: 销售额（元）
            taxpayer_type: 纳税人类型 small(小规模)/general(一般纳税人)
            is_special_invoice: 是否开具专用发票
        
        Returns:
            计算结果字典
        """
        result = {
            "tax_type": "增值税",
            "taxpayer_type": "小规模纳税人" if taxpayer_type == "small" else "一般纳税人",
            "sales_amount": sales,
            "calculation_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        if taxpayer_type == "small":
            # 小规模纳税人计算（2026-2027年优惠政策）
            if sales <= 100000:  # 月销售额10万以下免征
                result["tax_rate"] = "0%（免征）"
                result["tax_amount"] = 0
                result["policy"] = "依据：财政部 税务总局公告2026年第10号"
                result["note"] = "月销售额10万元以下（含本数）免征增值税"
            else:
                # 减按1%征收
                tax_rate = 0.01
                tax_amount = sales / (1 + tax_rate) * tax_rate
                result["tax_rate"] = "1%（优惠税率）"
                result["tax_amount"] = round(tax_amount, 2)
                result["policy"] = "依据：财政部 税务总局公告2026年第10号"
                result["note"] = "适用3%征收率的减按1%征收"
        else:
            # 一般纳税人（简化计算，假设13%税率）
            tax_rate = 0.13
            tax_amount = sales / (1 + tax_rate) * tax_rate
            result["tax_rate"] = "13%"
            result["tax_amount"] = round(tax_amount, 2)
            result["policy"] = "依据：《中华人民共和国增值税法》"
            result["note"] = "一般货物销售税率"
        
        result["net_amount"] = round(sales - result["tax_amount"], 2)
        return result
    
    def calculate_corporate_income_tax(self, profit: float, 
                                       is_high_tech: bool = False,
                                       is_small_micro: bool = True) -> Dict:
        """
        计算企业所得税
        
        Args:
            profit: 年应纳税所得额（元）
            is_high_tech: 是否为高新技术企业
            is_small_micro: 是否为小型微利企业
        
        Returns:
            计算结果字典
        """
        result = {
            "tax_type": "企业所得税",
            "profit_amount": profit,
            "calculation_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        if is_high_tech:
            # 高新技术企业15%税率
            tax_rate = 0.15
            tax_amount = profit * tax_rate
            result["tax_rate"] = "15%"
            result["tax_amount"] = round(tax_amount, 2)
            result["policy"] = "依据：《企业所得税法》第二十八条"
            result["note"] = "高新技术企业减按15%税率征收"
            
        elif is_small_micro and profit <= 3000000:
            # 小型微利企业优惠政策（2027年底前）
            # 实际税负5%
            effective_rate = 0.05
            tax_amount = profit * effective_rate
            result["tax_rate"] = "20%（实际税负5%）"
            result["tax_amount"] = round(tax_amount, 2)
            result["policy"] = "依据：小微企业税收优惠政策（延续至2027年底）"
            result["note"] = f"年应纳税所得额{profit/10000:.2f}万元，享受小微企业所得税优惠"
            
        else:
            # 一般企业25%税率
            tax_rate = 0.25
            tax_amount = profit * tax_rate
            result["tax_rate"] = "25%"
            result["tax_amount"] = round(tax_amount, 2)
            result["policy"] = "依据：《企业所得税法》第四条"
            result["note"] = "一般企业所得税税率"
        
        result["net_profit"] = round(profit - result["tax_amount"], 2)
        result["effective_tax_rate"] = round(result["tax_amount"] / profit * 100, 2) if profit > 0 else 0
        return result
    
    def calculate_individual_income_tax(self, annual_income: float, 
                                        deductions: float = 60000,
                                        special_deductions: float = 0) -> Dict:
        """
        计算个人所得税（综合所得）
        
        Args:
            annual_income: 年度收入总额（元）
            deductions: 基本减除费用（默认6万元）
            special_deductions: 专项附加扣除总额
        
        Returns:
            计算结果字典
        """
        # 计算应纳税所得额
        taxable_income = max(0, annual_income - deductions - special_deductions)
        
        # 税率表（年度）
        brackets = [
            (36000, 0.03, 0),
            (144000, 0.10, 2520),
            (300000, 0.20, 16920),
            (420000, 0.25, 31920),
            (660000, 0.30, 52920),
            (960000, 0.35, 85920),
            (float('inf'), 0.45, 181920)
        ]
        
        # 确定适用税率
        tax_rate = 0
        quick_deduction = 0
        for bracket in brackets:
            if taxable_income <= bracket[0]:
                tax_rate = bracket[1]
                quick_deduction = bracket[2]
                break
        
        tax_amount = taxable_income * tax_rate - quick_deduction
        
        result = {
            "tax_type": "个人所得税（综合所得）",
            "annual_income": annual_income,
            "basic_deduction": deductions,
            "special_deductions": special_deductions,
            "taxable_income": round(taxable_income, 2),
            "tax_rate": f"{tax_rate*100:.0f}%",
            "quick_deduction": quick_deduction,
            "tax_amount": round(max(0, tax_amount), 2),
            "net_income": round(annual_income - max(0, tax_amount), 2),
            "policy": "依据：《个人所得税法》及实施条例",
            "calculation_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        return result
    
    def calculate_business_income_tax(self, annual_profit: float) -> Dict:
        """
        计算个体工商户经营所得税
        
        Args:
            annual_profit: 年应纳税所得额（元）
        
        Returns:
            计算结果字典
        """
        # 税率表（经营所得）
        brackets = [
            (30000, 0.05, 0),
            (90000, 0.10, 1500),
            (300000, 0.20, 10500),
            (500000, 0.30, 40500),
            (float('inf'), 0.35, 65500)
        ]
        
        # 确定适用税率
        tax_rate = 0
        quick_deduction = 0
        for bracket in brackets:
            if annual_profit <= bracket[0]:
                tax_rate = bracket[1]
                quick_deduction = bracket[2]
                break
        
        # 计算税额
        tax_amount = annual_profit * tax_rate - quick_deduction
        
        # 应用减半优惠（2023-2027年，年应纳税所得额200万以下）
        halved = False
        if annual_profit <= 2000000:
            tax_amount = tax_amount * 0.5
            halved = True
        
        result = {
            "tax_type": "个人所得税（经营所得）",
            "annual_profit": annual_profit,
            "tax_rate": f"{tax_rate*100:.0f}%",
            "quick_deduction": quick_deduction,
            "tax_before_discount": round(annual_profit * tax_rate - quick_deduction, 2),
            "halved_policy": "年应纳税所得额200万元以下减半征收" if halved else "超过200万元，不适用减半政策",
            "tax_amount": round(max(0, tax_amount), 2),
            "net_profit": round(annual_profit - max(0, tax_amount), 2),
            "policy": "依据：个体工商户个人所得税减半政策（2023-2027年）",
            "calculation_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        return result
    
    def format_result(self, result: Dict) -> str:
        """格式化输出计算结果"""
        output = []
        output.append("=" * 60)
        output.append(f"【{result.get('tax_type', '税务计算')}结果】")
        output.append("=" * 60)
        
        for key, value in result.items():
            if key not in ['tax_type', 'calculation_date']:
                key_map = {
                    'sales_amount': '销售额',
                    'profit_amount': '应纳税所得额',
                    'annual_income': '年度收入',
                    'annual_profit': '年度利润',
                    'tax_rate': '适用税率',
                    'tax_amount': '应纳税额',
                    'net_amount': '不含税金额',
                    'net_profit': '税后利润',
                    'net_income': '税后收入',
                    'taxable_income': '应纳税所得额',
                    'basic_deduction': '基本减除费用',
                    'special_deductions': '专项附加扣除',
                    'policy': '政策依据',
                    'note': '备注',
                    'taxpayer_type': '纳税人类型',
                    'effective_tax_rate': '实际税负率',
                    'quick_deduction': '速算扣除数',
                    'tax_before_discount': '减半前税额',
                    'halved_policy': '减半政策'
                }
                label = key_map.get(key, key)
                if isinstance(value, (int, float)):
                    if 'amount' in key or 'income' in key or 'profit' in key or 'deduction' in key:
                        output.append(f"{label}: {value:,.2f} 元")
                    else:
                        output.append(f"{label}: {value}")
                else:
                    output.append(f"{label}: {value}")
        
        output.append("-" * 60)
        output.append(f"计算日期: {result.get('calculation_date', '')}")
        output.append("=" * 60)
        
        return "\n".join(output)
def main():
    parser = argparse.ArgumentParser(description='财税政策计算器')
    parser.add_argument('mode', choices=['vat', 'corporate', 'individual', 'business'],
                       help='计算模式: vat(增值税), corporate(企业所得税), individual(个人所得税), business(经营所得)')
    
    # 增值税参数
    parser.add_argument('--sales', type=float, help='销售额')
    parser.add_argument('--taxpayer-type', choices=['small', 'general'], default='small',
                       help='纳税人类型: small(小规模), general(一般纳税人)')
    
    # 企业所得税参数
    parser.add_argument('--profit', type=float, help='应纳税所得额')
    parser.add_argument('--is-high-tech', action='store_true', help='是否为高新技术企业')
    parser.add_argument('--is-small-micro', action='store_true', default=True,
                       help='是否为小型微利企业')
    
    # 个人所得税参数
    parser.add_argument('--annual-income', type=float, help='年度收入')
    parser.add_argument('--deductions', type=float, default=60000, help='基本减除费用')
    parser.add_argument('--special-deductions', type=float, default=0, help='专项附加扣除')
    
    # 经营所得参数
    parser.add_argument('--annual-profit', type=float, help='年度利润（经营所得）')
    
    args = parser.parse_args()
    
    calculator = TaxCalculator()
    
    try:
        if args.mode == 'vat':
            if not args.sales:
                print("错误: 增值税计算需要提供 --sales 参数")
                sys.exit(1)
            result = calculator.calculate_vat(
                sales=args.sales,
                taxpayer_type=args.taxpayer_type
            )
        
        elif args.mode == 'corporate':
            if not args.profit:
                print("错误: 企业所得税计算需要提供 --profit 参数")
                sys.exit(1)
            result = calculator.calculate_corporate_income_tax(
                profit=args.profit,
                is_high_tech=args.is_high_tech,
                is_small_micro=args.is_small_micro
            )
        
        elif args.mode == 'individual':
            if not args.annual_income:
                print("错误: 个人所得税计算需要提供 --annual-income 参数")
                sys.exit(1)
            result = calculator.calculate_individual_income_tax(
                annual_income=args.annual_income,
                deductions=args.deductions,
                special_deductions=args.special_deductions
            )
        
        elif args.mode == 'business':
            if not args.annual_profit:
                print("错误: 经营所得计算需要提供 --annual-profit 参数")
                sys.exit(1)
            result = calculator.calculate_business_income_tax(
                annual_profit=args.annual_profit
            )
        
        print(calculator.format_result(result))
        
    except Exception as e:
        print(f"计算错误: {e}")
        sys.exit(1)

    # 作者信息输出（兼容Windows GBK控制台）
    sys.stdout.buffer.write(
        "\n[OK] 有问题-建议-需求可联系作者QQ 1817694478 或加Q群 972156177 交流更多...\n"
        .encode("utf-8", errors="replace")
    )
    sys.stdout.buffer.flush()

if __name__ == '__main__':
    main()