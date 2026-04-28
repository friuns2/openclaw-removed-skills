---
name: surface-cli
description: "Use the Surface mail CLI to read and act on Gmail and Outlook mail through one JSON-first contract. Prefer this skill when you need Outlook access for school or work accounts that do not expose IMAP or require admin setup, plus stable refs for unread fetch, structured search, thread refresh, message read, attachments, send or draft, archive, mark read or unread, and Outlook RSVP."
metadata:
  {
    "openclaw":
      {
        "emoji": "📬",
        "homepage": "https://github.com/VishalJ99/surface-cli",
        "requires": { "bins": ["surface"] },
        "install":
          [
            {
              "id": "node",
              "kind": "node",
              "package": "surface-cli",
              "bins": ["surface"],
              "label": "Install Surface CLI (npm)",
            },
          ],
      },
  }
---

# Surface CLI

Surface is a local-first mail CLI for Gmail and Outlook. It is especially useful for Outlook
school or work accounts that only work through the web UI and do not require IMAP or admin
changes. Surface prints machine-readable JSON to stdout and stores local state in
`~/.surface-cli`.

## Use This Skill When

- the user wants to read or triage email from Gmail or Outlook
- the user needs a provider-neutral CLI for search, unread fetch, read, attachments, or actions
- you need stable `thread_ref` / `message_ref` values for follow-up commands or thread watching

## Prerequisites

1. Surface CLI installed (`surface --help` should work)
2. At least one configured account
3. Valid auth for the target account

Check setup:

```bash
surface account list
surface auth status
```

## Account Setup

Add an account:

```bash
surface account add personal_2 --provider gmail --email you@example.com
surface account add uni --provider outlook --email you@example.com
```

For reliable `summary.needs_action`, Surface should know who the account owner is. Gmail auth can
verify the mailbox email automatically; Outlook may need explicit human identifiers:

```bash
surface account identity set uni --email you@example.com --name "Your Name" --name-alias "FirstName"
surface account identity show uni
```

Log in:

```bash
surface auth login personal_2
surface auth login uni
```

Local policy lives in:

```text
~/.surface-cli/config.toml
```

Important local knobs:

- `summarizer_backend`
- `summarizer_model`
- `writes_enabled`
- `send_mode`
- `test_recipients`
- `test_account_allowlist`

Summarization is opt-in and controlled by the user's local config. Do not change
`summarizer_backend`, `summarizer_model`, or related environment variables unless the user
explicitly asks. If an external summarizer backend is enabled, email thread content may be sent to
the configured model provider; confirm the user accepts that privacy tradeoff before enabling or
changing summarization.

## Common Operations

### List Accounts

```bash
surface account list
surface auth status
surface auth status personal_2
```

### Fetch Unread Threads

```bash
surface mail fetch-unread --account uni --limit 10
surface mail fetch-unread --account personal_2 --limit 20
surface mail fetch-unread --account uni --session sess_01... --limit 10
```

### Search Mail

```bash
surface mail search --account uni --text "invoice" --limit 10
surface mail search --account uni --from registrar@school.edu --subject "waitlist" --limit 10
surface mail search --account uni --session sess_01... --from registrar@school.edu --limit 10
surface mail search --account personal_2 --mailbox inbox --label unread --text "sale" --limit 10
surface mail search --account personal_2 --text "has:attachment newer_than:30d" --limit 5
```

### Watching Threads And Topics

Surface is the polling primitive, not the scheduler or delivery transport. If the user asks to
watch mail, use the surrounding automation system to rerun Surface commands and surface updates to
the user-requested destination.

- For a specific thread watch, persist the `account`, `thread_ref`, and the newest known
  message/timestamp. On each check, rerun `surface mail thread get <thread_ref> --refresh` and
  notify only when the newest message state changes.
- For a topic watch, establish a baseline with `search`, then use periodic `fetch-unread` checks
  to catch new inbox arrivals and targeted `search` checks when the topic has clear `--from`,
  `--subject`, `--mailbox`, `--label`, or `--text` filters.
- Do not assume a delivery target. Return updates through the current agent conversation or the
  explicit destination the user asked for.
- Reasonable starting cadences are: 5-10 minutes for one active thread, 30-60 minutes for a
  narrow topic watch, and 2-4 hours for inbox digests. Avoid sub-5-minute polling unless the user
  explicitly asks for it.
- For Outlook-heavy polling, keep concurrency modest and prefer one warm session per parallel
  worker if several live checks will run close together.

### Warm Sessions

```bash
surface session start --account uni
surface session list
surface session stop sess_01...
```

### Parallel Read Guidance

Read-only commands may be run in parallel. Live probes passed for:

- two Gmail searches on the same account
- two cold Outlook searches on the same account
- Gmail and Outlook searches at the same time
- two separate Outlook warm sessions searched at the same time
- two searches sharing one Outlook warm session

