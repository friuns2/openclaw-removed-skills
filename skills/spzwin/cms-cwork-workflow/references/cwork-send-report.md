### 1. 发送汇报 — `cwork-send-report.py`

**意图**：先**全量**保存/更新草稿（API 5.23，更新前会拉 API 5.25 详情合并，避免覆盖丢字段）→ 输出接口返回的**完整**草稿（`draftDetail`）供用户过目 → 仅在用户明确同意后加 `--confirm-send` 调用 **API 5.27**（`draftBox/submit/{汇报id}`）发出。

**汇报 id 与 `draftId` 字段（避免歧义）**

| 概念 | 含义 | 出现位置 |
|------|------|----------|
| **汇报 id** | 草稿对应的汇报记录主键 | API 5.23 返回 `data.id`、API 5.25 路径与 `draftDetail.id`、API 5.27 路径 `{id}` |
| **草稿箱记录 id** | 草稿箱列表里一行的主键，**仅用于 API 5.26 删除** | API 5.24 列表项的 `id`（勿与汇报 id 混用） |

**删除草稿（`cwork_client`）**：`delete_draft` 的参数必须是 **API 5.24 列表项的 `id`**。若只有汇报 id（与列表里的 `businessId` 相同），须调用 **`delete_draft_by_report_id(汇报id)`**；误把汇报 id 传给 `delete_draft` 时，接口可能仍返回 `true` 但列表中草稿未删（见开放 API 5.26 与 5.24 参数说明）。

脚本 stdout 里同时有根字段 **`reportId`** 与 **`draftId`**：二者**不是**两种 id，而是**同一汇报 id 的重复输出**——`draftId` **并非**开放平台文档里的字段名，而是本脚本为衔接历史参数 `--draft-id` 而保留的 JSON 键名，容易让人误以为是「草稿箱 id」。**以 `reportId` / `draftDetail.id` 为准即可**；后续步骤一律传该汇报 id（`--draft-id <汇报id>` 中的值也是它）。

```bash
# 第一步：保存草稿并输出完整预览（默认不会发出；且需显式确认保存）
python3 scripts/cwork-send-report.py \
  --title "周报标题" \
  --content "<p>汇报内容</p>" \
  --receivers "张三,李四" \
  --confirm-save-draft \
  --grade "一般"

# 第二步：用户确认 draftDetail 全文后，仅发出（无需再传标题正文）
python3 scripts/cwork-send-report.py --draft-id "<汇报id>" --confirm-send

# Markdown 正文（须 --content-type markdown）
python3 scripts/cwork-send-report.py \
  --title "周报标题" \
  --content-type markdown \
  --content "## 小节\n正文" \
  --receivers "张三" \
  --confirm-save-draft

# 测试/调试建议：默认发给当前用户本人
python3 scripts/cwork-send-report.py \
  --title "API冒烟草稿" \
  --content "<p>仅测试，不正式发出</p>" \
  --test-mode \
  --current-user-name "当前用户姓名" \
  --preview-only \
  --confirm-save-draft
```

**字段映射（避免与开放接口字段混淆）**

- 脚本/Skill 入参（CLI 与 `--params-file`）使用：`title`、`content`。
- 脚本在调用开放接口 `save_draft` / `submit_report` 时会映射为：`main`、`contentHtml`。
- `contentType` 与 `acceptEmpIdList` 也会按接口要求透传。

接口请求体（开放 API）示例：

```json
{
  "main": "汇报标题",
  "contentHtml": "<p>汇报正文内容</p>",
  "contentType": "markdown",
  "acceptEmpIdList": ["empId1", "empId2"]
}
```

**正文（编排侧参数仍使用 `content`）**

- 汇报正文：CLI 用 **`--content`** / **`-c`**，`--params-file` 用键 **`content`**。脚本会自动映射到接口字段 `contentHtml`。
- Markdown：须同时指定 **`--content-type markdown`**。
- 新建未传 `--content-type` 时脚本默认 `html`；带 `--draft-id` 更新且未传时沿用草稿详情中的正文类型。
- **`--content-html`** 可选，与 **`--content` 二选一**（兼容旧自动化，勿同时使用）。

| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` / `-t` | 保存草稿时 ✅ | 汇报标题（与 `--draft-id --confirm-send` 单独发出时勿传） |
| `--content` / `-c` | 保存草稿时 ✅ | 汇报正文 |
| `--content-html` | ❌ | [兼容] 同 `--content` |
| `--content-type` | ❌ | 正文格式：`html` 或 `markdown`（默认与更新沿用规则见上文） |
| `--receivers` / `-r` | ❌ | 接收人姓名；**多个姓名**可用英文逗号 `,`、中文逗号 `，`、顿号 `、` 或分号 `;`/`；` 分隔（勿整串写成一人）。更新时若省略则沿用草稿详情中的接收人。**若本次传了姓名**且草稿已有 `reportLevelList`（且未使用 `--report-level-json`），脚本会把解析后的 empId **写回**对应节点的 `levelUserList`，与开放 API「接收人以 `reportLevelList` 为准」一致，避免仅 `summary` 显示新人而 `draftDetail` 仍为旧人 |
| `--cc` | ❌ | 抄送；分隔规则同 `--receivers` |
| `--grade` | ❌ | 优先级：`一般`（默认）/ `紧急` |
| `--type-id` | ❌ | 汇报类型 ID（默认 9999） |
| `--file-paths` | ❌ | 本地附件；**未传且为更新**时沿用草稿已有附件 |
| `--file-names` | ❌ | 附件显示名称 |
| `--plan-id` | ❌ | 关联任务 ID |
| `--business-unit-id` | ❌ | 业务单元 ID；传入后按业务单元预设节点流转 |
| `--virtual-emp-id` | ❌ | 虚拟员工提交人 ID。传入后按虚拟人提交（脚本鉴权仍使用当前用户 AppKey）；在 `--draft-id --confirm-send` 发送-only 场景也可单独传入，最终发出时会带入提交接口 |
| `--report-level-json` | ❌ | JSON 文件路径，`reportLevelList` 数组，覆盖流程节点 |
| `--preview-only` | ❌ | 仅保存+预览；**即使带 `--confirm-send` 也不会发出** |
| `--draft-id` | ❌ | **值为汇报 id**（参数名历史沿用）：更新草稿或配合 `--confirm-send` 仅执行 5.27 |
| `--confirm-save-draft` | 保存草稿时 ✅ | **必须显式确认后才会执行 5.23**；用于防止调试时自动落草稿 |
| `--confirm-send` | ❌ | **必须**在用户确认完整 `draftDetail` 后再加；并且**必须搭配 `--draft-id` 使用**，才会调用 5.27 |
| `--test-mode` | ❌ | 测试/调试模式。默认仅允许接收人为当前用户本人；若未传 `--receivers` 且传了 `--current-user-name`，会自动以本人为接收人 |
| `--current-user-name` | ❌ | 当前发起用户姓名；`--test-mode` 下用于默认接收人与“仅本人”校验 |
| `--allow-external-test-receivers` | ❌ | 在 `--test-mode` 下放开“仅本人”限制（高风险；必须先用户确认） |
| `--allow-minimal-body` | ❌ | 跳过「正文过短」校验（默认纯文本长度 **≤10** 会拒绝保存，**超过 10 字**不拦截；极短占位可加本参数） |
| `--fail-on-literal-newlines` | ❌ | 仅供 CI/自动化使用：若 `markdown` 正文中含字面量 `\n` / `\r\n`，则在自动修正前直接失败退出，用于尽早暴露上游转义问题 |

**流程节点角色映射（重点，避免模型误解）**

- “建议人” = `reportLevelList[].type = "suggest"`
- “决策人” = `reportLevelList[].type = "decide"`
- “传阅/接收” = `reportLevelList[].type = "read"`
- `type` 仅允许：`suggest` / `decide` / `read`（英文小写）
- `nodeName` 是展示文案，可按业务语义自定义；`nodeCode` 非必填
- 每个节点都应包含处理对象：`levelUserList`（或分组/部门字段）

**示例 A：两个建议节点（同一人）**

```json
[
  {
    "level": 1,
    "nodeName": "确认研究报告输出时间",
    "type": "suggest",
    "levelUserList": [{"empId": 10001}]
  },
  {
    "level": 2,
    "nodeName": "提交天工系统研究报告",
    "type": "suggest",
    "levelUserList": [{"empId": 10001}]
  }
]
```

**示例 B：建议后决策**

```json
[
  {
    "level": 1,
    "nodeName": "建议人评估可行性",
    "type": "suggest",
    "levelUserList": [{"empId": 10001}]
  },
  {
    "level": 2,
    "nodeName": "负责人决策是否立项",
    "type": "decide",
    "levelUserList": [{"empId": 20001}]
  }
]
```

**流程步骤**：
1. **Resolve** — 按姓名搜索员工；本轮回填的姓名参与合并，未填则沿用 5.25 详情中的接收人/抄送
2. **Validate** — 姓名未找到或多匹配时报错终止
3. **Upload** — 若传了 `--file-paths` 则上传并作为附件；否则更新时保留原附件列表
4. **Detail（更新时）** — 若有 `--draft-id`，先 `get_draft_detail` 再与本次参数合并，并用于正文长度校验（未传 `--allow-minimal-body` 时）
5. **Draft（5.23）** — 仅在显式传入 `--confirm-save-draft` 时才执行全量 `saveOrUpdate`，返回汇报 id
6. **Preview** — 再次 `get_draft_detail`，stdout 含完整 **`draftDetail`**（含全文**正文**）及 **`summary`**。`summary` 的 `contentPlainText` / `contentPreview` 为便于速览的纯文本预览（对 HTML 标签做了剥离；Markdown 正文通常无标签，与 `--content` 接近）；过长截断；过短有 `previewWarnings`。`confirmPrompt` 内嵌预览（≤2000 字）。**向用户确认时以完整 `draftDetail` 为准**，不要只用 `summary`。
7. **Submit（发送-only）** — 仅当 `--confirm-send`、`--draft-id` 同时存在且非 `--preview-only` 时发出：  
   - 若本次传了 `--virtual-emp-id`，或草稿详情本身已有 `virtualEmpId`，脚本走 **5.1 `/report/record/submit`（携带 `id` + `virtualEmpId`）** 发出，确保虚拟人参数参与最终提交。  
   - 若草稿无 `virtualEmpId` 且本次也未传，脚本走 **5.27** 发出。  
   - 两种路径都保持“先草稿、确认后发送”。

---
