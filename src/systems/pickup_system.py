"""拾取系统 — 处理玩家与掉落物的交互，支持 XP、生命、装备三种类型。

拾取机制:
  - 磁吸范围: 根据 pick_type 和玩家 magnet_bonus 决定吸引距离
  - XP 自动磁吸: 范围随玩家等级递增
  - 飞向玩家: 在磁吸范围内逐渐向玩家移动
  - 收集距离: 小于阈值则拾取生效
"""

import math
from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.collision import Collider
from src.ecs.components.pickup import Pickup
from src.ecs.components.player import Player
from src.ecs.components.health import Health
from src.core.event_bus import EventBus
from src.data.config_loader import BALANCE


class PickupSystem(System):
    """拾取系统：检测玩家与掉落物距离，在磁吸范围内吸引并在收集距离内拾取。"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    def update(self, world: World, dt: float):
        """每帧处理所有掉落物与玩家的距离判定。"""
        players = world.query(Transform, Player, Health)
        if not players:
            return
        p_eid = players[0]
        pt = world.get_component(p_eid, Transform)
        pp = world.get_component(p_eid, Player)
        ph = world.get_component(p_eid, Health)

        pickups = world.query(Transform, Pickup)

        for pk_eid in pickups:
            pkt = world.get_component(pk_eid, Transform)
            pk = world.get_component(pk_eid, Pickup)

            dx = pt.x - pkt.x
            dy = pt.y - pkt.y
            dist = math.sqrt(dx * dx + dy * dy)

            pcfg = BALANCE["pickup"]
            # 磁吸范围 = 基础范围 + 玩家磁吸加成
            magnet = pk.magnet_range + pp.magnet_bonus

            # XP 自动磁吸：范围随等级增大
            if pk.pickup_type == "xp":
                magnet += pp.level * pcfg["xp_magnet_per_level"]

            if dist < magnet:
                # 磁吸范围内：飞向玩家
                if dist > 0:
                    pkt.x += (dx / dist) * pcfg["fly_speed"] * dt
                    pkt.y += (dy / dist) * pcfg["fly_speed"] * dt

            # 收集判定：距离小于收集阈值时拾取
            if dist < pcfg["collect_distance"]:
                if pk.pickup_type == "xp":
                    pp.xp += pk.value
                    self.event_bus.emit("XP_GAINED", amount=pk.value, total=pp.xp, xp_to_level=pp.xp_to_level)
                elif pk.pickup_type == "health":
                    ph.current = min(ph.max, ph.current + pk.value)
                elif pk.pickup_type == "equipment":
                    self.event_bus.emit("EQUIPMENT_DROPPED",
                                        equipment_id=pk.equipment_id, x=pkt.x, y=pkt.y)

                world.destroy_entity(pk_eid)
                self.event_bus.emit("PICKUP_COLLECTED", pickup_type=pk.pickup_type)
