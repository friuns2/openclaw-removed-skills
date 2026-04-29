---
name: pangolinfo-amazon-niche
description: >
  Amazon niche & category intelligence API. Let your AI agents discover profitable Amazon niches autonomously. Navigate category trees, map BSR, and filter by sales metrics. Ready for AutoGen, CrewAI, and OpenClaw.

metadata:
  openclaw:
    emoji: "🎯"
    os: ["darwin", "linux"]
    requires:
      env:
        - PANGOLINFO_API_KEY
        - PANGOLINFO_EMAIL
        - PANGOLINFO_PASSWORD
      notes: "Set PANGOLINFO_API_KEY (recommended). Alternative: set PANGOLINFO_EMAIL + PANGOLINFO_PASSWORD instead (optional, for email/password login). Credentials are NOT cached to disk by default; disk persistence only activates with explicit --cache-key flag or PANGOLINFO_CACHE=1."
tags: [amazon, niche-discovery, ecommerce, market-research, data-analysis, bestseller, api, scraping, product-hunting]
homepage: https://pangolinfo.com/?referrer=clawhub_amz_niche
version: 2.0.0
---


## 🌟 Why Use This Skill? (User Stories)
Stop manual product hunting. Let your AI agents discover profitable Amazon niches autonomously:
- **Niche Hunting & Discovery**: Automatically navigate Amazon category trees and filter sub-categories by sales volume and competition density.
- **BSR Intelligence**: Map Best Seller Ranks across complex category paths to validate product ideas.

## 🤖 Compatible Agent Frameworks
- **OpenClaw** (Perfect for autonomous market-research tasks)
- **LangGraph / CrewAI** (Ideal for multi-step product discovery graphs)

## 🌐 多语言适配 (Multi-language Support)
- **🇨🇳 中文适用场景**: 亚马逊底层选品类目挖掘与 BSR 追踪。通过细分市场过滤器定位蓝海类目，辅助卖家数据决策。
- **Agent Directive**: Always output the final analysis/report in the language of the user's prompt (e.g., reply in Chinese if asked in Chinese).


# Pangolinfo Amazon Niche Data

Query Amazon category and niche intelligence via Pangolinfo's 利基数据 (niche data) APIs. Covers 5 endpoints under `/api/v1/amzscope/*` for category exploration, search, path resolution, and advanced filtering by business metrics.

## When to Use This Skill

| Intent (EN) | Intent (CN) | Action |
|---|---|---|
| Browse Amazon category tree | 浏览亚马逊类目树 | Category Tree |
| Search for an Amazon category | 搜索亚马逊类目 | Category Search |
| Get full path of category IDs | 批量查询类目路径 | Category Paths |
| Filter categories by metrics | 按指标筛选类目 | Category Filter |
| Find Amazon niches | 查找亚马逊利基市场 | Niche Filter |
| Analyze category sales/trends | 分析类目销量/趋势 | Category Filter |
| Find low-competition niches | 寻找低竞争利基 | Niche Filter |

Do **not** use for Amazon product scraping, keyword search, or reviews -- those require the **pangolinfo-amazon-scraper** skill.

## Prerequisites

- **Python 3.8+** (stdlib only, no pip install needed)
- **Pangolinfo account** at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_niche)
- **Environment variables**: `PANGOLINFO_API_KEY` (recommended) OR `PANGOLINFO_EMAIL` + `PANGOLINFO_PASSWORD`

> **Security:** Credentials are held **in-memory only** by default. The script will **not** write any key or password to disk unless you explicitly opt in via `--cache-key` (or `PANGOLINFO_CACHE=1`), which persists the API key to `~/.pangolinfo_api_key` (mode 600).

macOS SSL error? Run: `/Applications/Python\ 3.x/Install\ Certificates.command`

## Script Execution

```bash
python3 scripts/pangolinfo.py --api category-search --keyword "headphones"
```

## Intent-to-Command Mapping

### 1. Browse Category Tree (top-level)

```bash
python3 scripts/pangolinfo.py --api category-tree
```

### 2. Browse Children of a Specific Node

```bash
python3 scripts/pangolinfo.py --api category-tree --parent-path "2619526011"
```

Nested nodes use `/`-joined paths: `--parent-path "2619526011/18116197011"`.

### 3. Search Categories by Keyword

```bash
python3 scripts/pangolinfo.py --api category-search --keyword "headphones"
```

Matches both English and Chinese category names.

### 4. Batch Resolve Category Paths

```bash
python3 scripts/pangolinfo.py --api category-paths --category-ids "2619526011,172282"
```

Also accepts JSON array: `--category-ids '["2619526011","172282"]'`.

