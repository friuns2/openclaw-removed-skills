#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import hashlib
import subprocess

# Windows 编码崩溃防护
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

# 禁用所有警告（解决SSL报错）
import warnings

warnings.filterwarnings("ignore")

API_BASE = "https://api.socialepoch.com"
TIMEOUT = 10
RETRY_TIMES = 2

# ==========================
# 【跨平台兼容】配置目录自动适配 Windows/Mac
# ==========================
if os.name == "nt":  # Windows
    CONFIG_DIR = os.path.join(os.environ.get("USERPROFILE", ""), ".openclaw")
else:  # Mac/Linux
    CONFIG_DIR = os.path.expanduser("~/.openclaw")

CONFIG_FILE = os.path.join(CONFIG_DIR, "scrm_config.json")

SUPPORTED_COMMANDS = {"set_config", "help", "query_online_agents", "query_task", "send_text", "send_img", "send_audio",
                      "send_file", "send_video", "send_card", "send_card_link", "send_flow_link", "bulk_send",
                      "bulk_send_img", "bulk_send_audio", "bulk_send_file", "bulk_send_video", "bulk_send_card_link"}

# ==========================
# 【跨平台兼容】Windows 不支持 SIGINT 优雅退出
# ==========================
try:
    import signal
    signal.signal(signal.SIGINT, lambda *_: sys.exit(130))
except:
    pass

# ==========================
# 状态中文映射
# ==========================
STATUS_TEXT = {
    0: "待下发",
    1: "待发送",
    2: "发送中",
    3: "已发送",
    4: "已到达",
    5: "已读",
    6: "已读已回",
    7: "已读未回",
    -1: "发送失败"
}

TASK_STATUS_TEXT = {
    1: "待开始",
    2: "待发送",
    3: "群发中",
    4: "已停止",
    5: "已完成",
    6: "已暂停"
}


def output(code=200, message="", data=None):
    print(json.dumps({"code": code, "message": message, "data": data}, ensure_ascii=False, indent=2))
    sys.exit(0)


# ==========================
# 全自动安装依赖（Windows + Mac 双兼容）
# ==========================
def install_deps():
    try:
        import requests
        return
    except ImportError:
        pass

    pip_args = [sys.executable, "-m", "pip", "install", "requests<2.32.0", "--no-warn-script-location"]

    # Windows 不需要加 --user --break-system-packages
    if os.name != "nt":
        pip_args.extend(["--user", "--break-system-packages"])

    try:
        subprocess.check_call(
            pip_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except:
        pass

    try:
        import requests
    except:
        output(-1, "依赖安装失败，请检查Python环境")


install_deps()

import requests

requests.packages.urllib3.disable_warnings()


# ==========================
# 配置管理
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
            output(-1, "请先配置密钥：python3 scrm_api.py set_config tenant_id api_key [source]")

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            tid = cfg.get("TENANT_ID", "").strip()
            key = cfg.get("API_KEY", "").strip()
            if not tid or not key:
                output(-1, "配置文件不完整")

            final_cfg = {
                "TENANT_ID": tid,
                "API_KEY": key,
                "API_BASE": API_BASE,
                "SOURCE": cfg.get("SOURCE", "1")
            }
        except:
            output(-1, "配置文件读取失败")

    try:
        final_cfg["SOURCE"] = str(final_cfg.get("SOURCE", "1"))[0]
    except:
        final_cfg["SOURCE"] = "1"

    return final_cfg


def save_config(tid, key, source="1"):
    # 先读取旧配置，不传的参数就用旧的
    old_cfg = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            old_cfg = json.load(f)

    # 不传 = 保留原来的值
    final_tid = tid.strip() if tid.strip() else old_cfg.get("TENANT_ID", "").strip()
    final_key = key.strip() if key.strip() else old_cfg.get("API_KEY", "").strip()
    final_source = source.strip() if source.strip() else old_cfg.get("SOURCE", "1").strip()

    # 必须保证最终有值
    if not final_tid or not final_key:
        output(-1, "用法：scrm_api.py set_config 租户ID API密钥 [发送端类型(1/2/3)]")

    os.makedirs(CONFIG_DIR, exist_ok=True)
    cfg = {
        "TENANT_ID": final_tid,
        "API_KEY": final_key,
        "SOURCE": final_source
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    output(200, "配置保存成功")


# ==========================
# 签名
# ==========================
def make_sign(tenant_id, api_key):
    ts = str(int(time.time() * 1000))
    s = f"{tenant_id}{ts}{api_key}"
    return ts, hashlib.md5(s.encode()).hexdigest()


# ==========================
# API 请求
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
        except:
            time.sleep(1)

    output(-1, "API请求失败")


# ==========================
# 业务功能
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
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-text", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 1, "text": text, "sort": 0}]
    })


def send_img(send, to, url, caption=""):
    cfg = load_config()
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-img", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 2, "url": url, "text": caption, "sort": 0}]
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
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-file", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 4, "url": url, "text": caption, "sort": 0}]
    })


def send_video(send, to, url, caption=""):
    cfg = load_config()
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-video", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 5, "url": url, "text": caption, "sort": 0}]
    })


