#!/usr/bin/env python3
"""
huiji / get-transcript 统一入口脚本

用途：智能获取会议转写原文，自动处理缓存（全量/增量切换 + 二次改写）

AI 只需调用此脚本，无需关心底层接口差异：
  python3 get-transcript.py <meetingChatId> [--name "会议名称"]

双缓存机制：
  - {chatId}_live.json  — 进行中的实时数据（splitRecordList 全量 + splitRecordListV2 增量）
  - {chatId}_final.json — 结束后的二次改写数据（checkSecondSttV2，质量更高）

优先级：_final > _live > 全量拉取
  - _final 存在 → 直接返回（最优质量）
  - _live 存在 + 进行中 → 增量拉取合并
  - _live 存在 + 已结束 → 尝试拉二次改写 → 写 _final
  - 无缓存 → 全量拉取 → 写 _live

环境变量：
  XG_BIZ_API_KEY   — appKey（必须）
  XG_USER_TOKEN    — access-token（可选）
"""

import sys
import os
import json
import time
from datetime import datetime, timezone, timedelta
import requests
import warnings

# 禁用 InsecureRequestWarning (因为 verify=False)
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)


def setup_utf8_stdio():
    """Best-effort UTF-8 stdio for Windows console display."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


setup_utf8_stdio()

TZ = timezone(timedelta(hours=8))


# 接口地址
API_FULL = "https://sg-al-ai-voice-assistant.mediportal.com.cn/api/open-api/ai-huiji/meetingChat/splitRecordList"
API_INCR = "https://sg-al-ai-voice-assistant.mediportal.com.cn/api/open-api/ai-huiji/meetingChat/splitRecordListV2"
API_SECOND_STT = "https://sg-al-ai-voice-assistant.mediportal.com.cn/api/open-api/ai-huiji/meetingChat/checkSecondSttV2"

MAX_RETRIES = 3
RETRY_DELAY = 1
CACHE_EXPIRE_DAYS = 15  # 缓存过期天数，超过此天数的已结束会议缓存自动清理

# 缓存目录：skill 根目录下的 .cache/huiji/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CACHE_DIR = os.path.join(SKILL_ROOT, ".cache", "huiji")


def build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("XG_USER_TOKEN")
    app_key = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if token:
        headers["access-token"] = token
    if app_key:
        headers["appKey"] = app_key
    if not token and not app_key:
        print(json.dumps({"error": "请至少设置 XG_USER_TOKEN 或 XG_BIZ_API_KEY"}, ensure_ascii=False))
        sys.exit(1)
    return headers


def call_api(url: str, body: dict) -> dict:
    headers = build_headers()
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                url,
                json=body,
                headers=headers,
                verify=False,
                allow_redirects=True,
                timeout=60,
            )
            response.raise_for_status()
            return json.loads(response.content.decode("utf-8"))
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    print(json.dumps({"error": f"请求失败（重试{MAX_RETRIES}次）: {last_err}"}, ensure_ascii=False))
    sys.exit(1)


def cache_path(chat_id: str, suffix: str = "") -> str:
    """获取缓存文件路径：_live / _final"""
    return os.path.join(CACHE_DIR, f"{chat_id}{suffix}.json")


def load_cache(chat_id: str, suffix: str = "") -> dict:
    """加载缓存，不存在返回 None"""
    path = cache_path(chat_id, suffix)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_cache(chat_id: str, cache: dict, suffix: str = ""):
    """原子写入缓存：先写临时文件，再 rename 替换"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = cache_path(chat_id, suffix)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    os.replace(tmp_path, path)


def backup_cache(chat_id: str, suffix: str = ""):
    """备份当前缓存"""
    path = cache_path(chat_id, suffix)
    bak_path = path + ".bak"
    if os.path.exists(path):
        os.replace(path, bak_path)


def merge_fragments(existing_fragments: list, new_fragments: list) -> list:
    """
    合并分片，按 startTime 去重排序
    同 startTime 取 text 较长的版本（防止增量返回截断版覆盖完整版）
    """
    merged = {}
    for frag in existing_fragments:
        st = frag.get("startTime")
        text = frag.get("text")
        if st is not None and text:
            merged[st] = frag
    for frag in new_fragments:
        st = frag.get("startTime")
        text = frag.get("text")
        if st is not None and text:
            if st in merged:
                if len(text) > len(merged[st].get("text", "")):
                    merged[st] = frag
            else:
                merged[st] = frag
    return sorted(merged.values(), key=lambda x: x["startTime"])


