### 7. 待办管理 — `cwork-todo.py`

**意图**：查询待办列表 / 完成待办（支持决策/建议/反馈三种类型）

**支持的三种待办类型**：
| 类型 | 英文标识 | 必填参数 | 说明 |
|------|---------|---------|------|
| **决策** | `decide` | `--operate agree/disagree` | 决策人必须明确同意或不同意 |
| **建议** | `suggest` | `--content` | 建议人提供意见或建议 |
| **反馈** | `feedback` | `--content` | 反馈人回复评论或补充信息 |

```bash
# 查询待办列表（API 5.15 分页结构为 PageInfo，条目见 items，字段含 todoId、reportId、main、todoType 等）
python3 scripts/cwork-todo.py list --page-size 20 --status pending

# 默认会为返回的待办补充 shareLink（最多前 20 条）
python3 scripts/cwork-todo.py list --with-share-link --share-top-n 20

# 如需关闭补链
python3 scripts/cwork-todo.py list --no-share-link

# 当前页全部补链
python3 scripts/cwork-todo.py list --share-top-n 0

# 完成决策待办（必须指定 operate）
python3 scripts/cwork-todo.py complete \
  --todo-id <id> \
  --content "同意该方案，建议增加异常处理" \
  --operate agree

# 完成建议待办
python3 scripts/cwork-todo.py complete \
  --todo-id <id> \
  --content "从技术角度看，建议采用微服务架构"

# 完成反馈待办
python3 scripts/cwork-todo.py complete \
  --todo-id <id> \
  --content "已补充相关数据，详见附件"

# 查看汇报详情（含节点与处理意见）
python3 scripts/cwork-query-report.py --mode node-detail --report-id <id>
```

| 参数 | 说明 |
|------|------|
| `action` | `list` / `complete` |
| `--page-index` | 页码（默认 1） |
| `--page-size` | 每页数量（默认 20） |
| `--status` | 状态筛选 |
| `--with-share-link` / `--no-share-link` | 是否补充待办关联对象分享链接（默认开启） |
| `--share-top-n` | 列表场景最多补充前 N 条 `shareLink`（默认 20，传 0 表示当前页全部） |
| `--todo-id` | 待办 ID（complete 必填） |
| `--content` | 完成说明（所有类型必填） |
| `--operate` | 决策操作：`agree`（同意）/ `disagree`（不同意）（仅决策类待办需要，不传则不发送此字段） |
| `--dry-run` | 仅预览（complete 可用） |

**输出格式**（complete）：
```json
{
  "success": true,
  "action": "list",
  "total": 2,
  "items": [
    {
      "todoId": "12345",
      "reportId": "2039993163862765570",
      "title": "互联网公司公章借出申请",
      "todoType": "decide",
      "status": "pending",
      "shareLink": "https://xxx/share/abc123"
    }
  ]
}
```

**输出格式**（complete）：
```json
{
  "success": true,
  "action": "complete",
  "todoId": "12345",
  "result": {}
}
```

### AI 汇总输出建议（含可点击链接）

- 当待办项含 `shareLink` 时，AI 在清单中应把链接附在标题后。
- 推荐格式：`- <待办标题>（[打开相关单据](<shareLink>)）`
- 若有待办类型与状态，建议补充为：`- <待办标题>（<todoType>/<status>，[打开相关单据](<shareLink>)）`
- 若某条无 `shareLink`，使用降级文案：`- <待办标题>（链接暂不可用，可让我重试补链）`
- 禁止编造链接；仅可使用脚本返回的真实 `shareLink`。

---
