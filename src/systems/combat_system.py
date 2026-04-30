"""战斗系统 — 处理所有战斗伤害判定，包括玩家子弹 vs 敌人、敌人子弹 vs 玩家、敌人近战、死亡爆发等。

主要流程:
  1. 无敌计时器递减
  2. 玩家生命回复
  3. 玩家子弹命中敌人
  4. 敌人子弹命中玩家
  5. 敌人近战/远程攻击玩家
  6. 死亡爆发（Spriggan 自爆）
"""

import math, random
from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.collision import Collider
from src.ecs.components.combat import Combat
from src.ecs.components.health import Health
from src.ecs.components.player import Player
from src.ecs.components.ai import AI
from src.ecs.components.weapon_pattern import WeaponPattern
from src.ecs.components.enemy_projectile import EnemyProjectile
from src.systems.collision_system import CollisionSystem
from src.entities.projectile_factory import create_projectile
from src.entities.enemy_projectile_factory import create_enemy_projectile
from src.core.event_bus import EventBus


class CombatSystem(System):
    """战斗系统：协调所有伤害判定流程，连接子弹命中、近战攻击、死亡事件。"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._tracked_deaths: set[int] = set()

    def update(self, world: World, dt: float):
        """每帧执行完整的战斗判定流程。"""
        # 无敌计时器递减
        for eid in world.query(Health):
            health = world.get_component(eid, Health)
            health.tick(dt)

        # 玩家生命回复
        self._apply_regen(world, dt)

        # 玩家子弹 vs 敌人
        self._process_player_projectiles(world)

        # 敌人子弹 vs 玩家
        self._process_enemy_projectiles(world)

        # 敌人近战 + 远程攻击玩家
        self._process_enemy_attacks(world, dt)

        # 死亡自爆处理（Spriggan）
        self._process_death_bursts(world)

        # 通用死亡检测：捕获被陷阱、中毒等非直接伤害杀死的实体
        self._detect_deaths(world)

    def _apply_regen(self, world, dt):
        """对玩家应用生命回复。"""
        players = world.query(Player, Health)
        if not players:
            return
        pp = world.get_component(players[0], Player)
        ph = world.get_component(players[0], Health)
        if pp.regen > 0 and ph.current < ph.max and ph.alive:
            ph.current = min(ph.max, ph.current + pp.regen * dt)

    def _process_player_projectiles(self, world):
        """玩家子弹命中敌人：AABB 碰撞检测，造成伤害，触发 impact_scatter 碎片。"""
        projectiles = world.query(Transform, Collider)
        enemies = world.query(Transform, Collider, Health)

        proj_ids = [eid for eid in projectiles
                    if world.has_component(eid, Combat)
                    and not world.has_component(eid, Player)
                    and not world.has_component(eid, Health)
                    and not world.has_component(eid, EnemyProjectile)]

        enemy_set = {eid for eid in enemies if not world.has_component(eid, Player)}
        dead_projectiles = set()

        for peid in proj_ids:
            if peid in dead_projectiles:
                continue
            pt = world.get_component(peid, Transform)
            pc = world.get_component(peid, Collider)
            pcombat = world.get_component(peid, Combat)

            for eeid in enemy_set:
                et = world.get_component(eeid, Transform)
                ec = world.get_component(eeid, Collider)
                eh = world.get_component(eeid, Health)

                if CollisionSystem.aabb_overlap(
                    pt.x, pt.y, pc.width, pc.height,
                    et.x, et.y, ec.width, ec.height,
                ):
                    eh.take_damage(pcombat.damage)
                    self.event_bus.emit("ATTACK_HIT", target=eeid, damage=pcombat.damage, x=et.x, y=et.y)
                    from src.entities.particle_factory import emit_damage_number
                    emit_damage_number(world, et.x, et.y - 8, pcombat.damage)

                    # impact_scatter 模式：命中后分裂碎片
                    wp = world.get_component(peid, WeaponPattern)
                    if wp is not None and wp.pattern == "impact_scatter":
                        self._spawn_fragments(world, pt.x, pt.y, wp.frag_count, pcombat)

                    if not eh.alive:
                        self._tracked_deaths.add(eeid)
                        self.event_bus.emit("ENTITY_DIED", entity=eeid, position=(et.x, et.y))

                    dead_projectiles.add(peid)
                    break

        for peid in dead_projectiles:
            world.destroy_entity(peid)

    def _process_enemy_projectiles(self, world):
        """敌人子弹命中玩家：AABB 碰撞检测，伤害受玩家护甲减免。"""
        players = world.query(Transform, Collider, Health, Player)
        if not players:
            return
        p_eid = players[0]
        pt = world.get_component(p_eid, Transform)
        pc_coll = world.get_component(p_eid, Collider)
        ph = world.get_component(p_eid, Health)
        pp = world.get_component(p_eid, Player)

        enemy_proj = [eid for eid in world.query(Transform, Collider, Combat)
                      if world.has_component(eid, EnemyProjectile)]

        dead = set()
        for epid in enemy_proj:
            ept = world.get_component(epid, Transform)
            epc = world.get_component(epid, Collider)
            epcombat = world.get_component(epid, Combat)

            if CollisionSystem.aabb_overlap(
                ept.x, ept.y, epc.width, epc.height,
                pt.x, pt.y, pc_coll.width, pc_coll.height,
            ):
                dmg = max(1, epcombat.damage - pp.armor)
                ph.take_damage(dmg)
                self.event_bus.emit("PLAYER_HIT", damage=dmg, x=pt.x, y=pt.y)
                dead.add(epid)
                if not ph.alive:
                    self.event_bus.emit("PLAYER_DIED", entity=p_eid)

        for epid in dead:
            world.destroy_entity(epid)

    def _process_enemy_attacks(self, world, dt):
        """敌人近战和远程攻击：根据 AI 模式决定攻击方式，管理攻击冷却。"""
        players = world.query(Transform, Collider, Health, Player)
        if not players:
            return
        p_eid = players[0]
        pt = world.get_component(p_eid, Transform)
        pc_coll = world.get_component(p_eid, Collider)
        ph = world.get_component(p_eid, Health)
        pp = world.get_component(p_eid, Player)

        enemies = world.query(Transform, Collider, Health, Combat, AI)

        for eeid in enemies:
            if eeid == p_eid:
                continue

            eh = world.get_component(eeid, Health)
            if not eh.alive:
                continue
            etc = world.get_component(eeid, Combat)
            if etc.cooldown > 0:
                etc.cooldown -= dt

            et = world.get_component(eeid, Transform)
            ai = world.get_component(eeid, AI)

            dx = pt.x - et.x
            dy = pt.y - et.y
            dist = math.sqrt(dx * dx + dy * dy)

            if ai.mode == "ranged":
                # 远程：向玩家发射子弹
                attack_range = ai.aggro_range
                if dist < attack_range and etc.cooldown <= 0:
                    etc.cooldown = 1.0 / etc.attack_speed if etc.attack_speed > 0 else 1.0
                    norm = dist if dist > 0 else 1
                    cfg = self._get_enemy_cfg(ai)
                    create_enemy_projectile(
                        world, et.x, et.y,
                        dx / norm, dy / norm,
                        cfg.get("projectile_speed", 220.0),
                        etc.damage,
                        cfg.get("projectile_color", (255, 100, 80)),
                    )
            else:
                # 近战攻击
                attack_range = ai.attack_range if ai else etc.range
                if dist < attack_range and etc.cooldown <= 0:
                    etc.cooldown = 1.0 / etc.attack_speed if etc.attack_speed > 0 else 1.0
                    dmg = max(1, etc.damage - pp.armor)
                    ph.take_damage(dmg)
                    self.event_bus.emit("PLAYER_HIT", damage=dmg, x=pt.x, y=pt.y)
                    if not ph.alive:
                        self.event_bus.emit("PLAYER_DIED", entity=p_eid)

    def _process_death_bursts(self, world):
        """检查死亡 Spriggan，对范围内玩家造成 AOE 自爆伤害。"""
        enemies = world.query(Transform, Health, AI)
        players = world.query(Transform, Health, Player)
        if not players:
            return
        p_eid = players[0]
        pt = world.get_component(p_eid, Transform)
        ph = world.get_component(p_eid, Health)
        pp = world.get_component(p_eid, Player)

        for eeid in enemies:
            eh = world.get_component(eeid, Health)
            if eh.alive:
                continue
            ai = world.get_component(eeid, AI)
            if ai is None or ai.burst_damage <= 0:
                continue
            # 每只敌人只爆发一次
            if getattr(ai, '_burst_done', False):
                continue
            ai._burst_done = True

            et = world.get_component(eeid, Transform)
            dx = pt.x - et.x
            dy = pt.y - et.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < ai.burst_radius:
                dmg = max(1, ai.burst_damage - pp.armor)
                ph.take_damage(dmg)
                self.event_bus.emit("PLAYER_HIT", damage=dmg, x=pt.x, y=pt.y)
                if not ph.alive:
                    self.event_bus.emit("PLAYER_DIED", entity=p_eid)

    def _detect_deaths(self, world):
        """检测非玩家实体死亡（来自陷阱、中毒等非直接伤害），发射 ENTITY_DIED 事件。"""

        for eid in world.query(Transform, Health):
            h = world.get_component(eid, Health)
            if h.alive:
                continue
            if world.has_component(eid, Player):
                continue
            if eid in self._tracked_deaths:
                continue
            self._tracked_deaths.add(eid)
            t = world.get_component(eid, Transform)
            self.event_bus.emit("ENTITY_DIED", entity=eid, position=(t.x, t.y))

        # 清理已销毁实体的追踪
        current_entities = set(world.entities)
        self._tracked_deaths = {eid for eid in self._tracked_deaths if eid in current_entities}

    @staticmethod
    def _get_enemy_cfg(ai):
        """占位函数 — 实际使用时从配置表查询敌人参数，此处返回默认值。"""
        return {}

    def _spawn_fragments(self, world, x, y, count, pcombat):
        """生成撞击散射碎片：在命中点向随机方向发射多枚小子弹。"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            dx = math.cos(angle)
            dy = math.sin(angle)
            create_projectile(
                world, x, y, dx, dy,
                200.0,
                max(1, pcombat.damage // 2),
                (255, 180, 80),
                max(3, 4),
                80.0,
                0,
            )
