#!/bin/bash
# rocky-know-how 统计面板 v3.3.0
# 用法: stats.sh

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SKILL_DIR/lib/common.sh"
STATE_DIR=$(get_state_dir)
SHARED_DIR=$(get_shared_dir)
ERRORS_FILE="$SHARED_DIR/experiences.md"
MEMORY_FILE="$SHARED_DIR/memory.md"
CORRECTIONS_FILE="$SHARED_DIR/corrections.md"
DOMAINS_DIR="$SHARED_DIR/domains"
PROJECTS_DIR="$SHARED_DIR/projects"
ARCHIVE_DIR="$SHARED_DIR/archive"

echo "╔════════════════════════════════════════════╗"
echo "║  📊 rocky-know-how 经验诀窍统计面板 v3.3.0 ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# ============ v2 分层存储统计 ============
echo "🔥 HOT (始终加载)"
echo "───────────────────────────────────"
if [ -f "$MEMORY_FILE" ]; then
  hot_lines=$(wc -l < "$MEMORY_FILE" | tr -d ' ')
  hot_entries=$(grep -c "^## " "$MEMORY_FILE" 2>/dev/null || echo "0")
  echo "  memory.md: ${hot_entries} 条目, ${hot_lines} 行"
else
  echo "  memory.md: (未初始化)"
fi
echo ""

echo "🌡️ WARM (按需加载)"
echo "───────────────────────────────────"
if [ -d "$DOMAINS_DIR" ]; then
  domain_count=$(find "$DOMAINS_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  echo "  domains/: ${domain_count} 文件"
  find "$DOMAINS_DIR" -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort | while read -r f; do
    f_name=$(basename "$f")
    f_lines=$(wc -l < "$f" | tr -d ' ')
    echo "    - $f_name: ${f_lines} 行"
  done
else
  echo "  domains/: 0 文件"
fi

if [ -d "$PROJECTS_DIR" ]; then
  project_count=$(find "$PROJECTS_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  echo "  projects/: ${project_count} 文件"
  find "$PROJECTS_DIR" -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort | while read -r f; do
    f_name=$(basename "$f")
    f_lines=$(wc -l < "$f" | tr -d ' ')
    echo "    - $f_name: ${f_lines} 行"
  done
else
  echo "  projects/: 0 文件"
fi
echo ""

echo "❄️ COLD (归档)"
echo "───────────────────────────────────"
if [ -d "$ARCHIVE_DIR" ]; then
  archive_count=$(find "$ARCHIVE_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  echo "  archive/: ${archive_count} 文件"
else
  echo "  archive/: 0 文件"
fi
echo ""

# ============ v1 experiences.md 统计 ============
echo "📚 v1 主数据 (experiences.md)"
echo "───────────────────────────────────"
if [ -f "$ERRORS_FILE" ]; then
  total_entries=$(grep -c '^## \[EXP-' "$ERRORS_FILE" 2>/dev/null || echo "0")
  echo "  总条目: $total_entries"

  current_month=$(date +%Y%m)
  this_month=$(grep '^## \[EXP-' "$ERRORS_FILE" 2>/dev/null | grep -c "${current_month}" || echo "0")
  echo "  本月新增: $this_month"

  echo ""
  echo "  📂 Area 分布:"
  area_data=$(grep '^\*\*Area\*\*:' "$ERRORS_FILE" 2>/dev/null | sed 's/^\*\*Area\*\*: //' | sort | uniq -c | sort -rn)
  if [ -n "$area_data" ]; then
    echo "$area_data" | while read count area; do
      printf "    %-20s %3d\n" "$area" "$count"
    done
  else
    echo "    (无数据)"
  fi

  echo ""
  echo "  🏷️  Tag 分布 (Top 10):"
  tag_data=$(grep '^\*\*Tags\*\*:' "$ERRORS_FILE" 2>/dev/null | sed 's/^\*\*Tags\*\*: //' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -v '^$' | sort | uniq -c | sort -rn | head -10)
  if [ -n "$tag_data" ]; then
    echo "$tag_data" | while read count tag; do
      bar=""
      i=1
      while [ $i -le $count ] && [ $i -le 10 ]; do
        bar="${bar}█"
        i=$((i + 1))
      done
      printf "    %-20s %3d %s\n" "$tag" "$count" "$bar"
    done
  else
    echo "    (无数据)"
  fi
else
  echo "  experiences.md 不存在"
fi
echo ""

# ============ corrections.md 统计 ============
echo "📋 纠正日志 (corrections.md)"
echo "───────────────────────────────────"
if [ -f "$CORRECTIONS_FILE" ]; then
  # corrections.md 条目以 ### HH:MM 开头，日期标题以 ## YYYY-MM-DD 开头
  corr_entries=$(grep -c "^- \*\*纠正:\*\*" "$CORRECTIONS_FILE" 2>/dev/null || echo "0")
  corr_lines=$(wc -l < "$CORRECTIONS_FILE" | tr -d ' ')
  echo "  条目: $corr_entries, 行数: $corr_lines"
  # 最近一周的纠正
  week_ago=$(date -v-7d +%Y-%m 2>/dev/null || date -d "7 days ago" +%Y-%m)
  recent=$(grep "^## [0-9]" "$CORRECTIONS_FILE" 2>/dev/null | grep -c "$week_ago" || echo "0")
  echo "  本周新增: $recent"
else
  echo "  (未初始化)"
fi
echo ""

# ============ 最近条目 ============
echo "📝 最近条目"
echo "───────────────────────────────────"
if [ -f "$ERRORS_FILE" ]; then
  grep '^## \[EXP-' "$ERRORS_FILE" 2>/dev/null | tail -5 | while read line; do
    echo "  $line"
  done
else
  echo "  (无数据)"
fi
echo ""

# ============ 存储总览 ============
echo "💾 存储总览"
echo "───────────────────────────────────"
total_size=0
for f in "$MEMORY_FILE" "$CORRECTIONS_FILE" "$ERRORS_FILE"; do
  [ -f "$f" ] && size=$(wc -c < "$f" | tr -d ' ') && total_size=$((total_size + size))
done
echo "  主数据大小: $((total_size / 1024)) KB"
echo "  存储路径: $SHARED_DIR"
echo ""

echo "💡 v2.0 晋升规则: Tag 7天内 ≥3次 → 晋升 HOT"
