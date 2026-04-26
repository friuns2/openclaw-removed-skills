#!/usr/bin/env python3
"""
AI Image Generator - Async Image Generation Script

Calls the AI Artist API to generate images from text prompts.
Handles async task polling until completion.

Supports Feishu webhook callback for result notification.
Set FEISHU_WEBHOOK_URL environment variable to enable.

Supports local file upload for reference images/videos.
Local files are automatically uploaded to get public URLs before calling generation APIs.
"""

import requests
import json
import time
import sys
import argparse
import os
import base64
from pathlib import Path

# Configuration
API_PREFIX = "https://ai.deepsop.com/prod-api/"
BASE_URL = f"{API_PREFIX.rstrip('/')}/ai"
FILE_UPLOAD_URL = f"{API_PREFIX.rstrip('/')}/system/fileUpload/upload"
ESTIMATE_COST_URL = f"{BASE_URL}/estimate/cost"
RECHARGE_URL = "https://ai.deepsop.com/"

# Get API key from environment variable (required)
API_KEY = os.environ.get("AI_ARTIST_TOKEN")

# Feishu webhook configuration (optional)
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL")


def check_api_key():
    """Check if user has set their API key."""
    if not API_KEY:
        print("错误：未配置 AI_ARTIST_TOKEN 环境变量", file=sys.stderr)
        print("", file=sys.stderr)
        print("请先设置你的 API Key:", file=sys.stderr)
        print("  export AI_ARTIST_TOKEN=\"sk-your_api_key_here\"", file=sys.stderr)
        print("", file=sys.stderr)
        print("验证配置:", file=sys.stderr)
        print("  python3 scripts/test_config.py", file=sys.stderr)
        print("", file=sys.stderr)
        sys.exit(1)
    return True


def get_headers():
    """Build request headers with API key."""
    return {
        "Content-Type": "application/json",
        "X-Api-Key": API_KEY
    }


def estimate_generation_cost(payload):
    try:
        response = requests.post(ESTIMATE_COST_URL, json=payload, headers=get_headers(), timeout=30)
        response.raise_for_status()
        result = response.json()

        if result.get("code") != 200:
            print(f"费用预估失败：{result.get('msg', '未知错误')}", file=sys.stderr)
            return False

        data = result.get("data") or {}
        estimated_cost = data.get("estimatedCost")
        sufficient_balance = data.get("sufficientBalance")

        if estimated_cost is not None:
            print(f"预估费用：{estimated_cost} K币")

        if sufficient_balance is True:
            print("余额充足，正在创建任务")
            return True

        if sufficient_balance is False:
            print(f"余额不足，无法提交创建任务。请前往 {RECHARGE_URL} 充值 K 币后重试。", file=sys.stderr)
            return False

        print("费用预估返回结果不完整", file=sys.stderr)
        return False

    except requests.exceptions.RequestException as e:
        print(f"费用预估网络错误：{e}", file=sys.stderr)
        return False
    except ValueError as e:
        print(f"费用预估响应解析失败：{e}", file=sys.stderr)
        return False


def upload_file(file_path):
    """
    Upload a local file to the file server and get a public URL.
    
    Args:
        file_path: Path to the local file
    
    Returns:
        str: Public URL of the uploaded file, or None if failed
    """
    if not os.path.exists(file_path):
        print(f"文件不存在：{file_path}", file=sys.stderr)
        return None
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            headers = {'X-Api-Key': API_KEY}
            
            response = requests.post(FILE_UPLOAD_URL, headers=headers, files=files, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 200:
                url = result.get("url")
                print(f"文件已上传：{file_path} → {url}")
                return url
            else:
                print(f"文件上传失败：{result.get('msg', '未知错误')}", file=sys.stderr)
                return None
                
    except Exception as e:
        print(f"文件上传错误：{e}", file=sys.stderr)
        return None


def download_image(url, output_path=None):
    """
    Download image from URL.
    
    Args:
        url: Image URL
        output_path: Optional path to save the image
    
    Returns:
        bytes: Image data, or None if failed
    """
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        image_data = response.content
        
        # Save to file if path provided
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"图片已保存：{output_path}")
        
        return image_data
        
    except Exception as e:
        print(f"下载图片失败：{e}", file=sys.stderr)
        return None


