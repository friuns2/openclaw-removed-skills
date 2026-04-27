---
name: h-ear
description: "H-ear.world transforms sound into an actionable, meaningful translation layer of the world around you. Describe, share and act upon environmental audio as a machine sensor that empowers you, your business and your AI flow."
version: 0.1.0
author: H-ear World
homepage: https://h-ear.world
metadata: {"openclaw": {"requires": {"env": ["HEAR_API_KEY", "HEAR_ENV"], "bins": []}, "primaryEnv": "HEAR_API_KEY"}}
---

# H-ear — Sound Intelligence for AI Agents

H-ear.world transforms sound into an actionable, meaningful translation layer of the world around you. Describe, share and act upon environmental audio as a machine sensor that empowers you, your business and your AI flow.

## Commands

| Command | Description |
|---------|-------------|
| `classify <url>` | Classify audio from a URL. Returns detected sound classes with confidence scores. |
| `classify batch <url1> <url2>...` | Batch classify multiple audio URLs. Results delivered asynchronously via the gateway's webhook endpoint. |
| `sounds [search]` | List supported sound classes (521+ across 3 taxonomies). |
| `usage` | Show API usage statistics (minutes, calls, quota). |
| `jobs [last N]` | List recent classification jobs with status. |
| `job <id>` | Show detailed job results with classifications. |
| `alerts on <sound>` | Enable real-time alerts for a sound class. Notifications delivered to your connected channel via the gateway. |
| `alerts off <sound>` | Disable alerts for a sound class. |
| `health` | Check API status. |

## Setup

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HEAR_API_KEY` | Yes* | | H-ear Enterprise API key (`ncm_sk_...`). Required unless `HEAR_BEARER_TOKEN` is set. Get one at [h-ear.world](https://h-ear.world). |
| `HEAR_BEARER_TOKEN` | Yes* | | OAuth bearer token. Alternative to `HEAR_API_KEY` — one of the two must be set. |
| `HEAR_ENV` | Yes | | Target environment: `dev`, `staging`, or `prod`. |
| `HEAR_BASE_URL` | No | Per-environment default | Override API base URL (advanced). |

*One of `HEAR_API_KEY` or `HEAR_BEARER_TOKEN` is required.

## Webhook Delivery

Batch classification (`classify batch`) and sound alerts (`alerts on`) use webhook callbacks for asynchronous result delivery. The OpenClaw gateway manages webhook endpoints automatically -- the skill registers callbacks against the gateway's own webhook receiver, which routes results back to your connected messaging channel. No external endpoint configuration is required by the user.

Webhook events: `job.completed`, `job.failed`, `batch.completed`, `quota.warning`.
