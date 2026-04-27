---
name: amazon-review-scraper
description: "Amazon Review Intelligence — input an ASIN, automatically fetch product reviews via VOC.AI and run Claude AI analysis. Outputs structured VOC report: sentiment breakdown, top pain points, key selling points, listing optimization suggestions, SEO keywords. No scraping needed — uses VOC.AI API. Free tier: 8 reviews per ASIN. Triggers: amazon review, asin analysis, voc analysis, voice of customer, listing optimization, pain points, review scraper, amazon fba research, product research, review analysis, amazon seller"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/amazon-review-scraper
---

# Amazon Review Scraper — VOC Intelligence

> Input an ASIN → fetch reviews via VOC.AI → Claude AI analysis → structured report.
> No browser, no scraping. Powered by VOC.AI API.

## Quick Start

```bash
# Basic analysis (8 reviews free, English report)
bash voc.sh B08N5WRWNW

# Chinese report
bash voc.sh B08N5WRWNW --lang zh

# More reviews (requires VOC.AI Team plan token)
bash voc.sh B08N5WRWNW --token YOUR_TOKEN --limit 50

# Save to file
bash voc.sh B08N5WRWNW --output report.md

# Fetch only (no AI, saves JSON)
bash voc.sh B08N5WRWNW --scrape-only --output reviews.json

# Analyze existing JSON
bash voc.sh --analyze reviews.json --asin B08N5WRWNW --lang zh
```

## API Token

- **Free tier**: 8 reviews per ASIN — no token needed
- **More reviews**: Get a VOC.AI token at https://voc.ai/pricing (Team/Enterprise plan)
- Pass via `--token YOUR_TOKEN` or `export VOC_TOKEN=YOUR_TOKEN`

## Sample Output

```
╔══════════════════════════════════════════════════════╗
║     Amazon Review Intelligence Report               ║
║  ASIN: B08N5WRWNW  │  Reviews: 8    │  amazon.com   ║
║  Generated: 2026-04-01 10:30                         ║
╚══════════════════════════════════════════════════════╝

📊 Sentiment Distribution
  Positive  ████████████░░░░  74%  (6 reviews)
  Neutral   ███░░░░░░░░░░░░░  13%  (1 reviews)
  Negative  ██░░░░░░░░░░░░░░  13%  (1 reviews)
  Verified  ████████████████  89% verified purchases

⭐ Rating Distribution
  5★  ███████████████  5
  4★  ████░░░░░░░░░░░  1
  3★  ██░░░░░░░░░░░░░  1
  2★  █░░░░░░░░░░░░░░  0
  1★  █░░░░░░░░░░░░░░  1

  Average Rating: ████  4.2/5.0

────────────────────────────────────────────────────────

## 🔴 Top 5 Pain Points

1. **Short battery life** (3 mentions)
   > "Battery drained in 2 days, very disappointed"
   - Customers expect longer standby time vs. what's advertised

## 🟢 Top 5 Selling Points

1. **Excellent sound quality** (5 mentions)
   > "Amazing bass and crystal clear highs for the price"

## 💡 Listing Optimization
...
```

## Requirements

- Python 3.8+
- `requests` (auto-installed on first run)
- `claude` CLI for AI analysis (optional — scrape-only mode works without it)
- VOC.AI API token for more than 8 reviews

## Notes

- Default free tier: 8 reviews per ASIN
- Want more? Upgrade to VOC.AI Team plan (https://voc.ai/pricing) — uses credits
- Each AI analysis uses ~2,000–5,000 Claude tokens (~$0.01–$0.03)
- Supports all Amazon marketplaces via VOC.AI
