---
name: api-event-query
description: "Closeli Device Event Query API. Supports natural language queries for device events and returns an AI summary and event list, including event types, time ranges, and image or video URLs. Use when: You need to directly ask about device events, such as “Was there anyone detected?”, “Did any car pass by?”, or “Where did my cat go?”, to quickly obtain event analysis results and details. ⚠ Security requirement: You must set the AI_GATEWAY_API_KEY environment variable and use a least-privilege credential. Please obtain the environment variable from the AI settings page in the app."
metadata:
  openclaw:
    requires:
      bins: ["python3"]
      env: ["AI_GATEWAY_API_KEY"]
      configPaths: ["~/.openclaw/.env"]
    primaryEnv: "AI_GATEWAY_API_KEY"
---

# Event Query API

`POST /api/event/query` is an AI-powered event query API that supports natural language queries and returns an AI summary and event list.

## ⚠️ Display Rules (MUST be strictly followed)

The script outputs structured data in JSON format, which is the expected behavior. The display rules below are formatting instructions for the agent: the agent MUST parse the JSON output from the script, convert it into a user-friendly format according to the following rules before displaying it, and MUST NOT display the raw JSON directly.

1. When `code == 0` and `data.events` is not empty:

📋 AI Summary: {summary}

| Time | Event Tags | Scene Description |
|------|----------|----------|
| {time} | {ai_events joined by commas} | {ai_scene} |

After the table, display the thumbnail link for each event one by one:

📷 {time} - {ai_events}
[View Screenshot]({pic_url})

Key rules:
- `device_id` MUST be displayed after removing the `xxxxS_` prefix
- `pic_url` MUST be output using Markdown link format `[View Screenshot](url)`
- MUST NOT use image syntax `![](url)` (some clients do not support inline image rendering)
- MUST NOT output bare URL text
- If there are more than 10 items, only display the first 10 and indicate the total count

2. When `events` is an empty array, reply: "No matching events were found within the query time range."
3. When `code != 0`, reply: "API call failed, error code {code}, reason: {message}"

## Prerequisites

The script depends on httpx. If it is not installed, the script will prompt `python3 -m pip install httpx`.

## Configuration Declaration

This skill depends on the following configuration items. The agent and user MUST confirm that they are correctly configured before running.

### Required Configuration

| Configuration Item | Delivery Method | Description |
|--------|----------|------|
| AI_GATEWAY_API_KEY | Environment variable (recommended), `~/.openclaw/.env` (fallback), command line `--api-key` | API key used for API authentication. The script automatically retrieves it according to this priority order |

### Optional Configuration

| Configuration Item | Delivery Method | Default Value | Description |
|--------|----------|--------|------|
| AI_GATEWAY_HOST | Environment variable, `~/.openclaw/.env` | `https://ai-open.icloseli.com` | Gateway address |
| AI_GATEWAY_VERIFY_SSL | Environment variable | true | Set to false to disable TLS certificate verification (development environments only) |
| AI_GATEWAY_NO_ENV_FILE | Environment variable | false | Set to true to disable fallback reading from `~/.openclaw/.env` (recommended for production environments) |

### Fallback Configuration Path

By default, the script reads the `~/.openclaw/.env` file as the fallback configuration source. This file is shared by all skills and uses the format `KEY=VALUE` (one per line). In production environments, you MUST set `AI_GATEWAY_NO_ENV_FILE=true` to disable this fallback and instead pass all configuration directly through environment variables.

## Security Notes

- The shared credential file `~/.openclaw/.env` can be read by all skills under the same user. In production environments, you MUST pass API_KEY through environment variables and MUST NOT rely on the shared credential file
- TLS certificate verification is enabled by default. You MUST NOT disable it in production environments (disabling it introduces man-in-the-middle attack risks, and attackers may intercept API_KEY and device data)
- Before use, you MUST confirm that AI_GATEWAY_HOST points to a trusted domain
- You MUST use a least-privilege API_KEY to avoid reusing high-privilege credentials. This skill only requires event query permission

## Network Access Declaration

This skill only accesses the following endpoints (all under AI_GATEWAY_HOST):

| Endpoint | Method | Purpose |
|------|------|------|
| /api/event/query | POST | Query device events in natural language |

The script does not access any other network resources.

## Quick Start

```bash
python3 query_events.py \
  --device-ids "xxxxS_aabbccddeeff" \
  --start-date "2026-03-16" \
  --end-date "2026-03-18" \
  --query "Was there anyone here today?"
```

## Request Format

### Request Body

| Parameter Name | Type | Required | Default Value | Description |
|--------|------|------|--------|------|
| device_ids | string[] | Yes | - | Device ID list, cannot be empty. Format: `xxxxS_<mac>` |
| start_date | string | Yes | - | Query start date, format `yyyy-MM-dd` |
| end_date | string | Yes | - | Query end date, format `yyyy-MM-dd` |
| query | string | Yes | - | Natural language query content |
| locale | string | No | `"zh_CN"` | Locale, affects the language of the AI summary |

## Response Format

```json
{
  "code": 0,
  "message": "success",
  "request_id": "<32-character request trace ID>",
  "data": {
    "summary": "A total of 3 person-detected events were identified today.",
    "events": [...],
    "_total_count": 15
  }
}
```

### data Field

| Parameter Name | Type | Description |
|--------|------|------|
| summary | string | AI-generated event summary text |
| events | array | Event list (the script has already trimmed it to the first 3 items) |
| _total_count | integer | Total number of events (additional field added by the script) |

### Elements of the `events` Array

| Parameter Name | Type | Description |
|--------|------|------|
| device_id | string | Device ID |
| event_id | string | Event ID |
| time | string | Formatted time string |
| ai_events | string[] | List of AI-recognized event tags |
| ai_scene | string | AI-described scene text |
| pic_url | string | Short link to the event thumbnail (may be empty) |

## Error Codes

| Error Code | HTTP Status Code | Description |
|--------|------------|------|
| 1001 | 401 | api_key not provided |
| 1002 | 401 | api_key is invalid or disabled |
| 2001 | 400 | Missing required parameter |
| 3001 | 502 | Internal gateway service call failed |
| 5000 | 500 | Internal error |

## Notes

- `device_ids` cannot be an empty array, otherwise error code 2001 is returned
- **IMPORTANT**: `device_id` is case-sensitive. The prefix MUST be lowercase `xxxxS_`, NOT uppercase `XXXXS_`. The script will auto-correct the case, but the agent SHOULD always pass the correct lowercase format
- `start_date` and `end_date` use the `yyyy-MM-dd` format
- `query` supports natural language
- Global request timeout is 120 seconds
