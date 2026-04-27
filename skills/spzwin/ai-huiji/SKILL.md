---
name: ai-huiji
description: AI慧记能力：查询个人会议（进行中/历史）基于会议号查询参与会议的相关纪要、支持一键接收分享的慧记链接并内容解读、基于原文进行AI分析（总结/待办提取/专题分析）。本 Skill 通过依赖 `cms-auth-skills` 获取 `AppKey` 并完成鉴权后，才允许进入脚本调用链路。
skillcode: ai-huiji
github: https://github.com/xgjk/ai-huiji-skills
dependencies:
  - cms-auth-skills
---

# AI慧记

**当前版本**: v2.6.0

> **AI慧记** 提供四类核心能力：
> 1. **📋 查询列表** — 从「我的慧记」或「视频会议号」两个维度查询会议记录
> 2. **📄 获取原文** — 拿到转写原文作为分析素材（支持全量 / 增量 / 改写三种模式）
> 3. **🔗 分享解析** — 支持一键接收分享的慧记链接并内容解读（短链 / 长链）
> 4. **🧠 AI 分析** — 基于原文进行总结、待办提取、专题分析

---

## 能力概览

| # | 接口 | 路径 | 说明 |
|---|---|---|---|
| 1 | chatListByPage | /ai-huiji/meetingChat/chatListByPage | 分页查询我的慧记列表（归属维度） |
| 2 | listHuiJiIdsByMeetingNumberV2 | /ai-huiji/meetingChat/listHuiJiIdsByMeetingNumberV2 | 按视频会议号查询慧记列表（会议维度） |
| 3 | splitRecordList | /ai-huiji/meetingChat/splitRecordList | 全量查询分片转写原文 |
| 4 | splitRecordListV2 | /ai-huiji/meetingChat/splitRecordListV2 | 增量查询分片转写原文 |
| 5 | checkSecondSttV2 | /ai-huiji/meetingChat/checkSecondSttV2 | 已结束会议的改写原文（更高质量，可能有发言人） |
| 6 | getChatFromShareId | /ai-huiji/meetingChat/getChatFromShareId | 通过分享链接的 shareId 获取原文 |

---

## 强制前置（保持不变）

调用任何脚本前，必须先通过依赖 Skill `cms-auth-skills` 获取有效 `AppKey`。  
未鉴权时，不允许执行本 Skill 的任何 Python 脚本。
本 Skill 发起的所有 CWork API 请求均基于该 `AppKey` 鉴权。

AppKey 的获取与传递方式必须为：由上游 `cms-auth-skills` 注入/传递到本 Skill 执行命令中（`--app-key`）。


---

## 意图路由表

### 📋 列表查询

| 用户说 | 路由 | 说明 |
|---|---|---|
| "我的慧记" / "我的会议纪要" / "最近有什么会议" | **chatListByPage** | 归属维度，无需会议号 |
| "会议号 xxx" / "这场会议的纪要"（提供了会议号时） | **listHuiJiIdsByMeetingNumberV2** | 会议维度，需要会议号 |
| "帮我找 xxx 的会议" / "搜索 xxx" | **chatListByPage** + nameBlur | 搜索模式 |
| "进行中的会议" / "正在开的会" | **chatListByPage** `--state 0` | 进行中，一条命令搞定 |
| "历史会议" / "已结束的会议" | **chatListByPage** `--state 2` | 历史，一条命令搞定 |

### 📄 原文获取

| 用户说 | 路由 | 说明 |
|---|---|---|
| "这个会议的原文" / "会议内容" / "转写" | **get-transcript.py** | 统一入口，自动处理全量/增量/改写 |
| "最新的" / "刚才说的" / "最近几分钟的" | **get-transcript.py** | 自动增量拉取最新内容 |

### 🔗 分享链接解析

