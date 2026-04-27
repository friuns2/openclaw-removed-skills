---
name: aitubiao-3d-illustration
description: AI图表3D插图生成。根据用户数据和指定图表类型，生成3D风格化数据可视化插画。当用户想要将图表转为3D插画、创建3D风格图表时使用，触发词包括"3D图表"、"3D插图"、"图表转3D"、"3D illustration"、"3d chart"、"stylize chart"等。
license: MIT
compatibility: Requires network access to api.aitubiao.com, Bash shell, curl, and jq
metadata:
  author: aitubiao
  version: "1.1.5"
allowed-tools: Bash Read
---

# AI 图表3D插图生成

根据用户提供的数据和指定的图表类型，生成3D风格化数据可视化插画。

## 强制规则

**以下规则必须严格执行，不得跳过、变通或使用替代方案：**

1. **认证优先**：在执行任何操作之前，必须先检查凭证状态。认证未通过时，禁止执行任何后续步骤。
2. **按顺序执行**：工作流程的 5 个步骤必须按顺序执行，禁止跳步。
3. **费用确认前禁止调用生成接口**：必须成功查询配额、计算费用、并获得用户明确确认后，才能调用创建接口。
4. **仅通过 API 生成3D插图**：禁止使用本地工具（Blender、Three.js、matplotlib 等）生成3D可视化。无论 API 因何种原因失败，都**绝对禁止使用本地工具**，没有任何例外。API 失败时正确做法是停止并告知用户，不是寻找替代方案。
5. **401/403 立即停止**：任何步骤中收到 HTTP 401/403（CLI exit 1），立即停止并引导用户前往 [API Key 管理页面](https://app.aitubiao.com/setting/api-keys) 检查或重新创建 API Key。401/403 不是超时，禁止重试。
6. **超时/500 不自动重试创建接口**：创建接口不可重试（可能重复扣费）。告知用户失败原因，由用户决定是否重新发起。

**⚠️ 以下想法是错误的，如果你发现自己在这样想，请立即停止：**
- ❌ "API 不可用，我可以用本地工具生成3D可视化作为替代" → 违反规则 4
- ❌ "至少让用户看到一些3D效果" → 本技能唯一输出方式是 aitubiao API
- ❌ "401 可能是暂时性的，重试几次" → 401 是认证失败，重试无意义，按规则 5 处理

## 认证

在调用任何 API 之前，先检查凭证状态。

### 检查凭证

```bash
bash scripts/aitubiao-cli.sh check-auth
```

- **Exit 0** → 认证通过
- **Exit 1** → 凭证问题，按 stderr 提示处理：
  - 文件不存在/API_KEY 为空 → 执行下方"配置凭证"流程
  - API_KEY 格式无效 → 告知用户"当前 API Key 已失效，请前往 [API Key 管理页面](https://app.aitubiao.com/setting/api-keys) 重新创建一个 API Key"
  - BASE_URL 与当前技能包环境不一致 → 说明凭证中残留了旧环境地址；向用户索要当前仍有效的 API Key，并执行下方"配置凭证"流程重写凭证（通常不需要重新创建 API Key）

### 配置凭证

1. 向用户索要 API Key（格式：`sk_v1_...`）。如果没有，引导用户前往 [API Key 管理页面](https://app.aitubiao.com/setting/api-keys) 创建一个新的 API Key，然后将创建好的 Key 粘贴回来。
2. 保存凭证：
```bash
bash scripts/aitubiao-cli.sh auth <用户提供的key>
```
3. 验证：再次运行 `bash scripts/aitubiao-cli.sh check-auth` 确认配置成功。

凭证保存在 `~/.aitubiao/credentials`，跨会话持久生效。

## Windows / Git Bash 注意事项（仅 Windows 用户需要关注）

在 Windows 上通过 Git Bash 运行本 CLI 时，**禁止把含中文等非 ASCII 字符的 JSON 直接写在 heredoc 里**——MSYS 会按 Windows 系统代码页（常为 GBK/CP936）转换 argv 字节，传到后端就是乱码。

正确做法：先用 Write 工具把完整 UTF-8 JSON 写到一个临时文件，然后用 `--body-file` 让 CLI 从文件读取（绕过任何 argv/控制台编码转换）：

```bash
# 第一步：用 Write 工具把请求体写到 /tmp/aitubiao-payload.json（内容必须是 UTF-8）
# 第二步：用 --body-file 调用 CLI
bash scripts/aitubiao-cli.sh --body-file /tmp/aitubiao-payload.json create-chart
```

`--body-file` 可用于所有读取 stdin JSON 的命令：`create-chart` / `create-ppt` / `create-sankey` / `create-3d` / `download-project`。CLI 会自动剥离 UTF-8 BOM 和 CRLF。

macOS / Linux 上无需改动，仍然可以使用 heredoc。

## 支持的图表类型

仅以下 11 种图表类型支持转换为3D插图：

| chartType | 中文名称 | 数据结构 | 数据行数 | 数据要求 | 推荐场景 |
|-----------|---------|---------|---------|---------|---------|
| `basic-line` | 基础折线图 | 1列时间 + 1-8列数值 | 2-120行 | 数值或比率 | 时间序列/趋势数据 |
| `cascaded-area` | 层叠面积图 | 1列时间 + 1-8列数值 | 2-120行 | 数值或比率 | 多系列趋势对比 |
| `stacked-area` | 堆叠面积图 | 1列时间 + 1-12列数值 | 2-120行 | 数值或比率 | 累计趋势可视化 |
| `basic-pie` | 饼图 | 1列分类 + 1列数值 | 2-12行 | 比率(总和≈100%) | 占比/分布数据 |
| `basic-column` | 基础柱状图 | 1列分类 + 1列数值 | 2-120行 | 数值或比率 | 分类对比 |
| `check-in-bubble` | 打卡气泡图 | 1列维度 + 2-48列数值 | 2-48行 | 数值或比率 | 频次/热度数据 |
| `funnel` | 漏斗图 | 1列阶段名 + 1列数值 | 2-12行 | 数值或比率 | 转化率/流程数据 |
| `donut-progress` | 圆环进度图 | 1列名称 + 1列数值 | 仅1行 | 比率(0-100) | 占比/完成度 |
| `bar-progress` | 条形进度图 | 1列名称 + 1列数值 | 仅1行 | 比率(0-100) | 单指标进度 |
| `word-cloud` | 词云图 | 1列关键词 + 1列数值 | 12-120行 | 纯数值 | 关键词频率 |
| `liquid` | 水波图 | 1列名称 + 1列数值 | 1-48行 | 比率(0-100) | 单指标比率 |

### 数据格式注意事项

- **比率值使用百分制**：如完成度75%必须传 `75`，禁止传 `0.75`
- **饼图特殊要求**：所有数值之和必须在99.5%-100%之间
- **时间序列图表**（basic-line、cascaded-area、stacked-area）：第一列必须是时间
- **圆环进度图和条形进度图**：仅支持1行数据

## 工作流程

**每一步必须在前一步完成后才能开始。禁止跳步。**

### 第一步：认证（前置条件：无）

运行检查凭证流程。认证未通过时按"认证"章节流程处理。

**认证未通过时，停止。不要读取用户数据，不要做任何分析。**

### 第二步：识别数据并选择图表类型（前置条件：第一步认证通过）

#### 2.1 获取数据

判断用户如何提供数据：

- **直接粘贴文本**：解析为二维数组格式 `(string|number)[][]`，第一行为表头。
- **本地文件**（CSV/TXT）：用 Read 工具读取，然后解析为二维数组。
- **Excel 文件**（.xlsx/.xls）：使用 xlsx skill 或 Read 工具读取，禁止手动编写 Python 脚本解析 XML。

**数据格式要求**：
API 接受 `data` 字段为 JSON 二维数组，第一行为表头，后续为数据行。数值类型的单元格应为 `number`，文本类型应为 `string`。

示例：
```json
[
  ["月份", "销售额", "利润"],
  ["1月", 1000, 200],
  ["2月", 1500, 350],
  ["3月", 2000, 500]
]
```

#### 2.2 确认图表类型

向用户展示解析后的数据（表格形式），并确认：
- 数据是否正确？
- 选择哪种图表类型？（展示上方支持的11种类型供选择）

如果用户不确定图表类型，根据数据特点推荐：
- **时间序列数据** → `basic-line`（折线图）或 `cascaded-area`（面积图）
- **分类占比数据** → `basic-pie`（饼图）或 `donut-progress`（圆环图）
- **分类对比数据** → `basic-column`（柱状图）
- **层级/流程数据** → `funnel`（漏斗图）
- **单个进度指标** → `bar-progress`（条形进度）或 `liquid`（水波图）

#### 2.3 选择3D风格（可选）

询问用户是否有特殊的3D风格要求。内置风格名称（直接传名称，系统自动解析为详细提示词，不区分大小写）：

`water` | `dollar` | `gold` | `chip` | `fuzzy` | `plants` | `steel` | `glass` | `watermelon` | `bread` | `crystal` | `container` | `wood`

用户也可以输入自定义风格描述（如"赛博朋克"、"黏土风"），系统直接使用。

| style 值 | 效果描述 |
|----------|---------|
| `water` | 纯净水/液体质感 |
| `dollar` | 美元钞票材质 |
| `gold` | 真实黄金材质 |
| `chip` | 电脑芯片/电路板风格 |
| `fuzzy` | 毛茸茸/长毛毯质感 |
| `plants` | 灌木丛/绿植风格 |
| `steel` | 不锈钢金属质感 |
| `glass` | 多彩玻璃质感 |
| `watermelon` | 西瓜切片材质 |
| `bread` | 面包切片材质 |
| `crystal` | 水晶质感 |
| `container` | 集装箱风格 |
| `wood` | 橡木木纹质感 |

### 第三步：检查配额并确认费用（前置条件：第二步数据和图表类型已确认）

在生成3D插图前，**必须**检查用户的 AI贝余额，并向用户确认费用后才能继续。

#### 3.1 查询配额

```bash
bash scripts/aitubiao-cli.sh quota --skill 3d
```

#### 3.2 计算总费用

**3D 插图按"次"计费**：每次调用固定扣 `.feature.cost` 个 AI贝，**与生成的图片张数无关**。

总费用 = `.feature.cost`

#### 3.3 向用户确认费用

**必须在调用生成接口前向用户展示费用确认信息，并等待用户确认后才能继续**：

```
本次操作将消耗 {cost} 个 AI贝（图表3D插图，按次计费）
当前余额: {shellBalance} 个 AI贝
操作后余额: {shellBalance - cost} 个 AI贝

是否继续？
```

- 如果 `shellBalance < cost`：告知用户当前 AI贝余额不足，需前往 aitubiao 网站购买会员或充值后再继续，**不要继续**

### 第四步：生成3D插图（前置条件：第三步用户已确认费用）

**只有用户明确确认费用后才能执行此步骤。**

**注意**：图表渲染 + 3D转换可能需要 60-120 秒。

```bash
bash scripts/aitubiao-cli.sh create-3d <<'EOF'
{
  "data": [["月份","销售额"],["1月",1000],["2月",1500],["3月",2000]],
  "chartType": "<图表类型>",
  "style": "<可选：3D风格描述>",
  "chartTitle": "<可选：图表标题>"
}
EOF
```

**请求体字段说明**：

| 字段 | 类型 | 必填 | 最大长度 | 说明 |
|------|------|------|---------|------|
| data | (string\|number)[][] | 是 | - | 二维数组，第一行表头，数值用 number，文本用 string |
| chartType | string | 是 | - | 图表类型（见上方 11 种支持类型） |
| style | string | 否 | 500 | 内置风格名或自定义描述 |
| chartTitle | string | 否 | 100 | 图表标题 |

**检查 CLI 退出码**：
- **Exit 0**：成功。**但必须检查 stdout JSON 中的 `success` 字段**（见下方 4.1）。
- **Exit 1**：认证失败。引导用户前往 [API Key 管理页面](https://app.aitubiao.com/setting/api-keys)。
- **Exit 2**：业务错误。向用户展示错误详情。
- **Exit 3**：网络/超时错误。告知用户稍后重试。

#### 4.1 图表类型不兼容处理

**即使 CLI exit 0，也必须检查返回 JSON 中的 `success` 字段。** 当 `success === false` 且 `errorCode === "chart_type_incompatible"` 时：
1. 向用户展示 `error` 中的不兼容原因
2. 展示 `compatibleChartTypes` 中可用的图表类型供选择
3. 用户选择新类型后，重新执行第四步

不兼容响应示例：
```json
{
  "success": false,
  "chartType": "basic-line",
  "errorCode": "chart_type_incompatible",
  "error": "Chart type \"basic-line\" requires the first column to contain time values...",
  "compatibleChartTypes": ["basic-column", "basic-pie", "funnel"]
}
```

### 第五步：返回结果（前置条件：第四步生成成功）

向用户提供：
- 3D插图图片 URL（从 `imageUrl` 获取）
- 摘要：图表类型、处理时间
- 如有图片展示能力，直接展示3D插图图片

## 错误处理

| CLI Exit Code | 含义 | 处理方式 |
|--------------|------|---------|
| 0 + success=false | 图表类型不兼容 | 见第四步 4.1 处理流程 |
| 1 | 认证失败（HTTP 401/403 或凭证无效） | 立即停止，引导用户前往 [API Key 管理页面](https://app.aitubiao.com/setting/api-keys) |
| 2 | 业务错误（code 90001=AI贝不足，14301=存储容量不足） | 向用户展示详情 |
| 3 | 网络/超时错误 | 告知用户稍后重试 |
