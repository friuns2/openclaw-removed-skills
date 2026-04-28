#!/usr/bin/env python3
import os
import sys
import argparse
import json
import hashlib
import shutil
import time
from datetime import datetime
import re


FACT_INDEX_FILENAME = 'index-facts.json'
FACT_SECTION_RE = re.compile(r'^###\s+(IN|OUT)-\d+:\s*(.+?)\s*$')
FACT_FIELD_RE = re.compile(r'^-\s+\*\*(.+?)\*\*:\s*(.*)$')
DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')
AMOUNT_RE = re.compile(r'(\d+(?:\.\d+)?\s*(?:万|元))')
PROJECT_RE = re.compile(r'([A-Za-z0-9\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff\-_/（）()· ]{0,80}?(?:系统|项目|产品|平台|Framework|Skill))')


def _fact_type_from_label(label, title='', summary=''):
    """将 CWork 类型字段映射为标准 fact 类型。"""
    normalized = (label or '').strip()
    context = ' '.join([normalized, title or '', summary or ''])
    lowered = context.lower()

    if normalized == '合同管理(OPS)':
        return 'contract'
    if normalized == '会议室预约':
        return 'meeting'
    if normalized == '销售项目':
        return 'project-progress'
    if '日报' in context:
        return 'daily-report'
    if '测试' in context or 'test' in lowered:
        return 'skill-test'
    if normalized == '其他汇报':
        return 'other'
    return 'other'


def _extract_fact_status(text):
    """基于标题与摘要做轻量状态推断。"""
    normalized = (text or '').strip()
    if not normalized:
        return 'unknown'

    if re.search(r'全部通过|通过率\s*100%|已完成|全部修复|现已全部修复|成功跑通|(?<![未不])完成(?!度)', normalized):
        return 'completed'
    if re.search(r'申请|放行|审批', normalized):
        return 'requested'
    if re.search(r'进展|进行中|跟进|处理中|待办|追踪', normalized):
        return 'in-progress'
    if re.search(r'会议|沟通会|预约', normalized):
        return 'scheduled'
    return 'unknown'


def _split_fact_sentences(text):
    """将摘要切分为句子列表。"""
    cleaned = re.sub(r'\s+', ' ', (text or '').strip())
    if not cleaned:
        return []

    parts = re.split(r'(?<=[。！？!?；;])\s*', cleaned)
    sentences = [part.strip() for part in parts if part.strip()]
    if sentences:
        return sentences
    return [cleaned]


def _extract_amount(text):
    """提取首个金额信息。"""
    match = AMOUNT_RE.search(text or '')
    if not match:
        return None
    return match.group(1).replace(' ', '')


def _extract_project(title, summary, entities):
    """尽量提取项目名/系统名。"""
    candidates = []
    if title:
        candidates.append(title)
    if summary:
        candidates.append(summary)
    candidates.extend(entities or [])

    for candidate in candidates:
        if not candidate:
            continue
        direct = candidate.strip()
        if re.search(r'(系统|项目|产品|平台|Framework|Skill)$', direct):
            return direct
        match = PROJECT_RE.search(direct)
        if match:
            return match.group(1).strip()
    return None


def _normalize_fact_value(value):
    """标准化过滤比较值。"""
    if value is None:
        return None
    return str(value).strip().lower()


def _load_fact_index(index_path):
    """读取事实索引文件，异常时回退为空列表并记录警告。"""
    if not os.path.exists(index_path):
        return []

    try:
        with open(index_path, 'r', encoding='utf-8') as file_obj:
            data = json.load(file_obj)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError as exc:
        print(json.dumps({"status": "warning", "message": f"Fact index JSON corrupted at {index_path}: {exc}"}), file=sys.stderr)
    except Exception as exc:
        print(json.dumps({"status": "warning", "message": f"Unexpected error loading fact index {index_path}: {exc}"}), file=sys.stderr)
    return []


def _write_fact_index(index_path, entries):
    """写回事实索引文件。"""
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, 'w', encoding='utf-8') as file_obj:
        json.dump(entries, file_obj, ensure_ascii=False, indent=2)


def parse_fact_index_entries(markdown_text):
    """解析 Markdown 快照中的事实条目。"""
    sections = []
    current = None

    for raw_line in (markdown_text or '').splitlines():
        line = raw_line.rstrip()
        section_match = FACT_SECTION_RE.match(line)
        if section_match:
            if current is not None:
                sections.append(current)
            current = {
                'section': section_match.group(1),
                'title': section_match.group(2).strip(),
                'lines': []
            }
            continue
        if current is not None:
            current['lines'].append(line)

    if current is not None:
        sections.append(current)

    entries = []
    for section in sections:
        fields = {}
        for line in section['lines']:
            field_match = FACT_FIELD_RE.match(line.strip())
            if not field_match:
                continue
            fields[field_match.group(1).strip()] = field_match.group(2).strip()

        title = section['title']
        author = fields.get('作者', '')
        time_text = fields.get('时间', '')
        type_label = fields.get('类型', '')
        summary = fields.get('摘要', '')
        entities_text = fields.get('关键实体', '')
        date_match = DATE_RE.search(time_text)
        date_value = date_match.group(1) if date_match else None
        entities = [item.strip() for item in re.split(r'[，,、；;]', entities_text) if item.strip()]
        context_text = '\n'.join([title, summary, type_label, entities_text])
        stable_id_seed = f"{title}|{date_value or ''}|{author}"

        entries.append({
            'id': hashlib.sha256(stable_id_seed.encode('utf-8')).hexdigest()[:24],
            'type': _fact_type_from_label(type_label, title=title, summary=summary),
            'title': title,
            'author': author,
            'date': date_value,
            'status': _extract_fact_status(context_text),
            'entities': entities,
            'key_facts': _split_fact_sentences(summary),
            'amount': _extract_amount(' '.join([title, summary])),
            'project': _extract_project(title, summary, entities),
            'source_file': None,
        })

    return entries


