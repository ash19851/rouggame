"""升级卡片组件 —— 升级时显示可选属性加成卡片，支持悬浮高亮和点击选择。"""

import pygame
from src.ui.text_renderer import draw_text


class UpgradeCard:
    """升级选择卡片：显示属性名称、描述，点击后应用对应加成。"""

    WIDTH = 110
    HEIGHT = 60
    GAP = 8

    def __init__(self, label: str, description: str, stat_key: str, x: float, y: float):
        """初始化升级卡片。

        参数:
            label: 属性名（如 "+20 Max HP"）
            description: 描述文本（如 "Increase max health"）
            stat_key: 对应的属性键名
            x, y: 卡片中心坐标
        """
        self.label = label
        self.description = description
        self.stat_key = stat_key
        self.rect = pygame.Rect(x - self.WIDTH / 2, y - self.HEIGHT / 2, self.WIDTH, self.HEIGHT)
        self._hovered = False

    def handle_event(self, event: pygame.event.Event):
        """处理鼠标移动事件，检测悬浮。"""
        if event.type == pygame.MOUSEMOTION:
            from src.core.engine import screen_to_virtual
            mx, my = screen_to_virtual(*event.pos)
            self._hovered = self.rect.collidepoint(mx, my)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """检测是否鼠标左键点击了此卡片。"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            from src.core.engine import screen_to_virtual
            mx, my = screen_to_virtual(*event.pos)
            return self.rect.collidepoint(mx, my)
        return False

    def render(self, surface: pygame.Surface):
        """渲染卡片：悬浮时更亮，包含圆角矩形背景、边框和文字。"""
        bg_color = (50, 50, 90) if self._hovered else (35, 35, 60)
        border_color = (120, 120, 200) if self._hovered else (70, 70, 110)
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=6)

        draw_text(surface, self.label, self.rect.centerx, self.rect.centery - 10,
                  size=18, center=True, shadow=True)
        draw_text(surface, self.description, self.rect.centerx, self.rect.centery + 14,
                  size=12, color=(180, 180, 200), center=True)