def build_full_text(fragments: list) -> str:
    """从分片列表拼接全文"""
    parts = []
    for frag in fragments:
        text = frag.get("text")
        if text:
            parts.append(text)
    return "".join(parts)


def parse_live_fragments(raw_data) -> list:
    """解析 splitRecordList/splitRecordListV2 返回的分片数据"""
    fragments = []
    if isinstance(raw_data, list):
        for f in raw_data:
            if f.get("text") is not None:
                fragments.append({
                    "startTime": f.get("startTime", 0),
                    "text": f.get("text"),
                    "realTime": f.get("realTime"),
                })
    return fragments


def parse_second_stt_fragments(raw_list) -> list:
    """解析 checkSecondSttV2 返回的 sttPartList 分片数据"""
    fragments = []
    if isinstance(raw_list, list):
        for f in raw_list:
            text = f.get("text")
            if text:
                frag = {"startTime": f.get("startTime", 0), "text": text}
                # sttPartList 可能有 speaker 等额外字段，一并保留
                for k in ("speaker", "realTime", "endTime"):
                    if k in f:
                        frag[k] = f[k]
                fragments.append(frag)
    return fragments


def try_fetch_second_stt(chat_id: str) -> dict:
    """
    尝试拉取二次改写数据
    返回 {"fragments": [...], "fullText": "...", "state": 2, "source": "second_stt"}
    或 {"fragments": [], "state": 1/3, "source": "second_stt_pending/failed"}
    """
    try:
        result = call_api(API_SECOND_STT, {"meetingChatId": chat_id})
        state = result.get("state", 0)
        stt_list = result.get("sttPartList", [])

        if state == 2 and stt_list:
            fragments = parse_second_stt_fragments(stt_list)
            if fragments:
                return {
                    "fragments": fragments,
                    "fullText": build_full_text(fragments),
                    "state": 2,
                    "source": "second_stt",
                }
        # state=1 处理中，state=3 失败，或 sttList 为空
        return {
            "fragments": [],
            "fullText": "",
            "state": state,
            "source": "second_stt_pending" if state == 1 else "second_stt_failed",
        }
    except Exception:
        return {
            "fragments": [],
            "fullText": "",
            "state": 3,
            "source": "second_stt_failed",
        }


