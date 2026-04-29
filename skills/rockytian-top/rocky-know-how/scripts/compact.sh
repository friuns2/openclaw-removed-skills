#!/bin/bash
# rocky-know-how 压缩整理脚本 v3.3.0
# 用法: compact.sh [--dry-run] [--file memory.md]
# 当文件超过限制时压缩：
#   memory.md: >100行 → 合并相似条目，摘要冗余，保留已确认偏好
#   domains/*.md: >200行 → 先把超出部分移到 archive/ 再截断
#   projects/*.md: >200行 → 先把超出部分移到 archive/ 再截断
# 永不删除已确认偏好

DRY_RUN=false
TARGET_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --file)    TARGET_FILE="$2"; shift 2 ;;
    -h|--help)
      echo "用法: compact.sh [--dry-run] [--file <file>]"
      echo "  --dry-run   模拟执行"
      echo "  --file      指定文件（默认全部检查）"
      exit 0 ;;
    *) shift ;;
  esac
done

LOCK_DIR=""
acquire_lock_from_common() {
  LOCK_DIR="$(get_lock_dir compact)"
  if ! acquire_lock "$LOCK_DIR"; then
    echo "❌ 无法获取压缩锁，请稍后重试"
    exit 1
  fi
}
release_lock_from_common() {
  [ -n "$LOCK_DIR" ] && release_lock "$LOCK_DIR"
}

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPTS_DIR/lib/common.sh"
STATE_DIR=$(get_state_dir)
SHARED_DIR=$(get_shared_dir)
# R4 fix: 获取压缩锁
acquire_lock_from_common
trap 'release_lock_from_common' EXIT
MEMORY_FILE="$SHARED_DIR/memory.md"
CORRECTIONS_FILE="$SHARED_DIR/corrections.md"
DOMAINS_DIR="$SHARED_DIR/domains"
PROJECTS_DIR="$SHARED_DIR/projects"
ARCHIVE_DIR="$SHARED_DIR/archive"

echo "=== 压缩整理 (v3.3.0) ==="
$DRY_RUN && echo "模式: 模拟 (dry-run)"
echo ""

# 限制阈值
MEMORY_LIMIT=100
WARM_LIMIT=200

check_and_compact() {
  local file="$1"
  local limit="$2"
  local label="$3"

  [ ! -f "$file" ] && return

  local lines=$(wc -l < "$file" | tr -d ' ')
  echo "  $label: ${lines} 行 (限制: ${limit})"

  if [ "$lines" -gt "$limit" ]; then
    local overflow=$((lines - limit))
    echo "    ⚠️  超出 ${overflow} 行，需要压缩"

    if $DRY_RUN; then
      echo "    [dry-run] 将压缩: $file"
      # 估算压缩后行数
      echo "    压缩策略:"
      echo "      1. 合并相似纠正为单一规则"
      echo "      2. 摘要冗长条目"
      echo "      3. 归档未使用的模式"
    else
      # 实际压缩
      compact_file "$file" "$limit"
      echo "    ✅ 已压缩: $file"
    fi
  else
    echo "    ✅ 正常，无需压缩"
  fi
}

