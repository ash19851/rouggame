"""门组件 —— 控制房间之间的过渡，支持挑战门、代价门和谜题门。"""

from dataclasses import dataclass, field
from src.ecs.component import Component


@dataclass
class Door(Component):
    """门组件：定义门的类型、开启代价、目标房间和激活状态。"""
    door_type: str = "challenge"  # 门类型："challenge"（挑战门）, "cost"（代价门）, "puzzle"（谜题门）
    cost_type: str = ""  # 代价类型："hp"（生命值）, "key"（钥匙）
    cost_value: int = 0  # 代价值（生命值扣除量或所需钥匙数）
    target_room: int = -1  # 目标房间编号，-1 表示无目标
    active: bool = False  # 是否已激活（当前房间清理后激活）
