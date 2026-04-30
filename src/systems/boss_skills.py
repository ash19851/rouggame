"""Boss 技能模块 —— 8 个独立技能函数 + 调度表。

每个技能函数签名:
    skill_xxx(world, boss_eid, player_eid, dt, boss_comp, params, event_bus=None) -> bool
    返回 True 表示技能仍在执行（阻塞），False 表示完成。

params 字典来自 SKILL_PARAMS 配置，包含 cooldown/duration/damage 等参数。
"""

import math, random
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.motion import Motion
from src.ecs.components.health import Health
from src.ecs.components.combat import Combat
from src.ecs.components.ai import AI
from src.ecs.components.boss import Boss, BossMinion
from src.ecs.components.render import Sprite
from src.ecs.components.collision import Collider
from src.entities.enemy_projectile_factory import create_enemy_projectile
from src.entities.particle_factory import emit_burst
from src.data.config_loader import ENEMIES, SKILL_PARAMS


# ── 辅助 ────────────────────────────────────────────────────────────────────

def _get_player(world: World) -> int | None:
    """查找玩家实体 ID，不存在或已死亡则返回 None。"""
    from src.ecs.components.player import Player
    players = world.query(Transform, Player, Health)
    return players[0] if players else None


def _distance(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(bx - ax, by - ay)


# ── 技能 1: 冲刺 ────────────────────────────────────────────────────────────

def skill_dash_charge(world: World, boss_eid: int, player_eid: int,
                      dt: float, boss_comp: Boss, params: dict, event_bus=None) -> bool:
    """高速冲刺：暂时将 AI 模式切换为 dash，用 Boss 参数覆盖默认冲刺配置。"""
    ai = world.get_component(boss_eid, AI)
    if ai is None:
        return False

    # 初始化冲刺
    if boss_comp.skill_timer <= 0:
        pt = world.get_component(boss_eid, Transform)
        ppt = world.get_component(player_eid, Transform)
        if pt is None or ppt is None:
            return False
        dx = ppt.x - pt.x
        dy = ppt.y - pt.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            ai.dash_dir_x = dx / dist
            ai.dash_dir_y = dy / dist
        ai.mode = "dash"
        ai.dash_speed_mult = params.get("speed_mult", 3.5)
        ai.dash_duration = params.get("duration", 0.4)
        ai.dash_timer = 0  # 立即触发冲刺
        boss_comp.skill_timer = params.get("duration", 0.4)
        return True

    # 冲刺持续中
    boss_comp.skill_timer -= dt
    if boss_comp.skill_timer > 0:
        return True

    # 冲刺结束，恢复 chase 模式
    ai.mode = "chase"
    ai.dash_speed_mult = 3.0  # 恢复默认
    return False


# ── 技能 2: 分裂 ────────────────────────────────────────────────────────────

def skill_split_self(world: World, boss_eid: int, player_eid: int,
                     dt: float, boss_comp: Boss, params: dict, event_bus=None) -> bool:
    """分裂成多个小克隆体，Boss 短暂无敌。"""
    pt = world.get_component(boss_eid, Transform)
    h = world.get_component(boss_eid, Health)
    c = world.get_component(boss_eid, Combat)
    spr = world.get_component(boss_eid, Sprite)
    if pt is None or h is None or c is None:
        return False

    # 初始化：Boss 无敌 + 生成克隆
    if boss_comp.skill_timer <= 0:
        h.invuln_time = 0.3
        clone_count = params.get("clone_count", 2)
        hp_ratio = params.get("clone_hp_ratio", 0.15)
        dmg_ratio = params.get("clone_dmg_ratio", 0.3)

        import pygame
        for i in range(clone_count):
            angle = (i / clone_count) * 2 * math.pi
            cx = pt.x + math.cos(angle) * 40
            cy = pt.y + math.sin(angle) * 40
            ceid = world.create_entity(tag="boss_minion")
            world.add_component(ceid, Transform(x=cx, y=cy))
            # 克隆体用缩小版精灵
            clone_size = int(spr.width * 0.6), int(spr.height * 0.6)
            clone_surf = None
            if spr.surface:
                clone_surf = pygame.transform.scale(
                    spr.surface, (max(1, clone_size[0]), max(1, clone_size[1])))
            world.add_component(ceid, Sprite(
                surface=clone_surf, color=spr.color,
                width=clone_size[0], height=clone_size[1], layer=4,
            ))
            mot = world.get_component(boss_eid, Motion)
            clone_speed = mot.speed * 0.8 if mot else 60.0
            world.add_component(ceid, Motion(speed=clone_speed))
            world.add_component(ceid, Collider(width=clone_size[0], height=clone_size[1], layer=1))
            world.add_component(ceid, Health(
                current=int(h.max * hp_ratio), max=int(h.max * hp_ratio),
            ))
            world.add_component(ceid, Combat(
                damage=int(c.damage * dmg_ratio), attack_speed=0.8, range=25.0, cooldown=0.0,
            ))
            world.add_component(ceid, AI(mode="chase", aggro_range=250.0, attack_range=25.0))
            world.add_component(ceid, BossMinion(parent_boss_eid=boss_eid))

            emit_burst(world, cx, cy, 8, spr.color, speed=40.0, lifetime=0.3, size=2.0)

        boss_comp.skill_timer = 0.4
        return True

    # 等待无敌帧结束
    boss_comp.skill_timer -= dt
    return boss_comp.skill_timer > 0


# ── 技能 3: 吹飞 ────────────────────────────────────────────────────────────

def skill_knockback_wind(world: World, boss_eid: int, player_eid: int,
                         dt: float, boss_comp: Boss, params: dict, event_bus=None) -> bool:
    """将玩家沿 Boss→玩家方向吹飞，施加推力 + 风粒子。"""
    pt = world.get_component(boss_eid, Transform)
    ppt = world.get_component(player_eid, Transform)
    pmot = world.get_component(player_eid, Motion)
    if pt is None or ppt is None or pmot is None:
        return False

    if boss_comp.skill_timer <= 0:
        dx = ppt.x - pt.x
        dy = ppt.y - pt.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            force = params.get("force", 300.0)
            pmot.vx = (dx / dist) * force
            pmot.vy = (dy / dist) * force
        duration = params.get("duration", 0.5)
        boss_comp.skill_timer = duration
        # 风粒子
        emit_burst(world, pt.x, pt.y, 12, (200, 220, 255), speed=120.0, lifetime=0.4, size=2.5)
        return True

    # 推力持续期间逐渐衰减
    boss_comp.skill_timer -= dt
    if boss_comp.skill_timer <= 0:
        pmot.vx = 0
        pmot.vy = 0
    return boss_comp.skill_timer > 0


# ── 技能 4: 召唤小怪 ────────────────────────────────────────────────────────

def skill_summon_minions(world: World, boss_eid: int, player_eid: int,
                         dt: float, boss_comp: Boss, params: dict, event_bus=None) -> bool:
    """在 Boss 周围召唤当前怪物池的小怪。"""
    pt = world.get_component(boss_eid, Transform)
    if pt is None:
        return False

    count = params.get("count", 3)
    spread = params.get("spread_radius", 80.0)
    # 从敌人配置中随机选择类型
    enemy_types = list(ENEMIES.keys()) if ENEMIES else ["skeleton", "slime"]

    from src.entities.enemy_factory import create_enemy
    for i in range(count):
        angle = (i / count) * 2 * math.pi + random.uniform(-0.2, 0.2)
        sx = pt.x + math.cos(angle) * spread
        sy = pt.y + math.sin(angle) * spread
        etype = random.choice(enemy_types)
        create_enemy(world, etype, sx, sy, stage_mult=1.0)

    emit_burst(world, pt.x, pt.y, 10, (150, 100, 200), speed=60.0, lifetime=0.35, size=3.0)
    # 一次性技能
    return False


# ── 技能 5: 弹幕 ────────────────────────────────────────────────────────────

def skill_projectile_barrage(world: World, boss_eid: int, player_eid: int,
                             dt: float, boss_comp: Boss, params: dict, event_bus=None) -> bool:
    """环形弹幕：发射 burst_count 枚弹丸，每 wave_interval 秒一波，共 waves 波。"""
    pt = world.get_component(boss_eid, Transform)
    c = world.get_component(boss_eid, Combat)
    if pt is None or c is None:
        return False

    burst_count = params.get("burst_count", 12)
    waves = params.get("waves", 3)
    proj_speed = params.get("proj_speed", 180.0)
    dmg_ratio = params.get("proj_dmg_ratio", 0.5)
    wave_interval = 0.15

    # 使用内部计数器追踪当前波次
    if boss_comp.skill_timer <= 0:
        boss_comp.skill_timer = waves * wave_interval
        # 用 charge 方向字段存波次计数
        boss_comp.charge_dir_x = 0
        boss_comp.charge_dir_y = 0  # 上次发射时间

    # 检查是否该发射新一波
    elapsed = (waves * wave_interval) - boss_comp.skill_timer
    wave_index = int(boss_comp.charge_dir_x)
    expected_wave_time = wave_index * wave_interval

    if elapsed >= expected_wave_time and wave_index < waves:
        boss_comp.charge_dir_x = wave_index + 1
        # 每波偏移角度
        offset = wave_index * (math.pi / burst_count / waves)
        for i in range(burst_count):
            angle = offset + (i / burst_count) * 2 * math.pi
            dx = math.cos(angle)
            dy = math.sin(angle)
            create_enemy_projectile(
                world, pt.x, pt.y, dx, dy, proj_speed,
                max(1, int(c.damage * dmg_ratio)),
                color=(200, 100, 220), size=5.0,
            )

    boss_comp.skill_timer -= dt
    if boss_comp.skill_timer <= 0:
        boss_comp.charge_dir_x = 0
        boss_comp.charge_dir_y = 0
        return False
    return True


# ── 技能 6: 地震 ────────────────────────────────────────────────────────────

def skill_ground_slam(world: World, boss_eid: int, player_eid: int,
                      dt: float, boss_comp: Boss, params: dict, event_bus=None) -> bool:
    """蓄力后对周围造成 AoE 伤害，对玩家造成额外击退。"""
    pt = world.get_component(boss_eid, Transform)
    c = world.get_component(boss_eid, Combat)
    ppt = world.get_component(player_eid, Transform)
    ph = world.get_component(player_eid, Health)
    pmot = world.get_component(player_eid, Motion)
    if pt is None or c is None:
        return False

    windup = params.get("windup", 0.4)
    slam_radius = params.get("slam_radius", 90.0)
    slam_mult = params.get("slam_mult", 1.5)

    if boss_comp.skill_timer <= 0:
        boss_comp.skill_timer = windup
        boss_comp.charge_dir_x = 0  # 标记: 0=蓄力中
        return True

    # 蓄力阶段
    if boss_comp.charge_dir_x == 0:
        boss_comp.skill_timer -= dt
        if boss_comp.skill_timer <= 0:
            # 触发地震
            boss_comp.charge_dir_x = 1
            boss_comp.skill_timer = 0.3  # 后摇
            if event_bus:
                event_bus.emit("BOSS_GROUND_SLAM", x=pt.x, y=pt.y, radius=slam_radius)
            # AoE 伤害
            if ppt is not None and ph is not None:
                dist = _distance(pt.x, pt.y, ppt.x, ppt.y)
                if dist < slam_radius:
                    dmg = max(1, int(c.damage * slam_mult))
                    ph.current = max(0, ph.current - dmg)
                    if ph.current <= 0:
                        ph.alive = False
                    # 击退
                    if pmot:
                        dx = ppt.x - pt.x
                        dy = ppt.y - pt.y
                        d = math.hypot(dx, dy)
                        if d > 0:
                            pmot.vx = (dx / d) * 200
                            pmot.vy = (dy / d) * 200
            # 冲击波粒子环
            for i in range(30):
                angle = (i / 30) * 2 * math.pi
                emit_burst(world,
                          pt.x + math.cos(angle) * 10,
                          pt.y + math.sin(angle) * 10,
                          2, (255, 200, 100), speed=80.0, lifetime=0.5, size=4.0)
        return True

    # 后摇
    boss_comp.skill_timer -= dt
    if boss_comp.skill_timer <= 0:
        boss_comp.charge_dir_x = 0
        return False
    return True


# ── 技能 7: 瞬移 ────────────────────────────────────────────────────────────

def skill_teleport(world: World, boss_eid: int, player_eid: int,
                   dt: float, boss_comp: Boss, params: dict, event_bus=None) -> bool:
    """瞬移到玩家附近指定范围内的随机位置。"""
    pt = world.get_component(boss_eid, Transform)
    ppt = world.get_component(player_eid, Transform)
    h = world.get_component(boss_eid, Health)
    if pt is None or ppt is None:
        return False

    min_dist = params.get("min_dist", 80.0)
    max_dist = params.get("max_dist", 150.0)

    if boss_comp.skill_timer <= 0:
        # 留离开粒子
        emit_burst(world, pt.x, pt.y, 10, (180, 130, 255), speed=50.0, lifetime=0.25, size=3.0)
        # 随机目标位置
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(min_dist, max_dist)
        pt.x = ppt.x + math.cos(angle) * dist
        pt.y = ppt.y + math.sin(angle) * dist
        # 到达粒子
        emit_burst(world, pt.x, pt.y, 10, (180, 130, 255), speed=60.0, lifetime=0.3, size=3.5)
        # 短暂无敌
        if h:
            h.invuln_time = 0.2
        return False

    return True


# ── 技能 8: 狂暴（被动）──────────────────────────────────────────────────────

def skill_enrage(world: World, boss_eid: int, player_eid: int,
                 dt: float, boss_comp: Boss, params: dict, event_bus=None) -> bool:
    """被动触发：血量低于阈值后提升速度和伤害，改变色调。"""
    h = world.get_component(boss_eid, Health)
    c = world.get_component(boss_eid, Combat)
    mot = world.get_component(boss_eid, Motion)
    spr = world.get_component(boss_eid, Sprite)
    if h is None or c is None:
        return False

    # 仅在未狂暴且血量低于阈值时触发
    if not boss_comp.enraged and h.fraction <= boss_comp.enrage_threshold:
        boss_comp.enraged = True
        if event_bus:
            event_bus.emit("BOSS_ENRAGE", entity=boss_eid)
        speed_mult = params.get("speed_mult", 1.5)
        dmg_mult = params.get("dmg_mult", 1.5)
        if mot:
            mot.speed *= speed_mult
        c.damage = int(c.damage * dmg_mult)
        # 色调变红
        if spr:
            spr.color = (max(60, spr.color[0] + 60),
                         max(20, spr.color[1] - 30),
                         max(20, spr.color[2] - 30))
        # 狂暴粒子
        pt = world.get_component(boss_eid, Transform)
        if pt:
            emit_burst(world, pt.x, pt.y, 20, (255, 60, 30), speed=100.0, lifetime=0.6, size=4.0)
    return False  # 被动技能不阻塞


# ── 调度表 ───────────────────────────────────────────────────────────────────

SKILL_DISPATCH = {
    "dash_charge": skill_dash_charge,
    "split_self": skill_split_self,
    "knockback_wind": skill_knockback_wind,
    "summon_minions": skill_summon_minions,
    "projectile_barrage": skill_projectile_barrage,
    "ground_slam": skill_ground_slam,
    "teleport": skill_teleport,
    "enrage": skill_enrage,
}
