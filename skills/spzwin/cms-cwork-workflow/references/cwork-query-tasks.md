### 5. 查询任务 — `cwork-query-tasks.py`

**意图**：我的任务 / 我创建的 / 团队任务 / 任务详情（含汇报链）/ 识别逾期和未闭环

```bash
# 分配给我的任务
python3 scripts/cwork-query-tasks.py --mode my --status 1

# 我创建的任务
python3 scripts/cwork-query-tasks.py --mode created

# 下属任务
python3 scripts/cwork-query-tasks.py --mode manager --subordinate-ids "id1,id2"

# 任务详情（含汇报链路）
python3 scripts/cwork-query-tasks.py --mode detail --task-id <planId>

# 识别逾期任务
python3 scripts/cwork-query-tasks.py --mode blocked --days-threshold 7

# 默认会为返回的任务补充 shareLink（最多前 20 条）
python3 scripts/cwork-query-tasks.py --mode my --with-share-link --share-top-n 20

# 如需关闭补链
python3 scripts/cwork-query-tasks.py --mode my --no-share-link

# 当前页全部补链
python3 scripts/cwork-query-tasks.py --mode my --share-top-n 0
```

| 参数 | 说明 |
|------|------|
| `--mode` | `my` / `created` / `team` / `assigned` / `detail` / `chain` / `blocked` / `unclosed` / `manager` / `nudge` |
| `--task-id` | 任务/计划 ID（detail / chain 必填） |
| `--subordinate-ids` | 下属 empId 列表（逗号分隔，manager 模式必填） |
| `--assignee` | 责任人姓名（my / assigned 模式可选，自动解析 empId） |
| `--status` | 任务状态：0=已关闭 / 1=进行中 / 2=未启动 |
| `--report-status` | 汇报状态：0=关闭 / 1=待汇报 / 2=已汇报 / 3=逾期 |
| `--key-word` | 关键词搜索 |
| `--days-threshold` | 逾期天数阈值（blocked 模式，默认 7） |
| `--page-index` | 页码（默认 1） |
| `--page-size` | 每页大小（默认 20） |
| `--with-share-link` / `--no-share-link` | 是否补充任务分享链接（默认开启） |
| `--share-top-n` | 列表场景最多补充前 N 条 `shareLink`（默认 20，传 0 表示当前页全部） |
| `--dry-run` | 仅预览，不调用 API |

### AI 汇总输出建议（含可点击链接）

- 当结果项包含 `shareLink` 时，AI 在任务清单里应把链接直接挂在标题后，方便用户点开任务。
- 推荐格式：`- <任务标题>（[打开任务](<shareLink>)）`
- 若存在状态与截止时间，建议补充为：`- <任务标题>（<状态>，截止 <日期>，[打开任务](<shareLink>)）`
- 若某条无 `shareLink`，使用降级文案：`- <任务标题>（链接暂不可用，可让我重试补链）`
- 禁止编造链接；仅可使用脚本返回的真实 `shareLink`。

---
