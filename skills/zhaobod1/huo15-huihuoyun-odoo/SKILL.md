---
name: huo15-claude-odoo
displayName: 火一五·辉火云企业套件插件
description: 自然语言操作 辉火云企业套件 — 实施经理助手，覆盖任务、CRM、项目、工单、财务、销售
version: 1.1.0
---

# 辉火云企业套件插件使用指南

OpenClaw 龙虾的辉火云企业套件插件。连接后即可用自然语言全面操作辉火云系统，
尤其适合**实施经理、项目经理、销售经理**的日常工作场景。

---

## 首次配置

### 方式一：通过对话连接（推荐）

> 帮我连接辉火云企业套件，地址 https://www.huo15.com，数据库 huo15，账号 admin@huo15.com，密码 xxxxxx

龙虾会自动调用 `odoo_connect` 工具，连接信息保存本地，下次启动自动恢复。

### 方式二：通过 openclaw.plugin.json 预配置

```json
{
  "odoo": {
    "url": "https://www.huo15.com",
    "db": "huo15",
    "username": "admin@huo15.com",
    "password": "your-password"
  },
  "sync": {
    "enabled": true,
    "intervalSeconds": 30,
    "channels": ["todo", "activity", "message", "email", "calendar"]
  }
}
```

---

## ⭐ 实施经理每日概况

每天早上第一句话：

> 今天有什么工作？

龙虾会一次性汇总：

| 类别 | 内容 |
|------|------|
| 📋 今日截止任务 | project.task 今日 deadline |
| ⏰ 活动提醒 | 今日及逾期的 mail.activity |
| 🎫 待处理工单 | 指派给我的 helpdesk.ticket |
| 💰 逾期应收 | 未付款且已逾期的 account.move |
| 🏆 商机跟进 | 需要今日跟进的 crm.lead |
| 💬 未读消息 | mail.message 未读数 |

---

## 待办 / 任务

| 你说 | 龙虾做什么 |
|------|-----------|
| 帮我写个待办 | 追问标题后创建任务（project.task） |
| 帮我创建任务：明天发报价单给华为 | 直接创建，截止日期设为明天 |
| 紧急待办：处理生产故障 | 创建优先级=3（紧急）的任务 |
| 看看我的待办 | 列出我的全部待办 |
| 我今天有什么要做的 | 列出今日截止任务 + 今日活动 |
| 把任务 #123 标记完成 | 更新 state = 1_done |
| 把任务 #123 截止日期改到下周五 | 更新 date_deadline |
| 任务 #123 调高优先级为紧急 | 更新 priority = 3 |

---

## 活动提醒

活动（mail.activity）关联到具体的辉火云记录（任务、商机、客户等）。

| 你说 | 龙虾做什么 |
|------|-----------|
| 提醒我明天开会 | 创建活动提醒，截止明天 |
| 帮我在客户 #42 上设一个跟进提醒 | 在 res.partner #42 创建活动 |
| 查看我今天有哪些活动 | 列出今日到期活动 |
| 查看逾期提醒 | 列出今日及逾期活动 |
| 有哪些活动类型 | 调用 odoo_activity_types |

> 常用 activity_type_id：4=待办、1=邮件、2=电话、3=会议（具体以系统为准，可通过 odoo_activity_types 查询）

---

## 日历 / 会议

| 你说 | 龙虾做什么 |
|------|-----------|
| 安排一个会议 | 追问主题和时间后创建 calendar.event |
| 明天上午10点安排产品评审会，持续1小时 | 创建 10:00~11:00 |
| 下午2点约华为团队开会 | 创建 14:00~15:00 |
| 查看我的日程安排 | odoo_search(model="calendar.event") |

---

## CRM 商机管理

| 你说 | 龙虾做什么 |
|------|-----------|
| 查看我的商机 | 查看我的商机管道 |
| 查看全部销售人员的商机 | odoo_crm_pipeline(all_users=true) |
| 新建一个商机：华为 ERP 项目 | 创建商机，追问金额/阶段 |
| 把商机 #88 推进到下一阶段 | 更新 stage_id |
| 把商机 #88 赢了 | 调用 odoo_crm_won |
| 商机 #88 输了 | 调用 odoo_crm_lost |
| 商机 #88 预计收入改为 50 万 | 更新 expected_revenue |
| 查看 CRM 各阶段 | odoo_search(model="crm.stage") |

---

## 项目管理

| 你说 | 龙虾做什么 |
|------|-----------|
| 项目进展如何 | 查看所有项目列表 + 里程碑 |
| 「辉火云实施」项目进度 | 查看指定项目 + 其里程碑 |
| 里程碑完成了多少 | 返回每个里程碑的 done_tasks/task_count |
| 今天记录了3小时的需求分析工时 | 创建工时记录 3h |
| 在任务 #55 上记录 2 小时工时 | 关联任务的工时记录 |

---

## 客服工单（Helpdesk）

| 你说 | 龙虾做什么 |
|------|-----------|
| 查看我的工单 | 列出指派给我的工单 |
| 查看紧急工单 | odoo_tickets(priority="3") |
| 帮我提交一个问题：系统登录失败 | 创建 helpdesk.ticket |
| 客户华为的工单 | odoo_tickets(partner_id=...) |

