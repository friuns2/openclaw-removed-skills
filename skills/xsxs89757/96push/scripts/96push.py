#!/usr/bin/env python3
"""96Push remote control CLI — wraps the proxy API for OpenClaw skills."""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

BASE_URL = "https://api.96.cn/api/push/proxy"

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv", ".wmv"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def media_extension(value: str) -> str:
    parsed = urllib.parse.urlparse((value or "").strip())
    path = parsed.path or value
    _, ext = os.path.splitext(path)
    return ext.lower()


def media_kind(value: str) -> str:
    raw = (value or "").strip()
    if raw.startswith("data:video/"):
        return "video"
    if raw.startswith("data:image/"):
        return "image"
    ext = media_extension(raw)
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    return ""


def content_type_from_publish_type(value) -> str:
    try:
        publish_type = int(value)
    except (TypeError, ValueError):
        return ""
    return {1: "article", 2: "graph_text", 3: "video"}.get(publish_type, "")


def infer_type_from_files(files: list[str]) -> str:
    kinds = [media_kind(item) for item in files]
    if any(kind == "video" for kind in kinds):
        return "video"
    if any(kind == "image" for kind in kinds):
        return "graph_text"
    return ""


def infer_type_from_content_detail(content_id: int) -> str:
    detail = request("GET", f"article/get/{content_id}")
    if not isinstance(detail, dict) or "error" in detail:
        return ""

    data = detail.get("data", detail)
    if not isinstance(data, dict):
        return ""

    content_type = content_type_from_publish_type(data.get("publish_type"))
    publish_data = data.get("publish_data") or {}
    if isinstance(publish_data, dict):
        inferred = infer_type_from_files(publish_data.get("files") or [])
        if inferred:
            return inferred
    return content_type


def resolve_content_type(explicit_type: str | None, files: list[str] | None = None, content_id: int | None = None) -> str:
    if explicit_type:
        if explicit_type == "article":
            inferred = infer_type_from_files(files or [])
            if inferred:
                return inferred
            if content_id is not None:
                inferred = infer_type_from_content_detail(content_id)
                if inferred in {"graph_text", "video"}:
                    return inferred
        return explicit_type
    inferred = infer_type_from_files(files or [])
    if inferred:
        return inferred
    if content_id is not None:
        inferred = infer_type_from_content_detail(content_id)
        if inferred:
            return inferred
    return "article"


def get_api_key() -> str:
    key = os.environ.get("PUSH_API_KEY", "").strip()
    if key:
        return key
    env_file = os.path.expanduser("~/.openclaw/.env")
    if os.path.isfile(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("PUSH_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def request(method: str, path: str, body: dict | None = None, query: dict | None = None, timeout: int = 30) -> dict:
    api_key = get_api_key()
    if not api_key:
        return {
            "error": "PUSH_API_KEY not configured",
            "setup": [
                "1. Download 96Push from https://push.96.cn",
                "2. Launch and login",
                "3. Go to profile (bottom-left avatar) → API Key → Generate",
                "4. Add to ~/.openclaw/.env: PUSH_API_KEY=pk_your_key_here",
            ],
        }

    url = f"{BASE_URL}/{path.lstrip('/')}"
    if query:
        url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})

    headers = {
        "X-Push-Api-Key": api_key,
        "Content-Type": "application/json",
    }

    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read())
        except Exception:
            err_body = {}
        return {"error": f"HTTP {e.code}", "detail": err_body}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}"}
    except TimeoutError:
        return {"error": "Request timed out"}


# ── Query commands ──────────────────────────────────────────────

def cmd_check(_args):
    return request("GET", "check")


def cmd_platforms(args):
    q = {"simple": "true"}
    if args.article:
        q["article"] = "true"
    if args.graph_text:
        q["graph_text"] = "true"
    if args.video:
        q["video"] = "true"
    return request("GET", "platform/list", query=q)


def cmd_accounts(args):
    q = {}
    if args.simple:
        q["simple"] = "1"
    return request("GET", "account/logged", query=q)


def cmd_all_accounts(_args):
    return request("GET", "account/list", query={"simple": "1"})


def cmd_articles(args):
    q = {"current": str(args.page), "size": str(args.size), "simple": "true"}
    if args.status is not None:
        q["status"] = str(args.status)
    return request("GET", "article/list", query=q)


def cmd_article(args):
    return request("GET", f"article/get/{args.id}")


