---
name: socialconductor
description: >
  Manage your SocialConductor AI comment automation bots from any chat app.
  Control Facebook, Instagram, YouTube, and TikTok — check status, pause or
  resume AI replies, view comment logs, manage leads, block users, and post
  manual replies — all without opening a browser. Automate social media
  comment responses with AI across multiple platforms.
summary: >
  AI-powered social media comment automation for Facebook, Instagram, YouTube,
  and TikTok. Control your bots via chat — pause, resume, view logs, manage
  leads, block users, post manual replies.
tags:
  - social-media
  - automation
  - facebook
  - instagram
  - youtube
  - tiktok
  - comments
  - ai-replies
  - marketing
  - saas
version: "1.7.1"
metadata:
  openclaw:
    emoji: "🤖"
    homepage: https://podium.socialconductor.ai
    always: false
---

# SocialConductor — Facebook, Instagram, YouTube & TikTok

Control your SocialConductor AI comment bots from WhatsApp, Slack, Telegram, or iMessage.

## Platforms

| Platform | Status | Dashboard |
|----------|--------|-----------|
| 👥 Facebook / Instagram | ✅ Live | podium.socialconductor.ai |
| 📺 YouTube | ✅ Live | studio.socialconductor.ai |
| 🎵 TikTok | ✅ Live | violin.socialconductor.ai |

Each platform uses its own API key. You can connect one, two, or all three —
commands are prefixed by platform so OpenClaw always knows which bot you mean.

---

## NEW: OpenClaw Core Features

Across all platforms, you can now access advanced features:

| Feature | Commands | Description |
|---------|----------|-------------|
| **Drafts & Approvals** | `show my pending drafts`<br>`approve all pending drafts` | View and bulk approve pending AI replies. |
| **Analytics** | `show my daily analytics`<br>`show performance insights` | View daily statistics, trends, and core performance metrics. |
| **AI Teaching** | `show teaching examples`<br>`add this comment to teaching examples` | View "star" and "bad" example lists, and add new examples to train the AI tone. |
| **Advanced Tools** | `show my friends list`<br>`turn on vacation mode`<br>`open the viral vault` | Access friends/subscriptions, configure vacation scheduling, and view top-performing viral comments. |

---

## Facebook / Instagram — Account Requirements

