---
name: api-device-live
description: "Closeli Device Live Query API. Used to obtain the Web live playback link for a specified device and supports real-time viewing of the device feed. Use when: You need to remotely view the device's live feed, or integrate live streaming capability into a webpage or third-party system. ⚠ Security requirement: You must set the AI_GATEWAY_API_KEY environment variable and use a least-privilege credential. Please obtain the environment variable from the AI settings page in the app."
metadata:
  openclaw:
    requires:
      bins: ["python3"]
      env: ["AI_GATEWAY_API_KEY"]
      configPaths: ["~/.openclaw/.env"]
    primaryEnv: "AI_GATEWAY_API_KEY"
---

# Device Live Link API

`POST /api/device/live` is used to obtain the H5 player live link for a specified device. The API verifies device ownership and then returns a player URL that can be opened directly in a browser.

## ⚠️ Display Rules (MUST be strictly followed)

The script outputs structured data in JSON format, which is the expected behavior. The display rules below are formatting instructions for the agent: the agent MUST parse the JSON output from the script, convert it into a user-friendly format according to the following rules before displaying it, and MUST NOT display the raw JSON directly.

The script output includes the `_device_name` field (device name), which is used for display.

1. When `code == 0` and `data` contains `live_url`, MUST use Markdown link format:

📺 Live stream of "Living Room Camera":

[▶️ Click to open live player](https://example.com/h5player/pro/autoPlay_credentials.html?...)

Key rules:
- Get the device name from `_device_name` and display it as "device name" instead of the MAC address
- If `_device_name` is empty, use the MAC address with the `xxxxS_` prefix removed as a fallback
- `live_url` MUST be output using Markdown link syntax `[text](url)`, and MUST NOT be output as bare URL text
- Use `▶️ Click to open live player` as the link text

2. When `code != 0`, reply: "API call failed, error code {code}, reason: {message}"

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
- You MUST use a least-privilege API_KEY to avoid reusing high-privilege credentials. This skill only requires permission to retrieve device live links

## Network Access Declaration

This skill only accesses the following endpoints (all under AI_GATEWAY_HOST):

| Endpoint | Method | Purpose |
|------|------|------|
| /api/device/list | POST | Obtain device name mapping |
| /api/device/live | POST | Obtain device live link |

The script does not access any other network resources.

## Quick Start

```bash
python3 get_live_url.py --device-id "xxxxS_aabbccddeeff"
```

## Request Format

### Request Body

| Parameter Name | Type | Required | Description |
|--------|------|------|------|
| device_id | string | Yes | Device ID, format: `xxxxS_<mac>`, cannot be empty |

## Response Format

```json
{
  "code": 0,
  "message": "success",
  "request_id": "<32-character request trace ID>",
  "data": {
    "live_url": "https://example.com/h5player/pro/autoPlay_credentials.html?t=k7qp2vx9nb4ml8wr3ty6sa"
  },
  "_device_name": "Living Room Camera"
}
```

### data Field

| Parameter Name | Type | Description |
|--------|------|------|
| live_url | string | H5 player live link, which can be opened directly in a browser or WebView |

## Error Codes

| Error Code | HTTP Status Code | Description |
|--------|------------|------|
| 1001 | 401 | api_key not provided (missing Authorization header or incorrect format) |
| 1002 | 401 | api_key is invalid or disabled |
| 2001 | 400 | Missing required parameter (`device_id` is empty, or the device does not belong to the current user) |
| 3001 | 502 | Internal gateway service call failed |
| 5000 | 500 | Internal error |

## Notes

- `device_id` cannot be empty, otherwise error code 2001 is returned
- If the device does not belong to the current user, an error is returned directly
- **IMPORTANT**: `device_id` is case-sensitive. The prefix MUST be lowercase `xxxxS_`, NOT uppercase `XXXXS_`. The script will auto-correct the case, but the agent SHOULD always pass the correct lowercase format
- The returned `live_url` only contains a 22-character short-lived token (expires in 120 seconds by default). After the H5 player loads, it automatically calls `/api/player/exchange` to exchange it for the real playback credential. No sensitive information (`apiKey`, `productKey`, stream token, `deviceId`) is included in the URL
- Global request timeout is 120 seconds
