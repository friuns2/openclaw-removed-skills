#!/usr/bin/env python3
"""
9 模型对比测试脚本
测试 9 个模型：8 个百炼模型 + 1 个 MiniMax 独立 API
"""

import json
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path

# API Keys
API_KEYS = {
    "bailian": "sk-sp-f5a1549b0ad343aa95bc149c118c0119",
    "minimax": "sk-api-YOucsplnx6MQm8oqyzuO6Tfo2onhwQszRA-2CIfV7vjPr1gQFbzqCfxqeq1qlNVDT4D4wa4-wdlHvxZ4ldwypzwgsaZQbbnc_vOs3TOTY5UnnK193KEjW7o"
}

# 模型配置
MODELS = [
    # 百炼模型 (bailian) - coding 端点
    {"name": "qwen3.5-plus", "provider": "bailian"},
    {"name": "qwen3-max-2026-01-23", "provider": "bailian"},
    {"name": "qwen3-coder-next", "provider": "bailian"},
    {"name": "qwen3-coder-plus", "provider": "bailian"},
    {"name": "glm-5", "provider": "bailian"},
    {"name": "glm-4.7", "provider": "bailian"},
    {"name": "kimi-k2.5", "provider": "bailian"},
    {"name": "MiniMax-M2.5", "provider": "bailian"},
    # MiniMax 独立 API
    {"name": "MiniMax-M2.7", "provider": "minimax"},
]

# 测试任务定义
TASKS = {
    "T1": {
        "name": "快速脚本",
        "difficulty": "⭐ 简单",
        "prompt": "请写一个 Python 脚本，功能：1.遍历当前目录下所有.py 文件 2.统计每个文件的行数（非空行）3.输出总行数和每个文件的行数 4.按行数从多到少排序。要求：代码简洁，有错误处理，能直接运行。",
        "max_time": 60
    },
    "T2": {
        "name": "API 项目",
        "difficulty": "⭐⭐⭐ 中等",
        "prompt": "请创建一个完整的 Python 项目，功能：1.调用公开 API（如 https://api.github.com/users/{username}）2.获取 GitHub 用户信息并格式化展示。包含以下要求：使用 requests 或 httpx 库、有完整的错误处理（网络错误、API 限流、用户不存在）、有日志记录、有简单的单元测试、有 README.md 说明使用方法。请生成完整的项目结构和所有文件内容。",
        "max_time": 180
    },
    "T3": {
        "name": "Bug 修复",
        "difficulty": "⭐⭐⭐⭐ 困难",
        "prompt": "以下代码有 3 个 Bug，请找出并修复，同时添加测试：import os, shutil; def backup_files(source_dir, backup_dir): for filename in os.listdir(source_dir): source_path = os.path.join(source_dir, filename); backup_path = os.path.join(backup_dir, filename); if os.path.isfile(source_path): shutil.copy2(source_path, backup_path) elif os.path.isdir(source_path): backup_files(source_path, backup_dir); return True。Bug 提示：1.没有检查目标目录是否存在 2.递归调用但没有处理递归备份 3.没有返回值或日志。要求：修复所有 Bug，添加完整的错误处理，添加日志记录，添加单元测试，说明每个 Bug 的问题和修复方案。",
        "max_time": 240
    }
}


