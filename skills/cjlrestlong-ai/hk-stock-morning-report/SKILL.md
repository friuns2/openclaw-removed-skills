---
name: hk-stock-morning-report
version: 1.2.7
description: >
  Generate HK stock market morning report (股市晨報) for Chinese bank trading desk.
  Use when user asks "生成晨报", "股市晨报", "今日股市", "港股晨報", or any similar HK stock market report request.
  Produces a 4-section daily report: market review, southbound capital flow, hot market news, and top HK stock.
  Follows strict format rules and sends via WeChat personal + Feishu group.
---

# HK Stock Morning Report (股市晨報)

## ⚠️ 第四部分：熱門港股

**搜索關鍵詞格式（強制）：** `{報告日前一日}熱門股票` 或 `{報告日前一日}港股熱點`
- 動態替換日期，例如報告日4月28日 → 搜索「4月27日熱門股票」
- 不是搜特定股票，是搜「熱門股票」這個主題，找到有新聞的股票後選1檔
- 自己根據搜索結果編寫新聞摘要，不直接引用未經核查的數字
- 搜不到具體新聞時：誠實寫「待更新」，不得編造數字

---

## 🚨 強制規則（零藉口）

1. **第一部分不准猜測假日** — 必須先確認當日是否交易日，不準主觀以為是假期
   - 香港2026年假日查證：只查 `https://www.gov.hk/sc/about/abouthk/holiday/2026.htm`
   - 佛誕翌日是5月26日（不是4月），耶穌受難節是4月3日（不是4月27日）
2. **第三部分搜索必須加「年月日」** — 關鍵詞格式：`YYYY年MM月DD日 港股/財經新聞`
   - 例：4月28日晨報 → 搜索「2026年4月28日 港股 新聞」
   - 不加日期會返回舊聞，導致數據時間錯乱
3. **早上8點，只可用上一個交易日的收盤數據** — 港股9:30開盤，8點不可能有今天收盤數；上一個交易日（4/27）收盤數據可用，今天（4/28）收盤數據不可用
4. **數據內部溯源（不上螢幕報告）** — 每個引用數字必須記錄來源URL和時間戳，存在工作記憶中備查；報告本身保持乾淨，不展示時間戳
5. **發送前二次核查清單** — 推送前必須逐項確認：
   - [ ] 今天是什麼日期？→ 大標題
   - [ ] 上一個交易日是哪天？→ 第一部分標題
   - [ ] 今天是否交易日？→ 查gov.hk
   - [ ] 搜索關鍵詞含「YYYY年MM月DD日」？
   - [ ] 早上（≤9:30）不得有今天收盤數據？
   - [ ] 每個數字有靠譜來源？懷疑的數字有二次核查？
   - [ ] 南下資金口徑確認（成交？凈買入？）
   - [ ] 標題和摘要之間有空行？
   - [ ] 報告已讀一遍，確認數字邏輯正確？

---

## 固化文件（直接引用，不重新揣測）

| 文件 | 用途 |
|------|------|
| `scripts/fetch_southbound_data.py` | 南下資金數據自動獲取腳本，輸出JSON |
| `scripts/southbound_report_template.md` | 完整模板+格式規範+核查清單 |
| `references/errors.md` | 錯誤全集，發送前必查 |
| `references/stock_report_format.md` | 格式模板原文 |

### 南下資金自動化流程（v1.0.6+）
1. **搜索**：用 tavily_search 搜索 `site:stcn.com 南向資金 {日期} 凈買入`
2. **確認口徑**：stcn.com 數據寶頁面會同時有「成交額」和「凈買入」，兩者不要混淆
   - **全市場凈買入 = 「合計凈買入」那個數字**（不是成交活躍股數字）
3. **寫入 JSON**：把搜索結果（口徑+日期+數字）寫入 `data/southbound_latest.json`
4. **格式化**：運行 `python3 scripts/fetch_southbound_data.py` 讀取 JSON 並輸出格式化文字
5. **核查**：確認數字口徑是全市場，不是成交活躍股

