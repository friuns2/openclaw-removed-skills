#!/usr/bin/env python3
"""
Pangolinfo Amazon Scrape API Client

Zero-dependency Python client for Pangolinfo's Amazon Scrape APIs.
Supports product detail lookup, keyword search, bestsellers, new releases,
category browsing, seller products, variant options, and product reviews.

Semantic usage (no URL required):
    pangolinfo.py --content B0DYTF8L2W --mode amazon --site amz_us
    pangolinfo.py --q "wireless mouse" --mode amazon --site amz_us
    pangolinfo.py --content B00163U4LK --mode review --site amz_us

Legacy usage (URL-based):
    pangolinfo.py --url "https://amazon.com/dp/..." --mode amazon

Environment:
    PANGOLINFO_API_KEY  - API key (skips login)
    PANGOLINFO_EMAIL    - Account email (for login)
    PANGOLINFO_PASSWORD - Account password (for login)
"""

import argparse
import io
import json
import os
import re
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Fix Windows / macOS console encoding for Unicode output
# ---------------------------------------------------------------------------
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_BASE = "https://scrapeapi.pangolinfo.com"
AUTH_ENDPOINT = f"{API_BASE}/api/v1/auth"
SCRAPE_V1_ENDPOINT = f"{API_BASE}/api/v1/scrape"
FOLLOW_SELLER_ENDPOINT = f"{API_BASE}/api/v1/scrape/follow-seller"
VARIANT_ASIN_ENDPOINT = f"{API_BASE}/api/v1/scrape/variant-asin"
API_KEY_CACHE_PATH = Path.home() / ".pangolinfo_api_key"

# User-facing registration/top-up link (not the API endpoint)
REFERRER_TAG = "clawhub_amz"
PANGOLINFO_URL = f"https://pangolinfo.com/?referrer={REFERRER_TAG}"

CACHE_TO_DISK = False

EXIT_SUCCESS = 0
EXIT_API_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_NETWORK_ERROR = 3
EXIT_AUTH_ERROR = 4

AMAZON_PARSERS = [
    "amzProductDetail",
    "amzKeyword",
    "amzProductOfCategory",
    "amzProductOfSeller",
    "amzBestSellers",
    "amzNewReleases",
    "amzFollowSeller",
    "amzVariantAsin",
    "amzReviewV2",
]

REVIEW_STAR_FILTERS = [
    "all_stars", "five_star", "four_star", "three_star",
    "two_star", "one_star", "positive", "critical",
]

REVIEW_SORT_OPTIONS = ["recent", "helpful"]

AMAZON_SITES = {
    "amz_us": "amazon.com",
    "amz_uk": "amazon.co.uk",
    "amz_ca": "amazon.ca",
    "amz_de": "amazon.de",
    "amz_fr": "amazon.fr",
    "amz_jp": "amazon.co.jp",
    "amz_it": "amazon.it",
    "amz_es": "amazon.es",
    "amz_au": "amazon.com.au",
    "amz_mx": "amazon.com.mx",
    "amz_sa": "amazon.sa",
    "amz_ae": "amazon.ae",
    "amz_br": "amazon.com.br",
}

# ASIN pattern: starts with B0 + 8 alphanumeric chars (most common Amazon ASIN format)
# More precise than generic 10-char to avoid false positives on seller IDs / node IDs
ASIN_PATTERN = re.compile(r"^B0[A-Z0-9]{8}$", re.IGNORECASE)

# Known Pangolinfo API error hints
API_ERROR_HINTS = {
    1004: "Invalid token. Will auto-retry with fresh credentials.",
    1009: "Invalid parser name. Check --parser value.",
    2001: f"Insufficient credits. Top up at {PANGOLINFO_URL}",
    2005: f"No active plan. Subscribe at {PANGOLINFO_URL}",
    2007: f"Account expired. Renew at {PANGOLINFO_URL}",
    2009: "Usage limit reached for current billing cycle. Contact support.",
    2010: "Bill day not configured. Contact support.",
    4029: "Rate limited by server. Reduce request frequency.",
    10000: "Task execution failed. Retry or check query format.",
    10001: "Task execution failed. Likely a temporary server issue.",
}


