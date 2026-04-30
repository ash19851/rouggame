"""音效系统 — 订阅 EventBus 事件，映射到音效键并通过 SoundManager 播放。

镜像 ParticleSystem 的订阅模式：在 __init__ 中注册所有事件回调，
游戏运行时仅做音效键查找和播放。
"""

from src.ecs.system import System
from src.ecs.world import World
from src.core.event_bus import EventBus
from src.audio.sound_manager import SoundManager

# 事件类型 → (sound_key, volume_multiplier) 映射
EVENT_SOUND_MAP: dict[str, tuple[str, float]] = {
    "ATTACK_HIT":        ("attack_hit",        0.8),
    "ENTITY_DIED":       ("entity_died",        1.0),
    "PLAYER_HIT":        ("player_hit",         1.0),
    "PLAYER_DIED":       ("player_died",        1.0),
    "XP_GAINED":         ("xp_gained",          0.7),
    "EQUIPMENT_DROPPED": ("equipment_dropped",  1.0),
    "PICKUP_COLLECTED":  ("pickup_collected",   0.8),
    "UPGRADE_READY":     ("upgrade_ready",      1.0),
    "DOOR_APPROACHED":   ("door_approached",    1.0),
    "ROOM_CLEARED":      ("room_cleared",       0.9),
    "NEW_ROOM":          ("new_room",           0.8),
    "BOSS_DIED":         ("boss_died",          1.0),
    "BOSS_GROUND_SLAM":  ("boss_ground_slam",   1.0),
    "BOSS_ENRAGE":       ("boss_enrage",        1.0),
    "INVENTORY_FULL":    ("inventory_full",     1.0),
}


class SoundSystem(System):
    """音效系统：桥接 EventBus 事件到 SoundManager 播放。"""

    def __init__(self, event_bus: EventBus, sound_manager: SoundManager):
        self.event_bus = event_bus
        self.sound_manager = sound_manager
        for event_type in EVENT_SOUND_MAP:
            self.event_bus.subscribe(event_type, self._on_event)

    def update(self, world: World, dt: float):
        """SoundSystem 无需每帧更新 — 所有逻辑由事件回调驱动。"""
        pass

    def _on_event(self, event_type: str, data: dict):
        """事件回调：查找音效键并播放。"""
        mapping = EVENT_SOUND_MAP.get(event_type)
        if mapping is None:
            return
        sound_key, volume = mapping
        self.sound_manager.play(sound_key, volume)

    def shutdown(self):
        """取消所有事件订阅。"""
        for event_type in EVENT_SOUND_MAP:
            self.event_bus.unsubscribe(event_type, self._on_event)