def send_card(send, to, card):
    cfg = load_config()
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-card", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 6, "text": card, "sort": 0}]
    })


def send_card_link(send, to, title, link, text="", img=""):
    cfg = load_config()
    return request_api("/group-dispatch-api/gsTask/assign/soCreate", {
        "name": "wa-clink", "sendType": 1, "targetType": 1,
        "sendWhatsApp": send, "friendWhatsApp": to,
        "source": cfg.get("SOURCE", "1"),
        "content": [{"type": 10, "title": title, "text": text, "link": link, "url": img, "sort": 0}]
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
    # === 自动把数字状态转中文 ===
    data = res.get("data", {})
    task_status = data.get("status")
    if task_status in TASK_STATUS_TEXT:
        data["status_text"] = TASK_STATUS_TEXT[task_status]

    for item in data.get("info", []):
        s = item.get("status")
        if s in STATUS_TEXT:
            item["status_text"] = STATUS_TEXT[s]
    # ======================================
    return res


# ==========================
# 【真正群发】文字消息（多目标）
# ==========================
def bulk_send(sendWhatsapp, friendList, text):
    cfg = load_config()
    # 构建发送列表
    sendInfos = []
    for friend in friendList:
        sendInfos.append({
            "sendWhatsApp": sendWhatsapp,
            "friendWhatsApp": friend.strip()
        })

    # 构建内容
    content = [{
        "type": 1,
        "text": text,
        "sort": 0
    }]

    # 群发接口（官方）
    return request_api("/group-dispatch-api/gsTask/assign/moscCreate", {
        "name": "bulk_send",
        "sendType": 1,
        "targetType": 1,
        "source": cfg.get("SOURCE", "1"),
        "sendInfos": sendInfos,
        "content": content
    })


# ==========================
# 【群发】图片消息
# ==========================
def bulk_send_img(sendWhatsapp, friendList, url, caption=""):
    cfg = load_config()
    sendInfos = [{"sendWhatsApp": sendWhatsapp, "friendWhatsApp": f.strip()} for f in friendList]
    content = [{
        "type": 2,
        "url": url,
        "text": caption,
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
# 【群发】音频消息
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
# 【群发】文件消息
# ==========================
def bulk_send_file(sendWhatsapp, friendList, url, caption=""):
    cfg = load_config()
    sendInfos = [{"sendWhatsApp": sendWhatsapp, "friendWhatsApp": f.strip()} for f in friendList]
    content = [{
        "type": 4,
        "url": url,
        "text": caption,
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
# 【群发】视频消息
# ==========================
def bulk_send_video(sendWhatsapp, friendList, url, caption=""):
    cfg = load_config()
    sendInfos = [{"sendWhatsApp": sendWhatsapp, "friendWhatsApp": f.strip()} for f in friendList]
    content = [{
        "type": 5,
        "url": url,
        "text": caption,
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
# 【群发】名片超链
# ==========================
def bulk_send_card_link(sendWhatsapp, friendList, title, link, text="", img=""):
    cfg = load_config()
    sendInfos = [{"sendWhatsApp": sendWhatsapp, "friendWhatsApp": f.strip()} for f in friendList]
    content = [{
        "type": 10,
        "title": title,
        "text": text,
        "link": link,
        "url": img,
        "sort": 0
    }]
    return request_api("/group-dispatch-api/gsTask/assign/moscCreate", {
        "name": "bulk_clink",
        "sendType": 1,
        "targetType": 1,
        "source": cfg.get("SOURCE", "1"),
        "sendInfos": sendInfos,
        "content": content
    })


# ==========================
# 命令入口
# ==========================
def main():
    if len(sys.argv) < 2:
        output(200,
               "支持命令：help set_config query_online_agents query_task send_text send_img send_audio send_file send_video send_card send_card_link send_flow_link bulk_send bulk_send_img bulk_send_audio bulk_send_file bulk_send_video bulk_send_card_link")

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd not in SUPPORTED_COMMANDS:
        output(-1, f"不支持命令：{cmd}")

    try:
        if cmd == "help":
            output(200,
                   "命令：set_config query_online_agents query_task send_text send_img send_audio send_file send_video send_card send_card_link send_flow_link bulk_send bulk_send_img bulk_send_audio bulk_send_file bulk_send_video bulk_send_card_link")
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
            # 参数：发送号 接收号 标题 链接 描述(可选) 封面图(可选)
            text = " ".join(args[4:5]) if len(args) >= 5 else ""
            img = args[5] if len(args) >= 6 else ""
            res = send_card_link(args[0], args[1], args[2], args[3], text, img)
        elif cmd == "send_flow_link":
            # 格式：发送号  接收号  标题  分流号码列表
            route_list = args[3] if len(args) >= 4 else [1]
            res = send_flow_link(args[0], args[1], args[2], route_list)
        elif cmd == "bulk_send":
            # 格式：发送号 接收号1,接收号2 文字内容
            send = args[0]
            friendList = args[1].split(",")  # 多个号码用逗号分隔
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
            res = {"code": 200, "message": "成功", "data": None}

        output(res.get("code", 200), res.get("message", "成功"), res.get("data"))
    except Exception as e:
        output(-1, f"执行失败：{str(e)}")


if __name__ == "__main__":
    main()