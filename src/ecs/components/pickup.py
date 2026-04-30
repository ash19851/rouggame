"""可拾取物组件 —— 定义掉落的经验值、生命值或装备物品的属性。"""

from dataclasses import dataclass
from src.ecs.component import Component


@dataclass
class Pickup(Component):
    """可拾取物组件：定义拾取物的类型、数值、磁吸范围和装备标识。"""
    pickup_type: str = "xp"  # 拾取类型："xp"（经验值）, "health"（生命值）, "equipment"（装备）
    value: int = 1  # 拾取数值（经验量或生命恢复量）
    magnet_range: float = 30.0  # 磁吸范围（像素），玩家靠近时自动吸引
    equipment_id: str = ""  # 装备 ID（装备类拾取物时非空）
