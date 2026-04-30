"""波形运动组件 —— 使投射物沿前进方向作正弦波轨迹飞行。"""

from dataclasses import dataclass, field
from src.ecs.component import Component


@dataclass
class WaveMotion(Component):
    """波形运动组件：定义投射物沿指定方向以正弦波方式飞行的参数。"""
    dir_x: float = 0.0  # 前进方向 X 分量
    dir_y: float = 0.0  # 前进方向 Y 分量
    speed: float = 500.0  # 前进速度（像素/秒）
    amplitude: float = 15.0  # 波形振幅（峰值到峰值的像素距离）
    frequency: float = 8.0    # 波形频率（Hz，每秒振荡次数）
    elapsed: float = 0.0       # 自创建以来经过的时间（秒）
