---
name: happyhorse-video-creator
description: 使用阿里云百炼 HappyHorse 模型生成视频，支持图生视频（首帧/尾帧控制）和文生视频。
description_zh: 使用阿里云百炼 HappyHorse 模型生成视频，支持图生视频（首帧/尾帧控制）和文生视频。
version: 1.0.0
author: 卡妹
license: MIT
metadata:
  openclaw:
    homepage: https://github.com/Cindypapa/happyhorse-video-creator
    requires:
      bins:
        - python3
      packages:
        - requests>=2.28
---

# happyhorse-video-creator - HappyHorse 视频创作助手 v1.0

## 📋 技能描述

使用阿里云百炼（DashScope）HappyHorse 视频生成模型，帮助用户创作专业视频。支持**图生视频**（首帧/尾帧控制）和**文生视频**两种模式。

**平台**: 阿里云百炼（DashScope）  
**API 端点**: `https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis`

## 🎯 触发条件

用户提到以下关键词时触发：
- "HappyHorse 生成视频"
- "用 HappyHorse 做视频"
- "阿里百炼视频"
- "happyhorse 视频"

## 🔄 工作流程

### 阶段 0：首次配置

```
您好！我是 HappyHorse 视频创作助手 🎬

需要配置阿里百炼 API Key：

1️⃣ 阿里百炼 API Key
   - 获取地址：https://bailian.console.aliyun.com/
   - 默认已配置（测试可用）
```

### 阶段 1：需求收集

```
请告诉我：

**1. 视频主题**：想表达什么内容？

**2. 视频风格**：科技感？温馨？专业？电影感？

**3. 图片资料**：

🖼️ **首帧图片**（图生视频必须）：
   - 控制视频起始画面

🖼️ **尾帧图片**（可选）：
   - 控制视频结束画面
   - 首尾帧结合可精确控制过渡效果

📝 **文字描述**：
   - 具体需求说明
```

### 阶段 2：提示词确认

1. 生成视频提示词
2. 发送提示词给用户确认
3. **用户确认后**才生成

### 阶段 3：视频生成

1. 调用阿里百炼 API
2. 等待完成（约 1-3 分钟）
3. 发送视频给用户确认

## 🛠️ API 调用

### 阿里百炼 HappyHorse API

**API Key**: `sk-d05aba5a2dae4453b97ed07fdb983e5a`

#### 图生视频（首帧模式）✅ 已验证

```python
import requests

url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-d05aba5a2dae4453b97ed07fdb983e5a",
    "X-DashScope-Async": "enable"  # ⚠️ 必须设置
}

payload = {
    "model": "happyhorse-1.0-i2v",
    "input": {
        "prompt": "镜头缓缓推进，阳光洒在咖啡杯上",
        "media": [
            {"type": "first_frame", "url": "http://example.com/coffee.jpg"}
        ]
    },
    "parameters": {
        "resolution": "720P",    # 480P/720P/1080P
        "ratio": "16:9",          # 16:9/9:16/1:1
        "duration": 15            # 2-15 秒
    }
}

response = requests.post(url, headers=headers, json=payload, timeout=30)
task_id = response.json()["output"]["task_id"]
```

#### 图生视频（首尾帧模式）✅ 支持

```python
payload = {
    "model": "happyhorse-1.0-i2v",
    "input": {
        "prompt": "镜头从白天缓缓过渡到夜晚",
        "media": [
            {"type": "first_frame", "url": "http://example.com/day.jpg"},
            {"type": "last_frame", "url": "http://example.com/night.jpg"}
        ]
    },
    "parameters": {
        "resolution": "720P",
        "ratio": "16:9",
        "duration": 15
    }
}
```

#### 文生视频 ✅ 已验证

```python
payload = {
    "model": "happyhorse-1.0-t2v",
    "input": {
        "prompt": "一只可爱的小猫在草地上玩耍，阳光明媚"
    },
    "parameters": {
        "resolution": "720P",
        "ratio": "16:9",
        "duration": 15
    }
}
```

#### 查询任务状态

```python
status_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
headers = {"Authorization": "Bearer sk-d05aba5a2dae4453b97ed07fdb983e5a"}
response = requests.get(status_url, headers=headers, timeout=30)
result = response.json()

# task_status: PENDING → RUNNING → SUCCEEDED / FAILED
if result["output"]["task_status"] == "SUCCEEDED":
    video_url = result["output"]["video_url"]
```

### 关键参数说明

| 参数 | 默认 | 说明 |
|------|------|------|
| `model` | happyhorse-1.0-i2v | 模型：i2v（图生视频）或 t2v（文生视频） |
| `input.prompt` | 必填 | 视频描述提示词 |
| `input.media` | 可选 | 媒体数组（图生视频必填） |
| `media[].type` | first_frame | first_frame / last_frame / driving_audio / first_clip |
| `parameters.resolution` | 720P | 480P / 720P / 1080P |
| `parameters.ratio` | 16:9 | 16:9 / 9:16 / 1:1 |
| `parameters.duration` | 15 | 2-15 秒 |

### ⚠️ 关键注意事项

1. **必须使用异步模式**：`X-DashScope-Async: enable`
2. **图生视频用 `input.media` 数组**，type 必须是 `first_frame` / `last_frame` / `driving_audio` / `first_clip`
3. **`type: "image"` 会报错**：必须用 `first_frame`
4. **图片必须是 HTTP/HTTPS URL**，不支持本地路径
5. **生成时间**：约 1-3 分钟
6. **文生视频用 `happyhorse-1.0-t2v`**，不需要 `input.media`

## 📁 文件管理

### 项目目录
```
/root/.openclaw/workspace/happyhorse-video-projects/
└── video_20260428_140000/
    ├── project.json
    ├── references/
    ├── videos/
    └── final_video.mp4
```

## 🚀 Python 模块调用

```python
from happyhorse_video_creator import HappyHorseCreator

creator = HappyHorseCreator()

# 图生视频
success, video_path = creator.generate_video(
    prompt="镜头缓缓推进，阳光洒在咖啡杯上",
    image_url="http://example.com/coffee.jpg",
    duration=15,
    resolution="720P"
)

# 首尾帧视频
success, video_path = creator.generate_video(
    prompt="从白天过渡到夜晚",
    image_url="http://example.com/day.jpg",
    end_frame_url="http://example.com/night.jpg",
    duration=15
)

# 文生视频
success, video_path = creator.generate_video(
    prompt="一只小猫在草地上玩耍",
    duration=15
)
```

## ✅ 测试记录

### 图生视频测试 (2026-04-28 14:46)
- **模型**: happyhorse-1.0-i2v
- **输入**: http://43.167.197.36/img2.jpg + "test"
- **结果**: ✅ 成功 (2.9 MB, 720P, 5 秒)
- **耗时**: 约 83 秒

### 文生视频测试 (2026-04-28 14:48)
- **模型**: happyhorse-1.0-t2v
- **输入**: "一只小猫在草地上玩耍"
- **结果**: ✅ 成功 (3.4 MB, 720P, 5 秒, 16:9)
- **耗时**: 约 83 秒

---

**版本**: v1.0  
**创建时间**: 2026-04-28  
**作者**: 卡妹 🌸  
**平台**: 阿里云百炼（DashScope）