# ---------------------------------------------------------------------------
# Error helper
# ---------------------------------------------------------------------------
def _emit_error(code, message, hint=None, api_code=None, exit_code=None):
    """Print structured error JSON to stderr and optionally exit."""
    envelope = {"success": False, "error": {"code": code, "message": message}}
    if api_code is not None:
        envelope["error"]["api_code"] = api_code
    if hint:
        envelope["error"]["hint"] = hint
    print(json.dumps(envelope, ensure_ascii=False), file=sys.stderr)
    if exit_code is not None:
        sys.exit(exit_code)


def _is_ssl_error(exc):
    msg = str(exc)
    return "CERTIFICATE_VERIFY_FAILED" in msg or "SSL" in msg


def _emit_ssl_error():
    _emit_error(
        "SSL_CERT",
        "SSL certificate verification failed.",
        hint=(
            "macOS: run '/Applications/Python 3.x/Install Certificates.command' "
            "or set SSL_CERT_FILE. See: python3 -c \"import certifi; print(certifi.where())\""
        ),
        exit_code=EXIT_NETWORK_ERROR,
    )


# ---------------------------------------------------------------------------
# API key management
# ---------------------------------------------------------------------------
def load_cached_api_key():
    if API_KEY_CACHE_PATH.exists():
        api_key = API_KEY_CACHE_PATH.read_text().strip()
        if api_key and len(api_key.split(".")) == 3:
            return api_key
    return None


def save_cached_api_key(api_key):
    if not CACHE_TO_DISK:
        return
    try:
        fd = os.open(
            str(API_KEY_CACHE_PATH) + ".tmp",
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            stat.S_IRUSR | stat.S_IWUSR,
        )
        with os.fdopen(fd, "w") as f:
            f.write(api_key)
        os.replace(str(API_KEY_CACHE_PATH) + ".tmp", str(API_KEY_CACHE_PATH))
    except OSError:
        API_KEY_CACHE_PATH.write_text(api_key)
        try:
            API_KEY_CACHE_PATH.chmod(0o600)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------
def _http_post(url, body_dict, headers=None, timeout=30):
    """POST JSON and return parsed response."""
    payload = json.dumps(body_dict).encode()
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=payload, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        if _is_ssl_error(e):
            _emit_ssl_error()
        raise
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        _emit_error(
            "PARSE_ERROR",
            "API returned invalid JSON.",
            hint="The API may be temporarily unavailable. Retry in a moment.",
            exit_code=EXIT_NETWORK_ERROR,
        )


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def authenticate(email, password):
    try:
        result = _http_post(AUTH_ENDPOINT, {"email": email, "password": password})
    except urllib.error.URLError:
        _emit_error(
            "NETWORK", "Network error during authentication.",
            hint="Check your internet connection and try again.",
            exit_code=EXIT_NETWORK_ERROR,
        )

    if result.get("code") != 0:
        _emit_error(
            "AUTH_FAILED", "Authentication failed.",
            hint="Verify PANGOLINFO_EMAIL and PANGOLINFO_PASSWORD are correct.",
            api_code=result.get("code"),
            exit_code=EXIT_AUTH_ERROR,
        )

    api_key = result["data"]
    save_cached_api_key(api_key)
    return api_key


def get_api_key():
    api_key = os.environ.get("PANGOLINFO_API_KEY")
    if api_key:
        save_cached_api_key(api_key)
        return api_key

    api_key = load_cached_api_key()
    if api_key:
        return api_key

    email = os.environ.get("PANGOLINFO_EMAIL")
    password = os.environ.get("PANGOLINFO_PASSWORD")
    if not email or not password:
        _emit_error(
            "MISSING_ENV", "No authentication credentials found.",
            hint="Set PANGOLINFO_API_KEY, or both PANGOLINFO_EMAIL and PANGOLINFO_PASSWORD.",
            exit_code=EXIT_AUTH_ERROR,
        )
    return authenticate(email, password)


def refresh_api_key():
    email = os.environ.get("PANGOLINFO_EMAIL")
    password = os.environ.get("PANGOLINFO_PASSWORD")
    if not email or not password:
        _emit_error(
            "MISSING_ENV", "Cannot refresh API key without credentials.",
            hint="Set PANGOLINFO_EMAIL and PANGOLINFO_PASSWORD environment variables.",
            exit_code=EXIT_AUTH_ERROR,
        )
    return authenticate(email, password)