def cmd_records(args):
    q = {"current": str(args.page), "size": str(args.size)}
    if args.status:
        q["status"] = str(args.status)
    return request("GET", "record/list", query=q)


def cmd_record(args):
    return request("GET", f"record/info/{args.id}")


def cmd_dashboard(_args):
    return request("GET", "home/dashboard")


def cmd_overview(_args):
    return request("GET", "home/overview")


def cmd_user(_args):
    return request("GET", "user/info")


def cmd_plat_sets(args):
    return request("GET", f"platSet/list/{args.pid}")


# ── Content creation ────────────────────────────────────────────

def cmd_create(args):
    thumb = json.loads(args.thumb) if args.thumb else []
    files = json.loads(args.files) if args.files else []
    content_type = resolve_content_type(args.type, files=files)

    body = {
        "title": args.title,
        "desc": args.desc or "",
        "content": args.content or "",
        "markdown": args.markdown or "",
        "autoThumb": not args.no_auto_thumb,
        "thumb": thumb,
        "files": files if content_type != "article" else [],
    }

    endpoints = {
        "article": "article/create",
        "graph_text": "article/graphText",
        "video": "article/video",
    }
    return request("POST", endpoints.get(content_type, "article/create"), body=body)


def cmd_update(args):
    thumb = json.loads(args.thumb) if args.thumb else []
    files = json.loads(args.files) if args.files else []
    content_type = resolve_content_type(args.type, files=files, content_id=args.id)

    body = {
        "title": args.title,
        "desc": args.desc or "",
        "content": args.content or "",
        "markdown": args.markdown or "",
        "autoThumb": not args.no_auto_thumb,
        "thumb": thumb,
        "files": files if content_type != "article" else [],
    }
    return request("POST", f"article/update/{args.id}", body=body)


def cmd_delete_article(args):
    return request("DELETE", f"article/delete/{args.id}")


# ── Publishing ──────────────────────────────────────────────────

def cmd_publish(args):
    if not getattr(args, "force", False):
        active = request("GET", "record/list", query={"current": "1", "size": "5"})
        active_list = active.get("list", []) if isinstance(active, dict) else []
        busy = [r for r in active_list if r.get("status") in (1, 5)]
        if busy:
            names = {1: "发布中", 5: "排队中"}
            items = [f"#{r['id']}({names.get(r.get('status'), '?')})" for r in busy[:3]]
            print(f"[info] 当前有任务: {', '.join(items)}，新任务将自动入队", file=sys.stderr)

    if args.accounts_json:
        accounts = json.loads(args.accounts_json)
    elif args.accounts:
        accounts = []
        for a in args.accounts.split(","):
            a = a.strip()
            if a:
                accounts.append({"id": int(a), "platName": "", "settings": {}})
    else:
        return {"error": "Either --accounts or --accounts-json is required"}

    body = {
        "headless": True,
        "syncDraft": args.draft,
        "postAccounts": accounts,
    }
    content_type = resolve_content_type(args.type, content_id=args.id)
    endpoints = {
        "article": f"publish/article/{args.id}",
        "graph_text": f"publish/graphText/{args.id}",
        "video": f"publish/video/{args.id}",
    }
    result = request("POST", endpoints.get(content_type, f"publish/article/{args.id}"), body=body, timeout=60)

    # 自动 poll 等待结果（除非 --no-wait）
    if getattr(args, "no_wait", False):
        return result

    if "error" in result:
        return result

    data = result.get("data", result)
    rid = data.get("publishRecordId")
    if not rid:
        return result

    print(f"[publish] 已提交，recordId={rid}，等待完成...", file=sys.stderr)

    max_attempts = 200
    interval = 5
    for i in range(max_attempts):
        time.sleep(interval)
        rec = request("GET", "record/list", query={"current": "1", "size": "10"})
        rec_list = rec.get("list", []) if isinstance(rec, dict) else []
        target = next((r for r in rec_list if r.get("id") == rid), None)
        if not target:
            continue
        status = target.get("status", 1)
        if status == 6:
            return {"publish": "cancelled", "record": target, "detail": []}
        if status not in (1, 5):
            info = request("GET", f"record/info/{rid}")
            detail = info if isinstance(info, list) else info.get("data", [])
            return {
                "publish": "done",
                "record": target,
                "detail": detail if isinstance(detail, list) else [],
            }
        qpos = target.get("queue_position")
        if qpos is not None and status == 5:
            print(f"[poll {i+1}/{max_attempts}] 排队中，位置: {qpos}", file=sys.stderr)
        elif status == 1:
            print(f"[poll {i+1}/{max_attempts}] 发布中...", file=sys.stderr)

    return {
        "publish": "timeout",
        "publishRecordId": rid,
        "message": f"Record {rid} still active after {max_attempts * interval // 60}min",
    }


