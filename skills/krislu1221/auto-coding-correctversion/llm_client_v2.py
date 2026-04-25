#!/usr/bin/env python3
"""
Auto-Coding LLM Client - 使用 nanobot 内部机制

由于 DashScope API Key 是 nanobot 内部集成的特殊格式，
我们使用降级方案：通过 exec 调用 nanobot CLI 来生成代码。
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM 配置"""
    model: str = "qwen3.5-plus"
    max_tokens: int = 8192
    temperature: float = 0.1


class AutoCodingLLM:
    """
    Auto-Coding 专用 LLM 客户端
    
    使用 nanobot 内部机制调用 LLM
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.nanobot_path = Path.home() / ".nanobot"
        self.config_file = self.nanobot_path / "config.json"
        
        # 检查 nanobot 配置
        if self.config_file.exists():
            print(f"✅ 找到 nanobot 配置")
        else:
            print(f"⚠️  未找到 nanobot 配置")
    
    async def chat(self, messages: list[dict[str, Any]]) -> str:
        """
        通过 nanobot 内部机制发送聊天请求
        
        由于 API Key 是内部集成的，我们通过临时脚本调用 nanobot
        """
        try:
            # 创建一个临时 Python 脚本来调用 nanobot
            temp_script = self._create_temp_script(messages)
            
            # 执行脚本
            result = subprocess.run(
                [sys.executable, str(temp_script)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.nanobot_path)
            )
            
            # 清理临时文件
            temp_script.unlink(missing_ok=True)
            
            if result.returncode == 0:
                print(f"  ✅ LLM 调用成功")
                return result.stdout.strip()
            else:
                print(f"  ❌ 执行失败：{result.stderr[:200]}")
                return self._fallback_response(messages)
                
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  LLM 调用超时")
            return self._fallback_response(messages)
        except Exception as e:
            print(f"  ⚠️  LLM 调用异常：{e}")
            return self._fallback_response(messages)
    
    def _create_temp_script(self, messages: list[dict]) -> Path:
        """创建临时调用脚本"""
        import tempfile
        
        # 构建 prompt
        user_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_content += msg.get("content", "") + "\n"
        
        script_content = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/krislu/nanobot')

from nanobot.providers.litellm_provider import LiteLLMProvider
import asyncio
import json

async def main():
    # 从 config.json 读取配置
    from pathlib import Path
    
    config_path = Path.home() / ".nanobot" / "config.json"
    config = json.loads(config_path.read_text())
    
    dashscope_config = config.get("providers", {}).get("dashscope", {})
    api_key = dashscope_config.get("apiKey")
    api_base = dashscope_config.get("apiBase")
    
    if not api_key:
        print("Error: No API key found")
        sys.exit(1)
    
    # 创建 provider
    provider = LiteLLMProvider(
        api_key=api_key,
        api_base=api_base,
        default_model="dashscope/qwen3.5-plus"
    )
    
    # 调用 LLM
    user_content = """''' + user_content.replace('"""', '\\"\\"\\"') + '''"""
    messages = [
        {"role": "user", "content": user_content}
    ]
    
    response = await provider.chat(
        messages=messages,
        max_tokens=8192,
        temperature=0.1
    )
    
    print(response.content or "")

asyncio.run(main())
'''
        
        # 写入临时文件
        fd, temp_path = tempfile.mkstemp(suffix='.py', prefix='nanobot_llm_')
        with os.fdopen(fd, 'w') as f:
            f.write(script_content)
        
        return Path(temp_path)
    
    def _fallback_response(self, messages: list[dict]) -> str:
        """降级响应"""
        return '# 自动生成的代码\n\n注意：LLM 服务暂时不可用。\n\n```python\n#!/usr/bin/env python3\ndef main():\n    print("Hello World")\n\nif __name__ == "__main__":\n    main()\n```'
    
    async def generate_code(self, task: str, analysis: dict, search_results: list) -> str:
        """生成代码"""
        prompt = f"""你是一个专业的软件工程师。请实现以下功能：

**任务**: {task}

**需求**:
- 项目类型：{analysis.get('project_type', '脚本')}
- 复杂度：{analysis.get('complexity', 'medium')}
- 需要技能：{', '.join(analysis.get('required_skills', []))}

请生成**完整的、可运行的**Python 代码，包含：
1. 完整的 shebang 和模块文档
2. 必要的 import 语句
3. 主函数实现具体功能
4. 适当的错误处理
5. 清晰的注释

直接返回代码，用 ```python 包裹。"""

        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages)
    
    async def delivery_check(self, task: str, code: str) -> dict:
        """
        交付检查
        
        Args:
            task: 任务描述
            code: 代码内容
        
        Returns:
            检查结果（JSON 格式）
        """
        prompt = f"""你是一个严格的代码审查员。请检查以下代码是否达到交付标准：

**任务**: {task}

**代码**:
```python
{code[:3000]}
```

**检查清单**:
- [ ] 代码能运行（无语法错误）
- [ ] 有基本测试（测试用例或示例）
- [ ] 有文档（模块文档和关键注释）
- [ ] 有错误处理（try-except 和错误提示）
- [ ] 安全检查（无 eval/exec/命令注入等）
- [ ] 功能完整（实现了所有需求）

请**仅**返回 JSON 格式：
{{
  "checks": [
    {{"name": "runs_without_error", "status": "pass|fail|warning", "details": "..."}},
    {{"name": "has_basic_tests", "status": "pass|fail|warning", "details": "..."}},
    {{"name": "has_documentation", "status": "pass|fail|warning", "details": "..."}},
    {{"name": "has_error_handling", "status": "pass|fail|warning", "details": "..."}},
    {{"name": "security_check_passed", "status": "pass|fail|warning", "details": "..."}},
    {{"name": "feature_complete", "status": "pass|fail|warning", "details": "..."}}
  ],
  "ready_to_deliver": true|false,
  "suggestions": ["...", "..."]
}}"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages)
        
        # 解析 JSON
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response)
        except Exception:
            return {
                "checks": [],
                "ready_to_deliver": False,
                "suggestions": ["LLM 解析失败，请手动检查"]
            }
    
    async def reflect_and_fix(self, task: str, code: str, errors: list, reflection: str) -> str:
        """根据反思修复代码"""
        prompt = f"""你是一个擅长调试的开发者。请修复以下代码：

**任务**: {task}

**当前代码**:
```python
{code[:3000]}
```

**测试错误**:
{chr(10).join([f"- {e}" for e in errors])}

**反思结果**:
{reflection}

请：
1. 分析错误原因
2. 提供修复后的完整代码
3. 确保修复后的代码能通过所有测试

请**仅**返回修复后的代码，用 ```python 包裹。"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages)
        
        # 提取代码
        import re
        code_match = re.search(r'```(?:python)?\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1)
        return response


if __name__ == "__main__":
    async def test():
        print("🚀 测试 LLM Client (nanobot 内部机制)...\n")
        
        llm = AutoCodingLLM()
        response = await llm.chat([{"role": "user", "content": "你好"}])
        
        print(f"\n✅ 响应:\n{response[:200]}...")
    
    asyncio.run(test())
