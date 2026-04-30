"""运动组件 —— 存储实体的移动速度和当前速度向量。"""

from dataclasses import dataclass
from src.ecs.component import Component


@dataclass
class Motion(Component):
    """运动组件：定义实体的速度标量和 X/Y 方向的速度分量。"""
    vx: float = 0.0  # X 轴速度（像素/秒）
    vy: float = 0.0  # Y 轴速度（像素/秒）
    speed: float = 0.0  # 基础移动速度（像素/秒）
