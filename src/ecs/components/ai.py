"""AI（人工智能）组件 —— 控制敌人的行为模式和战斗策略。"""

from dataclasses import dataclass, field
from src.ecs.component import Component


@dataclass
class AI(Component):
    """敌人 AI 组件：定义敌人的行为模式、攻击范围、冲刺和远程战斗参数。"""
    mode: str = "chase"  # 行为模式："chase"（追击）, "patrol"（巡逻）, "idle"（待机）, "ranged"（远程）, "dash"（冲刺）
    aggro_range: float = 200.0  # 仇恨范围（像素）
    attack_range: float = 30.0  # 攻击范围（像素）
    patrol_timer: float = 0.0  # 巡逻计时器（秒）
    patrol_dir_x: float = 0.0  # 巡逻方向 X 分量
    patrol_dir_y: float = 0.0  # 巡逻方向 Y 分量
    # Dash（冲刺）
    dash_cooldown: float = 3.0  # 冲刺冷却时间（秒）
    dash_timer: float = 0.0  # 冲刺计时器（秒）
    dash_speed_mult: float = 3.0  # 冲刺速度倍率
    dash_duration: float = 0.3  # 冲刺持续时间（秒）
    dash_dir_x: float = 0.0  # 冲刺方向 X 分量
    dash_dir_y: float = 0.0  # 冲刺方向 Y 分量
    # Ranged（远程）
    preferred_range: float = 150.0  # 远程战斗首选距离（像素）
    # Burst on death（死亡爆发）
    burst_damage: int = 0  # 死亡时爆发伤害
    burst_radius: float = 0.0  # 死亡爆发范围（像素）
