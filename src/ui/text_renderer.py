"""文字渲染器 —— 自动检测 CJK 字体，支持居中、右对齐、阴影等绘制模式。"""

import os
import pygame

_font_cache: dict[tuple, pygame.font.Font] = {}


def _find_cjk_font(size: int) -> pygame.font.Font | None:
    """尝试查找支持中文渲染的系统字体。

    通过测试汉字"中"能否正常渲染来判断字体是否支持 CJK。

    查找顺序:
        1. 尝试系统已安装的常见中文字体名称列表
        2. 尝试 Windows/Linux 特定路径下的 .ttc/.ttf 字体文件
    """
    test_char = "中"  # 测试用汉字，验证字体是否支持中文

    # 先尝试系统字体名称列表
    for font_name in ["Microsoft YaHei", "SimHei", "SimSun", "KaiTi",
                       "Microsoft JhengHei", "FangSong",
                       "Noto Sans CJK SC", "WenQuanYi Micro Hei",
                       "Noto Sans SC", "PingFang SC", "Heiti SC", "STHeiti"]:
        try:
            font = pygame.font.SysFont(font_name, size)
            if font.size(test_char)[0] > 0:
                return font
        except Exception:
            pass

    # 再尝试直接加载字体文件（Windows / Linux 路径）
    font_paths = [
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "msyh.ttc"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "msyhbd.ttc"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "simhei.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = pygame.font.Font(path, size)
                if font.size(test_char)[0] > 0:
                    return font
            except Exception:
                pass

    return None


def get_font(size: int) -> pygame.font.Font:
    """获取指定大小的字体对象，优先使用 CJK 字体，缓存查找结果。"""
    key = (size,)
    if key not in _font_cache:
        cjk = _find_cjk_font(size)
        if cjk is not None:
            _font_cache[key] = cjk
        else:
            _font_cache[key] = pygame.font.Font(None, size)  # 回退到默认字体
    return _font_cache[key]


def draw_text(surface: pygame.Surface, text: str, x: float, y: float, size: int = 20,
              color: tuple[int, int, int] = (255, 255, 255), center: bool = False,
              shadow: bool = False):
    """在 surface 上绘制文字。

    参数:
        surface: 渲染目标
        text: 要绘制的文字
        x, y: 绘制位置（center=True 时为中心点，否则为左上角）
        size: 字号
        color: 文字颜色
        center: 是否居中绘制
        shadow: 是否绘制黑色阴影（偏移 1px）
    """
    font = get_font(size)
    if shadow:
        shadow_surf = font.render(text, True, (0, 0, 0))
        if center:
            r = shadow_surf.get_rect(center=(x + 1, y + 1))  # 阴影偏移 1px
            surface.blit(shadow_surf, r)
        else:
            surface.blit(shadow_surf, (x + 1, y + 1))
    text_surf = font.render(text, True, color)
    if center:
        r = text_surf.get_rect(center=(x, y))
        surface.blit(text_surf, r)
    else:
        surface.blit(text_surf, (x, y))


def draw_text_right(surface: pygame.Surface, text: str, x: float, y: float, size: int = 20,
                    color: tuple[int, int, int] = (255, 255, 255)):
    """右对齐绘制文字——x, y 为右上角锚点。"""
    font = get_font(size)
    text_surf = font.render(text, True, color)
    r = text_surf.get_rect(topright=(x, y))
    surface.blit(text_surf, r)
