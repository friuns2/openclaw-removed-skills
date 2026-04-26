---
name: xhs-download
description: 小红书笔记批量下载。通过已登录 Chrome 的 DevTools Protocol 自动化下载小红书笔记（图片+文字）到本地文件夹。
---

# 小红书笔记批量下载

通过已登录 Chrome 的 DevTools Protocol (CDP) 批量下载小红书笔记。

## 前置条件

- Chrome 已启动并登录小红书
- Python3 + `websocket-client` + `requests` 库已安装
- 安装：`pip3 install websocket-client requests`

## 快速开始（3步）

### 步骤1：获取目标账号 profile_id

在小红书网页版打开目标账号主页，URL 最后一段即为 profile_id：
```
https://www.xiaohongshu.com/user/profile/64902d2d000000001c0294eb
                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^
```

### 步骤2：启动 Chrome 并获取 tab_id

确保 Chrome 已开启远程调试端口：
```bash
# 检查 Chrome 是否在运行
curl -s http://127.0.0.1:9222/json | python3 -c "
import json, sys
tabs = json.load(sys.stdin)
for t in tabs:
    if 'xiaohongshu' in t.get('url', ''):
        print(f\"tab_id: {t['id']}\")
        print(f\"url: {t['url'][:80]}\")
"
```

如果未开启，用以下命令启动 Chrome：
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-xhs/
```

### 步骤3：运行下载脚本

```python
import json, time, requests, os, subprocess, websocket

# ===== 配置区（修改这里）=====
PROFILE_ID = "你的目标账号ID"          # 从小红书主页URL获取
TAB_ID = ""                            # 留空自动获取，或填入上一步获取的tab_id
SAVE_DIR = "~/Downloads/你的文件夹/"    # 下载保存路径
# ================================

SAVE_DIR = os.path.expanduser(SAVE_DIR)
os.makedirs(SAVE_DIR, exist_ok=True)

def get_tab_id():
    if TAB_ID: return TAB_ID
    r = subprocess.run(['curl', '-s', 'http://127.0.0.1:9222/json'],
                       capture_output=True, text=True, timeout=5)
    tabs = json.loads(r.stdout)
    for t in tabs:
        if 'xiaohongshu' in t.get('url', ''):
            return t['id']
    return tabs[0]['id']

def send(ws, method, params={}):
    """CDP 命令发送（3个参数：ws, method, params）"""
    msg_id = int(time.time()*1000) % 100000
    msg = {"id": msg_id, "method": method, "params": params}
    ws.send(json.dumps(msg))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id:
            return resp

def download_image(url, path):
    r = requests.get(url, headers={"Referer": "https://www.xiaohongshu.com/"}, timeout=30)
    if len(r.content) > 100:
        with open(path, 'wb') as f: f.write(r.content)
        return True
    return False

# 连接 Chrome
tab_id = get_tab_id()
print(f"使用 tab_id: {tab_id}")
ws = websocket.create_connection(f"ws://127.0.0.1:9222/devtools/page/{tab_id}", timeout=30)

# 导航到主页
url = f"https://www.xiaohongshu.com/user/profile/{PROFILE_ID}"
send(ws, "Page.navigate", {"url": url})
time.sleep(6)

# 滚动加载所有笔记
print("滚动加载中...")
for i in range(30):
    send(ws, "Input.synthesizeScrollGesture", {
        "x": 500, "y": 600, "xDistance": 0, "yDistance": -800, "speed": 2000
    })
    time.sleep(2)
    print(f"  滚动 {i+1}/30")

# 提取笔记列表
result = send(ws, "Runtime.evaluate", {"expression": """
(() => {
    const cards = document.querySelectorAll(".feeds-container .note-item");
    return JSON.stringify(Array.from(cards).map(c => {
        const a = c.querySelector("a[href*='/explore/']");
        return {
            href: a ? a.getAttribute("href") : "",
            title: a ? a.innerText.trim().substring(0, 60) : ""
        };
    }));
})()
"""})
notes = json.loads(result["result"]["result"]["value"])
print(f"找到 {len(notes)} 篇笔记")

