#!/usr/bin/env python3
"""
模型代码质量对比测试
直接用不同模型生成代码，然后用 auto-coding 的 delivery_check 评估
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 导入 auto-coding 的交付检查模块
import sys
sys.path.insert(0, str(Path(__file__).parent))
from delivery_check import DeliveryChecker, CheckStatus


# 测试任务定义
TEST_TASKS = [
    {
        "id": "T1",
        "name": "快速脚本",
        "description": "创建一个 Python 脚本，统计当前目录下所有 .py 文件的行数",
        "complexity": "simple"
    },
    {
        "id": "T2", 
        "name": "数据处理",
        "description": "创建一个函数，读取 CSV 文件，计算每列的平均值、最大值、最小值",
        "complexity": "medium"
    },
    {
        "id": "T3",
        "name": "API 客户端",
        "description": "创建一个 HTTP API 客户端类，支持 GET/POST 请求、超时控制、错误重试",
        "complexity": "complex"
    }
]


# 模型配置
MODELS = [
    {
        "id": "minimax",
        "name": "MiniMax-M2.7",
        "model": "MiniMax-M2.7",
        "provider": "minimax",
        "api_base": "https://api.minimaxi.com/anthropic"
    },
    {
        "id": "qwen",
        "name": "Qwen3.5-Plus",
        "model": "qwen3.5-plus",
        "provider": "dashscope",
        "api_base": "https://coding.dashscope.aliyuncs.com/v1"
    }
]


def load_config() -> dict:
    """加载 nanobot 配置"""
    config_path = Path.home() / ".nanobot" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_code_with_model(task: dict, model: dict, config: dict) -> Tuple[str, float, int]:
    """
    使用指定模型生成代码
    
    Returns:
        (code, time_cost, tokens_used)
    """
    import httpx
    
    api_key = config['providers'].get(model['provider'], {}).get('apiKey', '')
    
    prompt = f"""请完成以下编程任务，只返回 Python 代码，不要解释：

任务：{task['description']}

要求：
1. 代码完整可运行
2. 有适当的错误处理
3. 有文档字符串和注释
4. 有简单的测试或使用示例

直接返回代码："""

    start_time = time.time()
    
    try:
        if model['provider'] == 'minimax':
            # MiniMax API (Anthropic 兼容)
            response = httpx.post(
                f"{model['api_base']}/messages",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model['model'],
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            result = response.json()
            code = result['content'][0]['text']
            tokens = result.get('usage', {}).get('total_tokens', 0)
            
        elif model['provider'] == 'dashscope':
            # DashScope API (OpenAI 兼容)
            response = httpx.post(
                f"{model['api_base']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model['model'],
                    "max_tokens": 4096,
                    "temperature": 0.1,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            result = response.json()
            code = result['choices'][0]['message']['content']
            tokens = result.get('usage', {}).get('total_tokens', 0)
        else:
            raise ValueError(f"不支持的 provider: {model['provider']}")
        
        elapsed = time.time() - start_time
        
        # 清理代码块标记
        code = code.replace("```python", "").replace("```", "").strip()
        
        return code, elapsed, tokens
        
    except Exception as e:
        print(f"❌ {model['name']} 调用失败：{e}")
        return "", time.time() - start_time, 0


def evaluate_code(code: str, task: str) -> dict:
    """使用 delivery_check 评估代码质量"""
    checker = DeliveryChecker(strict=True)
    report = checker.check(code, task)
    
    # 计算综合得分
    total = report.total_checks
    passed = report.passed
    warnings = report.warnings
    
    # 得分计算：pass=100, warning=50, fail=0
    score = 0
    for item in report.items:
        if item.status == CheckStatus.PASS:
            score += 100
        elif item.status == CheckStatus.WARNING:
            score += 50
        # FAIL = 0
    
    max_score = total * 100
    percentage = (score / max_score * 100) if max_score > 0 else 0
    
    return {
        "total_checks": total,
        "passed": passed,
        "failed": report.failed,
        "warnings": warnings,
        "score": round(percentage, 1),
        "ready_to_deliver": report.ready_to_deliver,
        "suggestions": report.suggestions[:3]  # 最多 3 条建议
    }


def run_test():
    """运行完整测试"""
    print("=" * 70)
    print("🧪 模型代码质量对比测试")
    print("=" * 70)
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"任务数：{len(TEST_TASKS)} | 模型数：{len(MODELS)}")
    print("=" * 70)
    
    config = load_config()
    results = []
    
    for task in TEST_TASKS:
        print(f"\n📋 任务 {task['id']}: {task['name']} ({task['complexity']})")
        print(f"   {task['description'][:60]}...")
        print("-" * 70)
        
        task_results = {
            "task_id": task['id'],
            "task_name": task['name'],
            "complexity": task['complexity'],
            "models": {}
        }
        
        for model in MODELS:
            print(f"\n   🤖 {model['name']} 生成中...", end=" ", flush=True)
            
            code, time_cost, tokens = generate_code_with_model(task, model, config)
            
            if not code:
                print("❌ 失败")
                continue
            
            print(f"✅ {time_cost:.2f}s | {tokens} tokens")
            
            # 评估代码质量
            eval_result = evaluate_code(code, task['description'])
            
            print(f"   📊 质量评分：{eval_result['score']}% | "
                  f"✅{eval_result['passed']} ❌{eval_result['failed']} ⚠️{eval_result['warnings']} | "
                  f"{'✅可交付' if eval_result['ready_to_deliver'] else '❌需改进'}")
            
            task_results['models'][model['id']] = {
                "model_name": model['name'],
                "time_cost": round(time_cost, 2),
                "tokens": tokens,
                "code_length": len(code),
                "evaluation": eval_result,
                "code": code[:500] + "..." if len(code) > 500 else code  # 只保存前 500 字符
            }
        
        results.append(task_results)
    
    # 生成汇总报告
    print("\n" + "=" * 70)
    print("📈 测试汇总")
    print("=" * 70)
    
    summary = []
    for task_result in results:
        for model_id, model_data in task_result['models'].items():
            summary.append({
                "task": task_result['task_id'],
                "model": model_id,
                "time": model_data['time_cost'],
                "score": model_data['evaluation']['score'],
                "deliverable": model_data['evaluation']['ready_to_deliver']
            })
    
    # 按模型分组统计
    for model in MODELS:
        model_data = [s for s in summary if s['model'] == model['id']]
        if model_data:
            avg_time = sum(d['time'] for d in model_data) / len(model_data)
            avg_score = sum(d['score'] for d in model_data) / len(model_data)
            deliverable_count = sum(1 for d in model_data if d['deliverable'])
            
            print(f"\n{model['name']}:")
            print(f"  ⏱️  平均耗时：{avg_time:.2f}s")
            print(f"  📊 平均质量分：{avg_score:.1f}%")
            print(f"  ✅ 可交付率：{deliverable_count}/{len(model_data)}")
    
    # 保存详细报告
    report_path = Path(__file__).parent / "model_code_quality_test.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "tasks": TEST_TASKS,
            "models": MODELS,
            "results": results,
            "summary": summary
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细报告已保存：{report_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_test()
