"""
关卡房间数据模块。

定义房间的数据结构，包含地图、出生点、门位置、怪物配置等。
房间由 MapManager 创建和管理。
"""

from dataclasses import dataclass, field
from src.world.tilemap import Tilemap


@dataclass
class Room:
    """单个关卡房间的完整数据。

    Attributes:
        room_id: 房间序号（从 0 开始）
        tilemap: 瓦片地图对象
        spawn_x/spawn_y: 玩家出生点（世界坐标）
        door_positions: 各门的世界坐标位置列表
        monster_pool: 可选怪物类型列表
        monster_count: 怪物随机数量范围 (min, max)
        cleared: 是否已清完怪物
        door_type: 门的外观主题，由地图生成器分配
    """
    room_id: int
    tilemap: Tilemap
    spawn_x: float = 0.0
    spawn_y: float = 0.0
    door_positions: list[tuple[float, float]] = field(default_factory=list)
    monster_pool: list[str] = field(default_factory=list)
    monster_count: tuple[int, int] = (3, 6)
    cleared: bool = False
    door_type: str = ""  # 门类型，由地图生成器分配
    is_boss_room: bool = False  # 是否为 Boss 房间

    @property
    def width_px(self) -> float:
        """房间宽度（像素）。"""
        return self.tilemap.width * self.tilemap.tile_size

    @property
    def height_px(self) -> float:
        """房间高度（像素）。"""
        return self.tilemap.height * self.tilemap.tile_size
