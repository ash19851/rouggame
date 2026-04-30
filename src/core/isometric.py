"""
等轴测投影工具模块。

所有游戏逻辑在二维世界空间中运行，本模块负责在渲染时将世界坐标
与等轴测屏幕坐标相互转换。使用 2:1 像素艺术的等轴测比例（宽高比 2:1）。
"""

from src.core.engine import VIRTUAL_W, VIRTUAL_H

# 2:1 等轴测像素比例（宽:高 = 2:1）
ISO_SCALE_X = 1.0
ISO_SCALE_Y = 0.5


def world_to_iso(wx: float, wy: float, cam_x: float, cam_y: float,
                 center_x: float | None = None, center_y: float | None = None
                 ) -> tuple[float, float]:
    """将世界坐标转换为等轴测屏幕坐标。

    cam_x/cam_y 应为显示在屏幕中心的世界空间坐标点。

    转换公式（反向旋转 45 度 + 垂直压缩）：
      iso_x = (wx - wy) * ISO_SCALE_X + center_x
      iso_y = (wx + wy) * ISO_SCALE_Y + center_y
    """
    if center_x is None:
        center_x = VIRTUAL_W / 2
    if center_y is None:
        center_y = VIRTUAL_H / 2

    # 相对于相机的位置
    rx = wx - cam_x
    ry = wy - cam_y

    # 应用等轴测投影
    iso_x = (rx - ry) * ISO_SCALE_X + center_x
    iso_y = (rx + ry) * ISO_SCALE_Y + center_y
    return iso_x, iso_y


def iso_to_world(sx: float, sy: float, cam_x: float, cam_y: float,
                 center_x: float | None = None, center_y: float | None = None
                 ) -> tuple[float, float]:
    """将等轴测屏幕坐标反算回世界坐标（逆向投影）。

    逆向公式：
      wx = (ix + iy) / 2 + cam_x
      wy = (iy - ix) / 2 + cam_y
    """
    if center_x is None:
        center_x = VIRTUAL_W / 2
    if center_y is None:
        center_y = VIRTUAL_H / 2

    ix = (sx - center_x) / ISO_SCALE_X   # 还原：rx - ry
    iy = (sy - center_y) / ISO_SCALE_Y   # 还原：rx + ry

    wx = (ix + iy) / 2 + cam_x
    wy = (iy - ix) / 2 + cam_y
    return wx, wy


def iso_depth(wx: float, wy: float) -> float:
    """等轴测渲染的深度排序键。值越大越靠近相机（越靠前绘制）。"""
    return wx + wy


def get_screen_center() -> tuple[float, float]:
    """返回虚拟表面的中心坐标，用于等轴测投影的屏幕原点。"""
    return VIRTUAL_W / 2, VIRTUAL_H / 2