def image_to_data_uri(image_data, mime_type="image/png"):
    """
    Convert image bytes to data URI.
    
    Args:
        image_data: Raw image bytes
        mime_type: MIME type of the image
    
    Returns:
        str: Data URI string
    """
    base64_data = base64.b64encode(image_data).decode('utf-8')
    return f"data:{mime_type};base64,{base64_data}"


def send_feishu_message(prompt, result):
    """Send generation result to Feishu chat."""
    if not FEISHU_WEBHOOK_URL:
        return False
    
    try:
        if result and result["status"] == "SUCCESS":
            content = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": "图片生成成功"},
                        "template": "green"
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": f"**提示词**: {prompt}\n\n**图片链接**: [点击查看]({result['url']})"
                            }
                        },
                        {
                            "tag": "action",
                            "actions": [{
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "打开图片"},
                                "url": result["url"],
                                "type": "default"
                            }]
                        }
                    ]
                }
            }
        else:
            error_msg = result.get("message", "未知错误") if result else "未知错误"
            content = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": "图片生成失败"},
                        "template": "red"
                    },
                    "elements": [{
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**提示词**: {prompt}\n\n**错误**: {error_msg}"
                        }
                    }]
                }
            }
        
        response = requests.post(
            FEISHU_WEBHOOK_URL,
            json=content,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        return True
        
    except Exception as e:
        print(f"[Feishu] 发送通知失败：{e}", file=sys.stderr)
        return False


# Model configurations
# media_type: "image" or "video" — determines task creation and output handling
MODEL_CONFIGS = {
    "SEEDREAM5_0": {
        "media_type": "image",
        "type": "10",
        "methodType": "4",
        "default_size": "2048x2048",
        "default_quality": "2K",
        "extra_params": {"duration": 10}
    },
    "NANO_BANANA_2": {
        "media_type": "image",
        "type": "10",
        "methodType": "5",
        "default_size": "1:1",
        "default_quality": "2K",
        "extra_params": {}
    },
    "SEEDANCE_1_5_PRO": {
        "media_type": "video",
        "type": "9",
        "methodType": "2",
        "default_ratio": "16:9",
        "default_resolution": "720p",
        "default_duration": 10,
        "extra_params": {
            "generationType": "FIRST&LAST",
            "negativePrompt": "",
            "firstImageUrl": None,
            "lastImageUrl": None,
            "durationList": [],
            "enhancePrompt": False,
            "generateAudio": True,
            "n": 1,
            "personGeneration": "allow_adult",
            "resizeMode": "pad",
            "promptExtend": False,
            "shotType": "single",
            "durationSwitch": "1",
            "targetMaxSize": 30,
            "targetMinLength": 300,
            "targetMaxLength": 6000
        }
    },
    "SORA2": {
        "media_type": "video",
        "type": "9",
        "methodType": "11",
        "default_ratio": "16:9",
        "default_resolution": "720p",
        "default_duration": 4,
        "extra_params": {
            "generationType": "FIRST&LAST",
            "negativePrompt": "",
            "firstImageUrl": None,
            "lastImageUrl": None,
            "enhancePrompt": False,
            "generateAudio": True,
            "n": 1,
            "personGeneration": "allow_adult",
            "resizeMode": "pad",
            "promptExtend": False,
            "shotType": "single",
            "durationSwitch": "1",
            "scaleFactor": 0.5,
            "targetMaxSize": 10,
            "targetMinLength": 300,
            "targetMaxLength": 6000,
            "imageUrlList": [],
            "videoUrlList": [],
            "durationList": []
        }
    },
    "VEO3.1FAST_LITE": {
        "media_type": "video",
        "type": "9",
        "methodType": "3",
        "default_ratio": "16:9",
        "default_resolution": "1080p",
        "default_duration": 8,
        "extra_params": {
            "generationType": "FIRST&LAST",
            "negativePrompt": "",
            "imageUrlList": None,
            "firstImageUrl": None,
            "lastImageUrl": None,
            "audioUrl": None,
            "videoUrlList": None,
            "durationList": [],
            "enhancePrompt": False,
            "generateAudio": True,
            "n": 1,
            "personGeneration": "allow_adult",
            "resizeMode": "pad",
            "promptExtend": False,
            "shotType": "single",
            "durationSwitch": "1",
            "targetMaxSize": 10,
            "targetMinLength": 300,
            "targetMaxLength": 6000
        }
    },
    "VEO3.1PRO_LITE": {
        "media_type": "video",
        "type": "9",
        "methodType": "4",
        "default_ratio": "adaptive",
        "default_resolution": "720p",
        "default_duration": 8,
        "extra_params": {
            "generationType": "FIRST&LAST",
            "negativePrompt": "",
            "imageUrlList": None,
            "firstImageUrl": None,
            "lastImageUrl": None,
            "audioUrl": None,
            "videoUrlList": None,
            "durationList": [],
            "enhancePrompt": False,
            "generateAudio": True,
            "n": 1,
            "personGeneration": "allow_adult",
            "resizeMode": "pad",
            "promptExtend": False,
            "shotType": "single",
            "durationSwitch": "1",
            "targetMaxSize": 10,
            "targetMinLength": 300,
            "targetMaxLength": 6000
        }
    },
    "VEO3.1FAST": {
        "media_type": "video",
        "type": "9",
        "methodType": "5",
        "default_ratio": "16:9",
        "default_resolution": "720p",
        "default_duration": 8,
        "extra_params": {
            "generationType": "FIRST&LAST",
            "negativePrompt": "",
            "imageUrlList": None,
            "firstImageUrl": None,
            "lastImageUrl": None,
            "audioUrl": None,
            "videoUrlList": None,
            "durationList": [],
            "enhancePrompt": False,
            "generateAudio": True,
            "n": 1,
            "personGeneration": "allow_adult",
            "resizeMode": "pad",
            "promptExtend": False,
            "shotType": "single",
            "durationSwitch": "1",
            "targetMaxSize": 10,
            "targetMinLength": 300,
            "targetMaxLength": 6000
        }
    },
    "VEO3.1PRO": {
        "media_type": "video",
        "type": "9",
        "methodType": "6",
        "default_ratio": "16:9",
        "default_resolution": "1080p",
        "default_duration": 8,
        "extra_params": {
            "generationType": "FIRST&LAST",
            "negativePrompt": "",
            "imageUrlList": None,
            "firstImageUrl": None,
            "lastImageUrl": None,
            "audioUrl": None,
            "videoUrlList": None,
            "durationList": [],
            "enhancePrompt": False,
            "generateAudio": True,
            "n": 1,
            "personGeneration": "allow_adult",
            "resizeMode": "pad",
            "promptExtend": False,
            "shotType": "single",
            "durationSwitch": "1",
            "targetMaxSize": 10,
            "targetMinLength": 300,
            "targetMaxLength": 6000
        }
    },
    "WAN2.6_T2V": {
        "media_type": "video",
        "type": "9",
        "methodType": "7",
        "default_ratio": "16:9",
        "default_resolution": "720p",
        "default_duration": 10,
        "extra_params": {
            "generationType": "TEXT",
            "negativePrompt": "",
            "imageUrlList": None,
            "firstImageUrl": None,
            "lastImageUrl": None,
            "audioUrl": None,
            "videoUrlList": None,
            "durationList": [],
            "enhancePrompt": False,
            "generateAudio": True,
            "n": 1,
            "personGeneration": "allow_adult",
            "resizeMode": "pad",
            "promptExtend": False,
            "shotType": "single",
            "durationSwitch": "1",
            "targetMaxSize": 10,
            "targetMinLength": 360,
            "targetMaxLength": 2000
        }
    },
    "WAN2.6_I2V": {
        "media_type": "video",
        "type": "9",
        "methodType": "8",
        "default_ratio": "16:9",
        "default_resolution": "720p",
        "default_duration": 10,
        "extra_params": {
            "generationType": "FIRST&LAST",
            "negativePrompt": "",
            "imageUrlList": None,
            "firstImageUrl": None,
            "lastImageUrl": None,
            "audioUrl": None,
            "videoUrlList": None,
            "durationList": [],
            "enhancePrompt": False,
            "generateAudio": True,
            "n": 1,
            "personGeneration": "allow_adult",
            "resizeMode": "pad",
            "promptExtend": False,
            "shotType": "single",
            "durationSwitch": "1",
            "targetMaxSize": 10,
            "targetMinLength": 360,
            "targetMaxLength": 2000
        }
    },
    "WAN2.6_R2V": {
        "media_type": "video",
        "type": "9",
        "methodType": "9",
        "default_ratio": "16:9",
        "default_resolution": "720p",
        "default_duration": 10,
        "extra_params": {
            "generationType": "REFERENCE",
            "negativePrompt": "",
            "imageUrlList": None,
            "firstImageUrl": None,
            "lastImageUrl": None,
            "audioUrl": None,
            "videoUrlList": None,
            "durationList": [],
            "enhancePrompt": False,
            "generateAudio": True,
            "n": 1,
            "personGeneration": "allow_adult",
            "resizeMode": "pad",
            "promptExtend": False,
            "shotType": "single",
            "durationSwitch": "1",
            "targetMaxSize": 10,
            "targetMinLength": 240,
            "targetMaxLength": 5000
        }
    }
}


def create_video_task(prompt, model="SEEDANCE_1_5_PRO", ratio=None, resolution=None,
                      duration=None, first_image_url=None, last_image_url=None,
                      generate_audio=None, scale_factor=None, generation_type=None,
                      enhance_prompt=None, prompt_extend=None, audio_url=None,
                      image_url_list=None, video_url_list=None):
    """Create a video generation task.

    Args:
        prompt: Text description of the video
        model: Video model to use (e.g. SEEDANCE_1_5_PRO, SORA2)
        ratio: Aspect ratio, e.g. '16:9', '9:16', '1:1'
        resolution: Video resolution, e.g. '720p', '1080p'
        duration: Video duration in seconds
        first_image_url: URL of the first frame image (SORA2 FIRST&LAST mode)
        last_image_url: URL of the last frame image (SORA2 FIRST&LAST mode)
        generate_audio: Whether to generate audio (True/False)
        scale_factor: Scale factor for SORA2 (e.g. 0.5)
        generation_type: Generation type override, e.g. 'FIRST&LAST', 'TEXT'
        enhance_prompt: Whether to enhance the prompt
        prompt_extend: Whether to extend the prompt
        audio_url: URL of audio file (WAN2.6 series)
        image_url_list: List of image URLs for reference (WAN2.6_R2V)
        video_url_list: List of video URLs for reference (WAN2.6_R2V)
    """
    url = f"{BASE_URL}/AiArtistRecord"

    if model not in MODEL_CONFIGS or MODEL_CONFIGS[model]["media_type"] != "video":
        print(f"不支持的视频模型：{model}", file=sys.stderr)
        return None

    config = MODEL_CONFIGS[model]
    effective_ratio = ratio or config.get("default_ratio", "16:9")
    effective_resolution = resolution or config.get("default_resolution", "720p")
    effective_duration = duration or config.get("default_duration", 10)

    parameter = dict(config["extra_params"])  # copy defaults

    # Resolve pixel size from ratio + resolution
    resolution_size_map = {
        ("16:9", "720p"): "1280x720",
        ("16:9", "1080p"): "1920x1080",
        ("9:16", "720p"): "720x1280",
        ("9:16", "1080p"): "1080x1920",
        ("1:1", "720p"): "720x720",
        ("1:1", "1080p"): "1080x1080",
        ("3:4", "720p"): "720x960",
        ("3:4", "1080p"): "1080x1440",
        ("4:3", "720p"): "960x720",
        ("4:3", "1080p"): "1440x1080",
    }
    pixel_size = resolution_size_map.get((effective_ratio, effective_resolution), effective_ratio)

    parameter.update({
        "methodType": config["methodType"],
        "text": prompt,
        "resolution": effective_resolution,
        "ratio": effective_ratio,
        "size": pixel_size,
        "duration": effective_duration,
    })

    # VEO3.1 series: duration must be 4 or 8 seconds
    if model in ["VEO3.1FAST_LITE", "VEO3.1PRO_LITE", "VEO3.1FAST", "VEO3.1PRO"]:
        # Validate duration (must be 4 or 8)
        if effective_duration not in [4, 8]:
            print(f"VEO3.1 系列模型时长必须是 4 或 8 秒，当前 {effective_duration} 秒，自动调整为 8 秒")
            effective_duration = 8
            parameter["duration"] = effective_duration
        # For VEO3.1, size should match ratio (not pixel resolution)
        parameter["size"] = effective_ratio

    # WAN2.6 series: duration must be 3-15 seconds
    if model in ["WAN2.6_T2V", "WAN2.6_I2V", "WAN2.6_R2V"]:
        # Validate duration (must be 3-15)
        if effective_duration < 3 or effective_duration > 15:
            print(f"WAN2.6 系列模型时长必须是 3-15 秒，当前 {effective_duration} 秒，自动调整为 10 秒")
            effective_duration = 10
            parameter["duration"] = effective_duration
        # For WAN2.6, size should be pixel format for some models
        if model == "WAN2.6_T2V":
            parameter["size"] = f"{pixel_size.replace('x', '*')}"  # e.g., "1280*720"
        elif model == "WAN2.6_I2V":
            parameter["size"] = effective_ratio  # e.g., "16:9"
        elif model == "WAN2.6_R2V":
            parameter["size"] = f"{pixel_size.replace('x', '*')}"  # e.g., "1280*720"

    # SORA2: auto-switch generationType based on image inputs
    if model == "SORA2" and generation_type is None:
        if first_image_url or last_image_url:
            parameter["generationType"] = "FIRST&LAST"
        else:
            parameter["generationType"] = "FIRST&LAST"  # text-to-video also uses FIRST&LAST with null image URLs

    # WAN2.6_I2V: auto-switch generationType based on first_image_url
    if model == "WAN2.6_I2V" and generation_type is None:
        if first_image_url:
            parameter["generationType"] = "FIRST&LAST"
        else:
            parameter["generationType"] = "FIRST&LAST"

    # WAN2.6_R2V: set generationType to REFERENCE
    if model == "WAN2.6_R2V":
        parameter["generationType"] = "REFERENCE"

    # Apply optional overrides
    if first_image_url is not None:
        parameter["firstImageUrl"] = first_image_url
    if last_image_url is not None:
        parameter["lastImageUrl"] = last_image_url
    if generate_audio is not None:
        parameter["generateAudio"] = generate_audio
    if scale_factor is not None:
        parameter["scaleFactor"] = scale_factor
    if generation_type is not None:
        parameter["generationType"] = generation_type
    if enhance_prompt is not None:
        parameter["enhancePrompt"] = enhance_prompt
    if prompt_extend is not None:
        parameter["promptExtend"] = prompt_extend
    # WAN2.6 series: audio_url, image_url_list, video_url_list
    if audio_url is not None:
        parameter["audioUrl"] = audio_url
    if image_url_list is not None:
        parameter["imageUrlList"] = image_url_list
    if video_url_list is not None:
        parameter["videoUrlList"] = video_url_list

    payload = {
        "type": config["type"],
        "methodType": config["methodType"],
        "parameter": json.dumps(parameter)
    }

    if not estimate_generation_cost(payload):
        return None

    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=30)
        response.raise_for_status()
        result = response.json()

        if result.get("code") == 200 and result.get("data"):
            return result["data"][0]
        else:
            print(f"创建视频任务失败：{result.get('msg', '未知错误')}", file=sys.stderr)
            return None

    except requests.exceptions.RequestException as e:
        print(f"网络错误：{e}", file=sys.stderr)
        return None


