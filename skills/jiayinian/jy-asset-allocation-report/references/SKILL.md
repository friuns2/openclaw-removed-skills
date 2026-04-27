---
name: jy-asset-allocation-report
description: |
  专业大类资产配置报告生成器，基于恒生聚源 (gildata) MCP 金融数据库生成券商风格月度/季度配置报告。
  覆盖宏观经济分析、大类资产配置建议、行业配置主线、风险管理措施等核心模块，所有数据可溯源、带时间戳。
  
  **Triggers when user mentions:**
  - "生成资产配置报告"
  - "月度配置建议"
  - "大类资产配置"
  - "资产配置月报"
  - "生成{YYYY 年 MM 月}资产配置报告"
  - "投资组合配置"
  - "资产配置策略"
  - "季度配置报告"
  - "资产权重配置"
  
  **Output:** Markdown/PDF 格式报告，保存至 ~/桌面/资产配置报告输出/
  **Data Sources:** jy-financedata-tool (研报 + 宏观数据), jy-financedata-api (金融数据查询)
  **Auth:** 需要 JY_API_KEY 进行 MCP 服务鉴权
  **NOT investment advice.**
  
  Professional asset allocation report generator based on GILData MCP financial database, 
  producing broker-style monthly/quarterly allocation reports. Covers macroeconomic analysis, 
  asset class allocation recommendations, industry allocation themes, and risk management measures. 
  All data is traceable with timestamps.
  
  **Triggers:** "generate asset allocation report", "monthly allocation advice", 
  "strategic asset allocation", "portfolio allocation", "asset allocation strategy"
  
  **Output:** Markdown/PDF format reports saved to ~/Desktop/Asset Allocation Reports/
  **NOT investment advice.**
metadata:
  openclaw:
    requires:
      bins: ["node", "npm", "mcporter"]
    install:
      - id: install-mcporter
        kind: node
        package: mcporter
        label: Install mcporter via npm
---

# 【大类资产配置报告】

专业大类资产配置报告生成技能，基于恒生聚源 (gildata) MCP 金融数据库，生成券商风格的月度/季度资产配置报告。

## 功能范围

本技能支持以下功能：

| 功能 | 说明 |
|------|------|
| 月度资产配置报告 | 生成指定月份的完整资产配置报告 |
| 季度资产配置报告 | 生成指定季度的配置报告 |
| 行业专项配置报告 | 针对特定行业的资产配置建议 |
| 宏观数据查询 | 获取最新 GDP、CPI、PMI 等宏观经济指标 |
| 研报观点汇总 | 获取近 3 个月券商研报核心观点 |
| 资产权重建议 | 股票、债券、商品、现金等大类资产配置权重 |
| 情景推演分析 | 乐观/悲观/基准三种情景下的配置调整建议 |

## 查询建议

**查询需要具备的要素：**
- 报告类型：月度/季度/行业专项
- 时间范围：如"2026 年 3 月"、"2025 年第四季度"
- （可选）行业主题：如"科技行业"、"消费行业"

**查询写法：**
```
生成 {时间} 资产配置报告
生成{YYYY 年 MM 月}大类资产配置报告
生成{行业}资产配置报告
```

## 查询示例

```bash
# 生成当月报告
"生成 2026 年 3 月资产配置报告"

# 生成指定月份报告
"生成 2025 年 12 月大类资产配置报告"

# 生成季度报告
"生成 2025 年第四季度资产配置报告"

# 生成行业专项报告
"生成科技行业资产配置报告"
"生成消费行业月度配置建议"

# 英文触发
"generate asset allocation report for March 2026"
"monthly portfolio allocation advice"
```

## 环境检查与配置

**⚠️ 每次使用本技能前，必须先检查 mcporter 安装和 MCP 服务配置状态！**

### 步骤 1：检查 mcporter 是否安装

```bash
mcporter --version
```

**如未安装**，按以下流程安装：

```bash
# 1. 通过 npm 全局安装
npm install -g mcporter

# 2. 验证安装
mcporter --version
```

### 步骤 2：检查 MCP 服务配置

```bash
# 列出所有已配置的 MCP 服务
mcporter list
```

**预期输出**（必须包含以下两个服务）：
- `jy-financedata-tool`
- `jy-financedata-api`

**如服务未配置**，需要获取 JY_API_KEY 并配置：

#### 2.1 获取 JY_API_KEY

向恒生聚源官方邮箱发送邮件申请签发数据地图 JY_API_KEY，用于接口鉴权。

**申请邮箱：** datamap@gildata.com

**邮件标题：** 数据地图 KEY 申请 -XX 公司 - 申请人姓名

**正文模板：**
```
• 姓名：
• 手机号：
• 公司/单位全称：
• 所属部门：
• 岗位：
• MCP_KEY 申请用途：
• Skill 申请列表：
• 是否需要 Skill 安装包：（是，邮件提供/否，自行下载）
• 其他补充说明（可选）：
```

