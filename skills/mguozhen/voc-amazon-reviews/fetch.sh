#!/usr/bin/env bash
# Fetch Amazon reviews via Shulex VOC OpenAPI (Realtime Task)
# Usage: fetch.sh <ASIN> [--limit N] [--market US] [--output file.json]

set -euo pipefail

ASIN="${1:-}"
LIMIT=8
MARKET="US"
OUTPUT_FILE=""

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit) LIMIT="$2"; shift 2 ;;
    --market) MARKET="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$ASIN" ]]; then
  echo "Usage: fetch.sh <ASIN> [--limit N] [--market US]" >&2
  exit 1
fi

# ── Dependencies ──────────────────────────────────────────────
if ! command -v curl &>/dev/null; then
  echo "curl is required" >&2; exit 1
fi
if ! command -v python3 &>/dev/null; then
  echo "python3 is required" >&2; exit 1
fi

# ── API Key ───────────────────────────────────────────────────
API_BASE="https://openapi.shulex.com"
API_KEY="${VOC_API_KEY:-}"

if [[ -z "$API_KEY" ]]; then
  cat >&2 <<'MSG'

  ╔══════════════════════════════════════════════════════════╗
  ║  VOC_API_KEY not set — free registration to get started ║
  ╚══════════════════════════════════════════════════════════╝

  1. Register (free):  https://apps.voc.ai/openapi?utm_source=skill&utm_medium=onboarding&utm_campaign=launch_apr
  2. Create API key:   https://apps.voc.ai/openapi/keys?utm_source=skill&utm_medium=onboarding&utm_campaign=launch_apr
  3. Buy credits:      https://apps.voc.ai/openapi/billing?utm_source=skill&utm_medium=onboarding&utm_campaign=launch_apr
  4. Set your key:     export VOC_API_KEY=your-key

  New accounts include starter credits — enough for 8+ reviews.

MSG
  exit 1
fi

# ── Market code mapping (domain → code) ──────────────────────
case "$MARKET" in
  amazon.com|us|Us)       MARKET="US" ;;
  amazon.ca|ca|Ca)        MARKET="CA" ;;
  amazon.com.mx|mx|Mx)    MARKET="MX" ;;
  amazon.co.uk|gb|Gb|uk)  MARKET="GB" ;;
  amazon.de|de|De)        MARKET="DE" ;;
  amazon.fr|fr|Fr)        MARKET="FR" ;;
  amazon.it|it|It)        MARKET="IT" ;;
  amazon.es|es|Es)        MARKET="ES" ;;
  amazon.co.jp|jp|Jp)     MARKET="JP" ;;
  amazon.com.au|au|Au)    MARKET="AU" ;;
  US|CA|MX|GB|DE|FR|IT|ES|JP|AU) ;; # already valid
  *)
    echo "Unsupported market: $MARKET" >&2
    echo "Supported: US CA MX GB DE FR IT ES JP AU" >&2
    exit 1
    ;;
esac

# ── Calculate maxPage ─────────────────────────────────────────
# Amazon shows ~10 reviews per page; cost = 5 credits x maxPage
MAX_PAGE=$(( (LIMIT + 9) / 10 ))
if [[ $MAX_PAGE -lt 1 ]]; then MAX_PAGE=1; fi
if [[ $MAX_PAGE -gt 100 ]]; then MAX_PAGE=100; fi

echo "Fetching reviews for ASIN: $ASIN (market: $MARKET, limit: $LIMIT)" >&2

# ── Step 1: Submit realtime review task ───────────────────────
echo "   Submitting review task..." >&2
SUBMIT_RESP=$(curl -s -X POST "$API_BASE/v1/api/RtTask01" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{\"asin\":\"$ASIN\",\"market\":\"$MARKET\",\"maxPage\":$MAX_PAGE,\"platform\":\"AMAZON\"}")

TASK_ID=$(echo "$SUBMIT_RESP" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('data',{}).get('taskId',''))
except: print('')
" 2>/dev/null)

CODE=$(echo "$SUBMIT_RESP" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin).get('code',''))
except: print('')
" 2>/dev/null)

if [[ -z "$TASK_ID" || "$CODE" != "0" ]]; then
  echo "Failed to submit task:" >&2
  echo "   $SUBMIT_RESP" >&2
  exit 1
fi

echo "   Task submitted: $TASK_ID" >&2

# ── Step 2: Poll until SUCCESS or FAILED ──────────────────────
echo "   Waiting for reviews..." >&2
MAX_WAIT=120
WAITED=0
STATUS="PENDING"
POLL_RESP=""

while [[ "$STATUS" != "SUCCESS" && "$STATUS" != "FAILED" && $WAITED -lt $MAX_WAIT ]]; do
  sleep 5
  WAITED=$((WAITED + 5))

  POLL_RESP=$(curl -s "$API_BASE/v1/api/RtQry01?taskId=$TASK_ID&pageNo=1&pageSize=$LIMIT" \
    -H "X-API-Key: $API_KEY")

  STATUS=$(echo "$POLL_RESP" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin).get('data',{}).get('status','UNKNOWN'))
except: print('UNKNOWN')
" 2>/dev/null)

  echo "   ... status: $STATUS (${WAITED}s)" >&2
done

if [[ "$STATUS" != "SUCCESS" ]]; then
  ERR_MSG=$(echo "$POLL_RESP" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin).get('data',{})
    print(d.get('errorMsg','') or d.get('message','unknown error'))
except: print('Task timed out')
" 2>/dev/null)
  echo "Task failed: $ERR_MSG" >&2
  exit 1
fi

# ── Step 3: Extract reviews ───────────────────────────────────
RESULT=$(echo "$POLL_RESP" | python3 -c "
import sys, json

resp = json.load(sys.stdin)
data = resp.get('data', {})
reviews = data.get('reviews', [])
total = data.get('total', 0)
limit = $LIMIT

# Normalize review format
normalized = []
for r in reviews[:limit]:
    normalized.append({
        'rating':    r.get('rating'),
        'title':     r.get('title', ''),
        'body':      r.get('body', '') or r.get('content', ''),
        'date':      r.get('reviewDate', ''),
        'verified':  bool(r.get('verified') or r.get('verifiedPurchase')),
        'variant':   r.get('variant', ''),
        'author':    r.get('author', '') or r.get('reviewerName', ''),
        'helpful':   r.get('helpfulVotes', 0),
        'reviewId':  r.get('reviewId', ''),
        'vineVoice': bool(r.get('isVineVoice')),
    })

output = {
    'reviews': normalized,
    'meta': {
        'asin': data.get('asin', ''),
        'market': data.get('market', ''),
        'total_available': total,
        'fetched': len(normalized),
    }
}
print(json.dumps(output, ensure_ascii=False, indent=2))
" 2>/dev/null)

REVIEW_COUNT=$(echo "$RESULT" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('reviews',[])))" 2>/dev/null || echo "0")
TOTAL_AVAIL=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('meta',{}).get('total_available',0))" 2>/dev/null || echo "0")

echo "   Retrieved $REVIEW_COUNT reviews (total available: $TOTAL_AVAIL)" >&2

if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$RESULT" > "$OUTPUT_FILE"
  echo "   Saved to: $OUTPUT_FILE" >&2
else
  echo "$RESULT"
fi