def ingest_fact_index(doc_root, markdown_text):
    """将 Markdown 快照增量写入事实索引。"""
    index_path = os.path.join(doc_root, 'wiki', FACT_INDEX_FILENAME)
    existing_entries = _load_fact_index(index_path)
    parsed_entries = parse_fact_index_entries(markdown_text)
    existing_keys = {
        (_normalize_fact_value(item.get('title')), _normalize_fact_value(item.get('date')))
        for item in existing_entries if isinstance(item, dict)
    }

    added_entries = []
    for entry in parsed_entries:
        dedup_key = (_normalize_fact_value(entry.get('title')), _normalize_fact_value(entry.get('date')))
        if dedup_key in existing_keys:
            continue
        existing_keys.add(dedup_key)
        added_entries.append(entry)

    final_entries = existing_entries + added_entries
    _write_fact_index(index_path, final_entries)

    return {
        'status': 'success',
        'action': 'fact_index',
        'path': index_path,
        'entries_parsed': len(parsed_entries),
        'entries_added': len(added_entries),
        'total_entries': len(final_entries),
        'message': 'Fact index updated.'
    }


def query_facts(root_name, filters=None):
    """按条件查询事实索引。"""
    cwd = os.getcwd()
    doc_root = find_doc_root(cwd, root_name)
    index_path = os.path.join(doc_root, 'wiki', FACT_INDEX_FILENAME)
    entries = [item for item in _load_fact_index(index_path) if isinstance(item, dict)]
    parsed_filters = []

    for raw_filter in filters or []:
        if '=' not in raw_filter:
            continue
        field, value = raw_filter.split('=', 1)
        field = field.strip()
        value = value.strip()
        if not field or value == '':
            continue
        parsed_filters.append((field, value))

    def matches(entry):
        for field, expected in parsed_filters:
            expected_normalized = _normalize_fact_value(expected)

            if field == 'text':
                haystacks = [
                    entry.get('title', ''),
                    ' '.join(entry.get('key_facts', []) or []),
                    ' '.join(entry.get('entities', []) or []),
                ]
                searchable = _normalize_fact_value(' '.join(haystacks)) or ''
                if expected_normalized not in searchable:
                    return False
                continue

            actual = entry.get(field)
            if isinstance(actual, list):
                normalized_list = [_normalize_fact_value(item) for item in actual]
                if expected_normalized not in normalized_list:
                    return False
                continue

            if _normalize_fact_value(actual) != expected_normalized:
                return False

        return True

    return [entry for entry in entries if matches(entry)]


def _split_inline_list(text):
    """拆分 YAML 内联列表，支持简单引号场景。"""
    items = []
    current = []
    quote_char = None

    for char in text:
        if char in ('"', "'"):
            if quote_char == char:
                quote_char = None
            elif quote_char is None:
                quote_char = char
        if char == ',' and quote_char is None:
            item = ''.join(current).strip()
            if item:
                items.append(item)
            current = []
            continue
        current.append(char)

    tail = ''.join(current).strip()
    if tail:
        items.append(tail)
    return items


def _parse_yaml_scalar(value):
    """解析简单 YAML 标量/内联列表。"""
    value = value.strip()
    if value == '':
        return ''
    if value.startswith('[') and value.endswith(']'):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_yaml_scalar(item) for item in _split_inline_list(inner)]
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lowered = value.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False
    if lowered in ('null', 'none'):
        return None
    if re.fullmatch(r'-?\d+', value):
        return int(value)
    if re.fullmatch(r'-?\d+\.\d+', value):
        return float(value)
    return value


def _parse_simple_yaml(filepath):
    """使用标准库解析简单 YAML：顶层键值、嵌套字典、列表字典。"""
    with open(filepath, 'r', encoding='utf-8') as file_obj:
        raw_lines = file_obj.readlines()

    processed = []
    for raw_line in raw_lines:
        if not raw_line.strip() or raw_line.lstrip().startswith('#'):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(' '))
        processed.append({
            'indent': indent,
            'text': raw_line.strip()
        })

    def parse_mapping(index, indent):
        data = {}
        while index < len(processed):
            line = processed[index]
            if line['indent'] < indent:
                break
            if line['indent'] > indent:
                index += 1
                continue
            if line['text'].startswith('- '):
                break

            key, sep, remainder = line['text'].partition(':')
            if not sep:
                index += 1
                continue

            key = key.strip()
            remainder = remainder.strip()
            if remainder:
                data[key] = _parse_yaml_scalar(remainder)
                index += 1
                continue

            next_index = index + 1
            if next_index < len(processed) and processed[next_index]['indent'] > indent:
                child_indent = processed[next_index]['indent']
                if processed[next_index]['text'].startswith('- '):
                    data[key], index = parse_list(next_index, child_indent)
                else:
                    data[key], index = parse_mapping(next_index, child_indent)
            else:
                data[key] = {}
                index += 1
        return data, index

    def parse_list(index, indent):
        items = []
        while index < len(processed):
            line = processed[index]
            if line['indent'] < indent:
                break
            if line['indent'] > indent:
                index += 1
                continue
            if not line['text'].startswith('- '):
                break

            body = line['text'][2:].strip()
            if ':' in body:
                key, _, remainder = body.partition(':')
                item = {key.strip(): _parse_yaml_scalar(remainder.strip()) if remainder.strip() else {}}
                index += 1
                if index < len(processed) and processed[index]['indent'] > indent:
                    child_block, index = parse_mapping(index, processed[index]['indent'])
                    item.update(child_block)
                items.append(item)
                continue

            if body:
                items.append(_parse_yaml_scalar(body))
                index += 1
                continue

            index += 1
            if index < len(processed) and processed[index]['indent'] > indent:
                child_indent = processed[index]['indent']
                if processed[index]['text'].startswith('- '):
                    item, index = parse_list(index, child_indent)
                else:
                    item, index = parse_mapping(index, child_indent)
                items.append(item)
        return items, index

    parsed, _ = parse_mapping(0, 0)
    return parsed


