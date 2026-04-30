"""
瓦片地图模块。

管理二维瓦片网格数据，负责等轴测渲染所有瓦片类型。
支持地板、墙壁（3D 块）、障碍物、门（含开关动画）和陷阱的可视化。
"""

import math
import pygame
from src.world.tile import Tile
from src.core.isometric import world_to_iso, get_screen_center

# 各瓦片类型的渲染颜色
WALL_COLOR = (60, 60, 80)
FLOOR_COLOR = (25, 25, 35)
DOOR_COLOR = (100, 80, 40)
OBSTACLE_COLOR = (50, 40, 40)

TILE_SIZE = 32           # 瓦片宽度（世界空间像素）
WALL_HEIGHT = 16         # 墙壁 3D 块在等轴测空间的视觉高度
OBSTACLE_HEIGHT = 10     # 障碍物 3D 块的视觉高度


def _darken(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    """按比例变暗颜色，用于 3D 块侧面的明暗效果。"""
    return tuple(max(0, min(255, int(c * factor))) for c in color)


class Tilemap:
    """二维瓦片地图，存储瓦片网格并支持等轴测渲染。

    世界坐标与瓦片坐标的换算：
      瓦片坐标 = 世界坐标 / tile_size
    """

    def __init__(self, width: int, height: int, tile_size: int = TILE_SIZE):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        # grid[row][col]，即 grid[ty][tx]
        self.grid: list[list[Tile]] = [
            [Tile.FLOOR for _ in range(width)]
            for _ in range(height)
        ]

    def get(self, tx: int, ty: int) -> Tile:
        """获取瓦片坐标 (tx, ty) 处的瓦片类型。越界返回 WALL。"""
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.grid[ty][tx]
        return Tile.WALL

    def set(self, tx: int, ty: int, tile: Tile):
        """设置瓦片坐标 (tx, ty) 处的瓦片类型。越界忽略。"""
        if 0 <= tx < self.width and 0 <= ty < self.height:
            self.grid[ty][tx] = tile

    def is_wall(self, tx: int, ty: int) -> bool:
        """判断该瓦片是否不可行走（墙壁或障碍物）。"""
        return not self.get(tx, ty).is_walkable

    def world_to_tile(self, wx: float, wy: float) -> tuple[int, int]:
        """将世界坐标转换为瓦片坐标。"""
        return int(wx / self.tile_size), int(wy / self.tile_size)

    def tile_to_world_center(self, tx: int, ty: int) -> tuple[float, float]:
        """返回瓦片中心的世界坐标。"""
        return tx * self.tile_size + self.tile_size / 2, ty * self.tile_size + self.tile_size / 2

    def _tile_corners_iso(self, tx: int, ty: int, ox: float, oy: float,
                          height_offset: float = 0.0
                          ) -> list[tuple[float, float]]:
        """计算瓦片四个角在等轴测屏幕空间中的坐标。

        顺序：左上、右上、右下、左下（菱形顺时针）。
        height_offset 负值会将顶点向上偏移（渲染 3D 高度效果）。
        """
        cx, cy = get_screen_center()
        ts = self.tile_size
        # 四个角的世界坐标
        corners = [
            (tx * ts,      ty * ts),       # TL：左上
            (tx * ts + ts, ty * ts),       # TR：右上
            (tx * ts + ts, ty * ts + ts),  # BR：右下
            (tx * ts,      ty * ts + ts),  # BL：左下
        ]
        iso_pts = []
        for wx, wy in corners:
            ix, iy = world_to_iso(wx, wy, ox, oy, cx, cy)
            iso_pts.append((ix, iy - height_offset))
        return iso_pts

    def _tile_center_iso(self, tx: int, ty: int, ox: float, oy: float) -> tuple[float, float]:
        """计算瓦片中心在等轴测屏幕空间中的坐标。"""
        cx, cy = get_screen_center()
        ts = self.tile_size
        wx = tx * ts + ts / 2
        wy = ty * ts + ts / 2
        return world_to_iso(wx, wy, ox, oy, cx, cy)

    def _draw_block(self, surface: pygame.Surface, tx: int, ty: int,
                    ox: float, oy: float, color: tuple[int, int, int], height: float):
        """绘制 3D 方块（墙壁/障碍物），包含明暗面。

        三个面：左边面（暗）、右边面（中亮）、顶面（原色菱形）。
        """
        f = self._tile_corners_iso(tx, ty, ox, oy, 0)       # 底面（地板高度）
        t = self._tile_corners_iso(tx, ty, ox, oy, height)  # 顶面（3D 高度）

        # 左面（暗色调）：左上顶 -> 左下顶 -> 左下底 -> 左上底
        left_color = _darken(color, 0.55)
        # 右面（中等色调）
        right_color = _darken(color, 0.75)

        pygame.draw.polygon(surface, left_color, [t[0], t[3], f[3], f[0]])
        pygame.draw.polygon(surface, right_color, [t[1], t[2], f[2], f[1]])
        # 顶面（菱形，保持原色）
        pygame.draw.polygon(surface, color, t)

    def _draw_floor_diamond(self, surface: pygame.Surface, tx: int, ty: int,
                            ox: float, oy: float, color: tuple[int, int, int]):
        """绘制平面菱形（地板）。"""
        pts = self._tile_corners_iso(tx, ty, ox, oy, 0)
        pygame.draw.polygon(surface, color, pts)

    def render(self, surface: pygame.Surface, camera_offset: tuple[float, float],
               doors_open: bool = False):
        """渲染可见范围内的所有瓦片。

        使用视锥裁剪（frustum culling），只渲染屏幕可见区域的瓦片，
        提升大房间的渲染性能。门开启时带有呼吸灯脉冲动画。
        """
        ox, oy = camera_offset
        ts = self.tile_size

        # 增大裁剪边距，因为菱形瓦片比矩形更宽
        margin = int(ts * 2.0)
        start_tx = max(0, int((ox - margin) / ts))
        start_ty = max(0, int((oy - margin) / ts))
        end_tx = min(self.width, int((ox + surface.get_width() + margin) / ts) + 2)
        end_ty = min(self.height, int((oy + surface.get_height() + margin) / ts) + 2)

        # 行优先遍历（y 外层，x 内层），等轴测视角按此顺序自然获得正确遮挡
        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                tile = self.grid[ty][tx]

                if tile == Tile.FLOOR:
                    self._draw_floor_diamond(surface, tx, ty, ox, oy, FLOOR_COLOR)
                elif tile == Tile.WALL:
                    self._draw_block(surface, tx, ty, ox, oy, WALL_COLOR, WALL_HEIGHT)
                elif tile == Tile.OBSTACLE:
                    self._draw_block(surface, tx, ty, ox, oy, OBSTACLE_COLOR, OBSTACLE_HEIGHT)
                elif tile == Tile.DOOR:
                    if doors_open:
                        # 开门时显示脉冲动画（呼吸灯效果）
                        pulse = 0.6 + 0.4 * math.sin(pygame.time.get_ticks() / 400)
                        color = (int(100 * pulse), int(200 * pulse), int(60 * pulse))
                        self._draw_floor_diamond(surface, tx, ty, ox, oy, color)
                    else:
                        self._draw_block(surface, tx, ty, ox, oy, DOOR_COLOR, WALL_HEIGHT)
                elif tile == Tile.TRAP:
                    # 陷阱：深红色地板 + 中央尖刺标记
                    self._draw_floor_diamond(surface, tx, ty, ox, oy, (50, 20, 20))
                    cx, cy = self._tile_center_iso(tx, ty, ox, oy)
                    spike_color = (200, 60, 50)
                    pygame.draw.circle(surface, spike_color, (int(cx), int(cy)), 3, 1)

    def fill_border_walls(self):
        """将地图四条边填充为墙壁。"""
        for x in range(self.width):
            self.grid[0][x] = Tile.WALL
            self.grid[self.height - 1][x] = Tile.WALL
        for y in range(self.height):
            self.grid[y][0] = Tile.WALL
            self.grid[y][self.width - 1] = Tile.WALL

    def create_simple_room(self):
        """快速创建一个简单房间：边界墙壁 + 内部地板 + 几个散布柱子。"""
        self.fill_border_walls()
        import random
        for _ in range(4):
            px = random.randint(5, self.width - 6)
            py = random.randint(3, self.height - 4)
            self.grid[py][px] = Tile.OBSTACLE