def cleanup_expired_cache():
    """
    清理过期缓存：
    1. 删除 lastSyncAt 超过 CACHE_EXPIRE_DAYS 天的已结束会议缓存
    2. 删除 shared 目录下超过 CACHE_EXPIRE_DAYS 天的日期目录
    每次运行时调用一次，懒清理，不需要定时任务
    """
    now_ms = int(datetime.now(tz=TZ).timestamp() * 1000)
    expire_ms = CACHE_EXPIRE_DAYS * 24 * 60 * 60 * 1000

    # 1. 清理会议缓存
    if os.path.isdir(CACHE_DIR):
        for filename in os.listdir(CACHE_DIR):
            if not filename.endswith("_live.json"):
                continue
            filepath = os.path.join(CACHE_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                if cache.get("status") != "completed":
                    continue
                last_sync = cache.get("lastSyncAt", 0)
                if last_sync and (now_ms - last_sync) > expire_ms:
                    chat_id = filename.replace("_live.json", "")
                    for suffix in ["_live.json", "_final.json", "_live.json.bak", "_final.json.bak"]:
                        p = os.path.join(CACHE_DIR, chat_id + suffix)
                        if os.path.exists(p):
                            os.remove(p)
            except Exception:
                pass

    # 2. 清理 shared 目录下的过期日期子目录
    shared_dir = os.path.join(CACHE_DIR, "shared")
    if not os.path.isdir(shared_dir):
        return
    for meeting_dir_name in os.listdir(shared_dir):
        meeting_dir = os.path.join(shared_dir, meeting_dir_name)
        if not os.path.isdir(meeting_dir):
            continue
        for date_dir_name in list(os.listdir(meeting_dir)):
            date_dir = os.path.join(meeting_dir, date_dir_name)
            if not os.path.isdir(date_dir):
                continue
            try:
                # date_dir_name 格式: 20260329
                dir_date = datetime.strptime(date_dir_name, "%Y%m%d").replace(tzinfo=TZ)
                dir_ms = int(dir_date.timestamp() * 1000)
                if (now_ms - dir_ms) > expire_ms:
                    import shutil
                    shutil.rmtree(date_dir)
            except Exception:
                pass


def main():
    # 解析参数
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    name = None
    if "--name" in sys.argv:
        idx = sys.argv.index("--name")
        if idx + 1 < len(sys.argv):
            name = sys.argv[idx + 1]

    if not args:
        print(json.dumps({"error": "用法: get-transcript.py <meetingChatId> [--name '会议名称']"}, ensure_ascii=False))
        sys.exit(1)

    chat_id = args[0]
    now_ms = int(datetime.now(tz=TZ).timestamp() * 1000)

    # ========== 懒清理：每次运行时清理过期缓存 ==========
    cleanup_expired_cache()

    # ========== 优先级 1：_final 缓存（二次改写，最优） ==========
    final_cache = load_cache(chat_id, "_final")
    if final_cache and final_cache.get("fragments"):
        final_cache["source"] = "cache_final"
        print(json.dumps(final_cache, ensure_ascii=False))
        return

    # ========== 优先级 2：_live 缓存（实时数据） ==========
    live_cache = load_cache(chat_id, "_live")

    # 如果 _live 标记为已完成，尝试拉二次改写
    if live_cache and live_cache.get("status") == "completed":
        stt_result = try_fetch_second_stt(chat_id)
        if stt_result["state"] == 2:
            # 二次改写成功 → 写 _final
            final_data = {
                "meetingChatId": chat_id,
                "name": name or live_cache.get("name", ""),
                "status": "completed",
                "source": "second_stt",
                "lastSyncAt": now_ms,
                "fragments": stt_result["fragments"],
                "fullText": stt_result["fullText"],
                "lastStartTime": max(f["startTime"] for f in stt_result["fragments"]) if stt_result["fragments"] else 0,
            }
            save_cache(chat_id, final_data, "_final")
            print(json.dumps(final_data, ensure_ascii=False))
            return
        else:
            # 二次改写未就绪，返回 _live 缓存
            live_cache["source"] = "cache_live"
            if stt_result["source"] == "second_stt_pending":
                live_cache["note"] = "二次改写处理中，当前返回实时数据"
            print(json.dumps(live_cache, ensure_ascii=False))
            return

    # ========== 优先级 3：实时拉取 ==========
    if live_cache and live_cache.get("lastStartTime") is not None:
        # 有 _live 缓存 → 增量拉取（splitRecordListV2）
        result = call_api(API_INCR, {
            "meetingChatId": chat_id,
            "lastStartTime": live_cache["lastStartTime"]
        })
        source = "incremental"
        new_fragments = parse_live_fragments(result.get("data", []))
        all_fragments = merge_fragments(live_cache.get("fragments", []), new_fragments)
    else:
        # 无缓存 → 全量拉取（splitRecordList）
        result = call_api(API_FULL, {"meetingChatId": chat_id})
        source = "full"
        all_fragments = parse_live_fragments(result.get("data", []))

    full_text = build_full_text(all_fragments)
    last_start_time = max(f["startTime"] for f in all_fragments) if all_fragments else 0

    # 安全检查：增量合并后 fragment 数不能比旧缓存少
    warning = None
    if source == "incremental" and live_cache:
        old_count = len(live_cache.get("fragments", []))
        new_count = len(all_fragments)
        if new_count < old_count:
            all_fragments = live_cache.get("fragments", [])
            full_text = build_full_text(all_fragments)
            last_start_time = live_cache.get("lastStartTime", last_start_time)
            warning = f"增量合并后分片数({new_count})少于旧缓存({old_count})，已保留旧数据"

    # 写 _live 缓存
    cache_name = name or (live_cache.get("name", "") if live_cache else "") or ""
    live_data = {
        "meetingChatId": chat_id,
        "name": cache_name,
        "status": "ongoing",
        "source": source,
        "lastSyncAt": now_ms,
        "lastStartTime": last_start_time,
        "fullText": full_text,
        "fragments": all_fragments,
    }
    if warning:
        live_data["warning"] = warning

    backup_cache(chat_id, "_live")
    save_cache(chat_id, live_data, "_live")

    print(json.dumps(live_data, ensure_ascii=False))


if __name__ == "__main__":
    main()
