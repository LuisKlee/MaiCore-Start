"""
多Bot管理模块
支持多个机器人实例的同时运行和管理
"""

from .multi_bot_manager import MultiBotManager
from .bot_instance import BotInstance
from .bot_group import BotGroup
from .local_bot_takeover import LocalBotDetector, LocalBotTakeover
from .local_bot_takeover_ui import LocalBotTakeoverUI
from .port_manager import PortAllocator, BotPortManager, port_allocator
from .port_manager_ui import PortManagerUI

__all__ = [
    "MultiBotManager",
    "BotInstance",
    "BotGroup",
    "LocalBotDetector",
    "LocalBotTakeover",
    "LocalBotTakeoverUI",
    "PortAllocator",
    "BotPortManager",
    "port_allocator",
    "PortManagerUI"
]
