#!/bin/bash
# distill.sh — Self-improvement 模式检测扫描器
# v4.6.2 — 纯机械：扫描 + 计数 + notification_state + raw entry 输出
# 新增（v4.6.2）：notified / notification_count 字段读取，notification_trigger 计算
# 新增（v4.6.2）：meta.explanation 修正 scan_mode 描述
# 设计原则：「脚本做机械，AI 做语义」
#
# Canonical Source: ~/.openclaw/workspace/skills/self-improvement-loop/scripts/distill.sh
#
# Modes:
#   (no args)      — Full report, writes text to /tmp/distill-report-YYYYMMDD.txt
#   --check-only   — Fast JSON to stdout (for Cron heartbeat check)

WORKSPACE="${HOME}/.openclaw/workspace"
# Per-agent support: default to cwd/.learnings (automatically routes to agent's own dir)
# Can override via --learnings-dir flag or LEARNINGS_DIR env var
LEARNINGS_DIR="${LEARNINGS_DIR:-$(pwd)/.learnings}"
THRESHOLD=2
CHECK_ONLY=false

[ "$1" = "--check-only" ] && CHECK_ONLY=true


# ─────────────────────────────────────────────────────────────
# json_escape — Python json.dumps 替代脆弱 sed 转义
# ─────────────────────────────────────────────────────────────
json_escape() {
    printf '%s' "$1" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'
}

# ─────────────────────────────────────────────────────────────
# extract_notified_state — 从 raw_md 提取 Notified 和 Notification-Count
#   返回格式：notified_int|notification_count_int
#   notified: 1=true, 0=false, -1=字段不存在
# ─────────────────────────────────────────────────────────────
extract_notified_state() {
    local raw="$1"
    # Notified: true / false
    local notified_val
    notified_val=$(echo "$raw" | grep -i "[[:space:]]*-[[:space:]]*Notified:" | sed 's/.*:[[:space:]]*//' | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
    # Notification-Count: N
    local nc_val
    nc_val=$(echo "$raw" | grep -i "[[:space:]]*-[[:space:]]*Notification-Count:" | sed 's/.*:[[:space:]]*//' | tr -d '[:space:]')

    case "$notified_val" in
        true)  notified_int=1 ;;
        false) notified_int=0 ;;
        *)     notified_int=-1 ;;
    esac

    case "$nc_val" in
        [0-9]*) nc_int=$nc_val ;;
        *)      nc_int=0 ;;
    esac

    printf '%d|%d' "$notified_int" "$nc_int"
}

