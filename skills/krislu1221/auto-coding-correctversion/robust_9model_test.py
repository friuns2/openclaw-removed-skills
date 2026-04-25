#!/usr/bin/env python3
"""
9 模型对比测试脚本 - 带进度保存和重试
"""

import json
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path

API_KEYS = {
    "bailian": "sk-sp-f5a1549b0ad343aa95bc149c118c0119",
    "minimax": "sk-api-YOucsplnx6MQm8oqyzuO6Tfo2onhwQszRA-2CIfV7vjPr1gQFbzqCfxqeq1qlNVDT4D4wa4-wdlHvxZ4ldwypzwgsaZQbbnc_vOs3TOTY5UnnK193KEjW7o"
}

MODELS = [
    {"name": "qwen3.5-plus", "provider": "bailian"},
    {"name": "qwen3-max-2026-01-23", "provider": "bailian"},
    {"name": "qwen3-coder-next", "provider": "bailian"},
    {"name": "qwen3-coder-plus", "provider": "bailian"},
    {"name": "glm-5", "provider": "bailian"},
    {"name": "glm-4.7", "provider": "bailian"},
    {"name": "kimi-k2.5", "provider": "bailian"},
    {"name": "MiniMax-M2.5", "provider": "bailian"},
    {"name": "MiniMax-M2.7", "provider": "minimax"},
]

TASKS = {
    "T1": {"name": "快速脚本", "prompt": "请写一个 Python 脚本，功能：1.遍历当前目录下所有.py 文件 2.统计每个文件的行数（非空行）3.输出总行数和每个文件的行数 4.按行数从多到少排序。要求：代码简洁，有错误处理，能直接运行。", "max_time": 60},
    "T2": {"name": "API 项目", "prompt": "请创建一个完整的 Python 项目，功能：1.调用公开 API（如 https://api.github.com/users/{username}）2.获取 GitHub 用户信息并格式化展示。包含以下要求：使用 requests 或 httpx 库、有完整的错误处理、有日志记录、有简单的单元测试、有 README.md 说明使用方法。请生成完整的项目结构和所有文件内容。", "max_time": 180},
    "T3": {"name": "Bug 修复", "prompt": "以下代码有 3 个 Bug，请找出并修复，同时添加测试：import os, shutil; def backup_files(source_dir, backup_dir): for filename in os.listdir(source_dir): source_path = os.path.join(source_dir, filename); backup_path = os.path.join(backup_dir, filename); if os.path.isfile(source_path): shutil.copy2(source_path, backup_path) elif os.path.isdir(source_path): backup_files(source_path, backup_dir); return True。Bug 提示：1.没有检查目标目录是否存在 2.递归调用但没有处理递归备份 3.没有返回值或日志。要求：修复所有 Bug，添加完整的错误处理，添加日志记录，添加单元测试，说明每个 Bug 的问题和修复方案。", "max_time": 240}
}

output_dir = Path("/Users/krislu/.nanobot/workspace/research/2026-04-01_9model_compare")
output_dir.mkdir(parents=True, exist_ok=True)
results_file = output_dir / "results.json"

# 加载已有结果
results = []
if results_file.exists():
    with open(results_file, "r", encoding="utf-8") as f:
        results = json.load(f)
    print(f"📖 加载已有结果：{len(results)} 个测试")

done_keys = {(r["model"], r["task"]) for r in results if r.get("success")}

