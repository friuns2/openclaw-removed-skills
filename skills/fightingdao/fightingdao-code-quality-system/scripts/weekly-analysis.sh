#!/bin/bash
# 每周代码质量分析任务
# 自动计算本周四的日期作为周期值

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="/Users/zhangdi/work/codeCap/代码质量分析系统/analysis-output"

# 获取本周四日期（由 Node 脚本自动计算）
THURSDAY_DATE=$(node -e "
const now = new Date();
const dayOfWeek = now.getDay();
const daysToThursday = dayOfWeek <= 4 ? (4 - dayOfWeek) : (4 - dayOfWeek + 7);
const thursday = new Date(now);
thursday.setDate(now.getDate() + daysToThursday);
console.log(thursday.toISOString().slice(0, 10).replace(/-/g, ''));
")

LOG_FILE="${LOG_DIR}/weekly-${THURSDAY_DATE}.log"

echo "=========================================="
echo "每周代码质量分析"
echo "周期值: ${THURSDAY_DATE}"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

mkdir -p "${LOG_DIR}"

# 执行分析（使用 v2 版本脚本）
cd "${SCRIPT_DIR}"
echo "开始分析..." | tee -a "${LOG_FILE}"
node analyze-code-v2.js ${THURSDAY_DATE} 2>&1 | tee -a "${LOG_FILE}"

echo "分析完成！$(date '+%Y-%m-%d %H:%M:%S')" | tee -a "${LOG_FILE}"