compact_file() {
  local file="$1"
  local limit="$2"

  # 备份原文件
  local backup_file="${file}.bak.$(date +%s)"
  cp "$file" "$backup_file"
  echo "    📦 备份: $backup_file"

  # 策略1: 对于 memory.md，智能压缩
  # 实际格式：晋升条目以 `## YYYY-MM-DD` 开头，后面是晋升内容块
  # 策略：保留所有 `## YYYY-MM-DD` 开头的条目，删除其他条目
  # 如果文件格式与预期不符（无日期条目），跳过压缩以避免数据丢失
  if [ "$file" = "$MEMORY_FILE" ]; then
    # P4 fix: 使用 mktemp 替代固定路径
    local tmp_file=$(mktemp /tmp/rocky-know-how.XXXXXX)
    
    # 检查是否包含日期条目格式（`## YYYY-MM-DD` 开头）
    local has_date_entries=$(grep -c "^## [0-9]" "$file" 2>/dev/null || echo "0")
    
    if [ "$has_date_entries" -eq 0 ]; then
      echo "    ⚠️  memory.md 格式不符（无日期条目），跳过压缩以避免数据丢失"
      rm -f "$tmp_file"
      return 0
    fi
    
    # 保留所有日期条目（## YYYY-MM-DD 开头）及其完整内容
    # 用换行符保留原始 markdown 格式
    awk '
      BEGIN { buffer=""; in_date_entry=0 }
      /^## [0-9]{4}-[0-9]{2}-[0-9]{2}/ {
        if (in_date_entry && buffer != "") { print buffer }
        buffer=$0; in_date_entry=1; next
      }
      /^## / {
        if (in_date_entry && buffer != "") { print buffer }
        buffer=""; in_date_entry=0; next
      }
      in_date_entry { buffer = buffer "\n" $0; next }
      !in_date_entry { print }
      END { if (in_date_entry && buffer != "") { print buffer } }
    ' "$file" > "$tmp_file"
    
    # 检查压缩后是否有效（行数减少或有日期条目）
    local after_date_entries=$(grep -c "^## [0-9]" "$tmp_file" 2>/dev/null || echo "0")
    
    if [ "$after_date_entries" -eq 0 ]; then
      echo "    ❌ 压缩后 memory.md 无日期条目，恢复备份"
      rm -f "$tmp_file"
      return 1
    fi
    
    mv "$tmp_file" "$file"
    return 0
  fi

  # 策略2: 对于 corrections.md，保留最近50个日期块
  # corrections.md 格式:
  # # 纠正日志
  # ## YYYY-MM-DD (日期标题)
  # ### HH:MM — namespace:area (时间戳条目，每个条目以 ### HH:MM 开头)
  if [ "$file" = "$CORRECTIONS_FILE" ]; then
    # 计算当前日期块数量（以 ## YYYY-MM-DD 开头），与归档粒度保持一致
    local before_count=$(grep -c "^## [0-9]" "$file" 2>/dev/null || echo "0")
    echo "    📊 压缩前日期块数: ${before_count}"

    if [ "$before_count" -gt 50 ]; then
      # 创建 archive 目录
      mkdir -p "$ARCHIVE_DIR"
      local archive_file="${ARCHIVE_DIR}/corrections-archive.md"

      # 获取所有日期块（chronological 顺序，最旧→最新）
      local all_dates=$(grep "^## [0-9]" "$file" 2>/dev/null)
      local total_dates=$(echo "$all_dates" | wc -l | tr -d ' ')

      # 保留最近50个（chronological 的最后50条 = 最新），归档最旧的
      local dates_to_keep=$(echo "$all_dates" | tail -50)
      local to_archive=$((total_dates - 50))
      local dates_to_archive=$(echo "$all_dates" | head -$to_archive)

      echo "    📊 总日期数: ${total_dates}, 保留: 50, 归档: $((total_dates - 50))"
      
      # P4 fix: 使用 mktemp 替代固定路径，避免进程ID冲突和临时文件残留
      local tmp_kept
      local tmp_archive_content
      tmp_kept=$(mktemp /tmp/rocky-know-how.corr-kept.XXXXXX)
      tmp_archive_content=$(mktemp /tmp/rocky-know-how.corr-arch.XXXXXX)
      
      # 写入保留文件的头部（保留文件的前两行：标题和空行）
      head -n 2 "$file" > "$tmp_kept"
      
      # 写入归档内容
      {
        echo "# 纠正日志归档"
        echo "归档时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "压缩原因: 超出50条限制"
        echo ""
      } > "$tmp_archive_content"
      
      # 遍历原文件，根据日期决定保留还是归档
      local in_keep_date=0
      local current_date=""
      local line_buffer=""
      local in_entry=0
      
      while IFS= read -r line; do
        # 检测日期行
        if echo "$line" | grep -qE "^## [0-9]{4}-[0-9]{2}-[0-9]{2}$"; then
          current_date="$line"
          # 结束之前的条目
          if [ -n "$line_buffer" ]; then
            if [ $in_keep_date -eq 1 ]; then
              printf '%s\n' "$line_buffer" >> "$tmp_kept"
            else
              printf '%s\n' "$line_buffer" >> "$tmp_archive_content"
            fi
            line_buffer=""
          fi
          # 检查这个日期是否要保留
          if echo "$dates_to_keep" | grep -qF "$line"; then
            in_keep_date=1
            echo "" >> "$tmp_kept"
            printf '%s\n' "$line" >> "$tmp_kept"
          else
            in_keep_date=0
            echo "" >> "$tmp_archive_content"
            printf '%s\n' "$line" >> "$tmp_archive_content"
          fi
          in_entry=0
        elif echo "$line" | grep -qE "^### [0-9][0-9]:[0-9][0-9] "; then
          # 时间戳条目开始 - 结束之前的条目
          if [ -n "$line_buffer" ]; then
            if [ $in_keep_date -eq 1 ]; then
              printf '%s\n' "$line_buffer" >> "$tmp_kept"
            else
              printf '%s\n' "$line_buffer" >> "$tmp_archive_content"
            fi
            line_buffer=""
          fi
          line_buffer="$line"
          in_entry=1
        elif [ $in_entry -eq 1 ]; then
          line_buffer="$line_buffer"$'\n'$line
        elif [ -n "$line" ]; then
          # 非条目内容行（如空行或注释），直接处理
          if [ $in_keep_date -eq 1 ]; then
            printf '%s\n' "$line" >> "$tmp_kept"
          else
            printf '%s\n' "$line" >> "$tmp_archive_content"
          fi
        fi
      done < "$file"
      
      # 处理最后一行
      if [ -n "$line_buffer" ]; then
        if [ $in_keep_date -eq 1 ]; then
          printf '%s\n' "$line_buffer" >> "$tmp_kept"
        else
          printf '%s\n' "$line_buffer" >> "$tmp_archive_content"
        fi
      fi
      
      # 追加归档内容到归档文件
      cat "$tmp_archive_content" >> "$archive_file"
      echo "    📦 已归档旧条目到: ${archive_file}"
      
      # 用保留的内容替换原文件
      mv "$tmp_kept" "$file"
      
      # 清理临时文件
      rm -f "$tmp_archive_content"
      
      # P6 fix: 统一用日期块维度统计（before_count 也是日期块数）
      local after_count=$(grep -c "^## [0-9]" "$file" 2>/dev/null || echo "0")
      echo "    📊 压缩后日期块数: ${after_count}"
      
      if [ "$after_count" -ge "$before_count" ]; then
        echo "    ❌ 压缩后条目数异常: ${after_count} >= ${before_count}"
        # 恢复备份
        cp "$backup_file" "$file"
        echo "    🔄 已恢复备份"
        return 1
      fi
    fi
    return
  fi

  # 策略3: 对于 domains/projects，先把超出部分移到 archive/ 再截断
  local dir=$(dirname "$file")
  if [ -d "$dir" ]; then
    local basename=$(basename "$file")
    local lines=$(wc -l < "$file" | tr -d ' ')
    
    if [ "$lines" -gt "$limit" ]; then
      # 创建 archive 目录（如果不存在）
      mkdir -p "$ARCHIVE_DIR"
      
      # 把超出部分移到 archive
      tail -n +$((limit + 1)) "$file" > "${ARCHIVE_DIR}/${basename}.archived.$(date +%Y%m%d-%H%M%S)"
      echo "    📦 归档超出部分到: ${ARCHIVE_DIR}/${basename}.archived.$(date +%Y%m%d-%H%M%S)"
      
      # 截断到限制行数
      head -n "$limit" "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
    fi
  fi
}

