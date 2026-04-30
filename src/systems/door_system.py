"""门系统 — 管理房间门的状态，玩家清空房间后门变为可用，靠近时触发切换房间事件。

状态流转:
  ROOM_CLEARED -> 门激活 (doors_active = True)
  玩家踩到 DOOR 瓦片 -> DOOR_APPROACHED 事件 -> 切换房间
  NEW_ROOM -> 门重置
"""

from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.player import Player
from src.ecs.components.health import Health
from src.world.tilemap import Tilemap
from src.world.tile import Tile
from src.core.event_bus import EventBus


class DoorSystem(System):
    """门系统：监听房间清空事件激活门，检测玩家靠近门瓦片并发出切换事件。"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.doors_active: bool = False
        self._door_approached: bool = False
        self.tilemap: Tilemap | None = None
        event_bus.subscribe("ROOM_CLEARED", self._on_room_cleared)
        event_bus.subscribe("NEW_ROOM", self._on_new_room)

    def set_tilemap(self, tilemap: Tilemap):
        """设置当前瓦片地图引用。"""
        self.tilemap = tilemap

    def _on_room_cleared(self, event_type: str, data: dict):
        """房间清空回调：激活门。"""
        self.doors_active = True

    def _on_new_room(self, event_type: str, data: dict):
        """进入新房间回调：重置门状态。"""
        self.doors_active = False
        self._door_approached = False

    def reset_door(self):
        """重置门靠近状态。"""
        self._door_approached = False

    def is_door_active(self) -> bool:
        """查询门是否激活。"""
        return self.doors_active

    def update(self, world: World, dt: float):
        """每帧检测玩家是否站在门瓦片上，若是则发出 DOOR_APPROACHED 事件。"""
        if not self.doors_active or not self.tilemap or self._door_approached:
            return

        players = world.query(Transform, Player, Health)
        if not players:
            return

        p_eid = players[0]
        pt = world.get_component(p_eid, Transform)

        tx, ty = self.tilemap.world_to_tile(pt.x, pt.y)
        if self.tilemap.get(tx, ty) == Tile.DOOR:
            self._door_approached = True
            self.event_bus.emit("DOOR_APPROACHED", door_tile=(tx, ty))