# ---------------------------------------------------------------------------
# Amazon helpers
# ---------------------------------------------------------------------------
def is_asin(text):
    """Check if text looks like an Amazon ASIN (B0 prefix + 8 alphanumeric)."""
    return bool(ASIN_PATTERN.match(text))


def normalize_asin(text):
    """Uppercase an ASIN-like string."""
    return text.upper() if is_asin(text) else text


def infer_amazon_parser(content):
    """Infer parser from content pattern. Only called when parser is defaulted."""
    if not content:
        return None
    if is_asin(content):
        return "amzProductDetail"
    return "amzKeyword"


def infer_site_from_url(url):
    for site_code, domain in sorted(AMAZON_SITES.items(), key=lambda x: len(x[1]), reverse=True):
        if domain in url:
            return site_code
    return None


def build_review_body(asin, site, filter_by_star, sort_by, page_count, fmt):
    if not asin:
        _emit_error(
            "USAGE_ERROR", "Review mode requires an ASIN.",
            hint="Provide --content <ASIN> or --asin <ASIN>.",
            exit_code=EXIT_USAGE_ERROR,
        )
    domain = AMAZON_SITES.get(site or "amz_us", "amazon.com")
    return {
        "url": f"https://www.{domain}",
        "format": fmt,
        "parserName": "amzReviewV2",
        "bizContext": {
            "bizKey": "review",
            "asin": normalize_asin(asin),
            "pageCount": page_count,
            "filterByStar": filter_by_star,
            "sortBy": sort_by,
        },
    }


def build_follow_seller_body(asin, site, zipcode):
    if not asin:
        _emit_error(
            "USAGE_ERROR", "Follow Seller mode requires an ASIN.",
            hint="Provide --content <ASIN> or --asin <ASIN>.",
            exit_code=EXIT_USAGE_ERROR,
        )
    domain = AMAZON_SITES.get(site or "amz_us", "amazon.com")
    return {
        "url": f"https://www.{domain}",
        "parserName": "amzFollowSeller",
        "bizContext": {
            "zipcode": zipcode,
            "asin": normalize_asin(asin),
        },
    }


def build_variant_asin_body(asin, site, zipcode):
    if not asin:
        _emit_error(
            "USAGE_ERROR", "Variant ASIN mode requires an ASIN.",
            hint="Provide --content <ASIN> or --asin <ASIN>.",
            exit_code=EXIT_USAGE_ERROR,
        )
    domain = AMAZON_SITES.get(site or "amz_us", "amazon.com")
    return {
        "url": f"https://www.{domain}",
        "parserName": "amzVariantAsin",
        "bizContext": {
            "zipcode": zipcode,
            "asin": normalize_asin(asin),
        },
    }


def build_amazon_body(url, query, content, site, parser, zipcode, fmt, parser_was_defaulted):
    """Build request body for Amazon Scrape API."""
    body = {
        "format": fmt,
        "parserName": parser,
        "bizContext": {"zipcode": zipcode},
    }

    if url:
        body["url"] = url
        body["site"] = site or infer_site_from_url(url) or "amz_us"
        if content:
            body["content"] = normalize_asin(content)
        return body

    effective_content = content or query
    if effective_content:
        if not site:
            site = "amz_us"
        body["site"] = site
        body["content"] = normalize_asin(effective_content)
        # Only auto-infer parser if user didn't explicitly set it
        if parser_was_defaulted:
            inferred = infer_amazon_parser(effective_content)
            if inferred:
                body["parserName"] = inferred
        return body

    _emit_error(
        "USAGE_ERROR", "Amazon mode requires --url, --content, or --q.",
        hint="Provide at least one of: --url <URL>, --content <ASIN/keyword>, --q <keyword>.",
        exit_code=EXIT_USAGE_ERROR,
    )


