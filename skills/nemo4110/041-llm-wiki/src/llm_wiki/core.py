"""
LLM-Wiki 核心逻辑

处理 wiki 的读取、更新、索引维护。
"""

import hashlib
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Dict, Tuple
import yaml


@dataclass
class WikiPage:
    """Wiki 页面结构"""
    title: str
    content: str
    frontmatter: Dict
    path: Path

    @property
    def links(self) -> Set[str]:
        """提取页面中的所有 [[Link]]"""
        pattern = r'\[\[([^\]]+)\]\]'
        return set(re.findall(pattern, self.content))

    @property
    def status(self) -> str:
        return self.frontmatter.get('status', 'draft')

    @property
    def tags(self) -> List[str]:
        return self.frontmatter.get('tags', [])

    @property
    def content_hash(self) -> str:
        """计算页面内容哈希，用于增量更新"""
        text = f"{self.title}\n{'\n'.join(self.tags)}\n{self.content}"
        return hashlib.sha256(text.encode('utf-8')).hexdigest()


@dataclass
class IngestResult:
    """Ingest 操作结果"""
    source: str
    new_pages: List[str] = field(default_factory=list)
    updated_pages: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)


class WikiManager:
    """Wiki 管理器"""

    def __init__(self, wiki_dir: Path):
        self.wiki_dir = wiki_dir
        self.log_file = wiki_dir.parent / "log.md"
        self.index_file = wiki_dir / "index.md"

    def list_pages(self) -> List[WikiPage]:
        """列出所有 wiki 页面"""
        pages = []
        for md_file in self.wiki_dir.glob("*.md"):
            if md_file.name == "index.md":
                continue
            page = self._load_page(md_file)
            if page:
                pages.append(page)
        return pages

    def get_page(self, title: str) -> Optional[WikiPage]:
        """获取指定页面"""
        # 尝试多种文件名变体
        variations = [
            title,
            title.replace(' ', '-'),
            title.replace(' ', '_'),
        ]
        for var in variations:
            path = self.wiki_dir / f"{var}.md"
            if path.exists():
                return self._load_page(path)
        return None

    def create_page(self, title: str, content: str, frontmatter: Dict) -> Path:
        """创建新页面"""
        filename = f"{title.replace(' ', '-').replace('/', '-')}.md"
        path = self.wiki_dir / filename

        # 构建 frontmatter
        fm_lines = ["---"]
        for key, value in frontmatter.items():
            if isinstance(value, list):
                fm_lines.append(f"{key}:")
                for v in value:
                    fm_lines.append(f"  - \"{v}\"")
            else:
                fm_lines.append(f"{key}: \"{value}\"")
        fm_lines.append("---")

        full_content = "\n".join(fm_lines) + "\n\n" + content
        path.write_text(full_content, encoding='utf-8')
        return path

    def update_page(self, title: str, new_content: str,
                    merge_strategy: str = "append") -> Path:
        """更新现有页面"""
        page = self.get_page(title)
        if not page:
            raise ValueError(f"Page not found: {title}")

        # 更新 frontmatter
        page.frontmatter['updated'] = datetime.now().strftime('%Y-%m-%d')

        if merge_strategy == "replace":
            final_content = new_content
        else:  # append or smart merge
            final_content = self._merge_content(page.content, new_content)

        return self.create_page(title, final_content, page.frontmatter)

    def append_log(self, action: str, description: str,
                   details: List[str] = None):
        """追加日志条目"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_entry = f"\n## [{date_str}] {action} | {description}\n"
        if details:
            for detail in details:
                log_entry += f"- {detail}\n"

        # 追加到文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def read_log(self, n: int = 10) -> List[str]:
        """读取最近 n 条日志"""
        if not self.log_file.exists():
            return []

        content = self.log_file.read_text(encoding='utf-8')
        entries = re.findall(r'##\s*\[.*?\].*?(?=\n##|\Z)', content, re.DOTALL)
        return entries[-n:] if entries else []

    def lint(self) -> Dict[str, List[str]]:
        """运行健康检查"""
        issues = {
            'orphans': [],
            'dead_links': [],
            'stale': [],
            'drafts': [],
        }

        pages = self.list_pages()
        all_titles = {p.title for p in pages}
        all_links: Set[str] = set()

        for page in pages:
            # 收集所有链接
            all_links.update(page.links)

            # 检查草稿
            if page.status == 'draft':
                issues['drafts'].append(page.title)

            # 检查陈旧页面（90天未更新）
            updated = page.frontmatter.get('updated')
            if updated:
                try:
                    upd_date = datetime.strptime(updated, '%Y-%m-%d')
                    if (datetime.now() - upd_date).days > 90:
                        issues['stale'].append(page.title)
                except:
                    pass

        # 检查孤儿页面（没有被引用的页面）
        # 排除 index.md 和明显是入口的页面
        for page in pages:
            if page.title not in all_links and page.title != 'index':
                issues['orphans'].append(page.title)

        # 检查死链
        for link in all_links:
            if link not in all_titles:
                issues['dead_links'].append(link)

        return issues

    def _load_page(self, path: Path) -> Optional[WikiPage]:
        """从文件加载页面"""
        try:
            content = path.read_text(encoding='utf-8')

            # 解析 frontmatter
            frontmatter = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                        content = parts[2].strip()
                    except:
                        pass

            # 提取标题（第一个 # 行）
            title = path.stem
            for line in content.split('\n'):
                if line.startswith('# '):
                    title = line[2:].strip()
                    break

            return WikiPage(
                title=title,
                content=content,
                frontmatter=frontmatter,
                path=path
            )
        except Exception as e:
            print(f"Error loading page {path}: {e}")
            return None

    def _merge_content(self, old: str, new: str) -> str:
        """智能合并内容"""
        # 延迟导入避免循环依赖
        from .merge import ContentMerger, MergeStrategy
        merger = ContentMerger(self)
        # 构造一个临时页面对象用于合并
        temp_page = WikiPage(
            title="temp",
            content=old,
            frontmatter={"updated": datetime.now().strftime('%Y-%m-%d')},
            path=self.wiki_dir / "temp.md",
        )
        # 尝试 APPEND_SECTION 策略，追加为"补充说明"章节
        result = merger.append_after_section(
            old,
            "## 补充说明",
            new,
        )
        return result


def find_wiki_root(start_path: Path = None) -> Optional[Path]:
    """向上查找 wiki 根目录（包含 CLAUDE.md 的目录）"""
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    while current != current.parent:
        if (current / "CLAUDE.md").exists():
            return current
        current = current.parent

    # 检查常见位置
    candidates = [
        Path.home() / "llm-wiki",
        Path.home() / "wiki",
        Path.cwd() / "llm-wiki",
    ]
    for cand in candidates:
        if cand.exists() and (cand / "CLAUDE.md").exists():
            return cand

    return None
