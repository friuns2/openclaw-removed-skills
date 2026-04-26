#!/usr/bin/env python3
"""
RoundTable 用户确认和进度通知模块

功能：
1. 用户意图检测（复杂问题 → 推荐 RoundTable）
2. 发送确认消息（说明耗时）
3. 进度通知（每轮完成）
4. 完成报告通知

⚠️ 安全说明：
- 本模块仅发送进度通知，不包含讨论内容
- 发送的渠道 ID 由用户提供，不存储
- 不读取、不传输任何敏感信息
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, List

from requirement_analyzer import EXPERT_PROFILES


class RoundTableNotifier:
    """RoundTable 通知器"""
    
    def __init__(self, topic: str, mode: str = "pre-ac"):
        self.topic = topic
        self.mode = mode
        self.start_time: Optional[datetime] = None
        self.current_round: int = 0
        self.total_rounds: int = 5
        
    async def send_confirmation_request(self, user_channel: str) -> bool:
        """
        发送 RoundTable 确认请求
        
        Returns:
            bool: 用户是否确认开始
        """
        message = f"""
🔄 **RoundTable 多 Agent 深度讨论**

**讨论主题**：{self.topic}

📋 **讨论说明**：
- 参与 Agent：DevAgent（技术）+ AIBot（AI）+ UXDesigner（体验）
- 讨论轮次：5 轮深度讨论（R1-R5）
- 预计耗时：**10-30 分钟**
- 输出内容：完整技术方案 + 多方观点 + 行动建议

⚠️ **请注意**：
- RoundTable 适合需要深度分析的场景
- 如果您需要快速回答，请使用普通对话
- 讨论过程中您可以随时查看进度

**请确认您的需求**：
回复 "**确认**" 开始 RoundTable 深度讨论
回复 "**快速**" 获取简要方案（<1 分钟）
"""
        
        # 发送确认消息（通过飞书或其他渠道）
        # await send_message(user_channel, message)
        print(f"📤 已发送确认请求到 {user_channel}")
        print(message)
        
        # 等待用户确认（实际实现中需要等待用户回复）
        # user_response = await wait_for_user_response(timeout=300)
        # return user_response.lower() in ["确认", "confirm", "yes"]
        return True  # 演示用，默认确认
    
    async def send_start_notification(self, user_channel: str):
        """发送开始通知"""
        self.start_time = datetime.now()
        
        message = f"""
🚀 **RoundTable 已启动**

**主题**：{self.topic}
**状态**：R1 轮讨论中（1/{self.total_rounds}）
**参与**：DevAgent · AIBot · UXDesigner
**预计**：10-30 分钟

您可以在讨论过程中随时查看进度，
完成时会收到最终报告通知。
"""
        # await send_message(user_channel, message)
        print(f"📤 已发送开始通知")
        print(message)
    
    async def send_progress_update(self, user_channel: str, round_num: int, completed_agents: List[str]):
        """
        发送进度更新
        
        Args:
            round_num: 当前轮次
            completed_agents: 已完成的 Agent 列表
        """
        self.current_round = round_num
        progress = round_num / self.total_rounds * 100
        
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0
        estimated_remaining = (30 - elapsed) if elapsed < 30 else 0
        
        progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        
        message = f"""
📊 **RoundTable 进度更新**

**当前**：R{round_num} 轮完成（{round_num}/{self.total_rounds}）
**进度**：{progress_bar} {progress:.0f}%
**已完成**：{', '.join(completed_agents)}
**已耗时**：{elapsed:.1f} 分钟
**预计剩余**：{estimated_remaining:.0f}-{estimated_remaining + 10:.0f} 分钟

点击查看当前讨论内容 →
"""
        # await send_message(user_channel, message)
        print(f"📤 已发送进度更新（R{round_num}）")
        print(message)
    
    async def send_completion_notification(self, user_channel: str, report_url: str):
        """发送完成通知"""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0
        
        message = f"""
✅ **RoundTable 讨论完成**

**主题**：{self.topic}
**总耗时**：{elapsed:.1f} 分钟
**讨论轮次**：R1-R5（完整 5 轮）
**输出内容**：技术方案 + 安全建议 + 体验优化

📄 **查看完整报告**：
{report_url}

[打开报告] [下载 PDF] [分享给团队]
"""
        # await send_message(user_channel, message)
        print(f"📤 已发送完成通知")
        print(message)
    
    async def send_start_notification_v2(self, user_channel: str, experts: List[str], topic_count: int):
        """V2 发送开始通知"""
        self.start_time = datetime.now()
        
        expert_names = [EXPERT_PROFILES[e].name for e in experts if e in EXPERT_PROFILES]
        
        message = f"""
🚀 **RoundTable V2 已启动**

**主题**：{self.topic}
**专家阵容**：{' + '.join(expert_names)}
**关键议题**：{topic_count} 个
**状态**：讨论进行中

预计耗时：{topic_count * len(experts) * 2} 分钟

