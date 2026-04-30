"""装备 HUD —— 在屏幕右下角显示已装备的物品、攻击模式和提示。"""

import pygame
from src.data.equipment_defs import RARITY_COLORS, SLOT_LABELS
from src.ui.text_renderer import draw_text, draw_text_right
from src.graphics.sprite_atlas import get_sprite


# 攻击模式对应的显示名称
PATTERN_LABELS = {
    "normal": "普通",
    "scatter": "散射",
    "orbital": "环绕",
    "wave": "波纹",
    "impact_scatter": "冲击",
}


def draw_equipment_hud(surface: pygame.Surface, items: dict[str, dict],
                       virtual_w: int, virtual_h: int,
                       pattern: str = ""):
    """在右下角绘制装备 HUD（武器、护甲、饰品），右对齐。

    参数:
        surface: 渲染目标 surface
        items: 装备字典，key 为槽位名（weapon/armor/accessory）
        virtual_w, virtual_h: 虚拟分辨率
        pattern: 当前攻击模式标识
    """
    slots = ["weapon", "armor", "accessory"]
    x = virtual_w - 10
    y = virtual_h - 50

    for slot in slots:
        item = items.get(slot)
        label = SLOT_LABELS.get(slot, "?")
        if item:
            color = RARITY_COLORS.get(item["rarity"], (200, 200, 200))
            text = f"[{label}] {item['name']}"
            # 如果物品有图标精灵，在文字左侧绘制图标
            icon_name = item.get("icon_sprite", "")
            if icon_name:
                icon_surf = get_sprite(icon_name)
                if icon_surf:
                    text_w = len(text) * 6  # 粗略估算文字宽度
                    surface.blit(icon_surf, (int(x - text_w - 14), int(y)))
        else:
            color = (80, 80, 80)
            text = f"[{label}] ---"
        draw_text_right(surface, text, x, y, size=10, color=color)
        y += 14

    # 攻击模式指示器
    if pattern:
        pattern_key = f"pattern_{pattern}"
        pattern_icon = get_sprite(pattern_key)
        if pattern_icon:
            label = PATTERN_LABELS.get(pattern, pattern)
            draw_text_right(surface, f"模式: {label}", x, y, size=9, color=(160, 160, 200))
            surface.blit(pattern_icon, (x - 80, int(y)))
            y += 12

    # 背包快捷键提示
    draw_text_right(surface, "[Tab] 背包", x, y + 2, size=9, color=(100, 100, 120))


def draw_equipment_toast(surface: pygame.Surface, text: str, color: tuple[int, int, int],
                         alpha: float, virtual_w: int, virtual_h: int):
    """在屏幕底部中央显示装备拾取提示（带透明度渐变）。

    参数:
        surface: 渲染目标
        text: 提示文字
        color: 文字 RGB 颜色
        alpha: 透明度系数（1.0=完全不透明，0.0=完全透明）
        virtual_w, virtual_h: 虚拟分辨率
    """
    if alpha <= 0:
        return
    r, g, b = color
    c = (int(r * alpha), int(g * alpha), int(b * alpha))
    draw_text(surface, text, virtual_w / 2, virtual_h - 60,
              size=12, color=c, center=True)
