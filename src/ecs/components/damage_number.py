"""伤害数字组件 —— 浮空战斗文字效果（暴击金色大字，普通白色小字）。"""

from dataclasses import dataclass
from src.ecs.component import Component


@dataclass
class DamageNumber(Component):
    """浮空伤害数字组件：上浮 + 淡出 + 弹出缩放效果。"""
    text: str = ""
    color: tuple[int, int, int] = (255, 255, 255)
    lifetime: float = 0.8
    age: float = 0.0
    float_speed: float = -45.0
    font_size: int = 12
    is_crit: bool = False
