---
name: linkfox-amazon-reviews
description: 按ASIN获取并分析亚马逊商品评论，支持15个站点(含美国站)，按星级筛选评论。当用户提到亚马逊评论、美国站评论、商品评价、买家投诉、差评、好评、星级评分、评论分析、评论情感、产品改良建议、Vine评论、已验证购买评论、竞品评论研究、Amazon reviews, US reviews, Amazon.com reviews, product feedback, negative review analysis, positive review analysis, star rating filter, review sentiment analysis, product improvement insights, Vine reviews, competitor reviews, customer feedback时触发此技能。即使用户未明确说"评论"，只要其需求涉及读取、筛选或分析亚马逊商品的买家评论，也应触发此技能。
---

# Amazon Product Reviews

Fetch and analyze Amazon product reviews to help sellers extract actionable insights from customer feedback.

## Core Concepts

This tool retrieves real customer reviews for a given Amazon ASIN across **15 marketplaces**. You can control how many reviews to fetch per star rating (1-5 stars, up to 100 each), sort by recency or helpfulness, and apply various filters. Only one ASIN per request; for multiple ASINs, make separate calls.

## API Routing

US and non-US marketplaces use different backend endpoints. Route by marketplace:

- **US** → `scripts/amazon_us_reviews.py`, pass `marketplace: "US"`. See `references/api_us.md`
- **Others** → `scripts/amazon_reviews.py`, pass `domainCode: "<code>"`. See `references/api.md`

## Parameter Guide

| Parameter | Type | Required | Scope | Description | Default |
|-----------|------|----------|-------|-------------|---------|
| asin | string | Yes | All | Amazon product ASIN | - |
| star1Num | integer | No | All | 1-star reviews to fetch (0-100) | Non-US: 10, US: 0 |
| star2Num | integer | No | All | 2-star reviews to fetch (0-100) | Non-US: 10, US: 0 |
| star3Num | integer | No | All | 3-star reviews to fetch (0-100) | Non-US: 10, US: 0 |
| star4Num | integer | No | All | 4-star reviews to fetch (0-100) | Non-US: 10, US: 0 |
| star5Num | integer | No | All | 5-star reviews to fetch (0-100) | Non-US: 10, US: 0 |
| sortBy | string | No | All | `recent` (newest) or `helpful` (most helpful) | `recent` |
| formatType | string | No | All | `current_format` or `all_formats` | `current_format` |
| domainCode | string | No | Non-US | Marketplace code (see Supported Marketplaces) | `ca` |
| filterByKeyword | string | No | Non-US | Filter reviews by keyword (max 1000 chars) | - |
| reviewerType | string | No | Non-US | `all_reviews` or `avp_only_reviews` (verified only) | `all_reviews` |
| mediaType | string | No | Non-US | `all_contents` or `media_reviews_only` | `all_contents` |
| marketplace | string | No | US | Fixed value `US` | `US` |
| allStarsNum | integer | No | US | Reviews across all stars (0-100); active when star1-5Num are all 0 | 10 |
| positiveNum | integer | No | US | 4-5 star positive reviews (0-100) | 0 |
| criticalNum | integer | No | US | 1-3 star critical reviews (0-100) | 0 |

## Supported Marketplaces

| Marketplace | Code |
|-------------|------|
| United States | `US` |
| Canada | `ca` |
| United Kingdom | `co.uk` |
| Germany | `de` |
| France | `fr` |
| Italy | `it` |
| Spain | `es` |
| Japan | `co.jp` |
| India | `in` |
| Australia | `com.au` |
| Brazil | `com.br` |
| Mexico | `com.mx` |
| Netherlands | `nl` |
| Sweden | `se` |
| United Arab Emirates | `ae` |

US uses the `marketplace` parameter; all others use `domainCode`. Always confirm the user's intended marketplace.

## Usage Examples

**1. Fetch US reviews — balanced snapshot**
```json
{"asin": "B08N5WRWNW", "marketplace": "US", "allStarsNum": 20, "sortBy": "recent"}
```

