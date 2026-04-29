#!/bin/bash
# rocky-know-how 搜经验诀窍 v3.3.0
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"

# 用法: search.sh [选项] <关键词1> [关键词2]...
#       search.sh --all              显示所有
#       search.sh --preview "关键词"  只显示摘要
#       search.sh --tag "tag1,tag2"   按标签搜索
#       search.sh --area infra        按领域搜索
#       search.sh --domain code       按命名空间（domain）搜索
#       search.sh --project foo       按命名空间（project）搜索
#       search.sh --global "关键词"   搜所有workspace
#       search.sh --since YYYY-MM-DD  按日期过滤
#       search.sh --layer hot|warm|cold  按层搜索
#       search.sh --semantic "关键词"  语义搜索（基于向量）

# R1 fix: 路径穿越校验函数
# N13 fix: 精确匹配路径穿越组件 .. 和 ..\ 而非宽泛匹配
validate_name() {
  local name="$1"
  # 检测路径穿越: ../ 或 ..\ 或 /../ 或 \..\
  if [[ "$name" == *../* || "$name" == *..\\* || "$name" == */../* || "$name" == *\\..\\* ]]; then
    echo "❌ 无效名称: 包含非法字符"
    return 1
  fi
  # 检测 shell 特殊字符
  case "$name" in
    *\`*|*\$*)
      echo "❌ 无效名称: 包含非法字符"
      return 1 ;;
  esac
  return 0
}

# 转义 grep 固定字符串模式：使用 grep -F (fixed string) 而非正则
# 所有搜索函数使用 grep -qiF --color=never 进行固定字符串匹配
# 此函数清理控制字符
escape_grep() {
  # 移除换行符和控制字符，保留可打印字符
  printf '%s' "$1" | tr -d '\n\r\000-\037'
}

# 限制输入长度，防止资源耗尽
MAX_INPUT_LEN=1000

MAX_RESULTS=10
SINCE_DATE=""
SHOW_ALL=false
PREVIEW=false
GLOBAL=false
FILTER_TAG=""
FILTER_AREA=""
FILTER_DOMAIN=""
FILTER_PROJECT=""
FILTER_LAYER=""
SEMANTIC=false  # 默认关闭语义搜索，需 --semantic 显式启用
KEYWORDS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)         SHOW_ALL=true; shift ;;
    --preview)     PREVIEW=true; shift ;;
    --global)      GLOBAL=true; shift ;;
    --since)       SINCE_DATE="$2"; shift 2 ;;
    --limit)         MAX_RESULTS="$2"; shift 2 ;;
    --max-results) MAX_RESULTS="$2"; shift 2 ;;
    --tag)         FILTER_TAG="$2"; shift 2 ;;
    --area)        FILTER_AREA="$2"; shift 2 ;;
    --domain)      FILTER_DOMAIN="$2"; shift 2 ;;
    --project)     FILTER_PROJECT="$2"; shift 2 ;;
    --layer)       FILTER_LAYER="$2"; shift 2 ;;
    --semantic)    SEMANTIC=true; shift ;;
    --no-semantic) SEMANTIC=false; shift ;;
    -h|--help)
      echo "用法: search.sh [选项] <关键词...>"
      echo "  --all              显示所有"
      echo "  --preview          只显示摘要"
      echo "  --tag \"t1,t2\"      按标签搜索（AND）"
      echo "  --area infra       按领域搜索"
      echo "  --domain code      按 domain 命名空间搜索"
      echo "  --project foo      按 project 命名空间搜索"
      echo "  --layer hot|warm|cold  按层搜索"
      echo "  --global           搜所有workspace"
      echo "  --since YYYY-MM-DD 按日期过滤"
      echo "  --limit N          最多显示N条（默认10）"\n"  --max-results N    同上，别名"
      echo "  --semantic         启用语义搜索（默认关闭，需显式开启）"
      echo "  --no-semantic      禁用语义搜索"
      exit 0 ;;
    -*)  echo "未知选项: $1"; exit 1 ;;
    *)   KEYWORDS+=("$1"); shift ;;
  esac
done

# 自动拆分：如果只传了一个含空格的参数，拆成多个关键词
if [ ${#KEYWORDS[@]} -eq 1 ] && echo "${KEYWORDS[0]}" | grep -q ' '; then
  read -ra SPLIT_KW <<< "${KEYWORDS[0]}"
  KEYWORDS=("${SPLIT_KW[@]}")
fi

# 限制关键词长度，防止资源耗尽
for i in "${!KEYWORDS[@]}"; do
  if [ ${#KEYWORDS[$i]} -gt $MAX_INPUT_LEN ]; then
    KEYWORDS[$i]="${KEYWORDS[$i]:0:$MAX_INPUT_LEN}"
  fi
done

source "$SKILL_DIR/lib/common.sh"
STATE_DIR=$(get_state_dir)
SHARED_DIR=$(get_shared_dir)
ERRORS_FILE="$SHARED_DIR/experiences.md"

# 新版 layered 存储路径
MEMORY_FILE="$SHARED_DIR/memory.md"
DOMAINS_DIR="$SHARED_DIR/domains"
PROJECTS_DIR="$SHARED_DIR/projects"
ARCHIVE_DIR="$SHARED_DIR/archive"
CORRECTIONS_FILE="$SHARED_DIR/corrections.md"

# 临时目录
TMPDIR_KH=$(mktemp -d /tmp/rocky-know-how-XXXXXX)
trap 'rm -rf "$TMPDIR_KH"' EXIT

# ========== experiences.md（v1主数据）搜索函数 ==========

# 提取条目块
extract_blocks() {
  local file="$1"
  [ ! -f "$file" ] && return 1
  local lines=$(grep -n "^## \[EXP-" "$file" 2>/dev/null | cut -d: -f1)
  [ -z "$lines" ] && return 1
  local block_idx=0
  local prev=""
  for line in $lines; do
    if [ -z "$prev" ]; then
      prev=$line
      continue
    fi
    # 检查是否相邻（line <= prev 时范围为负，跳过）
    if [ "$line" -gt "$prev" ]; then
      sed -n "${prev},$((line-1))p" "$file" > "$TMPDIR_KH/block_${block_idx}.md"
      block_idx=$((block_idx+1))
    fi
    prev=$line
  done
  local total=$(wc -l < "$file" | tr -d ' ')
  sed -n "${prev},${total}p" "$file" > "$TMPDIR_KH/block_${block_idx}.md"
  block_idx=$((block_idx+1))
  echo $block_idx
}

# 评分单个块
score_block() {
  local block_file="$1"
  local score=0

  if [ -n "$SINCE_DATE" ]; then
    local entry_date=$(grep "^## \[EXP-" "$block_file" | head -1 | sed 's/.*\[EXP-\([0-9]\{8\}\)-.*/\1/')
    local since_num=$(echo "$SINCE_DATE" | sed 's/-//g')
    [ "${entry_date:-0}" -lt "${since_num:-0}" ] 2>/dev/null && echo "0" && return
  fi

  if [ -n "$FILTER_AREA" ]; then
    local entry_area=$(grep "^\*\*Area\*\*:" "$block_file" | head -1 | sed 's/\*\*Area\*\*: //')
    [ "$entry_area" != "$FILTER_AREA" ] && echo "0" && return
  fi

  if [ -n "$FILTER_TAG" ]; then
    local entry_tags=$(grep "^\*\*Tags\*\*:" "$block_file" | head -1 | sed 's/\*\*Tags\*\*: //')
    local tag_miss=false
    for t in $(echo "$FILTER_TAG" | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -v '^$'); do
      if ! echo ",${entry_tags}," | grep -qi --color=never ",${t}," 2>/dev/null; then
        tag_miss=true
        break
      fi
    done
    if $tag_miss; then
      echo "0" && return
    fi
  fi

  local kw_len=${#KEYWORDS[@]:-0}
  if [ "$kw_len" -gt 0 ]; then
    local total_kw=$kw_len
    local hit=0
    for kw in "${KEYWORDS[@]}"; do
      # 转义关键词防止正则注入
      local escaped_kw=$(escape_grep "$kw")
      grep -qiF --color=never "$escaped_kw" "$block_file" && hit=$((hit+1))
    done
    [ $hit -eq 0 ] && echo "0" && return
    score=$hit
  else
    score=1
  fi

  echo "$score"
}

# 打印条目
print_block() {
  local block_file="$1"
  local score="$2"
  local total_kw="${3:-1}"

  local id=$(grep "^## \[EXP-" "$block_file" | head -1 | sed 's/## //')
  local problem=$(sed -n '/^### 问题$/{n;p;}' "$block_file")
  local solution=$(sed -n '/^### 正确方案$/{n;p;}' "$block_file")
  local tags=$(grep "^\*\*Tags\*\*:" "$block_file" | head -1 | sed 's/\*\*Tags\*\*: //')
  local area=$(grep "^\*\*Area\*\*:" "$block_file" | head -1 | sed 's/\*\*Area\*\*: //')

  if $PREVIEW; then
    echo "📌 $id [匹配度: ${score}/${total_kw}]"
    echo "   问题: $problem"
    echo "   方案: $solution"
    echo "   Tags: $tags | Area: $area"
    echo ""
  else
    echo "$id [匹配度: ${score}/${total_kw}]"
    echo "───────────────────────────────────"
    cat "$block_file"
    echo ""
  fi
}

# 搜索单个 experiences 文件
search_experiences_file() {
  local file="$1"
  rm -f "$TMPDIR_KH/scores.txt"
  local count=$(extract_blocks "$file")
  [ -z "$count" ] && return 1
  [ "$count" -eq 0 ] && return 1
  # R7 fix: 大量条目时限制临时文件数，避免 fd 耗尽
  # N6 fix: 改为 stdout 输出，确保用户能看到提示
  if [ "$count" -gt 500 ]; then
    echo "⚠️ 条目数 ${count} 较多，仅搜索前500条"
    count=500
  fi

  local found=0
  local total_kw=${#KEYWORDS[@]:-0}
  [ "$total_kw" -eq 0 ] && total_kw=1

  for i in $(seq 0 $((count-1))); do
    local block_file="$TMPDIR_KH/block_${i}.md"
    [ ! -f "$block_file" ] && continue
    local s=$(score_block "$block_file")
    [ "$s" = "0" ] && continue
    echo "${s} ${i}" >> "$TMPDIR_KH/scores.txt"
  done

  [ ! -f "$TMPDIR_KH/scores.txt" ] && return 1

  while read -r s idx; do
    print_block "$TMPDIR_KH/block_${idx}.md" "$s" "$total_kw"
    found=$((found+1))
  done < <(sort -rn -k1 "$TMPDIR_KH/scores.txt" 2>/dev/null | head -$MAX_RESULTS)

  return 0
}

# 格式化全部条目（供 --all 使用）
format_all() {
  local file="$1"
  [ ! -f "$file" ] && return

  awk '
    /^## \[EXP-/ { id=$0; area=""; tags=""; created=""; problem=""; next }
    /^\*\*Area\*\*:/ { sub(/^\*\*Area\*\*: /,""); area=$0; next }
    /^\*\*Tags\*\*:/ { sub(/^\*\*Tags\*\*: /,""); tags=$0; next }
    /^\*\*Created\*\*:/ { sub(/^\*\*Created\*\*: /,""); created=$0; next }
    /^### 问题$/ { getline; problem=$0; next }
    /^---/ && id!="" {
      printf "%s\n  Area: %s | Tags: %s | 创建: %s\n  问题: %s\n---\n\n", id, area, tags, created, problem
      id=""
    }
    # 容错: 忽略无法解析的行，不中断处理
    { next }
  ' "$file"
}

# ========== layered 存储搜索 ==========

# 搜索 layered 文件（memory.md, domains/, projects/）
search_layered_file() {
  local file="$1"
  local source="$2"
  [ ! -f "$file" ] && return 1

  local kw_len=${#KEYWORDS[@]:-0}
  [ "$kw_len" -eq 0 ] && kw_len=1

  local hits=0
  local line_num=0
  while IFS= read -r line; do
    line_num=$((line_num+1))
    [ -z "$line" ] && continue
    # 跳过标题行
    echo "$line" | grep -qE "^#|^## |^\-\-|^\*\*" && continue

    local score=0
    for kw in "${KEYWORDS[@]}"; do
      local escaped_kw=$(escape_grep "$kw")
      echo "$line" | grep -qiF --color=never "$escaped_kw" && score=$((score+1))
    done

    if [ $score -gt 0 ]; then
      echo "📎 ${source}:${line_num} [${score}/${kw_len}]"
      echo "   $line"
      echo ""
      hits=$((hits+1))
    fi
  done < "$file"

  [ $hits -gt 0 ] && return 0 || return 1
}

# ========== 主流程 ==========

# --all 模式
if $SHOW_ALL; then
  any_content=0
  echo "=== 全部经验诀窍 ==="
  echo ""
  echo "─── v1 主数据 (experiences.md) ───"
  [ -f "$ERRORS_FILE" ] && { format_all "$ERRORS_FILE"; any_content=1; }
  echo ""
  echo "─── HOT 层 (memory.md) ───"
  [ -f "$MEMORY_FILE" ] && cat "$MEMORY_FILE" || echo "  (空)"
  echo ""
  echo "─── Domain 层 (domains/) ───"
  if [ -d "$DOMAINS_DIR" ]; then
    find "$DOMAINS_DIR" -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort | while read -r f; do
      echo "  📄 $(basename "$f"):"
      { grep -v "^#" "$f" | grep -v "^$"; } 2>/dev/null | head -5
      echo ""
    done
  fi
  echo "─── Project 层 (projects/) ───"
  if [ -d "$PROJECTS_DIR" ]; then
    find "$PROJECTS_DIR" -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort | while read -r f; do
      echo "  📄 $(basename "$f"):"
      { grep -v "^#" "$f" | grep -v "^$"; } 2>/dev/null | head -5
      echo ""
    done
  fi
  if [ "$any_content" = "1" ]; then
    exit 0
  else
    echo "(无数据)"
    exit 1
  fi
fi

# 层过滤模式
if [ -n "$FILTER_LAYER" ]; then
  layer_has_content=0
  case "$FILTER_LAYER" in
    hot)
      echo "─── HOT: memory.md ───"
      if [ -f "$MEMORY_FILE" ] && [ -s "$MEMORY_FILE" ]; then
        cat "$MEMORY_FILE"
        layer_has_content=1
      else
        echo "(空)"
      fi
      ;;
    warm)
      echo "─── WARM: domains/ + projects/ ───"
      if [ -d "$DOMAINS_DIR" ] && [ "$(ls -A "$DOMAINS_DIR"/*.md 2>/dev/null)" ]; then
        for f in "$DOMAINS_DIR"/*.md; do
          [ -f "$f" ] && echo "📄 $(basename "$f"):" && cat "$f" && echo "" && layer_has_content=1
        done
      fi
      if [ -d "$PROJECTS_DIR" ] && [ "$(ls -A "$PROJECTS_DIR"/*.md 2>/dev/null)" ]; then
        for f in "$PROJECTS_DIR"/*.md; do
          [ -f "$f" ] && echo "📄 $(basename "$f"):" && cat "$f" && echo "" && layer_has_content=1
        done
      fi
      [ "$layer_has_content" = "0" ] && echo "(空)"
      ;;
    cold)
      echo "─── COLD: archive/ ───"
      if [ -d "$ARCHIVE_DIR" ] && [ "$(find "$ARCHIVE_DIR" -name "*.md" 2>/dev/null)" ]; then
        find "$ARCHIVE_DIR" -name "*.md" -exec echo "📦 {}:" \; -exec head -10 {} \; 2>/dev/null
        layer_has_content=1
      else
        echo "(空)"
      fi
      ;;
  esac
  if [ "$layer_has_content" = "1" ]; then
    exit 0
  else
    exit 1
  fi
fi

# Domain 搜索（无关键词时直接展示全部内容）
if [ -n "$FILTER_DOMAIN" ]; then
  # R1 fix: 校验 domain 名称，防止路径穿越
  if ! validate_name "$FILTER_DOMAIN"; then exit 1; fi
  echo "─── Domain: ${FILTER_DOMAIN} ───"
  domain_file="$DOMAINS_DIR/${FILTER_DOMAIN}.md"
  if [ -f "$domain_file" ]; then
    if [ ${#KEYWORDS[@]} -eq 0 ]; then
      # 无关键词：展示 domain 文件 + experiences.md 中 Area 匹配的条目
      cat "$domain_file"
      echo ""
      echo "─── Domain: ${FILTER_DOMAIN} (experiences.md 中 Area:${FILTER_DOMAIN} 的条目) ───"
      if [ -f "$ERRORS_FILE" ]; then
        # H1 fix: 转义双引号，防止破坏 awk 脚本中的双引号平衡
        safe_area=$(printf '%s' "$FILTER_DOMAIN" | sed 's/"/\\"/g')
        awk -v area="$safe_area" '
          BEGIN { in_block=0 }
          /^## \[EXP-/ { id=$0; in_block=1; area_match=0 }
          /^\*\*Area\*\*:/ { sub(/^\*\*Area\*\*: /,""); if ($0 == area) area_match=1 }
          /^---$/ && in_block && area_match { print id; in_block=0 }
          /^---$/ && in_block && !area_match { in_block=0 }
        ' "$ERRORS_FILE" | while read -r entry; do
          echo "  $entry"
        done
      fi
      exit 0
    else
      # 有关键词：走搜索逻辑
      search_layered_file "$domain_file" "$FILTER_DOMAIN.md" && exit 0
    fi
  fi
  echo "未找到 domain: ${FILTER_DOMAIN}"
  exit 1
fi

# Project 搜索（无关键词时直接展示全部内容）
if [ -n "$FILTER_PROJECT" ]; then
  # R1 fix: 校验 project 名称，防止路径穿越
  if ! validate_name "$FILTER_PROJECT"; then exit 1; fi
  echo "─── Project: ${FILTER_PROJECT} ───"
  project_file="$PROJECTS_DIR/${FILTER_PROJECT}.md"
  if [ -f "$project_file" ]; then
    if [ ${#KEYWORDS[@]} -eq 0 ]; then
      # 无关键词：直接展示文件全部内容
      cat "$project_file"
      exit 0
    else
      # 有关键词：走搜索逻辑
      search_layered_file "$project_file" "${FILTER_PROJECT}.md" && exit 0
    fi
  fi
  echo "未找到 project: ${FILTER_PROJECT}"
  exit 1
fi

# 关键词校验：空字符串（不是“没有参数”，而是传了空串）
for i in "${!KEYWORDS[@]}"; do
  if [ -z "${KEYWORDS[$i]}" ]; then
    unset 'KEYWORDS[$i]'
  fi
done
KEYWORDS=("${KEYWORDS[@]}")  # 重新索引

# 需要关键词或过滤条件
if [ ${#KEYWORDS[@]} -eq 0 ] && [ -z "$FILTER_TAG" ] && [ -z "$FILTER_AREA" ] && [ -z "$FILTER_DOMAIN" ] && [ -z "$FILTER_PROJECT" ] && [ -z "$FILTER_LAYER" ] && [ -z "$SINCE_DATE" ] && ! $SEMANTIC; then
  echo "用法: search.sh [选项] <关键词...>"
  echo "提示: 用 --tag / --area / --domain / --project / --layer 过滤，或输入关键词搜索"
  exit 1
fi

# 搜索 experiences.md
echo "─── 经验诀窍 (experiences.md) ───"
total_found=0
rm -f "$TMPDIR_KH/scores.txt"
search_experiences_file "$ERRORS_FILE" && total_found=1

# 搜索 layered 文件（hot/warm 层，忽略 cold）
echo "─── Layered 记忆 ───"
layered_found=0

if [ -f "$MEMORY_FILE" ]; then
  search_layered_file "$MEMORY_FILE" "memory.md" && layered_found=1
fi

if [ -d "$DOMAINS_DIR" ]; then
  for f in "$DOMAINS_DIR"/*.md; do
    [ -f "$f" ] || continue
    search_layered_file "$f" "$(basename "$f")" && layered_found=1
  done
fi

if [ -d "$PROJECTS_DIR" ]; then
  for f in "$PROJECTS_DIR"/*.md; do
    [ -f "$f" ] || continue
    search_layered_file "$f" "$(basename "$f")" && layered_found=1
  done
fi

# 搜索 COLD 层（archive/），递归子目录
if [ -d "$ARCHIVE_DIR" ] && [ ${#KEYWORDS[@]} -gt 0 ]; then
  while IFS= read -r -d '' f; do
    search_layered_file "$f" "archive/${f#$ARCHIVE_DIR/}" && layered_found=1
  done < <(find "$ARCHIVE_DIR" -name "*.md" -type f -print0 2>/dev/null)
fi

# ============ 语义搜索（基于向量） ============
semantic_found=0
if $SEMANTIC; then
  source "$SKILL_DIR/lib/vectors.sh" 2>/dev/null
  
  # 检测向量功能是否可用
  vector_func_exists=false
  vector_api_available=false
  
  if declare -f vector_check >/dev/null 2>&1; then
    vector_func_exists=true
    if vector_check; then
      vector_api_available=true
    fi
  fi
  
  if ! $vector_func_exists || ! $vector_api_available; then
    echo "⚠️  向量搜索不可用（LM Studio 未运行或无 embedding 模型），使用关键词搜索"
  else
    vector_init "$STATE_DIR"
    
    # 首次语义搜索：如果索引为空或不存在，自动构建
    if [ ! -f "$VECTOR_DIR/index.jsonl" ] || [ ! -s "$VECTOR_DIR/index.jsonl" ]; then
      echo "📦 首次语义搜索，正在构建向量索引..."
      vector_reindex_all "$ERRORS_FILE"
    fi
    
    # 合并所有关键词作为查询
    QUERY=$(IFS=' '; echo "${KEYWORDS[*]}")
    echo ""
    echo "─── 语义搜索结果 ───"
    semantic_result=$(vector_search "$QUERY" 5 0.6)
    if [ -n "$semantic_result" ]; then
      echo "$semantic_result" | while IFS='|' read score id area text; do
        echo "  📊 [$score] $id [$area] $text"
      done
      semantic_found=1
    fi
  fi
fi

# 如果关键词和语义搜索都没有结果，退出
if [ $total_found -eq 0 ] && [ $layered_found -eq 0 ] && [ $semantic_found -eq 0 ]; then
  echo "经验诀窍未找到相关记录"
  exit 1
fi

exit 0
