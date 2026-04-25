#!/usr/bin/env python3
"""
Auto-Coding Worker - 核心工作流

核心理念：
1. 分析需求 → 识别能力缺口
2. 找方法 → 搜索工具/文档
3. 实现 → 编写代码
4. 测试 → 验证是否工作
5. 反思 → 哪里可以改进（关键！）
6. 修复 → 迭代优化
7. 交付 → 达到标准才结束
"""

import os
import re
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


# 导入 LLM 客户端
try:
    from llm_client_v2 import AutoCodingLLM
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    AutoCodingLLM = None

# 导入需求拆解器
try:
    from decomposer import RequirementDecomposer
    DECOMPOSER_AVAILABLE = True
except ImportError:
    DECOMPOSER_AVAILABLE = False
    RequirementDecomposer = None


class WorkMode(Enum):
    """工作模式"""
    QUICK = "quick"  # 快速模式：跳过测试和反思
    STANDARD = "standard"  # 标准模式：完整流程
    DEEP = "deep"  # 深度模式：多次反思迭代


@dataclass
class TaskAnalysis:
    """任务分析结果"""
    task: str
    domain: str
    complexity: str
    required_skills: List[str]
    potential_challenges: List[str]
    suggested_approach: str


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    relevance: float


@dataclass
class CodeVersion:
    """代码版本"""
    version: int
    code: str
    timestamp: str
    changes: str
    test_results: Optional[Dict] = None


@dataclass
class DeliveryResult:
    """交付结果"""
    success: bool
    final_code: str
    iterations: int
    total_time: float
    delivery_checks: Dict[str, bool]
    documentation: str = ""
    lessons_learned: str = ""


