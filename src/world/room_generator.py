"""
关卡房间生成器模块。

通过程序化生成算法创建不同的房间布局：
- arena: 开阔竞技场，中央有环形障碍物和散布柱子
- corridors: 走廊型，随机墙壁段形成通道和扼流点
- pillars: 密集柱子阵，提供大量掩体
"""

import random
from src.world.tilemap import Tilemap
from src.world.tile import Tile


def generate_room(
    cols: int = 25,
    rows: int = 17,
    tile_size: int = 32,
    layout_type: str | None = None,
    door_count: int = 2,
    trap_count: int = -1,
) -> tuple[Tilemap, tuple[float, float], list[tuple[int, int]]]:
    """生成带有指定布局的房间 Tilemap。

    Returns:
        (tilemap, spawn_xy, door_tiles)：地图对象、玩家出生点、门瓦片坐标列表
    """
    if layout_type is None:
        layout_type = random.choice(["arena", "corridors", "pillars"])

    tilemap = Tilemap(cols, rows, tile_size)
    tilemap.fill_border_walls()  # 先填充边界墙壁

    # 根据布局类型调用对应的生成函数
    if layout_type == "arena":
        _layout_arena(tilemap)
    elif layout_type == "corridors":
        _layout_corridors(tilemap)
    elif layout_type == "pillars":
        _layout_pillars(tilemap)
    elif layout_type == "boss_arena":
        _layout_boss_arena(tilemap)

    # 确保玩家出生点安全
    _clear_spawn_area(tilemap)
    # 随机放置陷阱（-1 表示使用默认范围 3-8）
    if trap_count < 0:
        trap_count = random.randint(3, 8)
    _place_traps(tilemap, trap_count)

    # 出生点在地图正中央
    spawn_x = cols * tile_size / 2
    spawn_y = rows * tile_size / 2

    door_tiles = _place_doors(tilemap, door_count)

    return tilemap, (spawn_x, spawn_y), door_tiles


def _layout_arena(tilemap: Tilemap):
    """竞技场布局：开阔空间 + 中央环形障碍物 + 随机散布柱子。"""
    w, h = tilemap.width, tilemap.height
    # 在中央生成环形障碍物
    cx, cy = w // 2, h // 2
    for dx in (-3, 0, 3):
        for dy in (-2, 0, 2):
            tx, ty = cx + dx, cy + dy
            if 1 < tx < w - 2 and 1 < ty < h - 2:
                if abs(dx) + abs(dy) > 0:  # 跳过中心点，保持通道
                    tilemap.set(tx, ty, Tile.OBSTACLE)

    # 随机散布柱子
    for _ in range(random.randint(4, 8)):
        tx = random.randint(3, w - 4)
        ty = random.randint(3, h - 4)
        tilemap.set(tx, ty, Tile.OBSTACLE)


def _layout_corridors(tilemap: Tilemap):
    """走廊布局：随机墙壁段 + 少量障碍物，形成通道和扼流点。"""
    w, h = tilemap.width, tilemap.height
    # 生成水平墙壁段
    for _ in range(random.randint(2, 4)):
        seg_y = random.randint(4, h - 5)
        seg_x = random.randint(3, w - 8)
        seg_len = random.randint(3, 7)
        for dx in range(seg_len):
            tx = seg_x + dx
            if 2 < tx < w - 3:
                tilemap.set(tx, seg_y, Tile.WALL)

    # 生成垂直墙壁段
    for _ in range(random.randint(2, 4)):
        seg_x = random.randint(4, w - 5)
        seg_y = random.randint(3, h - 8)
        seg_len = random.randint(3, 6)
        for dy in range(seg_len):
            ty = seg_y + dy
            if 2 < ty < h - 3:
                tilemap.set(seg_x, ty, Tile.WALL)

    # 少量散布障碍物
    for _ in range(random.randint(2, 4)):
        tx = random.randint(3, w - 4)
        ty = random.randint(3, h - 4)
        tilemap.set(tx, ty, Tile.OBSTACLE)