---

## 销售 & 采购

| 你说 | 龙虾做什么 |
|------|-----------|
| 查看销售订单 | 列出有效销售订单 |
| 查看待确认的报价单 | odoo_sale_orders(state="draft") |
| 查看采购订单 | 列出有效采购订单 |
| 查询到货日期 | odoo_purchase_orders，查 planned_arrival |

---

## 财务 / 发票

| 你说 | 龙虾做什么 |
|------|-----------|
| 查看发票 | 列出最近发票 |
| 有哪些客户还没付款 | odoo_invoices(payment_state="not_paid") |
| 逾期应收账款 | odoo_invoices(overdue_only=true) |
| 查供应商账单 | odoo_invoices(move_type="in_invoice") |

---

## 消息 / 邮件

| 你说 | 龙虾做什么 |
|------|-----------|
| 查看我的消息 | 列出未读 chatter 消息 |
| 看看邮件通知 | 列出收件箱未读通知 |
| 给商机 #88 发条消息：正在跟进 | 在 crm.lead #88 上发 chatter |

---

## 通用搜索

| 你说 | 模型 | 示例 |
|------|------|------|
| 帮我查「华为」客户 | res.partner | name ilike 华为 |
| 查所有活跃项目 | project.project | active=true |
| 查库存情况 | stock.quant | — |
| 查员工列表 | hr.employee | — |
| 查产品 | product.product | — |
| 查活动类型 | mail.activity.type | — |
| 查 CRM 阶段 | crm.stage | — |
| 查工单阶段 | helpdesk.stage | — |

---

## 通知同步（后台轮询）

插件启动后每 30 秒（可配置）自动检查：

| 通道 | 触发条件 |
|------|---------|
| todo | 我的任务有新增或更新 |
| activity | 今日到期活动 |
| message | 新 chatter 消息 |
| email（可选）| 新邮件通知 |
| calendar（可选）| 今明两天内的新日历事件 |

---

## 工具完整列表（23 个）

### 基础
| 工具 | 说明 |
|------|------|
| odoo_connect | 连接辉火云企业套件 |
| odoo_status | 检查连接状态和轮询状态 |

### 任务 & 活动
| 工具 | 说明 |
|------|------|
| odoo_create_task | 创建待办任务 |
| odoo_list_tasks | 查看待办列表（支持 today_only/state 筛选） |
| odoo_update_task | 更新任务（状态/阶段/截止日期/优先级） |
| odoo_create_activity | 创建活动提醒（关联到记录） |
| odoo_list_activities | 查看今日及逾期活动 |
| odoo_activity_types | 查询活动类型列表 |
| odoo_create_event | 创建日历事件/会议 |

### 消息
| 工具 | 说明 |
|------|------|
| odoo_get_messages | 查看未读消息/邮件通知 |
| odoo_send_message | 向记录发送 chatter 消息 |

### CRM
| 工具 | 说明 |
|------|------|
| odoo_crm_pipeline | 查看商机管道 |
| odoo_crm_create | 创建商机/线索 |
| odoo_crm_update | 更新商机信息 |
| odoo_crm_won | 标记赢单 |
| odoo_crm_lost | 标记输单 |

### 项目 & 工时
| 工具 | 说明 |
|------|------|
| odoo_project_overview | 项目列表 + 里程碑进度 |
| odoo_timesheet_log | 记录工时 |

### 销售 & 采购 & 财务
| 工具 | 说明 |
|------|------|
| odoo_sale_orders | 查看销售订单 |
| odoo_purchase_orders | 查看采购订单 |
| odoo_invoices | 查看发票/账单（支持逾期筛选） |

### 客服
| 工具 | 说明 |
|------|------|
| odoo_tickets | 查看客服工单 |
| odoo_ticket_create | 创建客服工单 |

### 搜索 & 助手
| 工具 | 说明 |
|------|------|
| odoo_search | 通用搜索（任意模型任意条件） |
| odoo_daily_briefing | ⭐ 实施经理每日工作概况 |

---

## 常见问题

**Q: 连接失败怎么办？**
A: 检查 URL（末尾不带斜杠）、数据库名（区分大小写）、账号密码。用 `odoo_status` 查看当前状态。

**Q: 活动提醒需要哪些参数？**
A: 必须提供 `res_model`（如 crm.lead）、`res_id`（记录ID）、`activity_type_id`、`date_deadline`。
通过 `odoo_activity_types` 查询系统中的活动类型。

**Q: 商机阶段 ID 怎么获取？**
A: 通过 `odoo_search(model="crm.stage")` 查询所有 CRM 阶段及其 ID。

**Q: 每日概况失败提示没有 helpdesk 模块？**
A: 系统中未安装 Helpdesk 模块时，工单部分会自动跳过，其他项正常返回。

---

## Changelog

- **v1.1.0** — CRM 商机管道（查询/创建/赢/输/更新）、项目里程碑、工时记录、销售/采购订单、Helpdesk 工单、发票/逾期账款查询、任务状态更新、活动类型查询、实施经理每日概况（odoo_daily_briefing）
- **v1.0.0** — 基础版：待办/任务、活动提醒、日历事件、消息/邮件、通用搜索、后台轮询
