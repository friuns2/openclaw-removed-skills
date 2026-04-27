# jy-asset-allocation-report-skill

大类资产配置报告生成技能 - 基于恒生聚源 (gildata) MCP 金融数据库

## 快速开始

### 1. 安装依赖

```bash
npm install -g mcporter
```

### 2. 配置 MCP 服务

```bash
# 获取 JY_API_KEY 后配置
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
```

### 3. 验证配置

```bash
mcporter list
```

### 4. 使用技能

在对话中触发：
- "生成 2026 年 3 月资产配置报告"
- "生成月度资产配置报告"
- "大类资产配置建议"

## 目录结构

```
jy-asset-allocation-report-skill/
├── SKILL.md              # 技能定义和使用说明
├── README.md             # 本文件
├── references/
│   ├── template.md       # 报告模板
│   └── data_sources.md   # MCP 工具使用说明
└── examples/
    └── sample_report.md  # 示例报告
```

## JY_API_KEY 申请

向恒生聚源官方邮箱发送邮件申请：
- **邮箱：** datamap@gildata.com
- **标题：** 数据地图 KEY 申请 -XX 公司 - 申请人姓名

详见 `SKILL.md` 中的"环境检查与配置"章节。

## 输出说明

- **默认格式：** Markdown
- **可选格式：** PDF（需调用 pdf skill 转换）
- **存储位置：** `~/桌面/资产配置报告输出/`

## 免责声明

本报告仅供研究参考，**NOT investment advice**。市场有风险，投资需谨慎。
