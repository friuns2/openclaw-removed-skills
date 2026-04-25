#!/usr/bin/env bash
# VOC AI - Amazon Review Intelligence
# Usage: voc.sh <ASIN> [--limit N] [--market US] [--output file.md]

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_banner() {
  echo -e "${BLUE}"
  echo "  ██╗   ██╗ ██████╗  ██████╗      █████╗ ██╗"
  echo "  ██║   ██║██╔═══██╗██╔════╝     ██╔══██╗██║"
  echo "  ██║   ██║██║   ██║██║          ███████║██║"
  echo "  ╚██╗ ██╔╝██║   ██║██║          ██╔══██║██║"
  echo "   ╚████╔╝ ╚██████╔╝╚██████╗     ██║  ██║██║"
  echo "    ╚═══╝   ╚═════╝  ╚═════╝     ╚═╝  ╚═╝╚═╝"
  echo -e "${NC}"
  echo "  Amazon Review Intelligence | Powered by Shulex VOC"
  echo "  ─────────────────────────────────────────────────────"
  echo ""
}

usage() {
  echo "Usage: voc.sh <ASIN> [options]"
  echo ""
  echo "Options:"
  echo "  --limit N        Number of reviews to fetch (default: 8, max with API key)"
  echo "  --market CODE    Amazon marketplace: US CA MX GB DE FR IT ES JP AU (default: US)"
  echo "  --output FILE    Save report to file"
  echo "  --help           Show this help"
  echo ""
  echo "Examples:"
  echo "  voc.sh B08N5WRWNW                         # Quick analysis (8 reviews)"
  echo "  voc.sh B08N5WRWNW --limit 100             # Deep analysis (100 reviews)"
  echo "  voc.sh B08N5WRWNW --market JP              # Japan marketplace"
  echo "  voc.sh B08N5WRWNW --limit 200 --output report.md"
  echo ""
  echo "Environment:"
  echo "  VOC_API_KEY      Shulex VOC API key (required)"
  echo "                   Get yours free: https://apps.voc.ai/openapi?utm_source=skill&utm_medium=onboarding&utm_campaign=launch_apr"
  exit 0
}

# Parse args
ASIN=""
LIMIT=8
MARKET="US"
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) usage ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --market) MARKET="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    -*) echo "Unknown option: $1" >&2; usage ;;
    *) ASIN="$1"; shift ;;
  esac
done

if [[ -z "$ASIN" ]]; then
  echo -e "${RED}Please provide an ASIN${NC}" >&2
  echo "Run 'voc.sh --help' for usage." >&2
  exit 1
fi

# Validate ASIN format (10 alphanumeric chars)
if ! echo "$ASIN" | grep -qE '^[A-Z0-9]{10}$'; then
  echo -e "${YELLOW}Warning: ASIN format may be incorrect (expected 10 alphanumeric chars, e.g. B08N5WRWNW)${NC}" >&2
fi

# Check dependencies
check_deps() {
  local missing=0

  if ! command -v curl &>/dev/null; then
    echo "  - curl" >&2
    missing=1
  fi

  if ! command -v python3 &>/dev/null; then
    echo "  - python3" >&2
    missing=1
  fi

  if [[ -z "${VOC_API_KEY:-}" ]]; then
    echo "" >&2
    echo -e "${YELLOW}  VOC_API_KEY not set.${NC}" >&2
    echo "" >&2
    echo -e "  Get your ${GREEN}free${NC} API key in 30 seconds:" >&2
    echo -e "  ${CYAN}1.${NC} Register:   https://apps.voc.ai/openapi?utm_source=skill&utm_medium=onboarding&utm_campaign=launch_apr" >&2
    echo -e "  ${CYAN}2.${NC} Create key: https://apps.voc.ai/openapi/keys?utm_source=skill&utm_medium=onboarding&utm_campaign=launch_apr" >&2
    echo -e "  ${CYAN}3.${NC} Set it:     export VOC_API_KEY=your-key" >&2
    echo "" >&2
    echo "  New accounts include starter credits (8 reviews = 5 credits)." >&2
    echo "" >&2
    missing=1
  fi

  if [[ $missing -eq 1 ]]; then
    exit 1
  fi
}

