# Use Cases

## Pick The Right Flow

### "Log into Sequenzy on this machine"

Use:

```bash
sequenzy login
```

Then verify:

```bash
sequenzy whoami
```

Prefer `SEQUENZY_API_KEY` instead when the task is fully non-interactive or running in CI.

## "Check whether I am authenticated"

Use:

```bash
sequenzy whoami
```

Interpretation:

- success means a local API key is available
- failure means the agent should ask for login or a `SEQUENZY_API_KEY`

Remember that this is local-state validation, not a fresh server-side account lookup.

## "Show me account or company info"

Use:

```bash
sequenzy account
sequenzy companies list
sequenzy companies get comp_123
sequenzy urls --company comp_123
```

Choose:

- `account` for user ID, current company, and accessible companies
- `companies list` for a compact list with localization info
- `companies get` when the user already has a company ID
- `urls` when the user needs a dashboard/settings link

## "Open, review, or edit something I just created"

Prefer the `url` or `appUrls` fields returned by recent CLI/MCP calls. If you need to generate links from IDs:

```bash
sequenzy urls --company comp_123 --sequence seq_123
sequenzy urls --company comp_123 --campaign camp_123
sequenzy urls --company comp_123 --settings-tab integrations
```

MCP equivalent: call `get_app_urls` with:

```json
{
  "companyId": "comp_123",
  "sequenceId": "seq_123",
  "settingsTab": "integrations"
}
```

URL patterns:

- sequence editor: `/dashboard/company/{companyId}/sequences/{sequenceId}`
- campaign editor: `/dashboard/company/{companyId}/campaign/{campaignId}`
- template/email editor: `/dashboard/company/{companyId}/emails/{emailId}`
- settings: `/dashboard/company/{companyId}/settings`
- settings tab: `/dashboard/company/{companyId}/settings?tab={tab}`

After generating a sequence or campaign, give the user the relevant review/edit URL instead of only returning the ID.

## "Show me delivery performance"

Use:

```bash
sequenzy stats
sequenzy stats --period 30d
sequenzy stats --campaign camp_123
sequenzy stats --sequence seq_123
```

Choose:

- plain `stats` for account-level overview
- `--campaign` when the user gives a campaign ID
- `--sequence` when the user gives a sequence ID

Ask for the missing ID instead of guessing.

## "Add or update a subscriber"

What works today:

```bash
sequenzy subscribers add user@example.com --tag premium --attr name=John
sequenzy subscribers add user@example.com --tag premium --tag beta --company comp_123
sequenzy subscribers get user@example.com
```

Guidance:

- use `add` for single-recipient creation or upsert
- use repeated `--attr key=value` pairs for metadata
- repeated `--tag` values are supported
- use `--company` when the API key can access multiple companies
- use `subscribers get` when you need the full profile, list memberships, sequence enrollments, email stats, or recent activity

What does not work well today:

- bulk import
- advanced subscriber workflows across many records

For those, prefer the Sequenzy dashboard or direct API use.

## "Remove a subscriber"

Use:

```bash
sequenzy subscribers list --tag vip
sequenzy subscribers get user@example.com
sequenzy subscribers remove user@example.com
```

Use `--hard` only when the task explicitly requires permanent deletion:

```bash
sequenzy subscribers remove user@example.com --hard
```

Notes:

- plain `remove` performs a full unsubscribe workflow rather than a hard delete
- use `--company` when operating with a personal API key across multiple companies

## "Send one transactional email"

Template flow:

```bash
sequenzy send user@example.com --template tmpl_123 --var name=John
```

Raw HTML flow:

```bash
sequenzy send user@example.com --subject "Status update" --html-file ./email.html --var orderId=123
```

Checklist:

1. Confirm recipient email.
2. Confirm template ID or HTML source.
3. Confirm subject when sending raw HTML.
4. Confirm merge variables as `key=value`.

This command is for one-off transactional send behavior, not bulk campaign sends.

## "Create a list, tag view, or saved segment"

What works today:

```bash
sequenzy lists create Newsletter --description "Public newsletter list"
sequenzy tags
sequenzy segments list
sequenzy segments count seg_123
sequenzy segments create --name "Bought Pro" --stripe-product prod_pro
sequenzy segments create --name "VIP or Churn Risk" --match any --filter-json '[{"field":"tag","operator":"contains","value":"vip"},{"field":"emailOpened","operator":"is_not","value":"30d"}]'
```

For Stripe purchase thresholds:

```bash
sequenzy segments create --name "3+ Pro Payments" --stripe-product prod_pro --purchase-operator at-least --payments 3
```

Guidance:

- use `tags` for inspection only; there are no CLI tag mutations
- use Stripe product IDs, not product names
- use `--filter-json` when the user needs a non-Stripe or mixed filter payload
- use `--match any` when the segment should match any top-level filter instead of all filters
- `segments count` is the quickest way to preview impact before using a segment in a campaign

