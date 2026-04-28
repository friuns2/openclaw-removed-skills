#!/usr/bin/env python3
"""
cwork-todo.py — 待办管理

功能：
1. 查询待办列表
2. 完成待办

用法：
    python3 cwork-todo.py list --page-size 20 --status pending
    python3 cwork-todo.py complete --todo-id <id> --content "已完成"
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cwork_client import make_client, apply_params_file_pre_parse


def _extract_first_id(item, candidates):
    if not isinstance(item, dict):
        return None
    for key in candidates:
        value = item.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def _safe_attach_share_link(client, item):
    if not isinstance(item, dict):
        return
    # 待办通常关联汇报；若存在任务字段则按任务补链
    report_id = _extract_first_id(item, ("reportId",))
    task_id = _extract_first_id(item, ("planId", "taskId"))
    try:
        if report_id is not None:
            item["shareLink"] = client.create_share_link(report_id, 1)
            return
        if task_id is not None:
            item["shareLink"] = client.create_share_link(task_id, 2)
            return
    except Exception:
        # 分享链接失败不阻断主查询结果
        return


def _attach_share_links_to_list(client, rows, top_n: int):
    if not isinstance(rows, list):
        return
    limit = len(rows) if top_n <= 0 else top_n
    for idx, row in enumerate(rows):
        if idx >= limit:
            break
        _safe_attach_share_link(client, row)


def list_todos(args):
    """查询待办列表"""
    client = make_client()
    
    result = client.get_todo_list(
        page_index=args.page_index,
        page_size=args.page_size,
        status=args.status
    )

    rows = result.get("list") or result.get("rows") or []
    if args.with_share_link:
        _attach_share_links_to_list(client, rows, args.share_top_n)
    
    if args.output_raw:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 5.15 返回 PageInfo：列表在 ``list``（见开放 API 6.3），非 ``rows``
    total = result.get("total", len(rows))

    output = {
        "success": True,
        "action": "list",
        "total": total,
        "items": [
            {
                "todoId": item.get("todoId"),
                "reportId": item.get("reportId"),
                "id": item.get("todoId"),
                "title": item.get("main") or item.get("title"),
                "todoType": item.get("todoType") or item.get("type"),
                "status": item.get("status"),
                "createTime": item.get("createTime"),
                "creator": item.get("writeEmpName") or item.get("creatorName"),
                "shareLink": item.get("shareLink"),
            }
            for item in rows
        ],
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


def complete_todo(args):
    """完成待办"""
    client = make_client()
    
    if not args.todo_id:
        print(json.dumps({
            "success": False,
            "error": "缺少必填参数: --todo-id"
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    
    if not args.content:
        print(json.dumps({
            "success": False,
            "error": "缺少必填参数: --content"
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    
    if args.dry_run:
        print(json.dumps({
            "success": True,
            "action": "complete",
            "dryRun": True,
            "todoId": args.todo_id,
            "content": args.content
        }, ensure_ascii=False, indent=2))
        return
    
    result = client.complete_todo(
        todo_id=args.todo_id,
        content=args.content,
        operate=args.operate
    )
    
    output = {
        "success": True,
        "action": "complete",
        "todoId": args.todo_id,
        "result": result
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="CWork 待办管理",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--params-file", dest="params_file", default=None,
                        help="UTF-8 JSON 文件路径，从文件读取参数")

    subparsers = parser.add_subparsers(dest="action", help="操作类型")
    
    # list 子命令
    list_parser = subparsers.add_parser("list", help="查询待办列表")
    list_parser.add_argument("--page-index", type=int, default=1, help="页码")
    list_parser.add_argument("--page-size", type=int, default=20, help="每页数量")
    list_parser.add_argument("--status", type=str, help="状态筛选")
    list_parser.add_argument("--with-share-link", dest="with_share_link", action="store_true", default=True,
                             help="在待办列表中补充分享链接（默认开启）")
    list_parser.add_argument("--no-share-link", dest="with_share_link", action="store_false",
                             help="关闭分享链接补充")
    list_parser.add_argument("--share-top-n", type=int, default=20,
                             help="最多补充前 N 条分享链接（默认 20，0=当前页全部）")
    list_parser.add_argument("--output-raw", action="store_true", help="输出原始响应")
    
    # complete 子命令
    complete_parser = subparsers.add_parser("complete", help="完成待办")
    complete_parser.add_argument("--todo-id", type=str, required=True, help="待办 ID")
    complete_parser.add_argument("--content", type=str, required=True, help="完成说明")
    complete_parser.add_argument("--operate", type=str, default=None,
                                     choices=["agree", "disagree"],
                                     help="决策操作: agree=同意, disagree=不同意（仅决策类待办需要）")
    complete_parser.add_argument("--dry-run", action="store_true", help="仅预览")
    
    apply_params_file_pre_parse()
    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)
    
    if args.action == "list":
        list_todos(args)
    elif args.action == "complete":
        complete_todo(args)


if __name__ == "__main__":
    main()
