# SocialEpoch WhatsApp SCRM API Intelligent Assistant

SocialEpoch WhatsApp SCRM open API, tailored for enterprise overseas marketing and customer service scenarios. 

Full coverage of WhatsApp account management, bulk sending,online agent query, customer operation, user profiling, chat record retrieval and Webhook callback. 

Supports one-on-one & bulk sending for text, image, audio, video, document, business card, link card and diversion link. Built-in signature adaptation, automatic dependency management and zero-configuration deployment to empower overseas private domain and automated operation.
## Core Features
### ✅ Full Message Types
Text / Image / Audio / Document / Video / Business Card / Card Link / Diversion Link

### ✅ SCRM Capabilities
Online agent query, task creation, message status tracking, task progress query,
custom diversion routing, marketing link push, bulk customer outreach.

### ✅ Global Network
Mainland & Indonesia dual-line switching, high-availability API scheduling, stable delivery.

### ✅ Send Source Control
PC (1) / Mobile (2) / Cloud (3), default to PC (1)

---

# 📦 Step 1: Install Python Environment
This tool supports **Windows + Mac**. Please install Python 3.11 or later.

## 1. Windows Install
Download: https://www.python.org/ftp/python/3.14.4/python-3.14.4-amd64.exe
Important: ✅ Check **Add python.exe to PATH**

## 2. Mac Install
```bash
brew install python3
```

## Verify Installation
```bash
python3 --version
```

---

# 🔧 Step 2: Configure Tenant Credentials
## Default (PC Source)
```bash
python3 scrm_api.py set_config YOUR_TENANT_ID YOUR_API_KEY
```

## Custom Send Source (1=PC, 2=Mobile, 3=Cloud)
```bash
python3 scrm_api.py set_config YOUR_TENANT_ID YOUR_API_KEY 1
```

## Example
```bash
python3 scrm_api.py set_config 5333381 bab62b4722344b8de3e453f7b644b333
```

## Natural Language Setup
set config 5333381 bab62b4722344b8de3e453f7b644b333

Success message: **Config saved successfully**

---

# 📌 Usage Rules
1. All WhatsApp numbers must include country code
2. For bulk sending: separate multiple numbers with **English comma**
3. Media (image/audio/file/video) requires public URL, max 25MB
4. Support natural language instructions
5. Query task progress by task ID
6. Send source: 1=PC (default), 2=Mobile, 3=Cloud

---

# 🚀 Natural Language Commands

## Basic Query
1. Query online agent accounts
2. Query online agent by user account: query_online_agents userName

## Single Message
1. Send text: senderNumber receiverNumber message content
2. Send image: senderNumber receiverNumber imageURL caption
3. Send audio: senderNumber receiverNumber audioURL
4. Send file: senderNumber receiverNumber fileURL caption
5. Send video: senderNumber receiverNumber videoURL caption
6. Send card link: senderNumber receiverNumber title link description imageURL
7. Send diversion link: senderNumber receiverNumber title routeList

## Bulk Sending (comma-separated numbers)
1. Bulk send text: senderNumber receiver1,receiver2 message
2. Bulk send image: senderNumber receiver1,receiver2 imageURL caption
3. Bulk send audio: senderNumber receiver1,receiver2 audioURL
4. Bulk send file: senderNumber receiver1,receiver2 fileURL caption
5. Bulk send video: senderNumber receiver1,receiver2 videoURL caption
6. Bulk send card link: senderNumber receiver1,receiver2 title link description imageURL

## Task Management
1. Query task status: query task taskId

---

# Technical Advantages
- Zero-code natural language interaction
- Auto dependency installation
- Full task lifecycle tracking
- Stable single & bulk delivery
- Compatible with OpenClaw
- Local configuration persistence
- Secure & reliable execution
- Customizable send source (PC/Mobile/Cloud)

---

# Official Resources
API Documentation: https://doc.socialepoch.com/wa-scrm-open-api-doc/
```