class AutoCodingWorker:
    """
    Auto-Coding 核心工作者
    
    使用示例:
        worker = AutoCodingWorker(mode="standard")
        result = await worker.run("创建一个批量重命名文件的脚本")
    """
    
    def __init__(
        self,
        mode: WorkMode = WorkMode.STANDARD,
        reflect_depth: str = "deep",
        max_iterations: int = 5,
        workspace: Optional[str] = None,
        use_llm: bool = True,
        use_decomposer: bool = True
    ):
        self.mode = mode
        self.reflect_depth = reflect_depth
        self.max_iterations = max_iterations
        self.workspace = Path(workspace) if workspace else Path.home() / ".nanobot" / "workspace"
        self.use_llm = use_llm
        self.use_decomposer = use_decomposer
        
        # 初始化 LLM
        self.llm: Optional[AutoCodingLLM] = None
        if use_llm and LLM_AVAILABLE:
            try:
                self.llm = AutoCodingLLM()
                print(f"✅ LLM 已初始化：{self.llm.config.model}")
            except Exception as e:
                print(f"⚠️  LLM 初始化失败：{e}，将使用模板模式")
                self.llm = None
        
        # 初始化需求拆解器
        self.decomposer: Optional[RequirementDecomposer] = None
        if use_decomposer and DECOMPOSER_AVAILABLE:
            try:
                self.decomposer = RequirementDecomposer(llm_client=self.llm)
                print(f"✅ 需求拆解器已初始化")
            except Exception as e:
                print(f"⚠️  需求拆解器初始化失败：{e}")
                self.decomposer = None
        
        # 状态追踪
        self.current_task: Optional[str] = None
        self.decomposition_result = None
        self.analysis: Optional[TaskAnalysis] = None
        self.search_results: List[SearchResult] = []
        self.code_versions: List[CodeVersion] = []
        self.start_time: Optional[datetime] = None
        
        # 交付标准
        self.delivery_standards = {
            "runs_without_error": False,
            "has_basic_tests": False,
            "has_documentation": False,
            "has_error_handling": False,
            "security_check_passed": False
        }
    
    async def run(self, task: str) -> DeliveryResult:
        """运行完整的 auto-coding 工作流"""
        self.start_time = datetime.now()
        self.current_task = task
        self.code_versions = []
        self.search_results = []
        self.delivery_standards = {k: False for k in self.delivery_standards}
        
        print(f"🚀 Auto-Coding 启动：{task}")
        print(f"📋 工作模式：{self.mode.value} | 反思深度：{self.reflect_depth}")
        print("-" * 60)
        
        # 0. 需求拆解
        if self.decomposer:
            print("\n📋 步骤 0/7: 需求拆解")
            self.decomposition_result = self.decomposer.decompose(task)
            self.decomposer.print_plan(self.decomposition_result)
            self._apply_decomposition_result(self.decomposition_result)
        else:
            print("\n⚠️  需求拆解器不可用，使用默认流程")
        
        # 1. 分析需求
        print("\n📊 步骤 1/7: 分析需求")
        self.analysis = await self._analyze_requirements(task)
        self._print_analysis(self.analysis)
        
        # 2. 找方法
        print("\n🔍 步骤 2/7: 找方法")
        await self._find_methods(self.analysis)
        print(f"✅ 找到 {len(self.search_results)} 个相关资源")
        
        # 3. 实现
        print("\n💻 步骤 3/7: 实现代码")
        code_v1 = await self._implement(task, self.analysis, self.search_results)
        self.code_versions.append(code_v1)
        print(f"✅ 完成版本 v{code_v1.version}")
        
        # 4-6. 测试 → 反思 → 修复 循环
        if "测试" in self.decomposition_result.execution_plan.steps if self.decomposition_result else True:
            print("\n🔄 步骤 4-6/7: 测试 → 反思 → 修复 循环")
            final_code = await self._test_reflect_fix_loop(task)
        else:
            print("\n⏭️  跳过测试 → 反思 → 修复 循环 (简单任务)")
            final_code = code_v1.code
        
        # 7. 交付检查
        print("\n✅ 步骤 7/7: 交付检查")
        delivery_result = await self._delivery_check(task, final_code)
        
        # 总结
        total_time = (datetime.now() - self.start_time).total_seconds()
        print("\n" + "=" * 60)
        print(f"🎉 Auto-Coding 完成!")
        print(f"📊 迭代次数：{len(self.code_versions)}")
        print(f"⏱️  总耗时：{total_time:.1f}秒")
        print(f"✅ 交付检查：{sum(self.delivery_standards.values())}/{len(self.delivery_standards)}")
        if self.decomposition_result:
            print(f"🎯 复杂度：{self.decomposition_result.complexity_score}/10 ({self.decomposition_result.complexity_level})")
            print(f"⚡ 预计：{self.decomposition_result.estimated_time}秒 | 实际：{total_time:.1f}秒")
        print("=" * 60)
        
        return delivery_result
    
    def _apply_decomposition_result(self, result):
        """根据拆解结果调整工作流"""
        if result.execution_plan.mode == "quick":
            print(f"⚡ 切换为快速模式")
            print(f"⏭️  跳过：测试生成，反思，修复")
    
    async def _analyze_requirements(self, task: str) -> TaskAnalysis:
        """分析需求"""
        # 简化实现
        return TaskAnalysis(
            task=task,
            domain="general",
            complexity="medium",
            required_skills=["python"],
            potential_challenges=[],
            suggested_approach="standard"
        )
    
    def _print_analysis(self, analysis: TaskAnalysis):
        """打印分析结果"""
        print(f"   领域：{analysis.domain}")
        print(f"   复杂度：{analysis.complexity}")
        print(f"   所需技能：{', '.join(analysis.required_skills)}")
    
    async def _find_methods(self, analysis: TaskAnalysis):
        """找方法"""
        # 简化实现
        pass
    
    async def _implement(self, task: str, analysis: TaskAnalysis, search_results: List[SearchResult]) -> CodeVersion:
        """实现代码"""
        # 简化实现
        return CodeVersion(
            version=1,
            code="# TODO: 实现代码",
            timestamp=datetime.now().isoformat(),
            changes="初始版本"
        )
    
    async def _test_reflect_fix_loop(self, task: str) -> str:
        """测试 → 反思 → 修复 循环"""
        # 简化实现
        return "# TODO: 实现代码"
    
    async def _delivery_check(self, task: str, code: str) -> DeliveryResult:
        """交付检查"""
        total_time = (datetime.now() - self.start_time).total_seconds()
        return DeliveryResult(
            success=True,
            final_code=code,
            iterations=len(self.code_versions),
            total_time=total_time,
            delivery_checks=self.delivery_standards,
            documentation="",
            lessons_learned=""
        )


if __name__ == "__main__":
    async def test():
        worker = AutoCodingWorker(mode=WorkMode.QUICK)
        result = await worker.run("写个 Hello World")
        print(f"\n结果：{result.success}")
    
    asyncio.run(test())
