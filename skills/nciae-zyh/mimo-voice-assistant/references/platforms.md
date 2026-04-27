# 🌐 Multi-Platform TTS 支持指南

## 概述

OpenClaw 支持多种消息平台，每个平台的语音消息格式和发送方式略有不同。
本指南说明如何在各平台上使用 MiMo TTS。

## v2.5 新功能

- **Token Plan**：TTS 全套餐免费（限时）
- **音色克隆**：使用参考音频克隆任意音色
- **方言支持**：东北话/四川话/河南话/粤语/台湾腔
- **细粒度控制**：语速、情绪、音调自然语言指令控制

## 平台兼容性矩阵

| 平台 | TTS 输出 | 语音消息 | 配置方式 | 备注 |
|------|----------|----------|----------|------|
| Telegram | ✅ | ✅ 原生语音 | `messages.tts` | 支持波形显示 |
| WhatsApp | ✅ | ✅ | `messages.tts` | 通过 WhatsApp Web API |
| Discord | ✅ | ✅ 文件发送 | `messages.tts` | 作为音频文件附件 |
| iMessage | ✅ | ✅ | `messages.tts` | macOS 原生支持 |
| Slack | ✅ | ✅ 文件上传 | `messages.tts` | 作为音频文件 |
| Line | ✅ | ⚠️ | `messages.tts` | 有限支持 |
| Google Chat | ⚠️ | ❌ | - | 需要额外适配 |

## OpenClaw TTS 配置

### 全局配置（所有平台）

```jsonc
// openclaw.json
{
  "messages": {
    "tts": {
      "auto": "inbound",      // 收到语音时自动回复语音
      "provider": "openai",   // 使用 OpenAI 兼容 API
      "baseUrl": "http://127.0.0.1:3999",  // MiMo TTS Proxy
      "maxTextLength": 4000   // 最大文本长度
    }
  }
}
```

### TTS 自动模式

| `auto` 值 | 行为 |
|-----------|------|
| `"inbound"` | 仅当用户发语音消息时，回复也用语音 |
| `"always"` | 所有回复都用语音 |
| `"off"` | 关闭自动 TTS（手动用 `[[tts:...]]` 标签） |

### 按 Agent 配置

如果不同 agent 需要不同的 TTS 行为，可以在 agent 级别覆盖：

```jsonc
{
  "agents": {
    "list": [
      {
        "id": "friend",
        "name": "友好助手",
        "messages": {
          "tts": {
            "auto": "always",
            "maxTextLength": 2000
          }
        }
      },
      {
        "id": "coder",
        "name": "代码专家",
        "messages": {
          "tts": { "auto": "off" }
        }
      }
    ]
  }
}
```

## 各平台详细配置

### Telegram

Telegram 原生支持语音消息（Voice Messages）。

```jsonc
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "your-token",
      "streaming": "partial"
    }
  },
  "messages": {
    "tts": {
      "auto": "inbound",
      "provider": "openai",
      "baseUrl": "http://127.0.0.1:3999"
    }
  }
}
```

**效果**：
- 用户发语音 → Agent 自动语音回复
- 语音带波形预览
- 支持速度调节

### WhatsApp

WhatsApp 通过 OpenClaw 的 WhatsApp 适配器支持语音。

```jsonc
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "dmPolicy": "allowlist"
    }
  }
}
```

### Discord

Discord 以文件附件形式发送语音。

```jsonc
{
  "channels": {
    "discord": {
      "enabled": true,
      "token": "your-token"
    }
  }
}
```

### iMessage

macOS 原生 iMessage 支持语音附件。

```jsonc
{
  "channels": {
    "imessage": {
      "enabled": true
    }
  }
}
```

### Slack

Slack 通过 Files API 上传音频文件。

```jsonc
{
  "channels": {
    "slack": {
      "enabled": true,
      "botToken": "your-token"
    }
  }
}
```

## 手动控制 TTS

在回复中使用 `[[tts:text]]` 标签，可以精确控制 TTS 输出：

```
这是一段文字回复。
[[tts:下面这段话我想用语音说]]这是一段特别用语音表达的内容。[[/tts:text]]
```

### 混合模式

```
回复可以同时包含文字和语音：
- 文字部分：详细的代码和链接
- 语音部分：简短的总结或问候
[[tts:代码改好了，主要变更在 auth.js 这个文件。]][[/tts:text]]
```

## TTS 输出格式

MiMo TTS Proxy 支持以下音频格式：

| 格式 | MIME 类型 | 用途 | 需要 ffmpeg |
|------|-----------|------|-------------|
| WAV | `audio/wav` | 默认，无损 | ❌ |
| MP3 | `audio/mpeg` | 通用兼容 | ✅ |
| Opus | `audio/ogg` | Telegram 首选 | ✅ |

## 代理启动脚本

推荐使用 launchd (macOS) 或 systemd (Linux) 管理 TTS Proxy 进程：

### macOS (launchd)

```xml
<!-- ~/Library/LaunchAgents/com.openclaw.mimo-tts-proxy.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.openclaw.mimo-tts-proxy</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/node</string>
    <string>/path/to/mimo-tts-proxy/src/server.mjs</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>MIMO_API_KEY</key>
    <string>YOUR_API_KEY_HERE</string>
    <key>MIMO_TTS_PORT</key>
    <string>3999</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.openclaw.mimo-tts-proxy.plist
```

### Linux (systemd)

```ini
# /etc/systemd/system/mimo-tts-proxy.service
[Unit]
Description=MiMo TTS Proxy
After=network.target

[Service]
Type=simple
User=openclaw
Environment=MIMO_API_KEY=YOUR_API_KEY_HERE
Environment=MIMO_TTS_PORT=3999
ExecStart=/usr/local/bin/node /opt/mimo-tts-proxy/src/server.mjs
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable mimo-tts-proxy
sudo systemctl start mimo-tts-proxy
```

## 故障排除

| 问题 | 排查步骤 |
|------|----------|
| 无语音输出 | `curl http://127.0.0.1:3999/health` 检查 proxy |
| 音频格式错误 | 确认 ffmpeg 已安装: `ffmpeg -version` |
| API Key 错误 | 检查环境变量: `echo $MIMO_API_KEY` |
| 平台不支持语音 | 参考上方兼容性矩阵 |
| 语音太长截断 | 调整 `maxTextLength` |

## 注意事项

- TTS Proxy 仅监听 `127.0.0.1`，不会被外部访问
- 临时音频文件使用后立即清理
- 不同平台可能有不同的音频大小限制
- 语音消息的字数限制取决于平台，通常 4000 字以内
- 情绪标记不影响文字显示，仅影响语音合成参数
