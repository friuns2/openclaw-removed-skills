#!/usr/bin/env python3
"""
帝国架构 v1 精简版 - CLI
Empire Architecture v1 Lite

用法:
  python3 main.py              # 交互模式
  python3 main.py "指令"        # 单次执行
  python3 main.py --status     # 查看状态
"""
import asyncio
import json
import sys
import os
import signal
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from chancellor import Chancellor


class EmpireCLI:
    """帝国控制台"""

    def __init__(self):
        self.chancellor = Chancellor()
        self.running = True

    def print_banner(self):
        print("""
╔══════════════════════════════════════════════╗
║       帝国架构 v1 精简版  Empire Lite        ║
║──────────────────────────────────────────────║
║  皇帝: AARONCXXX    丞相: Mimo              ║
║  参谋: 3人          执行: 3人               ║
║  安全: 锦衣卫       总计: 9个节点            ║
╚══════════════════════════════════════════════╝
        """)

    def print_help(self):
        print("""
命令:
  <指令>        向帝国下达指令
  status        查看帝国状态
  agents        查看所有节点状态
  tokens        查看 token 使用情况
  history       查看消息历史
  help          显示帮助
  exit / quit   退出
        """)

    async def execute_command(self, command: str):
        """执行皇帝指令"""
        print(f"\n⚡ 丞相接令，开始编排...")
        print(f"{'─' * 50}")

        try:
            result = await self.chancellor.receive_command(command)

            # 打印结果
            print(f"\n📋 任务 {result['task_id']} 完成 ({result['elapsed_seconds']}s)")
            print(f"{'─' * 50}")

            for agent_id, content in result["results"].items():
                if agent_id == "chancellor_summary":
                    continue
                agent = self.chancellor.agents.get(agent_id)
                name = agent.state.name if agent else agent_id
                print(f"\n🔸 {name}:")
                # 截断显示
                display = content[:500] + "..." if len(content) > 500 else content
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

            print(f"\n⏱  耗时: {result['elapsed_seconds']}s | Token 今日总消耗: {result['tokens_used']}")

        except Exception as e:
            print(f"\n❌ 执行失败: {e}")

    def show_status(self):
        status = self.chancellor.get_status()
        print(f"\n{'═' * 50}")
        print(f"帝国状态")
        print(f"{'─' * 50}")
        print(f"节点数: {len(status['agents'])}")
        print(f"消息总数: {status['message_history']}")
        print(f"安全事件: {status['security']['total_violations']}")

    def show_agents(self):
        status = self.chancellor.get_status()
        print(f"\n{'═' * 50}")
        print(f"节点状态")
        print(f"{'─' * 50}")
        for aid, info in status["agents"].items():
            icon = {"idle": "🟢", "busy": "🟡", "error": "🔴"}.get(info["status"], "⚪")
            print(f"  {icon} {info['name']:8s} [{info['role']:8s}] "
                  f"状态:{info['status']:6s} 完成:{info['tasks_completed']} "
                  f"运行:{info['uptime']}s")

    def show_tokens(self):
        usage = self.chancellor.tracker.get_usage()
        print(f"\n{'═' * 50}")
        print(f"Token 使用")
        print(f"{'─' * 50}")
        total_input = 0
        total_output = 0
        for agent_id, info in usage.items():
            name = self.chancellor.agents[agent_id].state.name if agent_id in self.chancellor.agents else agent_id
            print(f"  {name:8s} 输入:{info['input']:6d} 输出:{info['output']:6d}")
            total_input += info["input"]
            total_output += info["output"]
        print(f"{'─' * 50}")
        print(f"  总计    输入:{total_input:6d} 输出:{total_output:6d} 合计:{total_input+total_output}")

    def show_history(self):
        history = self.chancellor.bus.get_history(20)
        print(f"\n{'═' * 50}")
        print(f"最近消息 (最新20条)")
        print(f"{'─' * 50}")
        for msg in history:
            ts = time.strftime("%H:%M:%S", time.localtime(msg.timestamp))
            print(f"  [{ts}] {msg.sender} → {msg.receiver} ({msg.msg_type.value}): {msg.content[:80]}")

    async def interactive(self):
        """交互模式"""
        self.print_banner()
        self.print_help()

        while self.running:
            try:
                cmd = input("\n👑 皇帝> ").strip()
                if not cmd:
                    continue

                if cmd in ("exit", "quit", "q"):
                    print("帝国关闭。皇帝万岁。")
                    break
                elif cmd == "help":
                    self.print_help()
                elif cmd == "status":
                    self.show_status()
                elif cmd == "agents":
                    self.show_agents()
                elif cmd == "tokens":
                    self.show_tokens()
                elif cmd == "history":
                    self.show_history()
                else:
                    await self.execute_command(cmd)

            except KeyboardInterrupt:
                print("\n帝国关闭。")
                break
            except EOFError:
                break


async def main():
    cli = EmpireCLI()

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--status":
            cli.show_status()
        elif arg == "--agents":
            cli.show_agents()
        elif arg == "--tokens":
            cli.show_tokens()
        else:
            # 单次执行模式
            command = " ".join(sys.argv[1:])
            await cli.execute_command(command)
    else:
        await cli.interactive()


if __name__ == "__main__":
    asyncio.run(main())