| 用户说 | 路由 | 说明 |
|---|---|---|
| "帮我看下这个分享链接" / "这个慧记分享里的内容" | **get-chat-from-share-id.py** | 脚本自动解析 shareId 并获取原文 |
| "http://s.medihub.cn/p/xxx" | **get-chat-from-share-id.py** | 短链自动解析 307 Location，提取 shareId |
| "https://任意域名/#/shareLinkPage?shareId=xxx" | **get-chat-from-share-id.py** | 长链（域名可变），脚本自动提取 shareId |
| "https://任意域名/#/meetingChatNew?shareId=xxx" | **get-chat-from-share-id.py** | 新版长链（域名可变），脚本自动提取 shareId |
| "https://任意域名/#/meetingChatNew?shareId=xxx&userName=张三&personId=123" | **get-chat-from-share-id.py** | 带扩展参数也可解析，只使用 shareId |

### 🧠 AI 分析

| 用户说 | 能力 | 说明 |
|---|---|---|
| "总结一下" / "会议纪要" / "概要" / "说了什么" | 📝 会议总结 | 基于原文生成结构化纪要 |
| "有什么待办" / "谁负责什么" / "跟进事项" | ✅ 待办提取 | 从原文中提取待办 |
| "关于 xxx 讨论了什么" / "财务那块" | 🔍 专题分析 | 按主题提取相关内容 |

---

## 列表查询详解

### 两个维度的区别

| 维度 | 接口 | 口径 | 适用场景 |
|---|---|---|---|
| **归属维度** | chatListByPage | 查「我的」慧记（归属在当前用户名下的记录） | 浏览自己的纪要、搜索、筛选 |
| **会议维度** | listHuiJiIdsByMeetingNumberV2 | 按「我参加的视频会议」查（即使他人录制也可查到） | 已知会议号、查找特定会议的纪要 |

### 路由规则（⚠️ 必须严格遵守）

```
用户提供了会议号？
  ├─ 是 → listHuiJiIdsByMeetingNumberV2（按会议号精确查）
  └─ 否 → chatListByPage（走归属维度查询）
```

**⚠️ 常见错误：用户说"我的进行中会议"但 AI 跳过 chatListByPage 直接用了 listHuiJiIdsByMeetingNumberV2 + 上下文中记的会议号。这是错误的。没有明确会议号时必须走 chatListByPage。**

**⚠️ `lastTs` 默认值**：调用 listHuiJiIdsByMeetingNumberV2 时**必须传 `lastTs`**，默认限制为**最近 10 天**（`当前时间 - 10天` 的毫秒时间戳），避免返回过多无关记录。除非用户明确要求查更早的记录，否则一律带上此参数。

### 按状态查询（⚠️ 一步到位）

脚本已内置 `--state` 参数，**一次 API 调用 + 客户端过滤**，不要分多次查询：

```bash
# 进行中的会议（一条命令，无需二次查询）
python3 chat-list-by-page.py --human --state 0 0 10

# 已完成的会议
python3 chat-list-by-page.py --human --state 2 0 10
```

> 接口默认按 `updateTime` 倒序，进行中的会议必然排在最前面，`pageSize: 10` 绰绰有余。不需要额外加时间范围或多次查询。

### 无结果引导（⚠️ 必须执行）

当用户查询列表（chatListByPage）未找到任何结果时，AI 应主动引导：

- **chatListByPage 查无进行中会议**：提醒用户"归属维度没有找到你名下的进行中会议。如果你正在参加别人发起/录制的会议，请提供会议号，我按会议号帮你查。"
- **chatListByPage 查无任何会议**：提醒用户"归属维度没有找到记录。如果你参加的是他人录制的会议，请提供会议号试试。"

> **原因**：chatListByPage 只查归属在当前用户名下的记录，不包含用户仅"参加"但非"发起/录制"的会议。listHuiJiIdsByMeetingNumberV2 覆盖范围更广（按会议号查所有参与过的记录），但需要用户主动提供会议号。

### 会议状态判断

- **chatListByPage 返回** `combineState`: `0` = 进行中, `1` = 处理中, `2` = 已完成, `3` = 失败
- **listHuiJiIdsByMeetingNumberV2 返回** `recordState` 直接判断：

| `recordState` | 判断结果 | 说明 |
|---|---|---|
| `0` | 进行中 | 实时录制中 |
| `1` |已完成 | 可获取改写原文 |

