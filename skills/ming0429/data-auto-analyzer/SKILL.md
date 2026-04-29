---
name: data-auto-analyzer
description: 数据自动分析 + 广告投放优化一体化 Skill。当用户上传 Excel/CSV 文件，或提到以下任一场景时必须触发：①通用数据分析（看报表、数据趋势、可视化）；②账户诊断（哪些计划效果差、哪些要暂停、投放诊断、账户体检）；③A/B 测试分析（两组数据对比、哪个版本好、是否显著、置信度）；④日报生成（投放日报、每日汇报、钉钉/飞书周报、对比昨日）。适用于信息流广告优化师、运营、数据分析师。支持巨量引擎、腾讯广告、Meta Ads、Google Ads、快手等平台导出数据，也支持销售、财务、运营等任何结构化表格。即使用户只说"分析一下""看看报表""哪些计划要调整""这俩哪个好""生成日报"，也应触发此 Skill。
metadata:
  homepage: https://clawhub.ai/ming0429/data-auto-analyzer
  version: 3.0.1
  author: guojiaming
  tags: [data-analysis, advertising, ab-test, daily-report, 数据分析, 广告优化, 账户诊断, AB测试, 日报生成]
  clawdbot:
    emoji: 📊
    requires:
      bins: [python3]
      pip: [pandas, openpyxl, xlrd, jinja2, scipy]
      env: []
---

# 数据自动分析 Skill

一体化数据分析与广告优化工具集，包含 **4 个模式**，根据用户意图选择对应模式执行。

## 环境准备（所有模式通用）

```bash
python3 -m venv /home/claude/.venv && source /home/claude/.venv/bin/activate
pip install pandas openpyxl xlrd jinja2 scipy -q
```

## 模式选择决策树

```
用户上传了 Excel/CSV？
├── 是
│   ├── 提到"诊断/体检/哪些要暂停/计划效果差" → 模式 B：账户诊断
│   ├── 提到"日报/汇报/对比昨日" → 模式 D：日报生成
│   ├── 提到"A/B 测试/显著性/哪个版本好" → 模式 C：A/B 测试
│   └── 其他（看报表/分析数据/趋势） → 模式 A：通用分析
└── 否
    └── 用户直接描述两组数据（手工输入） → 模式 C：A/B 测试
```

**不确定时优先询问用户，不要猜。**

---

## 模式 A：通用数据分析

**用途**：任意 Excel/CSV 都能用，自动识别列类型，生成交互式 HTML 报告。

```bash
python3 scripts/analyze.py --file <输入文件> --out /mnt/user-data/outputs/data_report.html
```

**输出**：包含数据概览、指标汇总、异常检测、可分页表格、5 个 ECharts 图表的 HTML。

---

## 模式 B：广告账户诊断器

**用途**：分析广告投放报表，给每条计划打红/黄/绿预警，输出处置建议（暂停/降价/提价/观察）。

```bash
python3 scripts/diagnose.py --file <投放报表.xlsx> --out /mnt/user-data/outputs/diagnose_report.html
```

**诊断规则摘要**（完整说明见 `references/diagnose_rules.md`）：
- 🔴 红色（立即处理）：消耗 > 均值 2 倍但转化为 0、CPA > 均值 3 倍、CTR < 均值 0.3 倍
- 🟡 黄色（需优化）：CPA > 均值 1.5 倍、转化率 < 均值 0.5 倍
- 🟢 绿色（健康）：指标正常或优于均值

脚本自动识别常见列名（消耗/花费/cost、转化/conversion、点击/click、展示/impression 等），识别失败时提示用户手动指定。

---

## 模式 C：A/B 测试结果分析

**用途**：判断两组数据差异是否显著，给出置信度和结论。

两种场景：
- **比例型**（CTR、转化率）→ Z 检验
- **均值型**（CPC、CPA、ROI）→ T 检验

**执行方式 1：手工输入数据**
```bash
python3 scripts/ab_test.py --inline \
  --a-success 120 --a-total 2400 \
  --b-success 150 --b-total 2500 \
  --out /mnt/user-data/outputs/ab_result.html
```

**执行方式 2：从文件**
```bash
python3 scripts/ab_test.py --file <数据.xlsx> \
  --group-col <分组列名> --metric-col <指标列名> \
  --metric-type <rate|mean> \
  --out /mnt/user-data/outputs/ab_result.html
```

详细用法和场景示例见 `references/ab_test_guide.md`。

---

## 模式 D：每日投放日报生成器

**用途**：上传投放报表，生成结构化日报。输出钉钉/飞书可直接粘贴的纯文本版 + HTML 精美版。

```bash
# 单日报表
python3 scripts/daily_report.py --today <今日.xlsx> --out-dir /mnt/user-data/outputs/

# 带昨日对比（推荐）
python3 scripts/daily_report.py --today <今日.xlsx> --yesterday <昨日.xlsx> --out-dir /mnt/user-data/outputs/
```

**输出两个文件**：
- `daily_report.txt` — 纯文本，直接复制到钉钉/飞书/微信
- `daily_report.html` — 精美 HTML 版，适合邮件附件或存档

**日报结构**：核心指标卡片 + 环比涨跌 + TOP 3 最好/最差计划 + 异常提醒 + 明日建议。

详见 `references/daily_report_format.md`。

---

## Notes

- 分析过程完全本地执行，不上传任何数据；生成的 HTML 报告在浏览器打开时会从 CDN (cdnjs.cloudflare.com) 加载 ECharts
- 所有脚本必须保存为 `.py` 文件执行，不支持 `python3 -c` 内联
- 列名完全动态识别，不预设字段名
- 编码自动识别，兼容 UTF-8 / GBK / GB2312
