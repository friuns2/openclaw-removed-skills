# JSON Output Samples (Full Version)

The following are real structured output examples from various `methodalgo` CLI commands, provided to help AI agents accurately understand data patterns, field types, and their business meanings.

---

## 📰 News Data (news)

### 1. article (Deep Analysis)
```json
[
  {
    "type": "article",
    "title": {
      "en": "Coinbase disables Ronin trading as Ethereum L2 migration enters execution phase",
      "zh": "Coinbase 禁用 Ronin 交易，以太坊 L2 迁移进入执行阶段"
    },
    "excerpt": {
      "en": "Coinbase disabled Ronin trading as the network's Ethereum L2 migration enters execution.",
      "zh": "Coinbase 禁用了 Ronin 交易，因为该网络的以太坊 L2 迁移进入了执行阶段。"
    },
    "description": { "en": "...", "zh": "..." },
    "analysis": {
      "en": "Coinbase disabling Ronin trading may signal temporary disruption...",
      "zh": "Coinbase因Ronin进入L2迁移阶段授权而禁用交易，可能预示..."
    },
    "publish_date": "2026-03-30T19:35:00.865+00:00",
    "url": "https://ambcrypto.com/coinbase-disables-ronin-trading-..."
  }
]
```
> **Features**: Includes `excerpt`, `analysis`, and the original `url`.

### 2. breaking (Breaking News)
```json
[
  {
    "type": "news",
    "title": {
      "en": "JUST IN: BlackRock CIO Rick Rieder says he thinks the Federal Reserve will cut interest rates.",
      "zh": "突发：贝莱德首席信息官 Rick Rieder 称，他认为美联储将降息。"
    },
    "publish_date": "2026-03-30T19:15:56+00:00",
    "url": ""
  }
]
```
> **Features**: Highly concise fields, typically lacking an excerpt or analysis.

### 3. onchain (On-chain Data)
```json
[
  {
    "type": "news",
    "title": {
      "en": "Combined net outflows of nearly $1 billion reported from Binance/OKX over 24h.",
      "zh": "据报道，币安和 OKX 在过去 24 小时内的净流出总额接近 10 亿美元。"
    },
    "publish_date": "2026-03-30T17:00:53+00:00"
  }
]
```

### 4. report (Research Reports)
```json
[
  {
    "type": "report",
    "title": {
      "en": "Glassnode Update: Recent $76k rally coincided with smaller wallet distribution.",
      "zh": "Glassnode 更新：近期向 76k 美元的反弹伴随着小额钱包持有者的分发行为。"
    },
    "publish_date": "2026-03-30T18:07:01+00:00"
  }
]
```

---

## 📡 Signal Data (signals)

### 1. breakout-mtf/htf (Breakouts)
```json
[
  {
    "id": "1488261183843864617-0-0",
    "timestamp": 1774899516784,
    "signals": [
      {
        "title": "Breakout For NIGHTUSDT.P",
        "description": "Symbol: NIGHTUSDT.P\nType: Break-Down\nTimeFrame: 1h",
        "direction": "bear",
        "details": {
          "Symbol": "NIGHTUSDT.P", 
          "TimeFrame": "1h", 
          "Type": "DOWN", 
          "BreakPrice": "0.04284"
        }
      }
    ],
    "image": "https://m.methodalgo.com/tmp/xxx.webp"
  }
]
```

### 2. liquidation (Large Liquidations)
```json
[
  {
    "id": "1488258385802715154-1-0",
    "timestamp": 1774898849641,
    "signals": [
      {
        "title": "🔴🔴🔴 $20.1 K LIQUIDATION Line On ETHUSDT.P",
        "direction": "bear",
        "details": {
          "Symbol": "ETHUSDT.P",
          "Side": "🔴 SHORT",
          "Quantity": "8.52",
          "Average Price": "$2025.37",
          "Liquidation Price": "$2035.00",
          "Position Total": "$20111"
        }
      }
    ],
    "image": null
  }
]
```

### 3. exhaustion-buyer/seller (Liquidation Exhaustion/Reversal)
```json
[
  {
    "id": "1488212071433633804-0-0",
    "timestamp": 1774887807473,
    "signals": [
      {
        "title": "BUYER Exhaustion for DEGOUSDT.P",
        "description": "Liquidation lines below are under 10%",
        "direction": "bear",
        "details": {
          "Type": "Early Reversal",
          "Timeframe": "30m",
          "Exhaustion Side": "BUYER",
          "Safety": "Avoid unusual funding-rates / Apex",
          "Tip": "Limit order on gap-edge / final line / previous high",
          "Exchange": "Binance"
        }
      }
    ],
    "image": "https://m.methodalgo.com/tmp/xxx.webp"
  }
]
```

