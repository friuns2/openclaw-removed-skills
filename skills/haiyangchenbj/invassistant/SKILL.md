---
name: invassistant
description: |
  Investment portfolio management system covering A-shares (A股), US stocks (美股), and HK stocks (港股).
  A-shares: Three-condition entry system (引擎评分≥80 + 价格≤目标 + MA20企稳) with v1.4 enhancements
  (elastic window, dynamic target price, resilience downgrade, engine+momentum dual-track, earnings rules).
  US stocks: Three Red Lines entry system (emotion release + technical support + market risk) with
  multi-layered exit engine (take-profit tiers, stop-loss, trend-break, momentum-fade, systemic-risk).
  HK stocks: Position reduction strategy for company stock incentives.
  Supports pre-market analysis, post-market review, trading signal checks, and Notion sync.
  Trigger keywords: 检查持仓, 持仓信号, 今日信号, 红线检查, 建仓检查, 减仓信号, 止盈检查, 止损检查,
  退出信号, 清仓检查, 趋势破位, 动量衰竭, portfolio check, trading signal, entry check, exit check,
  red line check, stock signal, take profit, stop loss, 投资信号, 交易信号, 持仓检查, 详细分析,
  盘前分析, 盘后复盘, 选股引擎, 三条件, 弹性窗口, 动态目标价, 韧性降级, 动量双轨, 财报规则,
  A股策略, 美股策略, 港股持仓, 投资组合, 调仓纪律, 周五风险清单, 精选层, 观察池, ETF底仓,
  pre-market analysis, post-market review, stock screener, earnings season.
allowed-tools:
  - read_file
  - write_to_file
  - replace_in_file
  - execute_command
disable: false
metadata:
  openclaw:
    requires:
      bins:
        - python3
      env: []
    tags:
      - investment
      - trading
      - portfolio
      - signal
      - stock
      - finance
      - a-share
      - hk-stock
---

# InvAssistant v1.4 — 投资组合管理系统

跨市场投资组合管理：A股三条件建仓系统 + 美股三红线信号系统 + 港股减持策略。

**策略版本**: v1.4（2026-04-23 月度复盘优化）
**配置文件**: `my_portfolio.json`（A股+港股） / `invassistant-config.json`（美股信号）

---

## 一、A股策略体系（v1.4）

### 1.1 三条件建仓系统

三条件是**交叉验证过滤器**，全部满足才允许建仓：

| 条件 | 指标 | 标准 | 数据源 |
|------|------|------|--------|
| ① 引擎评分 | 选股引擎核心池评分 | ≥80分 + 连续3日在榜 | 每日引擎扫描 |
| ② 价格到位 | 当前价 ≤ 目标价 | 静态目标价或动态目标价 | 实时行情 |
| ③ MA20企稳 | 20日均线走平或拐头 | MA20 delta ≥ -0.05 | K线计算 |

### 1.2 v1.4 优化规则

#### 规则1：弹性窗口（Elastic Window）
- **触发**：2/3条件满足，且第三个偏差≤10%
- **动作**：可半仓试探（计划首笔股数×50%）
- **偏差定义**：
  - 引擎78-79分 → 视为≤10%偏差（门槛80）
  - 价格超目标≤5% → 偏差内
  - MA20 delta在[-0.05, 0] → 接近走平

#### 规则2：动态目标价（Dynamic Target）
- **公式**：`实际目标 = min(静态目标价, MA20 × 0.95)`
- **更新频率**：每周盘后更新一次
- 当MA20持续下行导致动态价远低于静态价时，以动态价为准

#### 规则3：A股韧性降级（Resilience Downgrade）
- **触发**：VIX>25 或外围单日跌>2%，但A股当日跌幅<0.5%
- **动作**：防守等级从"观望"降为"正常"，不因外围恐慌延迟满足条件的建仓
- **确认**：连续2个交易日A股韧性确认后生效，单日不算

