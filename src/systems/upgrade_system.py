"""升级系统 — 管理玩家经验升级和升级选择。

升级流程:
  1. XP 达到阈值 -> 扣除 XP、等级+1、升级阈值增长
  2. 发出 UPGRADE_READY 事件，暂停游戏展示升级选项
  3. 玩家选择升级 -> apply_upgrade 应用对应属性提升

可用升级: max_hp, attack_speed, move_speed, damage, heal, projectile_speed,
          range, projectile_size, magnet, armor, regen, crit_chance, crit_mult
"""

from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.player import Player
from src.ecs.components.health import Health
from src.ecs.components.combat import Combat
from src.ecs.components.motion import Motion
from src.core.event_bus import EventBus
from src.data.config_loader import UPGRADE_CHOICES, UPGRADE_XP_CURVE_MULT


class UpgradeSystem(System):
    """升级系统：检测 XP 达标触发升级，提供属性选择并应用对应加成。"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.pending_upgrade = False
        self._just_triggered = False

    def update(self, world: World, dt: float):
        """每帧检测 XP 是否达标，触发升级流程。"""
        if self._just_triggered:
            self._just_triggered = False
            return

        players = world.query(Transform, Player, Health)
        if not players:
            return

        p_eid = players[0]
        pp = world.get_component(p_eid, Player)

        # XP 达标：升级
        if pp.xp >= pp.xp_to_level:
            pp.xp -= pp.xp_to_level  # 扣除升级所需 XP，多余保留
            pp.level += 1
            # 下一级所需 XP 按倍率递增
            pp.xp_to_level = int(pp.xp_to_level * UPGRADE_XP_CURVE_MULT)
            self.pending_upgrade = True
            self._just_triggered = True
            self.event_bus.emit("UPGRADE_READY", level=pp.level)

    def apply_upgrade(self, world: World, choice: str):
        """应用玩家选择的升级：从 UPGRADE_CHOICES 查找对应属性加成并应用。"""
        players = world.query(Transform, Player, Health, Combat, Motion)
        if not players:
            return

        p_eid = players[0]
        pp = world.get_component(p_eid, Player)
        ph = world.get_component(p_eid, Health)
        pc = world.get_component(p_eid, Combat)
        pm = world.get_component(p_eid, Motion)

        amount = 0.0
        for ch in UPGRADE_CHOICES:
            if ch["key"] == choice:
                amount = ch["amount"]
                break

        if choice == "max_hp":
            ph.max += int(amount)
            ph.current = min(ph.current + int(amount), ph.max)
        elif choice == "attack_speed":
            pc.attack_speed += amount
        elif choice == "move_speed":
            pm.speed += amount
        elif choice == "damage":
            pc.damage += int(amount)
        elif choice == "heal":
            ph.current = ph.max
        elif choice == "projectile_speed":
            pc.projectile_speed += amount
        elif choice == "range":
            pc.range += amount
        elif choice == "projectile_size":
            pc.projectile_size += amount
        elif choice == "magnet":
            pp.magnet_bonus += amount
        elif choice == "armor":
            pp.armor += int(amount)
        elif choice == "regen":
            pp.regen += amount
        elif choice == "crit_chance":
            pp.crit_chance = min(pp.crit_chance + amount, 0.8)
        elif choice == "crit_mult":
            pp.crit_mult += amount

        self.pending_upgrade = False
