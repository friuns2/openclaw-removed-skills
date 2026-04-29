#!/bin/bash
# rocky-know-how 卸载脚本 v3.3.0
# 用法: bash uninstall.sh
# 本脚本只删除数据文件，不修改配置文件。

set -e

echo "╔════════════════════════════════════════════╗"
echo "║  rocky-know-how 卸载脚本 v3.3.0          ║"
echo "╚════════════════════════════════════════════╝"
echo ""

read -p "确定要卸载 rocky-know-how 吗？(y/N) " confirm
[[ "$confirm" != "y" && "$confirm" != "Y" ]] && { echo "取消卸载"; exit 0; }

echo "⚙️  请手动从 openclaw.json 移除 rocky-know-how 的 hooks.internal.load.extraDirs 条目"
echo ""

read -p "是否删除经验诀窍数据？(y/N) " confirm_data
if [[ "$confirm_data" == "y" || "$confirm_data" == "Y" ]]; then
  SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
  source "$SCRIPTS_DIR/lib/common.sh"
  STATE_DIR=$(get_state_dir)
  SHARED_DIR=$(get_shared_dir)
  if [ -d "$SHARED_DIR" ]; then
    echo "🗑️  删除经验诀窍数据..."
    rm -rf "$SHARED_DIR"
    echo "✅ 已删除 $SHARED_DIR"
  fi
else
  echo "ℹ️  保留数据（$SHARED_DIR）"
fi

echo ""
echo "卸载后请重启 Gateway: openclaw gateway restart"
echo ""
echo "🎉 卸载完成"
