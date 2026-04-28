#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import hashlib
import subprocess

# Windows encoding compatibility
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import warnings
# Only suppress trivial warnings, reserve SSL security check
warnings.filterwarnings("ignore", category=DeprecationWarning)

API_BASE = "https://api.socialepoch.com"
TIMEOUT = 10
RETRY_TIMES = 2

# ==========================
# Cross-platform config path: Windows / Mac / Linux
# ==========================
if os.name == "nt":
    # Windows
    CONFIG_DIR = os.path.join(os.environ.get("USERPROFILE", ""), ".openclaw")
else:
    # Mac / Linux
    CONFIG_DIR = os.path.expanduser("~/.openclaw")

CONFIG_FILE = os.path.join(CONFIG_DIR, "scrm_config.json")

SUPPORTED_COMMANDS = {
    "set_config", "help", "query_online_agents", "query_task",
    "send_text", "send_img", "send_audio", "send_file", "send_video",
    "send_card", "send_card_link", "send_flow_link",
    "bulk_send", "bulk_send_img", "bulk_send_audio",
    "bulk_send_file", "bulk_send_video", "bulk_send_card_link"
}

# ==========================
# Skip SIGINT handler for Windows compatibility
# ==========================
try:
    import signal
    signal.signal(signal.SIGINT, lambda *_: sys.exit(130))
except Exception:
    pass

# ==========================
# Task status mapping (English)
# ==========================
STATUS_TEXT = {
    0: "Pending Dispatch",
    1: "Pending Send",
    2: "Sending",
    3: "Sent",
    4: "Delivered",
    5: "Read",
    6: "Read & Replied",
    7: "Read & No Reply",
    -1: "Send Failed"
}

TASK_STATUS_TEXT = {
    1: "Not Started",
    2: "Pending",
    3: "Bulk Processing",
    4: "Stopped",
    5: "Completed",
    6: "Paused"
}

# ==========================
# Unified text cleaning to fix \n escaped to \\n
# ==========================
def clean_text(raw: str) -> str:
    if not raw:
        return ""
    s = raw.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t")
    return s.rstrip()

def output(code=200, message="", data=None):
    print(json.dumps({"code": code, "message": message, "data": data}, ensure_ascii=False, indent=2))
    sys.exit(0)

