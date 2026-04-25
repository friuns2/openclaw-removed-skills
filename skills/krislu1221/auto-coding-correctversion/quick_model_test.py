#!/usr/bin/env python3
"""模型代码质量对比测试 - 简化版"""

import json
import time
import httpx
from pathlib import Path
from delivery_check import DeliveryChecker, CheckStatus

# 加载配置
config = json.load(open(Path.home() / '.nanobot' / 'config.json'))

# 测试任务
TASK = "创建一个 Python 脚本，统计当前目录下所有.py 文件的行数"

print("=" * 60)
print("🧪 模型代码质量对比测试")
print("=" * 60)
print(f"任务：{TASK}")
print("-" * 60)

results = []

# ============ MiniMax-M2.7 ============
print("\n🤖 MiniMax-M2.7 生成中...", end=" ", flush=True)
start = time.time()
try:
    resp = httpx.post(
        "https://api.minimaxi.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {config['providers']['minimax']['apiKey']}",
            "Content-Type": "application/json"
        },
        json={
            "model": "MiniMax-M2.7",
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": f"请完成以下编程任务，只返回 Python 代码：\n\n任务：{TASK}\n\n直接返回代码："}]
        },
        timeout=30
    )
    result = resp.json()
    code = result['choices'][0]['message']['content'].replace('```python', '').replace('```', '').strip()
    t1 = time.time() - start
    tokens = result.get('usage', {}).get('total_tokens', 0)
    print(f"✅ {t1:.2f}s | {tokens} tokens")
    
    # 评估
    checker = DeliveryChecker(strict=True)
    report = checker.check(code, TASK)
    score = sum(100 if i.status == CheckStatus.PASS else 50 if i.status == CheckStatus.WARNING else 0 for i in report.items) / (report.total_checks * 100) * 100
    print(f"📊 质量分：{score:.1f}% | ✅{report.passed} ❌{report.failed} ⚠️{report.warnings} | {'✅可交付' if report.ready_to_deliver else '❌需改进'}")
    
    results.append({"model": "MiniMax-M2.7", "time": t1, "score": score, "report": report})
except Exception as e:
    print(f"❌ 失败：{e}")

# ============ Qwen3.5-Plus ============
print("\n🤖 Qwen3.5-Plus 生成中...", end=" ", flush=True)
start = time.time()
try:
    resp = httpx.post(
        "https://coding.dashscope.aliyuncs.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {config['providers']['dashscope']['apiKey']}",
            "Content-Type": "application/json"
        },
        json={
            "model": "qwen3.5-plus",
            "max_tokens": 2048,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": f"请完成以下编程任务，只返回 Python 代码：\n\n任务：{TASK}\n\n直接返回代码："}]
        },
        timeout=30
    )
    result = resp.json()
    code = result['choices'][0]['message']['content'].replace('```python', '').replace('```', '').strip()
    t2 = time.time() - start
    tokens = result.get('usage', {}).get('total_tokens', 0)
    print(f"✅ {t2:.2f}s | {tokens} tokens")
    
    # 评估
    checker = DeliveryChecker(strict=True)
    report = checker.check(code, TASK)
    score = sum(100 if i.status == CheckStatus.PASS else 50 if i.status == CheckStatus.WARNING else 0 for i in report.items) / (report.total_checks * 100) * 100
    print(f"📊 质量分：{score:.1f}% | ✅{report.passed} ❌{report.failed} ⚠️{report.warnings} | {'✅可交付' if report.ready_to_deliver else '❌需改进'}")
    
    results.append({"model": "Qwen3.5-Plus", "time": t2, "score": score, "report": report})
except Exception as e:
    print(f"❌ 失败：{e}")

# ============ 汇总 ============
print("\n" + "=" * 60)
print("📈 测试结果汇总")
print("=" * 60)

for r in results:
    print(f"\n{r['model']}:")
    print(f"  ⏱️  耗时：{r['time']:.2f}s")
    print(f"  📊 质量分：{r['score']:.1f}%")
    print(f"  详情：✅{r['report'].passed} ❌{r['report'].failed} ⚠️{r['report'].warnings}")
    if r['report'].suggestions:
        print(f"  💡 建议：{r['report'].suggestions[0]}")

print("=" * 60)