#### 规则4：引擎+动量双轨（Engine + Momentum Dual-Track）
- **78-80分区间**：额外检查20日涨幅
  - 20日涨幅>8% + 引擎≥78 → 恢复跟踪（纳入弹性窗口评估）
  - 引擎86分但20日跌幅>5% → 提示"高分低动量"，谨慎建仓时机

#### 规则5：财报季规则（Earnings Season）
- **冻结期**：财报发布前3个交易日冻结该标的建仓，已有持仓不受影响
- **财报后决策树**：
  - 营收+净利双超预期 → 解冻 + 正常三条件
  - 营收达标+净利小幅低于预期(<5%) → 解冻但首笔减半
  - 营收或净利大幅低于预期(>10%) → 冻结延长1周
  - 重大意外(商誉减值等) → 降级或移除精选层

#### 规则6：周五风险清单（Friday Risk Checklist）
- 每周五盘后检查：周末地缘事件、政策窗口、外围异动预期、持仓财报日历、仓位暴露度

### 1.3 A股组合结构

| 层级 | 占比 | 说明 |
|------|------|------|
| 底仓ETF | ~40% | 宽基ETF + 红利ETF |
| 精选观察 | ~30%预算 | 引擎筛出的候选标的，三条件验证 |
| 存量持仓 | 视情况 | 历史持仓的退出/减仓管理 |
| 机动资金 | ~5% | 特大错杀机会专用 |
| 永久现金 | ~20% | 不动 |

### 1.4 调仓纪律

**触发调仓**：
- 连续2周跌出核心池（<75分） → 研究替换
- 新风险标记（毛利率恶化等） → 查财报确认
- 季报低于预期 → 按财报决策树执行
- 单只止损 -8% → 强制

**不触发**：
- 排名小波动（3→5名）
- 新标的进核心池 → 只观察
- 分数波动1-2分 → 忽略

---

## 二、美股策略体系（三条红线）

### 2.1 三条红线入场系统

三条红线是**过滤条件（Filter）**，全部通过才允许建仓：

#### 红线1：情绪释放型下跌（最关键）
- 单日跌幅 ≥ 4%（可配置）
- 连续 3 个交易日下跌（可配置）
- 没有情绪释放 → 没有入场理由

#### 红线2：技术止跌信号（严格标准）
- 放量下跌后缩量（量能萎缩至前日 70% 以下）
- 均线强承接 = 下影线 + 收涨 + (放量 120%+ 或 强反弹 ≥ 1.5%)
- 完整 Higher Low 结构（低点A → 反弹 → 低点B > A → 2日确认）

#### 红线3：市场未进入系统性风险
- QQQ/SPX 未连续 3 日暴跌
- VIX < 25（可配置）

### 2.2 退出信号系统

按优先级从高到低：

| 优先级 | 类型 | 条件 | 动作 |
|--------|------|------|------|
| 🔴 CRITICAL | 止损清仓 | 浮亏超止损线 | 立即清仓 |
| 🟠 HIGH | 止盈减仓 | 浮盈达阶梯 | 分批减仓(20%→1/3, 40%→1/3, 80%→底仓) |
| 🟠 HIGH | 趋势破位 | 连续N日<MA50+拐头 | 减仓50% |
| 🟡 MEDIUM | 动量衰竭 | 量价背离/MACD顶背离 | 减仓1/3 |
| ⚫ OVERRIDE | 系统性风险 | VIX≥30恐慌/≥40极端 | 非核心减半/全组合50% |

### 2.3 策略类型

| 类型 | 说明 |
|------|------|
| `redline` | 三红线建仓 |
| `hold` | 永久持有 |
| `pullback` | 回调加仓 |
| `satellite` | 卫星仓不动 |

---

## 三、港股策略

### 3.1 公司股票激励减持策略
- **来源**：公司股票激励（中银国际账户）
- **策略框架**：折中方案 — 先减后持
- **减持触发**：反弹至短期均线附近时分批减持
- **止损线**：设定硬性止损价，不打折

### 3.2 港股观察池
- 观察池标的通过技术信号（缩量企稳、收回短期均线、周线止跌等）筛选
- 具体标的维护在 `my_portfolio.json` 中

---

