#!/bin/bash
# rocky-know-how 降级检查脚本 v3.3.0
# 用法: demote.sh [--dry-run] [--days N]
# 检查未使用模式，降级到 WARM（30天）或归档到 COLD（90天）
# 永不删除数据

DRY_RUN=false
DAYS_THRESHOLD=30
ARCHIVE_THRESHOLD=90

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --days)    DAYS_THRESHOLD="$2"; shift 2 ;;
    -h|--help)
      echo "用法: demote.sh [--dry-run] [--days N]"
      echo "  --dry-run  模拟执行，不实际写入"
      echo "  --days N   降级阈值天数（默认30）"
      exit 0 ;;
    *) shift ;;
  esac
done

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPTS_DIR/lib/common.sh"
STATE_DIR=$(get_state_dir)
SHARED_DIR=$(get_shared_dir)
# R4 fix: 获取降级锁
LOCK_DIR="$(get_lock_dir demote)"
if ! acquire_lock "$LOCK_DIR"; then
  echo "❌ 无法获取降级锁，请稍后重试"
  exit 1
fi
trap 'release_lock "$LOCK_DIR"' EXIT
MEMORY_FILE="$SHARED_DIR/memory.md"
INDEX_FILE="$SHARED_DIR/index.md"
ARCHIVE_DIR="$SHARED_DIR/archive"
DOMAINS_DIR="$SHARED_DIR/domains"
PROJECTS_DIR="$SHARED_DIR/projects"

echo "=== 降级检查 (v3.3.0) ==="
echo "降级阈值: ${DAYS_THRESHOLD} 天"
echo "归档阈值: ${ARCHIVE_THRESHOLD} 天"
echo ""

[ ! -f "$MEMORY_FILE" ] && echo "memory.md 不存在，跳过" && exit 0

DEMOTE_MARKER="# DEMOTED"
CUTOFF_DATE=$(date -v-${DAYS_THRESHOLD}d +%Y-%m-%d 2>/dev/null || date -d "${DAYS_THRESHOLD} days ago" +%Y-%m-%d)
ARCHIVE_CUTOFF=$(date -v-${ARCHIVE_THRESHOLD}d +%Y-%m-%d 2>/dev/null || date -d "${ARCHIVE_THRESHOLD} days ago" +%Y-%m-%d)

echo "降级截止: ${CUTOFF_DATE}"
echo "归档截止: ${ARCHIVE_CUTOFF}"
echo ""

# 创建必要的目录
mkdir -p "$ARCHIVE_DIR"
mkdir -p "$DOMAINS_DIR"
mkdir -p "$PROJECTS_DIR"

# 获取所有条目及其日期
get_entries_with_dates() {
  local file="$1"
  awk -v cutoff="$CUTOFF_DATE" -v archive_cutoff="$ARCHIVE_CUTOFF" '
    BEGIN { entry_date=""; entry_content=""; in_entry=0 }
    
    /^## [0-9]{4}-[0-9]{2}-[0-9]{2}/ {
      # 保存前一个条目
      if (entry_content != "" && entry_date != "") {
        if (entry_date < archive_cutoff) {
          print "ARCHIVE|" entry_date "|" entry_content
        } else if (entry_date < cutoff) {
          print "DEMOTE|" entry_date "|" entry_content
        }
      }
      # 解析日期 (标准AWK方式)
      if (match($0, /## ([0-9]{4}-[0-9]{2}-[0-9]{2})/)) {
        entry_date = substr($0, RSTART+3, RLENGTH-3)
      }
      entry_content = $0
      in_entry = 1
      next
    }
    
    in_entry && /^## / {
      # 保存前一个条目
      if (entry_content != "" && entry_date != "") {
        if (entry_date < archive_cutoff) {
          print "ARCHIVE|" entry_date "|" entry_content
        } else if (entry_date < cutoff) {
          print "DEMOTE|" entry_date "|" entry_content
        }
      }
      entry_content = ""
      entry_date = ""
      in_entry = 0
      next
    }
    
    in_entry {
      entry_content = entry_content "\n" $0
    }
    
    END {
      # 处理最后一个条目
      if (entry_content != "" && entry_date != "") {
        if (entry_date < archive_cutoff) {
          print "ARCHIVE|" entry_date "|" entry_content
        } else if (entry_date < cutoff) {
          print "DEMOTE|" entry_date "|" entry_content
        }
      }
    }
  ' "$file"
}

