#!/bin/bash
# rocky-know-how Tag 晋升机制 v3.3.0
# 用法: promote.sh
# 检查 7 天内同一 Tag 出现 ≥3 次，自动晋升到 HOT (memory.md)
# 环境变量: WORKSPACE, STATE_DIR (由 record.sh 传入)

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SKILL_DIR/lib/common.sh"
STATE_DIR=$(get_state_dir)
SHARED_DIR=$(get_shared_dir)
ERRORS_FILE="$SHARED_DIR/experiences.md"
CORRECTIONS_FILE="$SHARED_DIR/corrections.md"
MEMORY_FILE="$SHARED_DIR/memory.md"
TOOLS_FILE="${WORKSPACE:-$(echo "$STATE_DIR/workspace")}/TOOLS.md"

# R4 fix: 获取晋升锁
LOCK_DIR="$(get_lock_dir promote)"
acquire_lock "$LOCK_DIR" 2>/dev/null
# promote 可异步运行，锁失败不阻塞，仅警告
PROMOTE_LOCKED=$?

# 合并清理：锁释放 + 旧临时文件
cleanup_promote() {
  [ $PROMOTE_LOCKED -eq 0 ] && release_lock "$LOCK_DIR"
  rm -f "/tmp/rocky-know-how-tags-$$.txt" "/tmp/rocky-know-how-corr-$$.txt"
}
trap 'cleanup_promote' EXIT

# v2.0: 7天检查周期（之前是30天）
CUTOFF_DATE=$(date -v-7d +%Y%m%d 2>/dev/null || date -d "7 days ago" +%Y%m%d)
TODAY=$(date +%Y%m%d)

[ ! -f "$ERRORS_FILE" ] && echo "经验诀窍文件不存在，跳过晋升检查" && exit 0

echo "=== Tag 晋升检查 (v3.3.0) ==="
echo "检查周期: ${CUTOFF_DATE} - ${TODAY} (7天窗口)"
echo "目标 HOT: $MEMORY_FILE"
echo ""

# 初始化 memory.md
if [ ! -f "$MEMORY_FILE" ]; then
  printf "# HOT Memory\n\n## 已确认偏好\n\n## 活跃模式\n\n## 最近（最近7天）\n\n" > "$MEMORY_FILE"
fi

# 清理旧临时文件（由 trap EXIT 统一清理）

# ============ 阶段1: Tag 晋升到 HOT (7天内 ≥3次) ============
echo "─── Tag 晋升检查 ───"

