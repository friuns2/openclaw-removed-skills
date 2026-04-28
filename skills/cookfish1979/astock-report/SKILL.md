# A股报告系统

> A股数据驱动型报告自动生成与推送系统，支持晨报 / 收盘小结 / 晚报 / 盘中预警 / IPO周报 / 财经周末要闻

---

## 快速开始

```bash
# 收盘小结（默认当天，可指定历史日期）
python3 /workspace/skills/A-stock-report/scripts/send_close_summary.py
python3 /workspace/skills/A-stock-report/scripts/send_close_summary.py --date 20260413

# 晚报
python3 /workspace/skills/A-stock-report/scripts/send_evening_report.py

# 晨报（需LLM先生成内容，写入 /tmp/morning_report_content.txt）
python3 /workspace/skills/A-stock-report/scripts/send_morning_report.py

# 财经周末要闻（需LLM先生成内容，写入 /tmp/weekend_news_content.txt）
python3 /workspace/skills/A-stock-report/scripts/send_weekend_news.py
python3 /workspace/skills/A-stock-report/scripts/send_weekend_news.py --extract-only  # 仅提取情绪数据

# IPO周报
python3 /workspace/skills/A-stock-report/scripts/send_ipo_report.py

# 盘中预警
python3 /workspace/skills/A-stock-report/scripts/send_intraday_alert.py
```

---

## 三步执行流程（通用）

所有报告统一采用三步流程：

```
第一步：收集数据 / 生成内容
  ↓
第二步：保存 Markdown 文件到 /workspace/projects/A股报告系统/reports/
  ↓
第三步：打印报告 → 推送企业微信
```

---

## 数据来源

| 数据 | 来源 | 接口 |
|------|------|------|
| 六大指数（点位/涨跌幅） | 腾讯实时 API | `qt.gtimg.cn` |
| 富时A50期货（实时） | 腾讯实时 API | `qt.gtimg.cn/q=hf_A50` |
| 涨跌停家数 | AKShare | `stock_zt_pool_em` |
| 炸板率 | AKShare | `stock_zt_pool_em` |
| 北向资金 | AKShare | `stock_hsgt_north_net`（列名：`北向净买额`，需 `.fillna(0)`） |
| 概念板块涨跌（前5/后5） | 妙想 MX → cron LLM兜底 | `claw/query`（概念板块涨幅/跌幅前10） |
| 行业板块涨跌（申万） | AKShare | `stock_board_industry_name_em` |
| 两融余额/融资余额 | AKShare | `stock_margin_detail` |
| 两融交易额/融资买入额 | AKShare | `stock_margin_detail` |
| 两融余额/A股流通市值 | AKShare | `stock_margin_detail` + `总市值` |
| 成交额（今日实时） | 腾讯实时 API | 沪市+深市 |
| 成交额（历史/两融同日期） | AKShare | `stock_sse_deal_daily` + `stock_szse_summary` |
| 沪深300 PE / 历史分位 | AKShare + 腾讯 | AKShare + PE |
| 股市风险溢价 | 本地计算 | PE → 国债收益率 |
| 主力净流入/行业资金 | 妙想 MX | `claw/query` |
| 盘面点评/后市展望 | 妙想 MX | `claw/news-search` |
| 舆情/财经要闻 | 妙想 MX / batch_web_search | `claw/news-search` |

---

## 文件名日期规则

| 报告 | 文件名日期取值 |
|------|--------------|
| 收盘小结 | `--date` 参数值；无参数则取当天 |
| 晚报 | `--date` 参数值；无参数则取当天 |
| 晨报 | 生成当天 |
| 财经周末要闻 | 生成当天 |

> **注意**：晚报内容里的两融余额/北向数据标注日期（如"两融余额（04月13日）"）是数据对应的上一交易日，与文件名日期可能差1天。

---

## 周末要闻情绪轨迹数据来源

一周情绪轨迹从历史报告MD文件中提取，合并规则：

| 指标 | 来源 | key取法 |
|------|------|--------|
| 涨停家数/情绪打分 | 收盘小结 `收盘小结_YYYYMMDD.md` | 从文件名提取 `YYYYMMDD` |
| 北向资金/两融余额/两融比例 | 晚报 `晚报_YYYYMMDD.md` | 从**报告内容**里两融余额那行提取日期作为 key |

两套数据以交易日 key 对齐合并，保证周一到周五趋势线一致。

---

## 防并发锁

各脚本使用独立的锁文件，同时运行互不干扰：

