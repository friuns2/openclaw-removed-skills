---
name: agent-ping-pong
version: 2.1.0
description: "Your OpenClaw is the brain. Codex or Claude Code are the hands. The clipboard is the protocol."
homepage: https://github.com/highnoonoffice/agent-ping-pong
source: https://github.com/highnoonoffice/agent-ping-pong
license: MIT
metadata: ~
---

# Agent Ping Pong

Agent Ping Pong is a two-agent coding workflow where OpenClaw acts as Maestro — speccing, reviewing, and directing — while a coding agent (Codex or Claude Code) does the build work. You relay structured blocks between them by copy-paste. No direct agent-to-agent connection required. Just two windows and a clipboard. The result: you ship real code to GitHub from a conversation, your agent reviews the PR, you approve the merge. Repeat.

If you have a ChatGPT Plus subscription ($20/month), you already have access to Codex — no extra cost. Claude Code works the same way and is the preferred choice for many OpenClaw users. Pick whichever you have.

**Your OpenClaw is the brain. Codex or Claude Code are the hands. The clipboard is the protocol.**

### The Aesthetic

Codex speaks in blocks. OpenClaw speaks in blocks. The blocks are addressed to each other — not to you.

When Codex finishes a build, it returns a compact structured report. You copy it. When OpenClaw reviews a PR, it returns a structured block formatted as a message to Codex. You copy it. You are the physical layer between two agents that are talking to each other. You're not reading the mail. You're carrying it.

That's the whole design. Two agents. One clipboard. You decide when to send.

**The block is the unit.** Every agent-to-agent payload lives inside a single block — one copy action, one paste. Agents can add human-readable context above or below the block. That prose is for you. The block is for the other agent. Never mix them.

Both agents must hold this standard. If either agent starts responding in prose instead of blocks, the ping pong breaks down. The block format is not optional — it's the protocol.

**Every block must request a block in return.** The last line of every `[AGENT_HANDOFF]` block — before the closing tag — must be:

    Reply with a single [AGENT_HANDOFF] block. No prose outside the block.

This applies to both agents. OpenClaw includes it in every spec and review block. Codex includes it in every delivery and acknowledgment block. If either agent drops it, the human adds it before relaying. The protocol is only as strong as both ends enforcing it.

**The `[AGENT_HANDOFF]` schema:**

Codex and OpenClaw use tagged blocks to communicate:

```
[AGENT_HANDOFF]
type: delivery | review_verdict | acknowledgment | schema_check
target: Magnus | Codex
status: completed | confirmed
... fields relevant to the type ...
[/AGENT_HANDOFF]
```

Codex uses this for build completions, status reports, and schema negotiations. OpenClaw uses this for specs, review verdicts, and confirmations. The human copies the block and pastes it to the other agent. Neither agent needs to see anything outside the block to do their job.

---

## What You Need

- **OpenClaw** — your Maestro. Higher-level intelligence. Specs the work, reviews PRs, sends critique.
- **Codex or Claude Code** — your coding agent. Codex is free with ChatGPT Plus ($20/mo). Claude Code works equally well. Either one does the build, opens PRs, and never merges without approval.
- **GitHub account** — free. Source of truth. Where the code lives.
- **Vercel account** — free tier. Deploy when something's ready to go public.
- **One sandbox repo for Codex** — `your-username/codex-repo`. Codex lives here permanently. One PAT. Every build goes here first.
- **One fine-grained PAT for Codex** — scoped to `codex-repo` only. You create this once and never touch it again.
- **One fine-grained PAT for OpenClaw** — scoped to `codex-repo` + each target repo you want it to push to. One PAT per repo. You add repos as you add projects.

---

## One-Time Setup