TAGS_DATA=$(awk -v cutoff="$CUTOFF_DATE" '
  /^## \[EXP-/ {
    date = substr($0, index($0, "[EXP-") + 5, 8)
    if (date >= cutoff) {
      while (getline > 0) {
        if (/^\*\*Tags\*\*:/) {
          sub(/^\*\*Tags\*\*: /, "")
          print
          break
        }
        if (/^## \[EXP-/) break
      }
    }
  }
' "$ERRORS_FILE")

if [ -z "$TAGS_DATA" ]; then
  echo "无 Tag 达到晋升标准（7天内无条目）"
else
  echo "近期 Tags 统计 (7天窗口):"
  echo "$TAGS_DATA" | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -v '^$' | sort | uniq -c | sort -rn

  TAG_COUNT_FILE="/tmp/rocky-know-how-tags-$$.txt"
  echo "$TAGS_DATA" | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -v '^$' | sort | uniq -c | sort -rn > "$TAG_COUNT_FILE"

  promoted=0
  while read -r count tag; do
    [ -z "$count" ] && continue
    tag=$(echo "$tag" | sed 's/^ *//;s/ *$//')
    [ -z "$tag" ] && continue
    if [ "$count" -ge 3 ]; then
      echo "🎯 晋升 Tag: $tag (出现 $count 次，≥3次阈值)"

      # 提取该 Tag 最近一条的"正确方案"（完整段落，支持多行）
      # P1 fix: 用 ,${tag}, 精确匹配 tag（避免 cssh 匹配到 ssh），用 awk 取完整段落
      solution=$(awk -v pat=",${tag}," '
        BEGIN { found=0 }
        /^## \[EXP-/ { in_exp=1 }
        /^## / && !/^## \[EXP-/ { in_exp=0 }
        /\*\*Tags\*\*/ && in_exp && index($0, pat) > 0 {
          # 找到了匹配的 Tags，记录当前 entry，切换到等待 solution 状态
          entry_match=1; found=1; next
        }
        # 进入新的 entry（EXP 开头）时，如果还没找到 solution，重置
        /^## \[EXP-/ && entry_match && found==1 { exit }
        found == 1 && index($0, "正确方案") > 0 {
          found=2; entry_match=0; next
        }
        found == 2 { if (/^### / || /^---/) exit; printf "%s%s", (NR==1?"":"\n"), $0 }
      ' "$ERRORS_FILE" 2>/dev/null)

      if [ -n "$solution" ]; then
        # 检查是否已在 memory.md
        if grep -qF --color=never "$tag" "$MEMORY_FILE" 2>/dev/null; then
          echo "   已存在于 memory.md，跳过"
        else
          # 添加到 memory.md
          MEMORY_ENTRY="
## $(date '+%Y-%m-%d') [晋升: $tag ×$count]
- **Tag:** $tag (7天内出现 $count 次)
- **方案:** $solution
- **来源:** 经验诀窍自动晋升
"
          echo "$MEMORY_ENTRY" >> "$MEMORY_FILE"
          echo "✅ 已晋升到 memory.md (HOT)"
          promoted=$((promoted+1))
        fi
      fi

      # 同时写入 TOOLS.md（保持 v1 兼容）
      if [ -f "$TOOLS_FILE" ]; then
        if ! grep -q --color=never "$tag.*经验诀窍" "$TOOLS_FILE" 2>/dev/null; then
          echo "" >> "$TOOLS_FILE"
          echo "### $tag" >> "$TOOLS_FILE"
          echo "" >> "$TOOLS_FILE"
          echo "- $solution (来源: 经验诀窍, ${count}次实战, 自动晋升)" >> "$TOOLS_FILE"
          echo "  - 自动晋升日期: $(date '+%Y-%m-%d')" >> "$TOOLS_FILE"
          echo "✅ 已写入 TOOLS.md"
        fi
      fi
    fi
  done < "$TAG_COUNT_FILE"

  [ $promoted -eq 0 ] && echo "无 Tag 达到晋升标准（需 ≥3 次，7天窗口）"
  rm -f "$TAG_COUNT_FILE"
fi

# ============ 阶段2: corrections.md 晋升检查 (3x → memory.md) ============
echo ""
echo "─── 纠正日志晋升检查 ───"

if [ -f "$CORRECTIONS_FILE" ]; then
  # 统计 corrections 中各 Pattern 出现次数（单次 grep + sort | uniq -c，O(n)）
  CORR_PATTERN_FILE="/tmp/rocky-know-how-corr-$$.txt"

  # 提取 corrections 中所有纠正模式，一次性统计
  grep -E "^\- \*\*纠正:\*\*" "$CORRECTIONS_FILE" 2>/dev/null \
    | sed 's/^- \*\*纠正:\*\* *//' \
    | sort | uniq -c | sort -rn \
    | while read -r count pattern; do
        [ -z "$pattern" ] && continue
        echo "$count | $pattern"
      done > "$CORR_PATTERN_FILE"

  corr_promoted=0
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    count=$(echo "$line" | cut -d'|' -f1 | sed 's/^ *//')
    pattern=$(echo "$line" | cut -d'|' -f2- | sed 's/^ *//')
    [ -z "$pattern" ] && continue

    if [ "$count" -ge 3 ] 2>/dev/null; then
      # 询问确认（自动模式静默跳过）
      if grep -q --color=never "$pattern" "$MEMORY_FILE" 2>/dev/null; then
        continue
      fi

      echo "🎯 corrections 晋升: $pattern (出现 $count 次)"
      MEMORY_ENTRY="
## $(date '+%Y-%m-%d') [纠正晋升 ×$count]
- **Pattern:** $pattern
- **Count:** $count 次纠正
- **Action:** 晋升为确认偏好
"
      echo "$MEMORY_ENTRY" >> "$MEMORY_FILE"
      echo "✅ 已晋升到 memory.md"
      corr_promoted=$((corr_promoted+1))
    fi
  done < "$CORR_PATTERN_FILE"

  rm -f "$CORR_PATTERN_FILE"
fi

echo ""
echo "检查完成"
echo "💡 新规则: Tag 7天内 ≥3次 → 晋升 HOT (之前是30天)"