def generate_video(prompt, model="SEEDANCE_1_5_PRO", ratio=None, resolution=None,
                   duration=None, poll_interval=5, first_image_url=None,
                   last_image_url=None, generate_audio=None, scale_factor=None,
                   generation_type=None, enhance_prompt=None, prompt_extend=None,
                   first_image_path=None, last_image_path=None, audio_url=None,
                   image_url_list=None, video_url_list=None, audio_path=None):
    """Generate a video from a text prompt.

    Args:
        prompt: Text description of the video
        model: Video model to use (e.g. SEEDANCE_1_5_PRO, SORA2)
        ratio: Aspect ratio (e.g. '16:9')
        resolution: Video resolution (e.g. '720p')
        duration: Video duration in seconds
        poll_interval: Polling interval in seconds
        first_image_url: URL of the first frame image (SORA2 FIRST&LAST mode)
        last_image_url: URL of the last frame image (SORA2 FIRST&LAST mode)
        generate_audio: Whether to generate audio
        scale_factor: Scale factor for SORA2
        generation_type: Generation type override
        enhance_prompt: Whether to enhance the prompt
        prompt_extend: Whether to extend the prompt
        first_image_path: Local path to first frame image (auto-uploaded)
        last_image_path: Local path to last frame image (auto-uploaded)
        audio_url: URL of audio file (WAN2.6 series)
        audio_path: Local path to audio file (auto-uploaded, WAN2.6 series)
        image_url_list: List of image URLs for reference (WAN2.6_R2V)
        video_url_list: List of video URLs for reference (WAN2.6_R2V)

    Returns:
        dict with 'status', 'url', 'message'
    """
    # Upload local files to get URLs if provided
    if first_image_path and not first_image_url:
        first_image_url = upload_file(first_image_path)
    if last_image_path and not last_image_url:
        last_image_url = upload_file(last_image_path)
    if audio_path and not audio_url:
        audio_url = upload_file(audio_path)
    
    config = MODEL_CONFIGS.get(model, {})
    effective_ratio = ratio or config.get("default_ratio", "16:9")
    effective_resolution = resolution or config.get("default_resolution", "720p")
    effective_duration = duration or config.get("default_duration", 10)

    print(f"正在生成视频：{prompt}")
    print(f"   模型：{model} | 分辨率：{effective_resolution} | 比例：{effective_ratio} | 时长：{effective_duration}s")
    if first_image_url:
        print(f"   首帧图片：{first_image_url}")
    if last_image_url:
        print(f"   尾帧图片：{last_image_url}")
    if audio_url:
        print(f"   音频：{audio_url}")
    if image_url_list:
        print(f"   参考图片：{image_url_list}")
    if video_url_list:
        print(f"   参考视频：{video_url_list}")

    task_id = create_video_task(
        prompt, model, ratio, resolution, duration,
        first_image_url=first_image_url,
        last_image_url=last_image_url,
        generate_audio=generate_audio,
        scale_factor=scale_factor,
        generation_type=generation_type,
        enhance_prompt=enhance_prompt,
        prompt_extend=prompt_extend,
        audio_url=audio_url,
        image_url_list=image_url_list,
        video_url_list=video_url_list
    )
    if not task_id:
        return None

    print(f"   任务 ID: {task_id}")

    result = poll_task_status(task_id, interval=poll_interval, max_wait=600)

    if result and result["status"] == "SUCCESS":
        print(f"视频生成成功!")
        print(f"   视频链接：{result['url']}")
    else:
        print(f"视频生成失败：{result.get('message', '未知错误')}", file=sys.stderr)

    return result


