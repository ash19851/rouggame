"""升级组件 —— 定义可升级属性的名称、数值和等级。"""

from dataclasses import dataclass
from src.ecs.component import Component


@dataclass
class Upgrade(Component):
    """升级组件：表示一个属性升级，指定升级的属性名、数值和当前等级。"""
    stat: str = ""  # 升级属性名："max_hp"（最大生命）, "attack_speed"（攻击速度）, "move_speed"（移动速度）, "damage"（伤害）
    amount: float = 0.0  # 升级数值增量
    tier: int = 1  # 当前升级等级