| 脚本 | 锁文件 |
|------|--------|
| `send_close_summary.py` | `/tmp/a_stock_close_summary.lock` |
| `send_evening_report.py` | `/tmp/a_stock_evening.lock` |
| `send_morning_report.py` | `/tmp/a_stock_morning.lock` |
| `send_weekend_news.py` | `/tmp/a_stock_weekend.lock` |
| `send_ipo_report.py` | `/tmp/a_stock_ipo.lock` |
| `send_intraday_alert.py` | `/tmp/a_stock_intraday.lock` |

---

## 报告模板

### 晨报

```
📰 【股市晨报】YYYY年MM月DD日（周X）

━━━ 隔夜全球市场 ━━━
【美股收盘】
▪ 道琼斯：XXXXX.XX点，+/-X.XX%
▪ 标普500：XXXXX.XX点，+/-X.XX%
▪ 纳斯达克：XXXXX.XX点，+/-X.XX%（可附"X连涨/连跌X日"）
▪ VIX恐慌指数：XX.XX（+/-X.XX%），恐慌等级：【XX区间】

【港股及A50】
▪ 恒生指数：XXXX，+/-X.XX%（附简要背景）
▪ 富时A50期货：XXXXX点，+/-X.XX%，偏强/偏弱运行【预判A股明日开盘】

【大宗商品】（可选）
▪ WTI原油：XXX美元/桶，+/-X.XX%
▪ 现货黄金：XXXX美元/盎司，+/-X.XX%

━━━ 财经要闻 ━━━
【1】（标题）｜✅利好/❌利空/⚠️中性 对A股影响
  点评：（2-3句，分析事件对A股情绪/板块的影响）
【2】（标题）｜✅利好/❌利空/⚠️中性 对A股影响
  点评：...
（6-10条，每条含：标题、✅/❌/⚠️标签、2-3句逻辑分析）

━━━ 今日操作建议 ━━━
【大盘研判】
（综合外围市场、宏观政策、量能等因素，给出2-3句综合判断）

【操作建议】
1. 【板块/策略】（期限）：具体建议+附标的
2. 【板块/策略】（期限）：...

【风险提示】
⚠️ （1-3条，最重要的风险）

⚠️ 仅供参考，不构成投资建议。股市有风险，投资需谨慎。
```

### 收盘小结

```
📊 【A股收盘小结】YYYY年MM月DD日

━━━ 一，主要股指表现 ━━━
• 上证指数：XXXX.XX，↑/↓X.XX%
• 深证成指：XXXX.XX，↑/↓X.XX%
• 创业板指：XXXX.XX，↑/↓X.XX%
• 科创50：XXXX.XX，↑/↓X.XX%
• 沪深300：XXXX.XX，↑/↓X.XX%
• 中证500：XXXX.XX，↑/↓X.XX%

━━━ 二，资金流向 ━━━
  主力资金：净流入/流出XX亿（全市场）
  🔺 涨幅前五：
    · 板块名+X.XX%
    · 板块名+X.XX%
    · 板块名+X.XX%
    · 板块名+X.XX%
    · 板块名+X.XX%
  🔻 跌幅前五：
    · 板块名-X.XX%
    · 板块名-X.XX%
    · 板块名-X.XX%

━━━ 四，量化情绪打分 ━━━
━━━ 四，量化情绪打分 ━━━（满分100，6项等权平均）
• 涨停XX家 → X分（满分15）
• 涨跌停比：XX倍 → X分（满分15）
• 北向净流入：+XX亿 → X分（满分20）
• 主力净流入：+XX亿 → X分（满分20）
• 炸板率：+XX% → X分（满分20）
• 沪深300：+X.XX% → X分（满分10）
━━━━━━━━━━━━
综合评分：XX/100 🟢做多｜🟡偏多｜⚪分歧｜🟠偏空谨慎｜🔴冰点

━━━ 五，后市展望 ━━━
（脚本固定文案，cron触发时AI自动补充）

━━━ 数据来源：腾讯财经·东方财富AKShare ━━━
⚠️ 仅供参考，不构成投资建议。股市有风险，投资需谨慎。
```

### 晚报

