"""帝国架构 - 时间加速引擎"""
import asyncio
import time
from dataclasses import dataclass


@dataclass
class EmpireClock:
    """帝国时钟 - 十倍现实时间流速"""
    acceleration: float = 10.0
    start_real: float = 0.0
    start_empire: float = 0.0

    def __post_init__(self):
        self.start_real = time.time()
        self.start_empire = time.time()

    @property
    def real_elapsed(self) -> float:
        return time.time() - self.start_real

    @property
    def empire_elapsed(self) -> float:
        return self.real_elapsed * self.acceleration

    @property
    def empire_time(self) -> str:
        """帝国当前时间"""
        secs = self.empire_elapsed
        hours = int(secs // 3600)
        mins = int((secs % 3600) // 60)
        return f"{hours:02d}:{mins:02d}"

    @property
    def empire_speed(self) -> str:
        return f"{self.acceleration}x"


class AcceleratedExecutor:
    """加速执行器 - 多任务并行流水线"""

    def __init__(self, chancellor, max_parallel: int = 8):
        self.chancellor = chancellor
        self.max_parallel = max_parallel
        self.clock = EmpireClock(acceleration=10.0)
        self.task_log: list[dict] = []
        self.semaphore = asyncio.Semaphore(max_parallel)

    async def execute_batch(self, commands: list[str]) -> list[dict]:
        """批量并行执行多个指令"""
        async def run_one(cmd: str, idx: int):
            async with self.semaphore:
                print(f"  ⚡ [#{idx+1}] 开始: {cmd[:40]}...")
                result = await self.chancellor.receive_command(cmd)
                self.task_log.append(result)
                print(f"  ✅ [#{idx+1}] 完成: {result['elapsed_seconds']}s")
                return result

        coros = [run_one(cmd, i) for i, cmd in enumerate(commands)]
        results = await asyncio.gather(*coros, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]

    async def execute_stream(self, command: str) -> dict:
        """单指令加速执行（内部多节点并行）"""
        return await self.chancellor.receive_command(command)

    def get_dashboard(self) -> str:
        """帝国仪表盘"""
        real = self.clock.real_elapsed
        empire = self.clock.empire_elapsed
        tasks = len(self.task_log)
        status = self.chancellor.get_status()

        lines = [
            f"╔══════════════════════════════════════════════╗",
            f"║  帝国时间加速引擎  ⚡ {self.clock.empire_speed}                    ║",
            f"╠══════════════════════════════════════════════╣",
            f"║  现实时间: {real:.0f}s | 帝国时间: {empire:.0f}s ({self.clock.empire_time}) ║",
            f"║  已完成任务: {tasks}                            ║",
            f"║  活跃节点: {len(status['agents'])} | 消息: {status['message_history']}            ║",
            f"║  Token消耗: {self.chancellor.tracker.get_total_today()}                      ║",
            f"╚══════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)
