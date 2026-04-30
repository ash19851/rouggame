"""陷阱系统 — 检测玩家和 Boss 踩中陷阱瓦片，触发随机负面效果。

陷阱类型:
  - damage: 直接伤害（玩家 15 点，Boss 按最大生命 8%）
  - slow:   减速 60% 持续 2 秒
  - poison: 中毒每秒扣 3 点持续 3 秒
触发概率: damage 50%, slow 25%, poison 25%
"""

import random
from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.health import Health
from src.ecs.components.player import Player
from src.ecs.components.motion import Motion
from src.ecs.components.status_effect import StatusEffect
from src.ecs.components.boss import Boss
from src.world.tile import Tile


class TrapSystem(System):
    """陷阱系统：检测玩家是否踩中陷阱瓦片，触发随机负面效果并解除陷阱。"""

    def __init__(self):
        self._tilemap = None
        self._trap_rearm: dict[tuple[int, int], float] = {}  # (tx,ty) → 重新装填剩余时间
        self._rearm_delay: float = 3.0  # 陷阱重新装填时间（秒）

    def set_tilemap(self, tilemap):
        """设置当前瓦片地图引用。"""
        self._tilemap = tilemap

    def update(self, world: World, dt: float):
        """每帧检测玩家和 Boss 周围 3x3 瓦片，踩中陷阱则触发效果。"""
        if self._tilemap is None:
            return

        # 陷阱重新装填计时器递减
        expired = []
        for key, timer in self._trap_rearm.items():
            self._trap_rearm[key] = timer - dt
            if self._trap_rearm[key] <= 0:
                expired.append(key)
        for key in expired:
            del self._trap_rearm[key]

        # 检测玩家
        players = world.query(Transform, Health, Player, Motion)
        if players:
            p_eid = players[0]
            pt = world.get_component(p_eid, Transform)
            if pt:
                self._check_traps(world, p_eid, pt.x, pt.y, is_player=True)

        # 检测 Boss
        bosses = world.query(Transform, Health, Boss)
        for b_eid in bosses:
            bt = world.get_component(b_eid, Transform)
            if bt:
                self._check_traps(world, b_eid, bt.x, bt.y, is_player=False)

    def _check_traps(self, world, eid, px, py, is_player):
        """检查实体周围 3x3 区域是否有陷阱瓦片。"""
        px_tile = int(px / self._tilemap.tile_size)
        py_tile = int(py / self._tilemap.tile_size)

        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                tx = px_tile + dx
                ty = py_tile + dy
                if 0 <= tx < self._tilemap.width and 0 <= ty < self._tilemap.height:
                    tile = self._tilemap.get(tx, ty)
                    if tile == Tile.TRAP and self._is_on_tile(px, py, tx, ty):
                        self._trigger_trap(world, eid, tx, ty, is_player)

    def _is_on_tile(self, px, py, tx, ty):
        """判断玩家坐标是否在指定瓦片区域内。"""
        ts = self._tilemap.tile_size
        tlx = tx * ts
        tly = ty * ts
        return tlx <= px < tlx + ts and tly <= py < tly + ts

    def _trigger_trap(self, world, entity_eid, tx, ty, is_player):
        """触发陷阱：检查装填状态、随机选择类型、对实体应用效果，然后进入冷却。"""
        key = (tx, ty)
        if key in self._trap_rearm:
            return  # 陷阱还在冷却中

        trap_type = random.choices(
            ["damage", "slow", "poison"],
            weights=[50, 25, 25],
            k=1,
        )[0]

        h = world.get_component(entity_eid, Health)
        m = world.get_component(entity_eid, Motion)

        if trap_type == "damage":
            if h:
                if is_player:
                    h.current = max(0, h.current - 15)
                else:
                    # Boss: 最大生命 8% 的陷阱伤害
                    dmg = max(5, int(h.max * 0.08))
                    h.current = max(0, h.current - dmg)
        elif trap_type == "slow":
            if m:
                m.speed *= 0.4
            se = world.get_component(entity_eid, StatusEffect)
            if se is None:
                se = StatusEffect()
                world.add_component(entity_eid, se)
            se.effects.append({
                "type": "slow", "tick_interval": 999.0, "tick_timer": 999.0,
                "remaining_ticks": 0, "damage": 0, "slow_pct": 0.4, "duration": 2.0,
            })
        elif trap_type == "poison":
            se = world.get_component(entity_eid, StatusEffect)
            if se is None:
                se = StatusEffect()
                world.add_component(entity_eid, se)
            se.effects.append({
                "type": "poison", "tick_interval": 0.5, "tick_timer": 0.5,
                "remaining_ticks": 5, "damage": 3, "slow_pct": 1.0, "duration": 3.0,
            })

        # 陷阱触发后进入冷却，冷却结束后可重新触发
        self._trap_rearm[key] = self._rearm_delay
