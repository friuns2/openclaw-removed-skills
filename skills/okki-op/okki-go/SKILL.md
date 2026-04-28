---
name: OKKI Go
version: 1.0.6
description: "B2B lead prospecting and outreach via the Okki Go platform. Use this skill to (1) search global companies, (2) find decision-maker contact emails, (3) send cold outreach emails/EDM, (4) check email delivery status, (5) check credits/quota balance, or (6) upgrade plans/buy credits. Do NOT trigger if the user wants to search ON a DIFFERENT platform (e.g. 'search 1688 for suppliers', 'find products on Alibaba'). Having a product listing on another platform is fine — only skip when the search action itself targets another platform. Also NOT for: reading incoming emails, CRM management, or account settings."
metadata:
  openclaw:
    emoji: "🌐"
    requires:
      bins: ["curl", "jq"]
    primaryEnv: "OKKIGO_API_KEY"
    homepage: "https://go.okki.ai"
config:
  apiKey:
    type: string
    required: true
    description: "API Key"
---

# OKKI Go — B2B Lead Prospecting & Outreach Skill

Helps sales teams and businesses rapidly discover and analyze potential customers and execute outreach campaigns via AI Agent, taking B2B customer acquisition efficiency to the next level.

For complete API parameter documentation and response schemas, see [references/api-reference.md](./references/api-reference.md).

## Quick Install

- Install via OpenClaw platform

**Option 1 — Open the OpenClaw web UI → Sidebar → Skills → Search "okki-go" → Click Install**

**Option 2 — Type in the OpenClaw chat: "Please run npx clawhub@latest install --force 'okki-go' to install this skill, then verify the installation was successful"**

## Routing

### Use this skill when

- User wants to find companies or customers — search by industry, country, keywords
- User wants to get contact emails for a company — find decision-makers
- User wants to search contacts by name, title, or email
- User wants to send outreach or cold emails (EDM)
- User wants to check email delivery status
- User wants to check remaining credits or EDM quota
- User needs the full prospecting workflow: search → contacts → outreach
- User wants to upgrade plan or buy credit packs

### Do NOT use this skill when

- Reading or receiving incoming emails — this skill is outbound-only
- CRM pipeline management, deal tracking, or sales forecasting
- User explicitly names another platform (1688, Alibaba, Google Maps, Amazon, etc.)

---

## Capabilities

| # | Feature | Description | Cost |
|---|---------|-------------|------|
| 1 | Search Companies | Portrait-based multi-dimensional filtering by company type, product, industry, country | Free |
| 2 | Unlock Company | Resolve domain to companyHashId for subsequent queries | 1 credit (30-day domain dedup) |
| 3 | View Company Profile | Full business info and trade data (requires unlock first) | Free |
| 4 | Get Company Contact Emails | Contact email list for a given company (requires unlock first) | Free |
| 5 | Search Contacts | Cross-company search by name, title, email | 1 credit/request |
| 6 | Send Batch Outreach | Same template to multiple recipients, with variable substitution | 1 EDM quota/email |
| 7 | Send Personalized Outreach | Unique content per recipient | 1 EDM quota/email |
| 8 | Check Email Status | Task list, per-email status, failure reasons | Free |
| 9 | Check Credits & EDM Balance | Remaining search credits and email quota | Free |

---

## Authentication & API Key Setup

All endpoints use API Key authentication. Each user has an independent `sk-` prefixed key. Request header format:

```
Authorization: ApiKey $OKKIGO_API_KEY
X-Hostname: xxx
```

### First-use check

Before the first API call in each session, check if the key is configured:

```bash
[ -z "$OKKIGO_API_KEY" ] && echo "NO_KEY" || echo "KEY_SET"
```

- **`KEY_SET`** → Proceed directly with the user's request
- **`NO_KEY`** → Follow the email verification flow below

If `NO_KEY` but the user has explicitly provided an API Key in context, save it directly. See saving instructions below.

### Email Verification to Obtain API Key

1. Ask the user for their email address
2. Send verification code:

