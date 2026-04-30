"""渲染组件 —— 定义实体的精灵图像、颜色、大小和渲染层级。"""

from dataclasses import dataclass
import pygame
from src.ecs.component import Component


@dataclass
class Sprite(Component):
    """精灵渲染组件：控制实体的可视化外观，包括表面图像、颜色、尺寸、层级和可见性。"""
    surface: pygame.Surface | None = None  # Pygame 表面（精灵图像），None 时使用纯色矩形
    color: tuple[int, int, int] = (255, 255, 255)  # 实体颜色 (R, G, B)
    width: int = 16  # 渲染宽度（像素）
    height: int = 16  # 渲染高度（像素）
    layer: int = 0  # 渲染层级（数值越大越靠前）
    visible: bool = True  # 是否可见
