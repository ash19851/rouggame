"""变换组件 —— 存储实体在世界空间中的位置坐标。"""

from dataclasses import dataclass
from src.ecs.component import Component


@dataclass
class Transform(Component):
    """变换组件：定义实体在世界中的 X、Y 坐标，是所有实体必备的基础组件。"""
    x: float = 0.0  # 世界 X 坐标（像素）
    y: float = 0.0  # 世界 Y 坐标（像素）
