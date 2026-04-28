### 2. 查询汇报 — `cwork-query-report.py`

**意图**：收件箱 / 发件箱 / 未读 / 汇报详情 / 节点详情 / **历史上下文检索** ✨ 新增

```bash
# 收件箱（默认）
python3 scripts/cwork-query-report.py --mode inbox --page-size 20

# 未读汇报
python3 scripts/cwork-query-report.py --mode unread --page-size 20

# 发件箱
python3 scripts/cwork-query-report.py --mode outbox

# 详情模式（包含回复链）
python3 scripts/cwork-query-report.py --mode detail --report-id <id>

# 节点详情（含审批/建议/反馈状态与处理意见）
python3 scripts/cwork-query-report.py --mode node-detail --report-id <id>

# 历史上下文检索（审批决策支持）
# 查询发件人历史汇报
python3 scripts/cwork-query-report.py --mode sender-history \
  --sender-emp-id <empId> \
  --days 90

# 关键字搜索汇报（客户端过滤）
python3 scripts/cwork-query-report.py --mode keyword-search \
  --keyword "公章" \
  --days 90

# 默认会为返回的汇报补充 shareLink（最多前 20 条）
python3 scripts/cwork-query-report.py --mode inbox --with-share-link --share-top-n 20

# 如需关闭补链
python3 scripts/cwork-query-report.py --mode inbox --no-share-link

# 当前页全部补链
python3 scripts/cwork-query-report.py --mode inbox --share-top-n 0
```

| 参数 | 说明 |
|------|------|
| `--mode` | `inbox` / `outbox` / `unread` / `detail` / `node-detail` / `sender-history` / `keyword-search` / `pending` / `my-sent` |
| `--page-size` | 分页大小（默认 20） |
| `--page-index` | 页码（默认 1） |
| `--report-id` | 汇报 ID（detail / node-detail 必填） |
| `--sender-emp-id` | 发件人员工 ID（sender-history 必填） |
| `--keyword` | 搜索关键词（keyword-search 必填） |
| `--days` | 回溯天数（sender-history / keyword-search，默认 90） |
| `--report-type` | 汇报类型：1-工作交流 / 2-工作指引 / 3-文件签批 / 4-AI汇报 / 5-工作汇报 |
| `--status` | 已读状态：0=未读 / 1=已读 |
| `--start-date` / `--end-date` | 时间范围（YYYY-MM-DD） |
| `--with-share-link` / `--no-share-link` | 是否补充汇报分享链接（默认开启） |
| `--share-top-n` | 列表场景最多补充前 N 条 `shareLink`（默认 20，传 0 表示当前页全部） |

**收件箱 / 发件箱列表 vs 详情**：`inbox` / `outbox` / `pending` / `unread` / `my-sent`（与 `outbox` 同脚本路径）等模式返回的 **`data` 为接口原始分页结构**（常见含 `list`、`total`）。列表项里的「正文」类字段多为**摘要**，与 `send-report` 的 `--content` 全文不一定一致；需要全文或完整字段时请用 **`--mode detail --report-id`**（或 `node-detail`）拉详情。默认会在可识别到汇报 ID 的结果上补充 `shareLink`，便于点击打开原始汇报。

**输出格式**（sender-history）：
```json
{
  "success": true,
  "data": {
    "senderEmpId": "1514822194347806721",
    "totalReports": 15,
    "recentReports": [
      {
        "id": "2039993163862765570",
        "main": "互联网公司公章借出申请",
        "createTime": "2026-04-03 17:11:48",
        "reportRecordType": 5
      }
    ]
  }
}
```

**输出格式**（keyword-search）：
```json
{
  "success": true,
  "data": {
    "keyword": "公章",
    "total": 5,
    "reports": [
      {
        "id": "2039993163862765570",
        "main": "互联网公司公章借出申请",
        "content": "用于办理工商变更...",
        "createTime": "2026-04-03 17:11:48",
        "sendEmpName": "刘丽华"
      }
    ]
  }
}
```

**输出格式**（node-detail）：
```json
{
  "success": true,
  "data": {
    "id": 汇报ID,
    "main": "汇报标题",
    "content": "汇报正文",
    "writeEmpName": "汇报人",
    "createTime": "发起时间",
    "nodeList": [
      {
        "nodeName": "建议人",
        "type": "建议",
        "status": "已完成",
        "level": 1,
        "userList": [
          {
            "empId": 员工ID,
            "name": "张三",
            "status": "已处理",
            "operate": "建议",
            "content": "建议增加异常处理",
            "finishTime": "2026-04-03 11:00:00"
          }
        ]
      }
    ]
  }
}
```

### AI 汇总输出建议（含可点击链接）

- 当结果项包含 `shareLink` 时，AI 在汇总文本中应将链接直接附在标题后，避免用户二次追问。
- 推荐格式：`- <汇报标题>（[打开汇报](<shareLink>)）`
- 若存在时间与汇报人，建议补充为：`- <汇报标题>（<时间>，<汇报人>，[打开汇报](<shareLink>)）`
- 若某条无 `shareLink`，使用降级文案：`- <汇报标题>（链接暂不可用，可让我重试补链）`
- 禁止编造链接；仅可使用脚本返回的真实 `shareLink`。

---
