---
name: ai-image-generator
description: |
  AI 图片与视频异步生成技能，调用 AI Artist API 根据文本提示词生成图片或视频，自动轮询直到任务完成。

  ⚠️ 使用前必须设置环境变量 AI_ARTIST_TOKEN 为你自己的 API Key！
  获取 API Key：访问 https://ai.deepsop.com/ 注册登录后创建。

  支持图片模型：DeepSop系列图片模型（S4.5、S5.0L、N1、N2系列、W2.7系列等，共11个模型）。
  支持视频模型：DeepSop系列视频模型（S1.5Pro、Sora2系列、Veo3.1系列、Wan2.6/Wan2.7系列、Kling V3 Omni等，共15个模型）。

  触发场景：
  - 用户要求生成图片，如"生成一匹狼"、"画一只猫"、"风景画"、"帮我画"等。
  - 用户要求生成视频，如"生成视频"、"文生视频"、"图生视频"、"生成一段...的视频"等。
  - 用户指定具体模型（详见下方模型列表）。
  - 用户上传参考图/参考视频时，自动先调用文件上传 API 转换为可访问 URL。
---

# AI Image Generator

异步生成 AI 图片与视频的技能。

## ⚠️ 首次使用必读

### 1. 获取 API Key

访问 [https://ai.deepsop.com/](https://ai.deepsop.com/) 注册并登录，然后创建你的 API Key。

### 2. 设置环境变量

**在使用前，你必须先设置自己的 API Key：**

```bash
# Linux/macOS/Git Bash (Windows)
export AI_ARTIST_TOKEN="sk-your_api_key_here"

# Windows PowerShell
$env:AI_ARTIST_TOKEN="sk-your_api_key_here"
```

### 3. 验证配置

**验证配置是否正确：**

```bash
python3 scripts/test_config.py
```

详细配置说明请查看下方"环境配置"章节。

## 快速开始

```bash
# 图片生成（默认 DeepSop·3.1Nano2-Evo）
python3 scripts/generate_image.py "一只可爱的猫"

# 视频生成（默认 DeepSop·V3.1FB）
python3 scripts/generate_video.py "海边日落风景"
```

## 参考图/视频上传流程

当用户提供本地文件作为参考图或参考视频时，需要先调用文件上传 API 转换为可访问的 URL：

### 文件上传 API

```bash
curl --location --request POST 'https://ai.deepsop.com/prod-api/system/fileUpload/upload' \
--header 'x-api-key: sk-your_api_key_here' \
--form 'file=@"C:\\Users\\admin\\Downloads\\image.png"'
```

**返回结果：**
```json
{
  "msg": "操作成功",
  "fileName": "image.png",
  "code": 200,
  "url": "https://kocgo-ai-sales-test.oss-cn-hangzhou.aliyuncs.com/material/100/xxx.png"
}
```

### 使用上传后的 URL

获取到 `url` 后，可作为 `firstImageUrl`、`lastImageUrl`、`imageUrlList`、`videoUrlList` 或 `elementList `等参数传入生成接口。

## 在对话中直接返回图片/视频

### 方式 1: Markdown 语法（推荐）

生成图片后，直接在回复中使用 Markdown 语法：

```markdown
![图片描述](图片URL)
![视频描述](视频URL)
```

**平台支持情况：**
- ✅ WebChat、Discord、Telegram：完全支持
- ✅ 飞书：支持（需公开 URL）
- ❌ WhatsApp：不支持

### 方式 2: 下载后发送（需要 message 工具）

使用 `--download` 参数下载媒体文件，然后通过 message 工具发送：

```bash
python3 scripts/generate_image.py "风景画" --download
python3 scripts/generate_video.py "海边" --download
```

比如图片生成接着在代码中读取图片并发送：

```python
from scripts.generate_image import generate_image
import base64

result = generate_image(prompt="风景画", download=True)

if result and result["status"] == "SUCCESS":
    # 方式 A: 使用 data URI
    image_uri = result["data_uri"]  # data:image/png;base64,...
    
    # 方式 B: 读取本地文件
    with open(result["local_path"], "rb") as f:
        image_data = f.read()
        base64_data = base64.b64encode(image_data).decode()
```

## 参数说明

### 通用参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `prompt` | 必填 | 生成提示词（图片或视频描述）|
| `--model` | 图片: `DeepSop·3.1Nano2-Evo` / 视频: `DeepSop·V3.1FB` | 生成模型（详见下方模型列表） |
| `--interval` | `5` | 轮询间隔(秒) |
| `--download` | - | 下载媒体文件到本地 |
| `--output-dir` | `workspace/images`（图片） / `workspace/videos`（视频） | 文件保存目录 |

### 图片专属参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--quality` | 按模型自动匹配	 | 图片质量：`1K`、`2K`、`3K`、`4K`（具体支持见下方模型能力表） |
| `--size` | 按模型自动匹配 | 图片比例：`1:1`、`3:4`、`4:3`、`16:9`、`9:16`、`2:3`、`3:2`、`4:5`、`5:4`、`1:4`、`4:1`、`1:8`、`8:1`、`21:9`、`auto`（具体支持见下方模型能力表） |
| `--download` | - | 下载图片到本地 |
| `--output-dir` | `workspace/images` | 图片保存目录 |
| `--markdown-output` | - | 以 Markdown 格式输出图片链接 |
| `--reference-image` | - | 参考图本地路径，自动上传后作为 image-to-image 参考 |
| `--web-search` | - | 开启联网搜索（仅 S5.0L 和 Nano2-Evo 支持） |

### 视频专属参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--generation-type` | `TEXT` | 生成类型：`TEXT`（文生视频）、`FIRST&LAST`（首尾帧生视频）、`REFERENCE`（参考图生视频）、`CONTINUATION`（视频续写）、`EDIT`（视频编辑）、`FEATURE`（参考视频生视频） |
| `--ratio` | 按模型自动匹配 | 画面比例（具体支持见下方模型能力表） |
| `--resolution` | 按模型自动匹配 | 视频分辨率：`480p`、`720p`、`1080p`、`2K`、`4K`（具体支持见下方模型能力表） |
| `--duration` | 按模型自动匹配	 | 视频时长（秒），不同模型支持范围不同 |
| `--mode` | `std` | 生成模式：std（标准模式）、pro（专家模式/高品质）（仅 Kling V3 Omni 支持） |
| `--first-image-url` | - | 首帧参考图 URL |
| `--last-image-url` | - | 尾帧参考图 URL |
| `--first-image` | - | 首帧参考图本地路径，自动上传后转换为 URL |
| `--last-image` | - | 尾帧参考图本地路径，自动上传后转换为 URL |
| `--first-clip-url` | - | 续写/编辑参考视频 URL |
| `--first-clip` | - | 续写/编辑参考视频本地路径，自动上传后转换为 URL |
| `--image-url-list` | - | 参考图片 URL 列表（用于参考图生视频） |
| `--video-url-list` | - | 参考视频 URL 列表（用于 R2V 模型） |
| `--element-list` | - | 参考主体 URL 列表（用于 Kling V3 Omni） |
| `--generate-audio` | - | 开启音频生成（按模型能力生效） |
| `--no-audio` | - | 关闭音频生成（按模型能力生效） |
| `--keep-original-sound` | - | 保留视频原声（仅 Kling V3 Omni） |
| `--prompt-extend` | -	| 开启智能提示词改写（Wan系列支持）
| `--enhance-prompt` | - | 开启提示词翻译成英文（Veo3.1系列支持）
| `--negative-prompt` | - | 负向提示词（Veo3.1 Fast/Pro、Wan系列支持）
| `--shot-type` | `single` | 镜头模式：`single`（单镜头）、`multi`（智能分镜）、`customize`（自定义分镜）
| `--duration-switch` | - | 时长模式开关（仅 S1.5Pro）
| `--person-generation` | `allow_adult` | 是否允许生成人物：`allow_adult`、`dont_allow`（仅 Veo3.1 Fast/Pro）
| `--resize-mode` | `pad` | 图像缩放模式：`pad`（调整图片）、`crop`（裁剪图片）（仅 Veo3.1 Fast/Pro）
| `--multi-shot` | - | 是否多镜头（仅 Kling V3 Omni）
| `--n` | `1` | 生成视频数量（仅 Veo3.1 Fast/Pro）
| `--audio-url` | -	| 参考音频 URL（Wan系列 T2V/I2V 支持）

## 支持的模型

### 图片模型

| 模型 | methodType | 支持质量 | 支持比例 | 联网搜索 | 特点 |
|------|-----------|---------|------|
| `S4.5` | `0` | 2K, 4K | 除 auto 外所有比例 | ❌ | 电影级画质4K，角色一致性
| `N1` | `1` | 1K | 除 21:9、4:5、5:4、1:4、4:1、1:8、8:1 外 | ❌ | 支持多模态输入，精细参数调节
| `N2` | `2` | 1K, 2K, 4K | 所有比例 | ❌ | 卓越的文字渲染和角色一致性
| `N2-147` | `3` | 1K, 2K, 4K | 除 auto、1:4、4:1、1:8、8:1 外 | ❌ | 147版本，支持多模态输入
| `S5.0L` | `4` | 2K, 3K | 除 auto 外所有比例 | ✅ | 默认模型，生成快、风格全、易用
| `N2-Pro` | `5` | 1K, 2K, 4K | 除 auto、1:4、4:1、1:8、8:1 外 | ✅ | Pro版本，画质细节更优
| `W2.7` | `6` | 1K, 2K | 除 auto、21:9 外 | ❌ | 画质清晰，细节丰富
| `W2.7Pro` | `7` | 1K, 2K | 除 auto、21:9 外 | ❌ | 精准控图与风格迁移
| `N2-Evo` | `8` | 1K, 2K, 4K | 所有比例 | ✅ | Evo版本，卓越的文字渲染
| `N2-Beta` | `9` | 1K, 2K, 4K | 所有比例 | ❌ | Beta测试版
| `Auto` | `auto` | 2K	除 auto、1:4、4:1、1:8、8:1、21:9 外 | ❌ | 自动选择最佳模型

### 视频模型

| 模型名称 | methodType | 支持生成类型 | 支持比例 | 支持分辨率 | 时长范围 | 特殊能力 |
|---------|-----------|------------|---------|-----------|---------|---------|
| `S1.5Pro` | `2` | TEXT, FIRST&LAST | 1:1, 3:4, 4:3, 16:9, 9:16, 21:9, adaptive | 480p, 720p, 1080p | 4-12s | 影视级叙事，支持音频生成、时长模式 |
| `Sora2 Beta` | `1` | TEXT, FIRST&LAST | 16:9, 9:16 | 720p | 10-15s | Beta版本 |
| `Sora2` | `11` | TEXT, FIRST&LAST | 16:9, 9:16 | 720p | 4-12s | 基础版本 |
| `Sora2 Pro` | `12` | TEXT, FIRST&LAST | 16:9, 9:16, 7:4, 4:7 | 720p, 2K | 4-12s | Pro版本 |
| `V3.1FB` | `3` | TEXT, FIRST&LAST, REFERENCE | 16:9, 9:16, adaptive | 720p, 1080p, 4K | 8s | 快速轻量版，支持提示词翻译 |
| `V3.1PB` | `4` | TEXT, FIRST&LAST, REFERENCE | 16:9, 9:16, adaptive | 720p, 1080p, 4K | 8s | 专业轻量版，多图参考 |
| `V3.1Fast` | `5` | TEXT, FIRST&LAST | 16:9, 9:16, adaptive | 720p, 1080p, 4K | 4s, 8s | 快速版，支持音画同步 |
| `V3.1Pro` | `6` | TEXT, FIRST&LAST | 16:9, 9:16, adaptive | 720p, 1080p, 4K | 4s, 8s | 专业版，4K超清，商业级 |
| `W2.6t` | `7` | TEXT | 1:1, 3:4, 4:3, 16:9, 9:16 | 720p, 1080p | 3-15s | 文生视频，支持音频、提示词改写 |
| `W2.6i` | `8` | FIRST&LAST | 固定 | 720p, 1080p | 3-15s | 首帧图生视频，比例由图片决定 |
| `W2.6r` | `9` | REFERENCE | 1:1, 3:4, 4:3, 16:9, 9:16 | 720p, 1080p | 3-10s | 参考视频生视频 |
| `W2.7i` | `14` | FIRST&LAST, CONTINUATION | 固定 | 720p, 1080p | 3-15s | 首帧图生视频，支持续写 |
| `W2.7t` | `15` | TEXT | 1:1, 3:4, 4:3, 16:9, 9:16 | 720p, 1080p | 3-15s | 文生视频，支持音频、提示词改写 |
| `W2.7r` | `16` | REFERENCE | 1:1, 3:4, 4:3, 16:9, 9:16 | 720p, 1080p | 3-15s（无视频引用）<br>3-10s（有视频引用） | 参考视频生视频 |
| `Kling V3 Omni` | `10` | TEXT, FIRST&LAST, REFERENCE, EDIT, FEATURE | 1:1, 16:9, 9:16 | 720p, 1080p | 3-15s | 全能模型，支持主体参考、多镜头 |
| `Auto` | `auto` | FIRST&LAST | 16:9, 9:16 | 720p | 4-12s | 自动选择最佳模型 |


**VEO3.1 系列（V3.1FB、V3.1PB、V3.1Fast、V3.1Pro）共同说明：**
| 模型名称 | 支持特性 |
|---------|-----------|
| `V3.1FB` / `V3.1PB` | 支持 `--enhance-prompt`（提示词翻译成英文） |
| `V3.1Fast` / `V3.1Pro` | 支持 `--n`、`--person-generation`、`--resize-mode`、`--negative-prompt`、`--enhance-prompt`、`--generate-audio` |

**WAN2.6 系列共同说明：**
| 模型名称 | 支持特性 |
|---------|-----------|
| `W2.6t` / `W2.7t` | 文生视频，支持 `--audio-url`（自定义音频） |
| `W2.6i` / `W2.7i` | 首帧图生视频，不支持 `--ratio` 参数（比例由首帧图决定），W2.7i 支持 `--first-clip-url`（续写） |
| `W2.6r` / `W2.7r` | 参考视频生视频，支持 `--video-url-list`（参考视频列表），W2.7r 时长根据是否有视频引用动态变化 |
| 全系列 | 支持 `--prompt-extend`（智能提示词改写）、`--negative-prompt`（负向提示词） |

**Kling V3 Omni 特有能力：**
| 能力	| 说明 |
|---------|-----------|
| `--element-list` | 参考主体选择 |
| `--keep-original-sound` | 保留视频原声 |
| `--mode` | 生成模式（std/pro） |
| `--multi-shot` | 是否多镜头 |
| `--shot-type` | 镜头模式（single/multi/customize） |
| `--generate-audio` | 生成声音 |
| 不支持 `--resolution` | 分辨率固定 |

## 参数联动规则（自动处理）

**图片质量按模型自动过滤**
| model | 支持质量 |
|-------|---------|
| Auto | 2K |
| S4.5 (`0`) | 2K, 4K |
| N1 (`1`) | 1K |
| N2 (`2`)、N2-147 (`3`)、N2-Pro (`5`)、N2-Evo (`8`)、N2-Beta (`9`) | 1K, 2K, 4K |
| S5.0L (`4`) | 2K, 3K |
| W2.7 (`6`)、W2.7Pro (`7`) | 1K, 2K |

**图片比例按模型自动过滤**
| model | 排除比例 |
|-------|---------|
| Auto | `auto`、`1:4`、`4:1`、`1:8`、`8:1`、`21:9` |
| S4.5 (`0`)、S5.0L (`4`) | `auto` |
| N1 (`1`) | `21:9`、`4:5`、`5:4`、`1:4`、`4:1`、`1:8`、`8:1` |
| N2-147 (`3`)、N2-Pro (`5`) | `auto`、`1:4`、`4:1`、`1:8`、`8:1` |
| W2.7 (`6`)、W2.7Pro (`7`) | `auto`、`21:9` |
| N2 (`2`)、N2-Evo (`8`)、N2-Beta (`9`) | 无（支持所有比例） |

**视频生成类型按模型自动过滤**
| model | 支持生成类型 |
|-------|------------|
| Auto | FIRST&LAST |
| Sora2 Beta (`1`)、S1.5Pro (`2`)、V3.1PB (`4`)、V3.1Fast (`5`)、V3.1Pro (`6`)、Sora2 (`11`)、Sora2 Pro (`12`) | TEXT, FIRST&LAST |
| W2.6t (`7`)、W2.7t (`15`) | TEXT |
| W2.6i (`8`) | FIRST&LAST |
| W2.7i (`14`) | FIRST&LAST, CONTINUATION |
| W2.6r (`9`)、W2.7r (`16`) | REFERENCE |
| Kling V3 Omni (`10`) | TEXT, FIRST&LAST, REFERENCE, EDIT, FEATURE |
| V3.1FB (`3`) | TEXT, FIRST&LAST, REFERENCE |

**视频分辨率按模型自动过滤**
| model | 支持分辨率 |
|-------|-----------|
| Auto、Sora2 Beta (`1`)、Sora2 (`11`) | 720p |
| S1.5Pro (`2`) | 480p, 720p, 1080p |
| V3.1FB (`3`)、V3.1PB (`4`)、V3.1Fast (`5`)、V3.1Pro (`6`) | 720p, 1080p, 4K |
| W2.6t (`7`)、W2.6i (`8`)、W2.6r (`9`)、Kling V3 Omni (`10`)、W2.7i (`14`)、W2.7t (`15`)、W2.7r (`16`) | 720p, 1080p |
| Sora2 Pro (`12`) | 720p, 2K |

**视频比例按模型自动过滤**
| model | 支持比例 |
|-------|---------|
| Auto、Sora2 Beta (`1`) | `16:9`, `9:16` |
| S1.5Pro (`2`) | `1:1`, `3:4`, `4:3`, `16:9`, `9:16`, `21:9`, `adaptive` |
| V3.1FB (`3`)、V3.1PB (`4`)、V3.1Fast (`5`)、V3.1Pro (`6`) | `16:9`, `9:16`, `adaptive` |
| Kling V3 Omni (`10`) | `1:1`, `16:9`, `9:16` |
| W2.6t (`7`)、W2.6r (`9`)、W2.7t (`15`)、W2.7r (`16`) | `1:1`, `3:4`, `4:3`, `16:9`, `9:16` |
| W2.6i (`8`)、W2.7i (`14`) | 固定（由首帧图比例决定） |
| Sora2 Pro (`12`) | `16:9`, `9:16`, `7:4`, `4:7` |

**视频时长按模型自动配置**
| model | 时长范围 | 可选档位 |
|-------|---------|---------|
| Sora2 Beta (`1`) | 5-15s | `10s`、`15s` |
| V3.1FB (`3`)、V3.1PB (`4`) | 8s（固定） | `8s` |
| V3.1Fast (`5`)、V3.1Pro (`6`) | 4-8s | `4s`、`8s` |
| W2.6t (`7`)、W2.6i (`8`)、Kling V3 Omni (`10`)、W2.7i (`14`)、W2.7t (`15`) | 3-15s | `3s`、`15s` |
| W2.6r (`9`) | 3-10s | `3s`、`10s` |
| W2.7r (`16`) | 3-15s（无视频引用）<br>3-10s（有视频引用） | `3s`、`10s` 或 `3s`、`15s` |
| Sora2 (`11`)、Sora2 Pro (`12`) | 4-12s | `4s`、`12s` |
| S1.5Pro (`2`)、Auto | 4-12s | `4s`、`12s` |

**镜头模式按模型自动过滤**
| model | 支持镜头模式 |
|-------|------------|
| W2.6t (`7`)、W2.6i (`8`)、W2.6r (`9`) | `single`、`multi` |
| Kling V3 Omni (`10`) | `single`、`multi`、`customize` |
| 其他 | `single`（默认） |

## 参数显隐逻辑（自动处理）

**按模型显示的参数**
| 参数 | 支持的 model (methodType) |
|------|-------------------------|
| `web_search`（联网搜索） | S5.0L (`4`)、N2-Evo (`8`) |
| `audio_url`（参考音频） | W2.6t (`7`)、W2.6i (`8`)、W2.7i (`14`)、W2.7t (`15`)、W2.7r (`16`) |
| `prompt_extend`（智能改写） | W2.6t (`7`)、W2.6i (`8`)、W2.6r (`9`)、W2.7i (`14`)、W2.7t (`15`)、W2.7r (`16`) |
| `first_clip_url`（续写视频） | Kling V3 Omni (`10`)、W2.7i (`14`) |
| `keep_original_sound`（保留原声） | Kling V3 Omni (`10`) |
| `element_list`（参考主体） | Kling V3 Omni (`10`) |
| `video_url_list`（参考视频） | W2.6r (`9`)、W2.7r (`16`) |
| `mode`（生成模式） | Kling V3 Omni (`10`) |
| `duration_switch`（时长模式） | S1.5Pro (`2`) |
| `generate_audio`（生成声音） | S1.5Pro (`2`)、V3.1Fast (`5`)、V3.1Pro (`6`)、Kling V3 Omni (`10`) |
| `enhance_prompt`（翻译英文） | V3.1FB (`3`)、V3.1PB (`4`)、V3.1Fast (`5`)、V3.1Pro (`6`) |
| `n`（生成数量） | V3.1Fast (`5`)、V3.1Pro (`6`) |
| `person_generation`（人物生成） | V3.1Fast (`5`)、V3.1Pro (`6`) |
| `resize_mode`（缩放模式） | V3.1Fast (`5`)、V3.1Pro (`6`) |
| `negative_prompt`（负向提示词） | V3.1Fast (`5`)、V3.1Pro (`6`)、W2.6t (`7`)、W2.6i (`8`)、W2.6r (`9`)、W2.7i (`14`)、W2.7t (`15`)、W2.7r (`16`) |
| `multi_shot`（多镜头） | Kling V3 Omni (`10`) |
| `shot_type`（镜头模式） | W2.6t (`7`)、W2.6i (`8`)、W2.6r (`9`)、Kling V3 Omni (`10`) |

**按模型隐藏的参数**
| 参数 | 不支持该参数的 model |
|------|---------------------|
| `last_image_url`（尾帧图片） | Auto、Sora2 Beta (`1`)、W2.6i (`8`)、Sora2 (`11`)、Sora2 Pro (`12`) |
| `ratio`（生成比例） | W2.6i (`8`)、W2.7i (`14`) |
| `resolution`（分辨率） | Kling V3 Omni (`10`) |
| `duration`（时长） | Auto |

**参数联动显隐（同模型下受其他参数影响）**
| 参数 | 依赖参数 | 显示条件 |
|------|---------|---------|
| `text`（提示词） | `shot_type` | `shot_type` = `'customize'` |
| `multi_prompt`（多镜头内容） | `shot_type` | `shot_type` = `'customize'` |
| `image_url_list`（参考图片） | `generation_type` | `generation_type` 为 REFERENCE、EDIT、FEATURE |
| `first_image_url`（首帧图） | `generation_type` | `generation_type` = FIRST&LAST |
| `last_image_url`（尾帧图） | `generation_type` | `generation_type` = FIRST&LAST |
| `first_clip_url`（续写视频） | `generation_type` | `generation_type` 为 CONTINUATION、EDIT、FEATURE |
| `keep_original_sound`（保留原声） | `first_clip_url` | `first_clip_url` 有值 |
| `element_list`（参考主体） | `generation_type` | `generation_type` ≠ TEXT |
| `ratio`（比例） | `generation_type` | Kling V3 Omni 除外：`generation_type` ≠ FIRST&LAST 且 ≠ EDIT |
| `duration`（时长） | `duration_switch` | `duration_switch` = `'1'` |


## 使用示例

**图片生成**
```bash
# 基础用法 - 默认模型 DeepSop·3.1Nano2-Evo
python3 scripts/generate_image.py "一匹狼"

# 指定质量
python3 scripts/generate_image.py "风景画" --quality "4K"

# 指定比例
python3 scripts/generate_image.py "风景画" --ratio "16:9"

# 使用 N2 模型
python3 scripts/generate_image.py "生成一只狗" --model N2

# 使用 N2-Pro 并开启联网搜索
python3 scripts/generate_image.py "2024年流行的装修风格" --model N2-Pro --web-search

# 使用 W2.7Pro
python3 scripts/generate_image.py "山水画" --model W2.7Pro --quality "2K" --ratio "9:16"

# 使用 N2-Evo
python3 scripts/generate_image.py "赛博朋克城市" --model N2-Evo --quality "4K" --ratio "16:9"

# 下载图片到本地
python3 scripts/generate_image.py "风景画" --download

# 直接输出 Markdown 图片链接
python3 scripts/generate_image.py "一只可爱的猫" --markdown-output

# 使用参考图生成
python3 scripts/generate_image.py "基于这张图生成变体" --reference-image "./reference.png"
```

**图片生成**
```bash
# 基础用法 - 默认 DeepSop·V3.1FB
python3 scripts/generate_video.py "海边日落风景"

# 指定比例和分辨率
python3 scripts/generate_video.py "海边日落风景" --ratio "9:16" --resolution "1080p"

# 指定时长
python3 scripts/generate_video.py "一只猫在玩耍" --duration 5

# 专家模式
python3 scripts/generate_video.py "海边日落风景" --mode pro

# 首尾帧生视频
python3 scripts/generate_video.py "花朵绽放" --generation-type FIRST&LAST --first-image "./flower_start.jpg" --last-image "./flower_end.jpg"

# 参考图生视频
python3 scripts/generate_video.py "产品展示" --generation-type REFERENCE --image-url-list "https://example.com/product1.jpg,https://example.com/product2.jpg"

# 视频续写
python3 scripts/generate_video.py "继续这个视频" --generation-type CONTINUATION --first-clip "./my_video.mp4" --duration 5

# Veo3.1 系列 - 文生视频
python3 scripts/generate_video.py "现代轻奢吊灯" --model V3.1FB --ratio "16:9" --duration 8

# Veo3.1 系列 - 首尾帧控制
python3 scripts/generate_video.py "灯具变形动画" --model V3.1Pro --first-image "./start.jpg" --last-image "./end.jpg" --duration 8

# Veo3.1 系列 - 负向提示词
python3 scripts/generate_video.py "人物奔跑" --model V3.1Pro --negative-prompt "模糊, 抖动" --duration 8

# Veo3.1Fast - 生成多个视频
python3 scripts/generate_video.py "产品广告" --model V3.1Fast --n 3 --duration 4

# W2.7t - 文生视频
python3 scripts/generate_video.py "现代轻奢吊灯宣传" --model W2.7t --ratio "16:9" --duration 10 --prompt-extend

# W2.7t - 带参考音频
python3 scripts/generate_video.py "产品展示" --model W2.7t --audio-url "https://example.com/audio.mp3" --duration 10

# W2.7i - 首帧图生视频
python3 scripts/generate_video.py "水晶灯展示" --model W2.7i --first-image "./lamp.jpg" --duration 8

# W2.7i - 视频续写
python3 scripts/generate_video.py "继续这个动画" --model W2.7i --first-image "./lamp.jpg" --first-clip "./lamp_animation.mp4" --duration 5

# W2.7r - 参考视频生视频
python3 scripts/generate_video.py "参考素材风格生成" --model W2.7r --video-url-list "https://example.com/video.mp4" --duration 10

# W2.7r - 多参考视频
python3 scripts/generate_video.py "风格迁移" --model W2.7r --video-url-list "https://example.com/style1.mp4,https://example.com/style2.mp4" --duration 8

# Kling V3 Omni - 多镜头分镜
python3 scripts/generate_video.py "电影预告片" --model "Kling V3 Omni" --shot-type multi --multi-shot --mode pro

# Kling V3 Omni - 参考主体
python3 scripts/generate_video.py "角色在行走" --model "Kling V3 Omni" --element-list "https://example.com/character.jpg"

# Kling V3 Omni - 保留原声的视频编辑
python3 scripts/generate_video.py "编辑这段视频" --model "Kling V3 Omni" --generation-type EDIT --first-clip "./original.mp4" --keep-original-sound

# Sora2 Pro - 高分辨率
python3 scripts/generate_video.py "风景大片" --model Sora2Pro --ratio "7:4" --resolution "2K" --duration 12
```

## 模型名称速查表

**图片模型（methodType → 模型名称）**
| methodType | 模型名称 | CLI 参数 |
|-----------|---------|---------|
| `0` | DeepSop·S4.5 | `S4.5` |
| `1` | DeepSop·N1 | `N1` |
| `2` | DeepSop·N2 | `N2` |
| `3` | DeepSop·3-Nano2-147 | `N2-147` |
| `4` | DeepSop·S5.0L | `S5.0L` |
| `5` | DeepSop·3.1Nano2-147 | `N2-Pro` |
| `6` | DeepSop.W2.7 | `W2.7` |
| `7` | DeepSop.W2.7Pro | `W2.7Pro` |
| `8` | DeepSop·3.1Nano2-Evo | `N2-Evo`（默认） |
| `9` | DeepSop·Nano2 Beta-Evo | `N2-Beta` |
| `auto` | DeepSop·Auto | `Auto` |

**视频模型（methodType → 模型名称）**
| methodType | 模型名称 | CLI 参数 |
|-----------|---------|---------|
| `1` | DeepSop·Sora2 Beta Max Evolink | `Sora2Beta` |
| `2` | DeepSop·S1.5Pro | `S1.5Pro` |
| `3` | DeepSop·V3.1FB | `V3.1FB`（默认） |
| `4` | DeepSop·V3.1PB | `V3.1PB` |
| `5` | DeepSop·V3.1Fast | `V3.1Fast` |
| `6` | DeepSop·V3.1Pro | `V3.1Pro` |
| `7` | DeepSop·W2.6t | `W2.6t` |
| `8` | DeepSop·W2.6i | `W2.6i` |
| `9` | DeepSop·W2.6r | `W2.6r` |
| `10` | DeepSop.klingV3Omni | `KlingV3Omni` |
| `11` | DeepSop·Sora2.147 | `Sora2` |
| `12` | DeepSop·Sora2 Pro.147 | `Sora2Pro` |
| `14` | DeepSop·W2.7i | `W2.7i` |
| `15` | DeepSop·W2.7t | `W2.7t` |
| `16` | DeepSop·W2.7r | `W2.7r` |
| `auto` | DeepSop·Auto | `Auto` |


## 程序化调用

```python
from scripts.generate_image import generate_image, generate_video

# 图片 - 默认 DeepSop·3.1Nano2-Evo
result = generate_image(prompt="一只可爱的猫咪")

# 图片 - N2 模型
result = generate_image(prompt="生成一只狗", model="N2")

# 图片 - 带联网搜索
result = generate_image(prompt="2024年流行的装修风格", model="N2-Pro", web_search=True)

# 图片 - 下载到本地
result = generate_image(prompt="风景画", model="S5.0L", download=True, output_dir="./images")

# 视频 - 默认 DeepSop·V3.1FB
result = generate_video(prompt="小骏马祝福大家新年快乐")

# 视频 - S1.5Pro 带音频
result = generate_video(
    prompt="海边日落风景",
    model="S1.5Pro",
    ratio="9:16",
    resolution="1080p",
    duration=5,
    generate_audio=True
)

# 视频 - V3.1Pro 首尾帧控制
result = generate_video(
    prompt="灯具变形动画",
    model="V3.1Pro",
    first_image_url="https://example.com/start.jpg",
    last_image_url="https://example.com/end.jpg",
    ratio="16:9",
    resolution="1080p",
    duration=8
)

# 视频 - V3.1Fast 生成多个
result = generate_video(
    prompt="产品广告",
    model="V3.1Fast",
    n=3,
    duration=4,
    person_generation="allow_adult"
)

# 视频 - W2.7t 带参考音频和提示词改写
result = generate_video(
    prompt="产品宣传片",
    model="W2.7t",
    ratio="16:9",
    resolution="1080p",
    duration=10,
    audio_url="https://example.com/music.mp3",
    prompt_extend=True
)

# 视频 - W2.7r 多参考视频
result = generate_video(
    prompt="风格迁移视频",
    model="W2.7r",
    video_url_list=["https://example.com/style1.mp4", "https://example.com/style2.mp4"],
    ratio="16:9",
    duration=10
)

# 视频 - Kling V3 Omni 多镜头模式
result = generate_video(
    prompt="电影预告片",
    model="KlingV3Omni",
    generation_type="TEXT",
    shot_type="multi",
    multi_shot=True,
    mode="pro"
)

# 视频 - Kling V3 Omni 参考主体
result = generate_video(
    prompt="角色在奔跑",
    model="KlingV3Omni",
    generation_type="REFERENCE",
    element_list=["https://example.com/character.jpg"],
    keep_original_sound=False
)

if result and result["status"] == "SUCCESS":
    print(f"媒体链接: {result['url']}")
    print(f"本地路径: {result.get('local_path')}")
```

## 图像生成前处理与参数变动

### 模型切换时的自动参数调整

当用户切换生成模型时，系统会自动调整以下参数：

| 切换场景 | 自动调整规则 |
|---------|-------------|
| 切换到 N1 (methodType=1) | `quality` 自动设置为 `1K` |
| 切换到其他模型 | `quality` 自动设置为 `2K`（默认）|
| 切换到 S5.0L (methodType=4) | `web_search` 自动开启 |
| 切换到其他模型 | `web_search` 自动关闭 |

### 模型与尺寸/质量的关系

图片生成时，`size` 参数会根据 `methodType`、`quality` 和用户选择的 `ratio` 自动计算：

| 模型类型 | methodType | size 格式 | 计算公式 |
|---------|-----------|----------|---------|
| S4.5、S5.0L | 0, 4 | `{width}x{height}` | 根据 quality 和 ratio 解析宽高后拼接 |
| W2.7、W2.7Pro | 6, 7 | `{width}*{height}` | 根据 quality 和 ratio 解析宽高后用 `*` 拼接 |
| N1、N2 系列 | 1, 2, 3, 5, 8, 9 | 比例字符串 | 直接使用用户选择的 ratio 值（如 `16:9`）|
| Auto | auto | 比例字符串 | 直接使用用户选择的 ratio 值 |

### 生成前预处理参数

在调用生成 API 前，系统会自动添加以下限制参数：

| 参数 | 说明 | 来源 |
|------|------|------|
| `targetMaxSize` | 目标图片最大尺寸（字节）| 根据模型类型自动匹配 |
| `targetMinLength` | 提示词最小长度 | 根据模型类型自动匹配 |
| `targetMaxLength` | 提示词最大长度 | 根据模型类型自动匹配 |

## 图片生成限制参数说明

### 各模型的输入限制参数

根据选择的模型，系统会自动应用以下限制参数（`targetMaxSize`、`targetMinLength`、`targetMaxLength`）：

| methodType | 模型名称 | maxSize (MB) | minLength (字) | maxLength (字) | maxQuantity (张) | 上传说明 |
|------------|---------|--------------|----------------|----------------|------------------|---------|
| auto | Auto | .jpeg,.jpg,.png,.webp | 10 | 2000 | 360 | 500 | - | 最长边≤2000px，最短边≥360px |
| 0 | S4.5 | .jpeg,.jpg,.png,.webp,.bmp,.tiff,.gif | 30 | 6000 | 300 | 500 | 14 | 宽高比 (0.4, 2.5)，最多生成15张 |
| 1 | N1 | .jpeg,.jpg,.png,.webp | 10 | 6000 | - | 1000 | 5 | 最长边≤6000px |
| 2 | N2 | .jpeg,.jpg,.png,.webp | 10 | 6000 | - | 1000 | 10 | 最长边≤6000px，最多5张真人图像 |
| 3 | N2-147 | .jpeg,.jpg,.png,.webp | 10 | 6000 | - | 1000 | 5 | 最长边≤6000px |
| 4 | S5.0L | .jpeg,.jpg,.png,.webp,.bmp,.tiff,.gif | 10 | 6000 | - | 300 | 14 | 宽高比 [1/16, 16]，最多生成15张 |
| 5 | N2-Pro | .jpeg,.jpg,.png,.webp | 10 | 6000 | - | 1000 | 5 | 最长边≤6000px |
| 6 | W2.7 | .jpeg,.jpg,.png,.bmp,.webp | 20 | 8000 | 240 | 2500 | 9 | 不支持透明通道，宽高比 [1:8, 8:1] |
| 7 | W2.7Pro | .jpeg,.jpg,.png,.bmp,.webp | 20 | 8000 | 240 | 2500 | 9 | 不支持透明通道，宽高比 [1:8, 8:1] |
| 8 | N2-Evo | .jpeg,.jpg,.png,.webp | 20 | 6000 | - | 1000 | 14 | 最长边≤6000px，最多4张真人图像 |
| 9 | N2-Beta | .jpeg,.jpg,.png,.webp | 10 | 6000 | - | 1000 | 14 | 最长边≤6000px，最多4张真人图像 |

### 图片生成提示词长度限制

| methodType | 模型名称 | textLength (最大提示词字数) |
|------------|---------|---------------------------|
| 0 | S4.5 | 500 |
| 1,2,3,5,8,9 | N1/N2 系列 | 1000 |
| 4 | S5.0L | 300 |
| 6,7 | W2.7/W2.7Pro | 2500 |
| auto | Auto | 500 |

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `targetAccept` | string | 支持的图片文件格式 |
| `targetMaxSize` | int (MB) | 上传图片的最大文件大小限制 |
| `targetMaxLength` | int (px) | 图片最长边的最大像素限制 |
| `targetMinLength` | int (px) | 图片最短边的最小像素限制 |
| `targetTextLength` | int (字) | 提示词的最大长度限制 |
| `targetMaxQuantity` | int (张) | 参考图片的最大上传数量 |
| `targetUploadTips` | string | 上传说明和合规性提示 |

### 图片上传合规性要求

**通用要求：**
- 支持格式：JPEG、JPG、PNG、WEBP（部分模型支持 BMP、TIFF、GIF）
- 文件大小：根据模型不同，限制为 10MB-30MB
- 最长边限制：根据模型不同，限制为 2000px-8000px

**内容审查要求（Sora2/Veo 系列）：**
1. 不得包含真人或拟真人图像
2. 提示词禁止暴力、色情、版权侵权或涉及名人信息

**Wan 系列特殊要求：**
1. 不支持透明通道（PNG 透明部分会被处理）
2. 宽高比必须在 [1:8, 8:1] 范围内

**Seedance 系列特殊要求：**
1. 宽高比（宽/高）必须在 (0.4, 2.5) 范围内
2. 上传图片最长边 ≤ 6000px，最短边 ≥ 300px

## 图片分辨率映射规则

### 质量等级与分辨率对照表

系统根据选择的 `quality`（图片质量）和 `ratio`（画面比例）自动计算输出图片的分辨率（宽 x 高）。

| 质量 | 1:1 | 16:9 | 9:16 | 3:4 | 4:3 | 2:3 | 3:2 | 4:5 | 5:4 | 1:4 | 4:1 | 1:8 | 8:1 | 21:9 |
|------|-----|------|------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|------|
| **1K** | 1024x1024 | 1920x1080 | 1080x1920 | 768x1024 | 1024x768 | 682x1024 | 1024x682 | 1024x1280 | 1280x1024 | 512x2048 | 2048x512 | 362x2896 | 2896x362 | 2560x1080 |
| **2K** | 2048x2048 | 2560x1440 | 1440x2560 | 1728x2304 | 2304x1728 | 1664x2496 | 2496x1664 | 1843x2304 | 2304x1843 | 1024x4096 | 4096x1024 | 724x5792 | 5792x724 | 3584x1536 |
| **3K** | 3072x3072 | 4096x2304 | 2304x4096 | 2592x3456 | 3456x2592 | 2496x3744 | 3744x2496 | 2884x3605 | 3605x2884 | 1536x6144 | 6144x1536 | 1088x8704 | 8704x1088 | 4704x2016 |
| **4K** | 4096x4096 | 3840x2160 | 2160x3840 | 3072x4096 | 4096x3072 | 2730x4096 | 4096x2730 | 3277x4096 | 4096x3277 | 2048x8192 | 8192x2048 | 1448x11584 | 11584x1448 | 5040x2160 |

### 不同模型的分辨率格式

| 模型类型 | methodType | 输出格式 | 示例 |
|---------|-----------|---------|------|
| S4.5、S5.0L | 0, 4 | `{width}x{height}` | `2048x2048` |
| W2.7、W2.7Pro | 6, 7 | `{width}*{height}` | `2048*2048` |
| N1、N2 系列 | 1, 2, 3, 5, 8, 9 | 比例字符串 | `1:1`、`16:9` |
| Auto | auto | 比例字符串 | `1:1`、`16:9` |

### 分辨率计算示例

```python
from scripts.generate_image import get_image_resolution

# 获取 2K 质量、16:9 比例的分辨率
resolution = get_image_resolution(quality="2K", ratio="16:9")
print(resolution)  # 输出: [2560, 1440]

# 获取 4K 质量、1:1 比例的分辨率
resolution = get_image_resolution(quality="4K", ratio="1:1")
print(resolution)  # 输出: [4096, 4096]

# 仅获取质量对应的所有分辨率
resolutions = get_image_resolution(quality="2K")
print(resolutions)  # 输出: {'1:1': [2048, 2048], '16:9': [2560, 1440], ...}
```


## 视频生成前处理与参数变动

### 模型切换时的自动参数调整

当用户切换视频模型时，系统会自动调整以下参数：

| 切换场景 | 自动调整规则 |
|---------|-------------|
| 切换到 W2.6t/W2.7t (methodType=7) | `generation_type` 自动设置为 `TEXT`（文生视频）|
| 切换到 W2.6r/W2.7r (methodType=9,16) | `generation_type` 自动设置为 `REFERENCE`（参考图/视频生视频）|
| 切换到 Kling V3 Omni (methodType=10) | `generation_type` 自动设置为 `REFERENCE` |
| 切换到其他模型 | `generation_type` 自动设置为 `FIRST&LAST`（首尾帧生视频）|
| 切换到 Kling V3 Omni (methodType=10) | `shot_type` 自动设置为 `multi`（智能分镜）|
| 切换到其他模型 | `shot_type` 自动设置为 `single`（单镜头）|
| 切换到 V3.1系列/Sora2系列 (3,4,5,6,11,12) | `duration` 自动设置为 `8` 秒 |
| 切换到其他视频模型 | `duration` 自动设置为 `10` 秒 |

### 镜头模式切换规则

当用户切换镜头模式时，系统会自动调整以下参数：

| 切换场景 | 自动调整规则 |
|---------|-------------|
| 切换到 Kling 多镜头模式（multi/customize） | `multi_shot` 自动设置为 `true` |
| 切换到 Kling 自定义多镜头（customize） | `text` 参数清空，`multi_prompt` 初始化为 `[{ index: 1, prompt: text, duration }]` |
| 切换到 Kling 智能分镜（multi） | `text` 参数设置为 `multi_prompt[0].prompt`，`multi_prompt` 清空 |
| 切换到单镜头模式（single） | `text` 参数设置为 `multi_prompt[0].prompt`，`multi_prompt` 清空，`multi_shot` 设置为 `false` |
| Kling 多镜头模式下禁止首尾帧生视频 | 如果 `generation_type` 为 `FIRST&LAST`，自动切换为 `REFERENCE` |

### 分辨率与比例的联动规则

| 模型 | 分辨率 | 比例联动规则 |
|------|--------|-------------|
| Sora2 Pro (methodType=12) | 720p | 支持比例：16:9、9:16 |
| Sora2 Pro (methodType=12) | 2K | 支持比例：7:4、4:7 |
| 其他模型 | - | 无特殊联动 |

### 生成类型切换时的参数重置

当用户切换生成类型时，系统会自动清空以下关联参数：

| 清空的参数 | 说明 |
|-----------|------|
| `image_url_list` | 参考图片列表 |
| `first_image_url` | 首帧图片 |
| `last_image_url` | 尾帧图片 |
| `first_clip_url` | 续写/编辑参考视频 |
| `element_list` | 参考主体列表 |
| `video_url_list` | 参考视频列表 |
| `audio_url` | 参考音频 |
| `duration_list` | 参考视频时长列表 |
| `generate_audio` | 视频编辑/参考视频生视频模式下自动关闭音频生成 |

在调用生成 API 前，系统会自动进行以下处理：

| 处理项 | 规则说明 |
|--------|---------|
| `size`（尺寸）| methodType=7,9（Wan系列）转换为 `{width}*{height}` 格式<br>methodType=11,12（Sora2系列）转换为 `{width}x{height}` 格式<br>其他模型保持比例字符串 |
| `duration`（时长）| durationSwitch='2' 时设置为 `-1`（智能时长）<br>否则使用用户选择的值 |
| `shot_type`（镜头类型）| Kling 多镜头模式（shot_type='multi'）转换为 `intelligence`<br>其他保持原值 |
| `generate_audio`（生成声音）| Kling 视频编辑模式（first_clip_url 有值）时自动设置为 `false` |
| `video_list`（视频列表）| Kling 视频编辑/参考视频生视频模式时构建视频对象 |

### 参数校验规则

生成前系统会进行以下校验：

| 校验项 | 条件 | 错误提示 |
|--------|------|---------|
| 提示词 | 非 Wan I2V 模式且无提示词，且非 Kling 自定义多镜头 | 请填写生成视频的提示词！ |
| Wan I2V 首帧 | Wan I2V 模式且生成类型为首尾帧生视频，无首帧图片 | 请上传首帧图片！ |
| Wan2.7 I2V 续写 | methodType=14 且生成类型为续写模式，无续写视频 | 请上传续写视频！ |
| Kling 首尾帧/参考图 | Kling 首尾帧模式无首帧图片且无参考主体<br>或参考图模式无参考图片且无参考主体 | 请上传首帧图片或选择参考主体！<br>或：请至少上传一张参考图片或选择一个参考主体！ |
| Kling 自定义多镜头 | Kling 自定义多镜头模式，分镜时长或提示词为空 | 分镜信息的时长不能为空或为0，镜头描述不能为空！ |
| Kling 视频编辑 | Kling 视频编辑模式且生成类型为 EDIT/FEATURE，无编辑视频 | 请上传编辑视频/参考视频！ |
| Wan R2V 数量 | Wan R2V 模式，参考图片+参考视频总数为0或大于5 | 上传的参考图片+参考视频总数不能为0且不能大于5！ |
| 尾帧图片 | 有尾帧图片但无首帧图片 | 请上传首帧图片！ |

### 使用示例

```python
from scripts.generate_video import generate_video

# 1. 模型切换示例 - 切换到 W2.6t 自动变为文生视频
result = generate_video(
    prompt="海边日落",
    model="W2.6t"
    # generation_type 会自动设置为 "TEXT"
)

# 2. 模型切换示例 - 切换到 Kling 自动变为多镜头模式
result = generate_video(
    prompt="电影预告片",
    model="KlingV3Omni"
    # shot_type 会自动设置为 "multi"
    # multi_shot 会自动设置为 True
)

# 3. 自定义多镜头模式
result = generate_video(
    prompt="",
    model="KlingV3Omni",
    shot_type="customize",
    multi_prompt=[
        {"index": 1, "prompt": "镜头1描述", "duration": 3},
        {"index": 2, "prompt": "镜头2描述", "duration": 3}
    ],
    duration=6
)

# 4. Kling 视频编辑模式（自动关闭音频生成）
result = generate_video(
    prompt="编辑这段视频",
    model="KlingV3Omni",
    generation_type="EDIT",
    first_clip_url="https://example.com/video.mp4",
    keep_original_sound=True
    # generate_audio 会自动设置为 False
)

# 5. Sora2 Pro - 分辨率与比例联动
result = generate_video(
    prompt="风景大片",
    model="Sora2Pro",
    resolution="2K",  # 2K 分辨率时比例会自动推荐 7:4
    ratio="7:4"
)

# 6. Wan R2V - 多参考素材
result = generate_video(
    prompt="风格迁移",
    model="W2.7r",
    image_url_list=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
    video_url_list=["https://example.com/style.mp4"]
    # 总数不能超过 5 个（图片+视频）
)
```

### 使用示例

```python
from scripts.generate_image import generate_image

# 模型切换时的自动参数调整示例
# 1. 切换到 N1 模型时，quality 自动变为 "1K"
result = generate_image(
    prompt="一只猫",
    model="N1"  # quality 会自动设为 "1K"
)

# 2. 切换到 S5.0L 模型时，web_search 自动开启
result = generate_image(
    prompt="2024年流行的设计趋势",
    model="S5.0L"  # web_search 会自动设为 True
)

# 3. 手动覆盖自动参数（按此优先级：用户指定 > 系统默认）
result = generate_image(
    prompt="一只猫",
    model="N1",
    quality="2K"  # 手动指定会覆盖系统的 "1K" 默认值
)
```

## 视频模型输入限制参数

### 各视频模型的输入限制

根据选择的模型，系统会自动应用以下限制参数（图片、音频、视频上传）：

#### 图片上传限制

| methodType | 模型名称 | 支持格式 | maxSize (MB) | maxLength (px) | minLength (px) | textLength (字) | maxQuantity (张) | 特殊说明 |
|------------|---------|---------|--------------|----------------|----------------|-----------------|------------------|---------|
| auto | Auto | .jpeg,.jpg,.png,.webp | 10 | 2000 | 360 | 500 | - | 最长边≤2000px，最短边≥360px |
| 0 | Seedance1.0 Pro | .jpeg,.jpg,.png,.webp,.bmp,.tiff,.gif | 30 | 6000 | 300 | 500 | - | 宽高比 (0.4, 2.5) |
| 1 | Sora2 Beta | .jpeg,.jpg,.png,.webp | 10 | 6000 | 300 | 2500 | - | 不得包含真人或拟真人图像 |
| 2 | Seedance1.5 Pro | .jpeg,.jpg,.png,.webp,.bmp,.heic,.heif,.tiff,.gif | 30 | 6000 | 300 | 500 | - | 宽高比 (0.4, 2.5) |
| 3 | Veo3.1 Fast Lite | .jpeg,.jpg,.png,.webp | 10 | 6000 | 300 | 2500 | 2 | 支持负向提示词(250字) |
| 4 | Veo3.1 Pro Lite | .jpeg,.jpg,.png,.webp | 10 | 6000 | 300 | 2500 | - | 支持负向提示词(250字) |
| 5 | Veo3.1 Fast | .jpeg,.jpg,.png,.webp | 10 | 6000 | 300 | 2500 | - | 支持负向提示词(250字) |
| 6 | Veo3.1 Pro | .jpeg,.jpg,.png,.webp | 10 | 6000 | 300 | 2500 | - | 支持负向提示词(250字) |
| 8 | Wan2.6 i2v | .jpeg,.jpg,.png,.bmp,.webp | 10 | 2000 | 360 | 750 | - | 宽高比 [1:8, 8:1] |
| 9 | Wan2.6 r2v | .jpeg,.jpg,.png,.bmp,.webp | 10 | 5000 | 240 | 750 | 5 | 图片+视频≤5 |
| 10 | Kling V3 Omni | .jpeg,.jpg,.png | 10 | - | 300 | 1250 | 7 | 宽高比 [1:2.5, 2.5:1] |
| 11 | Sora2 | .jpeg,.jpg,.png,.webp | 10 | 6000 | 300 | 2500 | - | 图片比例必须符合生成比例 |
| 12 | Sora2 Pro | .jpeg,.jpg,.png,.webp | 10 | 6000 | 300 | 2500 | - | 图片比例必须符合生成比例 |
| 14 | Wan2.7 i2v | .jpeg,.jpg,.png,.bmp,.webp | 20 | 8000 | 240 | 2500 | - | 宽高比 [1:8, 8:1] |
| 16 | Wan2.7 r2v | .jpeg,.jpg,.png,.bmp,.webp | 10 | 8000 | 240 | 2500 | 5 | 图片+视频≤5，宽高比 [1:8, 8:1] |

#### 音频上传限制

| methodType | 模型名称 | 支持格式 | maxSize (MB) | maxLength (秒) | minLength (秒) | 说明 |
|------------|---------|---------|--------------|----------------|----------------|------|
| 7 | Wan2.6 t2v | .wav,.mp3 | 15 | 30 | 3 | 时长超出视频则截取，不足则无声 |
| 8 | Wan2.6 i2v | .wav,.mp3 | 15 | 30 | 3 | 时长超出视频则截取，不足则无声 |
| 14 | Wan2.7 i2v | .wav,.mp3 | 15 | 30 | 3 | 时长超出视频则截取，不足则无声 |
| 15 | Wan2.7 t2v | .wav,.mp3 | 15 | 30 | 3 | 时长超出视频则截取，不足则无声 |
| 16 | Wan2.7 r2v | .wav,.mp3 | 15 | 10 | 2 | 用于指定参考素材中主体角色的音色 |

#### 视频上传限制

| methodType | 模型名称 | 支持格式 | maxSize (MB) | maxLength (秒) | minLength (秒) | maxQuantity | 说明 |
|------------|---------|---------|--------------|----------------|----------------|-------------|------|
| 9 | Wan2.6 r2v | .mp4,.mov | 100 | 30 | 1 | 3 | 图片+视频≤5 |
| 10 | Kling V3 Omni | .mp4,.mov | 200 | 10 | 3 | - | 视频编辑/参考视频生视频 |
| 14 | Wan2.7 i2v | .mp4,.mov | 100 | 10 | 2 | 1 | 视频续写模式，宽高比 [1:8, 8:1] |
| 16 | Wan2.7 r2v | .mp4,.mov | 100 | 30 | 1 | 3 | 图片+视频≤5 |

### 负向提示词支持

| methodType | 模型名称 | negativeTextLength (字) |
|------------|---------|------------------------|
| 3 | Veo3.1 Fast Lite | 250 |
| 4 | Veo3.1 Pro Lite | 250 |
| 5 | Veo3.1 Fast | 250 |
| 6 | Veo3.1 Pro | 250 |
| 7 | Wan2.6 t2v | 250 |
| 8 | Wan2.6 i2v | 250 |
| 9 | Wan2.6 r2v | 250 |
| 14 | Wan2.7 i2v | 250 |
| 15 | Wan2.7 t2v | 250 |
| 16 | Wan2.7 r2v | 250 |

### Kling V3 Omni 特殊限制

当使用 Kling V3 Omni 模型时，参考图片数量限制根据是否有编辑视频动态变化：

| 场景 | 参考图片 + 多图主体数量限制 |
|------|---------------------------|
| 无编辑视频/参考视频 | ≤ 7 |
| 有编辑视频/参考视频 | ≤ 4 |

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `targetMaxSize` | int (MB) | 上传文件的最大大小限制 |
| `targetMinLength` | int (px/秒) | 图片最短边像素 / 音视频最短时长 |
| `targetMaxLength` | int (px/秒) | 图片最长边像素 / 音视频最长时长 |
| `targetTextLength` | int (字) | 提示词的最大长度限制 |
| `targetNegativeTextLength` | int (字) | 负向提示词的最大长度限制 |
| `targetMaxQuantity` | int | 单次最多上传文件数量 |
| `targetAccept` | string | 支持的文件格式 |
| `targetUploadTips` | string | 上传说明提示 |

## 视频分辨率映射规则

### 质量等级与分辨率对照表

系统根据选择的 `resolution`（视频质量）和 `ratio`（画面比例）自动计算输出视频的分辨率（宽 x 高）。

| 质量 | 1:1 | 16:9 | 9:16 | 3:4 | 4:3 | 7:4 | 4:7 |
|------|-----|------|------|-----|-----|-----|-----|
| **720p** | 960x960 | 1280x720 | 720x1280 | 832x1088 | 1088x832 | - | - |
| **1080p** | 1440x1440 | 1920x1080 | 1080x1920 | 1248x1632 | 1632x1248 | - | - |
| **2K** | - | - | - | - | - | 1792x1024 | 1024x1792 |

### 不同视频模型的尺寸输出格式

| 模型类型 | methodType | 输出格式 | 示例 |
|---------|-----------|---------|------|
| Wan2.6/2.7 系列 (T2V/R2V) | 7, 9, 15, 16 | `{width}*{height}` | `1280*720` |
| Sora2 系列 | 11, 12 | `{width}x{height}` | `1280x720` |
| 其他视频模型 | 其他 | 比例字符串 | `16:9`、`9:16` |

### 分辨率计算示例

```python
from scripts.generate_video import get_video_resolution

# 获取 1080p 质量、16:9 比例的分辨率
resolution = get_video_resolution(quality="1080p", ratio="16:9")
print(resolution)  # 输出: [1920, 1080]

# 获取 720p 质量、1:1 比例的分辨率
resolution = get_video_resolution(quality="720p", ratio="1:1")
print(resolution)  # 输出: [960, 960]

# 获取 2K 质量、7:4 比例的分辨率
resolution = get_video_resolution(quality="2K", ratio="7:4")
print(resolution)  # 输出: [1792, 1024]

# 仅获取质量对应的所有分辨率
resolutions = get_video_resolution(quality="1080p")
print(resolutions)  # 输出: {'1:1': [1440, 1440], '16:9': [1920, 1080], '9:16': [1080, 1920], '3:4': [1248, 1632], '4:3': [1632, 1248]}
```

## 视频提示词写作建议
推荐书写模版：主体 + 运动，背景 + 运动，镜头 + 运动 ...

1. 基础结构：图生视频已经有了场景，因此尽量减少（甚至避免）对静止/无变化部分的描述，在明确指出运动对象的情况下，多描述运动的部分，包括主体的运动、背景的运动/变化、以及镜头的运动。

2. 简单直接：尽量使用简单词语和句子结构，模型会根据我们的表达与对图像画面的理解进行提示词扩写，生成符合预期的视频。

3. 特征描述：当主体具有一些突出特征时，可以加上突出特征来更好定位主体，比如老人、戴墨镜的女人等。描述运动时，关键的程度副词一定要明确，比如快速、幅度大。

4. 遵从图片：需要基于输入的图片内容来写，需要明确写出主体以及想做的动作或者运镜，需注意提示词不要与图片内容/基础参数存在事实矛盾。

5. 负向提示词：部分模型不响应负向提示词（如 Kling V3 Omni），请查阅上方各模型说明。

## 返回字段

| 字段 | 说明 |
|------|------|
| `status` | SUCCESS / FAILED / TIMEOUT |
| `url` | 媒体文件URL |
| `message` | 状态描述 |
| `local_path` | 本地保存路径（需 --download） |
| `data_uri` | Base64 Data URI（需 --download） |
| `image_data` | 原始图片字节（需 --download） |

## 环境配置

### 必需配置 - API Key

**重要：使用前必须设置你自己的 API Key！**

#### 获取 API Key

1. 访问 [https://ai.deepsop.com/](https://ai.deepsop.com/)
2. 注册并登录账号
3. 在控制台创建你的 API Key
4. 复制生成的 API Key（格式：`sk-xxxxxx...`）

#### 方式 1：使用 .env 文件（推荐）

1. 复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入你的 API Key：
   ```bash
   AI_ARTIST_TOKEN=sk-your_api_key_here
   ```

3. 在运行脚本前加载环境变量：
   ```bash
   # Linux/macOS/Git Bash
   source .env

   # 或使用 export
   export $(cat .env | xargs)
   ```

#### 方式 2：直接设置环境变量

##### Linux / macOS / Git Bash (Windows)

```bash
export AI_ARTIST_TOKEN="sk-your_api_key_here"
```

为了永久生效，将上述命令添加到 `~/.bashrc` 或 `~/.zshrc` 文件中。

##### Windows PowerShell

```powershell
$env:AI_ARTIST_TOKEN="sk-your_api_key_here"
```

永久设置（系统级）：
```powershell
[System.Environment]::SetEnvironmentVariable('AI_ARTIST_TOKEN', 'sk-your_api_key_here', 'User')
```

##### Windows CMD

```cmd
set AI_ARTIST_TOKEN=sk-your_api_key_here
```

#### 验证配置

运行以下命令验证 API Key 是否设置成功：

```bash
# Linux/macOS/Git Bash
echo $AI_ARTIST_TOKEN

# Windows PowerShell
echo $env:AI_ARTIST_TOKEN

# Windows CMD
echo %AI_ARTIST_TOKEN%
```

如果输出为空或显示默认值，说明环境变量未正确设置。

#### 测试配置（推荐）

运行配置测试脚本，验证 API Key 是否正确设置：

```bash
python3 scripts/test_config.py
```

该脚本会检查：
- API Key 是否已设置
- 是否使用了默认 Key（需要替换为你自己的）
- 配置是否可以正常使用

### 可选配置 - 飞书通知

```bash
export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

## 相关文件

- `scripts/generate_image.py` - 图片生成脚本
- `scripts/generate_video.py` - 视频生成脚本
- `references/api.md` - API 详细文档
