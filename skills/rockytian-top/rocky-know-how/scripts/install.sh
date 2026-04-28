#!/bin/bash
# rocky-know-how 一键安装脚本 v3.3.0
set -e

VERSION="3.3.0"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPTS_DIR/lib/common.sh"

STATE_DIR=$(get_state_dir)
SHARED_DIR=$(get_shared_dir)

echo "╔════════════════════════════════════════════╗"
echo "║  rocky-know-how 一键安装 v${VERSION}         ║"
echo "║  经验诀窍技能                              ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# 1. 创建目录结构
echo "📂 创建经验诀窍目录..."
mkdir -p "$SHARED_DIR"/{domains,projects,archive}
echo "   ✅ $SHARED_DIR/"

# 2. 初始化文件
echo ""
echo "📄 初始化存储文件..."
init_file() {
  [ -f "$1" ] && { echo "   ⏭️  $(basename $1) 已存在"; return; }
  printf "%s" "$2" > "$1"
  echo "   ✅ $(basename $1)"
}

init_file "$SHARED_DIR/memory.md" "# HOT Memory

## 已确认偏好

## 活跃模式

## 最近（最近7天）

"

init_file "$SHARED_DIR/experiences.md" "# 经验诀窍

---

"

init_file "$SHARED_DIR/corrections.md" "# 纠正日志

## $(date '+%Y-%m-%d')

"

init_file "$SHARED_DIR/reflections.md" "# 自我反思日志

## (新条目在此)
"

init_file "$SHARED_DIR/heartbeat-state.md" "# Self-Improving Heartbeat State

last_heartbeat_started_at: never
last_reviewed_change_at: never
last_heartbeat_result: never

## Last actions
- none yet
"

init_file "$SHARED_DIR/index.md" "# 记忆索引

## HOT
- memory.md: 0 行

## WARM
- (尚无)

## COLD
- (尚无归档)

Last compaction: never
"

# 3. 配置 Hook
echo ""
echo "⚙️  配置 Hook..."
configure_hook() {
  local oc_json="$STATE_DIR/openclaw.json"
  local hook_path="$SKILL_DIR/hooks"

  if [ ! -f "$oc_json" ]; then
    echo "   ⚠️  未找到 openclaw.json，跳过 Hook 配置"
    return 0
  fi

  python3 << PYEOF
import json, os, shutil

f = '$oc_json'
bak = f + '.bak.install'
shutil.copy(f, bak)

with open(f, 'r') as fp:
    data = json.load(fp)

# 确保结构存在
data.setdefault('hooks', {}).setdefault('internal', {}).setdefault('load', {}).setdefault('extraDirs', [])
data['hooks']['internal'].setdefault('entries', {})

hook_path = '$hook_path'

# 添加 extraDirs
if hook_path not in data['hooks']['internal']['load']['extraDirs']:
    data['hooks']['internal']['load']['extraDirs'].append(hook_path)

# 注册 4 个事件
events = ['agent:bootstrap', 'before_compaction', 'after_compaction', 'before_reset']
for evt in events:
    data['hooks']['internal']['entries'].setdefault(evt, {})['rocky-know-how'] = {}

with open(f, 'w') as fp:
    json.dump(data, fp, indent=2, ensure_ascii=False)

print('   ✅ Hook 已注册 4 个事件')
print('   ✅ 备份: ' + bak)
PYEOF
}

configure_hook

# 4. 重启网关
echo ""
echo "🔄 重启网关使配置生效..."
restart_gateway() {
  local pid=$(pgrep -f "openclaw-gateway" | head -1)
  if [ -n "$pid" ]; then
    kill -9 $pid 2>/dev/null || true
    sleep 2
  fi
  # 使用 launchctl 重启
  launchctl list | grep -q "ai.openclaw.gateway" && {
    launchctl kickstart -k gui/$(launchctl list | grep "ai.openclaw.gateway" | awk '{print $1}') 2>/dev/null || true
  }
  sleep 3
  # 检查是否运行
  pgrep -f "openclaw-gateway" > /dev/null && echo "   ✅ 网关已重启" || echo "   ⚠️  网关重启失败，请手动执行: openclaw gateway restart"
}

restart_gateway 2>/dev/null || {
  echo "   ⚠️  自动重启失败，可手动执行: openclaw gateway restart"
}

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  ✅ 安装完成！                            ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "📊 统计: bash $SCRIPTS_DIR/stats.sh"
echo "🔍 搜索: bash $SCRIPTS_DIR/search.sh \"关键词\""
echo "📝 写入: bash $SCRIPTS_DIR/record.sh ..."
echo ""
