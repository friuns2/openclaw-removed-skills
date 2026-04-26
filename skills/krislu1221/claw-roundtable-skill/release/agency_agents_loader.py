#!/usr/bin/env python3
"""
从 agency-agents-zh 加载 146 个专家档案

功能：
1. 扫描所有专家 Markdown 文件
2. 解析 frontmatter 和正文
3. 转换为 AgentProfile 格式
4. 支持按领域筛选

安全加固：
- 路径遍历防护
- 输入验证
- 安全的日志记录

作者：虾软 Claw soft
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentProfile:
    """Agent 档案（从 Markdown 文件加载）"""
    agent_id: str
    name: str
    description: str
    category: str
    content: str
    file_path: str


class AgencyAgentsLoader:
    """agency-agents-zh 加载器（安全加固版）"""
    
    def __init__(self, base_path: str = None):
        """
        初始化加载器
        
        Args:
            base_path: agency-agents-zh 基础路径
            
        默认路径优先级：
        1. 传入的 base_path 参数
        2. 环境变量 AGENCY_AGENTS_PATH（需验证）
        3. 默认路径（相对于当前文件）
        """
        if base_path is None:
            env_path = os.environ.get("AGENCY_AGENTS_PATH")
            if env_path:
                if self._is_safe_path(env_path):
                    base_path = env_path
                else:
                    logger.warning(f"AGENCY_AGENTS_PATH 路径不安全，使用默认路径")
            
            if base_path is None:
                base_path = os.path.join(
                    os.path.dirname(__file__),
                    "agency-agents-zh"
                )
        
        self.base_path = Path(base_path).resolve()
        
        if not self._is_safe_path(str(self.base_path)):
            raise ValueError(f"不安全的 base_path: {self.base_path}")
        
        self.agents: Dict[str, AgentProfile] = {}
        self.categories: Dict[str, List[str]] = {}
    
    def _is_safe_path(self, path: str) -> bool:
        """
        验证路径是否安全
        
        安全标准：
        1. 必须在技能目录内
        2. 不允许访问系统敏感目录
        3. 不允许符号链接跳出目录
        """
        try:
            real_path = os.path.realpath(path)
            skill_dir = os.path.realpath(os.path.dirname(__file__))
            
            # 必须位于技能目录内
            if not real_path.startswith(skill_dir):
                logger.warning(f"路径不在技能目录内：{real_path}")
                return False
            
            # 禁止访问敏感目录
            forbidden = ['/etc', '/proc', '/sys', '/root']
            if any(real_path.startswith(p) for p in forbidden):
                return False
            
            return True
        except Exception as e:
            logger.error(f"路径验证失败：{e}")
            return False
    
    def load_all(self) -> Dict[str, AgentProfile]:
        """加载所有专家档案（安全加固）"""
        logger.info(f"从 {self.base_path} 加载专家档案...")
        
        if not self.base_path.exists():
            logger.error(f"专家目录不存在：{self.base_path}")
            return {}
        
        if not self.base_path.is_dir():
            logger.error(f"专家目录不是目录：{self.base_path}")
            return {}
        
        md_files = []
        real_base = str(self.base_path)
        
        for file_path in self.base_path.rglob("*.md"):
            try:
                real_file = str(file_path.resolve())
                
                if not real_file.startswith(real_base):
                    logger.warning(f"跳过目录外文件：{file_path}")
                    continue
                
                if self._should_exclude(file_path):
                    continue
                
                md_files.append(file_path)
            except Exception as e:
                logger.warning(f"处理文件失败 {file_path}: {e}")
        
        logger.info(f"找到 {len(md_files)} 个专家文件")
        
        for file_path in md_files:
            try:
                agent = self._load_agent_file(file_path)
                if agent:
                    self.agents[agent.agent_id] = agent
                    if agent.category not in self.categories:
                        self.categories[agent.category] = []
                    self.categories[agent.category].append(agent.agent_id)
            except Exception as e:
                logger.error(f"加载失败 {file_path}: {type(e).__name__}")
        
        logger.info(f"成功加载 {len(self.agents)} 个专家")
        return self.agents
    
    def _should_exclude(self, file_path: Path) -> bool:
        """判断文件是否应该排除"""
        exclude_files = [
            "README.md", "CONTRIBUTING.md", "UPSTREAM.md",
            "QUICKSTART.md", "EXECUTIVE-BRIEF.md"
        ]
        exclude_dirs = ["strategy", "coordination", "playbooks", "runbooks"]
        
        if file_path.name in exclude_files:
            return True
        
        if file_path.parent.name in exclude_dirs:
            return True
        
        if "strategy" in str(file_path.parent):
            return True
        
        return False
    
    def _load_agent_file(self, file_path: Path) -> Optional[AgentProfile]:
        """加载单个专家文件（安全加固）"""
        try:
            file_size = file_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB 限制
                logger.warning(f"文件过大，跳过：{file_path} ({file_size} bytes)")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontmatter = self._parse_frontmatter(content)
            if not frontmatter:
                return None
            
            agent_id = file_path.stem
            category = file_path.parent.name
            
            return AgentProfile(
                agent_id=agent_id,
                name=frontmatter.get('name', agent_id),
                description=frontmatter.get('description', ''),
                category=category,
                content=content,
                file_path=str(file_path)
            )
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {type(e).__name__}")
            return None
    
    def _parse_frontmatter(self, content: str) -> Optional[Dict]:
        """解析 Markdown frontmatter"""
        match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if not match:
            return None
        
        frontmatter_text = match.group(1)
        frontmatter = {}
        
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()
        
        return frontmatter
    
    def get_agents_by_category(self, category: str) -> List[AgentProfile]:
        """按分类获取专家"""
        agent_ids = self.categories.get(category, [])
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    def get_agents_by_keywords(self, keywords: List[str]) -> List[AgentProfile]:
        """按关键词匹配专家"""
        if not keywords:
            return []
        
        matched = []
        for agent in self.agents.values():
            search_text = f"{agent.name} {agent.description} {agent.category}".lower()
            if any(kw.lower() in search_text for kw in keywords):
                matched.append(agent)
        return matched
    
    def get_expert_prompt(self, agent_id: str, topic: str, focus: Dict) -> str:
        """生成专家提示词"""
        agent = self.agents.get(agent_id)
        if not agent:
            return ""
        
        content = re.sub(r'^---\n.*?\n---\n', '', agent.content, flags=re.DOTALL)
        safe_topic = topic[:500] if topic else "未知主题"
        
        prompt = f"""{content}

