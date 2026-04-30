"""碰撞系统 — 处理实体与瓦片地图之间的物理碰撞，将实体推出阻挡瓦片。

支持碰撞类型:
  - WALL / OBSTACLE: 始终阻挡
  - DOOR: 门开启状态下不阻挡
  - 子弹命中墙壁后自动销毁
"""

from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.collision import Collider
from src.ecs.components.combat import Combat
from src.ecs.components.health import Health
from src.ecs.components.player import Player
from src.world.tilemap import Tilemap
from src.world.tile import Tile


class CollisionSystem(System):
    """碰撞系统：检查实体与瓦片地图的碰撞，将实体推出墙壁，并提供 AABB 碰撞检测工具方法。"""

    def __init__(self, tilemap: Tilemap | None = None):
        self.tilemap = tilemap
        self.doors_open: bool = False

    def set_tilemap(self, tilemap: Tilemap):
        """设置当前瓦片地图引用。"""
        self.tilemap = tilemap

    def update(self, world: World, dt: float):
        """每帧处理所有带碰撞体的实体与墙壁的碰撞。"""
        entities = world.query(Transform, Collider)

        for eid in entities:
            t = world.get_component(eid, Transform)
            c = world.get_component(eid, Collider)

            if self.tilemap:
                # hover 模式 Boss 跳过墙壁碰撞
                if self._is_hover_boss(world, eid):
                    continue
                hit = self._resolve_walls(t, c)
                # 子弹撞墙自动销毁
                if hit and self._is_projectile(world, eid):
                    world.destroy_entity(eid)

    @staticmethod
    def _is_hover_boss(world: World, eid: int) -> bool:
        """检查是否为悬浮移动模式的 Boss（无视墙壁碰撞）。"""
        from src.ecs.components.boss import Boss
        boss = world.get_component(eid, Boss)
        return boss is not None and boss.movement_mode == "hover"

    @staticmethod
    def _is_projectile(world: World, eid: int) -> bool:
        """判断是否为子弹实体：有 Combat 组件但没有 Health 和 Player。"""
        return (world.has_component(eid, Combat)
                and not world.has_component(eid, Health)
                and not world.has_component(eid, Player))

    def _resolve_walls(self, t: Transform, c: Collider) -> bool:
        """处理墙壁碰撞：检测实体与阻挡瓦片的重叠，沿最小分离轴推出。返回 True 表示碰到了墙。"""
        if not self.tilemap:
            return False

        half_w = c.width / 2
        half_h = c.height / 2
        left = t.x - half_w
        right = t.x + half_w
        top = t.y - half_h
        bottom = t.y + half_h

        tile_size = self.tilemap.tile_size

        # Check tiles overlapped by hitbox
        start_tx = max(0, int(left / tile_size))
        end_tx = min(self.tilemap.width - 1, int(right / tile_size))
        start_ty = max(0, int(top / tile_size))
        end_ty = min(self.tilemap.height - 1, int(bottom / tile_size))

        for ty in range(start_ty, end_ty + 1):
            for tx in range(start_tx, end_tx + 1):
                tile = self.tilemap.get(tx, ty)
                is_blocked = tile == Tile.WALL or tile == Tile.OBSTACLE
                if not self.doors_open and tile == Tile.DOOR:
                    is_blocked = True
                if is_blocked:
                    # 将实体推出墙壁，沿最小重叠轴方向
                    tile_left = tx * tile_size
                    tile_right = tile_left + tile_size
                    tile_top = ty * tile_size
                    tile_bottom = tile_top + tile_size

                    # 计算 X/Y 轴上的重叠量
                    overlap_x = min(right - tile_left, tile_right - left)
                    overlap_y = min(bottom - tile_top, tile_bottom - top)

                    # 选择重叠量较小的轴进行推出（最小分离轴）
                    if overlap_x < overlap_y:
                        if t.x < tile_left + tile_size / 2:
                            t.x = tile_left - half_w
                        else:
                            t.x = tile_right + half_w
                    else:
                        if t.y < tile_top + tile_size / 2:
                            t.y = tile_top - half_h
                        else:
                            t.y = tile_bottom + half_h
                    return True

        return False

    @staticmethod
    def aabb_overlap(
        x1: float, y1: float, w1: float, h1: float,
        x2: float, y2: float, w2: float, h2: float,
    ) -> bool:
        """AABB 矩形碰撞检测：判断两个轴对齐矩形是否重叠。"""
        return (
            abs(x1 - x2) < (w1 + w2) / 2
            and abs(y1 - y2) < (h1 + h2) / 2
        )