```
📋 【A股晚报】YYYY年MM月DD日

━━━ A股收盘 ━━━
• 上证指数：XXXX.X，↑/↓X.XX%（可附重要说明，如"创X年X月以来新高"）
• 深证成指：XXXX.X，↑/↓X.XX%
• 创业板指：XXXX.X，↑/↓X.XX%（附说明）
• 科创50：XXXX.X，↑/↓X.XX%
• 沪深300：XXXX.X，↑/↓X.XX%
• 中证500：XXXX.X，↑/↓X.XX%
• 成交额：X.XX万亿元

━━━ 亚太股市 ━━━
• 恒生指数：XXXX，↑/↓X.XX%（附简要背景，如"美伊封锁升级，港股承压"）
• 日经225：XXXXX，↑/↓X.XX%（附背景）
• 韩国综合：XXXX，↑/↓X.XX%（附背景）

━━━ 市场风险偏好 ━━━
• 两融余额（MM月DD日）：XXXXX亿，较前日+/-XXXX亿
• 两融余额/A股流通市值（MM月DD日）= X.XX%
  → 安全区间 ✅（或"⚠️预警/高危"）
• 两融交易额/A股成交额（MM月DD日）= X.X%
  阈值：<7%保守 | 7-11%中性 | >11%过热
  → 比例=X.X% → 中性/过热/保守
• 股市风险溢价（MM月DD日）= X.XX%
  阈值：<3%高估 | 3-6%中性 |>6%低估
  → 溢价率=X.XX% → 高估/中性/低估
• 沪深300 PE = XX.XX，近5年分位点 XX.X%

━━━ 财经要闻 ━━━
【1】（标题）｜✅利好/❌利空/⚠️中性 对A股影响
  点评：（2-3句，分析事件对A股情绪/板块的影响）
【2】...（共5-8条）

━━━ 今日操作建议 ━━━
【大盘研判】（综合判断，2-3句）
【操作建议】
1. 【板块/策略】（期限）：具体建议
2. 【板块/策略】（期限）：...
【风险提示】（1-3条）

⚠️ 仅供参考，不构成投资建议。股市有风险，投资需谨慎。
```

### 财经周末要闻（cron 触发后 LLM 生成）

```
📰 【财经周末要闻】过去48-72小时

━━━ 十条重要财经要闻 ━━━
【1】（标题）→ ✅利好/❌利空
  逻辑：...  交易风险提示：...

━━━ 一周情绪轨迹 ━━━
• 涨停家数趋势：周一X家 → 周二X家 → ... → 周五X家
• 北向资金趋势：周一+/-XX亿 → ... → 周五+/-XX亿
• 两融余额/A股流通市值：周一X.XX% → ... → 周五X.XX%
• 两融交易额占比：周一X.X% → ... → 周五X.X%
• 量化情绪打分：周一XX分 → ... → 周五XX分
• 整体趋势：[升温/降温/震荡]

━━━ 整体市场情绪研判 ━━━
情绪指标总结 | 核心驱动因素 | 当前风险点 | 下周操作参考

⚠️ 仅供参考，不构成投资建议。
```

---

## 定时任务（cron）

| 任务 | 时间（北京时间） | sessionTarget | wakeMode |
|------|---------------|--------------|----------|
| 📰 晨报-推送 | 周一～五 08:00 | isolated | now |
| 📉 收盘小结-推送 | 周一～五 15:30 | isolated | now |
| 📋 晚报-推送 | 周一～五 20:00 | isolated | now |
| 📈 盘中预警 | 周一～五 每5分钟 | isolated | now |
| 📰 财经周末要闻 | 周五 20:00 | isolated | now |
| 📋 A股IPO周报 | 周六 09:00 | isolated | now |

**wakeMode 已设为 `now`**，确保每次按时执行。

---

## 配置文件

- Webhook：`/workspace/keys/wecom_webhook.ini`
- MX_APIKEY（妙想）：`/workspace/keys/mx_api_key.ini`
- 加载器：`/workspace/keys/keys_loader.py`

MX_APIKEY 格式（注意 option 名必须为 `mkt_api_key`）：
```ini
[mx_api_key]
mkt_api_key = mkt_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## 常见问题

**Q：北向资金显示 0 亿？**
A：可能是接口数据为空（节假日/非交易日），或列名变更。检查 `北向净买额` 列是否存在，若有 NaN 值需用 `.fillna(0)`。

**Q：两融数据比当天少一天？**
A：正常现象。两融数据在当天收盘后约 1～2 小时后更新，晚报/收盘小结取到的是上一交易日数据。

**Q：定时任务重复推送？**
A：检查 `wakeMode` 是否为 `now`，并确认脚本锁文件（`/tmp/a_stock_*.lock`）已生效。

**Q：财经要闻/明日操作建议为空？**
A：晚报 cron 已配置 batch_web_search，AI 触发时自动搜索并填充。如仍为空说明搜索未返回有效结果。

**Q：报告内容日期和文件名不对应？**
A：收盘小结文件名=报告日期；晚报文件名=生成当天日期，内容日期=上一交易日；周末要闻以内容里两融余额标注的日期为 key，与收盘小结文件名日期对齐合并。

**Q：如何使用 `--date` 指定历史日期？**
A：`python3 send_close_summary.py --date 20260413`（只支持收盘小结）