**關鍵區分（stcn.com 頁面）：**
- stcn.com 同一個頁面同時有：
  - 「成交活躍股合計成交222.26億，凈買入22.51億」→ 這是**個股口徑**
  - 「合計成交額826.54億，凈買入37.38億」→ 這是**全市場口徑**
- **晨報必須用全市場口徑（37.38億），不是成交活躍股口徑（22.51億）**

## ⚠️ 2026-04-22 錯誤檢討後更新的核心規則（v1.0.5+）

### 南下資金數據口徑規則（最高優先）
**stcn.com同時有兩套口徑，必須區分：**
- 「港股通成交活躍股」口徑 → 這是**個股**凈買入，不是全市場總數
- 「南向資金今日凈買入XX億」口徑 → 這才是**全市場總數**，晨報必須用這個

**當看到「成交活躍股」字樣，立刻警惕：那不是我們需要的數字。**

**南下資金標準格式：**
```
📍二、南下資金凈買入XX億（港元）
📈 港股通(滬): 凈買入YY億（港元）
📉 港股通(深): 凈賣出ZZ億（港元）

其中：凈買入XXX；

凈賣出XXX。
```

> 注意：**無「成交」字段**，只顯示凈買入/凈賣出金額。口徑必須是全市場「合計凈買入」數字，不是成交活躍股數字。

### 用數字前三驗原則
**每次使用任何數字前，必須確認三項：否則寫「待更新」：**
1. **口徑**：這是成交額？凈買入？不同口徑數字差異巨大
2. **日期**：這個數字是哪天的？不是目標日期的立刻排除
3. **來源**：這個數字來自哪個網站？不同來源口徑不同

### 歷史版本優先原則
- 當用戶說「某版本有完整數據」，**先查歷史消息確認內容**，再決定是直接使用還是修補
- **不得用新的搜索結果直接覆蓋可能正確的歷史版本**

### 勝宏科技代碼
- **02476.HK**（2026-04-22 更新，之前錯為03839）
- 搜索確認，不得猜測

## Workflow (执行步骤)

### Step 1: Read Format Template
Read `references/stock_report_format.md` — this is the source of truth for all format rules. Do not deviate.

### Step 2: Determine Date Header
**⚠️ Big title date (x.xx) = Report generation date (natural day), NOT last trading day**

Example: Report generated on Sunday Apr 19 but covering Friday Apr 18 trading → big title = `4.19`, Section 1 = `上週五股市回顧`

Find the last trading day and determine the Section 1 header:
- Same week, no gap → `📍一、昨日股市回顧`
- Same week, gap (holiday) → `📍週X股市回顧`
- Last week → `📍一、上週X股市回顧`

### Step 3: Fetch Index Data
- Hang Seng Index: `https://qt.gtimg.cn/q=r_hkHSI`
  - Field[3] = current price, Field[4] = previous close
  - Calculate: change points = price - prev_close; change% = (price-prev_close)/prev_close × 100
- Hang Seng Tech Index: `https://qt.gtimg.cn/q=r_hkHSTECH` (same parsing)

### Step 4: Search Section 1 (Market Review)
- Search: `site:gelonghui.com "港股收評" "昨日日期"`
- Extract: market overview (30-50 chars), strong/weak stocks with exact figures, sector performance
- Fallback: futunn or Yahoo Finance

### Step 5: Search Section 2 (Southbound Capital) — ⚠️ 最重要步驟
**只使用stcn.com全市場口徑「南向資金今日凈買入XX億」**
- Primary: `site:stcn.com "南向資金" "昨日日期" "凈買入"`
- Also: `site:gelonghui.com "南向資金" "昨日日期"`
- Fallback: `site:futunn.com "南下" "昨日日期"`
- **⚠️ stcn.com的「成交活躍股」數字不是全市場總數，絕對不能使用**
- **⚠️ 當細分（滬/深）數字不確定時：保留📈📉兩行並填入「待更新」，不得刪除行**

