#!/bin/bash
# ============================================================
# 更新经验脚本 - v3.3.0
# 替换已有经验的解决方案
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LEARNINGS_DIR="$HOME/.openclaw/.learnings"
ERRORS_FILE="$LEARNINGS_DIR/experiences.md"

if [ $# -lt 3 ]; then
    echo "用法: $0 <经验ID> <新解决方案> <新预防措施> [新标签]"
    echo "示例: $0 EXP-20260423-001 '新方案...' '预防措施...' 'docker,nginx'"
    exit 1
fi

EXP_ID="$1"
NEW_SOLUTION="$2"
NEW_PREVENTION="$3"
NEW_TAGS="${4:-update}"

# 校验：经验ID不能为空且格式正确
if [ -z "$EXP_ID" ]; then
    echo "❌ 错误: 经验ID不能为空"
    exit 1
fi
if ! echo "$EXP_ID" | grep -qE '^EXP-[0-9]+-[0-9]+$'; then
    echo "❌ 错误: 经验ID格式无效: $EXP_ID (期望 EXP-YYYYMMDD-NNN)"
    exit 1
fi

# 校验：新方案不能为空
if [ -z "$NEW_SOLUTION" ]; then
    echo "❌ 错误: 新解决方案不能为空"
    exit 1
fi

# 校验：预防措施不能为空
if [ -z "$NEW_PREVENTION" ]; then
    echo "❌ 错误: 预防措施不能为空"
    exit 1
fi

# 校验：路径穿越检测
for val in "$EXP_ID" "$NEW_SOLUTION" "$NEW_PREVENTION" "$NEW_TAGS"; do
    if [[ "$val" == *../* || "$val" == *..\\\\* ]]; then
        echo "❌ 错误: 参数包含非法字符"
        exit 1
    fi
done

if [ ! -f "$ERRORS_FILE" ]; then
    echo "错误: 经验文件不存在: $ERRORS_FILE"
    exit 1
fi

# 检查ID是否存在
if ! grep -qF "## [${EXP_ID}]" "$ERRORS_FILE"; then
    echo "错误: 经验ID不存在: $EXP_ID"
    exit 1
fi

# 找到该经验的位置
EXP_START=$(grep -nF "## [${EXP_ID}]" "$ERRORS_FILE" | head -1 | cut -d: -f1)
if [ -z "$EXP_START" ]; then
    echo "错误: 无法找到经验ID: $EXP_ID"
    exit 1
fi

# 找到下一个经验的开始位置（或者文件末尾）
NEXT_EXP=$(tail -n +$((EXP_START+1)) "$ERRORS_FILE" | grep -n "^## \[" | head -1 | cut -d: -f1)
if [ -n "$NEXT_EXP" ]; then
    EXP_END=$((EXP_START + NEXT_EXP - 2))
else
    EXP_END=$(wc -l < "$ERRORS_FILE")
fi

# 提取现有经验块
EXP_BLOCK=$(sed -n "${EXP_START},${EXP_END}p" "$ERRORS_FILE")

# 更新解决方案部分
if echo "$EXP_BLOCK" | grep -q "### 正确方案"; then
    # 替换原有方案
    TEMP_FILE=$(mktemp)
    sed -n "1,${EXP_START}p" "$ERRORS_FILE" > "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    echo "### 正确方案" >> "$TEMP_FILE"
    echo "$NEW_SOLUTION" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    echo "### 预防" >> "$TEMP_FILE"
    echo "$NEW_PREVENTION" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    if echo "$EXP_BLOCK" | grep -q "\*\*Tags\*\*:"; then
        echo "**Tags**: ${NEW_TAGS},updated" >> "$TEMP_FILE"
        echo "" >> "$TEMP_FILE"
    fi
    sed -n "${EXP_END}p" "$ERRORS_FILE" >> "$TEMP_FILE"
    mv "$TEMP_FILE" "$ERRORS_FILE"
else
    echo "错误: 无法解析经验格式"
    exit 1
fi

echo "✅ 经验已更新: $EXP_ID"
echo "新方案: $NEW_SOLUTION"
echo "新预防: $NEW_PREVENTION"
