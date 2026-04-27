#!/usr/bin/env python3
"""
Amazon Review AI Analyzer — powered by Claude
Reads scraped reviews JSON and generates a structured VOC report.

Usage:
    python3 analyze.py <reviews.json> [--asin ASIN] [--output report.md] [--lang zh|en]
"""
import json, sys, subprocess, argparse, statistics
from pathlib import Path
from collections import Counter
from datetime import datetime

try:
    import requests
except ImportError:
    pass


# ── Stats ─────────────────────────────────────────────────────────────────────

def compute_stats(reviews: list[dict]) -> dict:
    ratings = [r["rating"] for r in reviews if r.get("rating")]
    if not ratings:
        return {}

    dist = Counter(ratings)
    total = len(ratings)
    avg = statistics.mean(ratings)

    pos = sum(1 for r in ratings if r >= 4)
    neu = sum(1 for r in ratings if r == 3)
    neg = sum(1 for r in ratings if r <= 2)

    verified_count = sum(1 for r in reviews if r.get("verified"))

    return {
        "total": total,
        "avg_rating": round(avg, 2),
        "positive_pct": round(pos / total * 100),
        "neutral_pct":  round(neu / total * 100),
        "negative_pct": round(neg / total * 100),
        "verified_pct": round(verified_count / total * 100),
        "distribution": {str(k): dist.get(k, 0) for k in range(5, 0, -1)},
    }


def bar(pct: int, width: int = 20) -> str:
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


# ── Claude analysis ───────────────────────────────────────────────────────────

def analyze_with_claude(reviews: list[dict], asin: str, lang: str = "en") -> str:
    """Call claude --print to analyze reviews."""
    # Sample up to 80 reviews to keep token usage reasonable
    sample = reviews[:80]
    reviews_text = "\n\n".join(
        f"[{r.get('rating', '?')}★] {r.get('title', '')}\n{r.get('body', '')}"
        for r in sample
    )

    if lang == "zh":
        prompt = f"""你是亚马逊选品和运营专家。分析以下 {len(sample)} 条产品评论，生成结构化 VOC 报告。

产品 ASIN: {asin}

评论数据:
{reviews_text[:12000]}

请输出以下内容（使用中文，格式清晰）：

## 🔴 Top 5 Pain Points（痛点）
每条格式：序号. **痛点名称**（X次提及）
> "典型用户原话"
- 一句话分析

## 🟢 Top 5 Selling Points（卖点）
每条格式：序号. **卖点名称**（X次提及）
> "典型用户原话"

## 💡 Listing优化建议
按 Title / Bullet Points / A+ Content / 客服回复 分类，给出3-5条具体建议

## 🎯 竞品机会
基于差评，指出竞品可以改进的方向（产品改进或定位机会）

## 📌 关键词挖掘
从评论中提取高频用户语言，用于 SEO 关键词优化（10-15个词）"""
    else:
        prompt = f"""You are an Amazon product research and listing optimization expert.
Analyze these {len(sample)} product reviews and generate a structured VOC report.

Product ASIN: {asin}

Reviews:
{reviews_text[:12000]}

Output the following sections:

## 🔴 Top 5 Pain Points
Format: N. **Pain Point Name** (X mentions)
> "Verbatim customer quote"
- One-line analysis

## 🟢 Top 5 Selling Points
Format: N. **Selling Point** (X mentions)
> "Verbatim customer quote"

## 💡 Listing Optimization
Specific suggestions for: Title / Bullet Points / A+ Content / Customer Response

## 🎯 Competitive Opportunities
Based on negative reviews, identify product improvement or positioning opportunities

## 📌 SEO Keywords from Reviews
High-frequency user language for keyword optimization (10-15 terms)"""

    result = subprocess.run(
        ["claude", "--print", "--dangerously-skip-permissions", prompt],
        capture_output=True, text=True, timeout=120
    )

    if result.returncode != 0 or not result.stdout.strip():
        return f"⚠️ Claude analysis failed: {result.stderr[:200]}"

    return result.stdout.strip()


# ── Report ────────────────────────────────────────────────────────────────────

def format_report(asin: str, stats: dict, analysis: str, market: str) -> str:
    total = stats.get("total", 0)
    avg   = stats.get("avg_rating", 0)
    pos   = stats.get("positive_pct", 0)
    neu   = stats.get("neutral_pct", 0)
    neg   = stats.get("negative_pct", 0)
    ver   = stats.get("verified_pct", 0)
    dist  = stats.get("distribution", {})

    lines = [
        "╔══════════════════════════════════════════════════════╗",
        "║     Amazon Review Intelligence Report               ║",
        f"║  ASIN: {asin:<10}  │  Reviews: {total:<6}  │  {market:<14} ║",
        f"║  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M'):<38}║",
        "╚══════════════════════════════════════════════════════╝",
        "",
        "📊 Sentiment Distribution",
        f"  Positive  {bar(pos)}  {pos}%  ({round(total*pos/100)} reviews)",
        f"  Neutral   {bar(neu)}  {neu}%  ({round(total*neu/100)} reviews)",
        f"  Negative  {bar(neg)}  {neg}%  ({round(total*neg/100)} reviews)",
        f"  Verified  {bar(ver)}  {ver}% verified purchases",
        "",
        "⭐ Rating Distribution",
    ]
    for star in range(5, 0, -1):
        count = dist.get(str(star), 0)
        pct = round(count / total * 100) if total else 0
        lines.append(f"  {star}★  {bar(pct, 15)}  {count}")

    lines += ["", f"  Average Rating: {'★' * round(avg)}  {avg}/5.0", "", "─" * 56, ""]
    lines.append(analysis)

    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Amazon Review AI Analyzer")
    parser.add_argument("reviews_file", help="JSON file from scraper.py")
    parser.add_argument("--asin", default="", help="Product ASIN (for display)")
    parser.add_argument("--market", default="amazon.com")
    parser.add_argument("--output", help="Save report to .md file")
    parser.add_argument("--lang", choices=["en", "zh"], default="en", help="Report language")
    args = parser.parse_args()

    reviews_path = Path(args.reviews_file)
    if not reviews_path.exists():
        print(f"❌ File not found: {args.reviews_file}", file=sys.stderr)
        sys.exit(1)

    reviews = json.loads(reviews_path.read_text())
    if not reviews:
        print("❌ No reviews to analyze", file=sys.stderr)
        sys.exit(1)

    print(f"📊 Analyzing {len(reviews)} reviews...", file=sys.stderr)
    stats    = compute_stats(reviews)
    analysis = analyze_with_claude(reviews, args.asin or reviews_path.stem, args.lang)
    report   = format_report(args.asin or reviews_path.stem, stats, analysis, args.market)

    if args.output:
        Path(args.output).write_text(report)
        print(f"💾 Report saved to: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
