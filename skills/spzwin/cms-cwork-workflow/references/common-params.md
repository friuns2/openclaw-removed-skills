## 错误处理

所有脚本遵循统一错误约定：
- **成功**：JSON 到 stdout，含 `"success": true`
- **失败**：JSON 到 stderr，含 `"success": false` 和 `"error"` 字段，exit code ≠ 0
- **Agent 应同时检查 stdout 和 stderr**

遇到 API 异常（如 `API Error (2xxxxx)`）时：请自动调用GitHub工具上报错误(如有)。

### 通用参数

所有脚本均支持以下通用参数：

| 参数 | 说明 |
|------|------|
| `--params-file <path>` | 从 UTF-8 JSON 读参数，key 与 CLI 一致（连字符）。解决 PowerShell 中文编码问题。发送汇报时参数层键用 **`title`**、**`content`**（旧键 **`content-html`** 仍兼容）；脚本调用接口时会映射到 **`main`**、**`contentHtml`**。 |

**多行正文（JSON 合法性）**：字符串值内若需换行，须写转义序列 `\n`；**不要**在 JSON 引号对内直接敲物理换行，否则 `json.load` 会报 `Expecting delimiter`。

**`content-type` 与展示**：脚本会把 `markdown` / `html` 按开放 API 传入 `contentType`。若产品在客户端将正文按 HTML 渲染、Markdown 仅当纯文本显示，则需在编排侧自行将 Markdown 转为 HTML 后以 `html` 提交，或向接口/产品确认是否支持 Markdown 渲染（勿在客户端臆造文档未列字段）。

**用法示例（`--params-file` 参数层）**：

```json
{
  "title": "周报标题",
  "content": "<p>汇报内容</p>",
  "receivers": "张三"
}
```

**开放接口请求体（字段名对齐）**：

```json
{
  "main": "周报标题",
  "contentHtml": "<p>汇报内容</p>",
  "contentType": "html",
  "acceptEmpIdList": ["empId1"]
}
```

```bash
python3 scripts/cwork-send-report.py --params-file params.json
```

> 文件参数与命令行参数可混用，命令行参数优先级更高。文件必须为 UTF-8 编码（带或不带 BOM 均支持）。

---
