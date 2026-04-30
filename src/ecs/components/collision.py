"""碰撞体组件 —— 为实体提供碰撞检测的边界框和层级信息。"""

from dataclasses import dataclass
from src.ecs.component import Component


@dataclass
class Collider(Component):
    """碰撞体组件：定义实体的碰撞矩形大小和碰撞层级，用于碰撞检测系统。"""
    width: float = 16.0  # 碰撞体宽度（像素）
    height: float = 16.0  # 碰撞体高度（像素）
    layer: int = 0  # 碰撞层级：0=玩家, 1=敌人, 2=投射物, 3=可拾取物
