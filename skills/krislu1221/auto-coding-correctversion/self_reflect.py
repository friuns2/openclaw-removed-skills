#!/usr/bin/env python3
"""
自我反思模块 - Auto-Coding 的核心

核心理念：
1. 不只是修复错误，而是理解为什么错
2. 分析思维模式问题，不只是代码问题
3. 提取可复用的经验教训
4. 建立持续改进的循环
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ErrorType(Enum):
    """错误类型"""
    SYNTAX = "syntax"              # 语法错误
    LOGIC = "logic"                # 逻辑错误
    SECURITY = "security"          # 安全问题
    PERFORMANCE = "performance"    # 性能问题
    COMPLETENESS = "completeness"  # 完整性问题
    DESIGN = "design"              # 设计问题


class ReflectionLevel(Enum):
    """反思层级"""
    SURFACE = "surface"    # 表面：什么错了
    ROOT = "root"          # 根本：为什么错
    PATTERN = "pattern"    # 模式：思维模式问题
    GROWTH = "growth"      # 成长：如何改进


@dataclass
class ErrorAnalysis:
    """错误分析"""
    error_type: ErrorType
    description: str
    location: Optional[str] = None       # 错误位置
    severity: str = "medium"             # low/medium/high/critical
    impact: str = ""                     # 影响范围


@dataclass
class Reflection:
    """反思结果"""
    level: ReflectionLevel
    what_went_wrong: str                 # 什么错了
    why_it_happened: str                 # 为什么发生
    thinking_pattern: Optional[str]      # 思维模式问题
    alternative_approach: Optional[str]  # 替代方案
    lesson_learned: str                  # 经验教训
    action_items: List[str]              # 改进行动


@dataclass
class ReflectionLog:
    """反思日志"""
    timestamp: datetime
    task: str
    code_version: int
    errors: List[ErrorAnalysis]
    reflection: Reflection
    changes_made: str


class SelfReflector:
    """
    自我反思器
    
    使用示例:
        reflector = SelfReflector()
        reflection = await reflector.analyze(errors, code, task)
    """
    
    def __init__(self, depth: str = "deep"):
        self.depth = depth  # basic/deep/critical
        self.reflection_history: List[ReflectionLog] = []
        self.pattern_database: Dict[str, List[str]] = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, List[str]]:
        """加载常见思维模式问题"""
        return {
            "syntax": [
                "急于写代码，没有先设计",
                "没有使用 IDE 的语法检查",
                "复制粘贴代码时没有仔细检查"
            ],
            "logic": [
                "没有考虑边界情况",
                "假设输入总是正确的",
                "没有追踪变量状态变化"
            ],
            "security": [
                "没有考虑恶意输入",
                "过度信任外部数据",
                "没有遵循最小权限原则"
            ],
            "performance": [
                "没有考虑数据规模",
                "选择了低效的算法",
                "没有进行性能分析就优化"
            ],
            "completeness": [
                "急于求成，实现不完整",
                "没有理解完整需求就开始",
                "忽略了错误处理"
            ],
            "design": [
                "没有先设计架构就编码",
                "过度设计或设计不足",
                "没有考虑可扩展性"
            ]
        }
    
    async def analyze(
        self,
        errors: List[str],
        code: str,
        task: str,
        iteration: int = 1
    ) -> Reflection:
        """
        分析错误并生成反思
        
        Args:
            errors: 错误列表
            code: 当前代码
            task: 任务描述
            iteration: 当前迭代次数
        
        Returns:
            Reflection: 反思结果
        """
        # 1. 分析错误类型
        error_analyses = self._analyze_errors(errors)
        
        # 2. 确定反思层级
        if self.depth == "basic":
            level = ReflectionLevel.SURFACE
        elif self.depth == "deep":
            level = ReflectionLevel.ROOT if iteration <= 2 else ReflectionLevel.PATTERN
        else:  # critical
            level = ReflectionLevel.GROWTH
        
        # 3. 生成反思
        reflection = self._generate_reflection(
            level=level,
            errors=error_analyses,
            code=code,
            task=task,
            iteration=iteration
        )
        
        # 4. 记录日志
        log = ReflectionLog(
            timestamp=datetime.now(),
            task=task,
            code_version=iteration,
            errors=error_analyses,
            reflection=reflection,
            changes_made=""
        )
        self.reflection_history.append(log)
        
        return reflection
    
    def _analyze_errors(self, errors: List[str]) -> List[ErrorAnalysis]:
        """分析错误类型"""
        analyses = []
        
        for error in errors:
            error_lower = error.lower()
            
            # 判断错误类型
            if "语法" in error_lower or "syntax" in error_lower:
                error_type = ErrorType.SYNTAX
                severity = "high"
            elif "安全" in error_lower or "security" in error_lower or "inject" in error_lower:
                error_type = ErrorType.SECURITY
                severity = "critical"
            elif "逻辑" in error_lower or "logic" in error_lower:
                error_type = ErrorType.LOGIC
                severity = "medium"
            elif "性能" in error_lower or "performance" in error_lower:
                error_type = ErrorType.PERFORMANCE
                severity = "low"
            elif "完整" in error_lower or "completeness" in error_lower or "todo" in error_lower:
                error_type = ErrorType.COMPLETENESS
                severity = "medium"
            elif "设计" in error_lower or "design" in error_lower or "architect" in error_lower:
                error_type = ErrorType.DESIGN
                severity = "medium"
            else:
                error_type = ErrorType.LOGIC
                severity = "medium"
            
            analyses.append(ErrorAnalysis(
                error_type=error_type,
                description=error,
                severity=severity
            ))
        
        return analyses
    
    def _generate_reflection(
        self,
        level: ReflectionLevel,
        errors: List[ErrorAnalysis],
        code: str,
        task: str,
        iteration: int
    ) -> Reflection:
        """生成反思"""
        
        # 什么错了
        what_went_wrong = "\n".join([f"- {e.description}" for e in errors])
        
        # 为什么发生
        why_it_happened = self._analyze_root_cause(errors)
        
        # 思维模式问题
        thinking_pattern = None
        if level in [ReflectionLevel.PATTERN, ReflectionLevel.GROWTH]:
            thinking_pattern = self._identify_pattern(errors)
        
        # 替代方案
        alternative_approach = None
        if level == ReflectionLevel.GROWTH:
            alternative_approach = self._suggest_alternatives(errors, task)
        
        # 经验教训
        lesson_learned = self._extract_lesson(errors)
        
        # 改进行动
        action_items = self._generate_actions(errors, level)
        
        return Reflection(
            level=level,
            what_went_wrong=what_went_wrong,
            why_it_happened=why_it_happened,
            thinking_pattern=thinking_pattern,
            alternative_approach=alternative_approach,
            lesson_learned=lesson_learned,
            action_items=action_items
        )
    
    def _analyze_root_cause(self, errors: List[ErrorAnalysis]) -> str:
        """分析根本原因"""
        causes = []
        
        for error in errors:
            if error.error_type == ErrorType.SYNTAX:
                causes.append("编写代码时没有仔细检查语法")
            elif error.error_type == ErrorType.SECURITY:
                causes.append("没有考虑安全边界和输入验证")
            elif error.error_type == ErrorType.LOGIC:
                causes.append("逻辑推理不完整，遗漏了边界情况")
            elif error.error_type == ErrorType.COMPLETENESS:
                causes.append("急于求成，没有实现完整功能")
            elif error.error_type == ErrorType.DESIGN:
                causes.append("没有先设计架构就开始编码")
            else:
                causes.append("需要更深入的分析")
        
        return "\n".join(causes)
    
    def _identify_pattern(self, errors: List[ErrorAnalysis]) -> str:
        """识别思维模式问题"""
        patterns = []
        
        for error in errors:
            pattern_key = error.error_type.value
            if pattern_key in self.pattern_database:
                patterns.extend(self.pattern_database[pattern_key][:2])
        
        if patterns:
            return "可能存在的思维模式问题:\n" + "\n".join([f"- {p}" for p in patterns])
        else:
            return "需要更多数据来识别思维模式"
    
    def _suggest_alternatives(self, errors: List[ErrorAnalysis], task: str) -> str:
        """建议替代方案"""
        alternatives = []
        
        # 根据错误类型建议
        for error in errors:
            if error.error_type == ErrorType.SECURITY:
                alternatives.append("使用更安全的 API（如 subprocess 替代 os.system）")
            elif error.error_type == ErrorType.LOGIC:
                alternatives.append("先写测试用例，再实现功能（TDD）")
            elif error.error_type == ErrorType.DESIGN:
                alternatives.append("先画流程图/架构图，再编码")
            elif error.error_type == ErrorType.COMPLETENESS:
                alternatives.append("使用检查清单确保完整性")
        
        if alternatives:
            return "替代方案:\n" + "\n".join([f"- {a}" for a in alternatives])
        else:
            return "当前方案已经合理"
    
    def _extract_lesson(self, errors: List[ErrorAnalysis]) -> str:
        """提取经验教训"""
        lessons = []
        
        for error in errors:
            if error.error_type == ErrorType.SYNTAX:
                lessons.append("写代码后立即运行语法检查")
            elif error.error_type == ErrorType.SECURITY:
                lessons.append("始终验证外部输入，遵循最小权限原则")
            elif error.error_type == ErrorType.LOGIC:
                lessons.append("考虑边界情况和异常输入")
            elif error.error_type == ErrorType.COMPLETENESS:
                lessons.append("实现前列出所有需求，逐一完成")
        
        if lessons:
            return "经验教训:\n" + "\n".join([f"- {l}" for l in lessons])
        else:
            return "持续学习和改进"
    
    def _generate_actions(
        self,
        errors: List[ErrorAnalysis],
        level: ReflectionLevel
    ) -> List[str]:
        """生成改进行动"""
        actions = []
        
        # 立即行动
        actions.append("立即：修复当前错误")
        
        # 短期行动
        if level in [ReflectionLevel.ROOT, ReflectionLevel.PATTERN, ReflectionLevel.GROWTH]:
            actions.append("短期：建立代码审查清单")
            actions.append("短期：添加自动化测试")
        
        # 长期行动
        if level == ReflectionLevel.GROWTH:
            actions.append("长期：学习相关最佳实践")
            actions.append("长期：建立个人知识库")
        
        return actions
    
    def get_patterns_summary(self) -> str:
        """获取思维模式总结"""
        if not self.reflection_history:
            return "暂无反思记录"
        
        # 统计错误类型
        error_counts = {}
        for log in self.reflection_history:
            for error in log.errors:
                key = error.error_type.value
                error_counts[key] = error_counts.get(key, 0) + 1
        
        # 生成总结
        summary = ["思维模式分析:", ""]
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            summary.append(f"- {error_type}: {count} 次")
        
        if self.reflection_history:
            summary.append(f"\n总反思次数：{len(self.reflection_history)}")
            summary.append(f"最近反思：{self.reflection_history[-1].timestamp.strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(summary)
    
    def save_log(self, filepath: Optional[str] = None) -> str:
        """保存反思日志"""
        if filepath is None:
            filepath = f"reflection_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = []
        for log in self.reflection_history:
            data.append({
                "timestamp": log.timestamp.isoformat(),
                "task": log.task,
                "code_version": log.code_version,
                "errors": [
                    {
                        "type": e.error_type.value,
                        "description": e.description,
                        "severity": e.severity
                    }
                    for e in log.errors
                ],
                "reflection": {
                    "level": log.reflection.level.value,
                    "what_went_wrong": log.reflection.what_went_wrong,
                    "why_it_happened": log.reflection.why_it_happened,
                    "thinking_pattern": log.reflection.thinking_pattern,
                    "lesson_learned": log.reflection.lesson_learned,
                    "action_items": log.reflection.action_items
                }
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath


# 快捷函数
async def reflect(
    errors: List[str],
    code: str,
    task: str,
    depth: str = "deep"
) -> Reflection:
    """快速反思"""
    reflector = SelfReflector(depth=depth)
    return await reflector.analyze(errors, code, task)


if __name__ == "__main__":
    # 测试
    import asyncio
    
    async def test():
        reflector = SelfReflector(depth="deep")
        
        errors = [
            "语法错误：invalid syntax at line 10",
            "安全风险：os.system + input 可能导致命令注入"
        ]
        
        code = '''
def main():
    cmd = input("Enter command: ")
    os.system(cmd)
'''
        
        reflection = await reflector.analyze(errors, code, "测试任务")
        
        print("=== 反思结果 ===")
        print(f"层级：{reflection.level.value}")
        print(f"\n什么错了:\n{reflection.what_went_wrong}")
        print(f"\n为什么发生:\n{reflection.why_it_happened}")
        print(f"\n思维模式:\n{reflection.thinking_pattern}")
        print(f"\n经验教训:\n{reflection.lesson_learned}")
        print(f"\n改进行动:\n{chr(10).join(reflection.action_items)}")
    
    asyncio.run(test())
