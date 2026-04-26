# Official Document Writer（公文写作助手）

基于 OpenClaw 的公文写作 Skill，集成深知可信搜索、公文撰写、Word 排版，支持 15 种法定公文和多种事务文书。

## 核心特性

- **政策搜索**：调用深知可信搜索，从权威政策库检索法律法规、地方经验等素材，每条引用可溯源
- **智能撰写**：根据公文类型自动匹配格式规范，生成大纲确认后正式写作
- **Word 排版**：符合《党政机关公文格式》GB/T 9704-2012 国标，支持普通格式和红头格式
- **版本管理**：自动版本编号，避免文件覆盖
- **会议纪要**：支持党组会议纪要、局长办公会议纪要、工作会议纪要

## 支持文种

### 法定公文（15种）
决议、命令、公报、公告、通告、意见、通知、通报、报告、请示、批复、议案、函、纪要

### 事务文书
工作总结、年度总结、学习计划、发言稿、讲话稿、管理办法、实施细则、汇报材料等

## 快速开始

### 1. 安装依赖

```bash
pip3 install python-docx
```

### 2. 配置搜索（可选但推荐）

在 Skill 根目录手动创建 `config.ini`：

```bash
cat > config.ini << 'EOF'
[dkag]
# 深知可信搜索接口配置
# 接口地址: https://open.dknowc.cn/dependable/search/
# 请求方式: POST

# API 密钥（从 MAAS 平台获取）
api_key=你的API Key

# 注意：现在只需要配置 API Key，不需要配置 appid
# 接口使用固定地址，无需额外配置
EOF
```

或手动新建文件并填写：

```ini
[dkag]
# 深知可信搜索接口配置
# 接口地址: https://open.dknowc.cn/dependable/search/
# 请求方式: POST

# API 密钥（从 MAAS 平台获取）
api_key=你的API Key

# 注意：现在只需要配置 API Key，不需要配置 appid
# 接口使用固定地址，无需额外配置
```

> 如不配置搜索，写作时将跳过素材检索步骤。

### 3. 开始使用

在 OpenClaw 中直接对话即可，例如：

- "帮我写一份关于XX的通知"
- "根据以下来函写一份复函"
- "写一份会议纪要"

## 获取 API Key

深知可信搜索 API 通过 MAAS 平台提供：

1. 访问 MAAS 平台注册账号
2. 在控制台创建 API Key
3. 填入 `config.ini` 的 `api_key` 字段

## 目录结构

```
official-doc-writer/
├── SKILL.md              # Skill 核心逻辑（AI 执行流程）
├── config/
│   ├── format.json       # 排版格式配置（国标默认值）
├── config.ini            # 搜索 API 配置（用户手动创建，不随 skill 发布）
├── scripts/
│   ├── dkag_search.py    # 深知可信搜索接口
│   ├── format_document.py    # 公文排版脚本（普通格式）
│   ├── template_generator.py # 红头文件生成器
│   └── merge_search_results.py # 搜索结果合并
├── templates/            # 红头文件模板（占位符可替换）
│   ├── 上行文件格式-{红头,表尾}.docx   # 请示、报告
│   ├── 下行文件格式-{红头,表尾}.docx   # 通知、通报
│   ├── 函件（普通）格式-{红头,表尾}.docx # 函、复函
│   ├── 党组会议纪要-{红头,表尾}.docx
│   ├── 局长办公会议纪要-{红头,表尾}.docx
│   └── 工作会议纪要-{红头,表尾}.docx
├── reference/
│   └── standards/        # 各文种写作标准（15种+通用）
└── README.md
```

## 红头模板

`templates/` 目录下提供了上行文、下行文、函件、会议纪要的红头和表尾模板，使用【占位符】标记可替换内容：

- 【发文机关】【发文字号】【密级】【紧急程度】
- 【公开方式】【抄送】【签发人】
- 【印发日期】【成文日期】
- 【纪要编号】【出席人员】【列席人员】【印发单位】

模板会根据用户输入的单位信息自动替换占位符。

## 依赖

- Python 3.x
- python-docx
- OpenClaw

## 许可

MIT
