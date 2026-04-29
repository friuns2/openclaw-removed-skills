---
name: feishu-room-booking
description: |
  飞书会议室查询与预订。当用户提到"查会议室"、"订会议室"、"空闲会议室"、"预订会议室"、"开会"、"找个会议室"、"F4会议室"、"紫金会议室"、"哪个会议室有空"、或者创建会议时需要自动匹配空闲会议室时，必须使用此 skill。也适用于用户要求创建日程并指定楼栋/区域时自动完成会议室预订的场景。也适用于用户提到"会议室偏好"、"我的偏好"、"候补"、"补订会议室"、"自动订会议室"、"下周去哪"、"工区"、"出差"时。
---

# 飞书会议室查询与预订

管理飞书会议室的忙闲查询、自动匹配、日程预订、**多工区偏好管理**、**周工区管理**和候补轮询。

## 前置依赖

- `lark-cli` 已安装且 bot 身份可用
- 飞书应用已开通相关权限（calendar:calendar.free_busy:read, calendar:calendar.event:create 等）
- 数据文件：`references/room-mapping.json`、`references/user-preferences.json`、`references/room-waitlist.json`、`references/weekly-workspace.json`
- 脚本目录：`scripts/`

## 工具脚本

所有会议室操作**必须通过脚本**，不要手写 bash 循环。

### query_rooms.py — 会议室查询（不变）

```bash
# 列出所有楼栋
python3 scripts/query_rooms.py --list-buildings

# 列出指定楼栋的会议室
python3 scripts/query_rooms.py --list-rooms -b "丽金"

# 查询空闲会议室（表格输出）
python3 scripts/query_rooms.py -b "丽金" \
  -s "2026-04-20T14:00:00+08:00" \
  -e "2026-04-20T15:00:00+08:00" -o table

# 按容量筛选
python3 scripts/query_rooms.py -b "丽金" \
  -s "2026-04-20T14:00:00+08:00" \
  -e "2026-04-20T15:00:00+08:00" \
  --capacity-gte 8 -o table
```

### workspace_manager.py — 周工区管理（🆕 新增）

```bash
# 获取当前工区信息
python3 scripts/workspace_manager.py --get

# 设置本周工区
python3 scripts/workspace_manager.py --set-current --workspace "丽金智地中心 B座"

# 设置下周工区
python3 scripts/workspace_manager.py --set-next --workspace "紫金数码园4号楼"

# 推荐下周工区（基于本周会议室使用频率）
python3 scripts/workspace_manager.py --recommend

# 手动周切换
python3 scripts/workspace_manager.py --advance-week

# 清空下周设置
python3 scripts/workspace_manager.py --clear-next
```

### manage_preferences.py — 偏好管理（简化版：仅按工区维护会议室偏好列表）

```bash
# 设置偏好（指定工区 + 会议室列表）
python3 scripts/manage_preferences.py --set \
  --user "ou_xxx" --building "丽金智地中心 西塔" \
  --preferred-rooms "F11-15,F11-07"

# 读取偏好（指定工区）
python3 scripts/manage_preferences.py --get --user "ou_xxx" --building "丽金智地中心 西塔"

# 读取所有偏好
python3 scripts/manage_preferences.py --get --user "ou_xxx"

# 列出所有用户偏好
python3 scripts/manage_preferences.py --list

# 删除指定工区的偏好
python3 scripts/manage_preferences.py --delete --user "ou_xxx" --building "丽金智地中心 西塔"
```

### watch_waitlist.py — 候补管理（🔄 去掉容量限制）

```bash
# 查看候补状态
python3 scripts/watch_waitlist.py --status

# 执行一轮轮询
python3 scripts/watch_waitlist.py --poll

# 添加候补（只需指定楼栋，不限容量）
python3 scripts/watch_waitlist.py --add \
  --event-id "xxx" --summary "周会" \
  --start "2026-04-20T14:00:00+08:00" --end "2026-04-20T15:00:00+08:00" \
  --building "丽金"

# 移除候补
python3 scripts/watch_waitlist.py --remove --event-id "xxx"

# 清理过期候补
python3 scripts/watch_waitlist.py --clean
```

## 数据文件

| 文件 | 用途 |
|------|------|
| `references/room-mapping.json` | 会议室资源 ID 映射 |
| `references/user-preferences.json` | 用户会议室偏好（按工区存储偏好会议室列表） |
| `references/room-waitlist.json` | 候补预订队列（不限容量） |
| `references/weekly-workspace.json` | 🆕 周工区记录（本周/下周） |

## 核心流程

### 流程 F：工区管理（🆕 新增）

管理用户的工区，支持**随时切换**（出差、临时调整）+ **周期兜底**（周五提醒下周）。

**第 1 层：显式切换（随时触发）：**
- 用户随时说"**今天我在紫金**"、"**这周去上海**"、"**明天起去丽金**"
- 立刻生效，支持指定日期范围
- 数据结构为 `segments` 数组，每个 segment 包含 from/to/workspace
- 新 segment 会自动截断与之重叠的旧 segment

