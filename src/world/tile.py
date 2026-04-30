"""
瓦片类型模块。

定义地图上所有瓦片的枚举类型，包括可通行性判断。
使用 IntEnum 方便与整数直接比较和序列化。
"""

from enum import IntEnum


class Tile(IntEnum):
    """地图瓦片类型枚举。

    每种瓦片有不同渲染方式和碰撞规则。
    """
    FLOOR = 0      # 地板（可行走）
    WALL = 1       # 墙壁（不可行走，3D 块渲染）
    DOOR = 2       # 门（可行走，关门时阻挡，开门时可通过）
    OBSTACLE = 3   # 障碍物（不可行走，3D 块渲染）
    TRAP = 4       # 陷阱（可行走但触发伤害效果）

    @property
    def is_walkable(self) -> bool:
        """判断该瓦片是否存在物理阻挡。

        地板、门和陷阱可行走（陷阱触发但不阻挡移动），墙壁和障碍物不可行走。
        """
        return self in (Tile.FLOOR, Tile.DOOR, Tile.TRAP)
