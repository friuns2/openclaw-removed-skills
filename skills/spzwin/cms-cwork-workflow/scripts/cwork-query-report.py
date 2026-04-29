#!/usr/bin/env python3
"""
CWork Query Reports - Agent-First

Modes: inbox / outbox / unread / detail / node-detail / sender-history / keyword-search / pending / my-sent

Usage:
  python3 scripts/cwork-query-report.py --mode inbox [--page-size 20]
  python3 scripts/cwork-query-report.py --mode detail --report-id <id>
  python3 scripts/cwork-query-report.py --mode node-detail --report-id <id>
  python3 scripts/cwork-query-report.py --mode sender-history --sender-emp-id <empId>
  python3 scripts/cwork-query-report.py --mode keyword-search --keyword "公章"
  python3 scripts/cwork-query-report.py --mode pending
  python3 scripts/cwork-query-report.py --mode unread
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cwork_client import CWorkClient, make_client, CWorkError, apply_params_file_pre_parse


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="CWork query reports (Agent-First)")
    parser.add_argument("--mode", required=True,
                        choices=["inbox", "outbox", "unread", "detail", "node-detail", "sender-history", "keyword-search", "pending", "my-sent"])
    parser.add_argument("--page-index", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--report-id", help="Report ID (required for detail/node-detail)")
    parser.add_argument("--sender-emp-id", help="Sender employee ID (required for sender-history)")
    parser.add_argument("--keyword", help="Search keyword (required for keyword-search)")
    parser.add_argument("--days", type=int, default=90, help="Days to look back (default 90)")
    parser.add_argument("--report-type", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--status", type=int, help="Read status: 0=unread 1=read")
    parser.add_argument("--keyword-filter", help="Legacy: Keyword filter")
    parser.add_argument("--start-date", help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", help="End date YYYY-MM-DD")
    parser.add_argument("--with-share-link", dest="with_share_link", action="store_true", default=True,
                        help="在返回结果中补充分享链接（默认开启）")
    parser.add_argument("--no-share-link", dest="with_share_link", action="store_false",
                        help="关闭分享链接补充")
    parser.add_argument("--share-top-n", type=int, default=20,
                        help="列表场景最多补充前 N 条分享链接（默认 20，0=当前页全部）")
    parser.add_argument("--params-file", dest="params_file", default=None,
                        help="UTF-8 JSON 文件路径，从文件读取参数")
    return parser.parse_args(argv)


def _parse_date(value, end_of_day: bool = False):
    """Convert YYYY-MM-DD to millisecond timestamp (always interpreted as UTC+8).

    Binds the date to UTC+8 explicitly so the result is identical regardless of
    the system timezone where the script is executed.

    end_of_day=True: returns 23:59:59.999 CST of that day so --end-date covers
    the full Beijing calendar day (e.g. 2026-04-07 → 2026-04-07T23:59:59.999+08:00).
    """
    if value is None:
        return None
    from datetime import datetime, timedelta, timezone
    _CST = timezone(timedelta(hours=8))
    try:
        dt = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=_CST)
        if end_of_day:
            dt = dt + timedelta(days=1) - timedelta(milliseconds=1)
        return int(dt.timestamp() * 1000)
    except ValueError:
        return None


def _die(msg):
    print(json.dumps({"success": False, "error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


def _extract_first_id(item, candidates):
    if not isinstance(item, dict):
        return None
    for key in candidates:
        value = item.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def _safe_attach_share_link(client, item, biz_type: int, id_candidates: tuple[str, ...]):
    if not isinstance(item, dict):
        return
    biz_id = _extract_first_id(item, id_candidates)
    if biz_id is None:
        return
    try:
        item["shareLink"] = client.create_share_link(biz_id, biz_type)
    except Exception:
        # 分享链接失败不阻断主查询结果
        return


def _attach_share_links_to_list(client, rows, biz_type: int, id_candidates: tuple[str, ...], top_n: int):
    if not isinstance(rows, list):
        return
    limit = len(rows) if top_n <= 0 else top_n
    for idx, row in enumerate(rows):
        if idx >= limit:
            break
        _safe_attach_share_link(client, row, biz_type, id_candidates)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    apply_params_file_pre_parse()
    args = parse_args()
    try:
        client = make_client()
    except CWorkError as e:
        _die(str(e))

    try:
        if args.mode == "detail":
            if not args.report_id:
                _die("--report-id is required for detail mode")
            data = client.get_report_info(args.report_id)
            if args.with_share_link:
                _safe_attach_share_link(client, data, 1, ("reportId", "id"))
            print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))
            return

        if args.mode == "node-detail":
            if not args.report_id:
                _die("--report-id is required for node-detail mode")
            data = client.get_report_node_detail(args.report_id)
            if args.with_share_link:
                _safe_attach_share_link(client, data, 1, ("reportId", "id"))
            print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))
            return

        if args.mode == "sender-history":
            if not args.sender_emp_id:
                _die("--sender-emp-id is required for sender-history mode")
            data = client.get_sender_history(
                sender_emp_id=args.sender_emp_id,
                days=args.days,
                max_count=args.page_size
            )
            if args.with_share_link:
                _attach_share_links_to_list(client, data.get("recentReports"), 1, ("reportId", "id"), args.share_top_n)
            print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))
            return

        if args.mode == "keyword-search":
            if not args.keyword:
                _die("--keyword is required for keyword-search mode")
            data = client.search_reports_by_keyword(
                keyword=args.keyword,
                days=args.days,
                max_count=args.page_size
            )
            if args.with_share_link:
                _attach_share_links_to_list(client, data.get("reports"), 1, ("reportId", "id"), args.share_top_n)
            print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))
            return

        if args.mode == "unread":
            data = client.get_unread_list(args.page_index, args.page_size)
            if args.with_share_link:
                _attach_share_links_to_list(client, data.get("list"), 1, ("reportId", "id"), args.share_top_n)
            print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))
            return

        read_status = args.status
        if args.mode == "pending":
            read_status = 0

        if args.mode in ("inbox", "pending"):
            data = client.get_inbox_list(
                page_size=args.page_size, page_index=args.page_index,
                report_record_type=args.report_type, read_status=read_status,
                begin_time=_parse_date(args.start_date), end_time=_parse_date(args.end_date, end_of_day=True))
        else:
            data = client.get_outbox_list(
                page_size=args.page_size, page_index=args.page_index,
                report_record_type=args.report_type,
                begin_time=_parse_date(args.start_date), end_time=_parse_date(args.end_date, end_of_day=True))

        if args.with_share_link:
            _attach_share_links_to_list(client, data.get("list"), 1, ("reportId", "id"), args.share_top_n)

        print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))

    except CWorkError as e:
        _die(str(e))


if __name__ == "__main__":
    main()