### 5. Filter Categories by Business Metrics

```bash
python3 scripts/pangolinfo.py --api category-filter \
  --marketplace-id US --time-range l7d --sample-scope all_asin
```

Single-category detail:

```bash
python3 scripts/pangolinfo.py --api category-filter \
  --marketplace-id US --time-range l7d --sample-scope all_asin \
  --category-id 979832011
```

With advanced filters via `--extra`:

```bash
python3 scripts/pangolinfo.py --api category-filter \
  --marketplace-id US --time-range l30d --sample-scope all_asin \
  --extra 'buyBoxPriceAvgMin=1000' \
  --extra 'buyBoxPriceTiers=["mainstream","premium"]' \
  --extra 'sortField=unitSoldSum' \
  --extra 'sortOrder=desc'
```

### 6. Filter Niches by Business Metrics

```bash
python3 scripts/pangolinfo.py --api niche-filter --marketplace-id US
```

Search by title:

```bash
python3 scripts/pangolinfo.py --api niche-filter \
  --marketplace-id US --niche-title "yoga mat"
```

With advanced range filters:

```bash
python3 scripts/pangolinfo.py --api niche-filter \
  --marketplace-id US \
  --extra 'searchVolumeT90Min=1000' \
  --extra 'sortField=searchVolumeT90' \
  --extra 'sortOrder=desc'
```

## Smart Defaults

1. **Pagination defaults** -- `page=1`, `size=10` if not specified
2. **Filter APIs cap** -- `size` max 10 and `page` max 10 for `category-filter` and `niche-filter`
3. **`--extra` is JSON-parsed** -- numbers become ints, arrays become arrays, strings stay strings
4. **Marketplace default** -- no default; must be explicitly provided for filter APIs

## All CLI Options

| Flag | Description | Default |
|---|---|---|
| `--api` | API to call (see APIs below) | *required* |
| `--page` | 1-based page number (max 10 for filter APIs) | `1` |
| `--size` | Items per page (max 10 for filter APIs) | `10` |
| `--parent-path` | category-tree: parent node path | -- |
| `--keyword` | category-search: search term (EN or CN) | -- |
| `--category-ids` | category-paths: comma-separated or JSON array | -- |
| `--marketplace-id` | Marketplace code (e.g. US, UK, DE) | -- |
| `--time-range` | Aggregation range (e.g. l7d, l30d, l90d) | -- |
| `--sample-scope` | Sample scope (e.g. all_asin) | -- |
| `--category-id` | category-filter: single-category detail | -- |
| `--niche-id` | niche-filter: specific niche ID | -- |
| `--niche-title` | niche-filter: keyword match on title | -- |
| `--extra` | Extra field as `key=value` (repeatable, JSON-parsed) | -- |
| `--auth-only` | Auth check only (no credits) | -- |
| `--raw` | Output raw API response | -- |
| `--timeout` | Timeout in seconds | `120` |
| `--cache-key` | Persist API key to `~/.pangolinfo_api_key` | off |

## APIs

| API | `--api` value | Required fields | Endpoint | Credits |
|---|---|---|---|---|
| Category Tree | `category-tree` | -- | `/api/v1/amzscope/categories/children` | 2 |
| Category Search | `category-search` | `--keyword` | `/api/v1/amzscope/categories/search` | 2 |
| Category Paths | `category-paths` | `--category-ids` | `/api/v1/amzscope/categories/paths` | 2 |
| Category Filter | `category-filter` | `--marketplace-id --time-range --sample-scope` | `/api/v1/amzscope/categories/filter` | 5 |
| Niche Filter | `niche-filter` | `--marketplace-id` | `/api/v1/amzscope/niches/filter` | 10 |

## Marketplace IDs

| Code | Region | Code | Region |
|---|---|---|---|
| `US` | United States | `JP` | Japan |
| `UK` | United Kingdom | `IT` | Italy |
| `CA` | Canada | `ES` | Spain |
| `DE` | Germany | `MX` | Mexico |
| `FR` | France | `AU` | Australia |
| `IN` | India | `BR` | Brazil |
| `AE` | UAE | `SA` | Saudi Arabia |

## Cost

| API | Credits |
|---|---|
| Category Tree | 2 |
| Category Search | 2 |
| Category Paths | 2 |
| Category Filter | 5 |
| Niche Filter | 10 |

Credits consumed on success only (API code 0). Empty results are not charged. Auth checks are free.

## Output Format

JSON to **stdout** on success, error JSON to **stderr** on failure.

### Success