> ⚠️ **Facebook requires a Business or Professional Creator account.**
> A personal Facebook profile will not work. Before connecting, make sure you have:
>
> - A **Facebook Page** (not a personal profile) set up at [business.facebook.com](https://business.facebook.com)
> - Your Page linked to a **Business Manager** or configured as a **Professional Creator Page**
> - Admin or Editor role on the Page
>
> Instagram automation is available if your Instagram account is connected to
> your Facebook Page as a **Professional (Creator or Business) Instagram account**.
> A standard personal Instagram account will not work.

## Facebook / Instagram — Setup (first time only)

Say:

> connect my facebook page

OpenClaw registers you and sends a browser link. Open it, log in with Facebook
(~30 seconds), close the tab. All Facebook and Instagram commands are now active.

> **Important:** Before the bot can post live replies, you must accept the
> SocialConductor terms of service at
> **https://podium.socialconductor.ai/terms** — takes 30 seconds.
> Until you do, the bot runs in simulation mode (replies are generated but
> not posted). You will see a `terms_required` error in chat as a reminder.

### Facebook / Instagram Trial

New accounts get a **7-day free trial** with up to 30 AI replies per day.
After the trial, visit podium.socialconductor.ai/upgrade to subscribe.

## Facebook / Instagram — Commands

| Say this | What happens |
|----------|-------------|
| check my facebook bot | Mode, plan, trial status, daily usage, last 3 replies |
| pause my facebook bot | Hold ON — AI replies stop immediately |
| resume my facebook bot | Hold OFF — AI replies resume |
| show recent facebook comments | Last 5 log entries |
| show posted facebook comments | Only successfully posted replies |
| show facebook skipped comments | Comments the bot filtered (gate skips) |
| show my facebook leads | Lead-flagged comments (price, buy, how much…) |
| reply to facebook comment abc123 saying Great question! | Posts manual reply |
| block @username | Adds @username to block list |
| unblock @username | Removes @username from block list |
| show blocked facebook users | Lists all blocked accounts |
| facebook simulation mode on | Replies generated but not posted |
| facebook simulation mode off | Bot posts for real |
| enable facebook bot | Turns on auto-reply |
| disable facebook bot | Turns off auto-reply |
| turn on viral intelligence | Enables Reaction-Weighted Intelligence |
| connect my facebook page | Get a one-time browser link |

## Facebook / Instagram — Webhook Base URL
https://podium.socialconductor.ai/api/openclaw/

---

## YouTube — Account Requirements

> ⚠️ **YouTube requires an active YouTube channel (YouTube Page).**
> A Google account alone is not enough — you must have created a YouTube channel
> at [youtube.com](https://youtube.com) before connecting. The channel can be
> a standard creator channel; no special business setup is required.

## YouTube — Setup (first time only)

Say:

> connect my youtube channel

OpenClaw registers you and sends a browser link. Open it, sign in with Google
(30 seconds), close the tab. All YouTube commands are now active.

## YouTube — Commands

| Say this | What happens |
|----------|-------------|
| check my youtube bot | Mode, plan, daily usage, last 3 replies |
| pause my youtube bot | Hold ON — replies stop |
| resume my youtube bot | Hold OFF — replies resume |
| show recent youtube comments | Last 5 log entries |
| show posted youtube comments | Only successfully posted replies |
| show youtube skipped comments | Comments the bot filtered |
| show youtube leads | Lead-flagged comments |
| reply to youtube comment abc123 saying Great question! | Posts manual reply |
| show my youtube videos | Video polling status |
| show stale youtube videos | Videos with no recent activity |
| reactivate youtube video abc123 | Resumes polling that video |
| youtube simulation mode on | Replies generated but not posted |
| youtube simulation mode off | Bot posts for real |
| enable youtube bot | Turns on auto-reply |
| disable youtube bot | Turns off auto-reply |
| fast youtube response mode | Sets delay to fast |
| aggressive youtube response mode | Sets delay to aggressive |
| conservative youtube response mode | Sets delay to conservative |

## YouTube — Webhook Base URL
https://studio.socialconductor.ai/api/openclaw/

---

## TikTok — Account Requirements

> ✅ **TikTok works with standard creator accounts.**
> No business account or special setup is required — any normal TikTok creator
> account can connect. Just make sure your account is active and can post/comment.

## TikTok — Setup (first time only)

Say:

> connect my tiktok account

OpenClaw registers you and sends a browser link. Open it on your phone or
computer, scan the TikTok QR code, close the tab. All TikTok commands are now active.

> **QR note:** TikTok login requires a QR code scanned in a real browser.
> OpenClaw sends you a link — it cannot embed the QR in chat.
> The link expires in 15 minutes.

### TikTok Trial

New accounts get a **7-day free trial** with up to 30 AI replies per day.
After the trial, visit violin.socialconductor.ai/upgrade to subscribe.
Expired trial channels are automatically removed from polling.

## TikTok — Commands

| Say this | What happens |
|----------|-------------|
| check my tiktok bot | Mode, plan, trial status, daily usage, last 3 replies |
| pause my tiktok bot | Hold ON — replies stop |
| resume my tiktok bot | Hold OFF — replies resume |
| show recent tiktok comments | Last 5 log entries |
| show posted tiktok comments | Only successfully posted replies |
| show tiktok skipped comments | Comments the bot filtered |
| show tiktok leads | Lead-flagged comments |
| reply to tiktok comment abc123 saying Great video! | Posts manual reply via Playwright |
| block @username | Adds @username to block list |
| unblock @username | Removes @username from block list |
| show blocked tiktok users | Lists all blocked accounts |
| show my tiktok videos | Video polling status |
| show stale tiktok videos | Videos with no recent activity |
| reactivate tiktok video abc123 | Resumes polling that video |
| connect my tiktok account | Get a QR code browser link |
| tiktok simulation mode on | Replies generated but not posted |
| tiktok simulation mode off | Bot posts for real |
| enable tiktok bot | Turns on auto-reply |
| disable tiktok bot | Turns off auto-reply |
| fast tiktok response mode | Sets delay to fast |
| aggressive tiktok response mode | Sets delay to aggressive |
| conservative tiktok response mode | Sets delay to conservative |

## TikTok — Webhook Base URL
https://violin.socialconductor.ai/api/openclaw/

---

## Auth & Privacy

**API Keys:** The environment variables (`SC_FB_API_KEY`, `SC_YT_API_KEY`, `SC_TIKTOK_API_KEY`) are **SocialConductor-issued API keys** generated from your SocialConductor dashboard. They are *not* your native Meta, Google, or TikTok passwords or OAuth tokens. You only need to provide the keys for the specific platforms you wish to automate.

**Registration & Data Privacy:** When you run a `connect` command, OpenClaw sends only a secure, anonymous identifier (`{"openclaw_user_id": "..."}`) to the SocialConductor API via `POST /api/openclaw/register` to generate your one-time browser link. **No chat history, personal data, or agent context is transmitted during this registration phase.**

Tokens are stored locally by OpenClaw and sent as `Authorization: Bearer <key>` on every call. Keys are SHA-256 hashed before server-side storage — the plaintext is never saved remotely.

| Platform | Register endpoint |
|----------|-------------------|
| Facebook / Instagram | https://podium.socialconductor.ai/api/openclaw/register |
| YouTube | https://studio.socialconductor.ai/api/openclaw/register |
| TikTok | https://violin.socialconductor.ai/api/openclaw/register |

---

## Error reference

| Error code | Meaning |
|------------|---------|
| `unauthorized` | API key missing or invalid |
| `trial_expired` | 7-day trial ended — upgrade at the platform's /upgrade page |
| `no_page` | Platform not linked yet — say "connect my facebook/tiktok/youtube account" |
| `terms_required` | Terms of service not accepted — visit podium.socialconductor.ai/terms |
| `rate_limited` | Platform rate-limited this channel — bot resumes automatically |
| `reply_failed` | Reply attempt failed — check dashboard for details |

---

## Support

- Email: support@socialconductor.ai
- Facebook Dashboard: https://podium.socialconductor.ai
- YouTube Dashboard: https://studio.socialconductor.ai
- TikTok Dashboard: https://violin.socialconductor.ai
