"""战斗组件 —— 定义实体的攻击属性，包括伤害、攻速、射程和投射物参数。"""

from dataclasses import dataclass, field
from src.ecs.component import Component


@dataclass
class Combat(Component):
    """战斗组件：存储实体的攻击伤害、攻击速度、射程和投射物相关配置。"""
    damage: int = 10  # 攻击伤害值
    attack_speed: float = 0.5  # 攻击速度（每秒攻击次数）
    range: float = 200.0  # 攻击射程（像素）
    cooldown: float = 0.0  # 剩余冷却时间（秒），为 0 时可以攻击
    projectile_speed: float = 300.0  # 投射物飞行速度（像素/秒）
    projectile_size: float = 6.0  # 投射物大小（像素）
    projectile_color: tuple[int, int, int] = (255, 255, 100)  # 投射物颜色 (R, G, B)
