#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
media-extractor.py - 视频/音频转写模块

从 YouTube 等平台下载视频并转写为文本。

支持的 ASR Provider:
  1. 阿里云 NLS（优先）
  2. 本地 mlx_whisper（降级）
  3. 降级模式（仅抓取标题/字幕/描述）

依赖:
  - yt-dlp: 视频下载
  - ffmpeg: 音频格式转换
  - requests: HTTP 请求
  - mlx_whisper (可选): 本地转写

用法:
  python3 scripts/media-extractor.py --url "https://youtu.be/xxx" --output /tmp/transcript.txt
  python3 scripts/media-extractor.py --url "https://youtu.be/xxx" --json
  python3 scripts/media-extractor.py --url "https://youtu.be/xxx" --provider aliyun-nls
  python3 scripts/media-extractor.py --check
  python3 scripts/media-extractor.py --url "https://youtu.be/xxx" --info-only
"""

import argparse
import atexit
import base64
import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

import requests

# ============================================================================
# 全局变量
# ============================================================================

# 临时文件列表，用于退出时清理
_temp_files = []
_temp_dirs = []


def _cleanup():
    """清理临时文件"""
    for f in _temp_files:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception:
            pass
    for d in _temp_dirs:
        try:
            if os.path.exists(d):
                shutil.rmtree(d)
        except Exception:
            pass


atexit.register(_cleanup)


def _add_temp_file(path: str):
    """注册临时文件"""
    _temp_files.append(path)


def _add_temp_dir(path: str):
    """注册临时目录"""
    _temp_dirs.append(path)


# ============================================================================
# 工具函数
# ============================================================================


def get_available_memory_gb() -> float:
    """
    获取 macOS 可用内存（GB）

    使用 vm_stat 命令获取页面信息，计算可用内存。
    """
    try:
        result = subprocess.run(
            ["vm_stat"],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout

        # 解析 vm_stat 输出
        # Pages free: xxxxxx.
        # Pages active: xxxxxx.
        free_match = re.search(r"Pages free:\s+(\d+)", output)
        active_match = re.search(r"Pages active:\s+(\d+)", output)
        inactive_match = re.search(r"Pages inactive:\s+(\d+)", output)
        speculative_match = re.search(r"Pages speculative:\s+(\d+)", output)

        # macOS 页面大小（ARM Mac 为 16384 字节）
        page_size = 16384

        free_pages = int(free_match.group(1)) if free_match else 0
        active_pages = int(active_match.group(1)) if active_match else 0
        inactive_pages = int(inactive_match.group(1)) if inactive_match else 0
        speculative_pages = int(speculative_match.group(1)) if speculative_match else 0

        # 可用内存 = free + inactive + speculative（更准确的可用内存估算）
        available_pages = free_pages + inactive_pages + speculative_pages
        available_bytes = available_pages * page_size
        available_gb = available_bytes / (1024 ** 3)

        return round(available_gb, 2)
    except Exception:
        return 0.0


def check_command_exists(cmd: str) -> bool:
    """检查命令是否存在"""
    return shutil.which(cmd) is not None


def format_duration(seconds: int) -> str:
    """将秒数格式化为 HH:MM:SS 格式"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


# ============================================================================
# ASR Provider 检测
# ============================================================================


def check_mlx_whisper() -> dict:
    """
    检测 mlx_whisper 是否可用

    Returns:
        dict: {"available": bool, "reason": str, "model": str or None}
    """
    result = {
        "available": False,
        "reason": "",
        "model": None,
        "memory_gb": 0.0
    }

    # 检查是否已安装 mlx_whisper
    try:
        import mlx_whisper
        result["available"] = True
    except ImportError:
        result["reason"] = "mlx_whisper not installed"
        return result

    # 检查 Apple Silicon
    import platform
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        result["available"] = False
        result["reason"] = "mlx_whisper requires Apple Silicon (arm64)"
        return result

    # 检查可用内存
    memory_gb = get_available_memory_gb()
    result["memory_gb"] = memory_gb

    if memory_gb < 6:
        result["available"] = False
        result["reason"] = f"Insufficient memory ({memory_gb:.1f}GB < 6GB required)"
        return result

    # 根据内存选择模型
    if memory_gb >= 10:
        result["model"] = "mlx-community/whisper-large-v3"
    elif memory_gb >= 6:
        result["model"] = "mlx-community/whisper-medium"
    else:
        result["available"] = False
        result["reason"] = f"Insufficient memory ({memory_gb:.1f}GB < 6GB required)"

    return result