def _layout_pillars(tilemap: Tilemap):
    """密集柱子布局：大量柱子提供掩体，适合掩体战斗。"""
    w, h = tilemap.width, tilemap.height
    count = random.randint(12, 20)
    for _ in range(count):
        tx = random.randint(3, w - 4)
        ty = random.randint(3, h - 4)
        # 避免堵住中央出生点
        cx, cy = w // 2, h // 2
        if abs(tx - cx) > 2 or abs(ty - cy) > 2:
            tilemap.set(tx, ty, Tile.OBSTACLE)


def _layout_boss_arena(tilemap: Tilemap):
    """Boss 竞技场布局：中央开阔 + 散布障碍和柱子，陷阱对 Boss 同样生效。"""
    w, h = tilemap.width, tilemap.height
    # 散布障碍物，数量与普通房间相当
    for _ in range(random.randint(6, 12)):
        tx = random.randint(3, w - 4)
        ty = random.randint(3, h - 4)
        cx, cy = w // 2, h // 2
        # 中央 5x3 区域保持开阔作为主战场
        if abs(tx - cx) <= 2 and abs(ty - cy) <= 1:
            continue
        if tilemap.get(tx, ty) == Tile.FLOOR:
            tilemap.set(tx, ty, Tile.OBSTACLE)


def _clear_spawn_area(tilemap: Tilemap):
    """强制清空中央 3x3 区域为地板，确保玩家不会出生在墙壁或障碍物中。"""
    cx, cy = tilemap.width // 2, tilemap.height // 2
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            tx, ty = cx + dx, cy + dy
            if 0 < tx < tilemap.width - 1 and 0 < ty < tilemap.height - 1:
                tilemap.set(tx, ty, Tile.FLOOR)


def _place_doors(tilemap: Tilemap, count: int) -> list[tuple[int, int]]:
    """在边界墙壁上放置门，替换墙壁瓦片。

    只在四边（不含角落）的墙壁位置选择候选，并保持门之间有一定间距。
    Returns:
        (tx, ty) 门瓦片坐标的列表
    """
    w, h = tilemap.width, tilemap.height

    # 收集四条边上所有墙壁位置（不含四角）
    candidates = []
    for x in range(1, w - 1):
        if tilemap.get(x, 0) == Tile.WALL:
            candidates.append((x, 0))
        if tilemap.get(x, h - 1) == Tile.WALL:
            candidates.append((x, h - 1))
    for y in range(1, h - 1):
        if tilemap.get(0, y) == Tile.WALL:
            candidates.append((0, y))
        if tilemap.get(w - 1, y) == Tile.WALL:
            candidates.append((w - 1, y))

    # 随机打乱候选，按最小间距选择
    random.shuffle(candidates)
    chosen = []
    for tx, ty in candidates:
        too_close = False
        for cx, cy in chosen:
            # 曼哈顿距离小于 5 视为太近
            if abs(tx - cx) + abs(ty - cy) < 5:
                too_close = True
                break
        if not too_close:
            chosen.append((tx, ty))
            tilemap.set(tx, ty, Tile.DOOR)
            if len(chosen) >= count:
                break

    return chosen


def _place_traps(tilemap: Tilemap, count: int):
    """在随机地板位置放置陷阱瓦片。

    陷阱不会放置在出生点附近、已有陷阱的相邻位置或非地板瓦片上。
    最多尝试 100 次以防死循环。
    """
    w, h = tilemap.width, tilemap.height
    cx, cy = w // 2, h // 2      # 中心（出生点）
    placed = 0
    attempts = 0
    while placed < count and attempts < 100:
        attempts += 1
        tx = random.randint(3, w - 4)
        ty = random.randint(3, h - 4)
        # 只在地板上放置
        if tilemap.get(tx, ty) != Tile.FLOOR:
            continue
        # 避免出生点附近区域
        if abs(tx - cx) <= 2 and abs(ty - cy) <= 2:
            continue
        # 不与另一个陷阱相邻
        neighbor_trap = False
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if tilemap.get(tx + dx, ty + dy) == Tile.TRAP:
                neighbor_trap = True
                break
        if neighbor_trap:
            continue
        tilemap.set(tx, ty, Tile.TRAP)
        placed += 1
