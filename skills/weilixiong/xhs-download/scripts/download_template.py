#!/usr/bin/env python3
"""批量下载小红书笔记 - {{ACCOUNT_NAME}}v3 - 修复重复计数"""
import json, websocket, time, subprocess, os, re, requests, sys

DOWNLOAD_DIR = os.path.expanduser("~/Downloads/铁头/{{ACCOUNT_SHORT_NAME}}/")
TAB_ID = "{{TAB_ID}}"
PROFILE_URL = "https://www.xiaohongshu.com/user/profile/{{PROFILE_ID}}"
MAX_NOTES = 400  # {{ACCOUNT_SHORT_NAME}}上海实际约362篇，设400为安全上限
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_ws():
    return websocket.create_connection(f"ws://127.0.0.1:9222/devtools/page/{TAB_ID}", timeout=30)

def send(ws, method, params={}):
    msg = {"id": int(time.time()*1000)%100000, "method": method, "params": params}
    ws.send(json.dumps(msg))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg["id"]:
            return resp

def safe_filename(name):
    name = re.sub(r'[\\/:*?"<>|]', '', name).strip()
    name = re.sub(r'\s+', ' ', name)
    return name[:80]

def download_image(url, path):
    try:
        headers = {"Referer": "https://www.xiaohongshu.com/", "User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=30)
        if len(r.content) > 100:
            with open(path, 'wb') as f:
                f.write(r.content)
            return True, len(r.content)
        return False, 0
    except:
        return False, 0

def get_notes(ws):
    """提取笔记列表，去重"""
    result = send(ws, "Runtime.evaluate", {
        "expression": """
        (() => {
            const notesVal = window.__INITIAL_STATE__?.user?.notes?._value;
            if (!notesVal) return "[]";
            const seen = new Set();
            const notes = [];
            for (const key of Object.keys(notesVal)) {
                const item = notesVal[key];
                if (item && typeof item === 'object') {
                    for (const k of Object.keys(item)) {
                        const note = item[k];
                        if (note?.noteCard?.noteId && !seen.has(note.noteCard.noteId)) {
                            seen.add(note.noteCard.noteId);
                            const nc = note.noteCard;
                            notes.push({
                                noteId: nc.noteId,
                                xsecToken: nc.xsecToken || "",
                                title: nc.displayTitle || "",
                                type: nc.type || "note"
                            });
                        }
                    }
                }
            }
            return JSON.stringify(notes);
        })()
        """
    })
    return json.loads(result.get('result', {}).get('result', {}).get('value', '[]'))

def main():
    ws = get_ws()
    if not ws:
        print("ERROR: 无法连接 Chrome")
        sys.exit(1)
    
    # 确认在主页
    result = send(ws, "Runtime.evaluate", {
        "expression": "JSON.stringify({url: window.location.href, title: document.title})"
    })
    current = json.loads(result.get('result', {}).get('result', {}).get('value', '{}'))
    print(f"当前页面: {current.get('title', 'unknown')}")
    
    if 'profile' not in current.get('url', ''):
        print("不在主页，导航中...")
        send(ws, "Page.navigate", {"url": PROFILE_URL})
        time.sleep(10)
    
    # 滚动加载所有笔记（去重）
    print("\n滚动加载所有笔记...")
    prev_count = 0
    no_change_count = 0
    for i in range(25):
        send(ws, "Runtime.evaluate", {
            "expression": "window.scrollTo(0, document.body.scrollHeight)"
        })
        time.sleep(2)
        
        notes = get_notes(ws)
        count = len(notes)
        print(f"  已加载: {count} 篇（去重）")
        if count == prev_count:
            no_change_count += 1
            if no_change_count >= 3:
                print("  连续3次无新增，停止滚动")
                break
        else:
            no_change_count = 0
        prev_count = count
        
        # 超过362篇就停止（防止无限滚动）
        if count >= 370:
            print("  已达到预期上限，停止滚动")
            break
    
    all_notes = get_notes(ws)
    print(f"\n最终获取到笔记总数: {len(all_notes)}")
    
    # 获取已下载的
    already = set(os.listdir(DOWNLOAD_DIR)) if os.path.exists(DOWNLOAD_DIR) else set()
    
    # 找出未下载的
    todo = []
    skipped = 0
    for note in all_notes:
        title = safe_filename(note['title'])
        if title in already or any(title in d for d in already):
            skipped += 1
        else:
            todo.append(note)
    
    print(f"已下载: {skipped} 篇")
    print(f"待下载: {len(todo)} 篇")
    
    if not todo:
        print("全部已完成！")
        ws.close()
        return
    
    # 开始下载
    downloaded = 0
    errors = []
    
    for idx, note in enumerate(todo):
        note_id = note['noteId']
        xsec_token = note['xsecToken']
        title = safe_filename(note['title'])
        note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}"
        
        folder = os.path.join(DOWNLOAD_DIR, title)
        os.makedirs(folder, exist_ok=True)
        
        try:
            send(ws, "Page.navigate", {"url": note_url})
            time.sleep(5)
            
            send(ws, "Runtime.evaluate", {
                "expression": "document.querySelector('[class*=note-content]')?.scrollTo(0, 99999)"
            })
            time.sleep(2)
            
            # 文字
            text_result = send(ws, "Runtime.evaluate", {
                "expression": "document.querySelector('[class*=note-content]')?.innerText || ''"
            })
            text = text_result.get('result', {}).get('result', {}).get('value', '')
            
            # 图片
            img_result = send(ws, "Runtime.evaluate", {
                "expression": """
                (() => {
                    function findNote(obj, noteId, depth) {
                        if (!obj || depth > 15) return null;
                        if (typeof obj !== 'object') return null;
                        if (obj.noteId === noteId && obj.imageList) return obj;
                        for (const v of Object.values(obj)) {
                            const r = findNote(v, noteId, depth + 1);
                            if (r) return r;
                        }
                        return null;
                    }
                    const found = findNote(window.__INITIAL_STATE__, '""" + note_id + """', 0);
                    if (found && found.imageList) {
                        return JSON.stringify(found.imageList.map(img => img.urlDefault || img.url || ''));
                    }
                    return "[]";
                })()
                """
            })
            image_urls = json.loads(img_result.get('result', {}).get('result', {}).get('value', '[]'))
            
            img_count = 0
            for i, url in enumerate(image_urls):
                if not url: continue
                ext = "webp" if "webp" in url else "jpg"
                img_path = os.path.join(folder, f"{i+1}.{ext}")
                success, size = download_image(url, img_path)
                if success:
                    img_count += 1
                    if ext == "webp":
                        jpg_path = os.path.join(folder, f"{i+1}.jpg")
                        try:
                            subprocess.run(f'python3 -c "from PIL import Image; Image.open(\'{img_path}\').convert(\'RGB\').save(\'{jpg_path}\', \'JPEG\'); import os; os.remove(\'{img_path}\')"', shell=True, timeout=10)
                        except: pass
            
            if text:
                with open(os.path.join(folder, "内容.txt"), 'w') as f:
                    f.write(text)
            
            downloaded += 1
            status = "✅" if text and img_count > 0 else ("⚠️" if text else "❌")
            print(f"  [{downloaded}/{len(todo)}] {status} {title[:40]} ({img_count}张, {len(text)}字)")
            
        except Exception as e:
            errors.append(f"{title}: {e}")
            print(f"  ❌ {title[:30]}: {e}")
            try: ws.close()
            except: pass
            ws = get_ws()
            time.sleep(3)
        
        time.sleep(2)
    
    try: ws.close()
    except: pass
    
    print(f"\n=== 完成: {downloaded}/{len(todo)} ===")
    if errors:
        print(f"错误: {len(errors)}")
        for e in errors[:5]: print(f"  {e}")

if __name__ == "__main__":
    main()