## 四、硬性规则

> 以下规则不可违反，优先级高于一切。

1. **信号优先级不可逆转**：止损 > 止盈 > 趋势破位 > 动量衰竭
2. **A股三条件是过滤器**：全部通过才建仓，弹性窗口也需2/3+偏差内
3. **美股三红线是过滤器**：全部通过才建仓，不存在"两条差不多"
4. **未成交 ≠ 已建仓**：portfolio.json 必须反映真实持仓状态
5. **不编造数据**：所有价格、指标必须来自实时数据源
6. **HOLD 标的只在系统性风险时干预**：VIX < 30 不生成卖出信号
7. **财报冻结期严格执行**：发布前3日不新建仓
8. **每次盘前报告**必须基于 my_portfolio.json 交叉验证持仓状态

---

## 五、工作流程

### 盘前分析流程（A股 + 港股）

1. 读取 `my_portfolio.json` 确认持仓状态
2. 获取隔夜外围市场数据（美股收盘、VIX、纳指）
3. 获取 A 股开盘前数据（集合竞价、北向资金预期）
4. 对精选观察层逐只检查三条件状态
5. 对存量持仓检查止损/减仓信号
6. 生成盘前策略报告（含操作建议优先级）

### 美股信号检查流程

#### 全组合检查
```bash
python scripts/portfolio_checker.py
```

#### 单标的详细分析
```bash
python scripts/portfolio_checker.py --detail TSLA
```

#### 检查并推送
```bash
python scripts/portfolio_checker.py --push
```

### 输出格式

**A股盘前报告**包含：
- 外围市场概览（美股/VIX/汇率）
- 精选层三条件逐只状态表
- 弹性窗口触发评估
- 存量持仓信号
- 今日操作建议（优先级排序）

**美股信号报告**包含：
- 三红线逐条判定 + 退出信号检查
- 系统性风险评估
- 全组合自检五问汇总

---

## 六、配置文件说明

### my_portfolio.json（A股+港股主配置）

```
├── 策略总览（资金分配）
├── 精选观察层（三条件标的 + 弹性窗口参数）
├── 存量持仓（减仓计划）
├── 底仓ETF（定投进度）
├── 机动资金
├── 永久现金
├── 港股持仓（减持计划）
├── 港股观察池
└── 调仓纪律（v1.4规则）
```

### invassistant-config.json（美股信号配置）

```
├── portfolio.watchlist（标的 + 策略类型 + 退出参数）
├── portfolio.systemic_risk_exit（系统性风险参数）
├── adapters（推送渠道：企微/钉钉/飞书）
├── commands（指令映射）
└── output（输出目录）
```

---

## 七、失败处理

| 失败场景 | 处理方式 |
|----------|----------|
| 配置文件不存在 | 执行 `python scripts/init_config.py` 生成默认配置 |
| 数据源 API 限流 | 重试3次（间隔3-5秒），仍失败跳过标注 `⚠️ 数据获取失败` |
| 数据不足（<20交易日） | 跳过技术指标，标注 `⚠️ 数据不足` |
| cost_basis 未配置 | 跳过止盈止损，标注 `ℹ️ 未配置成本价` |
| 推送渠道失败 | 重试1次，不阻断其他渠道 |

---

## 八、数据源优先级

| 数据类型 | 首选 | 备选 |
|----------|------|------|
| A股K线/技术指标 | westock-data skill | AKShare |
| A股资金流/筹码/分时 | westock-data skill | NeoData |
| 选股引擎扫描 | AKShare | — |
| VIX/美股行情 | Yahoo Finance | NeoData |
| 北向资金 | NeoData | AKShare |
| 港股行情 | Yahoo Finance | — |

---

## 九、Notion 同步

策略和每日分析同步到 Notion Trading Strategy 页面：
- **策略更新**：`_update_notion_v14.py`（版本迭代时运行）
- **每日分析**：`_notion_daily_analysis.py`（盘前盘后自动写入）
- **页面结构**：Trading Strategy → A股策略 / 风险控制 / 每日分析 等子页面
