#!/usr/bin/env python3
"""
Auto-Coding 使用示例

展示如何使用 auto-coding 技能生成代码
"""

import asyncio
import sys
from pathlib import Path

# 添加技能目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from worker import AutoCodingWorker, WorkMode


async def example_1_quick():
    """示例 1: 快速模式 - 生成简单脚本"""
    print("=" * 60)
    print("示例 1: 快速模式 - 创建 Hello World 脚本")
    print("=" * 60)
    
    worker = AutoCodingWorker(mode=WorkMode.QUICK, use_llm=True)
    result = await worker.run('创建一个 Hello World Python 脚本')
    
    print(f"\n✅ 交付检查：{sum(result.delivery_checks.values())}/{len(result.delivery_checks)}")
    print(f"📄 代码:\n{result.final_code[:500]}...\n")


async def example_2_standard():
    """示例 2: 标准模式 - 生成实用工具"""
    print("=" * 60)
    print("示例 2: 标准模式 - 创建批量重命名工具")
    print("=" * 60)
    
    worker = AutoCodingWorker(mode=WorkMode.STANDARD, use_llm=True)
    result = await worker.run('创建一个批量重命名文件的脚本，支持正则表达式')
    
    print(f"\n✅ 交付检查：{sum(result.delivery_checks.values())}/{len(result.delivery_checks)}")
    print(f"📄 代码:\n{result.final_code[:800]}...\n")


async def example_3_thorough():
    """示例 3: 彻底模式 - 生成复杂应用"""
    print("=" * 60)
    print("示例 3: 彻底模式 - 创建 Web 爬虫")
    print("=" * 60)
    
    worker = AutoCodingWorker(mode=WorkMode.THOROUGH, use_llm=True, max_iterations=5)
    result = await worker.run('创建一个简单的 Web 爬虫，抓取网页标题')
    
    print(f"\n✅ 交付检查：{sum(result.delivery_checks.values())}/{len(result.delivery_checks)}")
    print(f"📄 代码:\n{result.final_code[:800]}...\n")


async def main():
    """运行所有示例"""
    print("\n🚀 Auto-Coding 使用示例\n")
    
    # 运行示例（取消注释以启用）
    # await example_1_quick()
    # await example_2_standard()
    # await example_3_thorough()
    
    print("💡 提示：取消注释 main() 中的函数调用来运行示例")
    print("\n或者自定义任务:")
    print("""
import asyncio
from worker import AutoCodingWorker

async def custom_task():
    worker = AutoCodingWorker(mode=WorkMode.STANDARD)
    result = await worker.run('你的任务描述')
    print(result.final_code)

asyncio.run(custom_task())
    """)


if __name__ == "__main__":
    asyncio.run(main())