### 1. Install your coding agent
**Codex:** Download from [chatgpt.com](https://chatgpt.com) — available under the Tools menu with a ChatGPT Plus subscription. Free with your existing subscription.

**Claude Code:** Install via `npm install -g @anthropic-ai/claude-code`. Requires an Anthropic API key or Claude Pro/Max subscription. Works identically to Codex in this workflow — same block format, same PR protocol, same merge rules.

### 2. Create the Codex sandbox repo
Go to github.com/new. Name it `codex-repo`. Make it private. No template, no README — Codex will initialize it.

This is Codex's permanent home. Every project Codex touches goes here first, regardless of where it ends up. You never create another repo for Codex.

### 3. Create a fine-grained PAT for Codex
In GitHub: Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens.

Scope it to **codex-repo only**. Permissions needed:
- Contents: Read & Write
- Pull Requests: Read & Write
- Metadata: Read

This is the key insight: Codex only gets access to what you give it. `codex-repo` is the sandbox. Your other repos are untouched. You set this token once and never change it.

### 4. Create a fine-grained PAT for OpenClaw
In GitHub: Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens.

Scope it to **codex-repo** to start. As you add public target repos, add each one to this token's repository access list. Permissions needed:
- Contents: Read & Write
- Pull Requests: Read & Write
- Metadata: Read

This gives OpenClaw exactly what it needs — read PRs in the sandbox, push to approved target repos — and nothing else. Your other repos stay untouched.

**What OpenClaw can do with this PAT:** read PRs in `codex-repo`, push code to any repo explicitly listed in the token's scope, create branches, commit files, open PRs on target repos.

**What neither agent can do:** create new GitHub repos. That one manual step is always yours. Takes 20 seconds at github.com/new.

### 5. Connect Codex to codex-repo
In Codex Desktop: add `codex-repo`, paste the fine-grained PAT when prompted. Codex is now wired. This never changes regardless of what you're building.

### 6. Tell Codex one hard rule
In your first Codex message, establish the protocol:

    Hard rule: open a PR against main for every build. Do not merge. Wait for review.

Say it once. It holds for the session.

---

## The Workflow Loop

This is the ping pong. Each volley is a structured block you copy-paste from one agent to the other.

```
YOU → OpenClaw:  "Here's what I want to build: [describe it]"

OpenClaw → YOU:  Spec block. Exact requirements, edge cases, constraints.
                 Copy this.

YOU → Codex:     Paste the spec block.

Codex → YOU:     "PR opened. Branch: feature/x. Commit: abc1234."
                 Copy this.

YOU → OpenClaw:  Paste Codex's report.

OpenClaw → YOU:  Code review block. P0/P1/P2 findings. Fix instructions.
                 Copy this.

YOU → Codex:     Paste the review block.

Codex → YOU:     "Fixes applied. New commit: def5678."
                 Copy this.

YOU → OpenClaw:  Paste Codex's update.

OpenClaw → YOU:  "LGTM. Merge approved." or another review round.

YOU → Codex:     "Merge."  ← only you say this. Never OpenClaw directly.
```

The human never writes code. The human never writes to the agents in agent language. You describe intent to OpenClaw, relay blocks between them, and approve merges. That's the whole job.

---

## The Block Format

When OpenClaw hands you something to relay to Codex, it comes in a block. Copy it entirely. Paste it directly into Codex. Don't edit it.

When Codex reports back, copy its full response and paste it to OpenClaw with no wrapper. Just: "From Codex:" and paste.

The agents write to each other. You are the relay, not the translator.

---

## Code Review Format

When relaying a PR to OpenClaw for review, say:

```
Review this PR from Codex. Repo: [repo name]. PR: [number or URL]. Branch: [branch name].
```

OpenClaw will pull the code, read it, and return a review block formatted like this:

```
[Repo] — Code Review
    [files changed]

    ---

    P0 — [Must fix before merge]
    File: path/to/file — function name
    Issue: what's wrong
    Why it matters: impact
    Suggested patch: code or plain English fix

    ---

    P1 — [Should fix]
    ...

P2 — [Nice to have]
...
```

Paste that block to Codex verbatim. It knows what to do with it.

---

## Human in the Loop

The default is full ping pong — you relay blocks without intervening. But you're always in control. The clipboard is yours. You decide when to send.

Two modes:

**Relay mode (default):** Codex sends a block. You copy it. Paste to OpenClaw. OpenClaw sends a block. You copy it. Paste to Codex. You're not reading deeply — you're routing. Fast, token-efficient, gets things shipped.

**Review mode (your call):** Before you paste a block, read it. Decide if you agree. Add your own instruction. Change direction. This isn't a workflow break — it's the design working as intended. You intercept when the stakes are high enough to warrant it. The agents don't know the difference. They just receive whatever you send.

The rule: you always hit send. That's the human-in-the-loop. Not a gate, not a checkpoint — just a hand on the clipboard.

---

## Merge Protocol

Only you merge. Never ask OpenClaw to merge. Never ask Codex to merge without OpenClaw's approval.

The sequence:
1. OpenClaw says "LGTM" or "approved"
2. You tell Codex: "Merge."
3. Codex merges the PR
4. Done

If OpenClaw sends back findings, another round of ping pong happens before merge.

---

## The Sandbox Pattern — How Projects Actually Ship

Codex builds everything in `codex-repo`. That's the sandbox. OpenClaw reviews the PR there. When a build is approved, OpenClaw ports the clean code to the target repo — the public-facing project repo you created manually.

The flow for any new project:

    1. You create the target repo on GitHub (e.g. your-username/my-project)
    2. You describe what you want to OpenClaw
    3. OpenClaw writes the spec, sends it to Codex via you
    4. Codex builds in codex-repo, opens a PR
    5. You relay the PR to OpenClaw for review
    6. OpenClaw reviews, sends findings back to Codex
    7. Codex fixes, you relay, OpenClaw approves
    8. You tell Codex to merge in codex-repo
    9. OpenClaw ports the approved code to the target repo
    10. Done. The target repo has clean, reviewed code. Codex never touched it directly.

Codex stays in the sandbox forever. The sandbox accumulates a full history of everything ever built — searchable, auditable, contained. If Codex does something unexpected, it's in the sandbox, not in production.

OpenClaw uses one fine-grained PAT scoped to the repos it needs. Start with `codex-repo`. When you create a new target repo, add it to the token's repository access list in GitHub settings. No new token needed — just update the scope. Codex never needs a new one.

---

## Why This Is Cheaper Than You Think

If you have ChatGPT Plus, Codex costs you nothing on top of what you're already paying. If you're a Claude user, Claude Code runs on your existing subscription or API credits. Either way, the coding agent carries all the build volume at flat rate — no per-token cost on the work that generates the most tokens.

OpenClaw only spends tokens on judgment — speccing, reviewing, architectural decisions. That's the right use of a high-intelligence model. The rest is handled by the coding agent.

Stop burning a gigabrain on pawn-level tasks. Learn to play ping pong with your agents.

---

## The Trust Arc

Agent Ping Pong isn't one mode. It's a progression.

**Phase 1 — Eyes on everything.** Every block, you read it. You understand what Codex built. You understand what OpenClaw found. You're learning the workflow and building a baseline for what good looks like. Stay here until the pattern feels natural.

**Phase 2 — Relay mode.** You've seen enough clean PRs to trust the loop. You copy blocks without reading deeply. OpenClaw reviews. Codex fixes. You approve merges. You're the conductor — you show up for the performance, not the rehearsal.

**Phase 3 — Auto mode.** Early phases of a project, Codex is iterating fast, OpenClaw is reviewing consistently, nothing surprising is happening. You let it cook. You check in when a block lands. You merge when you see LGTM. The agents are doing the work. You're the human in the loop by presence, not by effort.

**Phase 4 (future).** The relay disappears. Direct agent-to-agent communication, human approval only at merge. Not today — but today's version builds the trust that makes that possible.

You decide which phase you're in on any given session. High-stakes build: eyes on everything. Routine iteration: auto mode. The clipboard is always yours. The agents only move when you send.

---

## Token Management

Codex runs on your ChatGPT Plus subscription — flat rate, no per-token cost. Use it for all build work, file creation and editing, running tests and lint, and fixing review findings.

OpenClaw handles judgment — speccing the work, reviewing PRs, architectural decisions, anything requiring real reasoning about intent.

This split is why the workflow is financially sustainable. Codex carries the volume. OpenClaw carries the intelligence.

---

## Don't Have OpenClaw?

You can run a lighter version of this workflow with ChatGPT chat as your reviewer instead of OpenClaw. The loop is the same — spec in one window, build in Codex, paste the PR back for review.

What you're missing: OpenClaw has memory across sessions, can access your files, runs on your machine, and costs nothing beyond the API calls you make. It's a fundamentally different class of agent than a stateless chat window.

Get OpenClaw at [openclaw.ai](https://openclaw.ai).

---

## Real Examples

### Schema Negotiation

Before the first build, Codex sent this unprompted:

```
[AGENT_HANDOFF]
type: schema_check
target: Magnus
request: Confirm preferred handoff schema for future completed outputs.
options:
- Current tagged text block format
- JSON
- YAML
note: Until you confirm, I will keep using the current tagged text block format.
[/AGENT_HANDOFF]
```

The human relayed it. OpenClaw confirmed the tagged block format. Codex acknowledged. Three messages. Two agents aligned on protocol. The human carried the blocks and didn't need to understand the negotiation to complete it.

That's the system working.

---

### Full Build Loop

A developer wanted to build a standalone React module — three sub-tabs with local JSON data, black/gold Tailwind theme, no API calls. They described it to OpenClaw in one message. OpenClaw returned a full spec block with component structure, data schema, interaction requirements, and edge cases. The developer pasted it to Codex.

Codex built the module, ran typecheck and lint, opened a PR. The developer pasted the PR report to OpenClaw. OpenClaw pulled the branch, read every file, and returned a structured review: 2 P1s and 3 P2s. The developer pasted the review block to Codex verbatim.

Codex fixed all five findings in one commit. The developer pasted the confirmation to OpenClaw. OpenClaw verified against the live commit. LGTM. The developer told Codex to merge. Done.

Total OpenClaw tokens: spec + review + verification. Zero build tokens. That's the split.

---

## OpenClaw PR Review Trigger

Instead of framing a PR review manually, use this exact prompt to trigger OpenClaw's review mode:

```
Review this PR from Codex. Repo: [repo name]. PR: [number or URL]. Branch: [branch name].
```

OpenClaw will pull the branch, read every changed file, and return a structured block addressed to Codex — P0/P1/P2 findings with file paths, issue descriptions, and suggested patches. Copy the block. Paste it to Codex. That's the volley.

You don't need to read it to relay it. But you can. That's review mode.

---

## Tips

- **One sandbox, always.** Codex lives in `codex-repo`. Never give Codex a PAT to a production repo or anything with real data.
- **Name your branches.** Tell Codex: "Branch name: feature/[short-description]." Keeps the PR history readable.
- **Feature branch → PR → approve → merge.** Never push direct to main for anything non-trivial.
- **Session context.** Start each Codex session with a one-paragraph context block: what the project is, what's already built, what this session is for. Codex doesn't have memory. Give it the brief.
- **When Codex goes sideways.** Paste the broken output to OpenClaw. Ask for a diagnosis. Relay the fix instruction back. One extra volley is cheaper than debugging blind.