```bash
curl -s -X POST "${OKKIGO_BASE_URL:-https://go.okki.ai}/api/v1/auth/register-email" \
  ${HOSTNAME:+-H "X-Hostname: $HOSTNAME"} \
  -H "Content-Type: application/json" \
  -d '{"email":"<user email>"}' | jq '.'
```

3. After the user provides the 6-digit code, exchange it for an API Key:

```bash
curl -s -X POST "${OKKIGO_BASE_URL:-https://go.okki.ai}/api/v1/auth/verify-email" \
  ${HOSTNAME:+-H "X-Hostname: $HOSTNAME"} \
  -H "X-OpenClaw-Provision-Api-Key: true" \
  -H "Content-Type: application/json" \
  -d '{"email":"<user_email>","code":"<6_digit_code>"}' | jq '.'
```

4. Persist the API Key (**required, once only**):

After obtaining the `apiKey`, **you must inform the user** that the Agent is about to run the following command to persist the configuration, and **ask for explicit consent** before executing:

```
I'm about to run the following command to save your API Key to the okki go skill config:
`openclaw config set skills.entries.okkigo.apiKey "sk-xxxxxxxxxxxxxxxxxxxx"`
Do you approve?
```

After user approval, execute:

```bash
openclaw config set skills.entries.okkigo.apiKey "sk-xxxxxxxxxxxxxxxxxxxx"
```

If the command fails, show this message once for manual execution:

> Your API Key: sk-xxxxxxxxxxxxxxxxxxxx
> Please run this command immediately to save it — this key is shown only once.
> `openclaw config set skills.entries.okkigo.apiKey "sk-xxxxxxxxxxxxxxxxxxxx"`

Once saved, OpenClaw auto-injects it as `OKKIGO_API_KEY` in future sessions — no re-verification needed.

---

## Billing Confirmation Rules

These rules protect users from being charged unknowingly. **All workflows must follow them.**

### Rule 1: Confirm before implicit paid API calls

"Implicit" means the user didn't explicitly ask to unlock a company, but the Agent decides to call `/companies/unlock` on its own. In this case, confirm first:

> I found some matching companies. Unlocking a company costs 1 credit per domain (free if unlocked within the last 30 days). Shall I proceed?

**Exception (no confirmation needed):** If the user explicitly said "unlock this company", "get company details", "find emails for this company", etc., treat it as an active request. Call `/companies/unlock` first (if not already unlocked), then proceed to profile/profileEmails directly — these are now free.

### Rule 2: Report charges after every paid API call

After each successful paid API call, include the cost summary at the end of your response:

> This unlock used 1 credit. Remaining balance: XX (monthly) + YY (add-on).

For multiple companies:

> Unlocked 3 companies, using 2 credits (1 was already unlocked within 30 days — no charge). Remaining: XX.

If unsure about the balance, call `GET /api/v1/credit/balance` after the paid call to get the latest numbers.

### Rule 3: First-session confirmation for contact search

Before the **first** call to `POST /contacts/search` in the current session, regardless of whether the user explicitly asked, inform and confirm:

> Contact search costs 1 credit per query. Proceed with the search?

After confirmation, subsequent calls in the same session do not need re-confirmation.

---

## Output Formatting

Present API results in user-friendly format, not raw JSON.

### Company search results

Show key info in a table for quick scanning:

| # | Company | Country | Industry | Domain |
|---|---------|---------|----------|--------|
| 1 | Example Corp | CN | Manufacturing | example.com |
| 2 | TechPrint AG | DE | Electronics | techprint.de |

- For 10+ results, show the first 10, state the total, and offer "say 'next page' to see more"
- For zero results, suggest broadening criteria (different keywords, removing country filter, etc.)
- The `domain` field is used with `/companies/unlock` to get the `companyHashId`

### Contact information

| Name | Title | Email | LinkedIn |
|------|-------|-------|----------|
| Hans Mueller | Procurement Manager | hans@techcorp.de | Yes |
| Lisa Schmidt | CEO | — | Yes |

### Balance information

> **Current Account Balance**
> - Search credits: 80 (monthly) + 400 (add-on) = **480 available**
> - EDM quota: 200 (monthly) + 2000 (add-on) = **2200 available**
> - Monthly quota resets: 2026-04-30