# ---------------------------------------------------------------------------
# API call with retry
# ---------------------------------------------------------------------------
def call_api(api_key, body, endpoint, max_retries=3, timeout=120):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Pangolinfo-CLI/2.0",
    }

    for attempt in range(max_retries):
        try:
            result = _http_post(endpoint, body, headers=headers, timeout=timeout)
            return result
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode() if e.fp else ""
            except Exception:
                pass

            if e.code == 429:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                _emit_error(
                    "RATE_LIMIT", "Rate limited by API server.",
                    hint="Wait a moment and retry, or reduce request frequency.",
                    exit_code=EXIT_NETWORK_ERROR,
                )

            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue

            detail = ""
            if error_body:
                try:
                    err_json = json.loads(error_body)
                    detail = f" Server: {err_json.get('message', error_body[:200])}"
                except (json.JSONDecodeError, ValueError):
                    detail = f" Server: {error_body[:200]}"

            _emit_error(
                "API_ERROR", f"HTTP {e.code} from API.{detail}",
                hint="Check your request parameters and try again.",
                exit_code=EXIT_NETWORK_ERROR,
            )
        except urllib.error.URLError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            _emit_error(
                "NETWORK", "Network error communicating with API.",
                hint="Check your internet connection and try again.",
                exit_code=EXIT_NETWORK_ERROR,
            )

    _emit_error(
        "NETWORK", "API call failed after retries.",
        hint="Check your internet connection and try again.",
        exit_code=EXIT_NETWORK_ERROR,
    )


def handle_response(result, api_key, body, endpoint, timeout=120):
    if result.get("code") == 1004:
        new_api_key = refresh_api_key()
        return call_api(new_api_key, body, endpoint, timeout=timeout)
    return result


