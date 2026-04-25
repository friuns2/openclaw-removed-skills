#!/usr/bin/env python3
"""
交付标准检查模块

核心理念：
1. 代码能运行只是基本要求
2. 必须有测试、文档、错误处理
3. 安全检查不可少
4. 达到标准才交付
"""

import re
import ast
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class CheckStatus(Enum):
    """检查状态"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class CheckItem:
    """检查项"""
    name: str
    description: str
    status: CheckStatus
    details: str = ""
    severity: str = "medium"  # low/medium/high/critical


@dataclass
class DeliveryReport:
    """交付报告"""
    timestamp: datetime
    task: str
    code: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    items: List[CheckItem]
    ready_to_deliver: bool
    suggestions: List[str]


class DeliveryChecker:
    """
    交付标准检查器
    
    使用示例:
        checker = DeliveryChecker()
        report = checker.check(code, task)
    """
    
    def __init__(self, strict: bool = True):
        self.strict = strict  # 严格模式
        self.checks: List[CheckItem] = []
    
    def check(self, code: str, task: str = "") -> DeliveryReport:
        """
        执行完整交付检查
        
        Args:
            code: 代码内容
            task: 任务描述
        
        Returns:
            DeliveryReport: 交付报告
        """
        self.checks = []
        
        # 1. 基础检查
        self._check_syntax(code)
        self._check_runs_without_error(code)
        
        # 2. 质量检查
        self._check_documentation(code)
        self._check_error_handling(code)
        self._check_basic_tests(code)
        
        # 3. 安全检查
        self._check_security(code)
        self._check_dangerous_patterns(code)
        
        # 4. 完整性检查
        self._check_completeness(code, task)
        self._check_todo_comments(code)
        
        # 5. 代码风格检查（可选）
        if self.strict:
            self._check_code_style(code)
        
        # 生成报告
        passed = sum(1 for c in self.checks if c.status == CheckStatus.PASS)
        failed = sum(1 for c in self.checks if c.status == CheckStatus.FAIL)
        warnings = sum(1 for c in self.checks if c.status == CheckStatus.WARNING)
        
        # 判断是否可以交付
        critical_failed = any(
            c.status == CheckStatus.FAIL and c.severity == "critical"
            for c in self.checks
        )
        high_failed = any(
            c.status == CheckStatus.FAIL and c.severity == "high"
            for c in self.checks
        )
        
        ready = not critical_failed and not high_failed
        
        return DeliveryReport(
            timestamp=datetime.now(),
            task=task,
            code=code,
            total_checks=len(self.checks),
            passed=passed,
            failed=failed,
            warnings=warnings,
            items=self.checks.copy(),
            ready_to_deliver=ready,
            suggestions=self._generate_suggestions()
        )
    
    def _add_check(
        self,
        name: str,
        description: str,
        status: CheckStatus,
        details: str = "",
        severity: str = "medium"
    ):
        """添加检查项"""
        self.checks.append(CheckItem(
            name=name,
            description=description,
            status=status,
            details=details,
            severity=severity
        ))
    
    def _check_syntax(self, code: str):
        """检查语法"""
        try:
            compile(code, '<string>', 'exec')
            self._add_check(
                name="语法检查",
                description="代码无语法错误",
                status=CheckStatus.PASS,
                severity="critical"
            )
        except SyntaxError as e:
            self._add_check(
                name="语法检查",
                description=f"语法错误：{e}",
                status=CheckStatus.FAIL,
                severity="critical"
            )
    
    def _check_runs_without_error(self, code: str):
        """检查能否运行"""
        # 简单检查：至少有一个可执行的语句
        if "pass\n" == code.strip() or code.strip() == "":
            self._add_check(
                name="可运行性",
                description="代码为空或只有 pass",
                status=CheckStatus.FAIL,
                details="需要实现具体功能",
                severity="high"
            )
        else:
            self._add_check(
                name="可运行性",
                description="代码包含可执行语句",
                status=CheckStatus.PASS
            )
    
    def _check_documentation(self, code: str):
        """检查文档"""
        has_module_docstring = '"""' in code or "'''" in code
        has_comments = '#' in code
        has_function_docstring = bool(re.search(r'def \w+\([^)]*\):\s*"""', code))
        
        if has_module_docstring and has_comments:
            self._add_check(
                name="文档完整性",
                description="有模块文档和注释",
                status=CheckStatus.PASS
            )
        elif has_module_docstring or has_comments:
            self._add_check(
                name="文档完整性",
                description="有部分文档",
                status=CheckStatus.WARNING,
                details="建议添加更多注释和文档字符串",
                severity="low"
            )
        else:
            self._add_check(
                name="文档完整性",
                description="缺少文档",
                status=CheckStatus.FAIL,
                details="需要添加模块文档和关键注释",
                severity="medium"
            )
    
    def _check_error_handling(self, code: str):
        """检查错误处理"""
        has_try_except = "try:" in code and "except" in code
        has_error_message = bool(re.search(r'(print|log|logger).*错误|error|exception', code, re.IGNORECASE))
        has_exit_handling = "sys.exit" in code or "exit(" in code
        
        if has_try_except and has_error_message:
            self._add_check(
                name="错误处理",
                description="有完整的错误处理和提示",
                status=CheckStatus.PASS
            )
        elif has_try_except:
            self._add_check(
                name="错误处理",
                description="有异常捕获，但缺少错误提示",
                status=CheckStatus.WARNING,
                details="建议添加用户友好的错误信息",
                severity="low"
            )
        else:
            self._add_check(
                name="错误处理",
                description="缺少错误处理",
                status=CheckStatus.FAIL if self.strict else CheckStatus.WARNING,
                details="建议添加 try-except 块",
                severity="medium"
            )
    
    def _check_basic_tests(self, code: str):
        """检查基本测试"""
        has_test_file = "test" in code.lower()
        has_assert = "assert" in code
        has_main_guard = 'if __name__ == "__main__"' in code
        has_example_usage = bool(re.search(r'# 示例|# Example|>>> ', code))
        
        if has_assert or (has_main_guard and has_example_usage):
            self._add_check(
                name="基本测试",
                description="有测试用例或示例",
                status=CheckStatus.PASS
            )
        elif has_main_guard:
            self._add_check(
                name="基本测试",
                description="有主程序入口，但缺少测试",
                status=CheckStatus.WARNING,
                details="建议添加测试用例",
                severity="low"
            )
        else:
            self._add_check(
                name="基本测试",
                description="缺少测试",
                status=CheckStatus.WARNING,
                details="建议添加测试用例或示例用法",
                severity="low"
            )
    
    def _check_security(self, code: str):
        """检查安全性"""
        dangerous_patterns = []
        
        # eval/exec
        if re.search(r'\beval\s*\(', code):
            dangerous_patterns.append("使用 eval 可能导致代码注入")
        if re.search(r'\bexec\s*\(', code):
            dangerous_patterns.append("使用 exec 可能导致代码注入")
        
        # os.system + input
        if "os.system" in code and "input(" in code:
            dangerous_patterns.append("os.system + input 可能导致命令注入")
        
        # pickle
        if "pickle.load" in code or "pickle.loads" in code:
            dangerous_patterns.append("pickle.load 可能执行恶意代码")
        
        # SQL injection (simple check)
        if re.search(r'execute\s*\(\s*["\'].*%s', code, re.IGNORECASE):
            dangerous_patterns.append("可能存在 SQL 注入风险")
        
        if dangerous_patterns:
            self._add_check(
                name="安全检查",
                description="发现安全隐患",
                status=CheckStatus.FAIL,
                details="\n".join(dangerous_patterns),
                severity="critical"
            )
        else:
            self._add_check(
                name="安全检查",
                description="未发现明显安全问题",
                status=CheckStatus.PASS,
                severity="high"
            )
    
    def _check_dangerous_patterns(self, code: str):
        """检查危险模式"""
        warnings = []
        
        # 硬编码密码/密钥
        if re.search(r'(password|passwd|pwd|secret|api_key|token)\s*=\s*["\'][^"\']+["\']', code, re.IGNORECASE):
            warnings.append("发现硬编码的密码或密钥")
        
        # 硬编码路径
        if re.search(r'["\'][/\\](?:Users|home|var|etc)[/\w]+["\']', code):
            warnings.append("发现硬编码的绝对路径")
        
        # 无限循环风险
        if re.search(r'while\s+True\s*:', code) and "break" not in code:
            warnings.append("while True 循环缺少 break 语句")
        
        if warnings:
            self._add_check(
                name="危险模式",
                description="发现潜在问题",
                status=CheckStatus.WARNING,
                details="\n".join(warnings),
                severity="medium"
            )
    
    def _check_completeness(self, code: str, task: str):
        """检查完整性"""
        # 检查是否实现了基本功能
        if task:
            task_keywords = task.lower().split()
            implemented = 0
            
            for keyword in task_keywords:
                if len(keyword) > 3 and keyword in code.lower():
                    implemented += 1
            
            if implemented < len(task_keywords) * 0.5:
                self._add_check(
                    name="功能完整性",
                    description="代码可能未完整实现需求",
                    status=CheckStatus.WARNING,
                    details=f"需求关键词匹配度：{implemented}/{len(task_keywords)}",
                    severity="medium"
                )
            else:
                self._add_check(
                    name="功能完整性",
                    description="代码覆盖了主要需求",
                    status=CheckStatus.PASS
                )
    
    def _check_todo_comments(self, code: str):
        """检查 TODO 注释"""
        todos = re.findall(r'#\s*(TODO|FIXME|XXX|HACK)[:\s]*(.*)', code, re.IGNORECASE)
        
        if todos:
            todo_list = [f"{t[0]}: {t[1]}" for t in todos[:5]]  # 最多显示 5 个
            self._add_check(
                name="TODO 检查",
                description=f"发现 {len(todos)} 个待办事项",
                status=CheckStatus.WARNING if len(todos) <= 3 else CheckStatus.FAIL,
                details="\n".join(todo_list),
                severity="low" if len(todos) <= 3 else "medium"
            )
        else:
            self._add_check(
                name="TODO 检查",
                description="无待办事项",
                status=CheckStatus.PASS
            )
    
    def _check_code_style(self, code: str):
        """检查代码风格"""
        issues = []
        
        # 行长度
        lines = code.split('\n')
        long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 120]
        if long_lines:
            issues.append(f"{len(long_lines)} 行超过 120 字符")
        
        # 缩进
        if '\t' in code:
            issues.append("使用 Tab 缩进（应使用空格）")
        
        # 导入顺序
        imports = re.findall(r'^(?:import|from)\s+\S+', code, re.MULTILINE)
        if len(imports) > 3:
            # 简单检查：标准库应该在第三方库之前
            pass  # 需要更复杂的分析
        
        if issues:
            self._add_check(
                name="代码风格",
                description="发现风格问题",
                status=CheckStatus.WARNING,
                details="\n".join(issues),
                severity="low"
            )
        else:
            self._add_check(
                name="代码风格",
                description="符合基本规范",
                status=CheckStatus.PASS
            )
    
    def _generate_suggestions(self) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        for check in self.checks:
            if check.status == CheckStatus.FAIL:
                if "语法" in check.name:
                    suggestions.append("修复语法错误后再继续")
                elif "安全" in check.name:
                    suggestions.append("优先解决安全问题")
                elif "文档" in check.name:
                    suggestions.append("添加模块文档和关键注释")
                elif "错误处理" in check.name:
                    suggestions.append("添加 try-except 块和错误提示")
            
            elif check.status == CheckStatus.WARNING:
                if "测试" in check.name:
                    suggestions.append("添加测试用例提高可靠性")
                elif "TODO" in check.name:
                    suggestions.append("完成待办事项或创建跟踪任务")
                elif "风格" in check.name:
                    suggestions.append("优化代码风格提高可读性")
        
        return suggestions
    
    def print_report(self, report: DeliveryReport):
        """打印报告"""
        print("\n" + "=" * 60)
        print("📋 交付检查报告")
        print("=" * 60)
        print(f"任务：{report.task}")
        print(f"时间：{report.timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"结果：{'✅ 可以交付' if report.ready_to_deliver else '❌ 需要改进'}")
        print("-" * 60)
        print(f"总计：{report.total_checks} 项 | ✅ {report.passed} | ❌ {report.failed} | ⚠️ {report.warnings}")
        print("-" * 60)
        
        # 按状态分组打印
        for status in [CheckStatus.FAIL, CheckStatus.WARNING, CheckStatus.PASS]:
            items = [c for c in report.items if c.status == status]
            if items:
                icon = "❌" if status == CheckStatus.FAIL else "⚠️" if status == CheckStatus.WARNING else "✅"
                print(f"\n{icon} {status.value.upper()}:")
                for item in items:
                    print(f"  - {item.name}: {item.description}")
                    if item.details:
                        print(f"    {item.details}")
        
        if report.suggestions:
            print("\n💡 改进建议:")
            for i, sug in enumerate(report.suggestions, 1):
                print(f"  {i}. {sug}")
        
        print("=" * 60)


# 快捷函数
def check_delivery(code: str, task: str = "", strict: bool = True) -> DeliveryReport:
    """快速检查"""
    checker = DeliveryChecker(strict=strict)
    return checker.check(code, task)


if __name__ == "__main__":
    # 测试
    code = '''#!/usr/bin/env python3
"""
测试脚本
"""

import sys


def main():
    try:
        print("Hello")
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''
    
    checker = DeliveryChecker(strict=True)
    report = checker.check(code, "测试任务")
    checker.print_report(report)
