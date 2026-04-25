"""
需求拆解器 - Requirement Decomposer

职责:
1. 理解用户需求
2. 拆解为子任务
3. 评估复杂度
4. 生成执行计划

架构原则：
- 独立模块，职责单一
- 可测试，可复用
- 透明决策，用户可见
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class Subtask:
    """子任务"""
    name: str
    description: str
    complexity: int  # 1-5
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """执行计划"""
    mode: str  # "quick" | "standard" | "thorough"
    steps: List[str]
    skip_steps: List[str]
    max_iterations: int
    reflection_level: str  # "surface" | "root" | "pattern" | "growth"


@dataclass
class DecompositionResult:
    """拆解结果"""
    original_task: str
    subtasks: List[Subtask]
    complexity_score: int  # 1-10
    complexity_level: str  # "simple" | "medium" | "complex"
    execution_plan: ExecutionPlan
    estimated_time: int  # 秒
    reasoning: str  # 决策理由


class RequirementDecomposer:
    """需求拆解器"""
    
    # 复杂度阈值
    SIMPLE_THRESHOLD = 3
    COMPLEX_THRESHOLD = 6  # 降低阈值，让更多任务进入 complex 模式
    
    # 关键词库
    SIMPLE_KEYWORDS = [
        "hello", "简单", "测试", "示例", "demo", "打印",
        "创建文件", "脚本", "小工具"
    ]
    
    COMPLEX_KEYWORDS = [
        "系统", "完整", "生产", "优化", "重构", "架构",
        "部署", "数据库", "API", "服务", "平台", "引擎",
        "多文件", "模块", "框架", "集成"
    ]
    
    # 执行计划模板
    PLAN_TEMPLATES = {
        "simple": ExecutionPlan(
            mode="quick",
            steps=["分析", "实现", "基础检查", "交付"],
            skip_steps=["测试生成", "反思", "修复"],
            max_iterations=1,
            reflection_level="surface"
        ),
        "medium": ExecutionPlan(
            mode="standard",
            steps=["分析", "实现", "测试", "交付"],
            skip_steps=["深度反思"],
            max_iterations=2,
            reflection_level="root"
        ),
        "complex": ExecutionPlan(
            mode="thorough",
            steps=["分析", "实现", "测试", "反思", "修复", "交付"],
            skip_steps=[],
            max_iterations=5,
            reflection_level="growth"
        )
    }
    
    # 预计耗时 (秒)
    TIME_ESTIMATES = {
        "simple": {"base": 10, "per_subtask": 5},
        "medium": {"base": 30, "per_subtask": 15},
        "complex": {"base": 60, "per_subtask": 30}
    }
    
    def __init__(self, llm_client=None):
        """
        初始化拆解器
        
        Args:
            llm_client: LLM 客户端，用于深度分析
        """
        self.llm_client = llm_client
    
    def decompose(self, task: str, context: Optional[Dict] = None) -> DecompositionResult:
        """
        拆解需求
        
        Args:
            task: 用户任务描述
            context: 上下文信息 (可选)
        
        Returns:
            DecompositionResult: 拆解结果
        """
        # 1. 关键词快速匹配
        keyword_match = self._keyword_match(task)
        
        # 2. 拆解子任务
        subtasks = self._extract_subtasks(task, keyword_match)
        
        # 3. 评估复杂度
        complexity_score = self._assess_complexity(subtasks, task)
        complexity_level = self._get_complexity_level(complexity_score)
        
        # 4. 生成执行计划
        execution_plan = self._generate_plan(complexity_level, subtasks)
        
        # 5. 估算时间
        estimated_time = self._estimate_time(complexity_level, subtasks)
        
        # 6. 生成决策理由
        reasoning = self._generate_reasoning(
            task, subtasks, complexity_score, complexity_level, execution_plan
        )
        
        return DecompositionResult(
            original_task=task,
            subtasks=subtasks,
            complexity_score=complexity_score,
            complexity_level=complexity_level,
            execution_plan=execution_plan,
            estimated_time=estimated_time,
            reasoning=reasoning
        )
    
    def _keyword_match(self, task: str) -> str:
        """关键词快速匹配"""
        task_lower = task.lower()
        
        # 检查复杂关键词 (优先级高)
        complex_count = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in task_lower)
        if complex_count >= 2:  # 2 个以上复杂关键词 → complex
            return "complex"
        
        # 检查简单关键词
        if any(kw in task_lower for kw in self.SIMPLE_KEYWORDS):
            return "simple"
        
        # 检查复杂关键词
        if complex_count >= 1:
            return "complex"
        
        return "medium"
    
    def _extract_subtasks(self, task: str, keyword_match: str) -> List[Subtask]:
        """
        拆解子任务
        
        简单规则：
        - simple: 通常 1 个子任务
        - medium: 2-4 个子任务
        - complex: 5+ 个子任务
        """
        subtasks = []
        
        if keyword_match == "simple":
            # 简单任务：单个子任务
            subtasks.append(Subtask(
                name="实现功能",
                description=f"完成：{task}",
                complexity=1,
                dependencies=[]
            ))
        
        elif keyword_match == "medium":
            # 中等任务：2-3 个子任务
            subtasks = [
                Subtask(
                    name="设计结构",
                    description="设计代码结构和接口",
                    complexity=2,
                    dependencies=[]
                ),
                Subtask(
                    name="实现核心功能",
                    description="实现主要功能逻辑",
                    complexity=3,
                    dependencies=["设计结构"]
                ),
                Subtask(
                    name="测试验证",
                    description="编写测试并验证",
                    complexity=2,
                    dependencies=["实现核心功能"]
                )
            ]
        
        else:  # complex
            # 复杂任务：4-6 个子任务
            subtasks = [
                Subtask(
                    name="需求分析",
                    description="分析需求和现有代码",
                    complexity=3,
                    dependencies=[]
                ),
                Subtask(
                    name="架构设计",
                    description="设计系统架构和模块",
                    complexity=4,
                    dependencies=["需求分析"]
                ),
                Subtask(
                    name="核心实现",
                    description="实现核心模块",
                    complexity=4,
                    dependencies=["架构设计"]
                ),
                Subtask(
                    name="集成测试",
                    description="集成测试和验证",
                    complexity=3,
                    dependencies=["核心实现"]
                ),
                Subtask(
                    name="优化完善",
                    description="性能优化和文档",
                    complexity=3,
                    dependencies=["集成测试"]
                )
            ]
        
        return subtasks
    
    def _assess_complexity(self, subtasks: List[Subtask], task: str) -> int:
        """
        评估复杂度 (1-10 分)
        
        考虑因素：
        1. 子任务数量
        2. 子任务复杂度
        3. 任务描述长度
        4. 依赖关系复杂度
        """
        score = 0
        
        # 子任务数量 (0-3 分)
        score += min(len(subtasks), 3)
        
        # 子任务平均复杂度 (0-3 分)
        if subtasks:
            avg_complexity = sum(s.complexity for s in subtasks) / len(subtasks)
            score += min(avg_complexity, 3)
        
        # 任务描述长度 (0-2 分)
        if len(task) > 50:
            score += 1
        if len(task) > 100:
            score += 1
        
        # 依赖关系 (0-2 分)
        total_deps = sum(len(s.dependencies) for s in subtasks)
        if total_deps > 2:
            score += 1
        if total_deps > 5:
            score += 1
        
        return min(max(int(score), 1), 10)
    
    def _get_complexity_level(self, score: int) -> str:
        """将分数转换为等级"""
        if score <= self.SIMPLE_THRESHOLD:
            return "simple"
        elif score <= self.COMPLEX_THRESHOLD:
            return "medium"
        else:
            return "complex"
    
    def _generate_plan(self, complexity_level: str, subtasks: List[Subtask]) -> ExecutionPlan:
        """生成执行计划"""
        # 使用模板
        plan = self.PLAN_TEMPLATES[complexity_level]
        
        # 根据子任务微调
        if complexity_level == "medium" and len(subtasks) <= 2:
            # 中等任务但子任务少，可以跳过一些步骤
            plan = ExecutionPlan(
                mode="standard",
                steps=["分析", "实现", "测试", "交付"],
                skip_steps=["反思"],
                max_iterations=1,
                reflection_level="surface"
            )
        
        return plan
    
    def _estimate_time(self, complexity_level: str, subtasks: List[Subtask]) -> int:
        """估算耗时 (秒)"""
        estimate = self.TIME_ESTIMATES[complexity_level]
        base_time = estimate["base"]
        per_subtask_time = estimate["per_subtask"]
        
        return base_time + len(subtasks) * per_subtask_time
    
    def _generate_reasoning(
        self,
        task: str,
        subtasks: List[Subtask],
        complexity_score: int,
        complexity_level: str,
        execution_plan: ExecutionPlan
    ) -> str:
        """生成决策理由"""
        reasons = []
        
        # 复杂度理由
        reasons.append(f"复杂度评分：{complexity_score}/10 ({complexity_level})")
        
        # 子任务理由
        reasons.append(f"拆解为 {len(subtasks)} 个子任务")
        
        # 执行计划理由
        if execution_plan.skip_steps:
            reasons.append(f"跳过步骤：{', '.join(execution_plan.skip_steps)} (加速)")
        
        # 时间估算
        reasons.append(f"预计耗时：{self._estimate_time(complexity_level, subtasks)}秒")
        
        return " | ".join(reasons)
    
    def print_plan(self, result: DecompositionResult):
        """打印执行计划"""
        print("\n" + "=" * 60)
        print("📋 需求拆解结果")
        print("=" * 60)
        print(f"任务：{result.original_task}")
        print(f"复杂度：{result.complexity_score}/10 ({result.complexity_level})")
        print(f"子任务：{len(result.subtasks)} 个")
        
        print("\n📝 子任务列表:")
        for i, subtask in enumerate(result.subtasks, 1):
            deps = f" → 依赖：{', '.join(subtask.dependencies)}" if subtask.dependencies else ""
            print(f"  {i}. {subtask.name} (复杂度：{subtask.complexity}/5){deps}")
        
        print(f"\n🚀 执行计划:")
        print(f"  模式：{result.execution_plan.mode}")
        print(f"  步骤：{' → '.join(result.execution_plan.steps)}")
        if result.execution_plan.skip_steps:
            print(f"  跳过：{', '.join(result.execution_plan.skip_steps)}")
        print(f"  最大迭代：{result.execution_plan.max_iterations} 次")
        
        print(f"\n⏱️  预计耗时：{result.estimated_time}秒")
        print(f"💡 决策理由：{result.reasoning}")
        print("=" * 60 + "\n")


# 快速测试
if __name__ == "__main__":
    decomposer = RequirementDecomposer()
    
    test_tasks = [
        "写个 Hello World",
        "写个爬取天气数据的爬虫",
        "重构整个用户认证系统"
    ]
    
    for task in test_tasks:
        print(f"\n{'='*60}")
        print(f"测试任务：{task}")
        print('='*60)
        result = decomposer.decompose(task)
        decomposer.print_plan(result)
