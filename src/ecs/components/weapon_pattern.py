"""武器模式组件 —— 定义装备武器赋予的攻击模式和弹幕参数。"""

from dataclasses import dataclass, field
from src.ecs.component import Component


@dataclass
class WeaponPattern(Component):
    """武器模式组件：存储当前武器的攻击模式类型及各模式的相关参数。"""
    pattern: str = "normal"       # 攻击模式：normal（普通）| scatter（散射）| impact_scatter（撞击散射）| orbital（环绕）| wave（波形）
    # Scatter（散射）参数
    spread_count: int = 3         # 散射投射物数量
    spread_angle: float = 15.0    # 散射扇面半角（度）
    # Impact-scatter（撞击散射）参数
    frag_count: int = 4           # 撞击时产生的碎片数量
    # Orbital（环绕）参数
    orbital_radius: float = 40.0  # 环绕半径（像素）
    orbital_speed: float = 4.0    # 环绕角速度（弧度/秒）
    orbital_max: int = 5          # 最大环绕投射物数量
    orbital_lifetime: float = 3.0 # 每个环绕投射物的存活时间（秒）
    # Wave（波形）参数
    wave_amplitude: float = 15.0  # 波形振幅（像素，峰到峰）
    wave_frequency: float = 8.0   # 波形频率（Hz，每秒振荡次数）
