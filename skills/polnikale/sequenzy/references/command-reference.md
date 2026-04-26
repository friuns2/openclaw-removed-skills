# Command Reference

## Source Of Truth

- Command registration: `packages/cli/src/index.tsx`
- Auth storage and config: `packages/cli/src/config.ts`
- HTTP requests: `packages/cli/src/api.ts`
- Implemented handlers: `packages/cli/src/commands/`

If docs and code disagree, trust the code.

## Authentication

### Interactive login

```bash
sequenzy login
```

- starts device auth against `POST /api/device-auth/initiate`
- polls `POST /api/device-auth/poll`
- opens `${SEQUENZY_APP_URL}/setup/auth?code=...` in the browser
- stores the API key in `Bun.secrets` when available, otherwise in local config

### Non-interactive auth

Set `SEQUENZY_API_KEY` in the environment. `packages/cli/src/config.ts` checks this before local storage, so it is the safest path for automation.

### Identity and logout

```bash
sequenzy whoami
sequenzy account
sequenzy logout
```

Behavior:

- `whoami` prints cached local config only
- `account`: `GET /api/v1/account`
- `logout` removes locally stored auth

Caveat:

- treat `whoami` as "is this machine authenticated?" rather than authoritative server-side account discovery

## Environment Variables

```bash
SEQUENZY_API_KEY=...
SEQUENZY_API_URL=https://api.sequenzy.com
SEQUENZY_APP_URL=https://sequenzy.com
```

Notes:

- `SEQUENZY_API_KEY` overrides local keychain/config state
- the current CLI code defaults `SEQUENZY_APP_URL` to `https://sequenzy.com`
- many company-scoped commands accept `--company`, which sends `x-company-id` for personal API keys

## Dashboard URLs

```bash
sequenzy urls --company comp_123
sequenzy urls --company comp_123 --sequence seq_123
sequenzy urls --company comp_123 --campaign camp_123
sequenzy urls --company comp_123 --template tmpl_123
sequenzy urls --company comp_123 --settings-tab integrations
sequenzy urls --company comp_123 --json
```

Behavior:

- uses `SEQUENZY_APP_URL` as the base URL, defaulting to `https://sequenzy.com`
- if `--company` is omitted, tries the current company from `GET /api/v1/account`
- returns route templates, settings tab values, and concrete URLs when a company ID is known
- campaign, sequence, template, company, and account outputs include `url` or `appUrls` fields when the company can be resolved

Common route patterns:

- sequence editor: `/dashboard/company/{companyId}/sequences/{sequenceId}`
- campaign editor: `/dashboard/company/{companyId}/campaign/{campaignId}`
- template/email editor: `/dashboard/company/{companyId}/emails/{emailId}`
- settings: `/dashboard/company/{companyId}/settings`
- settings tab: `/dashboard/company/{companyId}/settings?tab={tab}`

## Stats

```bash
sequenzy stats
sequenzy stats --period 30d
sequenzy stats --campaign camp_123
sequenzy stats --sequence seq_123
```

Behavior:

- no ID: `GET /api/v1/metrics?period=7d|30d|90d`
- `--campaign`: `GET /api/v1/metrics/campaigns/:id`
- `--sequence`: `GET /api/v1/metrics/sequences/:id`

Output includes:

- `sent`
- `delivered`
- `opened`
- `clicked`
- `unsubscribed`
- `openRate`
- `clickRate`

## Subscribers

### List

```bash
sequenzy subscribers list
sequenzy subscribers list --tag vip
sequenzy subscribers list --segment seg_123
sequenzy subscribers list --limit 100
sequenzy subscribers list --tag vip --company comp_123 --json
```

Behavior:

- sends `GET /api/v1/subscribers`
- maps `--segment` to `segmentId`
- maps `--tag` to `tags`
- maps `--limit` to `limit`
- fetches every result page by default when `--limit` is omitted
- supports `--company` and `--json`

### Add

```bash
sequenzy subscribers add user@example.com
sequenzy subscribers add user@example.com --tag premium --attr name=John --attr plan=pro
sequenzy subscribers add user@example.com --tag premium --tag beta --company comp_123 --json
```

Behavior:

- sends `POST /api/v1/subscribers`
- body shape is `{ email, tags, customAttributes }`
- supports repeated `--tag` values
- supports `--company` and `--json`

### Get

```bash
sequenzy subscribers get user@example.com
sequenzy subscribers get user@example.com --company comp_123 --json
```

Behavior:

- sends `GET /api/v1/subscribers/:email`
- returns the full subscriber profile, including list memberships, sequence enrollments, email stats, and recent activity
- supports `--company` and `--json`

### Remove

```bash
sequenzy subscribers remove user@example.com
sequenzy subscribers remove user@example.com --hard
sequenzy subscribers remove user@example.com --company comp_123 --json
```

Behavior:

- without `--hard`, sends `PATCH /api/v1/subscribers/:email` with `{ status: "unsubscribed" }`
- with `--hard`, sends `DELETE /api/v1/subscribers/:email`
- supports `--company` and `--json`

## Transactional Send

### Template-based

```bash
sequenzy send user@example.com --template tmpl_123 --var name=John
```

### Raw HTML

```bash
sequenzy send user@example.com --subject "Hello" --html "<h1>Hi</h1>"
sequenzy send user@example.com --subject "Hello" --html-file ./email.html
```

Behavior:

- sends `POST /api/v1/transactional/send`
- body shape is `{ to, templateId, subject, html, variables }`

Validation enforced by the CLI:

- require either `--template` or `--html`/`--html-file`
- require `--subject` when sending raw HTML

## Companies, Lists, Tags, And Segments

### Companies

```bash
sequenzy companies list
sequenzy companies get comp_123
sequenzy companies create example.com --name Example
```

Behavior:

- `companies list`: `GET /api/v1/companies`
- `companies get`: `GET /api/v1/companies/:id`
- `companies create`: `POST /api/v1/companies`

### Lists

```bash
sequenzy lists list
sequenzy lists create Newsletter --description "Public newsletter list"
sequenzy lists create VIP --private --company comp_123
```

Behavior:

- `lists list`: `GET /api/v1/lists`
- `lists create`: `POST /api/v1/lists`
- create body shape is `{ name, description, isPrivate }`

### Tags

```bash
sequenzy tags
sequenzy tags --company comp_123 --json
```

Behavior:

- sends `GET /api/v1/tags`
- this is list-only; there are no tag mutation commands in the current CLI

### Segments

```bash
sequenzy segments list
sequenzy segments count seg_123
sequenzy segments create --name "Bought Pro" --stripe-product prod_pro
sequenzy segments create --name "3+ Pro Payments" --stripe-product prod_pro --purchase-operator at-least --payments 3
sequenzy segments create --name "VIP or Churn Risk" --match any --filter-json '[{"field":"tag","operator":"contains","value":"vip"},{"field":"emailOpened","operator":"is_not","value":"30d"}]'
```

Behavior:

- `segments list`: `GET /api/v1/segments`
- `segments count`: `GET /api/v1/segments/:id/count`
- `segments create`: `POST /api/v1/segments`
- `--filter-json` accepts the raw segment filter array used by the API/MCP
- `--match all|any` controls whether top-level filters are combined with `and` or `or`
- MCP/API use `filterJoinOperator: "and" | "or"` for the same behavior
- Stripe product filters use `field: "stripeProduct"` and product IDs, not product names
- threshold operators encode the count as `productId:count`, for example `prod_pro:3`

## Templates

```bash
sequenzy templates list
sequenzy templates get tmpl_123
sequenzy templates create welcome --subject "Welcome" --html-file ./welcome.html
sequenzy templates create welcome --subject "Welcome" --blocks-file ./welcome-blocks.json
sequenzy templates update tmpl_123 --subject "Updated" --html-file ./welcome-v2.html
sequenzy templates update tmpl_123 --blocks-file ./welcome-v2-blocks.json
sequenzy templates delete tmpl_123
```

Behavior:

- `templates list`: `GET /api/v1/templates`
- `templates get`: `GET /api/v1/templates/:id`
- `templates create`: `POST /api/v1/templates`
- `templates update`: `PUT /api/v1/templates/:id`
- `templates delete`: `DELETE /api/v1/templates/:id`

Caveats:

- create requires `name`, `subject`, and either `html` or `blocks`
- update accepts `name`, `subject`, `html`, and `blocks`
- `--blocks-json` and `--blocks-file` pass Sequenzy block arrays through directly
- conditional email content is only available through block JSON, using a block-level `condition` object
- raw HTML is still stored as a single text block by the current API path
- deletion can fail if the template is still referenced by a campaign or sequence

## Campaigns

```bash
sequenzy campaigns list
sequenzy campaigns list --status draft --company comp_123
sequenzy campaigns get camp_123
sequenzy campaigns create "April Launch" --prompt "Announce our new dashboard"
sequenzy campaigns create "April Launch" --subject "We shipped" --html-file ./campaign.html
sequenzy campaigns create "April Launch" --subject "We shipped" --blocks-file ./campaign-blocks.json
sequenzy campaigns update camp_123 --subject "Updated subject"
sequenzy campaigns update camp_123 --blocks-file ./campaign-v2-blocks.json
sequenzy campaigns update camp_123 --reply-to support@example.com
sequenzy campaigns update camp_123 --reply-profile reply_123
sequenzy campaigns test camp_123 --to you@example.com
```

Behavior:

- `campaigns list`: `GET /api/v1/campaigns`
- `campaigns get`: `GET /api/v1/campaigns/:id`
- `campaigns create`: `POST /api/v1/campaigns`
- `campaigns update`: `PUT /api/v1/campaigns/:id`
- `campaigns test`: `POST /api/v1/campaigns/:id/test`
- dashboard-aware responses include `url` on campaign records and `appUrls` on the top-level JSON when the company can be resolved