def cmd_poll(args):
    rid = args.id
    max_attempts = args.max or 60
    interval = args.interval or 5

    for i in range(max_attempts):
        rec = request("GET", "record/list", query={"current": "1", "size": "10"})
        rec_list = rec.get("list", []) if isinstance(rec, dict) else []
        target = next((r for r in rec_list if r.get("id") == rid), None)

        if target:
            status = target.get("status", 1)
            # status 6 = Cancelled — terminal state
            if status == 6:
                return {
                    "poll": "cancelled",
                    "attempts": i + 1,
                    "record": target,
                    "detail": [],
                }
            # status 1 = Publishing, status 5 = Queued — still waiting
            if status not in (1, 5):
                info = request("GET", f"record/info/{rid}")
                detail = info if isinstance(info, list) else info.get("data", [])
                return {
                    "poll": "done",
                    "attempts": i + 1,
                    "record": target,
                    "detail": detail if isinstance(detail, list) else [],
                }
            # Show queue position if available
            qpos = target.get("queue_position")
            if qpos is not None and status == 5:
                print(f"[poll {i+1}/{max_attempts}] 排队中，位置: {qpos}", file=sys.stderr)
            elif status == 1:
                print(f"[poll {i+1}/{max_attempts}] 发布中...", file=sys.stderr)

        if i < max_attempts - 1:
            time.sleep(interval)

    return {
        "poll": "timeout",
        "attempts": max_attempts,
        "message": f"Record {rid} still active after {max_attempts * interval}s. The browser automation may be stuck or the daemon needs restart.",
    }


def cmd_queue(_args):
    return request("GET", "queue/list")


def cmd_cancel_queue(args):
    return request("POST", f"queue/cancel/{args.id}")


# ── Platform settings management ────────────────────────────────

def cmd_create_plat_set(args):
    body = {
        "name": args.name,
        "description": args.description or "",
        "platform_id": args.pid,
        "setting": json.loads(args.setting),
    }
    return request("POST", "platSet/create", body=body)


def cmd_update_plat_set(args):
    body = {
        "name": args.name,
        "description": args.description or "",
        "platform_id": args.pid,
        "setting": json.loads(args.setting),
    }
    return request("POST", f"platSet/update/{args.sid}", body=body)


def cmd_delete_plat_set(args):
    return request("DELETE", f"platSet/delete/{args.sid}")