def check_aliyun_nls() -> dict:
    """
    检测阿里云 NLS 是否可用

    Returns:
        dict: {"available": bool, "has_appkey": bool, "has_access_key": bool}
    """
    result = {
        "available": False,
        "has_appkey": False,
        "has_access_key": False
    }

    appkey = os.environ.get("ALIYUN_NLS_APPKEY", "")
    access_key_id = os.environ.get("ALIYUN_ACCESS_KEY_ID", "")
    access_key_secret = os.environ.get("ALIYUN_ACCESS_KEY_SECRET", "")

    result["has_appkey"] = bool(appkey)
    result["has_access_key"] = bool(access_key_id and access_key_secret)
    result["available"] = result["has_appkey"] and result["has_access_key"]

    return result


def check_all_providers() -> dict:
    """
    检查所有 ASR Provider 的可用性

    Returns:
        dict: 包含各 provider 状态的字典
    """
    aliyun = check_aliyun_nls()
    mlx = check_mlx_whisper()

    # 推荐 provider
    recommended = None
    message = ""

    if aliyun["available"]:
        recommended = "aliyun-nls"
        message = "ASR 可用。将使用阿里云 NLS 进行语音转写。"
    elif mlx["available"]:
        recommended = "mlx-whisper"
        message = f"ASR 可用。将使用 mlx_whisper ({mlx['model']}) 进行语音转写。"
    else:
        message = "未检测到 ASR 配置。视频转写需要以下任一服务："

    return {
        "aliyun_nls": aliyun,
        "mlx_whisper": mlx,
        "recommended": recommended,
        "message": message
    }


def print_provider_guidance():
    """打印 ASR 配置引导信息到 stderr"""
    guidance = """
⚠️ 未检测到 ASR 配置。视频转写需要以下任一服务：

方案 A（推荐）：阿里云 NLS（¥0.14/30分钟）
- 注册阿里云 → 开通智能语音交互 → 获取 AppKey + AccessKey
- 配置环境变量：ALIYUN_NLS_APPKEY, ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET

方案 B（免费）：本地 mlx_whisper（需 Apple Silicon + 5GB 内存）
- pip install mlx-whisper

未配置 ASR 时，将尝试抓取视频标题、字幕、描述等可用信息。
"""
    print(guidance, file=sys.stderr)


# ============================================================================
# 阿里云 NLS 相关函数
# ============================================================================