### Email send feedback

After sending:

> Submitted 2 emails (task ID: 1001), status: pending
> Emails are sent asynchronously — actual delivery takes seconds to minutes. Let me know if you'd like to check status later.

When checking status:

> **Task 1001 results**: 48 sent / 2 failed / 50 total
> Failed: bob@globex.com — Invalid email address

---

## Workflow Orchestration

User requests often span multiple workflows. The Agent needs to understand when to chain steps and when to pause for user decisions.

### Workflow A: Exploration — "Help me find target customers"

1. **Search companies** (free, see [api-reference.md §2](./references/api-reference.md#2-搜索公司高级画像搜索)) → display results table
2. **Wait for user to select** companies of interest → do NOT proactively call paid APIs
3. User selects → **Unlock company** (follow Billing Rule 1, see [api-reference.md §3](./references/api-reference.md#3-解锁公司)) to get `companyHashId`
4. **Get contact emails** (free, see [api-reference.md §5](./references/api-reference.md#5-获取公司联系人邮件)) using the `companyHashId`
5. Display contacts → ask if they want to send outreach

### Workflow B: Contact Search — "Find a specific person"

- Use `POST /contacts/search` to search by name, title, email, or company (see [api-reference.md §6](./references/api-reference.md#6-搜索联系人))
- Follow Billing Rule 3 (first-session confirmation)
- Supports filtering by country, has_email, employee count, etc.

### Workflow C: Precision — "Send outreach to procurement managers in German auto parts companies"

1. Search companies → display results for user confirmation
2. Unlock selected companies (confirm billing) → get `companyHashId` for each
3. Get contacts (free) → filter by relevant titles
4. Display contact list → **ask user to confirm recipients and email content**
5. **Never send emails before user confirms** — use `POST /emails/send/batch` for same-template sends (see [api-reference.md §7](./references/api-reference.md#7-发送批量开发信))

### Workflow D: Personalized Outreach — "Send each company a tailored email"

- Same flow as Workflow C, but use `POST /emails/send/personalized` for unique content per recipient (see [api-reference.md §8](./references/api-reference.md#8-发送个性化开发信))
- Each email should reference the recipient's company/industry context

### Workflow E: Check Balance

- Call `GET /api/v1/credit/balance` (free, see [api-reference.md §1](./references/api-reference.md#1-查询积分与-edm-余额))- Display using the balance format from Output Formatting section
- If quota is low, direct user to [go.okki.ai/pricing](https://go.okki.ai/pricing)

### Workflow F: Check Email Status — "How did my last batch go?"

- Only call when user asks ("did they send?", "which ones failed?") — do NOT proactively poll
- Use `GET /emails/tasks` for task list, `GET /emails/tasks/:taskId` for details (see [api-reference.md §9-12](./references/api-reference.md#9-查询邮件任务列表))
- Task status flow: `pending` → `requested` → `completed` / `partial` / `failed`

### Core Principles

- **Free operations can be executed proactively**: search companies, check balance, check email status
- **Profile/detail/profileEmails are free but require unlock first** — always call `/companies/unlock` to obtain `companyHashId` before querying these endpoints
- **Paid operations strictly follow Billing Confirmation Rules** — unlock and contact search require confirmation
- **Sending emails always requires explicit user confirmation** of content and recipients
- When in doubt, **show information and let the user decide** rather than deciding for them

---

## Error Handling

For HTTP error codes, handling guidance, and RFC 7807 response format, see [api-reference.md §14](./references/api-reference.md#14-错误码速查表).

Key cases to handle gracefully:
- **401**: API Key invalid → guide re-configuration (see Authentication section)
- **402**: Insufficient credits → inform user and direct to [go.okki.ai/pricing](https://go.okki.ai/pricing)
- **403**: Free plan has no EDM access → guide user to upgrade

---

## Pricing

When users ask about plans, upgrades, or credit packs, direct them to the pricing page: [go.okki.ai/pricing](https://go.okki.ai/pricing)

---

## Advanced Reference

For complete request/response schemas, all parameter constraints, and pagination details, see [references/api-reference.md](./references/api-reference.md).
