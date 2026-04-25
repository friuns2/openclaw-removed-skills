"""
Auto-Coding Skill - Nanobot 版

自主编程系统 - 分析需求、找方法、自我反思、迭代优化，达到交付标准
"""

from .worker import AutoCodingWorker, WorkMode, auto_code
from .self_reflect import SelfReflector, ReflectDepth, reflect
from .delivery_check import DeliveryChecker, CheckStatus, check_delivery

__version__ = "1.0.0"
__author__ = "Krislu + nanobot"
__all__ = [
    "AutoCodingWorker",
    "WorkMode",
    "auto_code",
    "SelfReflector",
    "ReflectDepth",
    "reflect",
    "DeliveryChecker",
    "CheckStatus",
    "check_delivery"
]
