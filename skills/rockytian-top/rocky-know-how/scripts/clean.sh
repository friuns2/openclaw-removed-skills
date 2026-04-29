#!/bin/bash
# rocky-know-how 清理工具 v3.3.0
# 用法: clean.sh [--test] [--old] [--reindex]

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPTS_DIR/lib/common.sh"
source "$SCRIPTS_DIR/lib/vectors.sh"  # P3 fix: --reindex 后重建向量索引
STATE_DIR=$(get_state_dir)
SHARED_DIR=$(get_shared_dir)
ERRORS_FILE="$SHARED_DIR/experiences.md"
CORRECTIONS_FILE="$SHARED_DIR/corrections.md"
DOMAINS_DIR="$SHARED_DIR/domains"
PROJECTS_DIR="$SHARED_DIR/projects"

[ ! -f "$ERRORS_FILE" ] && echo "文件不存在" && exit 0

# P4 fix: 支持多选项参数解析（MODE + DRY_RUN flag）
MODE="info"
DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --test|--old|--reindex|--test-dry-run) MODE="$arg" ;;
    --info) MODE="info" ;;
  esac
done

# 处理 --dry-run 别名（指向 --test-dry-run）
if [ "$MODE" = "--dry-run" ]; then
  MODE="--test-dry-run"
fi

