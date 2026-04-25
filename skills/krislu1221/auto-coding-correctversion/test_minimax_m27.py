#!/usr/bin/env python3
"""
重新测试 MiniMax-M2.7 - 修复响应解析
"""

import json
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path

API_KEY = "sk-api-YOucsplnx6MQm8oqyzuO6Tfo2onhwQszRA-2CIfV7vjPr1gQFbzqCfxqeq1qlNVDT4D4wa4-wdlHvxZ4ldwypzwgsaZQbbnc_vOs3TOTY5UnnK193KEjW7o"

TASKS = {
    "T1": {"name": "快速脚本", "prompt": "请写一个 Python 脚本，功能：1.遍历当前目录下所有.py 文件 2.统计每个文件的行数（非空行）3.输出总行数和每个文件的行数 4.按行数从多到少排序。要求：代码简洁，有错误处理，能直接运行。", "max_time": 60},
    "T2": {"name": "API 项目", "prompt": "请创建一个完整的 Python 项目，功能：1.调用公开 API（如 https://api.github.com/users/{username}）2.获取 GitHub 用户信息并格式化展示。包含以下要求：使用 requests 或 httpx 库、有完整的错误处理、有日志记录、有简单的单元测试、有 README.md 说明使用方法。请生成完整的项目结构和所有文件内容。", "max_time": 180},
    "T3": {"name": "Bug 修复", "prompt": "以下代码有 3 个 Bug，请找出并修复，同时添加测试：import os, shutil; def backup_files(source_dir, backup_dir): for filename in os.listdir(source_dir): source_path = os.path.join(source_dir, filename); backup_path = os.path.join(backup_dir, filename); if os.path.isfile(source_path): shutil.copy2(source_path, backup_path) elif os.path.isdir(source_path): backup_files(source_path, backup_dir); return True。Bug 提示：1.没有检查目标目录是否存在 2.递归调用但没有处理递归备份 3.没有返回值或日志。要求：修复所有 Bug，添加完整的错误处理，添加日志记录，添加单元测试，说明每个 Bug 的问题和修复方案。", "max_time": 240}
}

output_dir = Path("/Users/krislu/.nanobot/workspace/research/2026-04-01_9model_compare")

async def call_minimax(prompt: str, timeout: int) -> str:
    api_base = "https://api.minimaxi.com/anthropic/v1"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_base}/messages",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            json={"model": "MiniMax-M2.7", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4000, "system": "你是一个专业的 Python 开发者，直接输出代码。"},
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"API 错误 {resp.status}: {error[:200]}")
            data = await resp.json()
            # 查找 type=text 的块
            content_list = data.get("content", [])
            text_content = None
            for item in content_list:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_content = item.get("text", "")
                    break
            
            if not text_content:
                # 降级处理
                text_content = content_list[0].get("text", "") if content_list else str(data)
            
            # 提取代码
            if "```python" in text_content:
                code = text_content.split("```python")[1].split("```")[0].strip()
            elif "```" in text_content:
                code = text_content.split("```")[1].split("```")[0].strip()
            else:
                code = text_content
            return code

async def test_model(task_id: str, task: dict) -> dict:
    print(f"\n🧪 测试 MiniMax-M2.7 - {task_id}: {task['name']}", flush=True)
    start_time = time.time()
    try:
        code = await call_minimax(task["prompt"], task["max_time"])
        elapsed = time.time() - start_time
        print(f"  ✅ 完成 - {elapsed:.2f}s, 代码长度：{len(code)}", flush=True)
        return {"model": "MiniMax-M2.7", "provider": "minimax", "task": task_id, "success": True, "elapsed_time": round(elapsed, 2), "code_length": len(code), "code": code[:500]}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ❌ 失败 - {elapsed:.2f}s: {str(e)[:100]}", flush=True)
        return {"model": "MiniMax-M2.7", "provider": "minimax", "task": task_id, "success": False, "elapsed_time": round(elapsed, 2), "error": str(e)}

async def main():
    print("🚀 重新测试 MiniMax-M2.7", flush=True)
    
    results = []
    for task_id, task in TASKS.items():
        result = await test_model(task_id, task)
        results.append(result)
        await asyncio.sleep(2)
    
    # 保存结果
    results_file = output_dir / "minimax_m27_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 结果已保存到：{results_file}", flush=True)
    
    # 更新主结果文件
    main_results_file = output_dir / "results.json"
    if main_results_file.exists():
        with open(main_results_file, "r", encoding="utf-8") as f:
            all_results = json.load(f)
        # 移除旧的 MiniMax-M2.7 失败结果
        all_results = [r for r in all_results if r["model"] != "MiniMax-M2.7"]
        all_results.extend(results)
        with open(main_results_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"📊 已更新主结果文件：{main_results_file}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