Caveats:

- create supports `name`, optional `subject` when `--prompt` is used, `html`, `blocks`, `--prompt`, `--style`, and `--tone`
- update supports `name`, `subject`, `html`, `blocks`, `--reply-to`, and `--reply-profile`
- `--prompt` generates draft campaign content through `POST /api/v1/generate/email`; do not combine it with HTML or block flags
- `--blocks-json` and `--blocks-file` pass Sequenzy block arrays through directly
- conditional email content is only available through block JSON, using block-level `condition` rules
- `--reply-to` resolves an existing reply profile by email and `--reply-profile` sets it directly by ID
- `--reply-to` and `--reply-profile` are mutually exclusive
- `campaigns get` now includes saved reply-to details when the campaign has a reply profile
- only draft campaigns can be updated through this API path
- there is no CLI command for sending, scheduling, pausing, or cancelling campaigns
- in the current backend checkout, `campaigns test` returns a success message path rather than a confirmed email send

MCP parity:

- `update_campaign` accepts `name`, `subject`, `html`, `blocks`, `replyTo`, and `replyProfileId`
- `replyTo` and `replyProfileId` are mutually exclusive
- MCP rejects calls that omit all update fields before hitting the API
- MCP rejects unsupported extra update fields before hitting the API

## Sequences

```bash
sequenzy sequences list
sequenzy sequences get seq_123
sequenzy sequences create onboarding --trigger event_received --event-name signup.completed --goal "Guide new users to activation" --email-count 4
sequenzy sequences create onboarding --trigger contact_added --list-id list_123 --steps-file ./steps.json
sequenzy sequences update seq_123 --steps-file ./sequence-updates.json
sequenzy sequences enable seq_123
sequenzy sequences disable seq_123
sequenzy sequences delete seq_123
```

Behavior:

- `sequences list`: `GET /api/v1/sequences`
- `sequences get`: `GET /api/v1/sequences/:id`
- `sequences create`: `POST /api/v1/sequences`
- `sequences update`: `PUT /api/v1/sequences/:id`
- `sequences enable`: `POST /api/v1/sequences/:id/enable`
- `sequences disable`: `POST /api/v1/sequences/:id/disable`
- `sequences delete`: `DELETE /api/v1/sequences/:id`
- dashboard-aware responses include `url` on sequence records and `appUrls` on the top-level JSON when the company can be resolved

Caveats:

- CLI sequence creation supports either AI `--goal` mode or explicit `--steps-json` / `--steps-file` mode
- `--email-count` is only meaningful with `--goal`
- `--email-count` accepts 1 to 10 generated emails
- trigger-specific options depend on `--trigger`
- updates accept either step payloads or email payloads via `--steps-*` or `--emails-*`

## AI Generation

```bash
sequenzy generate email "Welcome a new user to our analytics product"
sequenzy generate email "Product launch announcement" --style branded --tone friendly
sequenzy generate sequence "Onboard a new workspace admin" --count 4 --days 14
sequenzy generate subjects "April product launch" --count 8
```

Behavior:

- `generate email`: `POST /api/v1/generate/email`
- `generate sequence`: `POST /api/v1/generate/sequence`
- `generate subjects`: `POST /api/v1/generate/subjects`
- `--json` returns the raw API response for agent/tool parsing

Caveats:

- generated content is draft content and should be reviewed before sending
- `generate sequence --count` accepts 1 to 10 emails
- `generate email` supports optional `--style` and `--tone`

## API Keys

```bash
sequenzy api-keys create
sequenzy api-keys create --name "CI deploy key" --company comp_123
```

Behavior:

- sends `POST /api/v1/api-keys`
- body shape is `{ name }`

Caveat:

- the plain API key is returned only at creation time; save it immediately

## Websites

```bash
sequenzy websites list --company comp_123
sequenzy websites add example.com --company comp_123
sequenzy websites check example.com --company comp_123
sequenzy websites guide --framework nextjs --use-case transactional
```

Behavior:

- `websites list`: `GET /api/v1/websites`
- `websites add`: `POST /api/v1/websites`
- `websites check`: `GET /api/v1/websites/:domain`
- `websites guide`: `POST /api/v1/integration-guide`

## Commands To Treat As Unsupported

Treat these requested workflows as unsupported in the CLI even though related nouns exist:

- campaign send, schedule, pause, cancel, or resume flows
- bulk subscriber import
- tag creation, update, or deletion
- list update or deletion

## Operational Caveats

- prefer `SEQUENZY_API_KEY` for automation instead of interactive login
- use `--json` when another tool or agent needs structured output; dashboard-aware commands add `url`/`appUrls` fields when possible
- when the user asks for a workflow outside the current CLI surface, say so directly and choose between dashboard or direct API use instead of inventing commands