# ── Main ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="96Push remote control")
    sub = parser.add_subparsers(dest="command", required=True)

    # Query
    sub.add_parser("check", help="Health check — is client online?")

    p = sub.add_parser("platforms", help="List supported platforms")
    p.add_argument("--article", action="store_true")
    p.add_argument("--graph-text", action="store_true")
    p.add_argument("--video", action="store_true")

    p = sub.add_parser("accounts", help="List logged-in accounts")
    p.add_argument("--simple", action="store_true", default=True)

    sub.add_parser("all-accounts", help="List all accounts (including logged out)")

    p = sub.add_parser("articles", help="List articles")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--size", type=int, default=10)
    p.add_argument("--status", type=int, default=None, help="1=draft, 2=published")

    p = sub.add_parser("article", help="Get article detail")
    p.add_argument("--id", type=int, required=True)

    p = sub.add_parser("records", help="List publish records")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--size", type=int, default=10)
    p.add_argument("--status", type=int, default=None, help="1=publishing,2=all_failed,3=partial,4=all_success")

    p = sub.add_parser("record", help="Get publish record detail")
    p.add_argument("--id", type=int, required=True)

    sub.add_parser("dashboard", help="Dashboard summary")
    sub.add_parser("overview", help="Overview with charts")
    sub.add_parser("user", help="Current user info")

    p = sub.add_parser("plat-sets", help="List platform publish configs")
    p.add_argument("--pid", type=int, required=True, help="Platform ID")

    # Content creation
    p = sub.add_parser("create", help="Create content")
    p.add_argument("--type", choices=["article", "graph_text", "video"], default=None, help="Content type. If omitted, inferred from --files")
    p.add_argument("--title", required=True)
    p.add_argument("--desc", default="", help="Description/summary")
    p.add_argument("--content", default="", help="HTML content (for article)")
    p.add_argument("--markdown", default="", help="Markdown source (for article)")
    p.add_argument("--files", default="", help='JSON array of public HTTP(S) URLs (images for graph_text, video URL for video)')
    p.add_argument("--thumb", default="", help='JSON array of cover image public HTTP(S) URLs')
    p.add_argument("--no-auto-thumb", action="store_true", help="Disable auto cover extraction from content")

    p = sub.add_parser("update", help="Update existing content")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--type", choices=["article", "graph_text", "video"], default=None, help="Content type. If omitted, inferred from existing content/files")
    p.add_argument("--title", required=True)
    p.add_argument("--desc", default="")
    p.add_argument("--content", default="")
    p.add_argument("--markdown", default="")
    p.add_argument("--files", default="")
    p.add_argument("--thumb", default="")
    p.add_argument("--no-auto-thumb", action="store_true")

    p = sub.add_parser("delete-article", help="Delete content")
    p.add_argument("--id", type=int, required=True)

    # Publish
    p = sub.add_parser("publish", help="Submit async publish task")
    p.add_argument("--type", choices=["article", "graph_text", "video"], default=None, help="Content type. If omitted, inferred from content detail")
    p.add_argument("--id", type=int, required=True, help="Content ID to publish")
    p.add_argument("--accounts", default="", help="Simple mode: comma-separated account IDs (no settings)")
    p.add_argument("--accounts-json", default="", help='Advanced: JSON array of {"id":N,"platName":"...","settings":{...}}')
    p.add_argument("--draft", action="store_true", help="Save as draft only (syncDraft)")
    p.add_argument("--force", action="store_true", help="Skip active-publish check (dangerous, can create duplicates)")
    p.add_argument("--no-wait", action="store_true", help="Return immediately without polling for result")

    p = sub.add_parser("poll", help="Poll publish result")
    p.add_argument("--id", type=int, required=True, help="publishRecordId")
    p.add_argument("--max", type=int, default=40, help="Max poll attempts (default 40 × 5s = 200s)")
    p.add_argument("--interval", type=int, default=5, help="Seconds between polls")

    sub.add_parser("queue", help="Show current publish queue")

    p = sub.add_parser("cancel-queue", help="Cancel a queued publish task")
    p.add_argument("--id", type=int, required=True, help="publishRecordId to cancel")

    # Platform setting management
    p = sub.add_parser("create-plat-set", help="Create a platform publish config")
    p.add_argument("--pid", type=int, required=True, help="Platform ID")
    p.add_argument("--name", required=True, help="Config name")
    p.add_argument("--description", default="")
    p.add_argument("--setting", required=True, help="JSON object of platform settings")

    p = sub.add_parser("update-plat-set", help="Update a platform publish config")
    p.add_argument("--sid", type=int, required=True, help="Setting ID")
    p.add_argument("--pid", type=int, required=True, help="Platform ID")
    p.add_argument("--name", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--setting", required=True, help="JSON object of platform settings")

    p = sub.add_parser("delete-plat-set", help="Delete a platform publish config")
    p.add_argument("--sid", type=int, required=True, help="Setting ID")

    args = parser.parse_args()

    handlers = {
        "check": cmd_check,
        "platforms": cmd_platforms,
        "accounts": cmd_accounts,
        "all-accounts": cmd_all_accounts,
        "articles": cmd_articles,
        "article": cmd_article,
        "create": cmd_create,
        "update": cmd_update,
        "delete-article": cmd_delete_article,
        "publish": cmd_publish,
        "poll": cmd_poll,
        "queue": cmd_queue,
        "cancel-queue": cmd_cancel_queue,
        "records": cmd_records,
        "record": cmd_record,
        "dashboard": cmd_dashboard,
        "overview": cmd_overview,
        "user": cmd_user,
        "plat-sets": cmd_plat_sets,
        "create-plat-set": cmd_create_plat_set,
        "update-plat-set": cmd_update_plat_set,
        "delete-plat-set": cmd_delete_plat_set,
    }

    result = handlers[args.command](args)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