> 注意：`recordState` 与 chatListByPage 返回的 `combineState` 含义不同，不可混用。

---

## 原文获取策略

这是本 Skill 的核心逻辑。AI 在需要获取会议原文时，**只需调用一个脚本**：

```bash
python3 scripts/huiji/get-transcript.py <meetingChatId> [--name "会议名称"]
```

脚本自动处理全量/增量切换、缓存读写、二次改写，AI **不需要**直接调用 `splitRecordList` / `splitRecordListV2` / `checkSecondSttV2` 接口。

## 分享链接解析策略

当用户消息中出现 AI 慧记分享链接时，AI 统一调用分享脚本，由脚本自动解析 shareId：

```bash
# 直接传 shareId
python3 scripts/huiji/get-chat-from-share-id.py 11be5542-c940-42e4-8528-be71d94f5b53

# 或直接传短链 URL / 短码（脚本自动解析）
python3 scripts/huiji/get-chat-from-share-id.py http://s.medihub.cn/p/128eeeOS
python3 scripts/huiji/get-chat-from-share-id.py 128eeeOS
```

### 支持的链接（域名可变）

- 短链：`http://s.medihub.cn/p/xxxxx`
- 长链：`https://<任意域名>/#/shareLinkPage?shareId=...`
- 新版长链：`https://<任意域名>/#/meetingChatNew?shareId=...`
- 带扩展参数：`https://<任意域名>/#/meetingChatNew?shareId=...&userName=...&personId=...`

### 处理流程

```
用户发送分享链接/短码/shareId
  │
  ├─ 统一调用 get-chat-from-share-id.py（脚本内部自动解析 shareId）
  ├─ 解析规则：优先直接 shareId，其次 URL query/hash，最后短链 307 Location
  └─ 取 srcText 进行总结/待办/专题分析并直接输出结论
```

### 失败处理

- 不能提取 `shareId`：提醒用户重新粘贴完整链接
- 业务错误（`resultCode != 1`）：停止重试并直接反馈原因
- 无 `srcText`：提示暂无可用原文
- 成功拿到 `srcText` 后必须继续执行分析并回复结果，不得只回传中间数据

### 分享场景输出模板（必须遵守）

拿到分享数据后，向用户输出时应先给出基础信息头，再给分析结果：

- 标题：使用会议标题（如 `name`）
- 分享人：使用分享人姓名（如 `srcUser.name`）
- 纪要时间：使用 `createTime`（转换为可读时间）
- 时长：使用 `meetingLength`（转换为分钟/小时）

> 说明：括号内字段仅用于取值，不可原样向用户展示；对外输出必须使用自然语言标签（如"分享人""纪要时间""会议时长"）。

然后再输出：总结 / 待办 / 专题分析等内容。

**禁止项**：
- 不展示 `updateTime`
- 不展示原始 JSON、API 字段名、技术过程描述

### 统一脚本工作流程

```
用户请求会议原文
  │
  ├─ _final 缓存存在？ → 直接返回（二次改写，最优质量）✅
  │
  ├─ _live 缓存标记 completed？ → 尝试拉 checkSecondSttV2
  │     ├─ state=2 成功 → 写入 _final 缓存 → 返回
  │     └─ state=1/3 未就绪 → 返回 _live 缓存
  │
  ├─ _live 缓存存在？ → splitRecordListV2 增量拉取 → 合并到 _live
  │
  └─ 无缓存 → splitRecordList 全量拉取 → 写入 _live 缓存
```

### 双缓存机制

| 缓存文件 | 来源 | 质量 | 说明 |
|---|---|---|---|
| `{id}_live.json` | splitRecordList + splitRecordListV2 | 实时转写 | 进行中会议的增量数据 |
| `{id}_final.json` | checkSecondSttV2 | 二次改写 | 已结束会议的最优数据（可能有发言人） |

**质量优先级**：`_final`（改写） > `_live`（实时） > 全量拉取

### 输出 JSON 结构

