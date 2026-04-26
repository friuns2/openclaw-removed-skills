#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PANGOLINFO="$SCRIPT_DIR/pangolinfo.py"

if python3 --version >/dev/null 2>&1; then
  PYTHON="python3"
else
  PYTHON="python"
fi

PASS=0
FAIL=0

run_test() {
  local name="$1"
  shift
  echo -n "  [$name] "
  if "$@"; then
    echo "PASS"
    PASS=$((PASS + 1))
  else
    echo "FAIL (exit code $?)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Pangolinfo Amazon Scraper Self-Test ==="

# --- Auth tests (free) ---
echo "Auth tests:"
run_test "auth-check" $PYTHON "$PANGOLINFO" --auth-only

# --- Input validation tests (free, no API calls) ---
echo "Input validation tests:"

run_test "missing-input" bash -c "! $PYTHON \"$PANGOLINFO\" --mode amazon 2>/dev/null"
run_test "invalid-pages" bash -c "! $PYTHON \"$PANGOLINFO\" --content B0TEST12345 --mode review --pages 0 2>/dev/null"
run_test "invalid-site" bash -c "! $PYTHON \"$PANGOLINFO\" --content test --site amz_zz 2>/dev/null"
run_test "invalid-parser" bash -c "! $PYTHON \"$PANGOLINFO\" --content test --parser badParser 2>/dev/null"
run_test "invalid-format" bash -c "! $PYTHON \"$PANGOLINFO\" --content test --format xml 2>/dev/null"

# --- ASIN detection test (free, no API call) ---
echo "ASIN normalization tests:"
run_test "asin-uppercase" bash -c "$PYTHON -c \"
import sys; sys.path.insert(0, '$SCRIPT_DIR')
from pangolinfo import normalize_asin, is_asin
assert is_asin('B0DYTF8L2W'), 'Should detect ASIN'
assert normalize_asin('b0dytf8l2w') == 'B0DYTF8L2W', 'Should uppercase'
assert not is_asin('A1B2C3D4E5'), 'Seller ID should NOT be detected as ASIN'
assert not is_asin('1234567890'), 'Node ID should NOT be detected as ASIN'
print('All assertions passed')
\""

# --- Live API tests (cost credits) ---
if [ "${RUN_LIVE_TESTS:-0}" = "1" ]; then
  echo "Live API tests (credits will be consumed):"

  run_test "keyword-search" bash -c "$PYTHON \"$PANGOLINFO\" --q 'wireless mouse' --site amz_us 2>/dev/null | $PYTHON -c \"import sys,json; d=json.load(sys.stdin); assert d['success']==True; print(f'Got {d.get(\\\"results_count\\\",0)} results')\""

  run_test "asin-lookup" bash -c "$PYTHON \"$PANGOLINFO\" --asin B0DYTF8L2W --site amz_us 2>/dev/null | $PYTHON -c \"import sys,json; d=json.load(sys.stdin); assert d['success']==True\""
else
  echo "Live API tests: SKIPPED (set RUN_LIVE_TESTS=1 to enable -- consumes credits)"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] || exit 1