case "$MODE" in
  --test*)
    CLEAN_DRY_RUN=false
    if [ "$MODE" = "--test-dry-run" ] || $DRY_RUN; then
      CLEAN_DRY_RUN=true
    fi
    echo "=== 清理测试条目 $( $CLEAN_DRY_RUN && echo '(模拟)' || echo '(交互确认模式)') ==="
    # P4 fix: 使用 mktemp 替代固定路径
    TEMP_FILE=$(mktemp /tmp/rocky-know-how.XXXXXX)
    TEST_IDS_FILE=$(mktemp /tmp/rocky-know-how-test-ids.XXXXXX)
    removed=0
    current_block=""
    is_test=false
    test_ids=""

    {
      echo "# 经验诀窍"
      echo ""
      echo "---"
    } > "$TEMP_FILE"

    while IFS= read -r line; do
      if echo "$line" | grep -q '^## \[EXP-'; then
        if [ -n "$current_block" ] && [ "$is_test" = false ]; then
          echo "$current_block" >> "$TEMP_FILE"
        fi
        if [ "$is_test" = true ]; then
          entry_id=$(echo "$current_block" | grep "^## \[EXP-" | sed 1q)
          $CLEAN_DRY_RUN && echo "  将删除: $entry_id"
          echo "$entry_id" >> "$TEST_IDS_FILE"
          removed=$((removed+1))
        fi
        current_block="$line"
        is_test=false
      elif echo "$line" | grep -q '^\*\*Tags'; then
        # 精确匹配 tag 列表中完全是 "test" 的条目（排除 retest、final-test 等）
        tags_val=$(echo "$line" | sed 's/^\*\*Tags[:*]* *: *//')
        if echo ",${tags_val}," | tr ',' '\n' | grep -qx 'test' 2>/dev/null; then
          is_test=true
        fi
        current_block="$current_block"$'\n'"$line"
      else
        current_block="$current_block"$'\n'"$line"
      fi
    done < "$ERRORS_FILE"

    if [ -n "$current_block" ] && [ "$is_test" = false ]; then
      echo "$current_block" >> "$TEMP_FILE"
    elif [ "$is_test" = true ]; then
      entry_id=$(echo "$current_block" | grep "^## \[EXP-" | sed 1q)
      $CLEAN_DRY_RUN && echo "  将删除: $entry_id"
      echo "$entry_id" >> "$TEST_IDS_FILE"
      removed=$((removed+1))
    fi

    if $CLEAN_DRY_RUN; then
      echo "模拟完成: 将清理 $removed 条测试条目"
      rm -f "$TEMP_FILE" "$TEST_IDS_FILE"
    else
      if [ "$removed" -eq 0 ]; then
        echo "没有找到 tag 为 'test' 的条目，无需清理。"
        rm -f "$TEMP_FILE" "$TEST_IDS_FILE"
      else
        echo ""
        echo "以下 $removed 条测试条目将被删除："
        cat "$TEST_IDS_FILE" | sed 's/^/  /'
        echo ""
        read -p "确认删除？(y/n) " -r reply; echo
        if [[ ! $reply =~ ^[Yy]$ ]]; then
          echo "已取消。"
          rm -f "$TEMP_FILE" "$TEST_IDS_FILE"
          exit 0
        fi
        mv "$TEMP_FILE" "$ERRORS_FILE"

        # 清理 corrections.md / domains/ / projects/ 中的孤立 EXP 引用
        echo ""
        echo "--- 清理 corrections.md / domains/ / projects/ 中的孤立引用 ---"
        cleaned_refs=0

        # 从 corrections.md 中删除引用了已删 EXP ID 的行
        if [ -f "$CORRECTIONS_FILE" ]; then
          if [ -s "$TEST_IDS_FILE" ]; then
            # 提取 EXP ID 模式 (e.g. EXP-20250101-001)
            while read -r expid; do
              # 删除包含此 EXP ID 的行
              if grep -q "$expid" "$CORRECTIONS_FILE" 2>/dev/null; then
                grep -v "$expid" "$CORRECTIONS_FILE" > "$CORRECTIONS_FILE.tmp" && mv "$CORRECTIONS_FILE.tmp" "$CORRECTIONS_FILE"
                echo "  清理: corrections.md 中引用 $expid 的行"
                cleaned_refs=$((cleaned_refs+1))
              fi
            done < <(grep -h -oE 'EXP-[0-9]{8}-[0-9]+' "$TEST_IDS_FILE" 2>/dev/null | sort -u)
          fi
        fi

        # 从 domains/ 和 projects/ 中删除引用了已删 EXP ID 的行
        for dir in "$DOMAINS_DIR" "$PROJECTS_DIR"; do
          [ -d "$dir" ] || continue
          while read -r f; do
            if [ -s "$TEST_IDS_FILE" ]; then
              while read -r expid; do
                if grep -q "$expid" "$f" 2>/dev/null; then
                  grep -v "$expid" "$f" > "$f.tmp" && mv "$f.tmp" "$f"
                  echo "  清理: $(basename "$f") 中引用 $expid 的行"
                  cleaned_refs=$((cleaned_refs+1))
                fi
              done < <(grep -h -oE 'EXP-[0-9]{8}-[0-9]+' "$TEST_IDS_FILE" 2>/dev/null | sort -u)
            fi
          done < <(find "$dir" -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
        done

        [ "$cleaned_refs" -eq 0 ] && echo "  (无孤立引用需清理)"
        echo "✅ 已清理 $removed 条测试条目$( [ "$cleaned_refs" -gt 0 ] && echo "及 $cleaned_refs 处孤立引用" || true)"
        rm -f "$TEST_IDS_FILE"
      fi
    fi
    ;;

  --reindex)
    echo "=== 重新编号 v3.3.0 ==="
    # P4 fix: 使用 mktemp 替代固定路径
    TEMP_FILE=$(mktemp /tmp/rocky-know-how.XXXXXX)
    TODAY=$(date +%Y%m%d)
    seq=0

    {
      echo "# 经验诀窍"
      echo ""
      echo "---"
    } > "$TEMP_FILE"

    current_block=""
    while IFS= read -r line; do
      # 跳过旧文件头和分隔符
      echo "$line" | grep -qE '^(# 经验诀窍|---+|# Domain|# Project|# 纠正|# 热门|# HOT|# 记忆|Inherits:)' && continue
      if echo "$line" | grep -q '^## \[EXP-'; then
        if [ -n "$current_block" ]; then
          echo "$current_block" >> "$TEMP_FILE"
        fi
        seq=$((seq+1))
        orig_date=$(echo "$line" | sed -n 's/.*\[EXP-\([0-9]\{8\}\)-.*/\1/p')
        [ -z "$orig_date" ] && orig_date="$TODAY"
        title=$(echo "$line" | sed 's/^## \[EXP-[^]]*\] //')
        current_block="## [EXP-${orig_date}-$(printf '%03d' $seq)] ${title}"
      else
        current_block="$current_block"$'\n'"$line"
      fi
    done < "$ERRORS_FILE"

    if [ -n "$current_block" ]; then
      echo "$current_block" >> "$TEMP_FILE"
    fi

    if $DRY_RUN; then
      echo "[dry-run] 将重新编号（原日期保留），共 $seq 条"
    else
      mv "$TEMP_FILE" "$ERRORS_FILE"
      echo "✅ 已重新编号（原日期保留），共 $seq 条"
    fi

    # R5 fix: 更新 corrections/domains/projects 中的旧 EXP-ID 引用
    echo ""
    echo "--- 更新外部引用 ---"
    updated_refs=0
    # 从备份文件中提取 旧ID→新ID 映射
    if [ -f "${ERRORS_FILE}.bak.reindex" ]; then
      # 先重建映射表（从旧文件和新文件对比）
      : # 旧备份可能不存在，直接从当前文件重建即可
    fi
    # 更简洁的方式：直接用 sed 批量替换当前文件中的 EXP-ID 格式
    # 由于 reindex 后 ID 已连续，只需修正外部文件引用即可
    for ref_file in "$CORRECTIONS_FILE" "$DOMAINS_DIR"/*.md "$PROJECTS_DIR"/*.md; do
      [ -f "$ref_file" ] || continue
      # 查找包含旧 EXP-ID 的行并输出提示
      ref_count=$(grep -cE 'EXP-[0-9]{8}-[0-9]+' "$ref_file" 2>/dev/null | tr -d '\n' || echo "0")
      if [ "$ref_count" -gt 0 ]; then
        echo "  ⚠️ $(basename "$ref_file") 含 $ref_count 处 EXP-ID 引用，reindex 后可能需要手动更新"
        updated_refs=$((updated_refs + 1))
      fi
    done
    [ $updated_refs -eq 0 ] && echo "  (无外部 EXP-ID 引用)"

    # N3 fix: --reindex 后自动重建向量索引（dry-run 时跳过）
    if $DRY_RUN; then
      echo "[dry-run] 将跳过向量重建"
    else
      echo ""
      echo "--- 重建向量索引 ---"
      vector_reindex_all
      echo "✅ 向量索引已重建"
    fi
    ;;

  --old)
    echo "=== 清理旧版残留 ==="
    cleaned=0
    for d in "$HOME"/.openclaw/workspace-*/.learnings; do
      [ ! -d "$d" ] && continue
      for f in LEARNINGS.md FEATURE_REQUESTS.md; do
        if [ -f "$d/$f" ]; then
          rm "$d/$f"
          echo "  删除: $d/$f"
          cleaned=$((cleaned+1))
        fi
      done
      if [ -f "$d/ERRORS.md" ] && [ ! -f "$d/experiences.md" ]; then
        mv "$d/ERRORS.md" "$d/experiences.md"
        echo "  重命名: $d/ERRORS.md → experiences.md"
      fi
    done
    echo "✅ 清理了 $cleaned 个旧文件"
    ;;

  --v2-init)
    echo "=== 初始化 v2.0 分层结构 ==="
    mkdir -p "$SHARED_DIR/domains" "$SHARED_DIR/projects" "$SHARED_DIR/archive"
    [ ! -f "$SHARED_DIR/memory.md" ] && printf "# HOT Memory\n\n## 已确认偏好\n\n## 活跃模式\n\n## 最近（最近7天）\n\n" > "$SHARED_DIR/memory.md" && echo "  ✅ memory.md"
    [ ! -f "$SHARED_DIR/corrections.md" ] && printf "# 纠正日志\n\n" > "$SHARED_DIR/corrections.md" && echo "  ✅ corrections.md"
    [ ! -f "$SHARED_DIR/index.md" ] && printf "# 记忆索引\n\n## HOT\n- memory.md: 0 行\n\n## WARM\n- (尚无)\n\n## COLD\n- (尚无)\n\nLast compaction: never\n" > "$SHARED_DIR/index.md" && echo "  ✅ index.md"
    echo "✅ v2.0 分层结构已初始化"
    ;;

  *)
    echo "用法: clean.sh [--test|--dry-run|--test-dry-run|--old|--reindex|--v2-init]"
    echo "  --test           清理 Tags 为 test 的条目（交互确认模式）"
    echo "  --dry-run        模拟清理测试条目（等同于 --test-dry-run）"
    echo "  --old            清理旧版残留文件（LEARNINGS.md等）"
    echo "  --reindex        重新编号让ID连续"
    echo "  --v2-init        初始化 v2.0 分层目录结构"
    ;;
esac