```json
{
  "source": "full | incremental | cache_live | cache_final | second_stt",
  "meetingChatId": "xxx",
  "name": "会议名称",
  "status": "ongoing | completed",
  "lastSyncAt": 1716349200000,
  "lastStartTime": 120034,
  "fullText": "拼接好的全文...",
  "fragments": [...]
}
```

`source` 字段说明当前数据来源，AI 可据此判断数据新鲜度，但**不需要向用户暴露此信息**。

### ⚠️ 防丢失保障

- **原子写入**：先写临时文件再 rename，防止写入崩溃损坏缓存
- **自动备份**：每次写入前备份旧缓存为 `.bak`
- **增量校验**：合并后分片数不能比旧缓存少，否则保留旧数据并输出 warning
- **去重策略**：同 startTime 保留 text 更长的版本，防止截断覆盖

---

## AI 分析能力

拿到原文后，AI 根据用户意图提供以下分析。所有分析基于原文内容，不依赖平台预生成的报告或待办。

### 📝 会议总结

**触发**："总结一下"、"会议纪要"、"概要"、"说了什么"

**输出结构**：
- **会议主题**：一句话概括
- **讨论要点**：按议题分段，每段包含核心观点和关键信息。有发言人信息时标注谁说了什么
- **决策/结论**：达成的共识和决定
- **遗留问题**：未解决的事项

**注意事项**：
- 进行中会议必须明确告知"这是截至目前的内容，会议仍在进行中"
- 已结束会议优先使用 checkSecondSttV2 改写原文（有发言人区分）；进行中会议不可使用此接口
- 原文较长时，分段总结后合并，避免遗漏

**⚠️ 严格约束：防幻觉与术语准确性**

原文由语音转文字生成，AI 在总结/待办提取/专题分析时必须遵守以下原则：

1. **禁止虚构以下任何信息**：
   - ❌ 时间信息：会议时间、截止时间、时间节点等
   - ❌ 人物信息：参会人员、负责人、相关人员等
   - ❌ 具体数据：数字、数量、百分比等
   - ❌ 决策结论：会议决策、结论、判断等
   - 只能总结和提炼会议内容中明确提到的信息
   - 所有引用的信息必须能在原始会议内容中找到对应依据

2. **专业术语智能纠错**：
   - 药品名称、疾病名称、医学术语、公司名称等专业领域术语，结合上下文判断是否为语音识别错误（同音字、近音字）
   - 同一术语在报告中统一使用正确标准表述
   - ⚠️ 仅纠正有把握确认的明显错误，无法确定时保持原文，不要臆测

3. **归纳需诚实标注**：
   - AI 归纳的框架名称、分类体系、流程总结等，需标注"AI 根据会议内容归纳"或类似说明
   - 区分"原文原话"和"AI 的归纳提炼"
   - 零散发言拼凑的时间线/决策链，需如实说明"根据多次讨论综合"

### ✅ 待办提取

**触发**："有什么待办"、"谁负责什么"、"跟进事项"

**输出格式**：
- 每条待办：`[待办内容] → [责任人] → [截止时间/优先级]`
- 无法从原文确认的部分标注 ⚠️ 待确认
- 区分「明确分配的待办」和「讨论中未定的事项」
- 按优先级或提及顺序排列
- ⚠️ 待办的责任人、截止时间必须严格来自原文，不可推测或默认

### 🔍 专题分析

**触发**："关于 xxx 讨论了什么"、"财务那块说了什么"

**输出**：
- 相关讨论内容的摘要
- 涉及的发言人（如有）
- 对应的大致时间位置（如"会议中段"、"后半段"）
- 关联的决策或待办（如有）

---

## 本地缓存机制

### 缓存目录（相对 Skill 根目录）

```
.cache/huiji/
```

### 双缓存文件

| 文件 | 命名 | 说明 |
|---|---|---|
| 实时缓存 | `{meetingChatId}_live.json` | 进行中会议（splitRecordList + splitRecordListV2） |
| 改写缓存 | `{meetingChatId}_final.json` | 已结束会议（checkSecondSttV2，最优质量） |

两份数据格式相同：

