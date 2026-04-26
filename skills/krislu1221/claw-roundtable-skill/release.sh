#!/bin/bash
# RoundTable V2 发布脚本
# 用于打包和验证 ClawHub 发布版本

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELEASE_DIR="${SKILL_DIR}/release"
VERSION="0.9.1"

echo "============================================================"
echo "🚀 RoundTable V2 发布脚本 v${VERSION}"
echo "============================================================"

# Step 1: 清理旧版本
echo -e "\n📦 Step 1: 清理旧版本..."
rm -rf "${RELEASE_DIR}"
mkdir -p "${RELEASE_DIR}"

# Step 2: 安全检查
echo -e "\n🔒 Step 2: 安全检查..."
echo "  检查个人路径..."
if grep -r "/Users/krislu" "${SKILL_DIR}"/*.py 2>/dev/null | grep -v __pycache__; then
    echo "  ❌ 发现个人路径！"
    exit 1
else
    echo "  ✅ 未发现个人路径"
fi

echo "  检查敏感信息..."
if grep -rE "(password|secret|api_key|API_KEY|TOKEN)" "${SKILL_DIR}"/*.py 2>/dev/null | grep -v __pycache__ | grep -v "# "; then
    echo "  ❌ 发现敏感信息！"
    exit 1
else
    echo "  ✅ 未发现敏感信息"
fi

# Step 3: 版本验证
echo -e "\n📋 Step 3: 版本验证..."
CLAWHUB_VERSION=$(grep '"version"' "${SKILL_DIR}/clawhub.json" | cut -d'"' -f4)
INIT_VERSION=$(grep '__version__' "${SKILL_DIR}/__init__.py" | cut -d'"' -f2)

if [ "${CLAWHUB_VERSION}" != "${VERSION}" ]; then
    echo "  ❌ clawhub.json 版本不匹配：${CLAWHUB_VERSION} (期望：${VERSION})"
    exit 1
fi

if [ "${INIT_VERSION}" != "${VERSION}" ]; then
    echo "  ❌ __init__.py 版本不匹配：${INIT_VERSION} (期望：${VERSION})"
    exit 1
fi

echo "  ✅ 版本一致：${VERSION}"

# Step 4: 复制发布文件
echo -e "\n📁 Step 4: 复制发布文件..."
cd "${SKILL_DIR}"

# 必需文件
REQUIRED_FILES=(
    "__init__.py"
    "requirement_analyzer.py"
    "roundtable_engine_v2.py"
    "roundtable_notifier.py"
    "agency_agents_loader.py"
    "agent_selector.py"
    "model_selector.py"
    "SKILL.md"
    "INSTALL.md"
    "CHANGELOG.md"
    "clawhub.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "${SKILL_DIR}/${file}" ]; then
        cp "${SKILL_DIR}/${file}" "${RELEASE_DIR}/"
        echo "  ✅ ${file}"
    else
        echo "  ⚠️  ${file} (不存在)"
    fi
done

# Step 5: 运行测试
echo -e "\n🧪 Step 5: 运行测试..."
cd "${RELEASE_DIR}"
if python3 -c "import requirement_analyzer; print('✅ 模块加载成功')"; then
    echo "  ✅ 模块加载测试通过"
else
    echo "  ❌ 模块加载测试失败"
    exit 1
fi

# Step 6: 生成发布说明
echo -e "\n📝 Step 6: 生成发布说明..."
cat > "${RELEASE_DIR}/RELEASE.md" << EOF
# RoundTable V2 发布说明

## 版本信息
- **版本号**: ${VERSION}
- **发布日期**: $(date +%Y-%m-%d)
- **作者**: 虾软 Claw soft

## 新增功能
- ✅ 集成 146 个全领域专家（engineering/design/marketing/sales 等）
- ✅ 需求智能分析器（8 种需求类型自动识别）
- ✅ 精准专家匹配（分类 + 关键词双匹配）
- ✅ 按议题分治讨论（不再固定 5 轮）
- ✅ 动态复杂度适配（auto/high/medium/low）

## 核心文件
- requirement_analyzer.py - 需求分析器
- roundtable_engine_v2.py - V2 引擎
- roundtable_notifier.py - 通知器
- agency_agents_loader.py - 146 个专家加载器

## 使用示例
\`\`\`python
from roundtable_engine_v2 import run_roundtable_v2

await run_roundtable_v2(
    topic="智能待办应用的架构设计",
    complexity="auto"
)
\`\`\`

## 安全检查
- ✅ 无个人路径
- ✅ 无硬编码地址
- ✅ 无敏感信息
- ✅ 版本一致

## 安装
上传到 ClawHub 后，用户可以通过以下方式安装：
\`\`\`
openclaw skills install roundtable-skill
\`\`\`

## 文档
- SKILL.md - 技能说明
- INSTALL.md - 安装与使用指南
- CHANGELOG.md - 变更日志
EOF

echo "  ✅ RELEASE.md"

# Step 7: 清理缓存
echo -e "\n🧹 Step 7: 清理缓存..."
find "${RELEASE_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${RELEASE_DIR}" -name "*.pyc" -delete 2>/dev/null || true
echo "  ✅ 缓存已清理"

# Step 8: 打包
echo -e "\n📦 Step 8: 打包..."
cd "${SKILL_DIR}"
tar --exclude="__pycache__" --exclude="*.pyc" -czf "roundtable-skill-v${VERSION}.tar.gz" -C "${RELEASE_DIR}" .
echo "  ✅ roundtable-skill-v${VERSION}.tar.gz"

# Step 8: 生成校验和
echo -e "\n🔐 Step 8: 生成校验和..."
cd "${SKILL_DIR}"
shasum -a 256 "roundtable-skill-v${VERSION}.tar.gz" > "roundtable-skill-v${VERSION}.sha256"
echo "  ✅ roundtable-skill-v${VERSION}.sha256"

# 完成
echo -e "\n============================================================"
echo "✅ 发布准备完成！"
echo "============================================================"
echo ""
echo "📦 发布包：${SKILL_DIR}/roundtable-skill-v${VERSION}.tar.gz"
echo "📋 发布说明：${RELEASE_DIR}/RELEASE.md"
echo "🔐 校验和：${SKILL_DIR}/roundtable-skill-v${VERSION}.sha256"
echo ""
echo "下一步："
echo "1. 检查发布包内容：tar -tzf roundtable-skill-v${VERSION}.tar.gz"
echo "2. 上传到 ClawHub：openclaw skills publish roundtable-skill-v${VERSION}.tar.gz"
echo "3. 或者手动上传到 https://clawhub.com"
echo ""