def create_generation_task(prompt, quality="2K", size=None, model="SEEDREAM5_0", reference_image_url=None):
    """Create an image generation task.
    
    Args:
        prompt: Text description of the image
        quality: Image quality (2K/4K)
        size: Image dimensions. SEEDREAM5_0 uses e.g. '2048x2048', NANO_BANANA_2 uses e.g. '1:1'
        model: Model to use, one of: SEEDREAM5_0, NANO_BANANA_2
        reference_image_url: Optional reference image URL for image-to-image generation
    """
    url = f"{BASE_URL}/AiArtistRecord"
    
    if model not in MODEL_CONFIGS:
        print(f"不支持的模型：{model}，可用模型：{list(MODEL_CONFIGS.keys())}", file=sys.stderr)
        return None
    
    config = MODEL_CONFIGS[model]
    
    # Use model's default size if not specified
    if size is None:
        size = config["default_size"]
    
    # Build image array - support reference image for image-to-image
    image_array = []
    if reference_image_url:
        image_array = [reference_image_url]
    
    parameter = {
        "methodType": config["methodType"],
        "prompt": prompt,
        "image": image_array,
        "quality": quality,
        "size": size,
        "webSearch": False,
        "targetMaxSize": 10,
        "targetMaxLength": 6000,
    }
    # Merge model-specific extra params
    parameter.update(config["extra_params"])
    
    payload = {
        "type": config["type"],
        "methodType": config["methodType"],
        "parameter": json.dumps(parameter)
    }
    
    if not estimate_generation_cost(payload):
        return None
    
    try:
        response = requests.post(url, json=payload, headers=get_headers(), timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") == 200 and result.get("data"):
            return result["data"][0]
        else:
            print(f"创建任务失败：{result.get('msg', '未知错误')}", file=sys.stderr)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"网络错误：{e}", file=sys.stderr)
        return None


