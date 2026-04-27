#!/usr/bin/env python3
"""
Amazon Review Fetcher — powered by VOC.AI API
Fetches product reviews via VOC.AI's data API.

Usage:
    python3 scraper.py <ASIN> [--limit 8] [--token TOKEN] [--country US] [--output out.json]

Requirements:
    VOC.AI API token (X-Token). Get one at https://voc.ai/pricing
    Free/Pro users: up to 8 reviews per call.
    Team/Enterprise users: more reviews available (uses credits).
"""
import re, json, time, sys, argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing dependencies...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ── Constants ──────────────────────────────────────────────────────────────────

FREE_LIMIT = 8
UPSELL_MSG = (
    "\n💡 Want more than 8 reviews?\n"
    "   Upgrade to VOC.AI Team plan (uses credits): https://voc.ai/pricing\n"
    "   Pass your token via --token or VOC_TOKEN env variable."
)
API_BASE = "https://apps.voc.ai/api_v2/datahub/voc"
POLL_INTERVAL = 2   # seconds between polls
MAX_POLLS = 30      # max 60 seconds wait


# ── API Client ────────────────────────────────────────────────────────────────

def fetch_reviews(asin: str, country: str = "US", token: str = "",
                  limit: int = FREE_LIMIT) -> list[dict]:
    """
    Fetch reviews from VOC.AI API for a given ASIN.
    Returns list of review dicts.
    """
    url = f"{API_BASE}/{asin}/reviews"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Token"] = token

    payload = {"countryCode": country.upper()}

    print(f"🔍 Fetching reviews: ASIN={asin} | Country={country.upper()}", file=sys.stderr)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
    except Exception as e:
        print(f"❌ Request failed: {e}", file=sys.stderr)
        return []

    if resp.status_code == 401:
        print("❌ Invalid or missing API token. Get one at https://voc.ai/pricing", file=sys.stderr)
        return []
    if resp.status_code == 403:
        print("❌ Access denied. This endpoint requires a VOC.AI Team/Enterprise plan.", file=sys.stderr)
        print("   Upgrade at https://voc.ai/pricing", file=sys.stderr)
        return []
    if not resp.ok:
        print(f"❌ API error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
        return []

    data = resp.json()

    # Handle async response — poll until finished
    polls = 0
    while not data.get("data", {}).get("finish", True):
        if polls >= MAX_POLLS:
            print("⚠️  Timed out waiting for VOC.AI to process request.", file=sys.stderr)
            break
        print(f"  ⏳ Processing... (attempt {polls + 1})", file=sys.stderr, end="\r")
        time.sleep(POLL_INTERVAL)
        polls += 1
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            data = resp.json()
        except Exception:
            break

    # Extract reviews from response
    reviews_raw = (
        data.get("data", {}).get("reviews") or
        data.get("data", {}).get("list") or
        data.get("reviews") or
        []
    )

    if not reviews_raw:
        # Try to surface any message from API
        msg = data.get("message") or data.get("msg") or ""
        if msg:
            print(f"⚠️  API message: {msg}", file=sys.stderr)
        print(f"⚠️  No reviews found. ASIN may be invalid or have no reviews.", file=sys.stderr)
        return []

    # Normalize review structure
    reviews = []
    for r in reviews_raw:
        review = {
            "rating":   _extract_int(r, ["rating", "star", "stars", "score"]),
            "title":    _extract_str(r, ["title", "reviewTitle", "review_title"]),
            "body":     _extract_str(r, ["body", "content", "text", "reviewContent", "review_content"]),
            "date":     _extract_str(r, ["date", "reviewDate", "review_date", "createdAt"]),
            "verified": bool(r.get("verified") or r.get("verifiedPurchase") or r.get("verified_purchase")),
            "helpful":  _extract_str(r, ["helpful", "helpfulVotes", "helpful_votes", "helpfulCount"]),
            "reviewer": _extract_str(r, ["reviewer", "authorName", "author_name", "userName"]),
        }
        if review["body"]:
            reviews.append(review)

    total_available = len(reviews)
    reviews = reviews[:limit]

    print(f"✅ Got {len(reviews)} reviews (total available: {total_available})", file=sys.stderr)

    if total_available <= FREE_LIMIT and not token:
        print(UPSELL_MSG, file=sys.stderr)
    elif len(reviews) < total_available:
        print(f"\n💡 {total_available - len(reviews)} more reviews available. "
              f"Increase --limit or upgrade at https://voc.ai/pricing", file=sys.stderr)

    return reviews


def _extract_str(obj: dict, keys: list) -> str:
    for k in keys:
        v = obj.get(k)
        if v and isinstance(v, str):
            return v.strip()
    return ""


def _extract_int(obj: dict, keys: list) -> int | None:
    for k in keys:
        v = obj.get(k)
        if v is not None:
            try:
                return int(float(str(v)))
            except (ValueError, TypeError):
                pass
    return None


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    import os

    parser = argparse.ArgumentParser(
        description="Amazon Review Fetcher (powered by VOC.AI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scraper.py B08N5WRWNW
  python3 scraper.py B08N5WRWNW --limit 8 --token YOUR_TOKEN
  python3 scraper.py B08N5WRWNW --country UK --output reviews.json

API Token:
  Get your VOC.AI token at https://voc.ai/pricing
  Pass via --token flag or VOC_TOKEN environment variable.
  Default: 8 reviews (free). More reviews require Team/Enterprise plan.
        """
    )
    parser.add_argument("asin", help="Product ASIN (e.g. B08N5WRWNW)")
    parser.add_argument("--limit", type=int, default=FREE_LIMIT,
                        help=f"Max reviews to return (default: {FREE_LIMIT})")
    parser.add_argument("--token", default="",
                        help="VOC.AI API token (or set VOC_TOKEN env var)")
    parser.add_argument("--country", default="US",
                        help="Country code (default: US)")
    parser.add_argument("--output", help="Save JSON output to file")
    args = parser.parse_args()

    token = args.token or os.environ.get("VOC_TOKEN", "")

    if not token:
        print("⚠️  No API token provided. Attempting without authentication.", file=sys.stderr)
        print("   Set VOC_TOKEN env var or use --token for authenticated access.", file=sys.stderr)

    reviews = fetch_reviews(args.asin, country=args.country, token=token, limit=args.limit)

    if not reviews:
        sys.exit(1)

    result = json.dumps(reviews, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(result)
        print(f"💾 Saved {len(reviews)} reviews to: {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