# ==========================
# Auto install dependencies (Cross-platform)
# ==========================
def install_deps():
    try:
        import requests
        return
    except ImportError:
        pass

    pip_args = [
        sys.executable, "-m", "pip",
        "install", "requests<2.32.0",
        "--no-warn-script-location"
    ]

    if os.name != "nt":
        pip_args.extend(["--user", "--break-system-packages"])

    try:
        subprocess.check_call(
            pip_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        output(-1, "Dependency installation failed, please check your Python environment")

    try:
        import requests
    except ImportError:
        output(-1, "Load requests failed, please install manually")

install_deps()

import requests
requests.packages.urllib3.disable_warnings()

# ==========================
# Config management
# ==========================
def load_config():
    tid = os.environ.get("SOCIALEPOCH_TENANT_ID", "").strip()
    key = os.environ.get("SOCIALEPOCH_API_KEY", "").strip()
    source = os.environ.get("SOCIALEPOCH_SOURCE", "").strip()

    env_cfg = {}
    if tid and key:
        env_cfg = {"TENANT_ID": tid, "API_KEY": key, "API_BASE": API_BASE}
        if source:
            env_cfg["SOURCE"] = source

    if env_cfg:
        final_cfg = env_cfg
    else:
        if not os.path.exists(CONFIG_FILE):
            output(-1, "Config not found. Please run: python3 scrm_api.py set_config [TENANT_ID] [API_KEY] [SOURCE(optional,1=PC,2=Mobile,3=Cloud)]")

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            tid = cfg.get("TENANT_ID", "").strip()
            key = cfg.get("API_KEY", "").strip()
            if not tid or not key:
                output(-1, "Config file incomplete")
            final_cfg = {
                "TENANT_ID": tid,
                "API_KEY": key,
                "API_BASE": API_BASE,
                "SOURCE": cfg.get("SOURCE", "1")
            }
        except Exception:
            output(-1, "Failed to read config file")

    try:
        final_cfg["SOURCE"] = str(final_cfg.get("SOURCE", "1"))[0]
    except:
        final_cfg["SOURCE"] = "1"

    return final_cfg

def save_config(tid, key, source="1"):
    # Load existing config first to keep old values
    old_cfg = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            old_cfg = json.load(f)

    # Use new value if provided, otherwise keep old one
    final_tid = tid.strip() if tid.strip() else old_cfg.get("TENANT_ID", "").strip()
    final_key = key.strip() if key.strip() else old_cfg.get("API_KEY", "").strip()
    final_source = source.strip() if source.strip() else old_cfg.get("SOURCE", "1").strip()

    # Validation
    if not final_tid or not final_key:
        output(-1, "Usage: scrm_api.py set_config TENANT_ID API_KEY [SOURCE(optional,1=PC,2=Mobile,3=Cloud)]")

    os.makedirs(CONFIG_DIR, exist_ok=True)
    cfg = {
        "TENANT_ID": final_tid,
        "API_KEY": final_key,
        "SOURCE": final_source
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    output(200, "Config saved successfully")

# ==========================
# Signature generation
# ==========================
def make_sign(tenant_id, api_key):
    ts = str(int(time.time() * 1000))
    s = f"{tenant_id}{ts}{api_key}"
    return ts, hashlib.md5(s.encode()).hexdigest()

# ==========================
# API request core
# ==========================
def request_api(path, body, method="POST"):
    cfg = load_config()
    ts, token = make_sign(cfg["TENANT_ID"], cfg["API_KEY"])

    headers = {
        "Content-Type": "application/json",
        "tenant_id": cfg["TENANT_ID"],
        "timestamp": ts,
        "token": token
    }

    for _ in range(RETRY_TIMES + 1):
        try:
            if method == "POST":
                r = requests.post(
                    cfg["API_BASE"] + path,
                    json=body,
                    headers=headers,
                    timeout=TIMEOUT,
                    verify=True
                )
            else:
                r = requests.get(
                    cfg["API_BASE"] + path,
                    params=body,
                    headers=headers,
                    timeout=TIMEOUT,
                    verify=True
                )

            if r.status_code == 200:
                return r.json()
        except Exception:
            time.sleep(1)

    output(-1, "API request failed")

# ==========================
# Business functions
# ==========================
def query_online_agents(userName=""):
    cfg = load_config()
    return request_api("/group-dispatch-api/user/queryUserStatus", {
        "userId": "",
        "source": cfg.get("SOURCE", "1"),
        "userName": userName.strip() if userName else ""
    })

def send_text(send, to, text):
    cfg = load_config()
    safe_text = clean_text(text)
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-text", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 1, "text": safe_text, "sort": 0}]
    })

def send_img(send, to, url, caption=""):
    cfg = load_config()
    safe_caption = clean_text(caption)
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-img", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 2, "url": url, "text": safe_caption, "sort": 0}]
    })

def send_audio(send, to, url):
    cfg = load_config()
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-audio", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 3, "url": url, "sort": 0}]
    })

def send_file(send, to, url, caption=""):
    cfg = load_config()
    safe_caption = clean_text(caption)
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-file", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 4, "url": url, "text": safe_caption, "sort": 0}]
    })

def send_video(send, to, url, caption=""):
    cfg = load_config()
    safe_caption = clean_text(caption)
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-video", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 5, "url": url, "text": safe_caption, "sort": 0}]
    })

def send_card(send, to, card):
    cfg = load_config()
    safe_card = clean_text(card)
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-card", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 6, "text": safe_card, "sort": 0}]
    })

def send_card_link(send, to, title, link, text="", img=""):
    cfg = load_config()
    safe_text = clean_text(text)
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-clink", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 10, "title": title, "text": safe_text, "link": link, "url": img, "sort": 0}]
    })

def send_flow_link(send, to, title, route_list):
    cfg = load_config()
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-flink", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 11, "title": title, "text": title, "routeType": 3, "routeList": route_list, "sort": 0}]
    })