class ModelTester:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
    
    async def test_model(self, model: dict, task_id: str, task: dict) -> dict:
        """测试单个模型"""
        model_name = model["name"]
        provider = model["provider"]
        
        print(f"\n🧪 测试 {model_name} - {task_id}: {task['name']}")
        start_time = time.time()
        
        try:
            if provider == "minimax":
                code = await self._call_minimax(model_name, task["prompt"], task["max_time"])
            else:
                code = await self._call_bailian(model_name, task["prompt"], task["max_time"])
            
            elapsed = time.time() - start_time
            
            # 检查代码质量
            quality_score = self._check_code_quality(code, task["prompt"])
            
            result = {
                "model": model_name,
                "provider": provider,
                "task": task_id,
                "success": True,
                "elapsed_time": round(elapsed, 2),
                "code_length": len(code),
                "quality_score": quality_score,
                "code": code[:500] + "..." if len(code) > 500 else code
            }
            
            print(f"  ✅ 完成 - {elapsed:.2f}s, 质量分：{quality_score.get('score', 'N/A')}")
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ 失败 - {elapsed:.2f}s: {str(e)[:100]}")
            return {
                "model": model_name,
                "provider": provider,
                "task": task_id,
                "success": False,
                "elapsed_time": round(elapsed, 2),
                "error": str(e)
            }
    
    async def _call_bailian(self, model: str, prompt: str, timeout: int) -> str:
        """调用百炼 API (OpenAI 兼容格式)"""
        api_key = API_KEYS["bailian"]
        api_base = "https://coding.dashscope.aliyuncs.com/v1"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "你是一个专业的 Python 开发者，直接输出代码，不要多余解释。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 4000,
                    "temperature": 0.1
                },
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"API 错误 {resp.status}: {error[:200]}")
                
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                
                # 提取代码块
                if "```python" in content:
                    code = content.split("```python")[1].split("```")[0].strip()
                elif "```" in content:
                    code = content.split("```")[1].split("```")[0].strip()
                else:
                    code = content
                
                return code
    
    async def _call_minimax(self, model: str, prompt: str, timeout: int) -> str:
        """调用 MiniMax API (Anthropic 格式)"""
        api_key = API_KEYS["minimax"]
        api_base = "https://api.minimaxi.com/anthropic/v1"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_base}/messages",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 4000,
                    "system": "你是一个专业的 Python 开发者，直接输出代码，不要多余解释。"
                },
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"API 错误 {resp.status}: {error[:200]}")
                
                data = await resp.json()
                content = data["content"][0]["text"] if "content" in data else str(data)
                
                # 提取代码块
                if "```python" in content:
                    code = content.split("```python")[1].split("```")[0].strip()
                elif "```" in content:
                    code = content.split("```")[1].split("```")[0].strip()
                else:
                    code = content
                
                return code
    
    def _check_code_quality(self, code: str, task: str) -> dict:
        """使用 delivery_check 检查代码质量"""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from delivery_check import DeliveryChecker
            
            checker = DeliveryChecker(strict=True)
            report = checker.check(code, task)
            
            return {
                "total_checks": report.total_checks,
                "passed": report.passed,
                "failed": report.failed,
                "warnings": report.warnings,
                "ready_to_deliver": report.ready_to_deliver,
                "score": round((report.passed / report.total_checks) * 100, 1) if report.total_checks > 0 else 0
            }
        except Exception as e:
            return {
                "error": str(e),
                "score": 0
            }
    
    def generate_report(self):
        """生成测试报告"""
        report_path = self.output_dir / "TEST_REPORT.md"
        
        # 按模型分组
        models_data = {}
        for result in self.results:
            model = result["model"]
            if model not in models_data:
                models_data[model] = {"provider": result["provider"], "tasks": {}}
            models_data[model]["tasks"][result["task"]] = result
        
        # 生成 Markdown 报告
        md = f"""# 🧪 9 模型对比测试报告

**测试日期**: {datetime.now().strftime("%Y-%m-%d %H:%M")}  
**测试任务**: T1(快速脚本) + T2(API 项目) + T3(Bug 修复)  
**评估标准**: auto-coding delivery_check 代码质量检查

---

## 📊 总体排名

| 排名 | 模型 | Provider | T1 时间 | T1 质量 | T2 时间 | T2 质量 | T3 时间 | T3 质量 | 平均分 |
|------|------|----------|---------|---------|---------|---------|---------|---------|--------|
"""
        
        # 计算平均分并排序
        model_scores = []
        for model, data in models_data.items():
            tasks = data["tasks"]
            avg_score = 0
            count = 0
            for task_id in ["T1", "T2", "T3"]:
                if task_id in tasks and tasks[task_id].get("success"):
                    avg_score += tasks[task_id].get("quality_score", {}).get("score", 0)
                    count += 1
            avg_score = avg_score / count if count > 0 else 0
            model_scores.append((model, data["provider"], avg_score, tasks))
        
        model_scores.sort(key=lambda x: x[2], reverse=True)
        
        for rank, (model, provider, avg_score, tasks) in enumerate(model_scores, 1):
            t1 = tasks.get("T1", {})
            t2 = tasks.get("T2", {})
            t3 = tasks.get("T3", {})
            
            t1_time = f"{t1.get('elapsed_time', 'N/A')}s" if t1.get("success") else "❌"
            t1_score = t1.get("quality_score", {}).get("score", "N/A") if t1.get("success") else "❌"
            t2_time = f"{t2.get('elapsed_time', 'N/A')}s" if t2.get("success") else "❌"
            t2_score = t2.get("quality_score", {}).get("score", "N/A") if t2.get("success") else "❌"
            t3_time = f"{t3.get('elapsed_time', 'N/A')}s" if t3.get("success") else "❌"
            t3_score = t3.get("quality_score", {}).get("score", "N/A") if t3.get("success") else "❌"
            
            md += f"| {rank} | {model} | {provider} | {t1_time} | {t1_score} | {t2_time} | {t2_score} | {t3_time} | {t3_score} | {avg_score:.1f} |\n"
        
        md += f"""

---

## 📈 详细结果

"""
        
        for model, data in models_data.items():
            md += f"### {model} ({data['provider']})\n\n"
            for task_id in ["T1", "T2", "T3"]:
                if task_id in data["tasks"]:
                    result = data["tasks"][task_id]
                    status = "✅" if result.get("success") else "❌"
                    md += f"**{task_id}**: {status} "
                    if result.get("success"):
                        md += f"{result.get('elapsed_time')}s, 质量分 {result.get('quality_score', {}).get('score', 'N/A')}\n"
                    else:
                        md += f"错误：{result.get('error', 'Unknown')[:100]}\n"
            md += "\n"
        
        # 保存报告
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md)
        
        # 保存原始数据
        json_path = self.output_dir / "results.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 报告已保存到：{report_path}")
        return report_path


async def main():
    print("🚀 开始 9 模型对比测试")
    print(f"📁 输出目录：{Path(__file__).parent.parent / 'research' / '2026-04-01_9 模型对比测试'}")
    
    tester = ModelTester("/Users/krislu/.nanobot/workspace/research/2026-04-01_9 模型对比测试")
    
    # 逐个测试
    for model in MODELS:
        for task_id, task in TASKS.items():
            result = await tester.test_model(model, task_id, task)
            tester.results.append(result)
            
            # 每个任务之间休息 2 秒
            await asyncio.sleep(2)
    
    # 生成报告
    report_path = tester.generate_report()
    
    print(f"\n✅ 测试完成！报告：{report_path}")


if __name__ == "__main__":
    asyncio.run(main())
