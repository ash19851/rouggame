"""小地图组件 —— 在屏幕右上角绘制 80px 宽的缩略地图。"""

import pygame
from src.world.tile import Tile


def render_minimap(surface: pygame.Surface, tilemap, player_pos: tuple[float, float] | None,
                   enemy_positions: list[tuple[float, float]], doors_open: bool,
                   vw: int, vh: int):
    """在屏幕右上角绘制 80px 宽的小地图，显示房间布局、玩家和敌人位置。

    参数:
        surface: 渲染目标
        tilemap: 房间瓦片地图对象
        player_pos: 玩家世界坐标 (x, y) 或 None
        enemy_positions: 所有敌人的世界坐标列表
        doors_open: 门是否已打开
        vw, vh: 虚拟屏幕宽高
    """
    if tilemap is None:
        return

    tw, th = tilemap.width, tilemap.height

    # 逐像素构建小地图源面（每个瓦片 1px）
    mm_surf = pygame.Surface((tw, th))
    for ty in range(th):
        for tx in range(tw):
            tile = tilemap.grid[ty][tx]
            if tile == Tile.WALL:
                color = (70, 70, 90)          # 墙壁: 灰蓝色
            elif tile == Tile.OBSTACLE:
                color = (90, 70, 50)          # 障碍物: 棕色
            elif tile == Tile.DOOR:
                color = (80, 180, 50) if doors_open else (130, 100, 40)  # 门: 绿/棕色
            elif tile == Tile.TRAP:
                color = (160, 35, 25)         # 陷阱: 深红色
            else:
                color = (18, 18, 28)          # 地面: 深色
            mm_surf.set_at((tx, ty), color)

    # 缩放到 80px 宽，保持宽高比
    mm_w = 80
    mm_h = max(1, int(mm_w * th / tw))
    scaled = pygame.transform.scale(mm_surf, (mm_w, mm_h))

    # 定位到右上角（10px 边距）
    mm_x = vw - mm_w - 10
    mm_y = 10

    surface.blit(scaled, (mm_x, mm_y))

    # 玩家标记点（蓝色圆点）
    if player_pos and tilemap.tile_size > 0:
        px = player_pos[0] / tilemap.tile_size
        py = player_pos[1] / tilemap.tile_size
        dot_x = mm_x + int(px * mm_w / tw)
        dot_y = mm_y + int(py * mm_h / th)
        pygame.draw.circle(surface, (80, 160, 255), (dot_x, dot_y), 2)

    # 敌人标记点（红色小圆点）
    for ex, ey in enemy_positions:
        epx = ex / tilemap.tile_size
        epy = ey / tilemap.tile_size
        dot_x = mm_x + int(epx * mm_w / tw)
        dot_y = mm_y + int(epy * mm_h / th)
        pygame.draw.circle(surface, (255, 80, 60), (dot_x, dot_y), 1)

    # 小地图边框
    pygame.draw.rect(surface, (60, 60, 80), (mm_x - 1, mm_y - 1, mm_w + 2, mm_h + 2), 1)
