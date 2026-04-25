#!/usr/bin/env python3
"""
Auto-Coding LLM Client - 复用 nanobot 实例的 LLM 配置

使用 OpenAI 兼容 API 调用 dashscope（coding.dashscope.aliyuncs.com）
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM 配置（从 nanobot config 继承）"""
    provider: str = "dashscope"
    model: str = "qwen3.5-plus"
    api_key: str = ""
    api_base: str = "https://coding.dashscope.aliyuncs.com/v1"
    max_tokens: int = 8192
    temperature: float = 0.1
    
    @classmethod
    def from_nanobot_config(cls, config_path: Optional[Path] = None) -> "LLMConfig":
        """从 nanobot config.json 加载配置"""
        if config_path is None:
            config_path = Path.home() / ".nanobot" / "config.json"
        
        if not config_path.exists():
            print(f"⚠️  未找到 nanobot 配置：{config_path}")
            return cls()
        
        try:
            config = json.loads(config_path.read_text())
            
            # 读取默认配置
            defaults = config.get("agents", {}).get("defaults", {})
            provider_name = defaults.get("provider", "dashscope")
            model = defaults.get("model", "qwen3.5-plus")
            
            # 读取 provider 配置
            providers = config.get("providers", {})
            provider_config = providers.get(provider_name, {})
            
            api_key = provider_config.get("apiKey", "")
            api_base = provider_config.get("apiBase", "")
            
            return cls(
                provider=provider_name,
                model=model,
                api_key=api_key,
                api_base=api_base if api_base else cls().api_base,
                max_tokens=defaults.get("maxTokens", 8192),
                temperature=defaults.get("temperature", 0.1)
            )
            
        except Exception as e:
            print(f"⚠️  读取 nanobot 配置失败：{e}")
            return cls()


class AutoCodingLLM:
    """
    Auto-Coding 专用 LLM 客户端
    
    复用 nanobot 实例的 LLM 配置，使用 OpenAI 兼容 API 调用
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_nanobot_config()
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """初始化 LLM 客户端"""
        if not self.config.api_key:
            print(f"⚠️  未找到 API Key，将使用降级模式")
            return
        
        try:
            # 尝试导入 openai 或 httpx
            try:
                import httpx
                self._client = httpx
                print(f"✅ LLM 已初始化：{self.config.model} ({self.config.provider}) - OpenAI 兼容 API")
            except ImportError:
                import requests
                self._client = requests
                print(f"✅ LLM 已初始化：{self.config.model} ({self.config.provider}) - requests")
            
        except ImportError:
            print(f"⚠️  httpx/requests 未安装，将使用降级模式")
            self._client = None
        except Exception as e:
            print(f"⚠️  LLM 初始化失败：{e}")
            self._client = None
    
    async def chat(self, messages: list[dict[str, Any]], system_prompt: Optional[str] = None) -> str:
        """
        发送聊天请求（使用 OpenAI 兼容 API）
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            system_prompt: 可选的系统提示词
        
        Returns:
            LLM 响应文本
        """
        if not self._client:
            return self._fallback_response(messages)
        
        try:
            # 构建消息
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
            
            # 构建请求体
            payload = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
            
            # 调用 API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            if hasattr(self._client, 'post'):  # httpx
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._client.post(
                        f"{self.config.api_base}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                )
                response.raise_for_status()
                data = response.json()
            else:  # requests
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._client.post(
                        f"{self.config.api_base}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                )
                response.raise_for_status()
                data = response.json()
            
            # 解析响应
            if data and "choices" in data and data["choices"]:
                content = data["choices"][0]["message"]["content"]
                print(f"  ✅ LLM 调用成功")
                return content
            else:
                print(f"  ⚠️  LLM 响应为空：{data}")
                return self._fallback_response(messages)
                
        except Exception as e:
            print(f"  ⚠️  LLM 调用失败：{e}")
            return self._fallback_response(messages)
    
    def _fallback_response(self, messages: list[dict]) -> str:
        """降级响应（当 LLM 不可用时）"""
        return '# 自动生成的代码\n\n注意：LLM 服务暂时不可用。\n\n```python\n#!/usr/bin/env python3\ndef main():\n    print("Hello World")\n\nif __name__ == "__main__":\n    main()\n```'
    
    async def generate_code(self, task: str, analysis: dict, search_results: list) -> str:
        """生成代码"""
        system_prompt = """你是一个专业的软件工程师。请生成完整的、可运行的 Python 代码。

要求：
1. 完整的 shebang 和模块文档
2. 必要的 import 语句
3. 主函数实现具体功能
4. 适当的错误处理（try-except）
5. 清晰的注释
6. 遵循 PEP 8 代码风格

直接返回代码，用 ```python 包裹。"""

        prompt = f"""**任务**: {task}

**需求分析**:
- 项目类型：{analysis.get('project_type', '脚本')}
- 复杂度：{analysis.get('complexity', 'medium')}
- 需要技能：{', '.join(analysis.get('required_skills', []))}

请实现这个功能。"""

        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, system_prompt)
    
    async def delivery_check(self, task: str, code: str) -> dict:
        """交付检查"""
        system_prompt = """你是一个严格的代码审查员。请检查代码是否达到交付标准。

请**仅**返回 JSON 格式，不要其他内容。"""

        prompt = f"""**任务**: {task}

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

请返回 JSON 格式：
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
        response = await self.chat(messages, system_prompt)
        
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
        system_prompt = """你是一个擅长调试的开发者。请修复代码中的问题。

请**仅**返回修复后的代码，用 ```python 包裹。"""

        prompt = f"""**任务**: {task}

**当前代码**:
```python
{code[:3000]}
```

**测试错误**:
{chr(10).join([f"- {e}" for e in errors])}

**反思结果**:
{reflection}

请分析错误原因，提供修复后的完整代码。"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages, system_prompt)
        
        # 提取代码
        import re
        code_match = re.search(r'```(?:python)?\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1)
        return response


if __name__ == "__main__":
    async def test():
        print("🚀 测试 LLM Client (OpenAI 兼容 API)...\n")
        
        # 从 nanobot config 加载配置
        config = LLMConfig.from_nanobot_config()
        print(f"配置：{config.provider}/{config.model}")
        print(f"API Base: {config.api_base}")
        
        llm = AutoCodingLLM(config)
        
        if llm._client:
            response = await llm.chat([{"role": "user", "content": "你好，请简单介绍一下自己"}])
            print(f"\n✅ 响应:\n{response[:200]}...")
        else:
            print("\n⚠️  LLM 未初始化，使用降级模式")
    
    asyncio.run(test())