申请通过后，恒生聚源将默认发送【工具版和接口版】KEY。

#### 2.2 配置 MCP 服务

```bash
# 配置 jy-financedata-tool 服务
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"

# 配置 jy-financedata-api 服务
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
```

#### 2.3 验证配置

```bash
mcporter list
```

确认两个服务均显示为 `connected` 状态。

### 步骤 3：测试数据获取

```bash
# 测试研报查询
mcporter call jy-financedata-tool.FinancialResearchReport --query "资产配置研报"

# 测试宏观数据查询
mcporter call jy-financedata-tool.MacroIndustryData --query "GDP CPI PMI 最新数据"
```

如返回数据正常，则配置完成。

## 工作流程

### 1. 确认需求
确认报告时间范围和类型（月度/季度/行业专项）。

### 2. 环境检查
执行环境检查流程，确保 mcporter 和 MCP 服务配置正常。

### 3. 数据收集
使用 `mcporter call` 调用以下工具获取数据：

| 工具 | MCP 服务 | 用途 |
|------|----------|------|
| `FinancialResearchReport` | jy-financedata-tool | 获取近 3 个月券商研报观点 |
| `MacroIndustryData` | jy-financedata-tool | 获取最新宏观经济数据 |
| `FinQuery` | jy-financedata-api | 获取资产类别价格/估值数据 |
| `FinGeneralQuery` | jy-financedata-api | 综合金融数据查询 |

### 4. 分析研判
按模板结构分析数据，研报时效性权重按发布时间倒序。

### 5. 生成报告
输出 Markdown 格式报告，包含：
- 报告摘要（核心观点表格化）
- 宏观经济分析（全球 + 国内 + 预期推演）
- 大类资产配置分析（含配置原因）
- 行业配置分析（顺周期/科技成长/高股息防御主线）
- 风险管理措施
- 结论与展望

### 6. 导出与保存

**推荐方式：使用 Chrome 浏览器生成 PDF（中文支持最佳）**

```bash
# 1. 先保存为 HTML 格式
# 2. 使用 Chrome 无头模式转换为 PDF
google-chrome --headless --disable-gpu --print-to-pdf="报告.pdf" "file://路径/报告.html"
```

**备用方式：使用 reportlab（需配置中文字体）**

```bash
# 需要安装中文字体（如 fonts-wqy-microhei）
# 使用 DroidSansFallback 或 AR PL UMing 字体
python3 generate_pdf.py
```

**保存位置：** `~/桌面/资产配置报告输出/`

**命名规范：** `{YYYY 年 MM 月} 大类资产配置报告.pdf`

## 可用工具

所有工具调用统一使用 `mcporter call` 命令，入参均为 `query`：

```bash
# 研报查询
mcporter call jy-financedata-tool.FinancialResearchReport --query "<查询内容>"

# 宏观数据查询
mcporter call jy-financedata-tool.MacroIndustryData --query "<查询内容>"

# 金融数据查询
mcporter call jy-financedata-api.FinQuery --query "<查询内容>"

# 综合查询
mcporter call jy-financedata-api.FinGeneralQuery --query "<查询内容>"
```

### 工具说明

| 工具 | 功能 | 典型查询 |
|------|------|----------|
| `FinancialResearchReport` | 获取券商研报观点 | "资产配置 最新观点"、"宏观经济 研报" |
| `MacroIndustryData` | 获取宏观经济数据 | "GDP CPI PMI 最新"、"货币供应 M2" |
| `FinQuery` | 获取金融市场价格数据 | "股票估值"、"债券收益率"、"商品价格" |
| `FinGeneralQuery` | 综合金融查询 | "行业景气度"、"资金流向" |

## 报告模板

完整报告模板结构详见 `references/template.md`。

### 核心模块

1. **报告摘要**
   - 核心观点表格化呈现
   - 配置建议一目了然

2. **宏观经济分析**
   - 全球宏观经济形势
   - 国内宏观经济形势
   - **预期推演**（新增）：乐观/悲观/基准三种情景

3. **大类资产配置分析**
   - 股票、债券、商品、现金、另类资产
   - 配置权重建议
   - **配置原因**（新增）：说明配置逻辑

4. **行业配置分析**
   - 顺周期主线
   - 科技成长主线
   - 高股息防御主线

5. **风险管理措施**
   - 风险识别
   - 对冲策略
   - 仓位控制

6. **结论与展望**
   - 下阶段配置建议
   - 关注事项

## 输出格式

| 项目 | 说明 |
|------|------|
| 默认格式 | Markdown |
| 推荐格式 | **HTML → Chrome 打印为 PDF**（中文支持最佳） |
| 备用格式 | reportlab 生成 PDF（需配置中文字体） |
| 存储位置 | `~/桌面/资产配置报告输出/` |
| 命名规范 | `{YYYY 年 MM 月} 大类资产配置报告.pdf` |
| 数据时效 | 研报近 3 个月，宏观数据最新可用 |