def get_nls_token(access_key_id: str, access_key_secret: str) -> str:
    """
    获取阿里云 NLS Token（使用 AccessKey 签名方式）

    Args:
        access_key_id: 阿里云 AccessKey ID
        access_key_secret: 阿里云 AccessKey Secret

    Returns:
        str: NLS Token ID

    Raises:
        Exception: 获取失败时抛出异常
    """
    params = {
        "AccessKeyId": access_key_id,
        "Action": "CreateToken",
        "Format": "JSON",
        "RegionId": "cn-shanghai",
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": str(uuid.uuid4()),
        "SignatureVersion": "1.0",
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "Version": "2019-02-28",
    }

    # 按字母顺序排序参数
    sorted_params = sorted(params.items())
    query_string = urllib_parse_urlencode(sorted_params)

    # 构建待签名字符串
    string_to_sign = "GET&%2F&" + urllib_parse_quote(query_string, safe="")

    # 计算签名
    signature = base64.b64encode(
        hmac.new(
            (access_key_secret + "&").encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1
        ).digest()
    ).decode("utf-8")

    params["Signature"] = signature

    # 构建请求 URL
    url = "https://nls-meta.cn-shanghai.aliyuncs.com/?" + urllib_parse_urlencode(params)

    # 发送请求
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "Token" in data and "Id" in data["Token"]:
            return data["Token"]["Id"]
        else:
            raise Exception(f"获取 Token 失败: {data}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"获取 NLS Token 网络请求失败: {e}")


def urllib_parse_urlencode(params):
    """兼容的 url_encode 实现"""
    import urllib.parse
    return urllib.parse.urlencode(params)


def urllib_parse_quote(s, safe=""):
    """兼容的 quote 实现"""
    import urllib.parse
    return urllib.parse.quote(s, safe=safe)


def split_audio_chunks(wav_path: str, chunk_duration: int = 55) -> list:
    """
    将 WAV 音频文件按指定时长分割

    Args:
        wav_path: WAV 文件路径
        chunk_duration: 每段时长（秒），默认 55 秒

    Returns:
        list: 每段音频文件的路径列表
    """
    # 获取音频总时长
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", wav_path],
        capture_output=True,
        text=True,
        timeout=30
    )
    total_duration = float(result.stdout.strip())

    chunks = []
    temp_dir = tempfile.mkdtemp(prefix="arc-chunks-")
    _add_temp_dir(temp_dir)

    # 按 chunk_duration 分割
    start = 0.0
    chunk_idx = 0
    while start < total_duration:
        end = min(start + chunk_duration, total_duration)
        chunk_path = os.path.join(temp_dir, f"chunk_{chunk_idx:04d}.wav")

        cmd = [
            "ffmpeg", "-y",
            "-i", wav_path,
            "-ss", str(start),
            "-t", str(end - start),
            "-ar", "16000",
            "-ac", "1",
            "-acodec", "pcm_s16le",
            chunk_path
        ]

        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        chunks.append(chunk_path)
        start = end
        chunk_idx += 1

    return chunks


def transcribe_audio_chunk(token: str, app_key: str, audio_path: str) -> str:
    """
    转写单个音频片段（调用阿里云一句话识别 API）

    Args:
        token: NLS Token
        app_key: 阿里云 AppKey
        audio_path: 音频文件路径

    Returns:
        str: 识别文本

    Raises:
        Exception: API 调用失败时抛出异常
    """
    endpoint = "https://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/asr"

    headers = {
        "X-NLS-Token": token,
        "Content-Type": "application/octet-stream"
    }

    params = {
        "appkey": app_key,
        "format": "wav",
        "sample_rate": "16000",
        "enable_punctuation_prediction": "true",
        "enable_inverse_text_normalization": "true"
    }

    try:
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        resp = requests.post(
            endpoint,
            headers=headers,
            params=params,
            data=audio_data,
            timeout=30
        )
        resp.raise_for_status()

        data = resp.json()

        if "result" in data:
            return data["result"]
        else:
            # 可能返回其他格式，尝试直接返回
            return str(data.get("text", ""))

    except requests.exceptions.Timeout:
        raise Exception("NLS API 请求超时（30秒）")
    except requests.exceptions.RequestException as e:
        raise Exception(f"NLS API 请求失败: {e}")


def transcribe_aliyun_nls(wav_path: str) -> str:
    """
    使用阿里云 NLS 转写 WAV 音频

    Args:
        wav_path: WAV 文件路径（16kHz mono）

    Returns:
        str: 完整转写文本
    """
    access_key_id = os.environ.get("ALIYUN_ACCESS_KEY_ID")
    access_key_secret = os.environ.get("ALIYUN_ACCESS_KEY_SECRET")
    app_key = os.environ.get("ALIYUN_NLS_APPKEY")

    if not all([access_key_id, access_key_secret, app_key]):
        raise Exception("缺少阿里云 NLS 环境变量")

    # 1. 获取 Token
    print("正在获取阿里云 NLS Token...", file=sys.stderr)
    token = get_nls_token(access_key_id, access_key_secret)

    # 2. 分割音频
    print("正在分割音频（每段 55 秒）...", file=sys.stderr)
    chunks = split_audio_chunks(wav_path, chunk_duration=55)
    print(f"共分割为 {len(chunks)} 个片段", file=sys.stderr)

    # 3. 逐段转写
    results = []
    for i, chunk in enumerate(chunks):
        print(f"\r转写中: {i + 1}/{len(chunks)}", end="", file=sys.stderr)
        sys.stderr.flush()

        try:
            text = transcribe_audio_chunk(token, app_key, chunk)
            if text:
                results.append(text)
        except Exception as e:
            print(f"\n片段 {i + 1} 转写失败: {e}", file=sys.stderr)
            # 继续处理下一段

    print("", file=sys.stderr)  # 换行

    # 4. 拼接结果
    full_text = " ".join(results)
    return full_text


