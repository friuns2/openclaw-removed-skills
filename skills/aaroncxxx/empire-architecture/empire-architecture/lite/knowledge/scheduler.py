"""
翰林院定时任务 - 每 2 小时自动出报表
Hanlin Scheduler - Auto-report every 2 hours

集成方式：
  在帝国主循环中调用 HanlinScheduler.tick() 即可。
  或者独立运行 python3 -m knowledge.scheduler
"""

import asyncio
import time
from .audit import KnowledgeAudit


class HanlinScheduler:
    """翰林院定时任务调度器"""

    def __init__(self, audit: KnowledgeAudit, interval_seconds: int = 7200):
        self.audit = audit
        self.interval = interval_seconds
        self._running = False

    async def tick(self) -> str | None:
        """
        主循环中调用此方法。
        到时间则生成报表并返回文本，否则返回 None。
        """
        if not self.audit.should_report():
            return None
        return await self._generate_and_notify()

    async def _generate_and_notify(self) -> str:
        """生成报表 + 保存 + 返回文本"""
        report = self.audit.generate_report(self.interval)
        self.audit.save_report(report)
        text = self.audit.format_report_text(report)
        return text

    async def run_loop(self, callback=None):
        """
        独立循环模式。
        callback: 接收报表文本的回调函数（如发送到消息频道）
        """
        self._running = True
        while self._running:
            await asyncio.sleep(60)  # 每分钟检查一次
            if self.audit.should_report():
                text = await self._generate_and_notify()
                if callback:
                    await callback(text)
                else:
                    print(text)

    def stop(self):
        self._running = False


# 独立运行入口
async def _main():
    audit = KnowledgeAudit()
    scheduler = HanlinScheduler(audit)

    async def print_report(text: str):
        print(text)

    print("翰林院审计调度器启动，每 2 小时出报表...")
    await scheduler.run_loop(callback=print_report)


if __name__ == "__main__":
    asyncio.run(_main())
