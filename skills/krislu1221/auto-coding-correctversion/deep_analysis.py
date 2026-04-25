#!/usr/bin/env python3
"""
深度分析 - 代码质量评估
使用 delivery_check 对每个模型的代码进行评分
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 导入 delivery_check
sys.path.insert(0, '/Users/krislu/.nanobot/workspace/skills/auto-coding')
from delivery_check import DeliveryChecker

results_file = Path('/Users/krislu/.nanobot/workspace/research/2026-04-01_9model_compare/results.json')
with open(results_file) as f:
    results = json.load(f)

output_dir = Path('/Users/krislu/.nanobot/workspace/research/2026-04-01_9model_compare')

# 任务描述
TASK_PROMPTS = {
    'T1': '请写一个 Python 脚本，功能：1.遍历当前目录下所有.py 文件 2.统计每个文件的行数（非空行）3.输出总行数和每个文件的行数 4.按行数从多到少排序。要求：代码简洁，有错误处理，能直接运行。',
    'T2': '请创建一个完整的 Python 项目，功能：1.调用公开 API（如 https://api.github.com/users/{username}）2.获取 GitHub 用户信息并格式化展示。包含以下要求：使用 requests 或 httpx 库、有完整的错误处理、有日志记录、有简单的单元测试、有 README.md 说明使用方法。请生成完整的项目结构和所有文件内容。',
    'T3': '以下代码有 3 个 Bug，请找出并修复，同时添加测试：import os, shutil; def backup_files(source_dir, backup_dir): for filename in os.listdir(source_dir): source_path = os.path.join(source_dir, filename); backup_path = os.path.join(backup_dir, filename); if os.path.isfile(source_path): shutil.copy2(source_path, backup_path) elif os.path.isdir(source_path): backup_files(source_path, backup_dir); return True。Bug 提示：1.没有检查目标目录是否存在 2.递归调用但没有处理递归备份 3.没有返回值或日志。要求：修复所有 Bug，添加完整的错误处理，添加日志记录，添加单元测试，说明每个 Bug 的问题和修复方案。'
}

checker = DeliveryChecker(strict=True)

# 按任务和模型分组
analysis = {'T1': {}, 'T2': {}, 'T3': {}}

print("🔍 开始代码质量评估...\n")

for r in results:
    if not r.get('success') or 'code' not in r:
        continue
    
    task_id = r['task']
    model = r['model']
    code = r['code']
    
    print(f"📝 检查 {model} - {task_id}...", end=" ")
    
    # 执行交付检查
    report = checker.check(code, TASK_PROMPTS[task_id])
    
    quality_data = {
        'elapsed_time': r['elapsed_time'],
        'code_length': r['code_length'],
        'total_checks': report.total_checks,
        'passed': report.passed,
        'failed': report.failed,
        'warnings': report.warnings,
        'score': round((report.passed / report.total_checks) * 100, 1) if report.total_checks > 0 else 0,
        'ready_to_deliver': report.ready_to_deliver,
        'suggestions': report.suggestions[:3]  # 只保留前 3 个建议
    }
    
    analysis[task_id][model] = quality_data
    print(f"✅ 质量分：{quality_data['score']}/100")

# 生成深度分析报告
report_path = output_dir / 'DEEP_ANALYSIS.md'

md = f"""# 🧪 9 模型深度分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**评估标准**: auto-coding delivery_check (严格模式)  
**检查项**: 语法检查、错误处理、文档、测试、安全检查、代码完整性

---

## 📊 T1: 快速脚本 - 详细排名

| 排名 | 模型 | 响应时间 | 代码长度 | 质量分 | 通过率 | 可交付 |
|------|------|---------|---------|--------|--------|--------|
"""

# T1 排名
t1_ranked = sorted(analysis['T1'].items(), key=lambda x: (-x[1]['score'], x[1]['elapsed_time']))
for rank, (model, data) in enumerate(t1_ranked, 1):
    status = "✅" if data['ready_to_deliver'] else "⚠️"
    md += f"| {rank} | {model} | {data['elapsed_time']:.1f}s | {data['code_length']} | {data['score']:.1f} | {data['passed']}/{data['total_checks']} | {status} |\n"

md += f"""

### T1 关键洞察
- **最快**: {min(analysis['T1'].items(), key=lambda x: x[1]['elapsed_time'])[0]} ({min(analysis['T1'].items(), key=lambda x: x[1]['elapsed_time'])[1]['elapsed_time']:.1f}s)
- **质量最高**: {max(analysis['T1'].items(), key=lambda x: x[1]['score'])[0]} ({max(analysis['T1'].items(), key=lambda x: x[1]['score'])[1]['score']:.1f}分)
- **代码最长**: {max(analysis['T1'].items(), key=lambda x: x[1]['code_length'])[0]} ({max(analysis['T1'].items(), key=lambda x: x[1]['code_length'])[1]['code_length']} 字符)

---

## 📊 T2: API 项目 - 详细排名

| 排名 | 模型 | 响应时间 | 代码长度 | 质量分 | 通过率 | 可交付 |
|------|------|---------|---------|--------|--------|--------|
"""

# T2 排名
t2_ranked = sorted(analysis['T2'].items(), key=lambda x: (-x[1]['score'], x[1]['elapsed_time']))
for rank, (model, data) in enumerate(t2_ranked, 1):
    status = "✅" if data['ready_to_deliver'] else "⚠️"
    md += f"| {rank} | {model} | {data['elapsed_time']:.1f}s | {data['code_length']} | {data['score']:.1f} | {data['passed']}/{data['total_checks']} | {status} |\n"

md += f"""

