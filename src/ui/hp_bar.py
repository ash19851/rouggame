"""HP 生命条组件 —— 渐变色彩的血量显示条。"""

import pygame


def draw_hp_bar(surface: pygame.Surface, x: float, y: float, width: int, height: int,
                current: int, maximum: int):
    """绘制渐变血条（从红色渐变到绿色，表示血量百分比）。

    参数:
        surface: 渲染目标
        x, y: 血条左上角坐标
        width, height: 血条宽高
        current: 当前生命值
        maximum: 最大生命值
    """
    # 背景暗红色底
    bg = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (40, 15, 15), bg)
    pygame.draw.rect(surface, (80, 40, 40), bg, 1)

    # 血量填充 —— 从红色(低血)到绿色(满血)渐变
    if maximum > 0:
        fill_w = int(width * current / maximum)
        fill = pygame.Rect(x, y, fill_w, height)
        ratio = current / maximum
        # ratio 越小越红，越大越绿
        color = (int(200 * (1 - ratio)), int(200 * ratio), 40)
        pygame.draw.rect(surface, color, fill)
