---
name: metal-price
description: Daily non-ferrous metals briefing for AI agents. Collects real-time base metals prices (Cu/Zn/Ni/Co/Mg/Bi) from Yahoo Finance, CCMN 長江有色, SMM, and Westmetall, then delivers a six-section professional investment research report via Telegram at 14:00 CST. Zero paid APIs required. Use when you need automated metals market monitoring, LME price tracking, or professional trading briefings with macro/inventory/futures-structure/sentiment cross-analysis.
---

# 有色小鑽風 · Metal Price Daily 🦞📊

> AI-driven non-ferrous metals daily briefing — six-section investment research report via Telegram.

每日 14:00 CST（上午盤收盤後）自動採集有色金屬行情，生成六板塊專業投研報告並推送到 Telegram。**零付費 API，開箱即用。**

## Features

- 📊 **多源價格聚合** — Yahoo Finance (USD)、CCMN 長江有色 (CNY)、SMM 上海有色、Westmetall (LME Cash)
- 📰 **新聞日期過濾** — Google News RSS（中英文，嚴格 48h 時效過濾，不顯示過期條目）
- 🏦 **機構觀點提煉** — 自動識別高盛/摩根大通/花旗報告，提煉中文結論，不堆原始鏈接
- 📈 **技術面分析** — 遠期曲線（spot/+2M/+6M）、Backwardation/Contango 結構判斷、各品種支撐阻力位
- 🔮 **四維交叉推理** — 宏觀（A/H 分化）× 庫存 × 期貨結構 × 情緒，段落式分析
- 🎯 **操作參考** — 六個品種各有具體價位建議（支撐/阻力/止損），非泛泛而談
- 🚫 **零付費 API** — 全部免費數據源

## Metals Covered（目標品種）

| Metal | USD | CNY |
|-------|-----|-----|
| Copper (Cu) | Yahoo HG=F ✅ + COMEX 遠期 ✅ | CCMN ✅ + SMM ✅（交叉驗證）|
| Zinc (Zn) | Westmetall LME Cash ✅ | CCMN ✅ + SMM ✅（交叉驗證）|
| Nickel (Ni) | Westmetall LME Cash ✅ | CCMN ✅ + SMM ✅（交叉驗證）|
| Cobalt (Co) | TradingEconomics ✅ | CCMN ✅ |
| Bismuth (Bi) | SMM CIF USD/kg ✅ | SMM 精鉍 ✅ |
| Magnesium (Mg) | — | CCMN 1#鎂 ✅ |

> 鋁（Al）不在本 Skill 追蹤範圍內。

## Report Format（六板塊）

```
一、行情快照   — 實時價格 + 漲跌 + 數據源
二、行業指數   — XME / COPX / 申萬有色，A/H 分化信號
三、技術面     — 各品種支撐/阻力/趨勢判斷
四、基本面     — LME 庫存（Cu/Zn/Ni）+ 去庫/累庫信號
五、市場情緒   — 機構觀點（中文提煉）+ 市場情緒分析
六、四維推理   — 宏觀/庫存/結構/情緒交叉推理 + 操作參考
```

## Quick Start

```bash
git clone https://github.com/RAMBOXIE/metal-price.git
cd metal-price
cp .env.example .env   # 填入 TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
node scripts/fetch-all-data.mjs   # 採集數據（~5s）
node scripts/daily-report.mjs     # 採集 + 生成 + 發送完整日報
```

## Environment Variables

```env
TELEGRAM_BOT_TOKEN=    # 必填：Telegram Bot Token
TELEGRAM_CHAT_ID=      # 必填：目標群組/頻道 ID
```

## Key Scripts

| Script | Description |
|--------|-------------|
| `scripts/fetch-all-data.mjs` | 主數據採集腳本，~5s 完成，輸出完整 JSON（價格/庫存/新聞/情緒/指數）|
| `scripts/daily-report.mjs` | 六板塊日報（調用 fetch-all-data → 生成分析 → Telegram 發送）|
| `scripts/fetch-news.mjs` | 獨立新聞抓取，含 48h 日期過濾 |
| `scripts/send-telegram.mjs` | Telegram 發送工具 |

## Agent Integration (OpenClaw Cron)

在 OpenClaw 中設置每日 14:00 定時任務：

```json
{
  "schedule": { "kind": "cron", "expr": "0 14 * * *", "tz": "Asia/Shanghai" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run node D:\\Projects\\metal-price\\scripts\\daily-report.mjs and confirm delivery.",
    "timeoutSeconds": 90
  }
}
```

## Data Sources

| Source | Metals | Status |
|--------|--------|--------|
| Yahoo Finance (HG=F) | Cu USD | ✅ Free |
| CCMN 長江有色 | Cu/Zn/Ni/Co/Mg CNY | ✅ Free |
| SMM hq.smm.cn/h5 | Bi/Pb/Sn CNY+USD | ✅ Free, no login |
| Westmetall | Zn/Ni USD + LME庫存 | ✅ Free |
| TradingEconomics | Co USD | ✅ Free (scrape) |
| OmetalCN | Cu/Zn/Ni/Sn CNY (備用) | ✅ Free |
| Reddit r/Commodities | 情緒 | ✅ JSON API |
| Google News RSS | 中英文新聞 | ✅ Free |
| LME official | 庫存 | ❌ Cloudflare封鎖（Westmetall替代）|

## Changelog

- **v1.3.4** — 全報告價格主展示統一為 CNY/噸（含技術面/結構維度/操作參考）；USD 僅保留為括號輔助資訊，避免非人民幣主展示。
- **v1.3.3** → 第七部分重寫為「結論→證據→影響」簡報研報格式（去標題黨/去省略號）；CCMN 故障時 Cu/Zn/Ni 自動切 SMM 備援；USD/CNY 新增多源備援（Yahoo + exchangerate.host + frankfurter）；外盤主顯示統一換算為 CNY/噸（保留原始 USD 於括號）
- **v1.3.2** — 第七部分改為「今日新增」模式：機構觀點按與昨日差異輸出（附日期），情緒模塊無新增時明示「第七部分無新增」，避免連續重複文案；新增報告狀態快照（memory/daily-report-state.json）
- **v1.3.1** — 机构觀點/市場情緒全中文提煉，去除英文原文；48h 時效過濾，無匹配直接跳過；無新增時明示，防止幻覺；報告前自檢（缺字段/無新訊提示），DRY_RUN 可安全預覽
- **v1.3.0** — 庫存三件套（交易所/保稅/社會佔位）、進口盈虧/到岸成本（Cu/Zn/Ni）、信號摘要四維打分（庫存/基差/進口/需求）、宏觀風險溫度計（DXY/VIX/CRB佔位/10Y）、DRY_RUN 安全開關
- **v1.2.0** — 新增鎂（Mg）品種；移除鋁（Al）；六板塊投研格式重寫；新聞 48h 時效過濾；操作建議含具體價位
- **v1.1.2** — OmetalCN 備用源；Westmetall 超時重試
- **v1.1.1** — SMM 交叉驗證（Cu/Zn/Ni）；Reddit 異動偵測
- **v1.1.0** — LME 庫存（Westmetall）；期貨遠期曲線；行業指數（XME/COPX/申萬）

## License

MIT · [GitHub](https://github.com/RAMBOXIE/metal-price)