```json
{
  "meetingChatId": "xxx",
  "name": "产品周会",
  "status": "ongoing | completed",
  "source": "full | incremental | second_stt | cache_live | cache_final",
  "lastSyncAt": 1716349200000,
  "lastStartTime": 120034,
  "fullText": "拼接好的全文...",
  "fragments": [
    { "startTime": 0, "text": "第一段内容...", "realTime": 1716345600000 },
    { "startTime": 120034, "text": "第二段内容...", "realTime": 1716345720000 }
  ]
}
```

### 字段说明

| 字段 | 说明 |
|---|---|
| `meetingChatId` | 会议 ID |
| `name` | 会议名称（来自列表或 `--name` 参数） |
| `status` | `ongoing`（进行中）/ `completed`（已结束） |
| `source` | 数据来源标识 |
| `lastSyncAt` | 上次同步的 Unix 毫秒时间戳 |
| `lastStartTime` | splitRecordListV2 增量查询的游标（分片的 startTime 值） |
| `fullText` | 按 startTime 排序拼接的完整转写文本 |
| `fragments` | 全部分片明细（startTime / text / realTime） |

### 缓存策略

- 用户每次请求会议原文时，`get-transcript.py` 自动管理缓存
- **进行中会议**：增量更新（splitRecordListV2 + `lastStartTime`），合并到 `_live`
- **已结束会议**：`_live` 标记 completed 后自动尝试拉改写，成功写入 `_final`
- 缓存无自动过期，由 AI 在必要时清理或用户主动清理
- ⚠️ AI **不需要**直接操作缓存文件，统一通过 `get-transcript.py` 管理
- **自动清理**：每次运行时自动清理超过 15 天的过期缓存（已结束会议 + 共享资料）

---

## 共享资料机制

多用户可以针对同一场会议共享分析资料，供其他人查看和讨论。

### 共享目录结构（相对 Skill 根目录）

```
.cache/huiji/shared/
└── {meetingNumber}/           # 按会议号隔离
    └── {yyyyMMdd}/            # 按天隔离
        ├── 184500_王晓辉_发言总结.md
        ├── 185200_成伟_AI训练方案.md
        └── ...
```

### 共享文件格式

```markdown
---
meetingNumber: 103760
meetingChatId: huijiXgMt_69c8cc89a61e5c000a9f8b72
author: 王晓辉
created: 2026-03-29 18:45:00
---

## 正文内容...
```

### 使用规则

1. **用户明确说"共享"时才写入**，不自动共享
2. **写入前必须确认**：告知用户即将共享的内容摘要和文件名
3. **文件名规范**：`{HHmmss}_{人名}_{原始标题}.md`，标题必须用原始标题，不额外处理
4. **查询时自动发现**：AI 在查询某场会议时，应检查 `shared/{meetingNumber}/` 目录，如有共享资料需主动提示用户
5. **读取共享**：用户说"看看有什么共享资料"或"分析下XX的那个总结"时，从对应目录读取
6. **时效性**：共享资料超过 15 天自动清理（与缓存同步清理）

### 典型场景

| 用户说 | AI 行为 |
|---|---|
| "把这个分析共享给其他人" | 写入 shared/{meetingNumber}/{yyyyMMdd}/ |
| "103760有什么共享资料" | 列出 shared/103760/ 下的所有文件 |
| "分析下王晓辉刚才的那个总结" | 从 shared/{meetingNumber}/ 下找到对应文件并读取分析 |

---

## _id 字段处理（重要）

chatListByPage 返回的 `_id` 可能有 `__数字` 后缀（如 `abc123__45678`），不能直接用作 `meetingChatId`：

- **处理方式一**：截取双下划线前的部分 → `abc123`
- **处理方式二**：使用 `originChatId` 字段的值

脚本和 AI 在将 chatListByPage 列表项传给 splitRecordList / checkSecondSttV2 / splitRecordListV2 时，必须做此处理。

---

## 时间戳处理规范（⚠️ 必须严格遵守）

所有接口返回的时间字段均为 **13 位毫秒级 Unix 时间戳**（如 `1774763950431`）。

### 转换规则

