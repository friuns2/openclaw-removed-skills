#!/usr/bin/env python3
"""帝国架构 v1.4 运行器 - 带知识库挂载"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/empire-architecture/lite"))
from chancellor import Chancellor
from knowledge.mount import mount_knowledge


BANNER = """
╔══════════════════════════════════════════════════╗
║     帝国架构 v1.5  Empire v1.5                   ║
║──────────────────────────────────────────────────║
║  皇帝: AARONCXXX    丞相: Mimo                   ║
║  参谋: 3人          执行: 3人                    ║
║  六部: 6人          翰林院: 2人                  ║
║  特殊: 3人          监察: 2人                    ║
║  扩展: 3人          安全: 锦衣卫                 ║
║  总计: 24 节点                                    ║
╚══════════════════════════════════════════════════╝
"""


async def main():
    print(BANNER)

    # 初始化帝国
    chancellor = Chancellor()

    # 挂载知识库 (v1.4 新增)
    print("📚 挂载知识库层...")
    kb = mount_knowledge(chancellor)
    router = kb["router"]
    director = kb["director"]

    sources = router.list_sources()
    print(f"✅ 知识源已挂载: {', '.join(sources) if sources else '无（全部待审批）'}")

    # 显示知识源状态
    status = director.get_status()
    for sid, info in status["scholars"].items():
        print(f"  📖 {info['name']} [{info['source']}]")

    print()

    # 执行指令
    command = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "帮我分析帝国架构的知识管理体系如何提升多智能体协作效率"

    print(f"⚡ 丞相接令: {command}")
    print("─" * 50)

    result = await chancellor.receive_command(command)

    # 输出结果
    print(f"\n📋 任务 {result['task_id']} 完成 ({result['elapsed_seconds']}s)")
    print("─" * 50)

    for agent_id, content in result["results"].items():
        if agent_id == "chancellor_summary":
            continue
        agent = chancellor.agents.get(agent_id)
        name = agent.state.name if agent else agent_id
        display = content[:500] + "..." if len(content) > 500 else content
        print(f"\n🔸 {name}:")
        print(f"  {display}")

    print(f"\n{'═' * 50}")
    print(f"📊 丞相汇总:")
    print(result["results"].get("chancellor_summary", "无汇总"))

    audit = result.get("audit", {})
    safe_icon = "✅" if audit.get("safe", True) else "⚠️"
    print(f"\n{safe_icon} 锦衣卫审计: {'通过' if audit.get('safe', True) else '发现问题'}")
    if audit.get("issues"):
        for issue in audit["issues"]:
            print(f"   - {issue}")

    print(f"\n⏱  耗时: {result['elapsed_seconds']}s | Token 消耗: {result['tokens_used']}")

    # 知识库状态
    print(f"\n📚 翰林院状态:")
    for sid, info in status["scholars"].items():
        print(f"  {info['name']}: 检索{info['queries_served']}次, 索引{info['docs_indexed']}篇")


if __name__ == "__main__":
    asyncio.run(main())