### 4. golden-pit-mtf/ltf (Golden Pit)
```json
[
  {
    "id": "1488251574781350068-1-0",
    "timestamp": 1774897225805,
    "signals": [
      {
        "title": "Golden Pit For BTRUSDT.P",
        "description": "Type: 🔴Bear Pit🔴",
        "direction": "bear",
        "details": {
          "Pattern": "Pull then Push",
          "Safety": "Wait 6-10 bars to develop, careful of reversal cloud"
        }
      }
    ],
    "image": "https://m.methodalgo.com/tmp/xxx.webp"
  }
]
```

### 5. token-unlock (Special Object Structure)
```json
{
  "signals": [
    {
      "ts": 1774915176616,
      "symbol": "OP",
      "perc": 1.52,
      "progress": "40.91%",
      "circSup": "6.79 B ICE",
      "countDown": "0Day23Hr30Min",
      "marketCap": "$218.99 M",
      "unlockToken": "32.21 M",
      "unlockTokenVal": "$3.36 M (1.52% of M.Cap)"
    }
  ],
  "updatedAt": 1774915176616
}
```
> ⚠️ **Note**: Returns a **single object** instead of an array.

### 6. etf-tracker
```json
[
  {
    "id": "14873193...",
    "signals": [
      {
        "title": "XRP ETF Inflow : 2026-03-27",
        "details": { "Net Inflow": "$0K", "7 Days Avg.": "$663.0K" }
      }
    ]
  }
]
```

### 7. market-today
```json
[
  {
    "id": "14876082...",
    "signals": [
      {
        "title": "Fear And Greed Index",
        "description": "Today: 9 Sentiment: Extreme Fear",
        "details": { "Yesterday": "12", "7Days Ago": "10" }
      }
    ]
  }
]
```

---

## 📸 Snapshot Data (snapshot)

```bash
methodalgo snapshot SOLUSDT.P 60 --url --json
```

```json
{
  "symbol": "SOLUSDT.P",
  "tf": "60",
  "url": "https://m.methodalgo.com/tmp/1774900570519.webp",
  "timestamp": 1774900570519
}
```
> **Features**: Simple mapping structure containing instant-access WebP preview links.

---

## 📅 Economic Calendar (calendar)

```bash
methodalgo calendar --countries US --json
```

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
    "source_url": "http://www.bls.gov/"
  }
]
```

---

## 🏦 Federal Reserve Data (FRED)

### 1. fred dashboard
```json
{
  "command": "dashboard",
  "sections": {
    "RATES": {
      "FEDFUNDS": { "value": 5.33, "date": "2024-03-01", "title": "Federal Funds Effective Rate" },
      "DGS10": { "value": 4.25, "date": "2024-03-25", "title": "10-Year Treasury Constant Maturity Rate" }
    },
    "INFLATION": {
      "T10YIE": { "value": 2.32, "date": "2024-03-25", "title": "10-Year Breakeven Inflation Rate" }
    }
  },
  "liquidity": {
    "WALCL": { "value_billions": 7450.21 },
    "RRPONTSYD": { "value_billions": 450.12 },
    "WTREGEN": { "value_billions": 750.45 },
    "NET_LIQ": { "value_billions": 6249.64 }
  },
  "inflation_yoy": {
    "CPI YoY": 3.15,
    "Core PCE YoY": 2.82
  }
}
```

### 2. fred recession
```json
{
  "command": "recession",
  "signals": [
    { "signal": "Yield Curve (10Y-2Y)", "status": "INVERTED", "reading": "-0.42%" },
    { "signal": "Sahm Rule", "status": "CLEAR", "reading": "0.15pp" },
    { "signal": "Financial Conditions (NFCI)", "status": "LOOSE", "reading": "-0.520" }
  ],
  "warnings": 1,
  "total": 6
}
```

### 3. fred liquidity (Net Liquidity Analysis)
```json
[
  {
    "date": "2024-03-20",
    "WALCL": 7490.5,
    "RRPONTSYD": 480.2,
    "WTREGEN": 720.1,
    "NET_LIQ": 6290.2
  },
  {
    "date": "2024-03-27",
    "WALCL": 7450.2,
    "RRPONTSYD": 450.1,
    "WTREGEN": 750.4,
    "NET_LIQ": 6249.7
  }
]
```
> **Formula**: `NET_LIQ = WALCL - RRPONTSYD - WTREGEN`. Values in Billions of USD.

### 4. fred latest
```json
{
  "series_id": "FEDFUNDS",
  "title": "Federal Funds Effective Rate",
  "units": "Percent",
  "date": "2024-03-01",
  "value": 5.33
}
```

### 5. fred zscore
```json
{
  "series_id": "CPIAUCSL",
  "title": "Consumer Price Index for All Urban Consumers: All Items in U.S. City Average",
  "lookback": "10y",
  "observations": 120,
  "current": 312.23,
  "mean": 270.45,
  "std": 25.12,
  "zscore": 1.66,
  "percentile": 92.5,
  "min": 236.12,
  "max": 312.23
}
```

---

💡 *Note: All timestamps are in milliseconds or ISO format.*