def _find_config_path(start_path=None):
    """向上查找配置文件路径。"""
    search_dir = os.path.abspath(start_path or os.getcwd())
    if os.path.isfile(search_dir):
        search_dir = os.path.dirname(search_dir)

    while True:
        direct_path = os.path.join(search_dir, 'arc-reactor-config.yaml')
        nested_path = os.path.join(search_dir, 'skills', 'arc-reactor', 'arc-reactor-config.yaml')
        if os.path.exists(direct_path):
            return direct_path
        if os.path.exists(nested_path):
            return nested_path

        parent_dir = os.path.dirname(search_dir)
        if parent_dir == search_dir:
            return None
        search_dir = parent_dir


def load_config(start_path=None):
    """查找并解析 `arc-reactor-config.yaml`。"""
    config_path = _find_config_path(start_path)
    if not config_path:
        return {}
    return _parse_simple_yaml(config_path)


def resolve_kb_root(content_source, tags=None):
    """根据来源或标签自动匹配知识库根目录。"""
    config = load_config()
    knowledge_bases = config.get('knowledge_bases', []) or []
    normalized_tags = {str(tag) for tag in (tags or [])}

    for kb_entry in knowledge_bases:
        auto_route = kb_entry.get('auto_route', {}) or {}
        sources = auto_route.get('sources', []) or []
        if content_source in sources:
            return kb_entry.get('root')

    for kb_entry in knowledge_bases:
        auto_route = kb_entry.get('auto_route', {}) or {}
        route_tags = {str(tag) for tag in (auto_route.get('tags', []) or [])}
        if normalized_tags & route_tags:
            return kb_entry.get('root')

    return None


def _format_kb_yaml_entry(kb_entry):
    """格式化 knowledge_bases 条目为 YAML 文本。"""
    name = kb_entry['name']
    root = kb_entry['root']
    description = kb_entry.get('description', '')
    auto_route = kb_entry.get('auto_route', {}) or {}
    sources = auto_route.get('sources', []) or []
    tags = auto_route.get('tags', []) or []
    sources_str = ', '.join(json.dumps(item, ensure_ascii=False) for item in sources)
    tags_str = ', '.join(json.dumps(item, ensure_ascii=False) for item in tags)

    return (
        f"  - name: {name}\n"
        f"    root: {root}\n"
        f"    description: {json.dumps(description, ensure_ascii=False)}\n"
        f"    auto_route:\n"
        f"      sources: [{sources_str}]\n"
        f"      tags: [{tags_str}]\n"
    )


def kb_init(root_name, name=None, description=None):
    """初始化一个新的多实例知识库并写回配置。"""
    config_path = _find_config_path()
    if not config_path:
        return {"status": "error", "message": "arc-reactor-config.yaml 未找到"}

    config = load_config()
    knowledge_bases = config.get('knowledge_bases', []) or []
    kb_name = name or root_name
    kb_description = description or ''

    for kb_entry in knowledge_bases:
        if kb_entry.get('name') == kb_name:
            return {"status": "error", "message": f"知识库名称已存在: {kb_name}"}
        if kb_entry.get('root') == root_name:
            return {"status": "error", "message": f"知识库根目录已存在: {root_name}"}

    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(config_path)))
    kb_root = os.path.join(workspace_root, root_name)
    dirs_to_create = [
        os.path.join(kb_root, 'wiki', 'sources'),
        os.path.join(kb_root, 'wiki', 'entities'),
        os.path.join(kb_root, 'wiki', 'concepts'),
        os.path.join(kb_root, 'raw'),
    ]
    files_to_create = [
        os.path.join(kb_root, 'wiki', 'index.md'),
        os.path.join(kb_root, 'wiki', 'log.md'),
        os.path.join(kb_root, 'wiki', FACT_INDEX_FILENAME),
    ]

    created = []
    try:
        for dir_path in dirs_to_create:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                created.append(dir_path)
        for file_path in files_to_create:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as file_obj:
                    if file_path.endswith(FACT_INDEX_FILENAME):
                        file_obj.write('[]')
                    else:
                        file_obj.write('')
                created.append(file_path)

        new_entry = {
            'name': kb_name,
            'root': root_name,
            'description': kb_description,
            'auto_route': {
                'sources': [],
                'tags': [],
            },
        }

        with open(config_path, 'r', encoding='utf-8') as file_obj:
            config_text = file_obj.read().rstrip()

        yaml_entry = _format_kb_yaml_entry(new_entry)
        if 'knowledge_bases:' in config_text:
            updated_text = f"{config_text}\n\n{yaml_entry.rstrip()}\n"
        else:
            updated_text = f"{config_text}\n\nknowledge_bases:\n{yaml_entry}"

        with open(config_path, 'w', encoding='utf-8') as file_obj:
            file_obj.write(updated_text)

        return {
            "status": "success",
            "action": "kb_init",
            "name": kb_name,
            "root": root_name,
            "path": kb_root,
            "config": config_path,
            "created": created,
            "message": "Knowledge base initialized."
        }
    except Exception as exc:
        return {"status": "error", "message": f"知识库初始化失败: {str(exc)}"}


def kb_list():
    """列出所有已配置知识库的统计信息。"""
    config = load_config()
    knowledge_bases = config.get('knowledge_bases', []) or []
    config_path = _find_config_path()
    if not config_path:
        return []

    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(config_path)))
    results = []

    for kb_entry in knowledge_bases:
        kb_root = os.path.join(workspace_root, kb_entry.get('root', ''))
        sources_dir = os.path.join(kb_root, 'wiki', 'sources')
        entities_dir = os.path.join(kb_root, 'wiki', 'entities')
        concepts_dir = os.path.join(kb_root, 'wiki', 'concepts')

        def count_markdown_files(root_dir):
            count = 0
            if not os.path.exists(root_dir):
                return count
            for _, _, files in os.walk(root_dir):
                count += sum(1 for filename in files if filename.endswith('.md'))
            return count

        latest_mtime = None
        if os.path.exists(kb_root):
            for root, _, files in os.walk(kb_root):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    file_mtime = os.path.getmtime(file_path)
                    if latest_mtime is None or file_mtime > latest_mtime:
                        latest_mtime = file_mtime

        results.append({
            'name': kb_entry.get('name'),
            'root': kb_entry.get('root'),
            'description': kb_entry.get('description', ''),
            'sources_count': count_markdown_files(sources_dir),
            'entities_count': count_markdown_files(entities_dir),
            'concepts_count': count_markdown_files(concepts_dir),
            'last_modified': datetime.fromtimestamp(latest_mtime).strftime('%Y-%m-%d %H:%M:%S') if latest_mtime else None,
            'exists': os.path.exists(kb_root),
        })

    return results