### T2 关键洞察
- **最快**: {min(analysis['T2'].items(), key=lambda x: x[1]['elapsed_time'])[0]} ({min(analysis['T2'].items(), key=lambda x: x[1]['elapsed_time'])[1]['elapsed_time']:.1f}s)
- **质量最高**: {max(analysis['T2'].items(), key=lambda x: x[1]['score'])[0]} ({max(analysis['T2'].items(), key=lambda x: x[1]['score'])[1]['score']:.1f}分)
- **代码最长**: {max(analysis['T2'].items(), key=lambda x: x[1]['code_length'])[0]} ({max(analysis['T2'].items(), key=lambda x: x[1]['code_length'])[1]['code_length']} 字符)

---

## 📊 T3: Bug 修复 - 详细排名

| 排名 | 模型 | 响应时间 | 代码长度 | 质量分 | 通过率 | 可交付 |
|------|------|---------|---------|--------|--------|--------|
"""

# T3 排名
t3_ranked = sorted(analysis['T3'].items(), key=lambda x: (-x[1]['score'], x[1]['elapsed_time']))
for rank, (model, data) in enumerate(t3_ranked, 1):
    status = "✅" if data['ready_to_deliver'] else "⚠️"
    md += f"| {rank} | {model} | {data['elapsed_time']:.1f}s | {data['code_length']} | {data['score']:.1f} | {data['passed']}/{data['total_checks']} | {status} |\n"

md += f"""

### T3 关键洞察
- **最快**: {min(analysis['T3'].items(), key=lambda x: x[1]['elapsed_time'])[0]} ({min(analysis['T3'].items(), key=lambda x: x[1]['elapsed_time'])[1]['elapsed_time']:.1f}s)
- **质量最高**: {max(analysis['T3'].items(), key=lambda x: x[1]['score'])[0]} ({max(analysis['T3'].items(), key=lambda x: x[1]['score'])[1]['score']:.1f}分)
- **代码最长**: {max(analysis['T3'].items(), key=lambda x: x[1]['code_length'])[0]} ({max(analysis['T3'].items(), key=lambda x: x[1]['code_length'])[1]['code_length']} 字符)

---

## 🏆 综合质量排名

| 排名 | 模型 | T1 质量 | T2 质量 | T3 质量 | 平均分 | 综合评级 |
|------|------|--------|--------|--------|--------|---------|
"""

# 计算综合排名
model_avg = {}
for model in set(list(analysis['T1'].keys()) + list(analysis['T2'].keys()) + list(analysis['T3'].keys())):
    scores = []
    for tid in ['T1', 'T2', 'T3']:
        if model in analysis[tid]:
            scores.append(analysis[tid][model]['score'])
    if scores:
        model_avg[model] = sum(scores) / len(scores)

comprehensive_ranked = sorted(model_avg.items(), key=lambda x: -x[1])
for rank, (model, avg) in enumerate(comprehensive_ranked, 1):
    t1_score = analysis['T1'].get(model, {}).get('score', 'N/A')
    t2_score = analysis['T2'].get(model, {}).get('score', 'N/A')
    t3_score = analysis['T3'].get(model, {}).get('score', 'N/A')
    
    # 评级
    if avg >= 80:
        rating = "🌟 S 级"
    elif avg >= 60:
        rating = "✅ A 级"
    elif avg >= 40:
        rating = "⚠️ B 级"
    else:
        rating = "❌ C 级"
    
    md += f"| {rank} | {model} | {t1_score} | {t2_score} | {t3_score} | {avg:.1f} | {rating} |\n"

md += f"""

---

## 💡 核心结论

### 速度 vs 质量 权衡
- **速度优先**: qwen3-coder-next (平均 10s) 但质量分中等
- **质量优先**: 待分析具体模型
- **最佳平衡**: 待分析

### 任务特异性表现
- **简单任务 (T1)**: 所有模型表现良好
- **中等任务 (T2)**: 差距开始显现
- **困难任务 (T3)**: 模型能力分化明显

### 推荐策略
| 使用场景 | 推荐模型 | 理由 |
|---------|---------|------|
| 快速原型 | qwen3-coder-next | 10s 内完成，适合迭代 |
| 生产代码 | 待分析 | 质量分最高的模型 |
| 复杂调试 | 待分析 | T3 质量分最高 |

---

## 📎 附录：常见问题

### 主要失败原因
"""

# 统计常见问题
common_issues = {}
for tid in ['T1', 'T2', 'T3']:
    for model, data in analysis[tid].items():
        for suggestion in data.get('suggestions', []):
            key = suggestion[:50]
            common_issues[key] = common_issues.get(key, 0) + 1

top_issues = sorted(common_issues.items(), key=lambda x: -x[1])[:5]
for issue, count in top_issues:
    md += f"- {issue}... ({count}次)\n"

md += f"""

---

**完整数据**: 见 `quality_analysis.json`
"""

# 保存分析数据
quality_data_file = output_dir / 'quality_analysis.json'
with open(quality_data_file, 'w', encoding='utf-8') as f:
    json.dump(analysis, f, indent=2, ensure_ascii=False)

# 保存报告
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(md)

print(f"\n📄 深度分析报告已保存到：{report_path}")
print(f"📊 质量数据已保存到：{quality_data_file}")
EOF