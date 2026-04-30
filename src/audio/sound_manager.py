"""音效管理器 — mixer 初始化、预生成缓存、优先级通道抢占、WAV/OGG 覆盖。

镜像 sprite_atlas.py 的覆盖模式：assets/sounds/<key>.wav 或 .ogg 存在时优先使用外部文件，
否则使用 sound_factory.py 中的程序化生成音效。
"""

import os
import pygame
from src.audio.sound_factory import SOUND_BUILDERS, SAMPLE_RATE

# 优先级 → 通道索引分配
PRIORITY_CHANNELS = {
    "critical": (0, 1),
    "high":     (2, 3),
    "medium":   (4, 5),
    "low":      (6, 7),
}

# 事件→优先级映射
SOUND_PRIORITY: dict[str, str] = {
    "player_hit":       "critical",
    "player_died":      "critical",
    "upgrade_ready":    "critical",
    "attack_hit":       "high",
    "entity_died":      "high",
    "boss_died":        "high",
    "xp_gained":        "medium",
    "equipment_dropped": "medium",
    "pickup_collected": "medium",
    "boss_ground_slam": "medium",
    "boss_enrage":      "medium",
    "door_approached":  "low",
    "room_cleared":     "low",
    "new_room":         "low",
    "inventory_full":   "low",
}

CHANNEL_COUNT = 8
SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sounds")


class SoundManager:
    """管理所有音效的加载、缓存、播放和通道抢占。"""

    def __init__(self, master_volume: float = 0.7):
        self._cache: dict[str, pygame.mixer.Sound] = {}
        self._enabled = True

        try:
            pygame.mixer.init(SAMPLE_RATE, -16, 1, CHANNEL_COUNT)
            pygame.mixer.set_num_channels(CHANNEL_COUNT)
            self._enabled = True
        except pygame.error:
            self._enabled = False

        if self._enabled:
            self.set_master_volume(master_volume)
            self._preload_all()

    @property
    def sound_enabled(self) -> bool:
        return self._enabled

    def set_master_volume(self, vol: float):
        """设置主音量 (0.0-1.0)。"""
        if self._enabled:
            pygame.mixer.music.set_volume(vol)
            # 设置所有已分配通道的音量
            for ch_idx in range(CHANNEL_COUNT):
                ch = pygame.mixer.Channel(ch_idx)
                if ch:
                    ch.set_volume(vol)

    def play(self, key: str, volume: float = 1.0) -> pygame.mixer.Channel | None:
        """播放缓存音效。通道满时按优先级抢占低优先级通道。

        Returns:
            Channel 对象，若无可用通道则返回 None。
        """
        if not self._enabled or key not in self._cache:
            return None

        priority = SOUND_PRIORITY.get(key, "low")
        ch_range = PRIORITY_CHANNELS.get(priority, (6, 7))

        sound = self._cache[key]

        # 优先找同一优先级范围内的空闲通道
        for ch_idx in range(ch_range[0], ch_range[1] + 1):
            ch = pygame.mixer.Channel(ch_idx)
            if ch and not ch.get_busy():
                ch.set_volume(volume)
                ch.play(sound)
                return ch

        # 无空闲通道：从最低优先级开始抢占
        steal_order = ["low", "medium", "high"]
        for steal_prio in steal_order:
            steal_range = PRIORITY_CHANNELS[steal_prio]
            for ch_idx in range(steal_range[0], steal_range[1] + 1):
                ch = pygame.mixer.Channel(ch_idx)
                if ch and ch.get_busy():
                    ch.set_volume(volume)
                    ch.play(sound)
                    return ch

        # 所有通道都忙且不可抢占，静默丢弃
        return None

    def stop_all(self):
        """停止所有通道的播放。"""
        if self._enabled:
            pygame.mixer.stop()

    def _preload_all(self):
        """预生成/加载所有音效到缓存。外部 WAV/OGG 文件优先。"""
        for key, builder in SOUND_BUILDERS.items():
            custom = self._load_custom_sound(key)
            if custom is not None:
                self._cache[key] = custom
            else:
                self._cache[key] = builder()

    def _load_custom_sound(self, key: str) -> pygame.mixer.Sound | None:
        """尝试从 assets/sounds/ 加载覆盖文件（WAV 或 OGG）。"""
        for ext in (".wav", ".ogg"):
            path = os.path.join(SOUNDS_DIR, key + ext)
            if os.path.isfile(path):
                try:
                    return pygame.mixer.Sound(path)
                except pygame.error:
                    pass
        return None
