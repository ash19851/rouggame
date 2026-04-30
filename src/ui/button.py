"""UI 按钮组件 —— 支持悬浮变色和点击检测。"""

import pygame
from src.ui.text_renderer import draw_text


class Button:
    """可点击的矩形按钮，支持悬浮高亮和文字居中显示。"""

    def __init__(self, text: str, x: float, y: float, width: float, height: float,
                 font_size: int = 20, color: tuple = (60, 60, 120), hover_color: tuple = (80, 80, 160)):
        """初始化按钮。

        参数:
            text: 按钮文字
            x, y: 按钮中心坐标
            width, height: 按钮宽高
            font_size: 文字大小
            color: 默认背景色
            hover_color: 鼠标悬浮时的背景色
        """
        self.text = text
        self.rect = pygame.Rect(x - width / 2, y - height / 2, width, height)
        self.font_size = font_size
        self.color = color
        self.hover_color = hover_color
        self._hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理鼠标移动事件，更新悬浮状态。"""
        if event.type == pygame.MOUSEMOTION:
            from src.core.engine import screen_to_virtual
            mx, my = screen_to_virtual(*event.pos)
            self._hovered = self.rect.collidepoint(mx, my)
        return False

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """检测鼠标左键是否点击了该按钮。"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            from src.core.engine import screen_to_virtual
            mx, my = screen_to_virtual(*event.pos)
            return self.rect.collidepoint(mx, my)
        return False

    def render(self, surface: pygame.Surface):
        """渲染按钮到目标 surface。"""
        color = self.hover_color if self._hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=4)          # 按钮背景
        pygame.draw.rect(surface, (100, 100, 180), self.rect, 2, border_radius=4)  # 边框
        draw_text(surface, self.text, self.rect.centerx, self.rect.centery,
                  size=self.font_size, center=True, shadow=True)