您可以随时查看进度，
完成时会收到最终报告通知。
"""
        print(f"📤 已发送 V2 开始通知")
        print(message)
    
    async def send_progress_update_v2(self, user_channel: str, current: int, total: int, topic_result):
        """V2 发送进度更新"""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0
        
        progress_bar = "█" * int(current / total * 10) + "░" * (10 - int(current / total * 10))
        
        message = f"""
📊 **RoundTable V2 进度更新**

**当前**：议题 {current}/{total} - {topic_result.topic_name}
**进度**：{progress_bar} {current/total*100:.0f}%
**已完成专家**：{len([r for r in topic_result.expert_results if r.success])}/{len(topic_result.expert_results)}
**已耗时**：{elapsed:.1f} 分钟

点击查看当前讨论内容 →
"""
        print(f"📤 已发送 V2 进度更新（议题{current}）")
        print(message)
    
    async def send_completion_notification_v2(self, user_channel: str, final_plan: str, results: Dict):
        """V2 发送完成通知"""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0
        
        topic_count = len(results)
        expert_count = sum(len(r.expert_results) for r in results.values())
        
        message = f"""
✅ **RoundTable V2 讨论完成**

**主题**：{self.topic}
**总耗时**：{elapsed:.1f} 分钟
**讨论议题**：{topic_count} 个
**参与专家**：{expert_count} 人次

**议题概览**：
{chr(10).join(['- ' + r.topic_name + ' (' + r.priority + ')' for r in results.values()])}

📄 **最终方案**：
{final_plan[:1000]}...

[查看完整报告] [下载 PDF] [分享给团队]
"""
        print(f"📤 已发送 V2 完成通知")
        print(message)
    
    async def send_timeout_warning(self, user_channel: str, round_num: int, timed_out_agents: List[str]):
        """
        发送超时警告
        
        Args:
            round_num: 当前轮次
            timed_out_agents: 超时的 Agent 列表
        """
        message = f"""
⚠️ **RoundTable 超时警告**

**当前轮次**：R{round_num}
**超时 Agent**：{', '.join(timed_out_agents)}

系统已自动重试或启用降级方案。
讨论将继续进行，最终报告可能缺少部分观点。

继续讨论 →
"""
        # await send_message(user_channel, message)
        print(f"⚠️ 已发送超时警告（R{round_num}）")


# 使用示例

    async def ask_model_config(self, user_channel: str) -> str:
        """询问用户模型配置"""
        message = f"""🎯 **RoundTable 模型配置**

您想为本次讨论配置专用模型吗？

**支持格式:**
- 单模型：`bailian/glm-5`
- 多模型：`bailian/glm-5,bailian/kimi-k2.5,bailian/qwen3.5-plus`
- 带标签：`bailian/glm-5:code,bailian/kimi-k2.5:creative`

**智能分配:**
- 工程专家 → 匹配 code/technical 标签的模型
- 设计专家 → 匹配 creative/long-context 标签的模型
- 测试专家 → 匹配 balanced/fast 标签的模型

**直接回车:** 使用 OpenClaw 默认模型

请输入模型配置（或回车跳过）："""
        
        print(f"\n{message}")
        # 由于没有用户交互，返回空字符串使用默认模型
        return ""

async def main():
    notifier = RoundTableNotifier("智能客服系统技术方案")
    
    # 1. 发送确认请求
    confirmed = await notifier.send_confirmation_request("user_channel")
    if not confirmed:
        print("用户取消 RoundTable")
        return
    
    # 2. 发送开始通知
    await notifier.send_start_notification("user_channel")
    
    # 3. 模拟讨论过程
    for round_num in range(1, 6):
        # 模拟 Agent 执行
        await asyncio.sleep(2)  # 模拟执行时间
        completed = ["DevAgent", "AIBot", "UXDesigner"]
        
        # 发送进度更新
        await notifier.send_progress_update("user_channel", round_num, completed)
    
    # 4. 发送完成通知
    await notifier.send_completion_notification(
        "user_channel", 
        "http://localhost:8080"
    )


if __name__ == "__main__":
    asyncio.run(main())

    async def ask_model_config(self, user_channel: str) -> str:
        """询问用户模型配置"""
        message = f"""🎯 **RoundTable 模型配置**

您想为本次讨论配置专用模型吗？

**支持格式:**
- 单模型：`bailian/glm-5`
- 多模型：`bailian/glm-5,bailian/kimi-k2.5,bailian/qwen3.5-plus`
- 带标签：`bailian/glm-5:code,bailian/kimi-k2.5:creative`

**智能分配:**
- 工程专家 → 匹配 code/technical 标签的模型
- 设计专家 → 匹配 creative/long-context 标签的模型
- 测试专家 → 匹配 balanced/fast 标签的模型

**直接回车:** 使用 OpenClaw 默认模型

请输入模型配置（或回车跳过）："""
        
        print(f"\n{message}")
        # 由于没有用户交互，返回空字符串使用默认模型
        return ""
