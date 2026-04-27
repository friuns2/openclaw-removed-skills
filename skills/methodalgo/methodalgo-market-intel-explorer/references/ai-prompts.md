# 🤖 AI Agent Prompt Templates (AI Prompts)

This document provides a series of optimized prompt examples designed to help AI agents (such as Claude or GPT-4) most efficiently utilize the `methodalgo-market-intel-explorer` skill.

---

## ⚡ Core Principles

- **JSON-Driven**: Always request JSON output for precise parsing.
- **Two-Phase Query**: Prioritize a brief preview before performing a deep dive.
- **Context-Aware**: Combine the current date with time-range filtering.

---

## 📝 Scenario-based Templates

### 1. Daily Morning Report / Market Overview
**Prompt**:
> Please use the `methodalgo-market-intel-explorer` skill to generate a crypto market overview for me today.
> 1. Call `signals market-today` to get the Fear & Greed Index and Altcoin Season metrics.
> 2. Call `signals etf-tracker` to get the latest ETF fund flows.
> 3. Call `news --type article --limit 50` to fetch 50 of today's deep-dive news articles.
> 4. Call `news --type breaking --limit 50` to fetch the latest 50 important breaking news flashes.
>
> Combine the above data to analyze current market sentiment and potential risks in concise English.

### 2. Deep Scan for a Specific Symbol (e.g., SOL)
**Prompt**:
> I need to perform a deep scan for SOL:
> 1. Search for the latest 10 news items about SOL: `news --type article --search 'SOL' --limit 10`.
> 2. Check for any MTF breakout signals for SOL: `signals breakout-mtf --limit 200` and filter for SOL-related items.
> 3. Get a 1-hour chart snapshot for SOLUSDT.P: `snapshot SOLUSDT.P 60 --url`.
>
> Integrate the above information to determine the current short-term trend for SOL.

### 3. Monitoring Large Liquidations and Sentiment Reversal
**Prompt**:
> Analyze market anomalies for a given session:
> 1. Fetch the latest 50 large liquidation records: `signals liquidation --limit 50`.
> 2. Check for any `exhaustion-buyer` or `exhaustion-seller` reversal signals: `signals exhaustion-seller --limit 5`.
>  3. If any large liquidations (over $1M) or strong reversal signals are found, include the corresponding chart snapshot links and summarize the key findings.

### 4. Token Unlock Alerts
**Prompt**:
> Query upcoming important token unlock events:
> Call `signals token-unlock --limit 1`.
> Note: This command returns an object; please extract `symbol`, `perc` (unlock percentage), `countDown`, and `unlockTokenVal` (unlock value) from the `signals` array. `ts` is the scheduled unlock time.
> Highlight projects with unlock proportions exceeding 1% of the circulating supply and analyze the potential downward pressure on price.

### 5. Macroeconomic Data & FRED Deep Analysis
**Prompt**:
> I need a comprehensive macroeconomic analysis:
> 1. Get the global macro dashboard: `methodalgo fred dashboard --json`.
> 2. Check the US recession scorecard: `methodalgo fred recession --json`.
> 3. Analyze crypto-related net liquidity: `methodalgo fred liquidity --json`.
> 4. Search for "Gold" related indicators: `methodalgo fred search 'Gold' --json`.
>
> Summarize the current macro environment, highlighting any "warning" or "danger" signals. Explain how current liquidity levels and recession risks might impact Bitcoin's mid-term price action.

### 6. Real-time Volatility Analysis (Calendar)
**Quick Tip**: Since macro events happen at precise times, you should fetch the latest data **immediately after the release time** (e.g., exactly at 8:30 AM ET for NFP) to capture the `actual` values for real-time volatility analysis.

**Prompt Template**:
> Use the `methodalgo-market-intel-explorer` skill to analyze this week's global macroeconomic events and their potential impact on Bitcoin:
> 1. Fetch the latest US economic events: `methodalgo calendar --countries US --json`.
> 2. Focus on high `importance` events (e.g., CPI, NFP, or FOMC-related data).
> 3. Compare `actual` vs. `forecast` trends to predict price volatility.
> 
> Summarize the key findings and how they might affect the Dollar Index (DXY) and cryptocurrency markets.

---

## 🛠️ Troubleshooting for AI

- **If `token-unlock` data parsing fails**:
  - *Cause*: This channel returns `{ signals: [...] }` instead of the `[...]` returned by standard channels.
  - *Solution*: The AI should check if the root object contains a `signals` key; if it does, iterate through the array under that key.

- **If data is outdated**:
  - *Solution*: Check the `timestamp` or `updatedAt` fields in the returned JSON. If they are older than 24 hours, suggest alerting the user about potential delays or attempting an incremental fetch for latest data.

- **If context overflow occurs**:
  - *Solution*: Reduce the `--limit` from 50 to 10, or use more specific `--search` keywords for exact matches.
