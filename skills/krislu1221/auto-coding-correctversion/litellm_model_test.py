#!/usr/bin/env python3
"""使用 LiteLLM 测试模型代码质量"""

import time
import json
from pathlib import Path
from litellm import completion
from delivery_check import DeliveryChecker, CheckStatus

# 加载配置
config = json.load(open(Path.home() / '.nanobot' / 'config.json'))

TASK = "创建一个 Python 脚本，统计当前目录下所有.py 文件的行数"

print("=" * 60)
print("🧪 模型代码质量对比测试 (LiteLLM)")
print("=" * 60)
print(f"任务：{TASK}")
print("-" * 60)

results = []

# ============ MiniMax-M2.7 ============
print("\n🤖 MiniMax-M2.7 生成中...", end=" ", flush=True)
start = time.time()

try:
    response = completion(
        model="minimax/MiniMax-M2.7",
        api_key=config['providers']['minimax']['apiKey'],
        api_base=config['providers']['minimax'].get('apiBase'),
        messages=[{"role": "user", "content": f"请完成以下编程任务，只返回 Python 代码：\n\n任务：{TASK}\n\n直接返回代码："}],
        max_tokens=2048,
        timeout=30
    )
    
    code = response.choices[0].message.content.replace('```python', '').replace('```', '').strip()
    t = time.time() - start
    tokens = response.usage.total_tokens if response.usage else 0
    print(f"✅ {t:.2f}s | {tokens} tokens")
    
    # 评估
    checker = DeliveryChecker(strict=True)
    report = checker.check(code, TASK)
    score = sum(100 if i.status == CheckStatus.PASS else 50 if i.status == CheckStatus.WARNING else 0 for i in report.items) / (report.total_checks * 100) * 100
    deliverable = '✅可交付' if report.ready_to_deliver else '❌需改进'
    print(f"📊 质量分：{score:.1f}% | ✅{report.passed} ❌{report.failed} ⚠️{report.warnings} | {deliverable}")
    
    results.append({"model": "MiniMax-M2.7", "time": t, "score": score, "deliverable": report.ready_to_deliver, "report": report})
except Exception as e:
    print(f"❌ 失败：{e}")

# ============ Qwen3.5-Plus ============
print("\n🤖 Qwen3.5-Plus 生成中...", end=" ", flush=True)
start = time.time()

try:
    response = completion(
        model="dashscope/qwen3.5-plus",
        api_key=config['providers']['dashscope']['apiKey'],
        api_base=config['providers']['dashscope'].get('apiBase'),
        messages=[{"role": "user", "content": f"请完成以下编程任务，只返回 Python 代码：\n\n任务：{TASK}\n\n直接返回代码："}],
        max_tokens=2048,
        temperature=0.1,
        timeout=30
    )
    
    code = response.choices[0].message.content.replace('```python', '').replace('```', '').strip()
    t = time.time() - start
    tokens = response.usage.total_tokens if response.usage else 0
    print(f"✅ {t:.2f}s | {tokens} tokens")
    
    # 评估
    checker = DeliveryChecker(strict=True)
    report = checker.check(code, TASK)
    score = sum(100 if i.status == CheckStatus.PASS else 50 if i.status == CheckStatus.WARNING else 0 for i in report.items) / (report.total_checks * 100) * 100
    deliverable = '✅可交付' if report.ready_to_deliver else '❌需改进'
    print(f"📊 质量分：{score:.1f}% | ✅{report.passed} ❌{report.failed} ⚠️{report.warnings} | {deliverable}")
    
    results.append({"model": "Qwen3.5-Plus", "time": t, "score": score, "deliverable": report.ready_to_deliver, "report": report})
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
    print(f"  可交付：{'✅' if r['deliverable'] else '❌'}")
    if 'report' in r and r['report'].suggestions:
        print(f"  💡 建议：{r['report'].suggestions[0]}")

print("=" * 60)