### PDF 生成方式对比

| 方式 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **Chrome 无头模式** | 中文支持完美，格式美观，字体嵌入完整 | 需要 Chrome 浏览器 | ⭐⭐⭐⭐⭐ |
| reportlab | 纯 Python，无需浏览器 | 中文字体配置复杂，易乱码 | ⭐⭐ |
| WeasyPrint | 支持 CSS 样式 | 中文字体嵌入有问题 | ⭐⭐ |
| pandoc+xelatex | 格式专业 | 需要安装 xelatex | ⭐⭐⭐ |

### Chrome 生成 PDF 示例

```bash
# 1. 准备 HTML 文件（包含完整 CSS 样式）
# 2. 使用 Chrome 无头模式转换
google-chrome --headless --disable-gpu --print-to-pdf="2026 年 3 月大类资产配置报告.pdf" "file:///path/to/report.html"

# 输出：3-4MB PDF 文件，中文显示正常，格式美观
```

## 示例报告

示例报告参考 `examples/sample_report.md`。

## 注意事项

- ⚠️ **报告仅供研究参考，NOT investment advice**
- ⚠️ 数据来源于 gildata 聚源数据库及官方统计机构，部分数据可能存在延迟
- ⚠️ 所有数据必须标注截止日期
- ⚠️ 首次使用需完成 JY_API_KEY 配置（配置一次即可）
- ⚠️ 如未配置 JY_API_KEY，技能将提示并要求用户提供

## Troubleshooting

**"mcporter: command not found"**
```bash
# 安装 mcporter
npm install -g mcporter
```

**"MCP server not connected"**
```bash
# 检查配置
mcporter list
# 如服务缺失，重新配置
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"
```

**"JY_API_KEY not found"**
```bash
# 检查环境变量或配置文件
# 如未配置，按"步骤 2.1 获取 JY_API_KEY"流程申请
```

**"Data query timeout"**
- gildata API 可能需要较长时间（30-60 秒）
- 重试或简化查询条件

**"PDF 中文乱码"**
```bash
# 解决方案 1（推荐）：使用 Chrome 浏览器生成 PDF
google-chrome --headless --disable-gpu --print-to-pdf="报告.pdf" "file://路径/报告.html"

# 解决方案 2：安装中文字体
apt-get install fonts-wqy-microhei fonts-noto-cjk

# 解决方案 3：使用 HTML 格式直接查看
# HTML 文件可在任意浏览器中正常显示中文
```

**"Chrome 无头模式失败"**
```bash
# 检查 Chrome 是否安装
google-chrome --version

# 如未安装，使用 Chromium
chromium-browser --headless --disable-gpu --print-to-pdf="报告.pdf" "file://路径/报告.html"

# 或使用系统默认浏览器打印功能手动保存为 PDF
```

## References

| 文件 | 说明 |
|------|------|
| `references/template.md` | 完整报告模板结构（Markdown 格式） |
| `references/report_template.html` | HTML 报告模板（支持 Chrome 生成 PDF） |
| `references/data_sources.md` | MCP 工具使用说明 |
| `examples/sample_report.md` | 示例报告参考 |

### HTML 模板使用说明

`references/report_template.html` 是一个包含完整 CSS 样式的 HTML 模板，支持：

1. **直接使用**：填充模板变量后在浏览器中查看
2. **生成 PDF**：使用 Chrome 无头模式转换为 PDF
   ```bash
   google-chrome --headless --disable-gpu --print-to-pdf="报告.pdf" "file://路径/report.html"
   ```
3. **中文支持**：内置多种中文字体回退方案，确保正常显示

### 模板变量列表

| 变量 | 说明 | 示例 |
|------|------|------|
| `{{TITLE}}` | 页面标题 | 2026 年 3 月大类资产配置报告 |
| `{{REPORT_TITLE}}` | 报告主标题 | 【2026 年 3 月】大类资产配置报告 |
| `{{ORGANIZATION}}` | 编制机构 | Test Agent |
| `{{REPORT_DATE}}` | 报告日期 | 2026-03-31 |
| `{{DATA_CUTOFF}}` | 数据截止 | 2026-03-31 |
| `{{KEYWORD1-4}}` | 本月关键词 | 地缘风险、滞胀担忧... |
| `{{CN_PMI}}` | 中国 PMI | 50.4 |
| `{{CN_CPI_YOY}}` | 中国 CPI 同比 | 1.3% |
| `{{HS300_PE}}` | 沪深 300 PE | 13.97 倍 |
| `{{BOND_10Y}}` | 10 年期国债收益率 | 1.804% |
| ... | ... | ... |
