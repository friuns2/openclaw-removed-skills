---
name: pangolinfo-amazon-scraper
description: >
  The ultimate automated market research tool for e-commerce. Stop manual product hunting and bypass CAPTCHAs. Perfect for LangChain, AutoGen, OpenDevin, and OpenClaw agents to extract ASIN products, keywords, category bestseller ranks, and reviews programmatically.

homepage: https://pangolinfo.com/?referrer=clawhub_amz
metadata:
  openclaw:
    emoji: "🛒"
    os: ["darwin", "linux"]
    requires:
      env:
        - PANGOLINFO_API_KEY
        - PANGOLINFO_EMAIL
        - PANGOLINFO_PASSWORD
      notes: "Auth: set PANGOLINFO_API_KEY (recommended) OR PANGOLINFO_EMAIL + PANGOLINFO_PASSWORD."
tags: [amazon, amazon-scraper, api, asin, automation, bestseller, category, data-pipeline, ecommerce, json, keyword, price-tracking, product, reviews, scraping]
version: 2.0.1
---

# Pangolinfo Amazon Scraper: Product + Keyword + Review + Category

Scrape Amazon programmatically via **Pangolinfo** APIs.

## 🌟 Why Use This Skill? (User Stories)
Bypass bot-detection and captchas instantly. Empower your AI with real-time Amazon market intelligence:
- **Automated Product Research**: Scrape detailed ASIN data, pricing, and inventory.
- **Competitor Analysis for FBA**: Track daily keyword rankings and BSR movements.
- **Voice of Customer (VoC)**: Extract bulk product reviews for sentiment analysis.

## 🤖 Compatible Agent Frameworks
- **OpenClaw** (Direct CLI execution & workflow chaining)
- **LangChain / LangGraph / Dify** (As an e-commerce scraping tool)

## 🌐 多语言适配 (Multi-language Support)
- **🇨🇳 中文适用场景**: 亚马逊全域数据抓取 API（ASIN详情、关键词排名、类目BSR、评论）。完美适配 AI Agent 自动化分析工作流。
- **Agent Directive**: Always output the final analysis/report in the language of the user's prompt (e.g., reply in Chinese if asked in Chinese).

Supports product detail pages, keyword search, category listings, seller pages, best sellers, and more.

## Prerequisites

- **Python 3.6+** (standard library only)
- A **Pangolinfo account**: https://pangolinfo.com/?referrer=clawhub_amz
- Auth env vars (choose one):
  - `PANGOLINFO_API_KEY` (recommended)
  - or `PANGOLINFO_EMAIL` + `PANGOLINFO_PASSWORD`

```bash
export PANGOLINFO_API_KEY="..."
# or
export PANGOLINFO_EMAIL="..."
export PANGOLINFO_PASSWORD="..."
```

## Minimal examples

Product detail:

```bash
python3 scripts/pangolinfo.py --url "https://www.amazon.com/dp/B0DYTF8L2W" --parser amzProductDetail
```

Keyword search:

```bash
python3 scripts/pangolinfo.py --q "wireless mouse" --parser amzKeyword
```

## Usage

```
--q QUERY          Keyword query (builds an Amazon search URL)
--url URL          Target Amazon URL (product/category/seller/etc.)
--parser PARSER    Parser name (default: amzProductDetail)
--zipcode CODE     Zipcode for localized pricing (default: 10041)
--format FMT       json (default) | rawHtml | markdown
--auth-only        Authenticate and show token info
--raw              Output raw API response instead of extracted data
```

### Amazon parsers

- `amzProductDetail` (default)
- `amzKeyword`
- `amzProductOfCategory`
- `amzProductOfSeller`
- `amzBestSellers`
- `amzNewReleases`
- `amzFollowSeller`

## Links

- Homepage: https://pangolinfo.com/?referrer=clawhub_amz

## References

- [references/amazon-api.md](references/amazon-api.md)
- [references/error-codes.md](references/error-codes.md)


## 🎯 Quick Start Prompts (Copy-Paste)
Try these prompts with your agent to see instant results:
- *"Fetch the top 10 bestsellers in the 'Electronics' category on Amazon and format the results as a CSV."*
- *"Scrape the top 50 reviews for ASIN B08XXXXXXX and summarize the main customer complaints."*
- *"Search Amazon for 'wireless earbuds', extract the first page results, and list their prices and ratings."*

## 🛑 Boundaries & Error Handling
**When NOT to use:** Do not use this for non-Amazon platforms (e.g., Shopify, Walmart). 
**Agent Instructions for Errors:**
- **401 Unauthorized**: The `PANGOLINFO_API_KEY` is missing or invalid. Prompt the user to set it.
- **429 Rate Limit**: The API is rate-limited. The agent MUST `yield` or `sleep` for 5 seconds before retrying, instead of failing the task.
- **Empty Results**: Check if the ASIN or keyword is valid for the target marketplace.
