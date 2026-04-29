### 11. 正文匹配业务单元并发汇报 — `cms-match-businessunit.py`

**意图**：用户给出标题与正文后，自动匹配最合适的业务单元并直接发送汇报。
**适用前提**：用户已配置至少一个业务单元；若未配置，请改用 `cwork-send-report.py` 常规发送。

**与员工搜索的区别**：本脚本**不**调用 `cwork-search-emp.py`。接收人/节点人员来自业务单元里已绑定的 `empList`，服务端按 `businessUnitId` 流转。**不要**把「自己匹配人员」理解成必须先搜员工。

```bash
# 仅匹配预览（不发送）
python3 scripts/cms-match-businessunit.py \
  --title "周报" \
  --content "<p>本周完成 API 接口联调与开发提测</p>" \
  --content-type html \
  --dry-run

# 匹配并发送
python3 scripts/cms-match-businessunit.py \
  --title "周报" \
  --content "<p>本周完成 API 接口联调与开发提测</p>" \
  --content-type html
```

支持参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` / `-t` | ✅ | 汇报标题 |
| `--content` / `-c` | ✅ | 汇报正文 |
| `--content-type` | ❌ | `html` / `markdown`（默认 `html`） |
| `--grade` | ❌ | `一般` / `紧急`（默认 `一般`） |
| `--type-id` | ❌ | 汇报类型 ID（默认 `9999`） |
| `--plan-id` | ❌ | 关联任务 ID |
| `--template-id` | ❌ | 模板 ID |
| `--virtual-emp-id` | ❌ | 虚拟员工 ID（业务代发参数；脚本鉴权仍使用当前用户 AppKey） |
| `--dry-run` | ❌ | 仅匹配不发送 |

匹配规则补充：
- 标题与正文都会参与匹配打分，且标题命中权重更高（用于处理“标题有关键词、正文较泛化”的场景）。
- 当返回 `matched=false` / `suggestion=NO_MATCH` 时，表示未达到可自动发送置信度，必须询问用户明确接收人或业务单元，禁止自动选 Top1 候选发送。

---

## `reportLevelList` 字段格式

`cwork-send-report.py` 可通过 **`--report-level-json`** 指向 UTF-8 JSON 文件（根节点为数组），内容对应 API 字段 `reportLevelList`，用于指定建议人/决策人/传阅等节点；不传时新建草稿可为空，**更新**时默认从 5.25 详情中的 `reportLevelList` 原样转换后写回，避免全量更新被清空。每个节点结构如下：

```python
report_level_list = [
    {
        "level": 1,                              # 节点序号（从1开始）
        "nodeName": "建议人",                     # 节点显示名称
        "type": "suggest",                       # suggest=建议 | decide=决策 | read=传阅
        "levelUserList": [
            {"empId": 1512393035869810694},       # empId 必须是整数（非字符串）
        ],
    }
]
```

> ⚠️ `type` 只接受英文小写 `suggest` / `decide` / `read`，不接受中文。`levelUserList` 是必填字段，不可为 `null` 或空列表。

---
