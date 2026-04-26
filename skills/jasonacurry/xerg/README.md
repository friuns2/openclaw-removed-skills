# Xerg

Xerg audits OpenClaw and Hermes workflows in dollars, not tokens. It reads gateway logs and session transcripts, surfaces confirmed waste plus savings opportunities, and lets you measure fixes with `--compare`.

Everything runs locally by default. The CLI is open source (MIT), published on npm as `@xerg/cli`, and the full source is at [github.com/xergai/xerg](https://github.com/xergai/xerg). No account is required for local audits. Hosted sync and hosted MCP are optional paid workspace features.

## Install

```bash
npm install -g @xerg/cli
```

Or run without installing:

```bash
npx @xerg/cli init
```

## What It Finds

- **Retry waste** — failed calls that burned spend before a later success
- **Loop waste** — runs that exceeded efficient iteration bounds
- **Context bloat** — input token volume far above the workflow baseline
- **Downgrade candidates** — expensive models on operationally simple tasks
- **Idle waste** — recurring heartbeat or monitoring loops worth reviewing

## Quick Start

```bash
xerg init
xerg audit --compare
```

Use direct commands when you want explicit control:

```bash
xerg doctor --runtime openclaw
xerg audit --runtime hermes
xerg audit --json
```

## Works Where Your Agents Run

- Local machine: OpenClaw and Hermes
- Remote VPS over SSH: `xerg audit --remote user@host` for OpenClaw in this phase
- Railway: `xerg audit --railway` for OpenClaw in this phase
- Multiple sources: `xerg audit --remote-config ~/.xerg/remotes.json` for OpenClaw sources in this phase

If local defaults are empty, inspect the target directly first with `xerg doctor --remote user@host` or `xerg doctor --railway`.

## Optional Hosted Follow-Up

```bash
xerg connect
xerg mcp-setup
```

- `connect` offers browser auth and pushing the latest audit
- `mcp-setup` prints or writes hosted MCP config for supported clients
- local audits and compare remain available if you skip hosted setup

## CI And Automation

```bash
xerg audit --push --fail-above-waste-rate 0.25
xerg audit --fail-above-waste-usd 100
xerg audit --json
```

## Links

- Docs: [xerg.ai/docs](https://xerg.ai/docs)
- GitHub: [xergai/xerg](https://github.com/xergai/xerg)
- npm: [@xerg/cli](https://www.npmjs.com/package/@xerg/cli)
- Pilot: [xerg.ai/pilot](https://xerg.ai/pilot)
- Support: `query@xerg.ai`
