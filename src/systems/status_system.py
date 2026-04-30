"""状态效果系统 — 管理实体身上的 buff/debuff 效果，如中毒、减速等。

支持效果:
  - poison: 周期性扣血，达 tick 次数后移除
  - slow:   持续减速，到期恢复原速度
"""

from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.status_effect import StatusEffect
from src.ecs.components.health import Health
from src.ecs.components.motion import Motion
from src.ecs.components.player import Player


class StatusSystem(System):
    """状态效果系统：每帧更新所有效果计时器，处理中毒扣血和减速恢复。"""

    def update(self, world: World, dt: float):
        """遍历所有带 StatusEffect 的实体，更新效果计时并应用伤害/减速。"""
        for eid in world.query(StatusEffect):
            se = world.get_component(eid, StatusEffect)
            if not se.effects:
                continue

            health = world.get_component(eid, Health)
            motion = world.get_component(eid, Motion)
            is_player = world.has_component(eid, Player)

            expired = []
            for i, eff in enumerate(se.effects):
                eff["tick_timer"] -= dt
                eff["duration"] -= dt

                if eff["duration"] <= 0:
                    # 持续时间到期：减速效果需恢复原速度
                    if eff["type"] == "slow" and motion is not None:
                        motion.speed /= eff.get("slow_pct", 0.5)
                    expired.append(i)
                    continue

                # tick 判定：中毒效果每个 tick 扣血一次
                if eff["tick_timer"] <= 0 and eff["remaining_ticks"] > 0:
                    eff["tick_timer"] = eff["tick_interval"]  # 重置 tick 计时
                    eff["remaining_ticks"] -= 1
                    if eff["type"] == "poison" and health is not None:
                        # 玩家至少保留 1 点血，其他实体可致死
                        floor = 1 if is_player else 0
                        health.current = max(floor, health.current - eff.get("damage", 3))

                if eff["remaining_ticks"] <= 0 and eff["type"] == "poison":
                    expired.append(i)

            # 倒序移除过期效果，避免索引错乱
            for i in reversed(expired):
                se.effects.pop(i)
