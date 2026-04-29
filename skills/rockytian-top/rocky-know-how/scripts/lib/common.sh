#!/bin/bash
# rocky-know-how 公共函数库 v3.3.0
# 被 search.sh / record.sh 等脚本 source

# 获取状态目录（支持多网关实例）
get_state_dir() {
  [ -n "$OPENCLAW_STATE_DIR" ] && echo "$OPENCLAW_STATE_DIR" || echo "$HOME/.openclaw"
}

# 获取共享经验目录
get_shared_dir() {
  echo "$(get_state_dir)/.learnings"
}

# 获取锁目录路径
get_lock_dir() {
  local lock_name="$1"
  echo "$(get_shared_dir)/.lock-${lock_name}"
}

# R4 fix: 获取 mkdir 原子锁（兼容 macOS/Linux）
acquire_lock() {
  local lock_dir="$1"
  local max_retries="${2:-50}"
  local retry=0
  while [ $retry -lt $max_retries ]; do
    if mkdir "$lock_dir" 2>/dev/null; then
      return 0
    fi
    sleep 0.1
    retry=$((retry + 1))
  done
  echo "⚠️ 获取锁超时: $lock_dir" >&2
  return 1
}

# R4 fix: 释放锁
release_lock() {
  local lock_dir="$1"
  rmdir "$lock_dir" 2>/dev/null
}