For MCP-driven workflows, `create_segment` supports the same Stripe filter shape and `filterJoinOperator: "or"` for match-any segments:

```json
{
  "filterJoinOperator": "or",
  "filters": [
    {
      "id": "filter-1",
      "field": "stripeProduct",
      "operator": "at_least",
      "value": "prod_pro:3"
    }
  ]
}
```

## "Create or manage a template"

What works today:

```bash
sequenzy templates list
sequenzy templates get tmpl_123
sequenzy templates create welcome --subject "Welcome" --html-file ./welcome.html
sequenzy templates create welcome --subject "Welcome" --blocks-file ./welcome-blocks.json
sequenzy templates update tmpl_123 --subject "Updated" --html-file ./welcome-v2.html
sequenzy templates update tmpl_123 --blocks-file ./welcome-v2-blocks.json
```

Guidance:

- use block JSON when the user needs conditional content or an exact editor-compatible structure
- use HTML input for simpler one-off content; this API path stores raw HTML as a single text block
- a conditional block uses a block-level `condition` object with merge-tag variable names and no `{{ }}` braces
- use `get` before `update` or `delete` when the user is uncertain about the target ID
- warn that delete can fail when the template is still referenced by a campaign or sequence

## "Create or manage a campaign"

What works today:

```bash
sequenzy campaigns list --status draft
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

Guidance:

- the CLI only handles draft creation, draft updates, inspection, and test requests
- create, get, update, list, and test outputs include dashboard URLs when the company can be resolved
- use `--prompt` for AI-generated draft content; do not combine it with HTML or block flags
- use block JSON when the user needs conditional content or an exact editor-compatible structure
- use `--reply-to` when the user knows the reply profile email and it already exists for the company
- use `--reply-profile` when the user already has the reply profile ID
- do not pass `--reply-to` and `--reply-profile` together
- use `campaigns get` after an update when you want to confirm the saved reply-to details
- there is no CLI command for sending or scheduling a campaign
- in the current backend checkout, `campaigns test` returns a success message path rather than confirmed delivery

For MCP-driven campaign updates, `update_campaign` supports the same reply-to behavior:

```json
{
  "campaignId": "camp_123",
  "replyTo": "support@example.com"
}
```

Use `replyProfileId` instead when the caller already has the reply profile ID, and never send both fields together.

Preferred fallback for unsupported campaign workflows:

- use the dashboard
- use direct API calls only if the task explicitly allows it and the relevant API is available

## "Create or manage a sequence"

What works today:

```bash
sequenzy sequences list
sequenzy sequences get seq_123
sequenzy sequences create onboarding --trigger event_received --event-name signup.completed --goal "Guide new users to activation" --email-count 4
sequenzy sequences create onboarding --trigger contact_added --list-id list_123 --steps-file ./steps.json
sequenzy sequences update seq_123 --steps-file ./sequence-updates.json
sequenzy sequences enable seq_123
sequenzy sequences disable seq_123
```

Minimal `steps.json` shape:

```json
[
  {
    "subject": "Welcome to Acme",
    "html": "<p>Hi there</p>",
    "delay": { "days": 0 }
  },
  {
    "subject": "Day 3 follow-up",
    "html": "<p>Here is the next step</p>",
    "delay": { "days": 3 }
  }
]
```

Guidance:

- CLI sequence creation supports either AI `--goal` mode or explicit step files
- create, get, update, and list outputs include dashboard URLs when the company can be resolved
- choose the correct trigger options for `--trigger`
- use `--goal` when you want AI-generated drafts, or `--steps-file` when you already know the exact step content
- use either `--steps-file` or `--emails-file` for update
- enable/disable are real CLI actions

## "Create an API key or inspect website/domain setup"

Use:

```bash
sequenzy api-keys create --name "CI deploy key" --company comp_123
sequenzy websites list --company comp_123
sequenzy websites add example.com --company comp_123
sequenzy websites check example.com --company comp_123
sequenzy websites guide --framework nextjs --use-case transactional
```

Guidance:

- save API keys immediately; the raw key is only returned on creation
- use `websites check` when the user needs DNS verification details
- use `websites guide` for integration code snippets rather than inventing framework examples

## "Generate email content with AI"

Use the CLI when the user wants draft copy or structured generated output:

```bash
sequenzy generate email "Welcome email for new SaaS trial users"
sequenzy generate sequence "Onboarding for SaaS trial users" --count 4 --days 14
sequenzy generate subjects "Black Friday sale" --count 5
```

Guidance:

- use `--json` when another agent or tool should parse the result
- generated content is draft content and should be reviewed before sending
- sequence generation accepts at most 10 emails
- use `sequenzy campaigns create "Name" --prompt "..."` when the user wants to create a draft campaign from generated content in one step
