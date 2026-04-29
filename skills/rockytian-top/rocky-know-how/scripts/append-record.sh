#!/bin/bash
# ============================================================
# 追加经验脚本 - v3.3.0
# 在已有经验后追加新的解决方式
# ============================================================

set -e

LEARNINGS_DIR="$HOME/.openclaw/.learnings"
ERRORS_FILE="$LEARNINGS_DIR/experiences.md"

if [ $# -lt 3 ]; then
    echo "用法: $0 <经验ID> <新方式> <标签>"
    echo "示例: $0 EXP-20260423-001 '新方式：docker exec -it ...' 'docker补充'"
    exit 1
fi

EXP_ID="$1"
NEW_METHOD="$2"
NEW_TAG="$3"

if [ ! -f "$ERRORS_FILE" ]; then
    echo "错误: 经验文件不存在"
    exit 1
fi

# 检查 ID 是否存在
if ! grep -q "^## \[${EXP_ID}\] " "$ERRORS_FILE"; then
    echo "错误: 经验ID不存在: $EXP_ID"
    exit 1
fi

# 使用 awk 精确插入新方式
# 策略：用 entry_start_line 记录进入条目的行号，用 index() 匹配前缀
awk -v exp_id="$EXP_ID" -v new_method="$NEW_METHOD" -v new_tag="$NEW_TAG" '
BEGIN {
    in_target = 0
    entry_start_line = 0
    after_prevention = 0
    inserted = 0
    # 匹配 ## [EXP-xxx] 开头，后跟空格
    target_prefix = "## [" exp_id "] "
}

# 匹配目标条目开始（使用 index 匹配前缀）
index($0, target_prefix) == 1 {
    in_target = 1
    entry_start_line = FNR
    print
    next
}

# 在条目内，遇到下一个条目（且不是当前行）
in_target == 1 && /^## \[/ && FNR > entry_start_line {
    if (!inserted) {
        printf "\n### 新增方式\n%s\n\n**Tags**: %s\n", new_method, new_tag
        inserted = 1
    }
    in_target = 0
    entry_start_line = 0
    print
    next
}

# 在条目内，遇到 ### 预防
in_target == 1 && /^### 预防/ {
    print
    after_prevention = 1
    next
}

# 预防内容行（直到遇到空行或下一个章节标记）
in_target == 1 && after_prevention == 1 {
    if (/^[ \t]*$/ || /^### / || /^\*\*Tags\*\*/ || /^---/) {
        after_prevention = 0
        if (!inserted) {
            printf "\n### 新增方式\n%s\n\n**Tags**: %s\n", new_method, new_tag
            inserted = 1
        }
    }
    print
    next
}

# 条目内其他内容
in_target == 1 {
    print
    next
}

# 非条目内容
{
    print
}
' "$ERRORS_FILE" > "${ERRORS_FILE}.tmp"

# 替换原文件
mv "${ERRORS_FILE}.tmp" "$ERRORS_FILE"
echo "✅ 已追加新方式到经验: $EXP_ID"
echo "新方式: $NEW_METHOD"
