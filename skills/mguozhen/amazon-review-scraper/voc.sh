#!/usr/bin/env bash
# Amazon Review Intelligence — main entry point
# Usage: voc.sh <ASIN> [--limit N] [--market amazon.com] [--lang en|zh] [--stars 1-5] [--output report.md]

set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Colors ─────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

banner() {
echo -e "${BLUE}${BOLD}"
cat <<'EOF'
  ██████╗ ███████╗██╗   ██╗██╗███████╗██╗    ██╗
  ██╔══██╗██╔════╝██║   ██║██║██╔════╝██║    ██║
  ██████╔╝█████╗  ██║   ██║██║█████╗  ██║ █╗ ██║
  ██╔══██╗██╔══╝  ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║
  ██║  ██║███████╗ ╚████╔╝ ██║███████╗╚███╔███╔╝
  ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝
EOF
echo -e "${NC}  Amazon Review Intelligence  ·  mguozhen/amazon-review-scraper"
echo -e "  ─────────────────────────────────────────────────────────────\n"
}

usage() {
  echo "Usage: voc.sh <ASIN> [options]"
  echo ""
  echo "Options:"
  echo "  --limit N        Reviews to fetch (default: 8, free tier)"
  echo "  --token TOKEN    VOC.AI API token (or set VOC_TOKEN env var)"
  echo "  --lang en|zh     Report language (default: en)"
  echo "  --output FILE    Save report to file"
  echo "  --scrape-only    Only fetch reviews, skip AI analysis"
  echo "  --analyze FILE   Analyze existing JSON file"
  echo "  --help           Show this help"
  echo ""
  echo "Examples:"
  echo "  voc.sh B08N5WRWNW"
  echo "  voc.sh B08N5WRWNW --lang zh"
  echo "  voc.sh B08N5WRWNW --token YOUR_TOKEN --limit 50 --output report.md"
  echo "  voc.sh --analyze reviews.json --asin B08N5WRWNW"
  echo ""
  echo "API Token:"
  echo "  Get free token at https://voc.ai/pricing"
  echo "  Default: 8 reviews (free). More requires Team/Enterprise plan."
  exit 0
}

# ── Parse args ─────────────────────────────────────────────────────────────────
ASIN=""; LIMIT=8; MARKET="amazon.com"; LANG="en"
OUTPUT=""; SCRAPE_ONLY=0; ANALYZE_FILE=""
TOKEN="${VOC_TOKEN:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) usage ;;
    --limit)   LIMIT="$2"; shift 2 ;;
    --market)  MARKET="$2"; shift 2 ;;
    --token)   TOKEN="$2"; shift 2 ;;
    --lang)    LANG="$2"; shift 2 ;;
    --output)  OUTPUT="$2"; shift 2 ;;
    --scrape-only) SCRAPE_ONLY=1; shift ;;
    --analyze) ANALYZE_FILE="$2"; shift 2 ;;
    -*) echo -e "${RED}Unknown option: $1${NC}"; usage ;;
    *)  ASIN="$1"; shift ;;
  esac
done

banner

# ── Analyze existing file ──────────────────────────────────────────────────────
if [[ -n "$ANALYZE_FILE" ]]; then
  ASIN_ARG=""
  [[ -n "$ASIN" ]] && ASIN_ARG="--asin $ASIN"
  LANG_ARG="--lang $LANG"
  OUTPUT_ARG=""
  [[ -n "$OUTPUT" ]] && OUTPUT_ARG="--output $OUTPUT"
  python3 "$SKILL_DIR/analyze.py" "$ANALYZE_FILE" $ASIN_ARG $LANG_ARG $OUTPUT_ARG
  exit 0
fi

# ── Validate ASIN ──────────────────────────────────────────────────────────────
if [[ -z "$ASIN" ]]; then
  echo -e "${RED}❌ ASIN required${NC}"; usage
fi

if ! echo "$ASIN" | grep -qE '^[A-Z0-9]{10}$'; then
  echo -e "${YELLOW}⚠️  ASIN format warning (expected 10 alphanumeric chars like B08N5WRWNW)${NC}"
fi

# ── Check deps ─────────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}❌ python3 not found${NC}"; exit 1
fi
if [[ $SCRAPE_ONLY -eq 0 ]] && ! command -v claude &>/dev/null; then
  echo -e "${YELLOW}⚠️  claude CLI not found — will scrape only (install Claude Code CLI for AI analysis)${NC}"
  SCRAPE_ONLY=1
fi

# ── Step 1: Scrape ─────────────────────────────────────────────────────────────
TEMP_JSON=$(mktemp /tmp/amazon_reviews_XXXXXX.json)
trap "rm -f $TEMP_JSON" EXIT

echo -e "${BLUE}[1/2] Scraping reviews...${NC}"

SCRAPE_ARGS="$ASIN --limit $LIMIT"
[[ -n "$TOKEN" ]] && SCRAPE_ARGS="$SCRAPE_ARGS --token $TOKEN"

if [[ -n "$OUTPUT" && $SCRAPE_ONLY -eq 1 ]]; then
  python3 "$SKILL_DIR/scraper.py" $SCRAPE_ARGS --output "$OUTPUT"
else
  python3 "$SKILL_DIR/scraper.py" $SCRAPE_ARGS --output "$TEMP_JSON"
fi

COUNT=$(python3 -c "import json; print(len(json.load(open('$TEMP_JSON'))))" 2>/dev/null || echo "0")

if [[ "$COUNT" -eq 0 ]]; then
  echo -e "${RED}❌ No reviews collected. Amazon may be blocking requests.${NC}"
  echo -e "   Try again in a few minutes, or use a different network."
  exit 1
fi

echo -e "${GREEN}✓ Collected $COUNT reviews${NC}\n"

[[ $SCRAPE_ONLY -eq 1 ]] && exit 0

# ── Step 2: Analyze ────────────────────────────────────────────────────────────
echo -e "${BLUE}[2/2] AI analysis (Claude)...${NC}"

ANALYZE_ARGS="$TEMP_JSON --asin $ASIN --market $MARKET --lang $LANG"
[[ -n "$OUTPUT" ]] && ANALYZE_ARGS="$ANALYZE_ARGS --output $OUTPUT"

python3 "$SKILL_DIR/analyze.py" $ANALYZE_ARGS

echo -e "\n${GREEN}${BOLD}✅ Done!${NC}"
[[ -n "$OUTPUT" ]] && echo -e "   Report saved to: ${YELLOW}$OUTPUT${NC}"