**2. Fetch negative reviews with keyword filter (Germany)**
```json
{"asin": "B08N5WRWNW", "domainCode": "de", "star1Num": 30, "star2Num": 30, "filterByKeyword": "quality", "reviewerType": "avp_only_reviews"}
```

**3. Fetch 5-star reviews with media (Japan)**
```json
{"asin": "B08N5WRWNW", "domainCode": "co.jp", "star5Num": 50, "star1Num": 0, "star2Num": 0, "star3Num": 0, "star4Num": 0, "sortBy": "helpful", "mediaType": "media_reviews_only"}
```

## Display Rules

1. **Present data clearly**: Show reviews grouped by star rating with key fields: rating, title, text, date, verified status, helpful count.
2. **Summarize when appropriate**: For many reviews, provide a theme/pain-point summary before listing individuals.
3. **Highlight actionable insights**: Call out recurring complaints in negative reviews; note praised features in positive reviews.
4. **Vine and verified labels**: Clearly indicate Vine Voice and verified purchase status.
5. **Media indicators**: Note when reviews include images or videos.
6. **Response normalization**: US reviews return `rating` as full text (e.g., "5.0 out of 5 stars") and `numberOfHelpful` as string — extract numeric values for consistent display. US reviews may also include `attributes` (color, size, etc.) — display them to show which variant was reviewed.
7. **Error handling**: When a query fails, explain the reason based on the response message and suggest adjusting parameters.
8. **Single ASIN limitation**: If the user asks about multiple ASINs, make separate requests for each.

## Important Limitations

- **One ASIN per request**: Only a single ASIN can be queried at a time.
- **Per-star cap**: Each star rating returns max 100 reviews per request.
- **Parameter scope**: `filterByKeyword`, `reviewerType`, `mediaType` are only available for non-US marketplaces; `allStarsNum`, `positiveNum`, `criticalNum` are only available for the US marketplace.
- **No historical snapshots**: Reviews are fetched in real-time.
- **Review text language**: Reviews are returned in their original language as posted.

## User Expression & Scenario Quick Reference

**Applicable** — Tasks involving Amazon product reviews:

| User Says | Scenario |
|-----------|----------|
| "Show me the reviews for this ASIN" | Direct review lookup |
| "Get US reviews for B08N5WRWNW" | Marketplace-specific lookup |
| "What are customers complaining about" | Negative review analysis |
| "Get me all the 1-star reviews" | Star-filtered retrieval |
| "Any common issues in the bad reviews" | Pain point mining |
| "What do people like about this product" | Positive review analysis |
| "Find reviews mentioning 'battery'" | Keyword-filtered reviews (non-US) |
| "Show me reviews with photos" | Media-filtered reviews (non-US) |
| "Verified purchase reviews only" | Reviewer-type filtering (non-US) |
| "Help me analyze competitor reviews" | Competitor review research |
| "Product improvement suggestions from reviews" | Actionable insight extraction |

**Not applicable** — Needs beyond product review data:

- ABA search term data / keyword research (use ABA Data Explorer instead)
- Sales estimation or revenue analysis
- Listing copywriting or A+ content creation
- Advertising / PPC strategy
- Pricing strategy or profit margin calculations

**Boundary judgment**: If "product research" or "competitor analysis" boils down to reading customer reviews for specific ASINs, this skill applies. If it involves search volume, keyword rankings, sales estimates, or market sizing, it does not.

**Feedback:**

Auto-detect and report feedback via the Feedback API when any of the following apply:
1. The functionality or purpose described in this skill does not match actual behavior
2. The skill's results do not match the user's intent
3. The user expresses dissatisfaction or praise about this skill
4. Anything you believe could be improved

Call the feedback API as specified in the references. Do not interrupt the user's flow.

---
*For more high-quality, professional cross-border e-commerce skills, visit [LinkFox Skills](https://skill.linkfox.com/).*