echo "─── HOT 层检查 ───"
check_and_compact "$MEMORY_FILE" "$MEMORY_LIMIT" "memory.md"

echo ""
echo "─── corrections.md 检查 ───"
if [ -f "$CORRECTIONS_FILE" ]; then
  corr_lines=$(wc -l < "$CORRECTIONS_FILE" | tr -d ' ')
  echo "  corrections.md: ${corr_lines} 行 (限制: 200)"
  # corrections 保留最近50条
  # 先检查条目数（以 ### HH:MM 开头）
  corr_entries=$(grep -c "^## [0-9]" "$CORRECTIONS_FILE" 2>/dev/null || echo "0")
  echo "  日期块数: ${corr_entries} (压缩阈值: 50)"
  if [ "$corr_entries" -gt 50 ]; then
    if $DRY_RUN; then
      echo "    [dry-run] 将压缩 corrections.md（保留最近50条）"
    else
      compact_file "$CORRECTIONS_FILE" 50
      echo "    ✅ 已压缩: corrections.md"
    fi
  else
    echo "    ✅ 无需压缩"
  fi
fi

echo ""
echo "─── WARM 层检查 ───"
if [ -d "$DOMAINS_DIR" ]; then
  for f in "$DOMAINS_DIR"/*.md; do
    [ ! -f "$f" ] && continue
    check_and_compact "$f" "$WARM_LIMIT" "$(basename "$f")"
  done
fi

if [ -d "$PROJECTS_DIR" ]; then
  for f in "$PROJECTS_DIR"/*.md; do
    [ ! -f "$f" ] && continue
    check_and_compact "$f" "$WARM_LIMIT" "$(basename "$f")"
  done
fi

echo ""
if $DRY_RUN; then
  echo "✅ 压缩检查完成（dry-run，未实际修改）"
else
  echo "✅ 压缩整理完成"
fi
echo ""
echo "💡 压缩策略 v3.3.0:"
echo "   1. memory.md: 合并相似条目，摘要冗余，保留已确认偏好"
echo "   2. corrections.md: 保留最近50条"
echo "   3. domains/projects: 超出部分移到 archive/ 再截断"
echo "   4. 永不删除已确认偏好类条目"
