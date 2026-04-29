#!/usr/bin/env python3
import os
import sys
import argparse
import json
import re
from datetime import datetime, timedelta

def find_doc_root(start_path, root_name='arc-reactor-doc'):
    """向上查找工作区根目录"""
    curr_dir = os.path.abspath(start_path)
    while curr_dir and curr_dir != '/':
        if os.path.exists(os.path.join(curr_dir, root_name)):
            return os.path.join(curr_dir, root_name)
        if os.path.exists(os.path.join(curr_dir, '.git')):
            return os.path.join(curr_dir, root_name)
        parent = os.path.dirname(curr_dir)
        if parent == curr_dir:
            break
        curr_dir = parent
    return os.path.join(start_path, root_name)

def _parse_frontmatter(content):
    """提取 Markdown 的 YAML Frontmatter"""
    meta = {}
    if content.strip().startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            header = parts[1]
            for line in header.splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    meta[k.strip().lower()] = v.strip().strip('"').strip("'")
    return meta

def main():
    parser = argparse.ArgumentParser(description='ARC Reactor Weekly Reporter')
    parser.add_argument('--days', type=int, default=7, help='聚合过去几天的内容')
    parser.add_argument('--root', default='arc-reactor-doc', help='文档根目录名称')
    args = parser.parse_args()

    cwd = os.getcwd()
    doc_root = find_doc_root(cwd, args.root)
    sources_dir = os.path.join(doc_root, 'wiki', 'sources')

    if not os.path.exists(sources_dir):
        print(json.dumps({"status": "error", "message": f"Sources directory not found: {sources_dir}"}))
        sys.exit(1)

    # 1. 计算时间窗口
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    target_dates = []
    for i in range(args.days + 1):
        target_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))

    # 2. 搜集符合时间窗的文件
    aggregated_items = []
    for date_str in target_dates:
        date_path = os.path.join(sources_dir, date_str)
        if os.path.exists(date_path):
            for filename in os.listdir(date_path):
                if filename.endswith('.md'):
                    fpath = os.path.join(date_path, filename)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            meta = _parse_frontmatter(content)
                            # 提取首段摘要 (跳过 Frontmatter)
                            body = content.split('---', 2)[-1].strip() if '---' in content else content
                            summary = body.split('\n\n')[0][:300].strip()
                            
                            aggregated_items.append({
                                "title": meta.get('title', filename),
                                "date": date_str,
                                "tags": meta.get('tags', []),
                                "summary": summary,
                                "path": os.path.relpath(fpath, doc_root)
                            })
                    except:
                        continue

    # 3. 输出汇总
    if not aggregated_items:
        print(f"### ARC Reactor 周报 ({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})\n\n> 本周暂无新增归档内容，休息一下吧！☕️")
        sys.exit(0)

    # 格式化输出 (供 LLM 进一步处理或直接展示)
    print(f"# ARC Reactor 知识周报\n区间：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}\n")
    print(f"## 📚 本周收录概览 (共 {len(aggregated_items)} 篇)\n")
    
    for item in aggregated_items:
        print(f"- **{item['title']}** ({item['date']})")
        print(f"  > {item['summary']}...")
        print(f"  [查阅原文]({item['path']})\n")

    print("\n---\n## 🧠 自动生成的洞察提炼 (Prompt 建议)\n")
    print("Orchestrator, 请根据以上聚合内容，回答：")
    print("1. 本周大家主要在研究什么？有没有形成明显的知识集群？")
    print("2. 哪些词条在不同文章里被反复提及？推荐我下一步该去深入了解哪个实体？")
    
    # 返回 JSON 回执以便 Orchestrator 审计
    receipt = {
        "status": "success",
        "action": "weekly_report",
        "days_scanned": args.days,
        "items_found": len(aggregated_items),
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d')
    }
    # 在 stderr 打印 JSON 回执，避免干扰正文
    print(json.dumps(receipt, ensure_ascii=False), file=sys.stderr)

if __name__ == "__main__":
    main()