print_banner
check_deps

# Map market display name
MARKET_UPPER=$(echo "$MARKET" | tr '[:lower:]' '[:upper:]')
echo -e "${GREEN}Analyzing ASIN: ${YELLOW}$ASIN${NC}"
echo -e "  Market: $MARKET_UPPER | Reviews: $LIMIT"
echo ""

# ── Step 1: Fetch reviews via Shulex API ─────────────────────
TEMP_DATA=$(mktemp /tmp/voc_data_XXXXXX.json)
TEMP_REVIEWS=$(mktemp /tmp/voc_reviews_XXXXXX.json)
trap "rm -f $TEMP_DATA $TEMP_REVIEWS" EXIT

echo -e "${BLUE}[1/2] Fetching review data via Shulex VOC API...${NC}"
bash "$SKILL_DIR/fetch.sh" "$ASIN" \
  --limit "$LIMIT" \
  --market "$MARKET" \
  --output "$TEMP_DATA"

# Extract just the reviews array for analyze.sh
python3 -c "
import json, sys
with open('$TEMP_DATA') as f:
    data = json.load(f)
reviews = data.get('reviews', data if isinstance(data, list) else [])
json.dump(reviews, sys.stdout, ensure_ascii=False, indent=2)
" > "$TEMP_REVIEWS" 2>/dev/null

REVIEW_COUNT=$(python3 -c "import json; print(len(json.load(open('$TEMP_REVIEWS'))))" 2>/dev/null || echo "0")
TOTAL_AVAIL=$(python3 -c "import json; print(json.load(open('$TEMP_DATA')).get('meta',{}).get('total_available',0))" 2>/dev/null || echo "?")

if [[ "$REVIEW_COUNT" -eq 0 ]]; then
  echo -e "${RED}No reviews retrieved. Check:${NC}" >&2
  echo "   - Is the ASIN correct?" >&2
  echo "   - Does this product have reviews?" >&2
  echo "   - Is your API key valid? Check: https://apps.voc.ai/openapi/keys?utm_source=skill&utm_medium=onboarding&utm_campaign=launch_apr" >&2
  exit 1
fi

echo -e "${GREEN}Retrieved $REVIEW_COUNT reviews (total available: $TOTAL_AVAIL)${NC}"
echo ""

# ── Step 2: AI analysis ──────────────────────────────────────
echo -e "${BLUE}[2/2] AI deep analysis...${NC}"

if [[ -n "$OUTPUT_FILE" ]]; then
  bash "$SKILL_DIR/analyze.sh" "$TEMP_REVIEWS" "$ASIN" --output "$OUTPUT_FILE"
else
  bash "$SKILL_DIR/analyze.sh" "$TEMP_REVIEWS" "$ASIN"
fi

echo ""
echo -e "${GREEN}Analysis complete!${NC}"

# ── Upgrade prompt (show when using default 8 reviews) ────────
if [[ "$LIMIT" -le 8 && "$TOTAL_AVAIL" != "?" ]]; then
  TOTAL_NUM=$(echo "$TOTAL_AVAIL" | tr -d '[:space:]')
  if [[ "$TOTAL_NUM" -gt 8 ]] 2>/dev/null; then
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  This report analyzed ${YELLOW}$REVIEW_COUNT${NC} of ${YELLOW}$TOTAL_AVAIL${NC} available reviews."
    echo -e "  For deeper insights, increase your limit:"
    echo ""
    echo -e "    ${GREEN}voc.sh $ASIN --limit 100${NC}"
    echo ""
    echo -e "  Need more credits? ${CYAN}https://apps.voc.ai/openapi/billing?utm_source=skill&utm_medium=report_cta&utm_campaign=launch_apr${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  fi
fi
