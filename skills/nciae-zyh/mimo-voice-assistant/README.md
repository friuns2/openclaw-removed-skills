# 🎤 MiMo Voice Assistant

端到端语音助手 Skill for [OpenClaw](https://github.com/openclaw/openclaw) agents。

集成 [Xiaomi MiMo-V2.5-TTS](https://mimo.xiaomi.com/mimo-v2-tts) 和 MiMo-V2-Omni，提供情绪感知 TTS、音色克隆、方言支持和 STT 能力，支持多平台。

## ✨ 功能

- **TTS (文字→语音)** — OpenAI 兼容格式，MiMo-V2.5-TTS
- **STT (语音→文字)** — MiMo-V2-Omni 语音转录
- **🎭 情绪感知** — 8 种情绪自动判断（开心/平静/难过/生气/激动/紧张/思考/温柔）
- **🎤 音色克隆** — 使用参考音频克隆任意音色
- **🗣️ 方言支持** — 东北话/四川话/河南话/粤语/台湾腔
- **🎯 细粒度控制** — 语速、情绪、音调自然语言指令控制
- **🌐 多平台** — Telegram / Discord / WhatsApp / iMessage / Slack / Line
- **💰 Token Plan** — TTS 全套餐免费（限时）

## 📦 安装

```bash
# 通过 ClawHub 安装
clawhub install mimo-voice-assistant

# 或手动克隆
git clone https://github.com/Nciae-Zyh/mimo-voice-assistant.git
cd mimo-voice-assistant/mimo-tts-proxy
npm install
```

## 🚀 快速开始

### 1. 配置环境变量

```bash
export MIMO_API_KEY="your-api-key-here"
export MIMO_TTS_PORT=3999
```

### 2. 启动 TTS Proxy

```bash
cd mimo-tts-proxy
node src/server.mjs
```

### 3. 配置 OpenClaw

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

## 🎤 音色克隆

使用参考音频克隆任意音色：

```json
{
  "model": "tts-1",
  "input": "你好，这是克隆的语音",
  "voice": "mimo_default",
  "reference_audio": "base64编码的音频数据"
}
```

## 🗣️ 方言支持

MiMo-V2.5-TTS 支持多种方言：

| 方言 | 标识 | 示例 |
|------|------|------|
| 东北话 | `dongbei` | "哎呀妈呀，这也太好了吧！" |
| 四川话 | `sichuan` | "巴适得很！" |
| 河南话 | `henan` | "中！" |
| 粤语 | `cantonese` | "你好犀利！" |
| 台湾腔 | `taiwanese` | "超好用的！" |

## 🎯 细粒度控制

通过自然语言指令控制语音风格：

```json
{
  "model": "tts-1",
  "input": "你好",
  "voice": "mimo_default",
  "style": "用温柔的语气，语速稍慢"
}
```

## 📁 项目结构

```
mimo-voice-assistant/
├── SKILL.md                          # OpenClaw skill 主文档
├── _meta.json                        # ClawHub 元数据
├── README.md                         # 本文件
├── mimo-tts-proxy/
│   ├── package.json
│   └── src/
│       ├── server.mjs                # TTS Proxy (OpenAI 兼容)
│       └── stt.mjs                   # 语音转录工具
├── references/
│   ├── emotion-detection.md          # 情绪检测详细指南
│   └── platforms.md                  # 多平台适配指南
└── scripts/
    └── detect-emotion.mjs            # 情绪检测工具
```

## 📄 License

MIT