# 备份文件
backup_file() {
  local file="$1"
  local backup="${file}.bak.$(date +%Y%m%d-%H%M%S)"
  cp "$file" "$backup"
  echo "  📦 备份: $backup"
}

# 更新 index.md
update_index() {
  local action="$1"  # "DEMOTE" or "ARCHIVE"
  local entry_title="$2"
  local target_file="$3"
  
  if [ ! -f "$INDEX_FILE" ]; then
    echo "# 索引" > "$INDEX_FILE"
    echo "" >> "$INDEX_FILE"
  fi
  
  # 添加索引条目
  local timestamp=$(date '+%Y-%m-%d %H:%M')
  echo "- $(date '+%Y-%m-%d') [$action] $entry_title → $target_file" >> "$INDEX_FILE"
}

# 处理条目
process_entries() {
  local demote_count=0
  local archive_count=0
  
  # 获取所有条目
  local entries_data=$(get_entries_with_dates "$MEMORY_FILE")
  
  if [ -z "$entries_data" ]; then
    echo "  无降级/归档候选"
    return
  fi
  
  # 分类处理
  local demote_entries=$(echo "$entries_data" | grep "^DEMOTE|")
  local archive_entries=$(echo "$entries_data" | grep "^ARCHIVE|")
  
  # 处理需要降级到 WARM 的条目
  if [ -n "$demote_entries" ]; then
    if ! $DRY_RUN; then
      backup_file "$MEMORY_FILE"
    fi
    echo "--- 需要降级到 WARM 的条目 ---"
    while IFS='|' read -r action date content; do
      # 提取 Tag 或 Pattern
      local tag=$(echo "$content" | grep -E "^\- \*\*Tag" | sed 's/.*\*\*Tag:\*\* *//' | head -1)
      local pattern=$(echo "$content" | grep -E "^\- \*\*Pattern" | sed 's/.*\*\*Pattern:\*\* *//' | head -1)
      local identifier="${tag}${pattern}"
      [ -z "$identifier" ] && identifier="unknown"
      # P1 fix: 提取第一行内容用于精确匹配，防止同日期多条目被误删
      local first_line=$(echo "$content" | sed 1q)

      echo "  📤 降级: ${identifier} (最后更新: ${date})"

      if ! $DRY_RUN; then
        # 确定目标文件
        local domain_file="${DOMAINS_DIR}/global.md"
        if [ ! -f "$domain_file" ]; then
          echo "# Domain: global" > "$domain_file"
          echo "" >> "$domain_file"
          echo "Inherits: global" >> "$domain_file"
          echo "" >> "$domain_file"
          echo "## 模式" >> "$domain_file"
          echo "" >> "$domain_file"
        fi

        # 提取实际的条目内容（去掉 DEMOTE|xxx| 前缀）
        # R3 fix: printf 替代 echo 防止 -e/-n 被当选项
        local entry_content=$(printf '%s' "$content" | sed '1d')

        # 追加到 WARM 层
        printf '%s\n' "$entry_content" >> "$domain_file"
        echo "  ✅ 已追加到: $domain_file (WARM)"

        # 更新索引
        update_index "DEMOTE" "$identifier" "$domain_file"

        # P4 fix: 使用 mktemp 替代固定路径
        local tmp_file
        tmp_file=$(mktemp /tmp/rocky-know-how.XXXXXX)
        # P1 fix: 同时匹配日期 AND 第一行内容，确保精确移除（防止同日期多条目被误删）
        # 注意: 当遇到 ## YYYY-MM-DD 时，block_buffer 是前一条目内容，$0 是当前条目第一行
        # 所以用 $0 而非 block_buffer 来匹配 target_first_line
        awk -v target_date="$date" -v target_first_line="$first_line" '
          BEGIN { in_entry=0; skip_entry=0 }
          /^## [0-9]{4}-[0-9]{2}-[0-9]{2}/ {
            if (in_entry && !skip_entry && block_buffer != "") {
              print block_buffer
            }
            if (match($0, /## ([0-9]{4}-[0-9]{2}-[0-9]{2})/)) {
              entry_date_str = substr($0, RSTART+3, RLENGTH-3)
              # P1 fix: 用 $0（当前条目第一行）匹配 target_first_line，而非 block_buffer（前一条目内容）
              if (entry_date_str == target_date && $0 == target_first_line) {
                skip_entry=1
              } else {
                skip_entry=0
                block_buffer=$0
              }
            }
            in_entry=1
            next
          }
          /^## / {
            if (in_entry && !skip_entry && block_buffer != "") {
              print block_buffer
            }
            in_entry=0; skip_entry=0; block_buffer=""
            next
          }
          in_entry && !skip_entry {
            block_buffer = block_buffer "\n" $0
            next
          }
          in_entry && skip_entry { next }
          { print }
        ' "$MEMORY_FILE" > "$tmp_file"
        mv "$tmp_file" "$MEMORY_FILE"

        demote_count=$((demote_count + 1))
      fi
    done < <(echo "$demote_entries")
  fi
  
  # 处理需要归档到 COLD 的条目
  if [ -n "$archive_entries" ]; then
    if ! $DRY_RUN; then
      backup_file "$MEMORY_FILE"
    fi
    echo ""
    echo "--- 需要归档到 COLD 的条目 ---"
    while IFS='|' read -r action date content; do
      # 提取 Tag 或 Pattern
      local tag=$(echo "$content" | grep -E "^\- \*\*Tag" | sed 's/.*\*\*Tag:\*\* *//' | head -1)
      local pattern=$(echo "$content" | grep -E "^\- \*\*Pattern" | sed 's/.*\*\*Pattern:\*\* *//' | head -1)
      local identifier="${tag}${pattern}"
      [ -z "$identifier" ] && identifier="unknown"
      # P1 fix: 提取第一行内容用于精确匹配，防止同日期多条目被误删
      local first_line=$(echo "$content" | sed 1q)

      echo "  📦 归档: ${identifier} (最后更新: ${date})"

      if ! $DRY_RUN; then
        # 创建归档文件
        local archive_file="${ARCHIVE_DIR}/entry.${date}.$(date +%Y%m%d-%H%M%S).md"

        # 提取实际的条目内容（去掉 ARCHIVE|xxx| 前缀）
        # R3 fix: printf 替代 echo 防止 -e/-n 被当选项
        local entry_content=$(printf '%s' "$content" | sed '1d')

        # 写入归档
        printf '# 归档条目: %s\n' "$identifier" > "$archive_file"
        printf '原始日期: %s\n' "$date" >> "$archive_file"
        printf '归档日期: %s\n' "$(date '+%Y-%m-%d')" >> "$archive_file"
        printf '\n' >> "$archive_file"
        printf '%s\n' "$entry_content" >> "$archive_file"
        echo "  ✅ 已归档到: $archive_file"

        # 更新索引
        update_index "ARCHIVE" "$identifier" "$archive_file"

        # P4 fix: 使用 mktemp 替代固定路径
        local tmp_file
        tmp_file=$(mktemp /tmp/rocky-know-how.XXXXXX)
        # P1 fix: 同时匹配日期 AND 第一行内容，确保精确移除（防止同日期多条目被误删）
        # 注意: 当遇到 ## YYYY-MM-DD 时，block_buffer 是前一条目内容，$0 是当前条目第一行
        # 所以用 $0 而非 block_buffer 来匹配 target_first_line
        awk -v target_date="$date" -v target_first_line="$first_line" '
          BEGIN { in_entry=0; skip_entry=0 }
          /^## [0-9]{4}-[0-9]{2}-[0-9]{2}/ {
            if (in_entry && !skip_entry && block_buffer != "") {
              print block_buffer
            }
            if (match($0, /## ([0-9]{4}-[0-9]{2}-[0-9]{2})/)) {
              entry_date_str = substr($0, RSTART+3, RLENGTH-3)
              # P1 fix: 用 $0（当前条目第一行）匹配 target_first_line，而非 block_buffer（前一条目内容）
              if (entry_date_str == target_date && $0 == target_first_line) {
                skip_entry=1
              } else {
                skip_entry=0
                block_buffer=$0
              }
            }
            in_entry=1
            next
          }
          /^## / {
            if (in_entry && !skip_entry && block_buffer != "") {
              print block_buffer
            }
            in_entry=0; skip_entry=0; block_buffer=""
            next
          }
          in_entry && !skip_entry {
            block_buffer = block_buffer "\n" $0
            next
          }
          in_entry && skip_entry { next }
          { print }
        ' "$MEMORY_FILE" > "$tmp_file"
        mv "$tmp_file" "$MEMORY_FILE"

        archive_count=$((archive_count + 1))
      fi
    done < <(echo "$archive_entries")
  fi
  
  echo ""
  if $DRY_RUN; then
    echo "✅ 降级检查完成（dry-run，未实际修改）"
  else
    echo "✅ 降级整理完成: $demote_count 条降级, $archive_count 条归档"
  fi
}