```json
{
  "success": true,
  "api": "searchCategoriesAPI",
  "items": [
    {
      "browseNodeId": "9059094011",
      "browseNodeName": "Headphones",
      "browseNodeNameCn": "耳机",
      "sellable": 1,
      "hasChild": 0
    }
  ],
  "total": 33,
  "page": 1,
  "size": 10,
  "totalPages": 4,
  "results_count": 10
}
```

### Error (stderr)

```json
{
  "success": false,
  "error": {
    "code": "API_ERROR",
    "api_code": 1002,
    "message": "Invalid Parameter: keyword is required",
    "hint": "Check required fields for this API. See references/error-codes.md."
  }
}
```

## Response Presentation

Match the user's language. Never dump raw JSON.

- **Category Tree**: hierarchical list with node name (EN/CN), sellable indicator
- **Category Search**: numbered list with category path, sellable, hasChild
- **Category Paths**: table of ID -> full path (EN/CN)
- **Category Filter**: metric summary card with sales, views, trends, price tier
- **Niche Filter**: niche overview with search volume, product count, brand count, growth
- **Empty results**: suggest loosening filters, checking marketplace, broadening search

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | API error |
| 2 | Usage error (bad arguments) |
| 3 | Network error |
| 4 | Authentication error |

## Error Reference

### Script Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| `MISSING_ENV` | No credentials | Set env vars |
| `AUTH_FAILED` | Wrong credentials | Verify email/password |
| `RATE_LIMIT` | Too many requests | Wait and retry |
| `NETWORK` | Connection issue | Check internet |
| `SSL_CERT` | Certificate error | See macOS SSL fix |
| `API_ERROR` | Pangolinfo API error | Check `api_code` and `hint` |
| `PARSE_ERROR` | Invalid API response | Retry |
| `USAGE_ERROR` | Bad arguments | Fix CLI args |

### Pangolinfo API Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| 1002 | Invalid parameter | Check required fields for the API |
| 1004 | Invalid token | Auto-retried by script |
| 2001 | Insufficient credits | Top up at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_niche) |
| 2005 | No active plan | Subscribe at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_niche) |
| 2007 | Account expired | Renew at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_niche) |
| 2009 | Usage limit reached | Wait for next billing cycle |
| 4029 | Rate limited | Reduce request frequency |
| 9100 | Service disabled | Retry later |
| 9101 | Data source unavailable | Retry later |
| 9102 | Quota exceeded | Contact support |

## Self-Test

Run `bash scripts/self_test.sh` to validate all 5 APIs. **This consumes up to ~21 credits** (Tree 2 + Search 2 + Paths 2 + CategoryFilter 5 + NicheFilter 10). Auth check is free. Only run when you need to verify connectivity.

## First-Time Setup

See [references/setup-guide.md](references/setup-guide.md) for interactive setup instructions.

Quick start:
```bash
export PANGOLINFO_API_KEY="your-api-key"
python3 scripts/pangolinfo.py --auth-only
```

## Important Notes for AI Agents

1. **Never dump raw JSON.** Parse and present per the Response Presentation guidelines.
2. **Match the user's language.**
3. **Be proactive.** Highlight top categories, summarize trends, flag high-competition niches.
4. **Credit awareness.** Niche Filter costs 10 credits -- warn before bulk queries.
5. **Use `--extra` for advanced filters.** All metric range/tier/trend filters go via `--extra key=value`.
6. **Default to `US` marketplace** unless context implies another region.
7. **Combine results.** "Find a good niche to sell in" = niche-filter + category-filter for deeper analysis.
8. **Security.** Never expose API keys or passwords.
9. **Handle multi-step.** E.g., "What's trending in electronics?" = category-search → category-filter with trend filters.
10. **Suggest next steps.** After showing niches, suggest drilling into specific categories.

## Advanced Filter Reference

See [references/amazon-niche-api.md](references/amazon-niche-api.md) for the full list of `--extra` filter fields (numeric ranges, tiers, trends, quantile buckets) for Category Filter and Niche Filter APIs.

## Output Schema

See [references/output-schema.md](references/output-schema.md) for per-API field documentation.


## 🎯 Quick Start Prompts (Copy-Paste)
- *"Navigate the Amazon category tree for 'Home & Kitchen', find sub-categories with low competition, and list the top 5 niches."*
- *"Extract the BSR (Best Seller Rank) history for the top 3 products in the 'Pet Supplies' niche."*

## 🛑 Boundaries & Error Handling
**When NOT to use:** Do not use for scraping individual product reviews (use `amazon-scraper` instead).
**Agent Instructions for Errors:**
- **401/403 Auth Error**: Ensure `PANGOLINFO_API_KEY` is injected into the environment.
- **429 Rate Limit**: Pause execution for 5 seconds, then retry automatically.
