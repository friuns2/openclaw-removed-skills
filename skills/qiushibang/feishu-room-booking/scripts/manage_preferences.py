#!/usr/bin/env python3
"""
用户会议室偏好管理 - 简化版（仅按工区维护会议室偏好列表）

用法:
  # 设置偏好（指定工区 + 会议室列表）
  python3 manage_preferences.py --set --user "ou_xxx" --building "丽金智地中心 西塔" \
    --preferred-rooms "F11-15,F11-07"

  # 读取偏好（指定工区）
  python3 manage_preferences.py --get --user "ou_xxx" --building "丽金智地中心 西塔"

  # 读取所有偏好
  python3 manage_preferences.py --get --user "ou_xxx"

  # 列出所有用户偏好
  python3 manage_preferences.py --list

  # 删除指定工区的偏好
  python3 manage_preferences.py --delete --user "ou_xxx" --building "丽金智地中心 西塔"

  # 删除用户全部偏好
  python3 manage_preferences.py --delete --user "ou_xxx"
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PREFS_FILE = SCRIPT_DIR.parent / "references" / "user-preferences.json"


def load_prefs():
    if not PREFS_FILE.exists():
        return {"preferences": {}}
    with open(PREFS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_prefs(data):
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cmd_set(args):
    """设置用户在指定工区的会议室偏好"""
    data = load_prefs()
    prefs = data.setdefault("preferences", {})

    if not args.building:
        print("错误: --set 需要 --building 指定工区")
        sys.exit(1)

    user_prefs = prefs.setdefault(args.user, {"buildings": {}})
    buildings = user_prefs.setdefault("buildings", {})

    rooms = [r.strip() for r in args.preferred_rooms.split(",")] if args.preferred_rooms else []
    buildings[args.building] = {"preferred_rooms": rooms}

    prefs[args.user] = user_prefs
    save_prefs(data)

    print(f"✅ 已保存 {args.user} 在 {args.building} 的偏好:")
    print(f"   偏好会议室: {', '.join(rooms) or '无'}")


def cmd_get(args):
    """获取用户偏好"""
    data = load_prefs()
    user_prefs = data.get("preferences", {}).get(args.user)

    if not user_prefs:
        print(f"❌ 未找到 {args.user} 的偏好设置")
        return None

    if args.building:
        buildings = user_prefs.get("buildings", {})
        bp = buildings.get(args.building)
        if not bp:
            print(f"❌ 未找到 {args.user} 在 {args.building} 的偏好")
            return None
        result = {
            "building": args.building,
            "preferred_rooms": bp.get("preferred_rooms", [])
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    print(json.dumps(user_prefs, ensure_ascii=False, indent=2))
    return user_prefs


def cmd_list():
    """列出所有用户偏好"""
    data = load_prefs()
    prefs = data.get("preferences", {})
    if not prefs:
        print("还没有任何用户偏好设置")
        return
    for user_id, p in prefs.items():
        buildings = p.get("buildings", {})
        print(f"👤 {user_id}")
        if buildings:
            for bname, bp in buildings.items():
                rooms = ", ".join(bp.get("preferred_rooms", [])) or "无"
                print(f"   🏢 {bname}: {rooms}")
        else:
            print("   ⚠️ 未设置任何工区偏好")


def cmd_delete(args):
    """删除偏好"""
    data = load_prefs()
    prefs = data.get("preferences", {})
    user_prefs = prefs.get(args.user)

    if not user_prefs:
        print(f"❌ 未找到 {args.user} 的偏好设置")
        return

    if args.building:
        buildings = user_prefs.get("buildings", {})
        if args.building in buildings:
            del buildings[args.building]
            save_prefs(data)
            print(f"✅ 已删除 {args.user} 在 {args.building} 的偏好")
        else:
            print(f"❌ 未找到 {args.user} 在 {args.building} 的偏好")
    else:
        del prefs[args.user]
        save_prefs(data)
        print(f"✅ 已删除 {args.user} 的全部偏好")


def main():
    parser = argparse.ArgumentParser(description="用户会议室偏好管理（简化版）")
    parser.add_argument("--set", action="store_true", help="设置偏好")
    parser.add_argument("--get", action="store_true", help="读取偏好")
    parser.add_argument("--list", action="store_true", help="列出所有偏好")
    parser.add_argument("--delete", action="store_true", help="删除偏好")
    parser.add_argument("--user", "-u", required=True, help="用户 open_id")
    parser.add_argument("--building", "-b", help="工区名称")
    parser.add_argument("--preferred-rooms", help="偏好会议室（逗号分隔，如 F11-15,F11-07）")

    args = parser.parse_args()

    if args.set:
        cmd_set(args)
    elif args.get:
        cmd_get(args)
    elif args.list:
        cmd_list()
    elif args.delete:
        cmd_delete(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
