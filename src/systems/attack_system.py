"""攻击系统 — 处理玩家攻击逻辑，包括普通射击、散射、轨道球、波形弹、撞击散射等多种武器模式。

武器模式:
  - normal:          单发子弹
  - scatter:         扇形散射
  - orbital:         环绕轨道球
  - wave:            正弦波弹
  - impact_scatter:  命中后分裂碎片
"""

import math
from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.combat import Combat
from src.ecs.components.player import Player
from src.ecs.components.health import Health
from src.ecs.components.weapon_pattern import WeaponPattern
from src.ecs.components.orbital import Orbital
from src.core.event_bus import EventBus
from src.entities.projectile_factory import create_projectile, create_orbital, create_wave_projectile
from src.entities.particle_factory import emit_burst


class AttackSystem(System):
    """攻击系统：管理玩家攻击冷却、暴击判定、枪口闪光粒子，并根据武器模式生成对应弹幕。"""

    def __init__(self, event_bus: EventBus | None = None):
        self._attacking = False
        self.event_bus = event_bus

    def set_attacking(self, attacking: bool):
        """设置攻击状态（按下/松开鼠标）。"""
        self._attacking = attacking

    def update(self, world: World, dt: float):
        """每帧更新：减冷却、判断是否攻击、生成弹幕。"""
        players = world.query(Transform, Combat, Player, Health)
        if not players:
            return

        peid = players[0]
        pt = world.get_component(peid, Transform)
        pc = world.get_component(peid, Combat)
        pp = world.get_component(peid, Player)

        # 冷却递减
        if pc.cooldown > 0:
            pc.cooldown -= dt

        # 攻击就绪且冷却完毕
        if self._attacking and pc.cooldown <= 0:
            pc.cooldown = 1.0 / pc.attack_speed  # 重置冷却为攻击间隔

            dir_x, dir_y = pp.aim_x, pp.aim_y

            wp = world.get_component(peid, WeaponPattern)
            pattern = wp.pattern if wp else "normal"

            # 暴击判定 — 临时提升本次攻击伤害
            import random
            base_damage = pc.damage
            is_crit = pp.crit_chance > 0 and random.random() < pp.crit_chance
            if is_crit:
                pc.damage = max(1, int(base_damage * pp.crit_mult))

            # 枪口闪光粒子（暴击时黄色）
            muzzle_x = pt.x + dir_x * 10
            muzzle_y = pt.y + dir_y * 10
            flash_color = (255, 220, 80) if is_crit else (200, 230, 255)
            emit_burst(world, muzzle_x, muzzle_y,
                       count=5 if is_crit else 3, color=flash_color, speed=40.0,
                       lifetime=0.15 if is_crit else 0.12, size=3.0 if is_crit else 2.0)

            if pattern == "scatter":
                self._attack_scatter(world, pt, pc, pp, wp, peid)
            elif pattern == "orbital":
                self._attack_orbital(world, pt, pc, wp, peid)
            elif pattern == "wave":
                self._attack_wave(world, pt, pc, pp, wp, peid)
            elif pattern == "impact_scatter":
                self._attack_impact(world, pt, pc, pp, peid)
            else:
                self._attack_normal(world, pt, pc, pp, peid)

            # 恢复原始伤害值
            pc.damage = base_damage

    def _attack_normal(self, world, pt, pc, pp, peid):
        """普通攻击：向瞄准方向发射单发子弹。"""
        create_projectile(
            world, pt.x, pt.y,
            pp.aim_x, pp.aim_y,
            pc.projectile_speed, pc.damage,
            pc.projectile_color, pc.projectile_size,
            pc.range, peid,
        )

    def _attack_scatter(self, world, pt, pc, pp, wp, peid):
        """散射攻击：在瞄准方向左右展开扇形弹幕。"""
        base_angle = math.atan2(pp.aim_y, pp.aim_x)
        count = wp.spread_count
        half_angle = math.radians(wp.spread_angle)
        for i in range(count):
            if count == 1:
                angle = base_angle
            else:
                angle = base_angle - half_angle + (2 * half_angle * i / (count - 1))
            dx = math.cos(angle)
            dy = math.sin(angle)
            create_projectile(
                world, pt.x, pt.y, dx, dy,
                pc.projectile_speed, pc.damage,
                pc.projectile_color, pc.projectile_size,
                pc.range, peid,
            )

    def _attack_orbital(self, world, pt, pc, wp, peid):
        """轨道攻击：在玩家周围等角度生成环绕轨道球，不超过上限。"""
        count = 0
        for eid in world.query(Orbital):
            orb = world.get_component(eid, Orbital)
            if orb.source_eid == peid:
                count += 1

        if count < wp.orbital_max:
            angle = count * (2 * math.pi / wp.orbital_max)
            create_orbital(
                world, pt.x, pt.y, angle, wp.orbital_radius,
                wp.orbital_speed, wp.orbital_lifetime,
                pc.damage, pc.projectile_color, pc.projectile_size,
                source_eid=peid,
            )

    def _attack_wave(self, world, pt, pc, pp, wp, peid):
        """波形攻击：发射正弦波路径子弹。"""
        create_wave_projectile(
            world, pt.x, pt.y,
            pp.aim_x, pp.aim_y,
            pc.projectile_speed,
            wp.wave_amplitude, wp.wave_frequency,
            pc.damage, pc.projectile_color, pc.projectile_size,
            peid,
        )

    def _attack_impact(self, world, pt, pc, pp, peid):
        """撞击散射：发射标记弹，命中敌人后分裂碎片。"""
        create_projectile(
            world, pt.x, pt.y,
            pp.aim_x, pp.aim_y,
            pc.projectile_speed, pc.damage,
            pc.projectile_color, pc.projectile_size,
            pc.range, peid,
            tag_extra="impact_scatter",
        )
