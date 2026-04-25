#!/usr/bin/env python3
"""模型代码质量测试 - 禁用代理"""

import os
# 禁用代理
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

import time
import json
import httpx
from pathlib import Path
from delivery_check import DeliveryChecker, CheckStatus

# 加载配置
config = json.load(open(Path.home() / '.nanobot' / 'config.json'))

TASK = "创建一个 Python 脚本，统计当前目录下所有.py 文件的行数"

print("=" * 60)
print("🧪 模型代码质量对比测试 (禁用代理)")
print("=" * 60)

results = []

# ============ MiniMax ============
print("\n🤖 MiniMax-M2.7...", end=" ", flush=True)
start = time.time()

try:
    # 禁用代理
    with httpx.Client() as client:
        resp = client.post(
            "https://api.minimaxi.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config['providers']['minimax']['apiKey']}",
                "Content-Type": "application/json"
            },
            json={
                "model": "MiniMax-M2.7",
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": f"任务：{TASK}\n\n只返回 Python 代码："}]
            },
            timeout=30
        )
    result = resp.json()
    code = result['choices'][0]['message']['content'].replace('```python', '').replace('```', '').strip()
    t = time.time() - start
    print(f"✅ {t:.2f}s")
    
    checker = DeliveryChecker(strict=True)
    report = checker.check(code, TASK)
    score = sum(100 if i.status == CheckStatus.PASS else 50 if i.status == CheckStatus.WARNING else 0 for i in report.items) / (report.total_checks * 100) * 100
    print(f"📊 {score:.1f}% | ✅{report.passed} ❌{report.failed} ⚠️{report.warnings}")
    results.append({"model": "MiniMax", "time": t, "score": score})
except Exception as e:
    print(f"❌ {e}")

# ============ Qwen ============
print("\n🤖 Qwen3.5-Plus...", end=" ", flush=True)
start = time.time()

try:
    with httpx.Client() as client:
        resp = client.post(
            "https://coding.dashscope.aliyuncs.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config['providers']['dashscope']['apiKey']}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen3.5-plus",
                "max_tokens": 2048,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": f"任务：{TASK}\n\n只返回 Python 代码："}]
            },
            timeout=30
        )
    result = resp.json()
    code = result['choices'][0]['message']['content'].replace('```python', '').replace('```', '').strip()
    t = time.time() - start
    print(f"✅ {t:.2f}s")
    
    checker = DeliveryChecker(strict=True)
    report = checker.check(code, TASK)
    score = sum(100 if i.status == CheckStatus.PASS else 50 if i.status == CheckStatus.WARNING else 0 for i in report.items) / (report.total_checks * 100) * 100
    print(f"📊 {score:.1f}% | ✅{report.passed} ❌{report.failed} ⚠️{report.warnings}")
    results.append({"model": "Qwen", "time": t, "score": score})
except Exception as e:
    print(f"❌ {e}")

# ============ 汇总 ============
print("\n" + "=" * 60)
for r in results:
    print(f"{r['model']}: {r['time']:.2f}s | {r['score']:.1f}分")
print("=" * 60)
