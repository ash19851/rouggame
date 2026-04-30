"""陷阱组件 —— 定义陷阱实体的类型、伤害和冷却参数。"""

from dataclasses import dataclass
from src.ecs.component import Component


@dataclass
class TrapComponent(Component):
    """陷阱组件：用于表示伤害、减速或中毒陷阱实体，支持冷却和触发逻辑。"""
    trap_type: str = "damage"  # 陷阱类型："damage"（伤害）, "slow"（减速）, "poison"（中毒）
    damage: int = 10  # 陷阱伤害值
    slow_pct: float = 0.5  # 减速百分比（0.0 ~ 1.0）
    slow_duration: float = 2.0  # 减速持续时间（秒）
    poison_damage: int = 3  # 中毒每次伤害值
    poison_ticks: int = 5  # 中毒触发次数
    armed: bool = True  # 陷阱是否已激活（可触发）
    cooldown: float = 3.0  # 触发冷却时间（秒）
    cooldown_timer: float = 0.0  # 冷却计时器（秒），为 0 时可再次触发
