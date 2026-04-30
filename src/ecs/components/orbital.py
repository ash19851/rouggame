"""环绕投射物组件 —— 使投射物围绕中心点旋转飞行。"""

from dataclasses import dataclass, field
from src.ecs.component import Component


@dataclass
class Orbital(Component):
    """环绕投射物组件：定义投射物围绕某个实体或中心点作圆周运动的参数。"""
    center_x: float = 0.0  # 环绕中心 X 坐标
    center_y: float = 0.0  # 环绕中心 Y 坐标
    radius: float = 40.0  # 环绕半径（像素）
    angle: float = 0.0          # 当前角度（弧度）
    angular_speed: float = 4.0  # 角速度（弧度/秒）
    lifetime: float = 3.0       # 剩余存在时间（秒）
    damage: int = 0  # 碰撞伤害
    source_eid: int = 0         # 环绕的源实体 ID