# ============================================================================
# mlx_whisper 转写
# ============================================================================


def transcribe_mlx_whisper(wav_path: str) -> str:
    """
    使用 mlx_whisper 转写音频

    Args:
        wav_path: WAV 文件路径

    Returns:
        str: 转写文本
    """
    import mlx_whisper

    memory_gb = get_available_memory_gb()
    if memory_gb >= 10:
        model_path = "mlx-community/whisper-large-v3"
    elif memory_gb >= 6:
        model_path = "mlx-community/whisper-medium"
    else:
        raise Exception(f"内存不足（{memory_gb:.1f}GB），无法使用 mlx_whisper")

    print(f"正在使用 mlx_whisper ({model_path}) 转写...", file=sys.stderr)

    result = mlx_whisper.transcribe(
        wav_path,
        language="zh",
        path_or_hf_repo=model_path
    )

    return result.get("text", "")


# ============================================================================
# 视频下载与信息获取
# ============================================================================


def get_video_info(url: str) -> dict:
    """
    获取视频信息（标题、描述、时长、字幕等）

    Args:
        url: 视频 URL

    Returns:
        dict: 视频信息
    """
    temp_dir = tempfile.mkdtemp(prefix="arc-info-")
    _add_temp_dir(temp_dir)
    info_file = os.path.join(temp_dir, "info.json")

    # 使用 yt-dlp 命令行工具（独立安装）
    ytdlp_cmd = shutil.which("yt-dlp")
    if not ytdlp_cmd:
        ytdlp_cmd = "yt-dlp"  # fallback to PATH

    cmd = [
        ytdlp_cmd,
        "--dump-json",
        "--no-download",
        "--no-warnings",
        url
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"获取视频信息失败: {result.stderr}", file=sys.stderr)
            return {}

        # 尝试解析输出
        try:
            info = json.loads(result.stdout.strip().split("\n")[-1])
        except json.JSONDecodeError:
            # 可能输出包含多行，尝试最后一行
            lines = result.stdout.strip().split("\n")
            for line in reversed(lines):
                if line.strip().startswith("{"):
                    try:
                        info = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue
            else:
                return {}

        # 提取自动字幕（优先中文）
        subtitles = {}
        if "subtitles" in info:
            subtitles = info.get("subtitles", {})
        elif "automatic_captions" in info:
            subtitles = info.get("automatic_captions", {})

        auto_subtitle = None
        # 优先找中文相关字幕
        for lang in ["zh-Hans", "zh-CN", "zh", "zh-TW", "en"]:
            if lang in subtitles and subtitles[lang]:
                # 获取字幕内容
                sub_url = subtitles[lang][0].get("url")
                if sub_url:
                    try:
                        sub_resp = requests.get(sub_url, timeout=30)
                        sub_resp.raise_for_status()
                        auto_subtitle = sub_resp.text
                        break
                    except Exception:
                        continue

        return {
            "title": info.get("title", ""),
            "description": info.get("description", ""),
            "duration": info.get("duration", 0),
            "url": info.get("webpage_url", url),
            "thumbnail": info.get("thumbnail", ""),
            "subtitles": auto_subtitle,
            "full_info": info
        }

    except subprocess.TimeoutExpired:
        print("获取视频信息超时（60秒）", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"获取视频信息异常: {e}", file=sys.stderr)
        return {}