# ─────────────────────────────────────────────────────────────
# scan_file — 纯机械：遍历单个 MD 文件，输出 raw entry 行
#   v4.6.2 格式：entry_id|Pattern-Key|category|status|notified|notification_count|raw_md(JSON-escaped)
#   只输出 pending 桶（pending/active/in_progress），过滤 resolved/promoted
# ─────────────────────────────────────────────────────────────
scan_file() {
    local file="$1"
    [ ! -f "$file" ] && return

    local in_entry=false
    local entry_id="" id_short="" pk="" cat="" status="" entry_lines=""

    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            "## ["*)
                # emit previous entry
                if $in_entry && [ -n "$entry_id" ]; then
                    # Status bucket check — only emit pending entries
                    case "$status" in
                        pending|active|in_progress|"") : ;;
                        *)
                            in_entry=false
                            entry_id=""
                            continue
                            ;;
                    esac
                    # v4.6.2: extract notified state from entry_lines
                    local not_state notified_int nc_int
                    not_state=$(extract_notified_state "$entry_lines")
                    notified_int=$(echo "$not_state" | cut -d'|' -f1)
                    nc_int=$(echo "$not_state" | cut -d'|' -f2)
                    local raw_escaped
                    raw_escaped=$(json_escape "$entry_lines")
                    local sf
                    sf=$(basename "$file")
                    printf '%s|%s|%s|%s|%d|%d|%s|%s\n' \
                        "$id_short" "$pk" "$cat" "$status" "$notified_int" "$nc_int" "$raw_escaped" "$sf"
                fi
                # start new entry
                in_entry=true
                entry_id="$line"
                id_short=$(echo "$line" | sed -n 's/^## \[//;s/\].*//p')
                cat=$(echo "$line" | sed 's/^## \[[^ ]*] //' | tr -d '[:space:]')
                [ -z "$cat" ] && cat="uncategorized"
                pk=""
                status=""
                entry_lines="$line"$'\n'
                ;;
            *)
                if $in_entry; then
                    entry_lines="$entry_lines$line"$'\n'
                    case "$line" in
                        *"- Pattern-Key:"*|*"**Pattern-Key**:"*)
                            pk=$(echo "$line" | sed 's/^[^:]*: *//' | sed 's/^\*\*Pattern-Key\*\*: *//' | tr -d '[:space:]')
                            # Pattern-Key format validation (v4.6.2): must be X.Y.Z
                            if [ -n "$pk" ]; then
                                dot_count=$(echo "$pk" | tr -cd '.' | wc -c)
                                if [ "$dot_count" -ne 2 ]; then
                                    # Not 3-part format — downgrade to category-only
                                    pk=""
                                fi
                            fi
                            ;;
                        *)
                            # **Status**: value (两颗星 markdown 格式)
                            if echo "$line" | grep -qi 'status.*resolved\|status.*promoted\|status.*active\|status.*pending\|status.*in_progress'; then
                                status=$(echo "$line" | sed 's/\*\*/./g; s/.*://' | sed 's/|.*//' | \
                                    tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
                            fi
                            ;;
                    esac
                fi
                ;;
        esac
    done < "$file"

    # flush last entry
    if $in_entry && [ -n "$entry_id" ]; then
        case "$status" in
            pending|active|in_progress|"")
                local not_state notified_int nc_int
                not_state=$(extract_notified_state "$entry_lines")
                notified_int=$(echo "$not_state" | cut -d'|' -f1)
                nc_int=$(echo "$not_state" | cut -d'|' -f2)
                local raw_escaped
                raw_escaped=$(json_escape "$entry_lines")
                local sf
                sf=$(basename "$file")
                printf '%s|%s|%s|%s|%d|%d|%s|%s\n' \
                    "$id_short" "$pk" "$cat" "$status" "$notified_int" "$nc_int" "$raw_escaped" "$sf"
                ;;
        esac
    fi
}

