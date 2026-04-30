"""装备系统 — 管理装备掉落、拾取存储、装备/卸下、属性加成、武器模式切换。

功能:
  - 装备掉落自动存入背包
  - 背包满时掉落在地
  - equip/unequip 切换装备与背包物品
  - 属性增量式加成/移除
  - 武器模式随装备切换
  - 装备数据持久化保存
"""

from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.player import Player
from src.ecs.components.health import Health
from src.ecs.components.combat import Combat
from src.ecs.components.motion import Motion
from src.ecs.components.equipment import Equipment
from src.ecs.components.inventory import Inventory
from src.ecs.components.weapon_pattern import WeaponPattern
from src.data.equipment_defs import EQUIPMENT_DEFS, RARITY_COLORS
from src.data.equipment_store import save_equipment
from src.core.event_bus import EventBus


class EquipmentSystem(System):
    """装备系统：处理装备掉落拾取、装备/卸下操作和属性加成计算。"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._pending_drops: list[dict] = []
        self._toast_timer: float = 0.0
        self._toast_text: str = ""
        self._toast_color: tuple[int, int, int] = (255, 255, 255)
        event_bus.subscribe("EQUIPMENT_DROPPED", self._on_equipment_dropped)

    @property
    def toast_alpha(self) -> float:
        """提示文本透明度：用于淡出效果。"""
        if self._toast_timer <= 0:
            return 0.0
        return min(1.0, self._toast_timer / 1.0)

    def _on_equipment_dropped(self, event_type: str, data: dict):
        """装备掉落事件回调：加入待处理队列。"""
        self._pending_drops.append(data)

    def update(self, world: World, dt: float):
        """每帧处理待处理的装备掉落和提示计时。"""
        if self._toast_timer > 0:
            self._toast_timer -= dt

        if self._pending_drops:
            for data in self._pending_drops:
                self._process_drop(world, data)
            self._pending_drops.clear()

    def _process_drop(self, world: World, data: dict):
        """处理单件装备掉落：优先放入背包，满则掉落在玩家位置。"""
        equipment_id = data.get("equipment_id", "")
        item = EQUIPMENT_DEFS.get(equipment_id)
        if not item:
            return

        players = world.query(Player, Health, Combat, Motion)
        if not players:
            return
        p_eid = players[0]

        inv = world.get_component(p_eid, Inventory)
        if not inv:
            inv = Inventory()
            world.add_component(p_eid, inv)

        # 尝试放入背包第一个空位
        for i in range(len(inv.backpack)):
            if inv.backpack[i] is None:
                inv.backpack[i] = dict(item)
                self._set_toast(f"已存入：{item['name']}（背包）",
                                RARITY_COLORS.get(item["rarity"], (255, 255, 255)))
                self._save_player(world, p_eid)
                return

        # 背包满 — 掉落在玩家位置
        ppos = data.get("x", 0), data.get("y", 0)
        self.event_bus.emit("INVENTORY_FULL", equipment_id=equipment_id, x=ppos[0], y=ppos[1])
        self._set_toast("背包已满！物品掉落", (255, 150, 80))

    # ---- 背包界面公共 API ----

    def equip_item(self, world: World, player_eid: int, inv_slot: int) -> bool:
        """装备物品：从背包槽位移到对应装备槽。若装备槽已有物品，则互换。"""
        inv = world.get_component(player_eid, Inventory)
        eq = world.get_component(player_eid, Equipment)
        if not inv or not eq:
            return False

        item = inv.backpack[inv_slot]
        if item is None:
            return False

        slot = item["slot"]
        old_item = eq.items.get(slot)

        inv.backpack[inv_slot] = None

        if old_item:
            self._apply_stats(world, old_item, reverse=True)
            if slot == "weapon":
                self._set_pattern(world, "normal")
            inv.backpack[inv_slot] = dict(old_item)

        self._apply_stats(world, item)
        if slot == "weapon":
            self._set_pattern(world, item.get("pattern", "normal"), item)
        eq.items[slot] = dict(item)

        self._set_toast(f"已装备：{item['name']}",
                        RARITY_COLORS.get(item["rarity"], (255, 255, 255)))
        self._save_player(world, player_eid)
        return True

    def unequip_item(self, world: World, player_eid: int, eq_slot: str) -> bool:
        """卸下装备：从装备槽移到背包第一个空位。"""
        inv = world.get_component(player_eid, Inventory)
        eq = world.get_component(player_eid, Equipment)
        if not inv or not eq:
            return False

        item = eq.items.get(eq_slot)
        if item is None:
            return False

        for i in range(len(inv.backpack)):
            if inv.backpack[i] is None:
                self._apply_stats(world, item, reverse=True)
                if eq_slot == "weapon":
                    self._set_pattern(world, "normal")
                inv.backpack[i] = dict(item)
                del eq.items[eq_slot]

                self._set_toast(f"已卸下：{item['name']}",
                                RARITY_COLORS.get(item["rarity"], (255, 255, 255)))
                self._save_player(world, player_eid)
                return True

        self._set_toast("背包已满！无法卸下", (255, 150, 80))
        return False

    def can_unequip(self, world: World, player_eid: int) -> bool:
        """检查背包是否有空位可以卸下装备。"""
        inv = world.get_component(player_eid, Inventory)
        if not inv:
            return False
        return any(slot is None for slot in inv.backpack)

    # ---- 属性 / 武器模式辅助方法 ----

    def _apply_stats(self, world: World, item: dict, reverse: bool = False):
        """应用或移除装备属性加成。reverse=True 时扣除属性。"""
        players = world.query(Player, Health, Combat, Motion)
        if not players:
            return
        p_eid = players[0]
        ph = world.get_component(p_eid, Health)
        pc = world.get_component(p_eid, Combat)
        pm = world.get_component(p_eid, Motion)

        sign = -1 if reverse else 1
        for stat_key, value in item.get("stats", {}).items():
            delta = int(value * sign) if stat_key in ("damage", "max_hp") else value * sign

            if stat_key == "max_hp":
                if ph:
                    ph.max += delta
                    if not reverse:
                        ph.current += delta
                    else:
                        ph.current = min(ph.current, ph.max)
            elif stat_key == "damage":
                if pc:
                    pc.damage += delta
            elif stat_key == "attack_speed":
                if pc:
                    pc.attack_speed += delta
            elif stat_key == "range":
                if pc:
                    pc.range += delta
            elif stat_key == "projectile_speed":
                if pc:
                    pc.projectile_speed += delta
            elif stat_key == "projectile_size":
                if pc:
                    pc.projectile_size += delta
            elif stat_key == "move_speed":
                if pm:
                    pm.speed += delta

    def _set_pattern(self, world: World, pattern_name: str, item: dict | None = None):
        """设置玩家武器模式及对应的散布、轨道等参数。"""
        players = world.query(Player)
        if not players:
            return
        p_eid = players[0]
        existing = world.get_component(p_eid, WeaponPattern)
        if existing is None:
            return
        existing.pattern = pattern_name
        if item:
            existing.spread_count = item.get("spread_count", 3)
            existing.spread_angle = item.get("spread_angle", 15.0)
            existing.frag_count = item.get("frag_count", 4)
            existing.orbital_radius = item.get("orbital_radius", 40.0)
            existing.orbital_speed = item.get("orbital_speed", 4.0)
            existing.orbital_max = item.get("orbital_max", 5)
            existing.orbital_lifetime = item.get("orbital_lifetime", 3.0)
            existing.wave_amplitude = item.get("wave_amplitude", 15.0)
            existing.wave_frequency = item.get("wave_frequency", 8.0)
        else:
            existing.spread_count = 3
            existing.spread_angle = 15.0
            existing.frag_count = 4
            existing.orbital_radius = 40.0
            existing.orbital_speed = 4.0
            existing.orbital_max = 5
            existing.orbital_lifetime = 3.0
            existing.wave_amplitude = 15.0
            existing.wave_frequency = 8.0

    def init_player_equipment(self, world: World, player_eid: int, loaded_data: dict):
        """从存档加载玩家装备和背包数据，并应用属性加成。"""
        eq = world.get_component(player_eid, Equipment)
        if not eq:
            eq = Equipment()
            world.add_component(player_eid, eq)

        inv = world.get_component(player_eid, Inventory)
        if not inv:
            inv = Inventory()
            world.add_component(player_eid, inv)

        if not loaded_data:
            return

        # Load equipped items
        for slot, item in loaded_data.get("equipped", {}).items():
            self._apply_stats(world, item)
            eq.items[slot] = item
            if slot == "weapon":
                self._set_pattern(world, item.get("pattern", "normal"), item)

        # Load inventory
        serialized_inv = loaded_data.get("inventory", [])
        for i, item in enumerate(serialized_inv):
            if i < len(inv.backpack) and item is not None:
                inv.backpack[i] = dict(item)

        self._set_toast("装备已加载", (200, 200, 200))

    def _save_player(self, world: World, player_eid: int):
        """保存玩家装备和背包数据到本地存储。"""
        eq = world.get_component(player_eid, Equipment)
        inv = world.get_component(player_eid, Inventory)
        save_equipment(
            equipped=eq.items if eq else {},
            inventory=inv.backpack if inv else [],
        )

    @staticmethod
    def _score_item(item: dict) -> float:
        """物品评分：根据属性类型加权计算，伤害类权重最高。"""
        score = 0.0
        for k, v in item.get("stats", {}).items():
            if k == "max_hp":
                score += v * 0.5
            elif k == "move_speed":
                score += v * 0.3
            elif k in ("damage", "attack_speed"):
                score += v * 2.0
            else:
                score += v * 1.0
        return score

    def _set_toast(self, text: str, color: tuple[int, int, int]):
        """设置弹出提示文本和颜色，计时器设为 2 秒。"""
        self._toast_text = text
        self._toast_color = color
        self._toast_timer = 2.0