| 用户说 | 解析 | 动作 |
|--------|------|------|
| "今天在紫金" | 只影响今天 | `set --workspace "紫金" --from "今天" --to "今天"` |
| "这周去上海" | 本周剩余 | `set --workspace "上海新江湾" --from "今天" --to "本周日"` |
| "明天起去紫金" | 明天开始 | `set --workspace "紫金" --from "明天"` |
| "下周回丽金" | 下周开始 | `set-next --workspace "丽金"` |

**第 2 层：周期兜底（周五提醒）：**
- Heartbeat 在周五检测下周工区是否已设置
- 未设置 → 执行 `--recommend` 推荐下周工区（基于本周会议室使用频率）
- 弹卡片询问用户确认
- 用户选择后 `--set-next` 写入
- 已设置 → 跳过，不打扰

**查询当前工区：**
- `--get` 自动根据今天的日期匹配 segment
- `--timeline` 展示完整工区时间线

**工区使用规则：**
- 所有流程默认使用 `--get` 返回的当前工区
- 用户显式指定楼栋时，覆盖默认工区
- 周一时 next_week 不会被自动提升，需通过显式 set 或新的 segment 覆盖

### 流程 A：查询空闲会议室

用户只想看哪些会议室有空。

1. **解析意图** — 时间段、楼栋（默认取周工区）、容量需求
2. **确定日期** — ⚠️ 严格验证星期几
3. **执行查询** — `python3 scripts/query_rooms.py -b "楼栋" -s ... -e ... -o table`
4. **呈现结果** — 直接转发脚本输出

### 流程 B：创建会议并自动预订

用户要开会，需要创建日程 + 匹配会议室。

1. **解析意图** — 标题、时间、楼栋（默认取周工区）、容量、参会人
2. **确定日期** — ⚠️ 严格验证星期几
3. **确定工区** — 读取 `weekly-workspace.json` 的 `current_week.workspace`，用户可显式覆盖
4. **读取该工区的偏好** — `python3 scripts/manage_preferences.py --get --user "ou_xxx" --building "丽金智地中心 西塔"`
   - 有偏好 → 偏好会议室排在选择列表最前面
   - **该工区无偏好** → 弹卡片让用户选，选择后写入偏好
5. **查询空闲会议室** — 用脚本查询，带上容量筛选
6. **用户选择** — `feishu_ask_user_question` 弹卡片（按偏好排序）
7. **创建日程** — `feishu_calendar_event` create
8. **添加会议室+参会人** — `feishu_calendar_event_attendee` create
   - ⚠️ 字段名是 `attendee_id`，不是 `id`
9. **验证 RSVP** — 等 5 秒后查 attendee list
10. **Fallback** — decline 时自动换下一个空闲会议室

### 流程 C：会议室偏好管理

每个工区独立维护偏好会议室列表（仅存储用户手动设置的偏好，无自动学习）。

**设置偏好：**
- 用户说"在丽金我偏好 F11-15 和 F11-07"
- 调用 `--set --building "丽金智地中心 西塔" --preferred-rooms "F11-15,F11-07"` 写入

**读取偏好：**
- `--get --user "ou_xxx" --building "丽金智地中心 西塔"` 读取指定工区偏好
- `--get --user "ou_xxx"` 读取全部偏好

**应用偏好：**
- 流程 B/D 自动读取当前工区的偏好
- 偏好会议室排在选择列表最前面
- 没有偏好时按容量从大到小排序

**删除偏好：**
- `--delete --user "ou_xxx" --building "丽金智地中心 西塔"` 删除指定工区偏好
- `--delete --user "ou_xxx"` 删除全部偏好

### 流程 D：扫描日程自动补订（🔄 收窄范围）

自动检测用户日程中缺少会议室的会议并补订。

**触发方式：**
- **手动**：用户说"帮我检查有没有缺会议室的日程"、"补订会议室"
- **自动**：Heartbeat 定时任务

**扫描步骤：**
1. 调用 `feishu_calendar_event` list 获取用户近期日程
2. **严格过滤**（只补订符合条件的会议）：
   - ✅ `self_rsvp_status = "accept"`（已接受的会议，不管发起者是谁）
   - ❌ `self_rsvp_status != "accept"` → 跳过（未接受/待定/拒绝的会议不补订）
   - ❌ 已有 resource 参会人 → 跳过
   - ❌ 标题含 "1:1/线上/phone/聚餐/假期" → 跳过
   - ❌ 全天事件 → 跳过
   - ❌ 纯线上视频会议（无 location）→ 跳过
3. 对符合条件的会议：
   - 读取**当前周工区**作为默认楼栋
   - **先获取该时段所有空闲会议室的完整列表**
   - 有偏好 → 按偏好排序，自动选偏好第一个（不弹卡片）
   - 无该工区偏好 → 弹卡片让用户选
   - **全部满** → 加入候补（不限容量，只指定楼栋）