# ═══════════════════════════════════════════════════════════════
# CHECK-ONLY MODE — v4.6.2 JSON output
# v4.6.2 新增：notified / notification_count / notification_trigger 字段
# ═══════════════════════════════════════════════════════════════
if [ "$CHECK_ONLY" = true ]; then

    # ── Step 1: 收集所有 pending entries ──────────────────
    # v4.6.2: 6字段输出（新增 notified_int, nc_int）
    ALL_ENTRIES=$(mktemp)
    for file in \
        "$LEARNINGS_DIR/LEARNINGS.md" \
        "$LEARNINGS_DIR/ERRORS.md" \
        "$LEARNINGS_DIR/FEATURE_REQUESTS.md"; do
        [ -f "$file" ] && scan_file "$file" >> "$ALL_ENTRIES"
    done
    [ ! -s "$ALL_ENTRIES" ] && > "$ALL_ENTRIES"

    # ── Step 2: 分离 Pattern-Key entries vs Category-only entries ──
    PK_ENTRIES=$(mktemp)
    CAT_ENTRIES=$(mktemp)
    # v4.6.2: 解析7字段（id|pk|cat|status|notified|nc|raw）
    while IFS='|' read -r id pk cat status notified nc raw; do
        # Invalid PK values → treat as category-only
        case "$pk" in
            ""|null|-|"<"*) echo "$id|$pk|$cat|$status|$notified|$nc|$raw" >> "$CAT_ENTRIES" ;;
            *)               echo "$id|$pk|$cat|$status|$notified|$nc|$raw" >> "$PK_ENTRIES" ;;
        esac
    done < "$ALL_ENTRIES"

    # ── Step 3: 聚合 PK entries（携带 notified 状态）──────
    # v4.6.2: 聚合规则：
    #   - notified: ANY entry 为 false → false（从未通知过）
    #   - notification_count: MIN across all entries（保守取最小值）
    #   - notification_trigger = (count >= 2) AND (notified == false OR nc < count)
    PK_AGG=$(mktemp)
    awk -F'|' '
    {
        pk=$2; id=$1; cat=$3; status=$4; notified=$5; nc=$6; raw=$7
        count[pk]++
        sfile=$8
        if (count[pk] == 1) {
            first_id[pk]=id; first_cat[pk]=cat
            first_status[pk]=status; first_raw[pk]=raw
            first_sfile[pk]=sfile
            # v4.6.2: notified state tracking
            # notified=false (−1特殊处理) → 聚合为false；notified=true → 只要有true就是true
            # 逻辑：任意entry为0（false）→ any_notified[pk]=0；否则取最大值
            if (notified + 0 == 0) {
                any_notified[pk]=0
            } else if (!(pk in any_notified)) {
                any_notified[pk]=notified
            } else {
                any_notified[pk]=any_notified[pk]
            }
            min_nc[pk]=nc
        } else {
            # Update notified: any false → false
            if (notified + 0 == 0) {
                any_notified[pk]=0
            }
            # Update min notification_count
            if (nc + 0 < min_nc[pk] + 0) {
                min_nc[pk]=nc
            }
        }
    }
    END {
        for (pk in count) {
            if (count[pk] > 0) {
                notified_val = (pk in any_notified) ? any_notified[pk] : -1
                nc_val = (pk in min_nc) ? min_nc[pk] : 0
                printf "%s|%d|%s|%s|%s|%d|%s|%d|%s\n", pk, count[pk], first_id[pk], first_cat[pk], first_status[pk], notified_val, first_raw[pk], nc_val, first_sfile[pk]
            }
        }
    }' "$PK_ENTRIES" > "$PK_AGG"

    # ── Step 4: 聚合 Category entries（携带 notified 状态）──
    CAT_AGG=$(mktemp)
    awk -F'|' '
    {
        cat=$3; id=$1; status=$4; notified=$5; nc=$6; raw=$7
        count[cat]++
        sfile=$8
        if (count[cat] == 1) {
            first_id[cat]=id; first_status[cat]=status; first_raw[cat]=raw
            first_sfile[cat]=sfile
            if (notified + 0 == 0) {
                any_notified[cat]=0
            } else if (!(cat in any_notified)) {
                any_notified[cat]=notified
            }
            min_nc[cat]=nc
        } else {
            if (notified + 0 == 0) {
                any_notified[cat]=0
            }
            if (nc + 0 < min_nc[cat] + 0) {
                min_nc[cat]=nc
            }
        }
    }
    END {
        for (cat in count) {
            if (count[cat] > 0) {
                notified_val = (cat in any_notified) ? any_notified[cat] : -1
                nc_val = (cat in min_nc) ? min_nc[cat] : 0
                printf "%s|%d|%s|%s|%d|%s|%d|%s\n", cat, count[cat], first_id[cat], first_status[cat], notified_val, first_raw[cat], nc_val, first_sfile[cat]
            }
        }
    }' "$CAT_ENTRIES" > "$CAT_AGG"

    # ── Step 5: 构建 JSON（v4.6.2 — 调用 Python 脚本）──────────
    DISTILL_JSON="$WORKSPACE/skills/self-improvement-loop/scripts/distill_json.py"
    python3 "$DISTILL_JSON" "$PK_AGG" "$CAT_AGG" "$THRESHOLD"

    rm -f "$ALL_ENTRIES" "$PK_ENTRIES" "$CAT_ENTRIES" "$PK_AGG" "$CAT_AGG"
    exit 0
fi


# ═══════════════════════════════════════════════════════════════
# FULL REPORT MODE — v4.6.2 (按需手动调用)
# ═══════════════════════════════════════════════════════════════
OUTPUT_FILE="/tmp/distill-report-$(date +%Y%m%d).txt"

echo "=== Self-Improvement Distillation Report ===" > "$OUTPUT_FILE"
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S %Z')" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "## Pattern Detection Snapshot (--check-only)" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
bash "$WORKSPACE/skills/self-improvement-loop/scripts/distill.sh" --check-only >> "$OUTPUT_FILE" 2>/dev/null || \
    echo "(scan failed)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "Report saved to: $OUTPUT_FILE"
cat "$OUTPUT_FILE"
exit 0