# ---------------------------------------------------------------------------
# Output extraction
# ---------------------------------------------------------------------------
def extract_amazon_output(result):
    code = result.get("code")
    if code != 0:
        hint = API_ERROR_HINTS.get(code, f"Pangolinfo API error code {code}. Retry or check request.")
        return {
            "success": False,
            "error": {
                "code": "API_ERROR",
                "api_code": code,
                "message": result.get("message", "Unknown API error"),
                "hint": hint,
            },
        }

    data = result.get("data", {})
    output = {
        "success": True,
        "task_id": data.get("taskId"),
        "url": data.get("url"),
    }

    json_data = data.get("json")

    if isinstance(json_data, list) and len(json_data) > 0:
        first = json_data[0]
        if isinstance(first, dict) and "metadata" in first:
            output["metadata"] = first["metadata"]
            inner_data = first.get("data", {})
            results = inner_data.get("results", [])
            output["results"] = results
            output["results_count"] = len(results)
        else:
            output["results"] = json_data
            output["results_count"] = len(json_data)
    elif isinstance(json_data, dict):
        output["results"] = [json_data]
        output["results_count"] = 1
    else:
        output["results"] = []
        output["results_count"] = 0

    return output


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Pangolinfo Amazon Scrape API Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 pangolinfo.py --asin B0DYTF8L2W --site amz_us\n"
            '  python3 pangolinfo.py --q "wireless mouse" --site amz_us\n'
            "  python3 pangolinfo.py --content electronics --parser amzBestSellers --site amz_us\n"
            "  python3 pangolinfo.py --content B00163U4LK --mode review --filter-star critical\n"
            "  python3 pangolinfo.py --asin B0G4QPYK4Z --parser amzVariantAsin\n"
            "  python3 pangolinfo.py --auth-only\n"
        ),
    )
    parser.add_argument("--q", dest="query", help="Search query or keyword")
    parser.add_argument("--url", dest="target_url", help="Target Amazon URL (legacy)")
    parser.add_argument("--content", help="Content identifier: ASIN, keyword, category Node ID, seller ID")
    parser.add_argument("--asin", help="Amazon ASIN shortcut (auto-uppercases, implies amzProductDetail)")
    parser.add_argument(
        "--site", "--region", dest="site",
        choices=list(AMAZON_SITES.keys()),
        help="Amazon site/region code (default: amz_us)",
    )
    parser.add_argument(
        "--mode", choices=["amazon", "review"], default="amazon",
        help="API mode (default: amazon)",
    )
    parser.add_argument(
        "--parser", choices=AMAZON_PARSERS, default=None,
        help="Parser name (auto-inferred when not specified)",
    )
    parser.add_argument("--zipcode", default="10041", help="US zipcode for localized pricing (default: 10041)")
    parser.add_argument(
        "--format", dest="fmt", choices=["json", "rawHtml", "markdown"],
        default="json", help="Response format (default: json)",
    )
    parser.add_argument(
        "--filter-star", dest="filter_star", choices=REVIEW_STAR_FILTERS,
        default="all_stars", help="Review star filter (review mode only)",
    )
    parser.add_argument(
        "--sort-by", dest="sort_by", choices=REVIEW_SORT_OPTIONS,
        default="recent", help="Review sort order (review mode only)",
    )
    parser.add_argument(
        "--pages", dest="page_count", type=int, default=1,
        help="Number of review pages (5 credits/page, default: 1)",
    )
    parser.add_argument("--auth-only", action="store_true", help="Auth check only")
    parser.add_argument("--raw", action="store_true", help="Output raw API response")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds (default: 120)")
    parser.add_argument(
        "--cache-key", action="store_true",
        help="Persist API key to ~/.pangolinfo_api_key. Also: PANGOLINFO_CACHE=1.",
    )

    args = parser.parse_args()

    # Track whether parser was explicitly set by user
    parser_was_defaulted = args.parser is None
    if parser_was_defaulted:
        args.parser = "amzProductDetail"

    # Configure caching
    global CACHE_TO_DISK
    CACHE_TO_DISK = bool(args.cache_key) or os.environ.get("PANGOLINFO_CACHE", "").strip().lower() in (
        "1", "true", "yes", "on",
    )

    # --asin shortcut
    if args.asin:
        args.content = args.asin.upper()
        if parser_was_defaulted:
            args.parser = "amzProductDetail"

    # Validation
    if args.page_count < 1:
        parser.error("--pages must be at least 1")

    # Auto-detect review mode
    if args.mode == "amazon":
        if args.parser == "amzReviewV2" or args.filter_star != "all_stars":
            args.mode = "review"

    if not args.query and not args.target_url and not args.content and not args.auth_only:
        parser.error("--q, --url, or --content is required unless using --auth-only")

    # Authenticate
    api_key = get_api_key()

    if args.auth_only:
        preview = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        print(json.dumps({
            "success": True,
            "message": "Authentication successful",
            "api_key_preview": preview,
        }, indent=2))
        sys.exit(EXIT_SUCCESS)

    # Route to correct endpoint and body builder
    if args.parser == "amzFollowSeller":
        asin = args.content or args.query
        body = build_follow_seller_body(asin, args.site, args.zipcode)
        endpoint = FOLLOW_SELLER_ENDPOINT
    elif args.parser == "amzVariantAsin":
        asin = args.content or args.query
        body = build_variant_asin_body(asin, args.site, args.zipcode)
        endpoint = VARIANT_ASIN_ENDPOINT
    elif args.mode == "review":
        asin = args.content or args.query
        body = build_review_body(
            asin, args.site, args.filter_star, args.sort_by, args.page_count, args.fmt,
        )
        endpoint = SCRAPE_V1_ENDPOINT
    else:
        body = build_amazon_body(
            args.target_url, args.query, args.content, args.site,
            args.parser, args.zipcode, args.fmt, parser_was_defaulted,
        )
        endpoint = SCRAPE_V1_ENDPOINT

    # Call API
    result = call_api(api_key, body, endpoint, timeout=args.timeout)

    if result is None:
        _emit_error(
            "NETWORK", "API call failed after retries.",
            hint="Check your internet connection and try again.",
            exit_code=EXIT_NETWORK_ERROR,
        )

    result = handle_response(result, api_key, body, endpoint, timeout=args.timeout)

    if result is None:
        _emit_error(
            "NETWORK", "API call failed after token refresh.",
            hint="Check your internet connection and try again.",
            exit_code=EXIT_NETWORK_ERROR,
        )

    # Output
    if args.raw:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        output = extract_amazon_output(result)
        if output.get("success"):
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            # Errors to stderr, matching documented behavior
            print(json.dumps(output, indent=2, ensure_ascii=False), file=sys.stderr)

    if result.get("code") != 0:
        sys.exit(EXIT_API_ERROR)

    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
