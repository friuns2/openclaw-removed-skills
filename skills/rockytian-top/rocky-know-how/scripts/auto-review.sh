#!/bin/bash
# ============================================================
# 全自动草稿审核脚本 - v2.1
# 草稿 → AI判断 → AI优化增强 → 同类检测 → 自动新增/追加 → 写入experiences.md → 自动晋升
# ============================================================

# 从 set -e 改为显式错误处理
set -E

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LEARNINGS_DIR="$HOME/.openclaw/.learnings"
DRAFTS_DIR="$LEARNINGS_DIR/drafts"
ARCHIVE_DIR="$DRAFTS_DIR/archive"
LOG_FILE="$LEARNINGS_DIR/.auto-review.log"

mkdir -p "$ARCHIVE_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查依赖
check_deps() {
    for cmd in record.sh append-record.sh search.sh; do
        if [ ! -f "$SCRIPT_DIR/$cmd" ]; then
            log "ERROR: Missing dependency: $SCRIPT_DIR/$cmd"
            exit 1
        fi
    done
}

# 处理单个草稿
process_draft() {
    local draft_file="$1"
    local draft_id=$(basename "$draft_file" .json)
    
    log "=== Processing draft: $draft_id ==="
    
    # 读取草稿内容
    problem=$(python3 -c "import json; print(json.load(open('$draft_file')).get('problem',''))" 2>/dev/null || echo "")
    tried=$(python3 -c "import json; print(json.load(open('$draft_file')).get('tried',''))" 2>/dev/null || echo "")
    solution=$(python3 -c "import json; print(json.load(open('$draft_file')).get('solution',''))" 2>/dev/null || echo "")
    prevention=$(python3 -c "import json; print(json.load(open('$draft_file')).get('prevention',''))" 2>/dev/null || echo "")
    tags=$(python3 -c "import json; print(','.join(json.load(open('$draft_file')).get('tags',[])))" 2>/dev/null || echo "draft")
    area=$(python3 -c "import json; print(json.load(open('$draft_file')).get('area','global'))" 2>/dev/null || echo "global")
    
    # 如果没有AI生成的prevention，使用默认值
    if [ -z "$prevention" ]; then
        prevention="No similar problems"
    fi
    
    if [ -z "$problem" ]; then
        log "WARN: Draft empty, skipping"
        return
    fi
    
    # 跳过 solution 不完整的草稿（防止写入"待补充"到 experiences.md）
    if [ -z "$solution" ] || [ "$solution" = "待补充" ]; then
        log "SKIP: solution 未完成 (待补充)，跳过此草稿"
        mv "$draft_file" "$ARCHIVE_DIR/"
        log "Archived: $draft_id (skipped - incomplete)"
        log ""
        return
    fi
    
    # 提取关键词用于搜索同类
    keywords=$(echo "$problem" | sed 's/[^a-zA-Z0-9 ]/ /g' | awk '{print $1,$2}' | head -2 | tr ' ' '\n' | head -2 | tr '\n' ' ' | sed 's/ $//')
    
    log "Problem: $problem"
    log "Tags: $tags"
    log "Prevention: $prevention"
    log "Keywords: $keywords"
    
    # 搜索同类经验
    similar_ids=$(bash "$SCRIPT_DIR/search.sh" $keywords 2>/dev/null | grep -oE 'EXP-[0-9]{8}-[0-9]{3}' | head -5 || echo "")
    
    if [ -n "$similar_ids" ]; then
        # 有同类经验 → 追加新方式
        first_id=$(echo "$similar_ids" | head -1)
        log "Found similar: $first_id"
        log "Appending solution..."
        
        bash "$SCRIPT_DIR/append-record.sh" "$first_id" "$solution" "$tags" 2>&1 | tee -a "$LOG_FILE"
        
        # 移动草稿到归档
        mv "$draft_file" "$ARCHIVE_DIR/"
        log "Done: $draft_id -> $first_id"
    else
        # 无同类经验 → 新增
        log "No similar found, creating new..."
        
        bash "$SCRIPT_DIR/record.sh" "$problem" "$tried" "$solution" "$prevention" "$tags" "$area" 2>&1 | tee -a "$LOG_FILE"
        
        # 移动草稿到归档
        mv "$draft_file" "$ARCHIVE_DIR/"
        log "Done: $draft_id (new)"
    fi
    
    log ""
}

# 主流程
main() {
    log "=========================================="
    log "AUTO REVIEW START"
    log "=========================================="
    
    check_deps
    
    DRAFTS=$(find "$DRAFTS_DIR" -name "draft-*.json" -type f 2>/dev/null | wc -l | tr -d ' ')
    log "Found $DRAFTS drafts"
    
    if [ "$DRAFTS" -eq 0 ]; then
        log "No drafts to process"
        exit 0
    fi
    
    # 处理每个草稿
    for f in "$DRAFTS_DIR"/draft-*.json; do
        [ -f "$f" ] || continue
        process_draft "$f"
    done
    
    log "=========================================="
    log "AUTO REVIEW COMPLETE"
    log "=========================================="
    
    # 自动晋升检查（Tag使用≥3次 → 写入TOOLS.md）
    log "Running auto-promote..."
    bash "$SCRIPT_DIR/promote.sh" 2>&1 | tee -a "$LOG_FILE" || true
    
    # 显示统计
    bash "$SCRIPT_DIR/stats.sh" 2>/dev/null | tail -5
}

main "$@"