## 当前讨论主题
**{safe_topic}**

## 你的专业领域
{agent.description}

## 当前议题
**{focus.get('name', '未知')}**

## 焦点问题
{chr(10).join(['- ' + q for q in focus.get('focus_questions', [])])}

---

## 你的任务
请从你的专业角度，对当前议题进行深度分析。

### 必须包含的内容
1. **专业分析**（400 字以上）
2. **实施建议**（200 字以上）

请开始你的专业分析：
"""
        return prompt
    
    def list_all_agents(self) -> str:
        """列出所有专家"""
        lines = ["# 146 个专家完整列表\n"]
        for category, agent_ids in sorted(self.categories.items()):
            lines.append(f"\n## {category}\n")
            for agent_id in agent_ids:
                agent = self.agents.get(agent_id)
                if agent:
                    lines.append(f"- **{agent.name}** (`{agent_id}`) - {agent.description}")
        return "\n".join(lines)


def load_all_agents() -> Dict[str, AgentProfile]:
    """快捷函数：加载所有专家"""
    loader = AgencyAgentsLoader()
    return loader.load_all()


def get_agents_for_topic(topic: str) -> List[AgentProfile]:
    """快捷函数：根据主题获取相关专家"""
    loader = AgencyAgentsLoader()
    loader.load_all()
    keywords = topic.split()
    return loader.get_agents_by_keywords(keywords)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loader = AgencyAgentsLoader()
    agents = loader.load_all()
    print(f"\n📊 统计信息：")
    print(f"  总专家数：{len(agents)}")
    print(f"  分类数：{len(loader.categories)}")