```
毫秒时间戳 → 秒：除以 1000（1774763950431 / 1000 = 1774763950.431）
秒 → 本地时间：UTC+8（Asia/Shanghai）
```

### 展示规则

**向用户展示时，必须将时间戳转换为人类可读格式**，禁止直接展示原始数字。

- **日期时间**：`2026-03-29 13:59:10`
- **仅日期**：`2026-03-29`
- **仅时间**：`13:59`
- **时长**：毫秒转分钟 → `7624789 ms ≈ 127 分钟 ≈ 2小时7分钟`

### 转换示例

| 原始值（毫秒时间戳） | 转换结果 |
|---|---|
| `1774763950431` | `2026-03-29 13:59:10` |
| `1774704179623` | `2026-03-28 22:42:59` |
| `7624789`（meetingLength，毫秒） | `2小时7分钟` |

### 分片时间戳

- `realTime`：现实时间戳（毫秒），转换为绝对时间展示
- `startTime`（splitRecordList/splitRecordListV2）：录音内偏移量（毫秒），转换为 `00:12:34` 格式的录音内时间点

---

## 多环境部署

本 Skill 可部署在任意 OpenClaw / EasyClaw 环境中。脚本调用使用相对于 SKILL.md 的路径：

```
scripts/huiji/<脚本名>.py
```

OpenClaw 在加载 Skill 时会将完整路径注入上下文，AI 直接拼接使用即可，无需硬编码绝对路径。

---

## 约束

### 执行硬约束（最高优先级）

1. **仅用现有脚本**：只允许调用 `scripts/huiji/` 下已存在脚本完成查询、取数与原文获取。
2. **禁止临时脚本**：禁止创建任何临时调用脚本（如 `temp_*.py`）、一次性中转脚本或额外落盘编排脚本。
3. **失败处理边界**：现有脚本失败时，仅允许重试或切换到其它已存在脚本；若能力缺口确实存在，必须先向用户说明并确认后再改代码。

### 统一规范

1. **鉴权**：所有接口只需 `appKey`（`XG_BIZ_API_KEY`），无需 access-token
2. **生产域名**：`sg-al-ai-voice-assistant.mediportal.com.cn/api/open-api`
3. **重试策略**：脚本内置最多重试 3 次，间隔 1 秒
4. **依赖声明**：鉴权依赖 `cms-auth-skills`

### 脚本使用规则

1. **统一入口**：获取会议原文时**必须使用 `get-transcript.py`**，禁止直接调用 `splitRecordList` / `splitRecordListV2` / `checkSecondSttV2` 脚本
2. **分页默认值**：chatListByPage 的 `pageNum` 从 0 开始；未经用户明确指定时，默认传 `pageNum=0`、`pageSize=10`，查询最新一页记录，禁止自行推断或沿用上下文中的历史页码
3. **增量优先**：有缓存时优先用 splitRecordListV2 增量拉取，减少重复传输
4. **checkSecondSttV2 容错**：已结束会议必须 fallback 到 splitRecordList，刚结束时 checkSecondSttV2 可能无内容
5. **_id 后缀处理**：chatListByPage 返回的 `_id` 可能有 `__数字` 后缀，用作 `meetingChatId` 时需截取或用 `originChatId`

### 路由与加载规则

1. **路由严格遵守**：用户未提供会议号时必须走 chatListByPage（归属维度），禁止从上下文记忆中自动取会议号跳过路由
2. **无结果引导**：chatListByPage 查无结果时，必须主动提醒用户可提供会议号走 listHuiJiIdsByMeetingNumberV2 查询（因为 chatListByPage 不含他人录制/发起的会议）
3. **进行中会议时间过滤**：查询进行中会议时，API 可能返回历史异常数据（录音未正常结束导致状态卡在"进行中"）。AI 必须过滤掉创建时间超过 **2 天**的"进行中"记录，只保留今天和昨天的。向用户展示前静默过滤，无需解释
4. **分享链接识别**：域名不做强绑定。只要消息中出现可解析 URL，且命中任一条件即识别为 AI 慧记分享链接：
    - URL 中包含 `shareId=` 参数；
    - hash 路由包含 `#/shareLinkPage` 或 `#/meetingChatNew`；
    - 或短链形态 `s.medihub.cn/p/`（由脚本内解析 307 Location 并提取 shareId）。
    - URL 中的其它参数（如 `userName`、`personId`、渠道参数等）一律忽略，不参与路由判断。
