#!/usr/bin/env python3
import os
import sys
import argparse
import json
import re
from datetime import datetime

# 复用 slugify 逻辑
def slugify(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text).strip('-')
    return text if text else "untitled"

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

def _parse_simple_yaml(filepath):
    """简单 YAML 解析，用于读取配置"""
    if not os.path.exists(filepath):
        return {}
    config = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line and not line.strip().startswith('#'):
                    key, val = line.split(':', 1)
                    # 剥离行内注释
                    val = val.split('#', 1)[0].strip()
                    config[key.strip()] = val.strip('"').strip("'")
    except:
        pass
    return config

def main():
    parser = argparse.ArgumentParser(description='ARC Reactor Context Injector')
    parser.add_argument('--query', required=True, help='User input query to match against knowledge base')
    parser.add_argument('--root', default='arc-reactor-doc', help='Document root name')
    args = parser.parse_args()

    cwd = os.getcwd()
    doc_root = find_doc_root(cwd, args.root)
    wiki_dir = os.path.join(doc_root, 'wiki')
    index_path = os.path.join(wiki_dir, 'index.md')
    entities_dir = os.path.join(wiki_dir, 'entities')

    # 1. 加载配置限额
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'arc-reactor-config.yaml')
    config = _parse_simple_yaml(config_path)
    max_entities = int(config.get('max_entities', 3))
    max_chars = int(config.get('max_chars', 10000))

    if not os.path.exists(index_path):
        # 如果索引不存在，静默退出
        sys.exit(0)

    # 2. 从 index.md 提取所有实体
    entities_in_index = []
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 匹配 [[Entity Name]]
            wiki_links = re.findall(r'\[\[([^\]]+)\]\]', content)
            for link in wiki_links:
                entities_in_index.append({
                    "original": link,
                    "slug": slugify(link)
                })
    except Exception as e:
        print(f"Error reading index: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. 匹配检索词 (简单关键词碰撞)
    query_lower = args.query.lower()
    hit_entities = []
    seen_slugs = set()

    for item in entities_in_index:
        if item['slug'] in seen_slugs:
            continue
        # 匹配逻辑：如果实体名在 query 中，或者 query 的词在实体名中
        if item['original'].lower() in query_lower or item['slug'].replace('-', ' ') in query_lower:
            hit_entities.append(item)
            seen_slugs.add(item['slug'])
        
        if len(hit_entities) >= max_entities:
            break

    # 4. 提取实体内容并格式化输出
    if not hit_entities:
        sys.exit(0)

    output_blocks = []
    total_chars = 0

    for entity in hit_entities:
        entity_path = os.path.join(entities_dir, f"{entity['slug']}.md")
        if os.path.exists(entity_path):
            try:
                with open(entity_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    block = f"### Entity: {entity['original']}\nURL: wiki/entities/{entity['slug']}.md\n\n{content}"
                    if total_chars + len(block) > max_chars:
                        break
                    output_blocks.append(block)
                    total_chars += len(block)
            except:
                continue

    if output_blocks:
        print("\n<ARC_KNOWLEDGE_CONTEXT>")
        print("以下是从您的私人百科全书（ARC Wiki）中自动检索到的关联知识条目，请结合这些背景信息回答用户：")
        print("\n---\n".join(output_blocks))
        print("</ARC_KNOWLEDGE_CONTEXT>\n")

if __name__ == "__main__":
    main()