if $DRY_RUN; then
  echo "=== 模拟模式 (dry-run) ==="
  echo ""
  entries_data=$(get_entries_with_dates "$MEMORY_FILE")
  
  if [ -z "$entries_data" ]; then
    echo "  无降级候选"
  else
    echo "需要降级的条目:"
    echo "$entries_data" | grep "^DEMOTE|" | while IFS='|' read -r action date content; do
      local tag=$(echo "$content" | grep -E "^\- \*\*Tag" | sed 's/.*\*\*Tag:\*\* *//' | head -1)
      local pattern=$(echo "$content" | grep -E "^\- \*\*Pattern" | sed 's/.*\*\*Pattern:\*\* *//' | head -1)
      local identifier="${tag}${pattern}"
      [ -z "$identifier" ] && identifier="unknown"
      echo "  📤 DEMOTE: ${identifier} (日期: ${date})"
    done
    
    echo ""
    echo "需要归档的条目:"
    echo "$entries_data" | grep "^ARCHIVE|" | while IFS='|' read -r action date content; do
      local tag=$(echo "$content" | grep -E "^\- \*\*Tag" | sed 's/.*\*\*Tag:\*\* *//' | head -1)
      local pattern=$(echo "$content" | grep -E "^\- \*\*Pattern" | sed 's/.*\*\*Pattern:\*\* *//' | head -1)
      local identifier="${tag}${pattern}"
      [ -z "$identifier" ] && identifier="unknown"
      echo "  📦 ARCHIVE: ${identifier} (日期: ${date})"
    done
  fi
  echo ""
  echo "💡 如需实际执行，请移除 --dry-run 参数"
else
  process_entries
fi

echo ""
echo "💡 降级规则: memory.md 中 ${DAYS_THRESHOLD}天+ 未使用的条目 → 降级到 domains/ (WARM)"
echo "💡 归档规则: ${ARCHIVE_THRESHOLD}天+ 未使用 → 归档到 archive/ (COLD)"
echo "💡 永不删除: 所有数据永久保留"
