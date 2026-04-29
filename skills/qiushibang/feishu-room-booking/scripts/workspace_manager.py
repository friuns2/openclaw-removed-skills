#!/usr/bin/env python3
"""
工区管理 - 支持随时切换 + 周期兜底

用法:
  # 获取当前工区（根据今天日期自动匹配）
  python3 workspace_manager.py --get

  # 设置工区（多种模式）
  python3 workspace_manager.py --set --workspace "丽金智地中心 B座"          # 从今天开始
  python3 workspace_manager.py --set --workspace "丽金" --from "2026-04-30"  # 从指定日期开始
  python3 workspace_manager.py --set --workspace "紫金" --from "2026-04-30" --to "2026-04-30"  # 指定日期范围

  # 设置下周工区
  python3 workspace_manager.py --set-next --workspace "紫金数码园4号楼"

  # 推荐下周工区
  python3 workspace_manager.py --recommend

  # 检查是否需要周五提醒（给 heartbeat 用）
  python3 workspace_manager.py --check-friday-reminder

  # 清空下周设置
  python3 workspace_manager.py --clear-next

  # 查看完整工区时间线
  python3 workspace_manager.py --timeline
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).parent
WORKSPACE_FILE = SCRIPT_DIR.parent / "references" / "weekly-workspace.json"
PREFS_FILE = SCRIPT_DIR.parent / "references" / "user-preferences.json"


def load_workspace():
    if not WORKSPACE_FILE.exists():
        return {"segments": [], "next_week": None}
    with open(WORKSPACE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_workspace(data):
    with open(WORKSPACE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_today():
    return date.today().isoformat()


def get_current_week_start():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return monday.isoformat()


def get_next_week_start():
    today = date.today()
    next_monday = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
    return next_monday.isoformat()


def get_current_week_end():
    today = date.today()
    sunday = today - timedelta(days=today.weekday()) + timedelta(days=6)
    return sunday.isoformat()


def find_current_workspace(data, target_date=None):
    """根据日期找到当前生效的工区"""
    if target_date is None:
        target_date = get_today()
    
    # 按 from 日期降序排列，找到第一个覆盖今天日期的 segment
    segments = data.get("segments", [])
    valid_segments = []
    for seg in segments:
        seg_from = seg.get("from", "")
        seg_to = seg.get("to", "")
        if seg_from and seg_to and seg_from <= target_date <= seg_to:
            valid_segments.append(seg)
    
    if not valid_segments:
        return None
    
    # 返回最精确匹配（to 最近的）
    valid_segments.sort(key=lambda s: s.get("to", ""), reverse=True)
    return valid_segments[0].get("workspace")


def cmd_get(args):
    """获取当前工区信息"""
    data = load_workspace()
    today = get_today()
    
    current = find_current_workspace(data, today)
    
    next_w = data.get("next_week")
    next_week_start = get_next_week_start()
    
    print(f"📅 今天: {today} ({_weekday_name(today)})")
    if current:
        seg = _find_segment(data, today)
        print(f"📍 当前工区: {current}")
        if seg:
            print(f"   有效期: {seg.get('from', '?')} ~ {seg.get('to', '?')}")
    else:
        print(f"⚠️ 未设置当前工区")
    
    print(f"\n📅 下周 ({next_week_start} 起):")
    if next_w and next_w.get("workspace"):
        print(f"   🏢 工区: {next_w['workspace']}")
    else:
        print(f"   ⚠️ 未设置下周工区")
    
    return {"current_workspace": current, "next_week": next_w, "today": today}


def cmd_set(args):
    """设置工区"""
    data = load_workspace()
    today = get_today()
    
    workspace = args.workspace
    from_date = args.from_date or today
    to_date = args.to_date
    
    if not to_date:
        # 如果没指定结束日期，默认覆盖到本周日
        week_end = get_current_week_end()
        # 如果 from_date 不在本周，to_date 设为 from_date 的周日
        from_dt = date.fromisoformat(from_date)
        if from_dt.weekday() == 6:  # 周六
            to_date = from_date
        else:
            to_date = (from_dt + timedelta(days=(6 - from_dt.weekday()))).isoformat()
    
    # 清理与新区间重叠的旧 segments
    segments = data.get("segments", [])
    # 简单策略：移除完全被新区间覆盖的旧 segments
    # 保留不重叠的
    new_segments = []
    for seg in segments:
        seg_from = seg.get("from", "")
        seg_to = seg.get("to", "")
        # 如果旧区间被新区间完全包含，跳过
        if from_date <= seg_from and to_date >= seg_to:
            continue
        # 如果完全不重叠，保留
        if to_date < seg_from or from_date > seg_to:
            new_segments.append(seg)
        # 部分重叠：截断旧区间
        else:
            # 保留 from_date 之前的部分
            if seg_from < from_date:
                new_segments.append({**seg, "to": from_date})
            # 保留 to_date 之后的部分
            if seg_to > to_date:
                new_segments.append({**seg, "from": to_date})
    
    # 添加新区间
    new_segments.append({
        "from": from_date,
        "to": to_date,
        "workspace": workspace,
        "set_at": datetime.now().isoformat(),
        "set_by": "manual"
    })
    
    # 按 from 排序
    new_segments.sort(key=lambda s: s.get("from", ""))
    data["segments"] = new_segments
    
    save_workspace(data)
    
    print(f"✅ 工区已设置: {workspace}")
    print(f"   有效期: {from_date} ~ {to_date}")
    
    if from_date <= today <= to_date:
        print(f"   📍 今天({today})已生效")


def cmd_set_next(args):
    """设置下周工区"""
    data = load_workspace()
    week_start = get_next_week_start()
    data["next_week"] = {
        "week_start": week_start,
        "workspace": args.workspace,
        "set_at": datetime.now().isoformat(),
        "set_by": "manual"
    }
    save_workspace(data)
    print(f"✅ 下周工区已设置: {args.workspace}")
    print(f"   周起始: {week_start}")


def cmd_clear_next(args):
    """清空下周设置"""
    data = load_workspace()
    data["next_week"] = None
    save_workspace(data)
    print("✅ 已清空下周工区设置")


def cmd_recommend(args):
    """基于历史选择推荐工区"""
    if not PREFS_FILE.exists():
        print("❌ 没有偏好数据，无法推荐")
        return
    
    with open(PREFS_FILE, "r", encoding="utf-8") as f:
        prefs_data = json.load(f)
    
    all_selections = []
    for user_id, user_prefs in prefs_data.get("preferences", {}).items():
        history = user_prefs.get("selection_history", [])
        for entry in history:
            all_selections.append(entry.get("building", ""))
    
    if not all_selections:
        print("❌ 没有历史选择记录，无法推荐")
        return
    
    recent = all_selections[-30:]
    building_counts = Counter(b for b in recent if b)
    
    if not building_counts:
        print("❌ 没有有效的工区记录")
        return
    
    print("📊 工区使用统计（最近 30 次选择）:")
    for building, count in building_counts.most_common():
        bar = "█" * count
        print(f"   {building}: {bar} ({count})")
    
    recommended = building_counts.most_common(1)[0][0]
    print(f"\n💡 推荐工区: {recommended}")


def cmd_check_friday_reminder(args):
    """检查是否需要周五提醒（给 heartbeat 用）"""
    data = load_workspace()
    next_w = data.get("next_week")
    
    if next_w and next_w.get("workspace"):
        # 已设置下周，不需要提醒
        print("NO_REMINDER")
        return
    
    # 没设置，需要提醒
    print("NEED_REMINDER")
    cmd_recommend(args)


def cmd_timeline(args):
    """查看工区时间线"""
    data = load_workspace()
    segments = data.get("segments", [])
    today = get_today()
    
    print("📅 工区时间线:")
    print(f"   今天: {today} ({_weekday_name(today)})")
    
    if not segments:
        print("   (暂无工区设置)")
        return
    
    for seg in segments:
        seg_from = seg.get("from", "?")
        seg_to = seg.get("to", "?")
        workspace = seg.get("workspace", "?")
        
        # 标记今天
        marker = ""
        if seg_from <= today <= seg_to:
            marker = " ◄ 今天"
        
        print(f"   {seg_from} ~ {seg_to}: {workspace}{marker}")


def _weekday_name(date_str):
    """获取星期几的中文名"""
    try:
        dt = date.fromisoformat(date_str)
        names = ["一", "二", "三", "四", "五", "六", "日"]
        return f"周{names[dt.weekday()]}"
    except:
        return ""


def _find_segment(data, target_date):
    """找到包含指定日期的 segment"""
    for seg in data.get("segments", []):
        if seg.get("from", "") <= target_date <= seg.get("to", ""):
            return seg
    return None


def main():
    parser = argparse.ArgumentParser(description="工区管理（支持随时切换 + 周期兜底）")
    sub = parser.add_subparsers(dest="command")
    
    sub.add_parser("get", help="获取当前工区")
    
    p_set = sub.add_parser("set", help="设置工区")
    p_set.add_argument("--workspace", "-w", required=True, help="工区名称")
    p_set.add_argument("--from", dest="from_date", help="开始日期 (默认今天)")
    p_set.add_argument("--to", dest="to_date", help="结束日期 (默认本周日)")
    
    p_next = sub.add_parser("set-next", help="设置下周工区")
    p_next.add_argument("--workspace", "-w", required=True, help="下周工区")
    
    sub.add_parser("clear-next", help="清空下周工区设置")
    sub.add_parser("recommend", help="推荐工区")
    sub.add_parser("check-friday-reminder", help="检查是否需要周五提醒")
    sub.add_parser("timeline", help="查看工区时间线")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "get":
        cmd_get(args)
    elif args.command == "set":
        cmd_set(args)
    elif args.command == "set-next":
        cmd_set_next(args)
    elif args.command == "clear-next":
        cmd_clear_next(args)
    elif args.command == "recommend":
        cmd_recommend(args)
    elif args.command == "check-friday-reminder":
        cmd_check_friday_reminder(args)
    elif args.command == "timeline":
        cmd_timeline(args)


if __name__ == "__main__":
    main()
