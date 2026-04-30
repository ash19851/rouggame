"""粒子系统 — 管理粒子特效的生成、老化和销毁。

监听事件触发粒子爆发:
  - ENTITY_DIED:  敌人死亡爆发
  - ATTACK_HIT:   攻击命中火花
  - PLAYER_HIT:   玩家受伤效果
  - UPGRADE_READY: 升级特效
"""

from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.particle import Particle
from src.ecs.components.render import Sprite
from src.core.event_bus import EventBus
from src.entities.particle_factory import emit_burst


class ParticleSystem(System):
    """粒子系统：监听游戏事件生成粒子爆发，管理粒子生命周期。"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        event_bus.subscribe("ENTITY_DIED", self._on_entity_died)
        event_bus.subscribe("ATTACK_HIT", self._on_attack_hit)
        event_bus.subscribe("PLAYER_HIT", self._on_player_hit)
        event_bus.subscribe("UPGRADE_READY", self._on_upgrade)
        self._pending_bursts: list[dict] = []

    def _on_entity_died(self, event_type: str, data: dict):
        """敌人死亡回调：生成死亡爆发粒子（带重力下落感）。"""
        self._pending_bursts.append({
            "x": data["position"][0],
            "y": data["position"][1],
            "color": (200, 180, 150),
            "count": 14,
            "speed": 150.0,
            "lifetime": 0.35,
            "size": 3.0,
            "gravity": 60.0,
        })

    def _on_attack_hit(self, event_type: str, data: dict):
        """攻击命中回调：生成命中火花 + 余烬粒子。"""
        self._pending_bursts.append({
            "x": data.get("x", 0),
            "y": data.get("y", 0),
            "color": (255, 255, 200),
            "count": 6,
            "speed": 60.0,
            "lifetime": 0.2,
            "size": 2.0,
        })

    def _on_player_hit(self, event_type: str, data: dict):
        """玩家受伤回调：生成红色血溅粒子（带重力）。"""
        self._pending_bursts.append({
            "x": data.get("x", 0),
            "y": data.get("y", 0),
            "color": (255, 80, 80),
            "count": 10,
            "speed": 90.0,
            "lifetime": 0.25,
            "size": 3.0,
            "gravity": 80.0,
        })

    def _on_upgrade(self, event_type: str, data: dict):
        """升级回调：由游戏场景处理（需要知道玩家位置）。"""
        pass

    def update(self, world: World, dt: float):
        """每帧处理待生成的粒子爆发，并更新所有粒子的生命周期。"""
        # 刷新待处理的粒子爆发
        for burst in self._pending_bursts:
            emit_burst(world, **burst)
        self._pending_bursts.clear()

        # 老化并移除过期粒子
        particles = world.query(Transform, Particle)
        for eid in particles:
            p = world.get_component(eid, Particle)
            s = world.get_component(eid, Sprite)

            p.age += dt

            # 粒子过期则销毁
            if p.age >= p.lifetime:
                world.destroy_entity(eid)
                continue

            # 粒子缩小效果：随生命进度缩小
            if p.shrink and s:
                scale = max(0.1, 1.0 - p.age / p.lifetime)
                s.width = int(p.size * 2 * scale)
                s.height = int(p.size * 2 * scale)

    def emit_upgrade_burst(self, world: World, x: float, y: float):
        """生成升级特效粒子爆发（金色外环 + 高速内环）。"""
        emit_burst(world, x, y, count=16, color=(255, 215, 0), speed=150.0, lifetime=0.5, size=4.0)
        emit_burst(world, x, y, count=8, color=(255, 240, 100), speed=200.0, lifetime=0.3, size=3.0)