def poll_task_status(task_id, interval=5, max_wait=600):
    """Poll the task status until completion or failure."""
    url = f"{BASE_URL}/AiArtistImage/getInfoByArtistId/{task_id}"
    
    elapsed = 0
    last_status = None
    
    while elapsed < max_wait:
        try:
            response = requests.get(url, headers=get_headers(), timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 200:
                time.sleep(interval)
                elapsed += interval
                continue
            
            data = result.get("data", {})
            status = data.get("status", "")
            
            # Only print status when it changes
            if status != last_status:
                print(f"{status} - {data.get('message', '')}")
                last_status = status
            
            if status == "SUCCESS":
                return {
                    "status": "SUCCESS",
                    "url": data.get("url"),
                    "message": data.get("message", "生成成功")
                }
            elif status == "FAILED":
                return {
                    "status": "FAILED",
                    "url": None,
                    "message": data.get("message", "生成失败")
                }
            else:
                time.sleep(interval)
                elapsed += interval
                
        except requests.exceptions.RequestException as e:
            print(f"查询状态出错：{e}", file=sys.stderr)
            time.sleep(interval)
            elapsed += interval
    
    return {
        "status": "TIMEOUT",
        "url": None,
        "message": f"超时（{max_wait}秒）"
    }


def generate_image(prompt, quality="2K", size=None, poll_interval=5,
                   download=False, output_dir=None, model="SEEDREAM5_0",
                   reference_image_path=None, reference_image_url=None):
    """
    Main function to generate an image from a prompt.
    
    Args:
        prompt: Text description of the image
        quality: Image quality (2K/4K)
        size: Image dimensions. Defaults to model's default size if not specified.
              SEEDREAM5_0: e.g. '2048x2048' | NANO_BANANA_2: e.g. '1:1'
        poll_interval: Polling interval in seconds
        download: Whether to download the image
        output_dir: Directory to save the image (default: workspace/images)
        model: Model to use. Options: SEEDREAM5_0, NANO_BANANA_2
        reference_image_path: Local path to reference image (auto-uploaded)
        reference_image_url: URL of reference image (if already uploaded)
    
    Returns:
        dict with generation result including 'url', 'local_path', 'data_uri' if successful
    """
    config = MODEL_CONFIGS.get(model, {})
    effective_size = size or config.get("default_size", "2048x2048")

    # Upload reference image if local path provided
    if reference_image_path and not reference_image_url:
        reference_image_url = upload_file(reference_image_path)

    print(f"正在生成：{prompt}")
    print(f"   模型：{model} | 质量：{quality} | 尺寸：{effective_size}")
    if reference_image_url:
        print(f"   参考图：{reference_image_url}")
    
    # Step 1: Create task
    task_id = create_generation_task(prompt, quality, size, model, reference_image_url)
    if not task_id:
        return None
    
    print(f"   任务 ID: {task_id}")
    
    # Step 2: Poll until complete
    result = poll_task_status(task_id, interval=poll_interval)
    
    if result and result["status"] == "SUCCESS":
        print(f"生成成功!")
        print(f"   图片链接：{result['url']}")
        
        # Download image if requested
        if download and result.get("url"):
            if not output_dir:
                output_dir = os.path.join(os.path.expanduser("~"), ".openclaw", "workspace", "images")
            
            # Generate filename from prompt
            safe_prompt = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in prompt)
            safe_prompt = safe_prompt[:50].strip().replace(' ', '_')
            filename = f"{safe_prompt}_{int(time.time())}.png"
            output_path = os.path.join(output_dir, filename)
            
            image_data = download_image(result["url"], output_path)
            if image_data:
                result["local_path"] = output_path
                result["data_uri"] = image_to_data_uri(image_data)
                result["image_data"] = image_data  # Raw bytes for programmatic use
        
        return result
    else:
        print(f"生成失败：{result.get('message', '未知错误')}", file=sys.stderr)
        return result