def query_task(task_id):
    res = request_api("/group-dispatch-api/gsTask/queryExecuteStatus", {"taskId": task_id}, "GET")
    data = res.get("data", {})
    task_status = data.get("status")
    if task_status in TASK_STATUS_TEXT:
        data["status_text"] = TASK_STATUS_TEXT[task_status]

    for item in data.get("info", []):
        s = item.get("status")
        if s in STATUS_TEXT:
            item["status_text"] = STATUS_TEXT[s]
    return res

# ==========================
# Bulk text message
# ==========================
def bulk_send(sendWhatsapp, friendList, text):
    cfg = load_config()
    sendInfos = []
    for friend in friendList:
        sendInfos.append({
            "sendWhatsApp": sendWhatsapp,
            "friendWhatsApp": friend.strip()
        })

    safe_text = clean_text(text)
    content = [{
        "type": 1,
        "text": safe_text,
        "sort": 0
    }]

    return request_api("/group-dispatch-api/gsTask/assign/moscCreate", {
        "name": "bulk_send",
        "sendType": 1,
        "targetType": 1,
        "source": cfg.get("SOURCE", "1"),
        "sendInfos": sendInfos,
        "content": content
    })

# ==========================
# Bulk image message
# ==========================
def bulk_send_img(sendWhatsapp, friendList, url, caption=""):
    cfg = load_config()
    sendInfos = [{"sendWhatsApp": sendWhatsapp, "friendWhatsApp": f.strip()} for f in friendList]
    safe_caption = clean_text(caption)
    content = [{
        "type": 2,
        "url": url,
        "text": safe_caption,
        "sort": 0
    }]
    return request_api("/group-dispatch-api/gsTask/assign/moscCreate", {
        "name": "bulk_img",
        "sendType": 1,
        "targetType": 1,
        "source": cfg.get("SOURCE", "1"),
        "sendInfos": sendInfos,
        "content": content
    })

# ==========================
# Bulk audio message
# ==========================
def bulk_send_audio(sendWhatsapp, friendList, url):
    cfg = load_config()
    sendInfos = [{"sendWhatsApp": sendWhatsapp, "friendWhatsApp": f.strip()} for f in friendList]
    content = [{
        "type": 3,
        "url": url,
        "sort": 0
    }]
    return request_api("/group-dispatch-api/gsTask/assign/moscCreate", {
        "name": "bulk_audio",
        "sendType": 1,
        "targetType": 1,
        "source": cfg.get("SOURCE", "1"),
        "sendInfos": sendInfos,
        "content": content
    })

# ==========================
# Bulk file message
# ==========================
def bulk_send_file(sendWhatsapp, friendList, url, caption=""):
    cfg = load_config()
    sendInfos = [{"sendWhatsApp": sendWhatsapp, "friendWhatsApp": f.strip()} for f in friendList]
    safe_caption = clean_text(caption)
    content = [{
        "type": 4,
        "url": url,
        "text": safe_caption,
        "sort": 0
    }]
    return request_api("/group-dispatch-api/gsTask/assign/moscCreate", {
        "name": "bulk_file",
        "sendType": 1,
        "targetType": 1,
        "source": cfg.get("SOURCE", "1"),
        "sendInfos": sendInfos,
        "content": content
    })

# ==========================
# Bulk video message
# ==========================
def bulk_send_video(sendWhatsapp, friendList, url, caption=""):
    cfg = load_config()
    sendInfos = [{"sendWhatsApp": sendWhatsapp, "friendWhatsApp": f.strip()} for f in friendList]
    safe_caption = clean_text(caption)
    content = [{
        "type": 5,
        "url": url,
        "text": safe_caption,
        "sort": 0
    }]
    return request_api("/group-dispatch-api/gsTask/assign/moscCreate", {
        "name": "bulk_video",
        "sendType": 1,
        "targetType": 1,
        "source": cfg.get("SOURCE", "1"),
        "sendInfos": sendInfos,
        "content": content
    })

