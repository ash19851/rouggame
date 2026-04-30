"""AI 行为系统 — 驱动敌人的追逐、巡逻、远程、冲刺等 AI 模式。

支持的 AI 模式:
  - chase:  追击玩家，接近后攻击
  - patrol: 随机巡逻，发现玩家后转为追击
  - ranged: 保持最佳距离，太近后撤、太远前进、适中时横移
  - dash:   间歇性高速冲刺，冲完后冷却
"""

import math, random
from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.motion import Motion
from src.ecs.components.ai import AI
from src.ecs.components.player import Player
from src.ecs.components.health import Health
from src.ecs.components.combat import Combat


class AISystem(System):
    """AI 系统：每帧根据 AI 模式更新敌人的移动速度，实现不同的行为策略。"""

    def update(self, world: World, dt: float):
        players = world.query(Transform, Player, Health)
        if not players:
            return

        player_eid = players[0]
        pt = world.get_component(player_eid, Transform)
        ph = world.get_component(player_eid, Health)
        if not ph.alive:
            return

        enemies = world.query(Transform, Motion, AI)

        for eid in enemies:
            et = world.get_component(eid, Transform)
            em = world.get_component(eid, Motion)
            ai = world.get_component(eid, AI)

            # 计算敌人到玩家的方向与距离
            dx = pt.x - et.x
            dy = pt.y - et.y
            dist = math.sqrt(dx * dx + dy * dy)

            if ai.mode == "chase":
                self._do_chase(ai, em, dx, dy, dist, dt)

            elif ai.mode == "patrol":
                self._do_patrol(ai, em, dx, dy, dist, dt)

            elif ai.mode == "ranged":
                self._do_ranged(ai, em, dx, dy, dist, dt)

            elif ai.mode == "dash":
                self._do_dash(ai, em, dx, dy, dist, dt)

    def _do_chase(self, ai, em, dx, dy, dist, dt):
        """追逐模式：在仇恨范围内向玩家移动，进入攻击范围后减速。"""
        if dist < ai.aggro_range:
            if dist > ai.attack_range:
                em.vx = (dx / dist) * em.speed
                em.vy = (dy / dist) * em.speed
            else:
                em.vx *= 0.3
                em.vy *= 0.3
        else:
            self._wander(ai, em, dt, speed_pct=0.3)

    def _do_patrol(self, ai, em, dx, dy, dist, dt):
        """巡逻模式：随机方向漫步，发现玩家后切换为追逐。"""
        ai.patrol_timer -= dt
        if ai.patrol_timer <= 0:
            ai.patrol_timer = random.uniform(2.0, 4.0)
            angle = random.uniform(0, 2 * math.pi)
            ai.patrol_dir_x = math.cos(angle)
            ai.patrol_dir_y = math.sin(angle)
        em.vx = ai.patrol_dir_x * em.speed * 0.4
        em.vy = ai.patrol_dir_y * em.speed * 0.4

        if dist < ai.aggro_range:
            ai.mode = "chase"

    def _do_ranged(self, ai, em, dx, dy, dist, dt):
        """远程模式：保持最佳射击距离，太近后撤、太远逼近、适中横移。"""
        if dist > ai.aggro_range:
            self._wander(ai, em, dt, speed_pct=0.3)
            return

        norm_x = dx / dist if dist > 0 else 0
        norm_y = dy / dist if dist > 0 else 0

        if dist < ai.preferred_range * 0.7:
            # Too close, retreat
            em.vx = -norm_x * em.speed
            em.vy = -norm_y * em.speed
        elif dist > ai.preferred_range * 1.3:
            # Too far, advance
            em.vx = norm_x * em.speed * 0.7
            em.vy = norm_y * em.speed * 0.7
        else:
            # In sweet spot, strafe slowly
            em.vx = -norm_y * em.speed * 0.2
            em.vy = norm_x * em.speed * 0.2

    def _do_dash(self, ai, em, dx, dy, dist, dt):
        """冲刺模式：间歇性高速冲向玩家，冲完后冷却。"""
        ai.dash_timer -= dt

        if dist > ai.aggro_range:
            self._wander(ai, em, dt, speed_pct=0.3)
            return

        # 冲刺冷却中，执行普通追逐行为
        if ai.dash_timer > 0:
            if dist > ai.attack_range:
                em.vx = (dx / dist) * em.speed
                em.vy = (dy / dist) * em.speed
            else:
                em.vx *= 0.3
                em.vy *= 0.3
        else:
            # 触发冲刺，记录方向和持续时间
            ai.dash_timer = ai.dash_cooldown
            ai.dash_dir_x = dx / dist if dist > 0 else 1
            ai.dash_dir_y = dy / dist if dist > 0 else 0
            ai._dash_remaining = ai.dash_duration

        # 应用冲刺速度爆发
        remaining = getattr(ai, '_dash_remaining', 0.0)
        if remaining > 0:
            remaining -= dt
            ai._dash_remaining = remaining
            dash_speed = em.speed * ai.dash_speed_mult
            em.vx = ai.dash_dir_x * dash_speed
            em.vy = ai.dash_dir_y * dash_speed

    def _wander(self, ai, em, dt, speed_pct: float = 0.3):
        """漫游行为：随机方向低速移动，用于非战斗状态的闲逛。"""
        ai.patrol_timer -= dt
        if ai.patrol_timer <= 0:
            ai.patrol_timer = random.uniform(1.0, 3.0)
            angle = random.uniform(0, 2 * math.pi)
            ai.patrol_dir_x = math.cos(angle)
            ai.patrol_dir_y = math.sin(angle)
        em.vx = ai.patrol_dir_x * em.speed * speed_pct
        em.vy = ai.patrol_dir_y * em.speed * speed_pct