### Step 6: Search Section 3 (Hot News) — ⚠️ Search TODAY's date
- Search today's date + "港股" + "熱點" or "最新"
- Must search today's news, NOT last trading day's market data
- Even if HK market is closed, there are macro policy, international market, broker reports with today's date
- If no results → write "待更新", do NOT fabricate data
- Select 3 most relevant news items

### Step 7: Search Section 4 (Hot HK Stock News) — Select 1 stock, write your own summary
**⚠️ 第四部分是新聞，新聞等於搜「熱門股票」而不是搜個股！**
- Search: `"{報告日前一日}熱門股票"` 或 `"{報告日前一日}港股熱點"`（例如：報告日4月23日 → 搜索「4月22日熱門股票」）
- **不是搜特定股票名稱或代碼** — 搜的是「熱門股票」這個主題
- 找出有最新新聞的股票，選1檔
- **自己根據搜索結果編寫新聞摘要**，不是直接引用未經核查的數字
- 如果搜不到具體新聞 → 如實寫「待更新」，不得編造數字
- 勝宏科技代碼：02476.HK（僅供參考，不強制使用）

### Step 8: Generate Report
Assemble the report strictly following the format template. Big title = 3 Section 3 ▶️ titles joined by semicolons. Write `待更新` if data unavailable — never estimate.

### Step 9: Pre-Send Verification
Read `references/errors.md` and verify each item. Check:
- [ ] Big title = Section 3 ▶️ titles (do not rewrite)
- [ ] Arrow direction: 📈=net buy, 📉=net sell
- [ ] No estimated numbers (write 待更新 if uncertain)
- [ ] Format: 📍 has no space after, ▶️ has no bold, Section 4 has only 1 stock, **▶️ title and content must have an empty line between them**
- [ ] 📈📉 rows with uncertain data: keep the rows, write "待更新", do NOT delete the rows
- [ ] **南下資金口徑確認**：數字來自全市場口徑，不是成交活躍股口徑
- [ ] **勝宏科技代碼**：02476.HK（搜索確認）

### Step 10: Send
**飛書只發卡片即可（2026-04-24 更新）：**
- **卡片**：完整晨報內容，header為「🔴股市晨報」（飛書卡片現已支援文字選取複製，無需再發代碼塊）

微信個人：純文字格式（不需卡片）

### 香港政府假日官網
- **原則**：查香港假日資訊，**只使用香港政府官網**
- 官網：`https://www.gov.hk/sc/about/abouthk/holiday/2026.htm`
- 示例：復活節日期（4月5日，不是4月22日）、核證交易日等，均以官網為準

## Key Format Rules (7 Rigid Constraints)

1. Big title contains 🔴 and 🔵
2. 📍一: X = 昨日 / 週一~週五 / 上週一~上週五
3. 📍二: Direction from actual data (📈=net buy, 📉=net sell)
4. Numbers with（港元）: only the first line of Section 2 header (e.g., `凈買入xx億（港元）`), the 📈📉 lines and summary do NOT repeat （港元）
5. ▶️ Title and content **must have an empty line between** (Error 9)
   - **⚠️ 全域段落空行規則（v1.2.3+）**：不只▶️與摘要之間，**所有邏輯段落之間都必須有空行**。這包括：大標題↔免責聲明、免責聲明↔📍一、📍N↔正文 ▶️標題↔摘要、資料來源↔版權聲明。微信/飛書的 Markdown 只識別 `\n\n`（雙換行）為空行，單換行無效。
6. Section 4: only 1 stock
7. 📍 followed directly by text, no space

## Data Sources

| Content | Source |
|---------|--------|
| Index (close/change) | Tencent Finance API qt.gtimg.cn |
| Section 1 (market overview) | gelonghui.com 港股收評 |
| Section 2 (southbound) | **stcn.com 全市場口徑（primary）；gelonghui.com；futunn.com (fallback)** |
| Section 3 (hot news) | Web search for today's date |
| Section 4 (top stock) | Web search for today's individual stock news |
