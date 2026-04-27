---
name: mimo-voice-assistant
version: 2.0.0
description: >
  End-to-end voice solution for OpenClaw agents.
  Xiaomi MiMo-V2.5-TTS with emotion-aware speech generation,
  voice cloning, dialect support, and fine-grained instruction control.
  MiMo-V2-Omni for voice transcription. Multi-platform ready.
  Supports Token Plan billing.
metadata:
  openclaw:
    requires:
      bins: [node, ffmpeg]
      env:
        - MIMO_API_KEY
    install:
      - id: mimo-tts-proxy
        kind: local
        dir: mimo-tts-proxy
        entry: src/server.mjs
---

# MiMo Voice Assistant

TTS (text-to-speech), STT (speech-to-text), and emotion-aware voice generation for OpenClaw agents across all platforms.

## What's New in v2.0.0

- **MiMo-V2.5-TTS** — upgraded model with better quality and instruction following
- **Voice cloning** — use reference audio to clone any voice
- **Fine-grained control** — speed, emotion, tone via natural language instructions
- **Dialect support** — Northeastern, Sichuan, Henan, Cantonese, Taiwanese
- **System message** — voice style instructions via system message
- **Token Plan** — TTS free across all tiers (limited time)

## Architecture

```
User voice → OpenClaw (Telegram/Discord/WhatsApp/...)
           → STT (MiMo-V2-Omni transcription)
           → Agent processes
           → TTS (MiMo-V2.5-TTS with emotion + language + voice cloning)
           → Voice reply
```

## Before Install

> ⚠️ This skill sends text/audio to Xiaomi's MiMo API (`api.xiaomimimo.com`) for TTS/STT processing. Ensure you trust this service and have a valid `MIMO_API_KEY`. If you need higher security, consider deploying the proxy in an isolated environment (Docker/container) and rotating your API key regularly.

## Quick Start

```bash
# 1. Install dependencies
cd mimo-tts-proxy && npm install

# 2. Set API key
export MIMO_API_KEY="your-key-here"

# 3. Start proxy
node src/server.mjs
```

OpenClaw config (`openclaw.json`):
```json
{
  "messages": {
    "tts": {
      "auto": "inbound",
      "provider": "openai",
      "baseUrl": "http://127.0.0.1:3999",
      "maxTextLength": 4000
    }
  }
}
```

## Token Plan

MiMo-V2.5-TTS is now part of the Token Plan:
- **TTS is free** across all tiers (limited time)
- Token-based billing with transparent quotas
- 20% off-peak discount
- 30% monthly auto-renewal discount

Get your API key at [platform.xiaomimimo.com](https://platform.xiaomimimo.com)

## Emotion Detection

See `references/emotion-detection.md`

## Multi-Platform

See `references/platforms.md`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/v1/models` | GET | Model list |
| `/v1/audio/speech` | POST | Text to speech |

**Request format:**
```json
{"model": "tts-1", "input": "Hello", "voice": "mimo_default", "response_format": "mp3"}
```

**With voice style instruction:**
```json
{"model": "tts-1", "input": "Hello", "voice": "mimo_default", "response_format": "mp3", "style": "用温柔的语气说"}
```

**With voice cloning:**
```json
{"model": "tts-1", "input": "Hello", "voice": "mimo_default", "response_format": "mp3", "reference_audio": "base64_audio_data"}
```

**Formats:** `wav` (default), `mp3` (needs ffmpeg), `opus` (needs ffmpeg)

## Multi-Language Support

**CRITICAL: TTS output must match the user's language automatically.**

### Language Detection

Detect the user's language from their message and respond in the **same language** for both text and voice.

| User sends | Agent text reply | TTS voice output |
|-----------|-----------------|------------------|
| "你好，帮我查一下天气" | 中文回复 | 中文语音 |
| "What's the weather?" | English reply | English voice |
| "おはようございます" | 日本語返答 | 日本語音声 |
| "Bonjour, comment ça va ?" | Réponse en français | Voix française |
| "안녕하세요" | 한국어 답변 | 한국어 음성 |

### How It Works

1. **Agent detects language** from the user's message (first message or latest message language)
2. **Agent replies in that language** (text)
3. **TTS speaks that language** — MiMo-V2-TTS supports Chinese, English, Japanese, Korean, and more
4. **No explicit instruction needed** — this is automatic behavior

### When to Override

Only switch language if the user explicitly asks:
- "请用英语回答" → Switch to English
- "Speak in Japanese" → Switch to Japanese
- Otherwise, always match the user's language

### TTS Language Compatibility

MiMo-V2.5-TTS supports natural speech in:
- ✅ Chinese (Mandarin)
- ✅ English (US/UK)
- ✅ Japanese
- ✅ Korean
- ✅ Dialects: Northeastern, Sichuan, Henan, Cantonese, Taiwanese
- ✅ Other languages (quality varies)

### Implementation

In your response, you can use `[lang:xx]` hints for the TTS proxy (optional):

```
[lang:zh]你好，这是你的语音回复。
[lang:en]Hello, here is your voice reply.
[lang:ja]こんにちは、音声返信です。
```

Or simply reply normally — the TTS proxy will automatically handle the language based on the text content.

## Security & Data Flow

- **API key**: passed via env var (`MIMO_API_KEY`) or `Authorization` Bearer header, never hardcoded
- **Network**: proxy only connects to `api.xiaomimimo.com` (Xiaomi official API) — text and base64 audio are sent there for TTS/STT processing
- **Local binding**: proxy binds to `127.0.0.1:3999` (localhost only, not externally exposed)
- **Temp files**: auto-cleaned after each request
- **User responsibility**: if using systemd/launchd for persistence, store API keys securely (env file or secret manager, not inline in service files)
