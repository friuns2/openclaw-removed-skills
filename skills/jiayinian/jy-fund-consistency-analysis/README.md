# 基金经理观点持仓一致性分析 Skill

## 快速开始

### 1. 安装依赖

```bash
# 安装 mcporter
npm install -g mcporter

# 安装 Python 依赖
pip install -r requirements.txt
```

### 2. 配置 MCP 服务

```bash
# 配置 jy-financedata-api 服务
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"

# 验证配置
mcporter list
```

### 3. 运行分析

```bash
python analyzer_v2.py --manager "张坤" --date "2024-12-31"
```

## 输出

报告将保存到 `consistency_reports/` 目录：
- Markdown 报告：`{基金经理}_{日期}_v2_consistency_report.md`
- HTML 文件：`{基金经理}_{日期}_v2_consistency_report.html`

## 注意事项

- 所有数据来自 MCP API，不编造任何信息
- API 调用可能需要 60-150 秒，请耐心等待
- 首次使用需要申请 JY_API_KEY