def slugify(text):
    """简单规范化文件名"""
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text).strip('-')
    return text if text else "untitled"

WIKI_LINK_RE = re.compile(r'\[\[([^\]]+)\]\]')
FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def resolve_entity_path(doc_root, topic):
    """在 entities 或 concepts 目录中寻找实体的物理路径。"""
    slug = slugify(topic)
    paths = [
        os.path.join(doc_root, 'wiki', 'entities', f"{slug}.md"),
        os.path.join(doc_root, 'wiki', 'concepts', f"{slug}.md")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def _count_link_mentions_in_sources(sources_dir, link_text):
    """统计 wiki/sources/ 目录中提及指定 link 文本的 .md 文件数量。

    使用 grep -rl 扫描，返回命中文件数（非行数），用于判断该 link 是否值得保留。
    """
    import subprocess
    if not os.path.exists(sources_dir):
        return 0
    pattern = re.escape(link_text)
    try:
        cmd = ["grep", "-rl", "--include=*.md", pattern, sources_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return len([l for l in result.stdout.splitlines() if l.strip()])
    except Exception:
        pass
    return 0


def sanitize_wiki_links(content, doc_root, existing_content=None):
    """扫描并清理孤儿 wiki-link，防止产生大量指向不存在页面的 [[link]]。

    处理逻辑：
    1. 提取所有 [[wiki-link]]
    2. 检查 wiki/entities/{slug}.md 和 wiki/concepts/{slug}.md 是否存在
    3. 若目标不存在，统计 wiki/sources/ 中被提及的文件数：
       - >= 3 次：保留 [[link]]（值得建页）
       - 2 次：降级为 **link**（加粗）
       - 1 或 0 次：降级为纯文本（去掉 [[]]）
    4. 如果传入了 existing_content，只对新增部分做清理，不动已有内容。
    """
    # 若为追加模式（append），分离已有内容与新增内容，只清理新增部分
    if existing_content:
        # 用最长公共前缀定位新增内容的起点
        common_len = 0
        min_len = min(len(existing_content), len(content))
        for i in range(min_len):
            if existing_content[i] == content[i]:
                common_len += 1
            else:
                break
        prefix = content[:common_len]
        suffix = content[common_len:]
        # 只对新增后缀做 sanitization
        sanitized_suffix = sanitize_wiki_links(suffix, doc_root, existing_content=None)
        return prefix + sanitized_suffix

    sources_dir = os.path.join(doc_root, 'wiki', 'sources')

    def _replacer(match):
        link_text = match.group(1)
        slug = slugify(link_text)
        # 检查目标实体/概念文件是否存在
        entity_path = os.path.join(doc_root, 'wiki', 'entities', f"{slug}.md")
        concept_path = os.path.join(doc_root, 'wiki', 'concepts', f"{slug}.md")
        if os.path.exists(entity_path) or os.path.exists(concept_path):
            # 目标页面已存在，保留 wiki-link
            return match.group(0)

        # 目标不存在，统计在 sources 中的提及次数
        mention_count = _count_link_mentions_in_sources(sources_dir, link_text)

        if mention_count >= 3:
            # 高频提及，保留 wiki-link（未来值得建页）
            return match.group(0)
        elif mention_count == 2:
            # 中频提及，降级为加粗
            return f"**{link_text}**"
        else:
            # 低频提及（1 或 0），降级为纯文本
            return link_text

    return WIKI_LINK_RE.sub(_replacer, content)


def find_backlinks(doc_root, topic):
    """使用 grep 扫描 wiki/sources 目录，寻找引用了该实体的源文件。"""
    sources_dir = os.path.join(doc_root, 'wiki', 'sources')
    if not os.path.exists(sources_dir):
        return []

    import subprocess
    # 搜索格式为 [[Topic]] 或 [[topic]]
    pattern = f"\\[\\[{topic}\\]\\]"
    # 使用 grep -rl 获取包含该字符串的文件名列表
    try:
        cmd = ["grep", "-rl", "--include=*.md", pattern, sources_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        pass
    return []


def export_entity(doc_root, topic, output_dir=None):
    """导出实体及其关联上下文为单一 Markdown 文档。"""
    entity_path = resolve_entity_path(doc_root, topic)
    if not entity_path:
        return {"status": "error", "message": f"未找到实体: {topic}"}

    wiki_dir = os.path.join(doc_root, 'wiki')
    if not output_dir:
        output_dir = os.path.join(doc_root, 'exports')
    os.makedirs(output_dir, exist_ok=True)

    # 1. 读取实体内容
    with open(entity_path, 'r', encoding='utf-8') as f:
        entity_content = f.read()

    # 2. 发现关联素材 (Sources)
    # A. 从 Frontmatter 读取
    linked_sources = []
    fm_match = FRONTMATTER_RE.match(entity_content)
    if fm_match:
        fm_text = fm_match.group(1)
        # 简单解析 YAML 列表
        sources_match = re.search(r'sources:\s*\[(.*?)\]', fm_text)
        if sources_match:
            raw_sources = sources_match.group(1)
            # 这里的路径通常是相对路径或 Slug
            linked_sources = [s.strip().strip('"').strip("'") for s in raw_sources.split(',')]

    # B. 发现反向链接
    backlinks = find_backlinks(doc_root, topic)

    # 3. 发现关联实体 (Related Entities)
    related_entities = WIKI_LINK_RE.findall(entity_content)
    unique_related = list(set(slugify(e) for e in related_entities if slugify(e) != slugify(topic)))

    # 4. 构建导出文档
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = [
        f"# {topic} — Knowledge Export",
        f"**Generated**: {now_str} | **Source**: ARC Reactor Wiki",
        "\n---",
        "\n## 1. Overview (Entity Content)",
        entity_content,
        "\n---",
        "\n## 2. Connections (Related Entities)"
    ]

    if not unique_related:
        lines.append("\n*No direct wiki-entity connections found.*")
    else:
        for r_slug in unique_related:
            r_path = resolve_entity_path(doc_root, r_slug)
            if r_path:
                with open(r_path, 'r', encoding='utf-8') as f:
                    r_content = f.read()
                lines.append(f"\n### [[{r_slug}]]")
                lines.append(r_content)

    lines.append("\n---")
    lines.append("\n## 3. Origins (Source Materials)")

    all_source_paths = set()
    # 尝试解析 Frontmatter 里的 source 路径
    for s_ref in linked_sources:
        # 这里逻辑较简化，尝试在 wiki/sources 递归寻找对应文件
        for root, _, files in os.walk(os.path.join(wiki_dir, 'sources')):
            for filename in files:
                if s_ref in filename or slugify(s_ref) in filename:
                    all_source_paths.add(os.path.join(root, filename))

    # 添加反向链接命中的路径
    for b_path in backlinks:
        all_source_paths.add(b_path)

    if not all_source_paths:
        lines.append("\n*No original source materials found.*")
    else:
        for s_path in all_source_paths:
            rel_name = os.path.relpath(s_path, os.path.join(wiki_dir, 'sources'))
            with open(s_path, 'r', encoding='utf-8') as f:
                s_content = f.read()
            lines.append(f"\n### Source: {rel_name}")
            lines.append(s_content)

    # 5. 写入文件
    dest_path = os.path.join(output_dir, f"{slugify(topic)}-bundle.md")
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return {
        "status": "success",
        "action": "export_entity",
        "topic": topic,
        "path": dest_path,
        "connections_found": len(unique_related),
        "sources_found": len(all_source_paths)
    }

def find_doc_root(start_path, root_name='arc-reactor-doc'):
    """Walk up from start_path to find the workspace root."""
    curr_dir = start_path
    while curr_dir and curr_dir != '/':
        if os.path.exists(os.path.join(curr_dir, root_name)):
            return os.path.join(curr_dir, root_name)
        if os.path.exists(os.path.join(curr_dir, '.git')):
            return os.path.join(curr_dir, root_name)
        curr_dir = os.path.dirname(curr_dir)
    return os.path.join(start_path, root_name)

def lint_wiki(doc_root, fix=False):
    """Health check for Wiki integrity. Returns issues found."""
    issues = []
    fixed = []
    
    wiki_dir = os.path.join(doc_root, 'wiki')
    if not os.path.exists(wiki_dir):
        return {"status": "error", "message": f"Wiki directory not found: {wiki_dir}"}
    
    # 1. Scan all entity files
    entities_dir = os.path.join(wiki_dir, 'entities')
    existing_entities = set()
    if os.path.exists(entities_dir):
        for f in os.listdir(entities_dir):
            if f.endswith('.md'):
                existing_entities.add(f[:-3])  # strip .md
    
    # 2. Scan all source files for wiki-links
    all_links = set()
    sources_dir = os.path.join(wiki_dir, 'sources')
    all_files = []
    
    # Collect all markdown files
    for root, dirs, files in os.walk(wiki_dir):
        for f in files:
            if f.endswith('.md'):
                all_files.append(os.path.join(root, f))
    
    for fpath in all_files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find all [[wiki-links]]
                links = WIKI_LINK_RE.findall(content)
                for link in links:
                    slug = slugify(link)
                    all_links.add(slug)
                    
                    # Check for orphan links
                    if slug not in existing_entities:
                        rel_path = os.path.relpath(fpath, doc_root)
                        issues.append({
                            "type": "orphan_link",
                            "link": f"[[{link}]]",
                            "slug": slug,
                            "found_in": rel_path,
                            "fix": f"Create entity: wiki/entities/{slug}.md"
                        })
                        # Auto-fix: create stub entity
                        if fix and not os.path.exists(os.path.join(entities_dir, f"{slug}.md")):
                            stub = f"---\ndate: {datetime.now().strftime('%Y-%m-%d')}\n---\n\n# {link}\n\n> Stub entity — awaiting Ingest completion.\n"
                            stub_path = os.path.join(entities_dir, f"{slug}.md")
                            with open(stub_path, 'w', encoding='utf-8') as ef:
                                ef.write(stub)
                            fixed.append(f"Created stub: wiki/entities/{slug}.md")
        except Exception:
            continue
    
    # 3. Check entities not in index.md
    index_path = os.path.join(wiki_dir, 'index.md')
    indexed_entities = set()
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            index_content = f.read()
            indexed_links = WIKI_LINK_RE.findall(index_content)
            for link in indexed_links:
                indexed_entities.add(slugify(link))
    
    for entity in existing_entities:
        if entity not in indexed_entities:
            issues.append({
                "type": "missing_from_index",
                "entity": entity,
                "fix": f"Add [[{entity}]] to wiki/index.md"
            })
    
    # 4. Check source files missing date
    if os.path.exists(sources_dir):
        for root, dirs, files in os.walk(sources_dir):
            for f in files:
                if f.endswith('.md'):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as sf:
                            content = sf.read()
                            if 'date:' not in content[:500].lower():
                                rel_path = os.path.relpath(fpath, doc_root)
                                issues.append({
                                    "type": "missing_date",
                                    "file": rel_path,
                                    "fix": "Add date field to frontmatter"
                                })
                    except Exception:
                        continue
    
    # 5. Check for empty files (< 50 bytes)
    for fpath in all_files:
        try:
            if os.path.getsize(fpath) < 50:
                rel_path = os.path.relpath(fpath, doc_root)
                issues.append({
                    "type": "empty_file",
                    "file": rel_path,
                    "fix": "Populate or remove empty file"
                })
        except Exception:
            continue
    
    return {
        "status": "lint_complete",
        "total_files": len(all_files),
        "total_entities": len(existing_entities),
        "total_links": len(all_links),
        "issues_found": len(issues),
        "issues_fixed": len(fixed),
        "issues": issues,
        "fixed": fixed
    }


def validate_files(doc_root, paths=None):
    """验证文件是否存在且有效。

    Args:
        doc_root: 文档根目录路径
        paths: 要验证的文件路径列表（相对于 doc_root），如果为 None 则验证整个 Wiki

    Returns:
        包含验证结果的 JSON 可序列化字典
    """
    if not paths:
        # 验证整个 Wiki 结构
        wiki_dir = os.path.join(doc_root, 'wiki')
        if not os.path.exists(wiki_dir):
            return {"status": "error", "message": f"Wiki directory not found: {wiki_dir}"}

        files_valid = 0
        files_invalid = []
        files_empty = []

        # 遍历所有 Markdown 文件
        for root, dirs, files in os.walk(wiki_dir):
            for f in files:
                if f.endswith('.md'):
                    fpath = os.path.join(root, f)
                    try:
                        # 验证文件可读且非空
                        with open(fpath, 'r', encoding='utf-8') as file_obj:
                            content = file_obj.read()
                        if not content.strip():
                            files_empty.append(fpath)
                            files_invalid.append(fpath)
                        else:
                            files_valid += 1
                    except Exception as e:
                        files_invalid.append(fpath)

        return {
            "status": "ok" if not files_invalid else "partial",
            "action": "validate_wiki",
            "files_valid": files_valid,
            "files_invalid": len(files_invalid),
            "files_empty": len(files_empty),
            "invalid_files": files_invalid,
            "message": f"Validation complete: {files_valid} valid, {len(files_invalid)} invalid ({len(files_empty)} empty)"
        }
    else:
        # 验证特定文件
        results = []
        all_valid = True

        for path in paths:
            full_path = os.path.join(doc_root, path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as file_obj:
                        content = file_obj.read()
                    if content.strip():
                        results.append({
                            "path": path,
                            "status": "valid",
                            "size": len(content)
                        })
                    else:
                        results.append({
                            "path": path,
                            "status": "empty",
                            "size": 0
                        })
                        all_valid = False
                except Exception as e:
                    results.append({
                        "path": path,
                        "status": "error",
                        "error": str(e)
                    })
                    all_valid = False
            else:
                results.append({
                    "path": path,
                    "status": "not_found"
                })
                all_valid = False

        return {
            "status": "ok" if all_valid else "partial",
            "action": "validate_files",
            "results": results,
            "message": f"Validated {len(results)} files: {sum(1 for r in results if r['status'] == 'valid')} valid"
        }


def validate_obsidian_config(vault_path):
    """Validate Obsidian vault configuration."""
    vault = os.path.expanduser(vault_path)
    if not os.path.isdir(vault):
        return False, "Obsidian 库路径不存在"
    test_path = os.path.join(vault, '.arc-sync-test')
    try:
        with open(test_path, 'w') as f:
            f.write('ping')
        os.remove(test_path)
        return True, "OK"
    except Exception as e:
        return False, f"无写入权限: {str(e)}"


def sync_to_obsidian(source_path, vault_path, target_dir, max_retries=3, retry_delay=300):
    """Sync a source file to Obsidian vault with exponential backoff."""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    now_date = datetime.now().strftime('%Y-%m-%d')
    
    is_valid, msg = validate_obsidian_config(vault_path)
    if not is_valid:
        return {"status": "error", "action": "obsidian_sync", "source": source_path, "error": msg, "retry_count": 0, "message": f"Obsidian sync failed: {msg}"}
    
    if not os.path.exists(source_path):
        return {"status": "error", "action": "obsidian_sync", "source": source_path, "error": "源文件不存在", "retry_count": 0, "message": "Obsidian sync failed: source file not found"}
    
    resolved_target = target_dir.replace('{date}', now_date)
    dest_dir = os.path.join(os.path.expanduser(vault_path), resolved_target)
    filename = os.path.basename(source_path)
    dest_path = os.path.join(dest_dir, filename)
    
    last_error = None
    for attempt in range(max_retries):
        try:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            sync_marker = f"\n\n---\n同步状态: ✅ Obsidian (时间: {now_str})\n---\n"
            with open(dest_path, 'a', encoding='utf-8') as f:
                f.write(sync_marker)
            return {"status": "success", "action": "obsidian_sync", "source": source_path, "destination": dest_path, "obsidian_vault": vault_path, "sync_time": now_str, "retry_count": attempt, "message": "Obsidian sync complete."}
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
            continue
    
    return {"status": "error", "action": "obsidian_sync", "source": source_path, "error": last_error, "retry_count": max_retries, "message": f"Obsidian sync failed after {max_retries} retries: {last_error}"}


def main():
    parser = argparse.ArgumentParser(description='ARC Reactor V4 Archive Manager (Karpathy Wiki Edition)')
    parser.add_argument('--lint', action='store_true', help='Run Wiki health check')
    parser.add_argument('--fix', action='store_true', help='Auto-fix issues found during lint')
    parser.add_argument('--validate', action='store_true', help='Validate file integrity and existence')
    parser.add_argument('--kb-init', action='store_true', help='初始化新的知识库实例')
    parser.add_argument('--kb-list', action='store_true', help='列出所有已配置知识库')
    parser.add_argument('--query-facts', action='store_true', help='查询事实索引')
    parser.add_argument('--export-entity', help='导出实体及其关联上下文')
    parser.add_argument('--type', choices=[
        'raw', 'source', 'entity', 'concept', 'index', 'log', 'template', 'fact-index'
    ], required=False, help='归档进入的 Wiki 圈层类型')
    parser.add_argument('--sync-obsidian', action='store_true', help='Sync source file to Obsidian vault')
    parser.add_argument('--source', required=False, default=None, help='Source file path (used with --sync-obsidian)')
    parser.add_argument('--vault', required=False, default=None, help='Obsidian vault path (used with --sync-obsidian)')
    parser.add_argument('--target', required=False, default='github分享/AI调研/{date}/', help='Target subdirectory in vault')
    parser.add_argument('--async', dest='async_mode', action='store_true', help='Async mode: return immediately, sync in background')
    
    parser.add_argument('--topic', required=False, default='knowledge-node', help='话题/实体名 (用于生成文件名)')
    parser.add_argument('--stdin', action='store_true', help='强制通过标准输入读取内容 (防止转义错误)')
    parser.add_argument('--root', default='arc-reactor-doc', help='文档根目录名称')
    parser.add_argument('--filter', action='append', default=None, help='事实查询过滤条件，格式为 field=value，可重复传入')
    parser.add_argument('--name', required=False, default=None, help='KB 显示名称，仅用于 --kb-init')
    parser.add_argument('--description', required=False, default=None, help='KB 描述，仅用于 --kb-init')
    parser.add_argument('--date', required=False, default=None, help='指定的日期戳，缺省为今日')
    parser.add_argument('--dedup', choices=['merge', 'skip', 'overwrite'], default='overwrite',
                        help='去重策略: merge=增量合并, skip=跳过, overwrite=覆盖(默认)')
    parser.add_argument('--url', help='直接从 URL 抓取正文内容 (支持智能反爬)')
    parser.add_argument('--output-dir', help='导出目标目录')

    args = parser.parse_args()

    # Obsidian sync mode
    if args.sync_obsidian:
        auto_sync = os.environ.get('AUTO_SYNC', 'true')
        if auto_sync.lower() in ('false', '0', 'no'):
            print(json.dumps({"status": "skipped", "action": "obsidian_sync", "reason": "AUTO_SYNC=false", "message": "Obsidian sync disabled via AUTO_SYNC=false"}, ensure_ascii=False))
            sys.exit(0)
        if not args.source:
            print(json.dumps({"status": "error", "message": "--sync-obsidian requires --source"}))
            sys.exit(1)
        vault_path = args.vault or os.environ.get('OBSIDIAN_VAULT_PATH', '')
        if not vault_path:
            print(json.dumps({"status": "error", "message": "OBSIDIAN_VAULT_PATH not configured"}))
            sys.exit(1)
        if getattr(args, 'async_mode', False):
            import subprocess
            sync_cmd = [sys.executable, os.path.abspath(__file__), '--sync-obsidian', '--source', args.source, '--vault', vault_path, '--target', args.target]
            subprocess.Popen(sync_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            print(json.dumps({"status": "pending", "action": "obsidian_sync", "source": args.source, "message": "Obsidian sync started in background."}, ensure_ascii=False))
            sys.exit(0)
        else:
            result = sync_to_obsidian(args.source, vault_path, args.target)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(0 if result.get('status') == 'success' else 1)

    if args.query_facts:
        result = query_facts(args.root, filters=args.filter)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.kb_init:
        result = kb_init(args.root, name=args.name, description=args.description)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.export_entity:
        cwd = os.getcwd()
        doc_root = find_doc_root(cwd, args.root)
        result = export_entity(doc_root, args.export_entity, output_dir=args.output_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.kb_list:
        result = kb_list()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    # Lint mode — separate flow
    if args.lint:
        cwd = os.getcwd()
        doc_root = find_doc_root(cwd, args.root)
        result = lint_wiki(doc_root, fix=args.fix)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    # Validate mode — verify file integrity
    if args.validate:
        cwd = os.getcwd()
        doc_root = find_doc_root(cwd, args.root)
        result = validate_files(doc_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    # Normal archive mode — type is required
    if not args.type:
        print(json.dumps({"status": "error", "message": "归档模式需要 --type 参数，或使用 --lint / --kb-init / --kb-list"}))
        sys.exit(1)

    # 0. 预计算常用值
    topic_slug = slugify(args.topic)
    now_date = datetime.now().strftime('%Y-%m-%d')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 1. 获取内容 (来自 URL 或 STDIN)
    content_to_write = ""
    if args.url:
        try:
            # P5: Ensure scripts directory is in path for dynamic import
            script_dir = os.path.dirname(os.path.abspath(__file__))
            if script_dir not in sys.path:
                sys.path.append(script_dir)
            import smart_fetcher
            print(json.dumps({"status": "processing", "message": f"正在尝试从 URL 摄入: {args.url}"}, ensure_ascii=False))
            content_to_write = smart_fetcher.smart_extract(args.url)
            if not content_to_write:
                print(json.dumps({"status": "error", "message": "无法从该 URL 提取有效内容，抓取器返回为空"}))
                sys.exit(1)
        except ImportError:
            # 如果没法直接 import（比如在不同目录），尝试 subprocess 调用
            import subprocess
            script_path = os.path.join(os.path.dirname(__file__), 'smart_fetcher.py')
            result = subprocess.run([sys.executable, script_path, args.url], capture_output=True, text=True)
            if result.returncode == 0:
                # smart_fetcher.py 在 __main__ 下会打印内容，需要通过正则提取
                full_out = result.stdout
                match = re.search(r'--- EXTRACTED CONTENT START ---\n(.*?)\n--- EXTRACTED CONTENT END ---', full_out, re.DOTALL)
                if match:
                    content_to_write = match.group(1)
                else:
                    content_to_write = full_out # Fallback
            else:
                print(json.dumps({"status": "error", "message": "smart_fetcher 脚本执行失败", "details": result.stderr}))
                sys.exit(1)
    elif args.stdin:
        content_to_write = sys.stdin.read()
    else:
        print(json.dumps({"status": "error", "message": "安全限制: 必须提供 --url 或使用 --stdin 通过管道传参"}))
        sys.exit(1)

    if not content_to_write or not content_to_write.strip():
        print(json.dumps({"status": "error", "message": "抓取或读取的内容为空"}))
        sys.exit(1)

    # 2. 确定物理路径
    cwd = os.getcwd()
    doc_root = find_doc_root(cwd, args.root)

    if args.type == 'fact-index':
        result = ingest_fact_index(doc_root, content_to_write)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    target_dir = ""
    filename = ""
    # topic_slug already computed above
    
    # Wiki 层路由判定
    if args.type == 'raw':
        target_dir = os.path.join(doc_root, 'raw')
        filename = f"{topic_slug}.md"
    elif args.type == 'source':
        date_dir = args.date if args.date else now_date
        target_dir = os.path.join(doc_root, 'wiki', 'sources', date_dir)
        filename = f"{topic_slug}.md"
    elif args.type == 'entity':
        target_dir = os.path.join(doc_root, 'wiki', 'entities')
        filename = f"{topic_slug}.md"
    elif args.type == 'concept':
        target_dir = os.path.join(doc_root, 'wiki', 'concepts')
        filename = f"{topic_slug}.md"
    elif args.type == 'index':
        target_dir = os.path.join(doc_root, 'wiki')
        filename = "index.md"
    elif args.type == 'log':
        target_dir = os.path.join(doc_root, 'wiki')
        filename = "log.md"
    elif args.type == 'template':
        target_dir = os.path.join(doc_root, 'references', 'templates')
        filename = f"custom_{topic_slug}.md"

    # 3. 稳健创建父目录
    try:
        os.makedirs(target_dir, exist_ok=True)
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"目录自愈创建失败: {str(e)}"}))
        sys.exit(1)

    # 4. 路由特定的写入模式 (Append vs Overwrite)
    target_path = os.path.join(target_dir, filename)
    mode = 'w'
    final_write_content = content_to_write
    # now_str and now_date already computed above

    if args.type in ['index', 'log']:
        # index 和 log 永远是增量追加
        mode = 'a'
        if args.type == 'log':
            final_write_content = f"\n- **[{now_str}]** {content_to_write.strip()}"
        else: # index.md
            final_write_content = f"\n{content_to_write.strip()}"
            
    elif args.type in ['entity', 'concept'] and os.path.exists(target_path):
        # 知识节点增量追加
        mode = 'a'
        final_write_content = f"\n\n---\n## 增量知识点合入 ({now_str})\n\n" + content_to_write
        
    # 自动探测并注入 Frontmatter 时间戳 (仅对新建的 Markdown 有效)
    if mode == 'w' and args.type in ['source', 'entity', 'concept', 'raw', 'fact-index']:
        # 使用正则表达式匹配 Frontmatter 块
        fm_match = FRONTMATTER_RE.match(final_write_content.lstrip())
        if fm_match:
            fm_text = fm_match.group(1)
            # 检查内部是否已有 date 字段
            if not re.search(r'^date:', fm_text, re.MULTILINE | re.IGNORECASE):
                # 在第一个 --- 下方插入 date
                insertion = f"---\ndate: {now_date}\n"
                final_write_content = re.sub(r'^---\s*\n', insertion, final_write_content.lstrip(), count=1)
        else:
            # 完全没有 YAML Frontmatter 格式，强制注入一个
            final_write_content = f"---\ndate: {now_date}\n---\n\n" + final_write_content.lstrip()

    # 4.5 去重检查 (dedup check)
    dedup_status = "new"
    if os.path.exists(target_path) and args.dedup != 'overwrite':
        existing_size = os.path.getsize(target_path)
        if args.dedup == 'skip':
            with open(target_path, 'rb') as ef:
                existing_checksum = hashlib.sha256(ef.read()).hexdigest()
            receipt = {
                "status": "skipped",
                "dedup": "skipped",
                "type_routed": args.type,
                "path": target_path,
                "size_bytes": existing_size,
                "checksum": existing_checksum,
                "message": f"Entity already exists ({existing_size} bytes). Skipped per --dedup skip."
            }
            print(json.dumps(receipt, ensure_ascii=False))
            sys.exit(0)
        elif args.dedup == 'merge':
            # For entity/concept: append (mode already set above)
            # For source: refuse to merge, warn instead
            if args.type == 'source':
                receipt = {
                    "status": "skipped",
                    "dedup": "source_exists",
                    "type_routed": args.type,
                    "path": target_path,
                    "message": f"Source already exists. Use --dedup overwrite to replace, or pick a different topic."
                }
                print(json.dumps(receipt, ensure_ascii=False))
                sys.exit(0)
            dedup_status = "merged"

    # 4.6 Link sanitization — 仅对 entity/concept 写入生效，防止孤儿 wiki-link
    if args.type in ['entity', 'concept']:
        existing_content_for_sanitize = None
        if mode == 'a' and os.path.exists(target_path):
            # 追加模式：读取已有内容，只清理新增部分
            try:
                with open(target_path, 'r', encoding='utf-8') as ef:
                    existing_content_for_sanitize = ef.read()
            except Exception:
                pass
        final_write_content = sanitize_wiki_links(
            final_write_content, doc_root,
            existing_content=existing_content_for_sanitize
        )

    # 5. 原子落盘及防幻觉回执生成
    try:
        with open(target_path, mode, encoding='utf-8') as f:
            f.write(final_write_content)
        
        with open(target_path, 'rb') as f:
            file_bytes = f.read()
            checksum = hashlib.sha256(file_bytes).hexdigest()
            size_bytes = len(file_bytes)
            
        receipt = {
            "status": "success",
            "dedup": dedup_status,
            "type_routed": args.type,
            "path": target_path,
            "size_bytes": size_bytes,
            "checksum": checksum,
            "date": now_date,
            "message": "Karpathy Wiki Layer write valid."
        }
        print(json.dumps(receipt, ensure_ascii=False))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({"status": "error", "message": f"I/O 崩溃: {str(e)}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
