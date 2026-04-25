#!/usr/bin/env python3
"""测试 dashscope SDK 响应格式"""

import json
from pathlib import Path

# 读取 nanobot 配置
config_path = Path.home() / ".nanobot" / "config.json"
config = json.loads(config_path.read_text())

api_key = config["providers"]["dashscope"]["apiKey"]
api_base = config["providers"]["dashscope"]["apiBase"]

print(f"API Key: {api_key[:20]}...")
print(f"API Base: {api_base}")

# 测试 dashscope
import dashscope
from dashscope import Generation

print("\n调用 qwen3.5-plus...")
response = Generation.call(
    model="qwen3.5-plus",
    messages=[{"role": "user", "content": "你好"}],
    api_key=api_key
)

print(f"\n响应类型：{type(response)}")
print(f"响应属性：{dir(response)}")
print(f"\n响应内容:")
print(response)

# 尝试访问 output
if hasattr(response, 'output'):
    print(f"\noutput 类型：{type(response.output)}")
    print(f"output 属性：{dir(response.output)}")
    
    if hasattr(response.output, 'choices'):
        print(f"\nchoices: {response.output.choices}")
        if response.output.choices:
            print(f"content: {response.output.choices[0].message.content}")