def download_audio(url: str) -> tuple:
    """
    下载视频音频并转换为 16kHz mono WAV

    Args:
        url: 视频 URL

    Returns:
        tuple: (wav_path, video_info)

    Raises:
        Exception: 下载或转换失败时抛出异常
    """
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="arc-audio-")
    _add_temp_dir(temp_dir)

    # 下载音频为 WAV
    raw_wav = os.path.join(temp_dir, "raw_audio.wav")
    _add_temp_file(raw_wav)

    print("正在下载音频...", file=sys.stderr)

    # 步骤 1: 用 yt-dlp 下载为 wav
    ytdlp_cmd = shutil.which("yt-dlp")
    if not ytdlp_cmd:
        ytdlp_cmd = "yt-dlp"

    cmd1 = [
        ytdlp_cmd,
        "-x",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", raw_wav,
        "--no-warnings",
        url
    ]

    result = subprocess.run(
        cmd1,
        capture_output=True,
        text=True,
        timeout=120  # 下载超时 2 分钟
    )

    if result.returncode != 0:
        raise Exception(f"音频下载失败: {result.stderr}")

    # yt-dlp 可能输出文件为 .wav.wav 或其他扩展名，查找实际文件
    actual_files = list(Path(temp_dir).glob("*.wav"))
    if actual_files:
        raw_wav = str(actual_files[0])
    elif not os.path.exists(raw_wav):
        raise Exception(f"音频文件未找到: {raw_wav}")

    # 步骤 2: 用 ffmpeg 转换为 16kHz mono WAV
    final_wav = os.path.join(temp_dir, "audio_16k.wav")
    _add_temp_file(final_wav)

    print("正在转换音频格式...", file=sys.stderr)

    cmd2 = [
        "ffmpeg",
        "-y",
        "-i", raw_wav,
        "-ar", "16000",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        final_wav
    ]

    result2 = subprocess.run(
        cmd2,
        capture_output=True,
        text=True,
        timeout=120  # 转换超时 2 分钟
    )

    if result2.returncode != 0:
        raise Exception(f"音频格式转换失败: {result2.stderr}")

    # 获取视频信息
    video_info = get_video_info(url)

    return final_wav, video_info


# ============================================================================
# 主转写函数
# ============================================================================


def transcribe(url: str, provider: str = "auto") -> dict:
    """
    转写视频音频

    Args:
        url: 视频 URL
        provider: ASR Provider ("auto", "aliyun-nls", "mlx-whisper", "fallback")

    Returns:
        dict: 转写结果
    """
    result = {
        "status": "pending",
        "provider": provider,
        "source_url": url,
        "title": "",
        "duration_seconds": 0,
        "transcript": "",
        "word_count": 0,
        "cost_estimate": "",
        "error": ""
    }

    # 检查 provider 可用性
    if provider == "auto":
        providers = check_all_providers()
        if providers["recommended"]:
            provider = providers["recommended"]
        else:
            print_provider_guidance()
            provider = "fallback"

    # 下载音频
    try:
        wav_path, video_info = download_audio(url)
        result["title"] = video_info.get("title", "")
        result["duration_seconds"] = video_info.get("duration", 0)
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"音频下载失败: {e}"
        return result

    # 根据 provider 转写
    try:
        if provider == "aliyun-nls":
            transcript = transcribe_aliyun_nls(wav_path)
            result["provider"] = "aliyun-nls"
            # 估算费用：约 ¥0.14/30分钟
            duration_min = result["duration_seconds"] / 60
            cost = 0.14 * (duration_min / 30)
            result["cost_estimate"] = f"{cost:.2f} CNY"

        elif provider == "mlx-whisper":
            transcript = transcribe_mlx_whisper(wav_path)
            result["provider"] = "mlx-whisper"
            result["cost_estimate"] = "0.00 CNY (本地)"

        else:
            # 降级模式：尝试使用字幕或描述
            transcript = ""

            # 尝试使用自动字幕
            if video_info.get("subtitles"):
                # 解析 srt/vtt 字幕为纯文本
                sub_text = video_info["subtitles"]
                # VTT 格式处理
                if sub_text.startswith("WEBVTT"):
                    lines = sub_text.split("\n")
                    for line in lines:
                        # 跳过时间码和标签
                        if "-->" in line or line.strip().startswith("-"):
                            continue
                        if line.strip() and not line.strip().startswith(">"):
                            transcript += " " + line.strip()
                else:
                    transcript = sub_text
                transcript = re.sub(r"<[^>]+>", "", transcript)
                transcript = re.sub(r"\s+", " ", transcript).strip()

            # 如果没有字幕，使用描述
            if not transcript and video_info.get("description"):
                transcript = video_info["description"]
                # 截取前 5000 字符
                transcript = transcript[:5000]

            result["provider"] = "fallback"
            result["cost_estimate"] = "0.00 CNY (字幕/描述)"

        result["transcript"] = transcript
        result["word_count"] = len(transcript.replace(" ", ""))
        result["status"] = "success"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