# 下载每篇笔记
downloaded = 0
errors = 0
for note in notes:
    href = note.get("href", "")
    title = note.get("title", "").strip()
    if not href or not title:
        continue

    note_dir = os.path.join(SAVE_DIR, title)
    if os.path.exists(note_dir):
        print(f"跳过（已存在）: {title}")
        continue

    os.makedirs(note_dir, exist_ok=True)

    # 提取 note_id 和 xsec_token
    import re
    note_id = re.search(r'/explore/([a-f0-9]+)', href)
    note_id = note_id.group(1) if note_id else ""

    # 从 __INITIAL_STATE__ 获取 xsec_token
    state_result = send(ws, "Runtime.evaluate", {"expression": """
    (() => {
        const state = window.__INITIAL_STATE__ || {};
        const user = state.user || {};
        const notes = user.notes || {};
        const items = notes._value && notes._value.items ? notes._value.items : [];
        return JSON.stringify(items.map(n => ({
            id: n.note && n.note.id || '',
            xsecToken: n.note && n.note.xsecToken || ''
        })));
    })()
    """})
    items = json.loads(state_result["result"]["result"]["value"])
    xsec_token = ""
    for item in items:
        if item.get("id") == note_id:
            xsec_token = item.get("xsecToken", "")
            break

    # 导航到详情页
    if xsec_token:
        detail_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}"
    else:
        detail_url = f"https://www.xiaohongshu.com/explore/{note_id}"
    send(ws, "Page.navigate", {"url": detail_url})
    time.sleep(4)

    # 提取图片
    img_result = send(ws, "Runtime.evaluate", {"expression": """
    (() => {
        const swiper = document.querySelector('.swiper-wrapper');
        const imgs = swiper ? swiper.querySelectorAll('img') : [];
        return JSON.stringify(Array.from(imgs).map((img, i) => ({
            i, src: img.src
        })));
    })()
    """})
    images = json.loads(img_result["result"]["result"]["value"])

    # 下载图片
    img_count = 0
    for img in images:
        src = img.get("src", "")
        if src:
            path = os.path.join(note_dir, f"{img['i']+1}.jpg")
            if download_image(src, path):
                img_count += 1

    # 提取文字
    text_result = send(ws, "Runtime.evaluate", {"expression": """
    (() => {
        const desc = document.querySelector('.note-content .desc');
        return desc ? desc.innerText : document.title || '';
    })()
    """})
    text = text_result["result"]["result"].get("value", "")
    with open(os.path.join(note_dir, "内容.txt"), "w", encoding="utf-8") as f:
        f.write(text)

    downloaded += 1
    print(f"✅ {title} ({img_count}张图片)")

ws.close()
print(f"\n完成: 下载 {downloaded} 篇")
```

## 下载结果

每篇笔记保存在独立文件夹：
```
~/Downloads/你的文件夹/
├── 笔记标题1/
│   ├── 内容.txt
│   ├── 1.jpg
│   └── 2.jpg
└── 笔记标题2/
    ├── 内容.txt
    └── 1.jpg
```

## 常见问题

| 问题 | 解决 |
|------|------|
| `Connection refused` | Chrome 未启动或端口不是9222 |
| 图片 403 | 必须加 `Referer: https://www.xiaohongshu.com/` |
| 笔记数量少 | 增加滚动次数（30→50） |
| `send()` 报错 | 确认是3个参数：`send(ws, method, params={})` |

## 铁律

1. **不杀 Chrome** — 先 `curl http://127.0.0.1:9222/json`
2. **不开新浏览器** — 用已登录实例
3. **图片必带 Referer** — 否则防盗链 403
4. **下载前检查已下载目录** — 避免重复