**关键变化：**
- ❌ 不再补订用户未接受的会议
- ❌ 不再补订聚餐、假期等特殊类型
- ✅ 先拿到完整空闲列表，再精准预订（避免竞态）
- ✅ 按当前周工区查询

### 流程 E：候补轮询（🔄 不限容量）

会议室满了时的自动候补机制。

**候补条件放宽：**
- ❌ **不使用 capacity_gte 筛选**（小会议室也比没有强）
- ❌ **不使用 preferred_rooms 排序**（候补时优先容量大的）
- ✅ **只需指定候补楼栋**

**添加候补：**
- 流程 D/B 发现全满时，调用 `watch_waitlist.py --add --building "楼栋"`
- 只需传 `--building`，不再传 `--capacity-gte`

**轮询检查：**
- Heartbeat 或手动触发 `watch_waitlist.py --poll`
- 扫描该楼栋**所有**空闲会议室（不限容量）
- 按容量从大到小排序，优先大会议室
- 找到空闲 → 标记为 ready，通知 agent 执行预订
- 仍然满 → 记录已尝试列表，等待下次轮询

**预订成功后：**
- agent 添加会议室 → 验证 RSVP accept → 从候补移除
- decline → 保持 waiting 状态

**清理：**
- 定期 `--clean` 清理已过期的候补（开始时间超过 1 小时）

---

## 交互规范

### 自然语言解析
| 用户说 | 解析 |
|--------|------|
| "明天下午3点开会" | 明天 15:00，默认 1 小时，用当前周工区 |
| "下周去紫金" | 流程 F，设置下周工区 |
| "下周在哪" | 流程 F，获取下周工区 |
| "帮我推荐下周工区" | 流程 F，基于使用统计推荐 |
| "找个会议室" | 流程 A，用当前周工区查询 |
| "在紫金4号楼找个会议室" | 流程 A，用指定楼栋查询 |
| "帮我设个偏好，丽金用 F11-15 和 F11-07" | 流程 C，设置丽金工区偏好 |
| "查一下我有没有缺会议室的会" | 流程 D，扫描补订 |
| "候补状态怎么样了" | 流程 E，查看候补 |

### 用户确认原则
- **流程 B**（主动创建）：必须确认时间、会议室、参会人
- **流程 D**（自动补订）— 见下方「流程 D 交互策略」
- **流程 E**（候补预订）：不需要确认，直接执行
- **流程 F**（周工区）：有推荐时弹卡片确认

### 流程 D 交互策略（无感预订 vs 交互询问）

扫描日程自动补订时，按以下决策树判断是否需要交互：

```
用户是否指定了工区？
├── 是 → 该工区有偏好？
│   ├── 是 → ✅ 无感预订：扫描 → 按偏好自动匹配 → 静默补订
│   └── 否 → ❓ 交互：弹卡片让用户选会议室 → 补订 → 写入偏好
└── 否 → 读取当前周工区（workspace_manager --get）
    ├── 有当前工区 → 该工区有偏好？
    │   ├── 是 → ✅ 无感预订：扫描 → 按偏好自动匹配 → 静默补订
    │   └── 否 → ❓ 交互：弹卡片让用户选会议室 → 补订 → 写入偏好
    └── 无当前工区 → ❓ 交互：弹卡片先问工区，再问会议室 → 补订
```

**关键原则：**
- **工区已知 + 偏好已知** → 全自动，零交互，最后汇总结果通知用户
- **工区已知 + 偏好未知** → 只弹一次卡片选会议室（选择后自动写入偏好）
- **工区未知** → 先问工区再问会议室（两步合一或分两步弹卡片）
- 补订结果无论是否交互，完成后都**统一汇报**：补订了 N 个会议室，哪些成功哪些失败

### 首次在新工区预订
当用户在某个工区没有偏好记录时：
1. 弹卡片让用户从该工区所有会议室中选择偏好
2. 选择后写入偏好，后续自动应用

---

## 注意事项

1. **room_id vs user_id**：freebusy 用 `room_id`，每次只查一个
2. **会议室是 resource**：attendee type 为 `"resource"`，`attendee_id` 传 `omm_xxx`
3. **预订异步**：添加后等 5 秒再查 RSVP
4. **时区统一**：`Asia/Shanghai`（+08:00），ISO 8601
5. **日期验证**：涉及相对时间必须验证星期几
6. **脚本优先**：统一用 scripts/ 下的脚本
7. **时间修改风险**：patch 改时间后会议室可能 decline，必须重新验证
8. **🆕 工区默认**：所有流程默认使用周工区，用户显式指定时覆盖
10. **🆕 补订范围**：只要是已接受的会议（`self_rsvp_status = "accept"`），不管发起者是谁都可以补订
11. **🆕 候补不限容量**：小会议室也可以候补，提高成功率
12. **🆕 先查空再订**：补订时先拿完整空闲列表，按偏好排序后精准预订
