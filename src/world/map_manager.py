"""
地图管理器模块。

管理一个关卡（stage）中所有房间的生成序列、怪物配置和难度递增。
负责按顺序创建房间，控制怪物种类和数量随进度增长。
"""

import random
from src.world.room import Room
from src.world.room_generator import generate_room
from src.world.tilemap import Tilemap
from src.data.config_loader import ENEMIES, BALANCE


class MapManager:
    """管理和生成关卡的房间序列。

    在初始化时预生成布局计划，每次进入新房间时按计划创建 Room 对象。
    难度随房间进度和关卡数递增：更多怪物、更丰富的怪物种类。
    """

    def __init__(self, room_count: int = 6, stage: int = 1):
        self.room_count = room_count
        self.stage = stage
        self.current_index: int = 0
        self.layouts: list[str] = []  # 每个房间的布局类型
        self._generate_plan()

    def _generate_plan(self):
        """预生成本关卡所有房间的布局类型（arena / corridors / pillars）。"""
        layout_types = ["arena", "corridors", "pillars"]
        self.layouts = [random.choice(layout_types) for _ in range(self.room_count)]

    @property
    def difficulty_mult(self) -> float:
        """难度系数，随房间进度和关卡数递增。

        基于 BALANCE 配置文件中的基础倍率和房间进度加成计算。
        """
        diff_cfg = BALANCE["difficulty"]
        base = 1.0 + (self.stage - 1) * diff_cfg["base_mult_per_stage"]
        progress_bonus = self.current_index * diff_cfg["room_progress_bonus"]
        return base + progress_bonus

    @property
    def is_last_room(self) -> bool:
        """当前房间是否为关卡最后一个房间。"""
        return self.current_index >= self.room_count - 1

    BOSS_ROOM_INTERVAL = 3  # 每 3 个房间出现 Boss

    @property
    def is_boss_room(self) -> bool:
        """当前房间是否为 Boss 房间（每 3 个房间一个）。"""
        return (self.current_index + 1) % self.BOSS_ROOM_INTERVAL == 0

    def get_encounter_level(self) -> int:
        """返回当前 Boss 房间的遭遇等级（1-6）。"""
        return (self.current_index + 1) // self.BOSS_ROOM_INTERVAL

    def create_room(self) -> Room:
        """生成当前进度的房间。在进入新房间时调用。

        怪物池和数量随 current_index 递增：
        - 怪物种类随进度解锁（每 2 个房间增加一种）
        - 怪物数量随进度线性增长
        - Boss 房间使用专用竞技场布局，怪物池为空（Boss 单独生成）
        """
        is_boss = self.is_boss_room
        boss_config = BALANCE.get("boss", {})

        if self.current_index >= self.room_count:
            layout = random.choice(["arena", "pillars"])
        elif is_boss:
            layout = "boss_arena"
        else:
            layout = self.layouts[self.current_index]

        # Boss 房间使用更大的尺寸，陷阱数与其他房间一致
        cols = boss_config.get("boss_arena_cols", 30) if is_boss else 25
        rows = boss_config.get("boss_arena_rows", 20) if is_boss else 17
        trap_count = random.randint(3, 8)  # Boss 房间同样有陷阱，对 Boss 也生效

        tilemap, spawn, door_tiles = generate_room(
            layout_type=layout,
            door_count=random.randint(1, 3),
            cols=cols,
            rows=rows,
            trap_count=trap_count,
        )

        if is_boss:
            monster_pool = []
            monster_count = (0, 0)
        else:
            all_types = list(ENEMIES.keys())
            pool_size = min(len(all_types), 1 + self.current_index // 2)
            monster_pool = random.sample(all_types, pool_size)
            base_count = (5, 10)
            extra_per_room = self.current_index * 3
            monster_count = (base_count[0] + extra_per_room, base_count[1] + extra_per_room)

        room = Room(
            room_id=self.current_index,
            tilemap=tilemap,
            spawn_x=spawn[0],
            spawn_y=spawn[1],
            door_positions=[(dt[0] * tilemap.tile_size + tilemap.tile_size / 2,
                             dt[1] * tilemap.tile_size + tilemap.tile_size / 2)
                            for dt in door_tiles],
            monster_pool=monster_pool,
            monster_count=monster_count,
            is_boss_room=is_boss,
        )

        return room

    def advance(self):
        """推进到下一个房间索引。返回 False 表示关卡已结束。"""
        self.current_index += 1
        return self.current_index < self.room_count
