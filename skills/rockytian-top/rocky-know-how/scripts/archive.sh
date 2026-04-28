#!/bin/bash
# rocky-know-how 归档旧条目 v3.3.0
# 用法: archive.sh [--days N] [--dry-run] [--auto]

DAYS=90
DRY_RUN=false
AUTO=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --days)    DAYS="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --auto)    AUTO=true; shift ;;
    -h|--help)
      echo "用法: archive.sh [--days N] [--dry-run] [--auto]"
      echo "  --days N    归档N天前的条目（默认90）"
      echo "  --dry-run   只预览不执行"
      echo "  --auto      自动模式（适合cron/heartbeat调用）"
      exit 0 ;;
    *) shift ;;
  esac
done

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPTS_DIR/lib/common.sh"
STATE_DIR=$(get_state_dir)
SHARED_DIR=$(get_shared_dir)
ERRORS_FILE="$SHARED_DIR/experiences.md"
ARCHIVE_DIR="$SHARED_DIR/archive"

# R4 fix: 获取归档锁
LOCK_DIR="$(get_lock_dir archive)"
if ! acquire_lock "$LOCK_DIR"; then
  echo "❌ 无法获取归档锁，请稍后重试"
  exit 1
fi
trap 'release_lock "$LOCK_DIR"' EXIT

[ ! -f "$ERRORS_FILE" ] && exit 0

ARCHIVE_MONTH_DIR="$ARCHIVE_DIR/$(date +%Y-%m)"
mkdir -p "$ARCHIVE_MONTH_DIR"

CUTOFF_DATE=$(date -v-${DAYS}d +%Y%m%d 2>/dev/null || date -d "${DAYS} days ago" +%Y%m%d)

extract_date() {
  echo "$1" | sed 's/.*\[EXP-\([0-9]\{8\}\)-.*/\1/'
}

is_old() {
  local d="$1"
  [ -z "$d" ] && return 1
  [ "$d" -lt "$CUTOFF_DATE" ] 2>/dev/null
}

# auto 模式：静默执行，只输出摘要
if $AUTO; then
  old_count=0
  while IFS= read -r line; do
    if echo "$line" | grep -q "^## \[EXP-"; then
      date=$(extract_date "$line")
      is_old "$date" && old_count=$((old_count+1))
    fi
  done < "$ERRORS_FILE"

  [ $old_count -eq 0 ] && exit 0

  BACKUP_FILE="$ARCHIVE_MONTH_DIR/experiences-$(date +%Y%m%d-%H%M%S).md"
  cp "$ERRORS_FILE" "$BACKUP_FILE"

  # P4 fix: 使用 mktemp 替代固定路径
  TEMP_FILE=$(mktemp /tmp/rocky-know-how.XXXXXX)
  {
    echo "# 经验诀窍"
    echo ""
    echo "---"
  } > "$TEMP_FILE"

  current_block=""
  in_old=false
  while IFS= read -r line; do
    if echo "$line" | grep -q "^## \[EXP-"; then
      if [ -n "$current_block" ] && ! $in_old; then
        echo "$current_block" >> "$TEMP_FILE"
      fi
      current_block="$line"
      date=$(extract_date "$line")
      in_old=false; is_old "$date" && in_old=true
    else
      current_block="${current_block}"$'\n'"${line}"
    fi
  done < "$ERRORS_FILE"

  if [ -n "$current_block" ] && ! $in_old; then
    echo "$current_block" >> "$TEMP_FILE"
  fi

  mv "$TEMP_FILE" "$ERRORS_FILE"
  echo "✅ [auto] 归档了 ${old_count} 条旧经验（>${DAYS}天），备份: $(basename "$BACKUP_FILE")"
  exit 0
fi

# 手动模式
if $DRY_RUN; then
  echo "=== 模拟归档 ==="
  echo "截止日期: ${CUTOFF_DATE:0:4}-${CUTOFF_DATE:4:2}-${CUTOFF_DATE:6:2}（${DAYS}天前）"
  echo ""
  echo "将被归档的条目:"
  in_block=0
  while IFS= read -r line; do
    if echo "$line" | grep -q "^## \[EXP-"; then
      date=$(extract_date "$line")
      if is_old "$date"; then
        echo "$line"
        in_block=1
      else
        in_block=0
      fi
    elif [ $in_block -eq 1 ]; then
      echo "$line"
      [ "$line" = "---" ] && in_block=0
    fi
  done < "$ERRORS_FILE"
  exit 0
fi

# 实际归档
BACKUP_FILE="$ARCHIVE_MONTH_DIR/experiences-$(date +%Y%m%d-%H%M%S).md"
cp "$ERRORS_FILE" "$BACKUP_FILE"

# P4 fix: 使用 mktemp 替代固定路径
TEMP_FILE=$(mktemp /tmp/rocky-know-how.XXXXXX)
{
  echo "# 经验诀窍"
  echo ""
  echo "---"
} > "$TEMP_FILE"

current_block=""
in_old=false
archived_count=0
while IFS= read -r line; do
  if echo "$line" | grep -q "^## \[EXP-"; then
    if [ -n "$current_block" ] && ! $in_old; then
      echo "$current_block" >> "$TEMP_FILE"
    else
      $in_old && archived_count=$((archived_count+1))
    fi
    current_block="$line"
    date=$(extract_date "$line")
    in_old=false; is_old "$date" && in_old=true
  else
    current_block="${current_block}"$'\n'"$line"
  fi
done < "$ERRORS_FILE"

if [ -n "$current_block" ] && ! $in_old; then
  echo "$current_block" >> "$TEMP_FILE"
elif $in_old; then
  archived_count=$((archived_count+1))
fi

mv "$TEMP_FILE" "$ERRORS_FILE"

echo "✅ 归档完成"
echo "   备份: $(basename "$BACKUP_FILE")"
echo "   已归档: ${archived_count} 条（>${DAYS}天）"
