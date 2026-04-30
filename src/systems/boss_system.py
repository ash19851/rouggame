"""BossSystem —— 每帧协调 Boss 技能执行、冷却管理、移动模式覆盖和狂暴触发。

在 AI 系统之后、移动系统之前运行。
执行顺序：
  1. 检查狂暴条件（被动）
  2. 递减所有技能冷却
  3. 继续执行活跃技能或选择下一个技能
  4. 应用移动模式覆盖（hover/charge/teleport_move）
"""

import math, random
from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.motion import Motion
from src.ecs.components.health import Health
from src.ecs.components.combat import Combat
from src.ecs.components.ai import AI
from src.ecs.components.player import Player
from src.ecs.components.boss import Boss
from src.systems.boss_skills import SKILL_DISPATCH
from src.data.config_loader import SKILL_PARAMS
from src.core.event_bus import EventBus


class BossSystem(System):
    """BossSystem：管理所有 Boss 实体的技能执行、冷却和移动模式。"""

    def __init__(self, event_bus: EventBus):
        self._boss_count = 0
        self.event_bus = event_bus

    def update(self, world: World, dt: float):
        bosses = world.query(Transform, Boss, AI, Health, Combat)
        if not bosses:
            return

        players = world.query(Transform, Player, Health)
        if not players:
            return
        player_eid = players[0]
        ppt = world.get_component(player_eid, Transform)
        ph = world.get_component(player_eid, Health)
        if ppt is None or ph is None or not ph.alive:
            return

        for boss_eid in bosses:
            boss_comp = world.get_component(boss_eid, Boss)
            h = world.get_component(boss_eid, Health)
            if boss_comp is None or h is None or not h.alive:
                continue

            # 1. 检查被动狂暴技能
            if "enrage" in boss_comp.skills and not boss_comp.enraged:
                enrage_fn = SKILL_DISPATCH.get("enrage")
                if enrage_fn:
                    params = SKILL_PARAMS.get("enrage", {})
                    enrage_fn(world, boss_eid, player_eid, dt, boss_comp, params, self.event_bus)

            # 2. 递减所有技能冷却
            for sk in boss_comp.skill_cooldowns:
                if boss_comp.skill_cooldowns[sk] > 0:
                    boss_comp.skill_cooldowns[sk] -= dt

            # 3. 执行活跃技能或选择新技能
            if boss_comp.skill_active:
                fn = SKILL_DISPATCH.get(boss_comp.skill_active)
                if fn:
                    params = SKILL_PARAMS.get(boss_comp.skill_active, {})
                    still_active = fn(world, boss_eid, player_eid, dt, boss_comp, params, self.event_bus)
                    if not still_active:
                        # 技能完成，设置冷却
                        cd = params.get("cooldown", 5.0)
                        boss_comp.skill_cooldowns[boss_comp.skill_active] = cd
                        boss_comp.skill_active = ""
            else:
                ready = [sk for sk in boss_comp.skills
                         if sk != "enrage" and boss_comp.skill_cooldowns.get(sk, 0) <= 0]
                if ready:
                    # 加权随机：dash 权重最高，地面技权重中等，召唤/分裂权重较低
                    chosen = self._pick_skill(ready)
                    boss_comp.skill_active = chosen
                    fn = SKILL_DISPATCH.get(chosen)
                    if fn:
                        params = SKILL_PARAMS.get(chosen, {})
                        fn(world, boss_eid, player_eid, dt, boss_comp, params, self.event_bus)

            # 4. 移动模式覆盖
            self._apply_movement(world, boss_eid, player_eid, dt, boss_comp)

    def _pick_skill(self, ready: list[str]) -> str:
        """加权随机选择一个就绪技能。dash/slam 权重高，split/summon 权重低。"""
        weights = {
            "dash_charge": 4,
            "ground_slam": 3,
            "projectile_barrage": 3,
            "knockback_wind": 2,
            "teleport": 2,
            "split_self": 1,
            "summon_minions": 1,
        }
        ws = [weights.get(sk, 2) for sk in ready]
        return random.choices(ready, weights=ws, k=1)[0]

    def _apply_movement(self, world: World, boss_eid: int, player_eid: int,
                        dt: float, boss_comp: Boss):
        """根据移动模式覆盖 Motion 行为。"""
        ai = world.get_component(boss_eid, AI)
        mot = world.get_component(boss_eid, Motion)
        pt = world.get_component(boss_eid, Transform)
        ppt = world.get_component(player_eid, Transform)
        if ai is None or mot is None or pt is None or ppt is None:
            return

        mode = boss_comp.movement_mode

        if mode == "hover":
            # 不覆盖，仅标记跳过墙壁碰撞（在 collision_system 中处理）
            pass

        elif mode == "charge":
            # 每 4 秒锁定方向加速 0.5 秒
            cd_key = "charge_move"
            if cd_key not in boss_comp.skill_cooldowns:
                boss_comp.skill_cooldowns[cd_key] = 0
            boss_comp.skill_cooldowns[cd_key] -= dt
            if boss_comp.skill_cooldowns[cd_key] <= 0:
                dx = ppt.x - pt.x
                dy = ppt.y - pt.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    boss_comp.charge_dir_x = dx / dist
                    boss_comp.charge_dir_y = dy / dist
                boss_comp.skill_cooldowns[cd_key] = random.uniform(3.0, 5.0)
                boss_comp.skill_timer = 0.5
            if boss_comp.skill_timer > 0:
                mot.vx = boss_comp.charge_dir_x * mot.speed * 2.0
                mot.vy = boss_comp.charge_dir_y * mot.speed * 2.0
                boss_comp.skill_timer -= dt

        elif mode == "teleport_move":
            # 每 3 秒短距瞬移
            cd_key = "tp_move"
            if cd_key not in boss_comp.skill_cooldowns:
                boss_comp.skill_cooldowns[cd_key] = 0
            boss_comp.skill_cooldowns[cd_key] -= dt
            if boss_comp.skill_cooldowns[cd_key] <= 0:
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(60, 120)
                pt.x = ppt.x + math.cos(angle) * dist
                pt.y = ppt.y + math.sin(angle) * dist
                boss_comp.skill_cooldowns[cd_key] = random.uniform(2.5, 4.0)
                from src.entities.particle_factory import emit_burst
                emit_burst(world, pt.x, pt.y, 6, (180, 130, 255), speed=50.0, lifetime=0.2)