# ============================================================================
# CLI 接口
# ============================================================================


def cmd_check():
    """检查 ASR Provider 可用性"""
    result = check_all_providers()

    # 如果没有可用 provider，打印引导
    if not result["recommended"]:
        print_provider_guidance()

    # 输出 JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_info(url: str):
    """获取视频信息（不转写）"""
    info = get_video_info(url)

    if not info:
        print(json.dumps({
            "status": "error",
            "error": "无法获取视频信息"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 简化输出
    output = {
        "status": "success",
        "title": info.get("title", ""),
        "description": info.get("description", ""),
        "duration_seconds": info.get("duration", 0),
        "duration_formatted": format_duration(info.get("duration", 0)),
        "url": info.get("url", url),
        "has_subtitles": bool(info.get("subtitles"))
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_transcribe(url: str, output_file: Optional[str], json_output: bool, provider: str):
    """转写视频"""
    result = transcribe(url, provider)

    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 纯文本输出
        if result["status"] == "success":
            if result["title"]:
                print(f"# {result['title']}")
                print()
            print(result["transcript"])
        else:
            print(f"转写失败: {result.get('error', '未知错误')}", file=sys.stderr)
            sys.exit(1)

    # 写入文件
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["transcript"])
        print(f"转写结果已保存到: {output_file}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="视频/音频转写工具 - 从 YouTube 等平台下载视频并转写为文本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 scripts/media-extractor.py --check
  python3 scripts/media-extractor.py --url "https://youtu.be/xxx" --json
  python3 scripts/media-extractor.py --url "https://youtu.be/xxx" --output /tmp/transcript.txt
  python3 scripts/media-extractor.py --url "https://youtu.be/xxx" --provider aliyun-nls
  python3 scripts/media-extractor.py --url "https://youtu.be/xxx" --info-only
        """
    )

    parser.add_argument(
        "--url",
        type=str,
        help="视频 URL（支持 YouTube 等平台）"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出文件路径（转写文本）"
    )

    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="输出 JSON 格式（含元数据）"
    )

    parser.add_argument(
        "--provider", "-p",
        type=str,
        default="auto",
        choices=["auto", "aliyun-nls", "mlx-whisper", "fallback"],
        help="ASR Provider（默认 auto）"
    )

    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="检查 ASR Provider 可用性"
    )

    parser.add_argument(
        "--info-only", "-i",
        action="store_true",
        help="仅获取视频信息（不转写）"
    )

    args = parser.parse_args()

    # 检查命令依赖
    if not check_command_exists("ffmpeg"):
        print("错误: 未找到 ffmpeg，请先安装: brew install ffmpeg", file=sys.stderr)
        sys.exit(1)

    if not check_command_exists("yt-dlp"):
        print("错误: 未找到 yt-dlp，请先安装: pip install yt-dlp", file=sys.stderr)
        sys.exit(1)

    # 执行对应命令
    if args.check:
        cmd_check()
    elif args.info_only:
        if not args.url:
            parser.error("--info-only 需要指定 --url")
        cmd_info(args.url)
    elif args.url:
        cmd_transcribe(args.url, args.output, args.json, args.provider)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