if __name__ == "__main__":
    # Check API key before proceeding
    check_api_key()

    image_models = [k for k, v in MODEL_CONFIGS.items() if v["media_type"] == "image"]
    video_models = [k for k, v in MODEL_CONFIGS.items() if v["media_type"] == "video"]
    all_models = list(MODEL_CONFIGS.keys())

    parser = argparse.ArgumentParser(
        description="AI 图片/视频生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"图片模型：{', '.join(image_models)}\n视频模型：{', '.join(video_models)}"
    )
    parser.add_argument("prompt", help="生成提示词")
    parser.add_argument("--model", default="SEEDREAM5_0",
                        choices=all_models,
                        help="生成模型 (默认：SEEDREAM5_0)")
    # 图片专属参数
    parser.add_argument("--quality", default="2K", help="[图片] 图片质量 (默认：2K)")
    parser.add_argument("--size", default=None, help="[图片] 图片尺寸，不传则使用模型默认值")
    parser.add_argument("--download", action="store_true", help="[图片] 下载图片到本地")
    parser.add_argument("--output-dir", help="[图片] 图片保存目录")
    parser.add_argument("--markdown-output", action="store_true", help="以 Markdown 格式输出图片链接")
    parser.add_argument("--reference-image", default=None, help="[图片] 参考图本地路径，自动上传后作为 image-to-image 参考")
    # 视频专属参数
    parser.add_argument("--ratio", default=None, help="[视频] 画面比例，如 16:9、9:16、1:1 (默认：16:9)")
    parser.add_argument("--resolution", default=None, help="[视频] 分辨率，如 720p、1080p (默认：720p)")
    parser.add_argument("--duration", type=int, default=None, help="[视频] 视频时长 (秒) (默认：10)")
    # SORA2 专属参数
    parser.add_argument("--first-image-url", default=None, help="[SORA2] 首帧图片 URL（FIRST&LAST 模式）")
    parser.add_argument("--last-image-url", default=None, help="[SORA2] 尾帧图片 URL（FIRST&LAST 模式）")
    parser.add_argument("--first-image", default=None, help="[SORA2] 首帧图片本地路径，自动上传")
    parser.add_argument("--last-image", default=None, help="[SORA2] 尾帧图片本地路径，自动上传")
    parser.add_argument("--generate-audio", action="store_true", default=None, help="[SORA2] 生成音频")
    parser.add_argument("--no-audio", action="store_true", help="[SORA2] 不生成音频")
    parser.add_argument("--scale-factor", type=float, default=None, help="[SORA2] 缩放系数 (默认：0.5)")
    parser.add_argument("--generation-type", default=None, help="[SORA2] 生成类型，如 FIRST&LAST、TEXT")
    # 通用参数
    parser.add_argument("--interval", type=int, default=5, help="轮询间隔秒数")

    args = parser.parse_args()

    media_type = MODEL_CONFIGS[args.model]["media_type"]

    if media_type == "video":
        # Resolve audio flag
        gen_audio = None
        if args.no_audio:
            gen_audio = False
        elif args.generate_audio:
            gen_audio = True

        result = generate_video(
            prompt=args.prompt,
            model=args.model,
            ratio=args.ratio,
            resolution=args.resolution,
            duration=args.duration,
            poll_interval=args.interval,
            first_image_url=args.first_image_url,
            last_image_url=args.last_image_url,
            first_image_path=args.first_image,
            last_image_path=args.last_image,
            generate_audio=gen_audio,
            scale_factor=args.scale_factor,
            generation_type=args.generation_type
        )
        if result and result["status"] == "SUCCESS" and result.get("url"):
            print(result["url"])
            sys.exit(0)
        elif result:
            sys.exit(0 if result["status"] == "SUCCESS" else 1)
        else:
            sys.exit(1)
    else:
        result = generate_image(
            prompt=args.prompt,
            quality=args.quality,
            size=args.size,
            poll_interval=args.interval,
            download=args.download,
            output_dir=args.output_dir,
            model=args.model,
            reference_image_path=args.reference_image
        )

        # Send result to Feishu if webhook is configured
        if FEISHU_WEBHOOK_URL:
            send_feishu_message(args.prompt, result)

        # Output based on --markdown-output flag
        if args.markdown_output and result and result["status"] == "SUCCESS" and result.get("url"):
            print(f"![{args.prompt}]({result['url']})")
            sys.exit(0)
        elif result and result["status"] == "SUCCESS" and result.get("url"):
            print(result["url"])
            sys.exit(0)
        elif result:
            sys.exit(0 if result["status"] == "SUCCESS" else 1)
        else:
            sys.exit(1)