async def call_api(model: str, provider: str, prompt: str, timeout: int) -> str:
    if provider == "minimax":
        api_base = "https://api.minimaxi.com/anthropic/v1"
        headers = {"Authorization": f"Bearer {API_KEYS['minimax']}", "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4000, "system": "你是一个专业的 Python 开发者，直接输出代码。"}
    else:
        api_base = "https://coding.dashscope.aliyuncs.com/v1"
        headers = {"Authorization": f"Bearer {API_KEYS['bailian']}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "system", "content": "你是一个专业的 Python 开发者，直接输出代码。"}, {"role": "user", "content": prompt}], "max_tokens": 4000, "temperature": 0.1}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{api_base}/chat/completions" if provider != "minimax" else f"{api_base}/messages", headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"API 错误 {resp.status}: {error[:200]}")
            data = await resp.json()
            if provider == "minimax":
                content = data["content"][0]["text"] if "content" in data else str(data)
            else:
                content = data["choices"][0]["message"]["content"]
            
            # 提取代码
            if "```python" in content:
                code = content.split("```python")[1].split("```")[0].strip()
            elif "```" in content:
                code = content.split("```")[1].split("```")[0].strip()
            else:
                code = content
            return code

async def test_model(model: dict, task_id: str, task: dict, retry: int = 0) -> dict:
    model_name = model["name"]
    provider = model["provider"]
    print(f"\n🧪 测试 {model_name} - {task_id}: {task['name']} (retry={retry})", flush=True)
    start_time = time.time()
    try:
        code = await call_api(model_name, provider, task["prompt"], task["max_time"])
        elapsed = time.time() - start_time
        print(f"  ✅ 完成 - {elapsed:.2f}s, 代码长度：{len(code)}", flush=True)
        return {"model": model_name, "provider": provider, "task": task_id, "success": True, "elapsed_time": round(elapsed, 2), "code_length": len(code), "code": code[:1000]}
    except Exception as e:
        elapsed = time.time() - start_time
        if retry < 2:
            print(f"  ⚠️ 重试 {retry+1}/2 - {str(e)[:80]}", flush=True)
            await asyncio.sleep(5)
            return await test_model(model, task_id, task, retry + 1)
        print(f"  ❌ 失败 - {elapsed:.2f}s: {str(e)[:100]}", flush=True)
        return {"model": model_name, "provider": provider, "task": task_id, "success": False, "elapsed_time": round(elapsed, 2), "error": str(e)}

def save_results():
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"💾 已保存结果到 {results_file}", flush=True)

def generate_report():
    report_path = output_dir / "TEST_REPORT.md"
    md = f"# 🧪 9 模型对比测试报告\n\n**测试日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    md += "## 📊 结果汇总\n\n"
    md += "| 排名 | 模型 | Provider | T1 | T2 | T3 | 平均时间 |\n"
    md += "|------|--------|----------|----|----|----|----------|\n"
    
    model_stats = []
    for model in MODELS:
        model_results = [r for r in results if r["model"] == model["name"]]
        t1 = next((r for r in model_results if r["task"] == "T1"), None)
        t2 = next((r for r in model_results if r["task"] == "T2"), None)
        t3 = next((r for r in model_results if r["task"] == "T3"), None)
        
        t1_str = f"{t1['elapsed_time']}s✅" if t1 and t1.get("success") else "❌"
        t2_str = f"{t2['elapsed_time']}s✅" if t2 and t2.get("success") else "❌"
        t3_str = f"{t3['elapsed_time']}s✅" if t3 and t3.get("success") else "❌"
        
        avg_time = 0
        count = 0
        for t in [t1, t2, t3]:
            if t and t.get("success"):
                avg_time += t["elapsed_time"]
                count += 1
        avg_time = avg_time / count if count > 0 else 0
        
        model_stats.append((model["name"], model["provider"], t1_str, t2_str, t3_str, avg_time))
    
    # 按平均时间排序
    model_stats.sort(key=lambda x: x[5] if x[5] > 0 else float('inf'))
    
    for rank, (name, provider, t1, t2, t3, avg) in enumerate(model_stats, 1):
        md += f"| {rank} | {name} | {provider} | {t1} | {t2} | {t3} | {avg:.1f}s |\n"
    
    md += "\n## 📝 详细结果\n\n见 `results.json`\n"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"📄 报告已保存到 {report_path}", flush=True)

async def main():
    print("🚀 开始 9 模型对比测试", flush=True)
    print(f"📁 输出目录：{output_dir}", flush=True)
    print(f"📊 已完成：{len(done_keys)}/27", flush=True)
    
    for model in MODELS:
        for task_id, task in TASKS.items():
            if (model["name"], task_id) in done_keys:
                print(f"⏭️ 跳过 {model['name']} - {task_id} (已完成)", flush=True)
                continue
            
            result = await test_model(model, task_id, task)
            results.append(result)
            save_results()
            await asyncio.sleep(2)
    
    generate_report()
    print(f"\n✅ 测试完成！", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
