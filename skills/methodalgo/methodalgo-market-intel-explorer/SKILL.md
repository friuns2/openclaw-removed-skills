---
name: methodalgo-market-intel-explorer
version: 1.2.0
description: Fetches cryptocurrency news, chart snapshots, macroeconomic events data, federal reserve indicators (FRED), and trading signals. Use this skill when the user wants to check the latest crypto news, market snapshots, chart screenshots, trading signals, token unlocks, ETF flows, Fear & Greed indices, and macro-economic data (GDP, CPI, Liquidity, etc.).
metadata:
  openclaw:
    requires:
      env:
        - METHODALGO_API_KEY
        - FRED_API_KEY
      bins:
        - methodalgo
      anyBins:
        - node
        - npm
    primaryEnv: METHODALGO_API_KEY
    install:
      - kind: node
        package: methodalgo-cli
        bins: [methodalgo]
    homepage: https://github.com/methodalgo/methodalgo-market-intel-explorer
category: data-provider
credentials:
  - name: METHODALGO_API_KEY
    description: API key for the Methodalgo service. Obtain one at https://account.methodalgo.com/account/api-keys
    required: true
  - name: FRED_API_KEY
    description: (Optional) Your personal FRED API key for higher rate limits on macro data. Get one at https://fred.stlouisfed.org/docs/api/api_key.html
    required: false
provenance:
  cli: https://www.npmjs.com/package/methodalgo-cli
  source: https://github.com/methodalgo/methodalgo-market-intel-explorer
  registry: https://clawhub.ai/methodalgo/methodalgo-market-intel-explorer
---

# Methodalgo Market Intel Explorer Skill

## Part 1 — Installing the Skill

Choose one of the following methods to install this skill into your AI agent:

### Option A — ClawHub (Recommended)
```bash
clawhub install methodalgo-market-intel-explorer
```
> 🔗 [https://clawhub.ai/methodalgo/methodalgo-market-intel-explorer](https://clawhub.ai/methodalgo/methodalgo-market-intel-explorer)

### Option B — GitHub Clone
```bash
git clone https://github.com/methodalgo/methodalgo-market-intel-explorer.git
```
Then point your AI agent (e.g. Claude, Cursor, Antigravity) to the cloned folder and instruct it to read `SKILL.md` to activate.

---

## Part 2 — Installing the CLI & Authentication

This skill relies on the `methodalgo-cli`, an **open-source npm package** ([npmjs.com/package/methodalgo-cli](https://www.npmjs.com/package/methodalgo-cli)), to fetch market data.

### 1. Install CLI
```bash
npm install -g methodalgo-cli
```

### 2. Authentication (Required)
The CLI supports two authentication methods. **The CLI will prioritize the environment variable over the local config.**

#### Method A: Environment Variable (Recommended for AI Agents)
Set the following environment variable in your system or IDE:
- `METHODALGO_API_KEY`: Your Methodalgo API key.

#### Method B: Local CLI Login (Classic)
Run the following command and enter your key when prompted:
```bash
methodalgo login
```

Apply for a key at: **https://account.methodalgo.com/account/api-keys**
- The key is stored locally on your machine after login; it is never transmitted outside of Methodalgo's own API.

Verify the installation:
```bash
methodalgo --version
```

### 3. Troubleshooting & Common Errors
If you encounter errors, check the following:

| Error Message | Solution |
|---------------|----------|
| **Authentication Required** | Run `methodalgo login` or set `METHODALGO_API_KEY` environment variable. |
| **Command Not Found** | Ensure `methodalgo-cli` is installed: `npm install -g methodalgo-cli`. |
| **Network Timeout** | Ensure your network can access `methodalgo.com`. |
| **Outdated Results** | Update the CLI: `methodalgo update`. |

---

## 📚 References (LLM Recommended Reading)

To execute tasks more accurately, it is recommended to refer to the following documents before handling complex queries:

- **[Signal Channels Detailed Reference](./references/signal-channels.md)**: Detailed explanation of the trigger mechanisms, timeframes, and `details` field meanings for various signal channels (Breakout, Exhaustion, Golden Pit, etc.).
- **[AI Prompts Guide](./references/ai-prompts.md)**: Provides prompt templates for scenarios such as "Daily Market Overview" and "Specific Coin Deep Scan".
- **[Data Output Samples](./references/sample-output.md)**: Shows real JSON response structures for news, signals, and snapshot commands to facilitate parsing logic.

---

## Usage

Invoke the `methodalgo` CLI directly; **the `--json` flag is mandatory** to obtain structured data:

```bash
# News
methodalgo news --type <type> --limit <N> --json

# Signals
methodalgo signals <channel> --limit <N> --json

# Snapshot
methodalgo snapshot <symbol> [tf] --url --json

# Calendar
methodalgo calendar --countries <codes> [options] --json

# Federal Reserve Data (FRED)
methodalgo fred <subcommand> [options] --json
```

---

## 📸 Snapshot Command

```bash
methodalgo snapshot <symbol> [tf] --url --json
```

### Parameter Description

| Parameter | Description | Example |
|----------|-------------|---------|
| `symbol` | Trading pair symbol (Required) | `SOLUSDT` (Spot) / `SOLUSDT.P` (Perpetual) |
| `tf` | Timeframe (Optional, default: 60) | `15` / `30` / `60` / `240` / `D` / `W` / `M` |
| `--url` | Forces a URL link to be returned instead of a binary stream | `--url` |
| `--buffer` | Outputs the raw binary image stream (suitable for direct programmatic processing) | `--buffer` |
| `--json` | Outputs structured JSON data | `--json` |

### Output Structure

```json
{
  "symbol": "SOLUSDT.P",
  "tf": "60",
  "url": "https://m.methodalgo.com/tmp/xxx.webp",
  "timestamp": 1774899516784
}
```

---

## 📰 News Command

```bash
methodalgo news --type <type> --limit <N> --json
```

### Available Types

| Type | Description |
|------|-------------|
| `article` | Deep crypto market news and analysis (includes summaries and AI analysis) |
| `breaking` | Real-time breaking news flashes |
| `onchain` | Monitoring for on-chain data anomalies |
| `report` | Institutional research reports |

### Optional Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--type` | News type (Required) | `--type breaking` |
| `--limit` | Limit on the number of results, up to 500 | `--limit 10` |
| `--language` | Language `zh` / `en` | `--language zh` |
| `--search` | Search for keywords in titles | `--search 'Bitcoin'` |
| `--start-date` | Start date | `--start-date 2026-03-20` |
| `--end-date` | End date | `--end-date 2026-03-30` |

### Output Structure

```json
[
  {
    "type": "breaking",
    "title": { "en": "...", "zh": "..." },
    "excerpt": { "en": "...", "zh": "..." },
    "description": { "en": "...", "zh": "..." },
    "analysis": { "en": "...", "zh": "..." },
    "publish_date": "2026-03-30T19:15:56+00:00",
    "url": "https://..."
  }
]
```

> The `article` type usually includes `excerpt`, `analysis`, and `url`; `breaking`, `onchain`, and `report` types typically do not have an `excerpt`. It is recommended to fetch a sufficient quantity of news items, such as 50-100, to ensure adequate time coverage.

---

## 📡 Signals Command

```bash
methodalgo signals <channel> --limit <N> --json
```

### Channels

| Channel | Description | Update Frequency |
|---------|-------------|------------------|
| `breakout-htf` | High Timeframe Breakout (1D/3D), 100-candle rolling window | Medium |
| `breakout-mtf` | Medium Timeframe Breakout (1H/4H), 100-candle rolling window | High |
| `breakout-24h` | 24-hour rolling window breakout detection | Ultra-high |
| `liquidation` | Real-time alerts for large liquidation orders | Real-time |
| `exhaustion-seller` | Seller exhaustion reversal signal (Liquidation Heatmap, inventory <10%/<5%) | Low/Medium |
| `exhaustion-buyer` | Buyer exhaustion reversal signal (Liquidation Heatmap, inventory <10%/<5%) | Low/Medium |
| `golden-pit-mtf` | Golden Pit signal (30m/1h/4h) - Bull=recovery after dip, Bear=drop after bounce | Medium |
| `golden-pit-ltf` | Golden Pit signal (5m/15m) - Bull=recovery after dip, Bear=drop after bounce | High |
| `token-unlock` | Token unlock events, including unlock time, fundamentals, volume, etc. | Daily |
| `etf-tracker` | Daily BTC/ETH/SOL/XRP ETF fund inflows and outflows | Daily |
| `market-today` | Altcoin Season Index + Fear & Greed Index | Daily |

### Standard Output Structure
**Standard Signal Channels** (breakout / liquidation / exhaustion / golden-pit / etf-tracker / market-today):

```json
[
  {
    "id": "1488261183843864617-0-0",
    "timestamp": 1774899516784, // Signal transmission timestamp
    "attachments": [],
    "image": "https://m.methodalgo.com/tmp/xxx.webp", // Link to chart or data image (optional, may be null)
    "signals": [
      {
        "title": "Signal title display...",
        "description": "Signal summary content (format varies by channel)...",
        "direction": "bull/bear/empty string", // Directional hint
        "details": { 
          // ⚠️ Field names in the details object vary by channel; see the following enumeration:
        }
      }
    ]
  }
]
```

#### `details` Structure Enumeration for Standard Channels:

1. **`breakout-*` series** (Detecting breakout trading opportunities)
```json
{
  "Symbol": "NIGHTUSDT.P", "TimeFrame": "1h", "Type": "DOWN / UP", 
  "BreakPrice": "0.04284", "Exchange": "BINANCE"
}
```
2. **`liquidation`** (Detecting large liquidation/blow-off orders)
```json
{
  "Symbol": "ZECUSDT.P", "Side": "🔴 SHORT / 🟢 LONG", "Quantity": "88.245", 
  "Average Price": "$227.43", "Liquidation Price": "$229.70", "Position Total": "$20069"
}
```
3. **`exhaustion-*` series** (Buyer or seller exhaustion, potential trend reversal)
```json
{
  "Type": "Early Reversal", "Timeframe": "30m", "Exhaustion Side": "SELLER / BUYER", 
  "Safety": "...", "Tip": "...", "Exchange": "Binance"
}
```
4. **`golden-pit-*` series** (Re-entry opportunities in Smart Cloud patterns)
```json
{
  "Pattern": "Pull then Push", "Safety": "Wait 6-10 bars to develop..."
}
```
5. **`etf-tracker`** (ETF fund flow broadcast)
```json
{
  "Net Inflow": "$0K", "7 Days Avg.": "$663.0K"
}
```
6. **`market-today`** (Market sentiment, including Season Index and Fear & Greed Index)
```json
// Type A (Season Index)
{ "Alt Season": "...", "Bitcoin Season": "..." }
// Type B (Fear And Greed Index)
{ "Yesterday": "12", "3Days Ago": "10", "7Days Ago": "10" }
```

#### `token-unlock` Channel Structure
**`token-unlock` channel** (Unique data structure with a `signals` array at the top level):

```json
{
  "signals": [
    {
      "ts": 1774915176617, // Unlock time
      "symbol": "OP", // Token name
      "perc": 1.52, // Unlock percentage
      "progress": "40.91%", // Unlock progress
      "circSup": "6.79 B ICE", // Current circulating supply
      "countDown": "0Day23Hr30Min", // Countdown relative to updatedAt. Please calculate real-time using the ts and updatedAt in the data.
      "marketCap": "$218.99 M", // Current market capitalization
      "unlockToken": "32.21 M", // Number of tokens unlocked
      "unlockTokenVal": "$3.36 M (1.52% of M.Cap)" // Value of tokens unlocked
    }
  ],
  "updatedAt": 1774915176617 // Data update time
}
```

---

## 📅 Calendar Command

```bash
methodalgo calendar --countries <codes> [options] --json
```

### Parameter Description

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--countries` | **(Required)** Comma-separated ISO country codes | `--countries US,EU,CN` |
| `--from` | Start date (Default: 2 days ago) | `--from 2026-03-20` |
| `--to` | End date (Default: 2 days later) | `--to 2026-03-30` |
| `--json` | Outputs structured JSON data | `--json` |

### Output Structure

```json
 [
   {
     "title": "Non Farm Payrolls",
     "country": "US",
     "indicator": "Jobs",
     "period": "Mar",
     "comment": "Nonfarm Payrolls measures the change in the number of people employed during the previous month, excluding the farming industry...",
     "actual": "275K",
     "forecast": "198K",
     "previous": "229K",
     "importance": 1,
     "date": "2026-04-03T12:30:00.000Z",
     "source": "Bureau of Labour Statistics",
     "source_url": "http://www.bls.gov"
   }
 ]
 ```

 ---

---

## 🏦 Federal Reserve Data (FRED) Command

Access 800,000+ macro economic time series from FRED (Federal Reserve Economic Data) maintained by the St. Louis Fed.

```bash
methodalgo fred <subcommand> [options] --json
```

### Subcommands

| Subcommand | Description | Example |
|------------|-------------|---------|
| `dashboard` | Full macro overview (Rates, Inflation, Liquidity, Employment, etc.) | `methodalgo fred dashboard --json` |
| `recession` | Recession indicator scorecard (6 classic signals) | `methodalgo fred recession --json` |
| `liquidity` | Net liquidity analysis (Fed Assets - RRP - TGA) | `methodalgo fred liquidity --json` |
| `latest <id>`| Get the latest value for a specific series ID | `methodalgo fred latest FEDFUNDS --json` |
| `search <q>` | Search for FRED series by keywords | `methodalgo fred search "gold price" --json` |
| `compare <ids>`| Compare multiple series (comma-separated IDs) | `methodalgo fred compare DGS10,DGS2 --json` |
| `changes <id>` | Show recent changes and trends for a series | `methodalgo fred changes WALCL --json` |
| `spread <i1,i2>`| Compute difference between two series | `methodalgo fred spread T10Y2Y,T10Y3M --json` |
| `zscore <id>` | Z-score and percentile analysis vs historical data | `methodalgo fred zscore CPIAUCSL --json` |

### 💡 High-Alpha Series IDs for Crypto Traders

| Category | Series ID | Name | Trading Relevance |
|----------|-----------|------|-----------|
| **Policy** | `FEDFUNDS` | Fed Funds Rate | Baseline for risk assets discount rate |
| **Liquidity**| `WALCL` | Fed Total Assets | The "Money Printer" (Direct correlation with BTC) |
| **Liquidity**| `M2SL` | M2 Money Supply | Global liquidity pool size |
| **Liquidity**| `RRPONTSYD`| Reverse Repo | Liquidity drain (Higher = Bad for Crypto) |
| **Liquidity**| `WTREGEN` | Treasury General Account | Gov cash (Lower = More market liquidity) |
| **Inflation**| `CPIAUCSL` | CPI (All Items) | Inflation core driver for Fed pivots |
| **Inflation**| `PCEPILFE` | Core PCE | Fed's internal favorite inflation gauge |
| **Yields** | `DGS10` / `DGS2`| 10Y / 2Y Treasury | Risk-free rate (Higher = Pressure on BTC) |
| **Real Rate**| `REAINTRATREARAT10Y` | 10Y Real Interest Rate | The true cost of money (Negative = Crypto Moon) |
| **Currency** | `DTWEXBGS` | Dollar Index (DXY) | Inverse correlation: Strong Dollar = Weak BTC |
| **Risk** | `VIXCLS` | VIX Fear Index | Market stress indicator |

### 📈 Macro Impact Logic (Quick Guide)

| Indicator | Direction | Typical Impact on Crypto |
|-----------|-----------|--------------------------|
| **Interest Rates** (`FEDFUNDS`, `DGS10`) | ⬆️ Increasing | **Bearish** (Higher cost of capital, attracts liquidity to bonds) |
| **Inflation** (`CPIAUCSL`, `PCEPILFE`) | ⬆️ Above Target | **Bearish** (Forces Fed to keep rates high or hike further) |
| **Net Liquidity** (`fred liquidity`) | ⬆️ Expanding | **Bullish** (More "excess" cash flowing into risk assets) |
| **US Dollar** (`DTWEXBGS`) | ⬆️ Strengthening | **Bearish** (Inverse correlation with BTC price) |
| **Real Rates** (`REAINTRATREARAT10Y`) | ⬇️ Falling/Negative| **Bullish** (Incentivizes holding non-yielding assets like Gold/BTC) |

> **Macro Pro-Tip**: `methodalgo fred liquidity` automatically calculates **Net Liquidity** using `Fed Assets - RRP - TGA`. This is the single most important macro driver for Bitcoin's medium-term price action.
### Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--lookback` | Lookback window for trend analysis | `--lookback 5y` / `24m` / `365d` |
| `--tail` | Show only the last N observations | `--tail 10` |
| `--json` | Outputs structured JSON data | `--json` |

---

## 🎯 Scenario Quick Look

| User Intent | Command |
|-------------|---------|
| Check latest news affecting market sentiment | `methodalgo news --type breaking --limit 50 --json` |
| Check crypto industry news | `methodalgo news --type article --limit 100 --json` |
| Search news for a specific symbol | `methodalgo news --type article --search 'Bitcoin' --limit 5 --json` |
| Check breakout signals | `methodalgo signals breakout-mtf --limit 10 --json` |
| Check token unlocks | `methodalgo signals token-unlock --limit 1 --json` |
| Check ETF fund flows | `methodalgo signals etf-tracker --limit 10 --json` |
| Check global market sentiment | `methodalgo signals market-today --limit 5 --json` |
| Check liquidation events | `methodalgo signals liquidation --limit 10 --json` |
| Check Golden Pit signals | `methodalgo signals golden-pit-mtf --limit 10 --json` |
| Check macroeconomic data (US) | `methodalgo calendar --countries US --json` |
| Check upcoming macro events | `methodalgo calendar --countries US,EU,CN --from 2026-04-01 --json` |
| Check global macro dashboard | `methodalgo fred dashboard --json` |
| Check US recession risk | `methodalgo fred recession --json` |
| Analyze macro liquidity impact on BTC | `methodalgo fred liquidity --lookback 1y --json` |
| Compare DXY and 10Y Yields | `methodalgo fred compare DTWEXBGS,DGS10 --json` |
| Analyze Real Interest Rate impact | `methodalgo fred zscore REAINTRATREARAT10Y --json` |
| Compare 10Y and 2Y Treasury (Recession Warning) | `methodalgo fred spread T10Y2Y,T10Y3M --json` |
| Search for specific economic data (e.g. Gold) | `methodalgo fred search 'Gold London Fix' --json` |
| Get specific macro indicator (e.g. CPI) | `methodalgo fred latest CPIAUCSL --json` |
| Get chart snapshots | `methodalgo snapshot BTCUSDT.P 60 --url --json` |
| Incremental fetch for more signals (except token-unlock) | `methodalgo signals <channel> --limit 100 --after "msgId" --json` |

---

## Important Notes

1. **Output Format**: Output is **pure JSON**; simply use `JSON.parse`.
2. **Two-Phase Fetch Strategy**:
   - Phase 1 (Snapshot): Fetch 5 items to make a preliminary trend assessment.
   - Phase 2 (Deep Dive): Perform incremental fetches based on specific IDs or keywords (`--after` / `--search`).
3. **Data Volume Limits**: `--limit` controls the amount of data. News: max 500 items; Signals: max 600 items.
4. **Language Handling**: For news data, prioritize `title.zh` / `excerpt.zh` / `analysis.zh` fields for Chinese content (if requested).
5. **Structural Inconsistency Alert**: `token-unlock` returns an object (containing a `signals` array), while other channels return an array. The AI must determine processing logic based on the `channel`.
6. **Snapshot Screenshots**: `snapshot` returns image links via `--url` by default. Please access the visualized market charts through these links. 
7. **Authentication Failure**: If commands fail with 401/403 errors, verify your API key at **https://account.methodalgo.com/account/api-keys** and re-run `methodalgo login`.
8. **FRED API Key**: While Methodalgo provides macro data, you can set your own FRED key for higher limits: `methodalgo config set fred-api-key <key>`.

> Github: https://github.com/methodalgo/methodalgo-market-intel-explorer
> ClawHub: https://clawhub.ai/methodalgo/methodalgo-market-intel-explorer