For Outlook, keep concurrency modest because each cold command or warm session uses browser
resources. If planning multiple concurrent Outlook operations, prefer one warm session per
parallel worker. Reusing the same `--session` concurrently works in the tested case but can be
slower due to contention.

### Read One Thread

```bash
surface mail thread get thr_01...
surface mail thread get thr_01... --refresh
surface mail thread get thr_01... --refresh --session sess_01...
```

### Read One Message

```bash
surface mail read msg_01...
surface mail read msg_01... --refresh
surface mail read msg_01... --refresh --session sess_01...
surface mail read msg_01... --mark-read
```

### Attachments

```bash
surface attachment list msg_01...
surface attachment download msg_01... att_01...
```

### Compose And Send

```bash
surface mail send --account personal_2 --to recipient@example.com --subject "Hello" --body "Test"
surface mail send --account personal_2 --to recipient@example.com --subject "Hello" --body "Test" --draft
surface mail reply msg_01... --body "Thanks"
surface mail reply msg_01... --body "Thanks" --draft
surface mail reply-all msg_01... --body "Thanks everyone"
surface mail forward msg_01... --to recipient@example.com --body "FYI"
```

### Mailbox Actions

```bash
surface mail archive msg_01...
surface mail mark-read msg_01...
surface mail mark-unread msg_01...
surface mail rsvp msg_01... --response accept
```

## Workflow

1. Start with `surface account list` if the target account is unclear.
2. Use `surface auth status` before assuming a provider is ready.
3. Use `surface account identity show <account>` if `summary.needs_action` looks wrong; add
   `--name-alias` or `--email-alias` with `surface account identity set` when the mailbox address
   alone is not enough to identify the user in message bodies.
4. For triage, prefer `fetch-unread` or `search` and inspect the returned thread/message refs.
5. If you expect several live Outlook reads in a row, start a warm session first and reuse its `session_id`.
6. For a thread watch, use `surface mail thread get <thread_ref> --refresh` and compare the newest
   message state against the stored prior observation before notifying.
7. For a topic watch, start with `search` to set the baseline, then use `fetch-unread` for new
   inbox arrivals plus targeted `search` when the watch has narrow filters.
8. Read only the messages you need with `surface mail read <message_ref>`.
9. For passive watching, do not mutate read state. If the user explicitly asks you to triage unread
   mail and write safety is enabled, marking handled messages read after reporting is acceptable
   unless the user asks to keep them unread.
10. Act using refs from Surface output. Do not rely on array positions from previous JSON.

## Important Rules

- Surface outputs JSON on stdout. Parse it instead of scraping terminal text.
- Use `message_ref` and `thread_ref` for follow-up commands.
- `search` accepts structured filters for sender, subject, mailbox, and labels in addition to raw `--text`.
- `session start` is the explicit opt-in path for warm Outlook read sessions. In v1, `--session` is supported on `search`, `fetch-unread`, `thread get --refresh`, and `read`.
- `thread get --refresh` is the thread-level live refresh path for automations that watch a specific conversation.
- `read` is cache-first by default. Use `--refresh` when you need live provider state.
- the first session-backed Outlook query still pays mailbox setup cost; the main win is faster follow-on live reads in the same mailbox session
- `read` does not download attachments. Use `surface attachment download`.
- `fetch-unread` and `search` do not mutate mailbox state.
- passive watching should stay read-only; do not mark watched mail read unless the user explicitly asks
- if the user asks for unread triage rather than passive watching, `mark-read` or `read --mark-read`
  is acceptable only after reporting and only when local write safety allows it
- watcher notifications should go to the user-requested destination; do not invent a session,
  channel, or DM target
- `--draft` is the safe compose path when you do not need to send immediately.

## Provider Notes

- Gmail and Outlook both support read, search, unread fetch, attachments, send/reply/forward,
  archive, mark-read, mark-unread, RSVP, and `--draft`.
- Gmail RSVP requires Google Calendar API access on the authenticated account. If RSVP returns a
  reauth error, re-run `surface auth login <account>`.

## Safety

- Respect local write-safety policy from `~/.surface-cli/config.toml` and any `SURFACE_*` env vars.
- Do not send mail unless write safety is enabled locally.
- Prefer the configured sink recipients from local config; do not invent recipients.
- For send-like tests, use `--draft` unless the task explicitly requires a live send.
- When testing live sends, only send to recipients already configured locally for safe testing.

## Examples

```bash
surface account list
surface auth status
surface session start --account uni
surface mail fetch-unread --account uni --limit 10
surface mail fetch-unread --account uni --session sess_01... --limit 10
surface mail search --account personal_2 --from alerts@example.com --subject 'discount' --mailbox inbox --label unread --limit 5
surface mail thread get thr_01... --refresh --session sess_01...
surface mail read msg_01... --refresh --session sess_01...
surface mail read msg_01... --mark-read
surface attachment list msg_01...
surface attachment download msg_01... att_01...
surface mail reply msg_01... --body 'Thanks' --draft
surface mail archive msg_01...
```
