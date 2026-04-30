"""经验条组件 —— 蓝色填充条显示当前经验与升级所需经验的比值，左侧标注等级。"""

import pygame


def draw_xp_bar(surface: pygame.Surface, x: float, y: float, width: int, height: int,
                current: int, needed: int, level: int):
    """绘制经验进度条。

    参数:
        surface: 渲染目标
        x, y: 经验条左上角坐标
        width, height: 经验条宽高
        current: 当前经验值
        needed: 升级所需经验值
        level: 当前等级
    """
    # 深蓝色背景底
    bg = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (15, 20, 40), bg)
    pygame.draw.rect(surface, (40, 60, 100), bg, 1)

    # 蓝色经验填充
    if needed > 0:
        fill_w = int(width * current / needed)
        fill = pygame.Rect(x, y, fill_w, height)
        pygame.draw.rect(surface, (80, 180, 255), fill)

    # 等级文字（显示在经验条左侧）
    from src.ui.text_renderer import draw_text
    draw_text(surface, f"Lv.{level}", x - 32, y - 1, size=14, color=(180, 220, 255))