5. **分享原文入口**：分享链接原文获取统一使用 `get-chat-from-share-id.py`。允许直接传 `shareId`、短链 URL 或短码；优先让脚本内部自动解析，避免在外部额外引入 `web_fetch` 前置步骤

### 宪章

1. **AI 分析基于原文**：所有分析由 AI 基于转写原文完成，不依赖平台预生成的报告或待办
2. **时间戳必须转换**：所有时间戳字段（createTime、startTime、realTime、meetingLength 等）向用户展示时必须转换为可读格式，禁止直接展示原始数字。详见上方「时间戳处理规范」
3. **防幻觉与术语准确性**：总结/待办/专题分析时，禁止虚构时间、人物、数据、决策；专业术语结合上下文智能纠错但不确定时保持原文；AI 归纳需诚实标注来源。详见上方「严格约束：防幻觉与术语准确性」
4. **API 校验错误不重试**：接口返回 `resultCode` 不为 `1` 的业务错误时，AI 必须**停止执行**，直接向用户展示错误原因，不得反复修改参数重试同一条接口
5. **隐藏技术细节**：向用户输出时禁止展示内部技术过程，包括但不限于：
    - 原文获取策略的选择过程（如"先尝试 checkSecondSttV2"、"fallback 到 splitRecordList"等）
    - 接口调用细节（如"调了 chatListByPage 接口"、"返回 resultCode: 1"等）
    - 脚本名称、缓存机制、增量拉取等实现细节
    - **所有 API 字段名**（后端返回的任何 JSON key），必须全部翻译为人类语言后呈现
    - 原始 JSON 数据结构
    - **原则**：用户只需要看到结果（会议内容/总结/待办），不需要知道你怎么拿到的
6. **输出约束（分享场景）**：拿到分享原文后，AI 必须先输出基础信息头（标题、分享人、纪要时间、会议时长），再输出总结/待办/专题分析结果；禁止直接向用户展示原始 JSON 结构、API 字段名或仅回传 `srcText`


---

## 能力树

```
ai-huiji/
├── SKILL.md
├── .cache/
│   └── huiji/                              # 会议原文缓存（按 meetingChatId 存储）
│       └── shared/                         # 共享资料（按 meetingNumber/yyyyMMdd 存储）
├── openapi/
│   └── huiji/
│       ├── api-index.md                    # 接口索引
│       ├── chat-list-by-page.md            # chatListByPage 查询我的慧记列表
│       ├── list-by-meeting-number.md       # listHuiJiIdsByMeetingNumberV2 按会议号查询慧记列表
│       ├── split-record-list.md            # splitRecordList 全量分片转写
│       ├── split-record-list-v2.md         # splitRecordListV2 增量分片转写
│       ├── check-second-stt-v2.md          # checkSecondSttV2 改写原文状态
│       └── get-chat-from-share-id.md       # 通过 shareId 获取分享原文
├── examples/
│   └── huiji/
│       └── README.md                        # 面向外部部署者的 Quick Start 手册（触发示例 + 脚本用法）
└── scripts/
    └── huiji/
        ├── README.md                        # 脚本清单 + 使用示例
        ├── get-transcript.py                # 🌟 统一入口（自动处理全量/增量/改写/缓存）
        ├── chat-list-by-page.py            # chatListByPage 分页查询
        ├── list-by-meeting-number.py       # listHuiJiIdsByMeetingNumberV2 按会议号查询
        ├── split-record-list.py            # splitRecordList 全量分片转写（内部使用）
        ├── split-record-list-v2.py         # splitRecordListV2 增量分片转写（内部使用）
        ├── check-second-stt-v2.py          # checkSecondSttV2 改写原文状态（内部使用）
        └── get-chat-from-share-id.py       # 按 shareId 获取分享原文
```