# ==========================
# Bulk link card
# ==========================
def bulk_send_card_link(sendWhatsapp, friendList, title, link, text="", img=""):
    cfg = load_config()
    sendInfos = [{"sendWhatsApp": sendWhatsapp, "friendWhatsApp": f.strip()} for f in friendList]
    safe_text = clean_text(text)
    content = [{
        "type": 10,
        "title": title,
        "text": safe_text,
        "link": link,
        "url": img,
        "sort": 0
    }]
    return request_api("/group-dispatch-api/gsTask/assign/moscCreate", {
        "name": "bulk_card_link",
        "sendType": 1,
        "targetType": 1,
        "source": cfg.get("SOURCE", "1"),
        "sendInfos": sendInfos,
        "content": content
    })

# ==========================
# Entry
# ==========================
def main():
    if len(sys.argv) < 2:
        output(200, "Commands: help set_config query_online_agents query_task send_text send_img send_audio send_file send_video send_card send_card_link send_flow_link bulk series")

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd not in SUPPORTED_COMMANDS:
        output(-1, f"Unsupported command: {cmd}")

    try:
        res = {}
        if cmd == "help":
            output(200, "Available commands: set_config query_online_agents query_task send_text send_img send_audio send_file send_video send_card send_card_link send_flow_link bulk series")
        elif cmd == "set_config":
            tid = args[0] if len(args) >= 1 else ""
            ak = args[1] if len(args) >= 2 else ""
            source = args[2] if len(args) >= 3 else "1"
            save_config(tid, ak, source)
        elif cmd == "query_online_agents":
            res = query_online_agents(args[0] if len(args) >= 1 else "")
        elif cmd == "query_task":
            res = query_task(args[0] if args else "")
        elif cmd == "send_text":
            res = send_text(args[0], args[1], " ".join(args[2:]))
        elif cmd == "send_img":
            res = send_img(args[0], args[1], args[2], " ".join(args[3:]))
        elif cmd == "send_audio":
            res = send_audio(args[0], args[1], args[2])
        elif cmd == "send_file":
            res = send_file(args[0], args[1], args[2], " ".join(args[3:]))
        elif cmd == "send_video":
            res = send_video(args[0], args[1], args[2], " ".join(args[3:]))
        elif cmd == "send_card":
            res = send_card(args[0], args[1], args[2])
        elif cmd == "send_card_link":
            text = " ".join(args[4:]) if len(args) >= 5 else ""
            img = args[5] if len(args) >= 6 else ""
            res = send_card_link(args[0], args[1], args[2], args[3], text, img)
        elif cmd == "send_flow_link":
            route_list = args[3] if len(args) >= 4 else [1]
            res = send_flow_link(args[0], args[1], args[2], route_list)
        elif cmd == "bulk_send":
            send = args[0]
            friendList = args[1].split(",")
            text = " ".join(args[2:])
            res = bulk_send(send, friendList, text)
        elif cmd == "bulk_send_img":
            send = args[0]
            friendList = args[1].split(",")
            url = args[2]
            caption = " ".join(args[3:])
            res = bulk_send_img(send, friendList, url, caption)
        elif cmd == "bulk_send_audio":
            send = args[0]
            friendList = args[1].split(",")
            url = args[2]
            res = bulk_send_audio(send, friendList, url)
        elif cmd == "bulk_send_file":
            send = args[0]
            friendList = args[1].split(",")
            url = args[2]
            caption = " ".join(args[3:])
            res = bulk_send_file(send, friendList, url, caption)
        elif cmd == "bulk_send_video":
            send = args[0]
            friendList = args[1].split(",")
            url = args[2]
            caption = " ".join(args[3:])
            res = bulk_send_video(send, friendList, url, caption)
        elif cmd == "bulk_send_card_link":
            send = args[0]
            friendList = args[1].split(",")
            title = args[2]
            link = args[3]
            text = args[4] if len(args) >= 5 else ""
            img = args[5] if len(args) >= 6 else ""
            res = bulk_send_card_link(send, friendList, title, link, text, img)
        else:
            res = {"code": 200, "message": "Success", "data": None}

        output(res.get("code", 200), res.get("message", "Success"), res.get("data"))
    except Exception as e:
        output(-1, f"Execution failed: {str(e)}")

if __name__ == "__main__":
    main()