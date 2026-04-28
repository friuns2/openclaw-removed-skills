---
name: flowyteam
version: "1.1.1"
description: Manage FlowyTeam projects, tasks, OKRs, KPIs, HR, CRM, finance, support tickets, attendance, and more via MCP — 34 tools for complete workspace management.
license: MIT
author: flowyteam
homepage: https://flowyteam.com
source: https://github.com/flowy-team/clawhub/tree/master/skills/flowyteam-mcp
metadata:
  clawhub:
    requires:
      env:
        - name: FLOWYTEAM_API_TOKEN
          description: "API token from FlowyTeam Settings → MCP & AI Integration."
          required: true
---

# FlowyTeam MCP

Connect Claude Code (or any MCP-compatible AI agent) to your FlowyTeam workspace.
Manage projects, tasks, OKRs, KPIs, employees, leads, clients, tickets, attendance,
leave, invoices, estimates, contracts, expenses, events, notices, time logs, and more
— all via natural language.

**Platform:** [flowyteam.com](https://flowyteam.com) — All-in-one SaaS for team
productivity and performance management. 7,000+ organizations, 140+ countries.

---

## Endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /api/mcp/gateway` | None (per-call) | **Gateway** — single URL for everything; `auth_register`, `auth_verify_email` & `auth_login` run without token, all other tools read Bearer from header |
| `POST /api/v2/mcp/rpc` | Bearer token | **RPC** — authenticated-only endpoint for all 31 workspace tools |

---

## Setup

### Recommended — Connect with API token

```bash
claude mcp add flowyteam \
  --transport http \
  --url https://flowyteam.com/api/v2/mcp/rpc \
  --header "Authorization: Bearer $FLOWYTEAM_API_TOKEN"
```

Get your token: FlowyTeam → **Settings → MCP & AI Integration** → copy token.

### Claude Desktop / Cursor (`mcp.json`)

```json
{
  "mcpServers": {
    "flowyteam": {
      "transport": "http",
      "url": "https://flowyteam.com/api/v2/mcp/rpc",
      "headers": {
        "Authorization": "Bearer YOUR_API_TOKEN"
      }
    }
  }
}
```

---

## Protocol

- **Gateway:** `POST https://flowyteam.com/api/mcp/gateway`
- **RPC:** `POST https://flowyteam.com/api/v2/mcp/rpc`
- **Transport:** Streamable HTTP (JSON-RPC 2.0)
- **Auth:** `Authorization: Bearer <api_token>` (not required for `auth_register` / `auth_verify_email` / `auth_login`)
- **Protocol Version:** `2024-11-05`

All workspace tools share a `method` parameter to select the HTTP verb:

| `method` | Operation |
|---|---|
| `GET` | Read / list records |
| `POST` | Create a new record |
| `PUT` | Update an existing record |
| `DELETE` | Delete a record |

Auth tools (`auth_register`, `auth_verify_email`, `auth_login`) only use `POST` and do not need a `method` field.

---

## Tools (34)

> All tools require a valid `FLOWYTEAM_API_TOKEN` Bearer token. See [Setup](#setup) above.

---

### 1. `tasks` *(requires Bearer token)*

**Manage tasks and assignments**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Task ID — required for PUT / DELETE |
| `project_id` | integer \| string | Filter by project (GET) or assign to project (POST) |
| `heading` | string | Task title — required for POST |
| `description` | string | Task description |
| `status` | string | Task status (e.g. `incomplete`, `complete`) |
| `priority` | string | `low` / `medium` / `high` / `urgent` |
| `assigned_to` | integer \| string | Employee user ID to assign |
| `user_id` | integer \| string | Alternative employee ID field |
| `due_date` | string | Due date `YYYY-MM-DD` |
| `task_category_id` | integer \| string | Task category ID |
| `search` | string | Search by keyword |

**Examples:**

```json
// GET — list incomplete tasks in project 12
{ "method": "GET", "project_id": 12, "status": "incomplete" }

// POST — create task
{ "method": "POST", "heading": "Write API docs", "project_id": 12,
  "due_date": "2026-05-10", "priority": "medium", "assigned_to": 7 }

// PUT — mark complete
{ "method": "PUT", "id": 101, "status": "complete" }

// DELETE
{ "method": "DELETE", "id": 101 }
```

---

### 2. `projects`

**Manage projects and project workflow**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Project ID — required for PUT / DELETE |
| `project_name` | string | Project name — required for POST |
| `status` | string | `not started` / `in progress` / `on hold` / `finished` |
| `start_date` | string | Start date `YYYY-MM-DD` |
| `deadline` | string | Deadline `YYYY-MM-DD` |
| `client_id` | integer \| string | Client ID |
| `category_id` | integer \| string | Project category ID |
| `project_summary` | string | Short description |
| `notes` | string | Additional notes |
| `search` | string | Search by keyword |

**Examples:**

```json
// GET — list in-progress projects
{ "method": "GET", "status": "in progress" }

// POST — create project
{ "method": "POST", "project_name": "Mobile App v2",
  "start_date": "2026-06-01", "deadline": "2026-09-30", "client_id": 3 }

// PUT — update status
{ "method": "PUT", "id": 12, "status": "on hold" }

// DELETE
{ "method": "DELETE", "id": 12 }
```

---

### 3. `employees`

**Manage employees and team members**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Employee ID — required for PUT / DELETE |
| `name` | string | Full name — required for POST |
| `email` | string | Email — required for POST |
| `password` | string | Password — required for POST |
| `department_id` | integer \| string | Department ID |
| `designation_id` | integer \| string | Job designation ID |
| `employee_id` | string | Custom employee ID/code |
| `joining_date` | string | Joining date `YYYY-MM-DD` |
| `status` | string | `active` / `inactive` |
| `search` | string | Search by name or email |

**Examples:**

```json
// GET — list active employees in department 4
{ "method": "GET", "department_id": 4, "status": "active" }

// POST — create employee
{ "method": "POST", "name": "John Doe", "email": "john@company.com",
  "password": "secret123", "department_id": 4, "designation_id": 2,
  "joining_date": "2026-06-01" }

// PUT — deactivate
{ "method": "PUT", "id": 7, "status": "inactive" }

// DELETE
{ "method": "DELETE", "id": 7 }
```

---

### 4. `objectives`

**Manage OKR objectives**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Objective ID — required for PUT / DELETE |
| `heading` | string | Objective title — required for POST |
| `description` | string | Objective description |
| `level` | string | `company` / `department` / `individual` |
| `type` | string | `qualitative` / `quantitative` |
| `status` | string | `on track` / `at risk` / `behind` / `achieved` |
| `cycle_id` | integer \| string | Performance cycle ID |
| `department_id` | integer \| string | Filter by department |
| `search` | string | Search by keyword |

**Examples:**

```json
// GET — company-level objectives in cycle 3
{ "method": "GET", "cycle_id": 3, "level": "company" }

// POST — create objective
{ "method": "POST", "heading": "Improve NPS Score",
  "level": "company", "cycle_id": 3, "type": "qualitative" }

// PUT — update status
{ "method": "PUT", "id": 20, "status": "at risk" }

// DELETE
{ "method": "DELETE", "id": 20 }
```

---

### 5. `key-result`

**Manage OKR key results linked to objectives**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Key result ID — required for PUT / DELETE |
| `objective_id` | integer \| string | Filter by objective (GET) |
| `krs_owner` | integer \| string | Objective ID owning this KR — required for POST |
| `krs_title` | string | Key result title |
| `krs_description` | string | Description |
| `krs_init` | number \| string | Initial value |
| `krs_tar` | number \| string | Target value |
| `krs_now` | number \| string | Current value |
| `krs_weight` | number \| string | Weight (1–100) |
| `krs_unit` | string | Unit (default `%`) |
| `krs_leader` | integer \| string | Employee details ID for KR owner |
| `krs_conf` | string | Confidence level |
| `krs_remarks` | string | Remarks |
| `associate_kpis` | array | Array of indicator IDs to link |
| `per_page` | integer | Page size |
| `page` | integer | Page number |

**Examples:**

```json
// GET — key results for objective 20
{ "method": "GET", "objective_id": 20 }

// POST — create key result
{ "method": "POST", "krs_owner": 20, "krs_title": "Reduce churn to < 5%",
  "krs_init": 8, "krs_tar": 5, "krs_now": 8, "krs_weight": 100, "krs_unit": "%" }

// PUT — update current value
{ "method": "PUT", "id": 30, "krs_now": 4.2 }

// DELETE
{ "method": "DELETE", "id": 30 }
```

---

### 6. `indicators`

**Manage KPIs and performance indicators**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | KPI ID — required for PUT / DELETE |
| `name` | string | KPI name — required for POST |
| `target` | number \| string | Target value |
| `unit` | string | Unit (e.g. `%`, `USD`, `count`) |
| `frequency` | string | `daily` / `weekly` / `monthly` / `quarterly` / `yearly` |
| `category_id` | integer \| string | Indicator category ID |
| `employee_id` | integer \| string | Assign to employee |
| `search` | string | Search by keyword |

**Examples:**

```json
// GET — monthly KPIs for employee 7
{ "method": "GET", "employee_id": 7, "frequency": "monthly" }

// POST — create KPI
{ "method": "POST", "name": "Customer Satisfaction Score",
  "target": 90, "unit": "%", "frequency": "monthly",
  "employee_id": 7, "category_id": 2 }

// PUT — update target
{ "method": "PUT", "id": 40, "target": 95 }

// DELETE
{ "method": "DELETE", "id": 40 }
```

---

### 7. `indicator-record`

**Manage KPI actual values per period**

Methods: `GET` `POST` `DELETE`

> **POST** maps to `indicator-record/update-record` (upsert by period).
> **GET with `id`** returns a single record; **GET without `id`** returns a list.

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `DELETE` |
| `id` | integer \| string | Record ID — GET single / DELETE |
| `indicator_id` | integer \| string | KPI indicator ID — required for GET list and POST |
| `period_key` | string | Period date `dd-m-YYYY` e.g. `01-6-2026` — required for POST |
| `current_value` | number \| string | Actual value for the period |
| `target_value` | number \| string | Target value for the period |
| `remark` | string | Notes |
| `score` | number \| string | Computed score |
| `month` | integer \| string | Filter by month number (GET list) |
| `year` | integer \| string | Filter by year (GET list) |
| `start_date` | string | Filter from date (GET list) |
| `end_date` | string | Filter to date (GET list) |
| `all` | boolean \| string | Return all records without pagination |
| `per_page` | integer | Page size |
| `page` | integer | Page number |

**Examples:**

```json
// GET — records for KPI 40 in May 2026
{ "method": "GET", "indicator_id": 40, "month": 5, "year": 2026 }

// POST — submit/update actual value for a period
{ "method": "POST", "indicator_id": 40, "period_key": "01-6-2026",
  "current_value": 112000, "target_value": 100000, "remark": "Exceeded target" }

// DELETE
{ "method": "DELETE", "id": 200 }
```

---

### 8. `leads`

**Manage sales leads and prospects**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Lead ID — required for PUT / DELETE |
| `client_name` | string | Lead contact name — required for POST |
| `company_name` | string | Company name |
| `email` | string | Contact email |
| `mobile` | string | Contact mobile |
| `website` | string | Company website |
| `address` | string | Address |
| `note` | string | Notes |
| `agent_id` | integer \| string | Assign to sales agent |
| `source_id` | integer \| string | Lead source ID (POST) |
| `status_id` | integer \| string | Lead status ID (POST) |
| `status` | integer \| string | Lead status ID (PUT) |
| `source` | integer \| string | Lead source ID (PUT) |
| `meeting_date` | string | Scheduled meeting date |
| `next_follow_up` | string | `yes` or `no` |
| `client` | string | `lead` or `client` filter (GET) |
| `followUp` | string | Filter follow-up required (GET) |
| `startDate` | string | Filter from date (GET) |
| `endDate` | string | Filter to date (GET) |
| `sort_field` | string | Sort column |
| `sort_direction` | string | `asc` / `desc` |
| `per_page` | integer | Page size |
| `page` | integer | Page number |

**Examples:**

```json
// GET — list leads with pagination
{ "method": "GET", "client": "lead", "per_page": 20, "page": 1 }

// POST — create lead
{ "method": "POST", "client_name": "PT Maju Jaya",
  "email": "info@majujaya.com", "mobile": "+6281234567890",
  "status_id": 1, "agent_id": 7 }

// PUT — update status and add note
{ "method": "PUT", "id": 55, "status": 3, "note": "Proposal sent" }

// DELETE
{ "method": "DELETE", "id": 55 }
```

---

### 9. `clients`

**Manage clients and customer relationships**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Client ID — required for PUT / DELETE |
| `name` | string | Contact name — required for POST |
| `email` | string | Email — required for POST |
| `company_name` | string | Company name |
| `website` | string | Company website |
| `address` | string | Address |
| `mobile` | string | Phone number |
| `send_email` | string | `yes` / `no` — send welcome email |
| `skype` | string \| null | Skype handle |
| `linkedin` | string \| null | LinkedIn URL |
| `twitter` | string \| null | Twitter handle |
| `facebook` | string \| null | Facebook URL |
| `gst_number` | string \| null | Tax/GST number |
| `note` | string \| null | Notes |
| `search` | string | Search by name or company |

**Examples:**

```json
// GET — search clients
{ "method": "GET", "search": "acme" }

// POST — create client
{ "method": "POST", "name": "Alice Johnson",
  "email": "alice@newclient.com", "company_name": "New Client Ltd",
  "mobile": "+0987654321", "send_email": "yes" }

// PUT — update website
{ "method": "PUT", "id": 3, "website": "https://acme-new.com" }

// DELETE
{ "method": "DELETE", "id": 3 }
```

---

### 10. `tickets`

**Manage support tickets and issues**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Ticket ID — required for PUT / DELETE |
| `subject` | string | Ticket subject — required for POST |
| `description` | string | Ticket description |
| `status` | string | `open` / `pending` / `resolved` / `closed` |
| `priority` | string | `low` / `medium` / `high` / `urgent` |
| `type_id` | integer \| string | Ticket type ID |
| `channel_id` | integer \| string | Ticket channel ID |
| `agent_id` | integer \| string | Assign to agent |
| `user_id` | integer \| string | Reporter user ID |
| `search` | string | Search by keyword |

**Examples:**

```json
// GET — high-priority open tickets
{ "method": "GET", "status": "open", "priority": "high" }

// POST — create ticket
{ "method": "POST", "subject": "Cannot export report",
  "description": "Export button not responding",
  "priority": "medium", "type_id": 1, "channel_id": 2, "user_id": 7 }

// PUT — resolve and reassign
{ "method": "PUT", "id": 500, "status": "resolved", "agent_id": 8 }

// DELETE
{ "method": "DELETE", "id": 500 }
```

---

### 11. `attendance`

**Manage attendance records and time tracking**

Methods: `GET` `POST` `PUT`

> **POST** → clock in (`attendance/clock-in`)
> **PUT** → clock out (`attendance/clock-out`)
> **GET with `today: true`** → today's attendance summary

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` |
| `id` | integer \| string | Attendance record ID — required for PUT (clock-out) |
| `employee_id` | integer \| string | Employee ID |
| `date` | string | Specific date `YYYY-MM-DD` |
| `month` | string | Filter by month |
| `year` | string | Filter by year |
| `clock_in_time` | string | Clock-in time `HH:MM:SS` |
| `clock_out_time` | string | Clock-out time `HH:MM:SS` |
| `working_from` | string | `office` / `home` / `other` |
| `late_reason` | string | Reason if arriving late |
| `today` | boolean \| string | Set `true` to get today's records (GET) |

**Examples:**

```json
// GET — today's attendance
{ "method": "GET", "today": true }

// GET — by month/year
{ "method": "GET", "employee_id": 7, "month": "5", "year": "2026" }

// POST — clock in
{ "method": "POST", "employee_id": 7, "working_from": "office" }

// PUT — clock out
{ "method": "PUT", "id": 300 }
```

---

### 12. `leave`

**Manage employee leave requests**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Leave ID — required for PUT / DELETE |
| `user_id` | integer \| string | Employee user ID — required for POST |
| `leave_type_id` | integer \| string | Leave type ID — required for POST / PUT |
| `leave_date` | string | Leave start date `YYYY-MM-DD` — required for POST |
| `duration` | string | `full day` / `half day` / `multiple` |
| `reason` | string | Leave reason |
| `status` | string | `pending` / `approved` / `rejected` (PUT for approval) |
| `multi_date` | string | Comma-separated dates for `multiple` duration |
| `userId` | integer \| string | Filter by employee (GET) |
| `startDate` | string | Filter from date (GET) |
| `endDate` | string | Filter to date (GET) |
| `search` | string | Search keyword |
| `all` | boolean \| string | Return all records without pagination |
| `per_page` | integer | Page size |
| `page` | integer | Page number |

**Examples:**

```json
// GET — pending leaves for employee 7
{ "method": "GET", "userId": 7, "status": "pending" }

// POST — apply for leave
{ "method": "POST", "user_id": 7, "leave_type_id": 1,
  "leave_date": "2026-05-15", "duration": "full day", "reason": "Family event" }

// PUT — approve leave
{ "method": "PUT", "id": 88, "status": "approved" }

// DELETE
{ "method": "DELETE", "id": 88 }
```

---

### 13. `department`

**Manage departments and teams**

Methods: `GET` `POST` `PUT` `DELETE`

> Supports lookup by `name` (string) in addition to `id` for PUT / DELETE.

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Department ID |
| `name` | string | Current department name — for lookup (PUT / DELETE) |
| `team_name` | string | Department name — required for POST / PUT |
| `description` | string | Department description |
| `parent_id` | integer \| string | Parent department ID |
| `leader_id` | integer \| string | Department leader employee ID |
| `search` | string | Search by name |
| `sort_field` | string | Sort column |
| `sort_direction` | string | `asc` / `desc` |

**Examples:**

```json
// GET — search departments
{ "method": "GET", "search": "marketing" }

// POST — create department
{ "method": "POST", "team_name": "Product Design",
  "description": "UI/UX and product design team" }

// PUT — rename by ID
{ "method": "PUT", "id": 4, "team_name": "Digital Marketing & SEO" }

// PUT — rename by name (auto-resolves ID)
{ "method": "PUT", "name": "Digital Marketing", "team_name": "Digital Marketing & SEO" }

// DELETE
{ "method": "DELETE", "id": 4 }
```

---

### 14. `designation`

**Manage job designations and roles**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Designation ID — required for PUT / DELETE |
| `name` | string | Designation name — required for POST / PUT |
| `search` | string | Search by keyword |

**Examples:**

```json
// GET — search designations
{ "method": "GET", "search": "engineer" }

// POST — create designation
{ "method": "POST", "name": "DevOps Engineer" }

// PUT — rename
{ "method": "PUT", "id": 2, "name": "Principal Software Engineer" }

// DELETE
{ "method": "DELETE", "id": 2 }
```

---

### 15. `performance-cycle`

**Manage performance / OKR cycles**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Cycle ID — required for PUT / DELETE |
| `name` | string | Cycle name — required for POST / PUT |
| `cycle_type` | string | Cycle type — required for POST / PUT (e.g. `quarterly`, `annual`) |
| `started_at` | string | Start date `YYYY-MM-DD` — required for POST / PUT |
| `finished_at` | string | End date `YYYY-MM-DD` — required for POST / PUT |
| `sort_field` | string | Sort column |
| `sort_direction` | string | `asc` / `desc` |
| `per_page` | integer | Page size |
| `page` | integer | Page number |

**Examples:**

```json
// GET — list cycles
{ "method": "GET", "per_page": 10, "page": 1 }

// POST — create quarterly cycle
{ "method": "POST", "name": "Q3 2026", "cycle_type": "quarterly",
  "started_at": "2026-07-01", "finished_at": "2026-09-30" }

// PUT — rename cycle
{ "method": "PUT", "id": 3, "name": "Q2 2026 Revised" }

// DELETE
{ "method": "DELETE", "id": 3 }
```

---

### 16. `holiday`

**Manage company holidays**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Holiday ID — required for PUT / DELETE |
| `occasion` | string | Holiday name — required for POST / PUT |
| `date` | string | Date in `dd/mm/yyyy` format — required for POST / PUT |
| `year` | integer \| string | Filter by year (GET) |
| `status` | string | `upcoming` / `past` / `all` (GET) |
| `search` | string | Search by keyword |
| `all` | boolean \| string | Return all records without pagination |
| `sort_field` | string | Sort column |
| `sort_direction` | string | `asc` / `desc` |
| `per_page` | integer | Page size |
| `page` | integer | Page number |

**Examples:**

```json
// GET — upcoming holidays in 2026
{ "method": "GET", "year": 2026, "status": "upcoming" }

// POST — add holiday
{ "method": "POST", "occasion": "New Year's Day", "date": "01/01/2027" }

// PUT — rename holiday
{ "method": "PUT", "id": 10, "occasion": "National Independence Day" }

// DELETE
{ "method": "DELETE", "id": 10 }
```

---

### 17. `project-category`

**Manage project categories and classifications**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Category ID — required for PUT / DELETE |
| `category_name` | string | Category name — required for POST / PUT |
| `search` | string | Search by keyword |

**Examples:**

```json
// GET — search categories
{ "method": "GET", "search": "web" }

// POST
{ "method": "POST", "category_name": "Mobile Development" }

// PUT
{ "method": "PUT", "id": 1, "category_name": "Web & PWA Development" }

// DELETE
{ "method": "DELETE", "id": 1 }
```

---

### 18. `task-category`

**Manage task categories and types**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Category ID — required for PUT / DELETE |
| `category_name` | string | Category name — required for POST / PUT |
| `search` | string | Search by keyword |

**Examples:**

```json
// GET
{ "method": "GET", "search": "bug" }

// POST
{ "method": "POST", "category_name": "Feature Request" }

// PUT
{ "method": "PUT", "id": 1, "category_name": "Critical Bug Fix" }

// DELETE
{ "method": "DELETE", "id": 1 }
```

---

### 19. `ticket-type`

**Manage ticket types and classifications**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Ticket type ID — required for PUT / DELETE |
| `type` | string | Ticket type name — required for POST / PUT |
| `search` | string | Search by keyword |

**Examples:**

```json
// GET
{ "method": "GET", "search": "bug" }

// POST
{ "method": "POST", "type": "Feature Request" }

// PUT
{ "method": "PUT", "id": 1, "type": "Critical Bug" }

// DELETE
{ "method": "DELETE", "id": 1 }
```

---

### 20. `ticket-channel`

**Manage ticket channels and submission methods**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Channel ID — required for PUT / DELETE |
| `channel_name` | string | Channel name — required for POST / PUT |
| `search` | string | Search by keyword |

**Examples:**

```json
// GET — list all channels
{ "method": "GET" }

// POST
{ "method": "POST", "channel_name": "WhatsApp" }

// PUT
{ "method": "PUT", "id": 1, "channel_name": "Email Support" }

// DELETE
{ "method": "DELETE", "id": 1 }
```

---

### 21. `ticket-agent`

**List ticket agents and their groups**

Methods: `GET`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` |

**Example:**

```json
// GET — list all ticket agents
{ "method": "GET" }
```

**Response:**

```json
{
  "status": "success",
  "data": [
    { "id": 7, "name": "Sarah Lee", "email": "sarah@company.com", "group": "Technical Support" }
  ]
}
```

---

### 22. `indicator-category`

**Manage KPI / indicator categories**

Methods: `GET` `POST` `PUT` `DELETE`

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | integer \| string | Category ID — required for PUT / DELETE |
| `indicator_type_name` | string | Category name — required for POST / PUT |
| `status` | string | Filter by status; omit or `all` for no filter (GET) |
| `search` | string | Search by keyword |
| `all` | boolean \| string | Return all records without pagination |
| `sort_field` | string | Sort column |
| `sort_direction` | string | `asc` / `desc` |
| `per_page` | integer | Page size |
| `page` | integer | Page number |

**Examples:**

```json
// GET — list all categories
{ "method": "GET", "all": true }

// POST
{ "method": "POST", "indicator_type_name": "Engineering" }

// PUT
{ "method": "PUT", "id": 1, "indicator_type_name": "Revenue & Sales" }

// DELETE
{ "method": "DELETE", "id": 1 }
```

---

### 23. `leave-type`

**Manage leave types (Annual, Sick, etc.)**

Methods: `GET` `POST` `PUT` `DELETE`

> Write operations (POST/PUT/DELETE) are admin-only.
> Lookup by `id` or `type_name` (partial match) for PUT/DELETE.

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | string | Leave type ID — or use `type_name` to look up |
| `type_name` | string | Leave type name — required for POST |
| `days` | number | Number of allowed days per year |
| `color` | string | Color code e.g. `#FF0000` |
| `is_paid` | boolean | Is this a paid leave type? Default: `true` |
| `search` | string | Search by name |

**Examples:**

```json
// GET — list all leave types
{ "method": "GET" }

// POST
{ "method": "POST", "type_name": "Maternity Leave", "days": 90, "is_paid": true }

// PUT — update days allowed
{ "method": "PUT", "type_name": "Annual Leave", "days": 14 }

// DELETE
{ "method": "DELETE", "id": "3" }
```

---

### 24. `invoices`

**Manage client invoices**

Methods: `GET` `POST` `PUT` `DELETE`

> Requires `invoices` module enabled. POST/PUT/DELETE are admin-only.
> Lookup by `id` or `invoice_number` (e.g. `INV#0001`) for PUT/DELETE.
> Employees see only invoices linked to projects they are members of.

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | string | Invoice ID |
| `invoice_number` | string | Display number e.g. `INV#0001` — used to look up for PUT/DELETE |
| `client_id` | string | Client user ID |
| `client_name` | string | Client company or contact name — auto-resolved to ID |
| `project_id` | string | Link to project |
| `issue_date` | string | Issue date `YYYY-MM-DD` (defaults to today) |
| `due_date` | string | Due date `YYYY-MM-DD` |
| `sub_total` | number | Subtotal amount |
| `total` | number | Total amount — **required for POST** |
| `currency_id` | string | Currency ID |
| `note` | string | Invoice notes |
| `search` | string | Search by invoice number or client name |
| `startDate` | string | Filter from issue date |
| `endDate` | string | Filter to issue date |

**Examples:**

```json
// GET — list invoices
{ "method": "GET", "client_name": "Acme Corp" }

// POST — create invoice
{ "method": "POST", "client_name": "Acme Corp", "total": 5000,
  "issue_date": "2026-05-01", "due_date": "2026-05-31" }

// PUT — update due date
{ "method": "PUT", "invoice_number": "INV#0001", "due_date": "2026-06-15" }

// DELETE
{ "method": "DELETE", "invoice_number": "INV#0001" }
```

---

### 25. `estimates`

**Manage client estimates and quotes**

Methods: `GET` `POST` `PUT` `DELETE`

> Requires `estimates` module enabled. POST/PUT/DELETE are admin-only.
> Lookup by `id` or `estimate_number` (e.g. `EST#0001`) for PUT/DELETE.

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | string | Estimate ID |
| `estimate_number` | string | Display number e.g. `EST#0001` — look up for PUT/DELETE |
| `client_id` | string | Client user ID |
| `client_name` | string | Client company or contact name — auto-resolved to ID |
| `valid_till` | string | Expiry date `YYYY-MM-DD` |
| `sub_total` | number | Subtotal |
| `total` | number | Total amount — **required for POST** |
| `discount` | number | Discount amount |
| `discount_type` | string | `percent` or `fixed` |
| `currency_id` | string | Currency ID |
| `note` | string | Notes |
| `status` | string | `draft` / `sent` / `declined` / `accepted` |
| `search` | string | Search by number or client |
| `startDate` | string | Filter from `valid_till` |
| `endDate` | string | Filter to `valid_till` |

**Examples:**

```json
// GET — list accepted estimates
{ "method": "GET", "status": "accepted" }

// POST — create estimate
{ "method": "POST", "client_name": "Acme Corp", "total": 12000,
  "valid_till": "2026-06-30", "status": "draft" }

// PUT — mark as sent
{ "method": "PUT", "estimate_number": "EST#0003", "status": "sent" }

// DELETE
{ "method": "DELETE", "estimate_number": "EST#0003" }
```

---

### 26. `contracts`

**Manage client contracts**

Methods: `GET` `POST` `PUT` `DELETE`

> Requires `contracts` module enabled. POST/PUT/DELETE are admin-only.
> Lookup by `id` or `subject` (partial match) for PUT/DELETE.

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | string | Contract ID |
| `subject` | string | Contract title — **required for POST**; also used for lookup |
| `client_id` | string | Client user ID |
| `client_name` | string | Client company name — auto-resolved to ID |
| `contract_type_id` | string | Contract type ID |
| `start_date` | string | Start date `YYYY-MM-DD` |
| `end_date` | string | End date `YYYY-MM-DD` |
| `amount` | number | Contract value |
| `currency_id` | string | Currency ID |
| `description` | string | Contract notes |
| `search` | string | Search by contract subject |
| `startDate` | string | Filter by start_date from |
| `endDate` | string | Filter by end_date to |

**Examples:**

```json
// GET — list contracts for a client
{ "method": "GET", "client_name": "Acme Corp" }

// POST — create contract
{ "method": "POST", "subject": "Annual Support Contract",
  "client_name": "Acme Corp", "start_date": "2026-01-01",
  "end_date": "2026-12-31", "amount": 24000 }

// PUT — update amount
{ "method": "PUT", "subject": "Annual Support Contract", "amount": 30000 }

// DELETE
{ "method": "DELETE", "id": "7" }
```

---

### 27. `events`

**Manage company calendar events**

Methods: `GET` `POST` `PUT` `DELETE`

> Requires `events` module enabled. POST/PUT/DELETE are admin-only.
> Lookup by `id` or `event_name` (partial match) for PUT/DELETE.
> Distinct from `holiday` — use `events` for internal company events, meetings, etc.

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | string | Event ID |
| `event_name` | string | Event name — **required for POST**; also used for lookup |
| `where` | string | Event location |
| `description` | string | Event description |
| `start_date_time` | string | Start date/time `YYYY-MM-DD HH:mm` — **required for POST** |
| `end_date_time` | string | End date/time `YYYY-MM-DD HH:mm` — **required for POST** |
| `repeat` | string | `yes` / `no` (default: `no`) |
| `repeat_every` | integer | Repeat interval (e.g. every 2 weeks) |
| `repeat_cycles` | integer | Number of repetitions |
| `repeat_type` | string | `daily` / `weekly` / `monthly` / `yearly` |
| `label_color` | string | Bootstrap class or hex color (default: `bg-info`) |
| `month` | string | Filter by month number 1–12 |
| `year` | string | Filter by year |
| `startDate` | string | Filter events from date |
| `endDate` | string | Filter events to date |
| `search` | string | Search by event name |

**Examples:**

```json
// GET — events in June 2026
{ "method": "GET", "month": "6", "year": "2026" }

// POST — create event
{ "method": "POST", "event_name": "Q2 All-Hands Meeting",
  "start_date_time": "2026-06-15 09:00",
  "end_date_time": "2026-06-15 11:00", "where": "Main Conference Room" }

// PUT — change location
{ "method": "PUT", "event_name": "Q2 All-Hands Meeting", "where": "Zoom" }

// DELETE
{ "method": "DELETE", "id": "15" }
```

---

### 28. `expenses`

**Manage expenses and claims**

Methods: `GET` `POST` `PUT` `DELETE`

> Requires `expenses` module enabled. DELETE is admin-only.
> Employees can create/update their own pending expenses.
> Admin-created expenses default to `approved`; employee-submitted default to `pending`.
> Lookup by `id` or `item_name` (partial match) for PUT/DELETE.

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | string | Expense ID |
| `item_name` | string | Expense item name — **required for POST**; also used for lookup |
| `purchase_date` | string | Purchase date `YYYY-MM-DD` — **required for POST** |
| `price` | number | Expense amount — **required for POST** |
| `purchase_from` | string | Where it was purchased |
| `currency_id` | string | Currency ID (defaults to company currency) |
| `expense_category_id` | string | Expense category ID |
| `user_id` | string | Employee user ID (admin only; defaults to self) |
| `employee_name` | string | Employee name — auto-resolved to `user_id` |
| `project_id` | string | Link to project |
| `description` | string | Additional notes |
| `status` | string | `pending` / `approved` / `rejected` — filter (GET) or update (PUT, admin only) |
| `can_claim` | integer \| boolean | `1` = reimbursement claim, `0` = regular expense |
| `startDate` | string | Filter from purchase date |
| `endDate` | string | Filter to purchase date |

**Examples:**

```json
// GET — pending expenses
{ "method": "GET", "status": "pending" }

// POST — submit expense
{ "method": "POST", "item_name": "Team Lunch", "purchase_date": "2026-05-10",
  "price": 250, "can_claim": 1, "description": "Client meeting lunch" }

// PUT — approve expense (admin)
{ "method": "PUT", "id": "99", "status": "approved" }

// DELETE
{ "method": "DELETE", "id": "99" }
```

---

### 29. `expense-category`

**Manage expense categories**

Methods: `GET` `POST` `PUT` `DELETE`

> Requires `expenses` module enabled. Write operations are admin-only.
> Lookup by `id` or `category_name` (partial match) for PUT/DELETE.

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | string | Category ID |
| `category_name` | string | Category name — **required for POST**; also used for lookup |
| `search` | string | Search by category name |

**Examples:**

```json
// GET
{ "method": "GET" }

// POST
{ "method": "POST", "category_name": "Travel & Accommodation" }

// PUT
{ "method": "PUT", "category_name": "Travel", "category_name": "Travel & Accommodation" }

// DELETE
{ "method": "DELETE", "id": "5" }
```

---

### 30. `notices`

**Manage company notice board**

Methods: `GET` `POST` `PUT` `DELETE`

> Requires `notices` module enabled. POST/PUT/DELETE are admin-only.
> Employees see only notices addressed to `all` or `employee`.
> Lookup by `id` or `heading` (partial match) for PUT/DELETE.

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | string | Notice ID |
| `heading` | string | Notice title — **required for POST**; also used for lookup |
| `description` | string | Notice content body — **required for POST** |
| `to` | string | Target audience: `all` / `employee` / `client` (default: `all`) |
| `search` | string | Search by heading |
| `startDate` | string | Filter from created date |
| `endDate` | string | Filter to created date |

**Examples:**

```json
// GET — notices for employees
{ "method": "GET", "to": "employee" }

// POST — create announcement
{ "method": "POST", "heading": "Office Closed on Friday",
  "description": "The office will be closed this Friday for maintenance.",
  "to": "all" }

// PUT — update content
{ "method": "PUT", "heading": "Office Closed on Friday",
  "description": "Updated: Office closed Friday AND Monday." }

// DELETE
{ "method": "DELETE", "id": "12" }
```

---

### 31. `timelogs`

**Manage project and task time logs**

Methods: `GET` `POST` `PUT` `DELETE`

> Requires `timelogs` module enabled. DELETE is admin-only.
> **POST** starts a timer (sets `end_time = null`).
> **PUT** stops a running timer by providing `end_time`, or edits any field.
> PUT without `id` finds the active (running) timer for the target user.
> Employees see only their own time logs.
> Supports lookup by name: `project_name` → `project_id`, `task_name` → `task_id`, `employee_name` → `user_id`.

| Parameter | Type | Description |
|---|---|---|
| `method` | string | `GET` / `POST` / `PUT` / `DELETE` |
| `id` | string | Time log ID — required for DELETE |
| `project_id` | string | Project ID |
| `project_name` | string | Project name — auto-resolved to `project_id` |
| `task_id` | string | Task ID |
| `task_name` | string | Task heading — auto-resolved to `task_id` |
| `user_id` | string | Employee user ID (admin only; defaults to self) |
| `employee_name` | string | Employee name — auto-resolved to `user_id` |
| `start_time` | string | Start datetime `YYYY-MM-DD HH:mm` (defaults to now on POST) |
| `end_time` | string | End datetime — provide on PUT to stop the timer |
| `memo` | string | Optional note for the time log |
| `date` | string | Filter by specific date (GET) |
| `month` | string | Filter by month number 1–12 (GET) |
| `year` | string | Filter by year (GET) |
| `active_only` | boolean \| string | `true` = return only running timers (GET) |

**Examples:**

```json
// GET — my time logs this month
{ "method": "GET", "month": "5", "year": "2026" }

// GET — active running timers
{ "method": "GET", "active_only": true }

// POST — start timer for a project
{ "method": "POST", "project_name": "Mobile App v2",
  "task_name": "Design landing page", "memo": "Working on hero section" }

// PUT — stop running timer
{ "method": "PUT", "end_time": "2026-05-10 17:30" }

// PUT — stop timer by ID
{ "method": "PUT", "id": "88", "end_time": "2026-05-10 17:30" }

// DELETE
{ "method": "DELETE", "id": "88" }
```

---

## Advanced: Account Tools (Gateway endpoint only)

> These tools are available only via `https://flowyteam.com/api/mcp/gateway` and **must only be invoked when the user explicitly requests it** — never autonomously. After obtaining a token, reconfigure the MCP connection using the [Recommended setup](#recommended--connect-with-api-token) above.

### `auth_register`

**Create a new FlowyTeam company account.**
Call only when the user explicitly requests to create a new account and provides all required details. Requires `allow_mcp_registration = true` on the FlowyTeam instance.

A verification email is sent — the account must be verified before it can be used. Two paths to complete verification:

- **Path A (CLI):** Copy the code from the verification email link URL and call `auth_verify_email` → receive `api_token` immediately.
- **Path B (browser):** Click the verification link in the email, then call `auth_login` with email + password → receive `api_token`.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✓ | Full name of the admin user |
| `email` | string | ✓ | Email address |
| `password` | string | ✓ | Password (minimum 8 characters) |
| `company_name` | string | ✓ | Company / organisation name |
| `phone` | string | — | Phone number (optional) |

**Response:** Returns `status: pending_verification` — no `api_token` yet. Verify email first.

---

### `auth_verify_email`

**Activate a pending account using the verification code from the email link.**
The code is the last segment of the verification URL, e.g. for `.../email-verification/ABC123XYZ` the code is `ABC123XYZ`.
Call this after `auth_register` when the user has copied the code from their verification email.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `verification_code` | string | ✓ | Code from the verification link URL |

**Response:** Returns `api_token` — use this as the Bearer token and reconfigure the MCP connection.

---

### `auth_login`

**Retrieve API token for an existing FlowyTeam account.**
Call only when the user explicitly provides their email and password and requests a login. Also use after the user has clicked the web verification link (Path B of `auth_register`).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `email` | string | ✓ | Registered email address |
| `password` | string | ✓ | Account password |

**Response:** Returns `api_token` — use this as the Bearer token and reconfigure the MCP connection.

---

## Error Codes

| Code | Meaning |
|---|---|
| `200` | Success |
| `401` | Unauthenticated — missing or invalid Bearer token |
| `403` | Forbidden — authenticated but lacks permission |
| `404` | Resource not found |
| `422` | Validation error — check the `errors` object in the response |
| `429` | Too many requests — rate limit exceeded |
| `500` | Server error |

---

## Natural Language Examples

Once connected, you can ask Claude:

```
"Create a task 'Review Q2 Report' in the Marketing project,
 assign to Sarah, due April 30"

"Show me all open high-priority tickets"

"List company-level OKRs for Q2 2026"

"Who is on leave this week?"

"Add a new employee: John Doe, email john@company.com,
 Engineering department, joining June 1"

"What are the KPI scores for the Sales team this month?"

"Create a new lead: PT Maju Jaya, contact info@majujaya.com,
 assign to agent ID 7"

"Clock in employee 7 from office"

"List all upcoming holidays in 2026"

"Show me all pending expense claims"

"Create an invoice for Acme Corp, total $5,000, due May 31"

"What events do we have in June?"

"Post an announcement: office closed Friday"

"Log 8 hours on the Mobile App project for today"

"Show me all running timers right now"
```

---

## Links

- **Website:** [flowyteam.com](https://flowyteam.com)
- **MCP Docs:** [flowyteam.com/get/mcp-server](https://flowyteam.com/get/mcp-server)
- **API Reference:** [flowyteam.com/get/mcp-docs](https://flowyteam.com/get/mcp-docs)
- **Sign Up:** [app.flowyteam.com/register](https://flowyteam.com/register)
