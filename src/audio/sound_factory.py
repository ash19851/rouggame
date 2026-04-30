"""程序化音效工厂 —— 波形原语 + 17 种音效生成函数。

使用 struct.pack 生成 16-bit signed PCM，通过 pygame.mixer.Sound(buffer=bytes) 创建 Sound。
全部音效在初始化时预生成，游戏运行时不再产生音频计算开销。
"""

import struct
import random as _random
import math
from typing import Callable

import pygame

SAMPLE_RATE = 22050  # Hz
MAX_AMP = 28000      # 峰值振幅（留余量防止削波）


# ── 波形原语 ────────────────────────────────────────────────────────────────

def _square(t: float, freq: float, duty: float = 0.5) -> float:
    """方波，duty 为占空比 (0-1)。"""
    phase = (t * freq) % 1.0
    return 1.0 if phase < duty else -1.0


def _triangle(t: float, freq: float) -> float:
    """三角波，音色柔和。"""
    phase = (t * freq) % 1.0
    if phase < 0.25:
        return phase * 4.0
    elif phase < 0.75:
        return 2.0 - phase * 4.0
    else:
        return phase * 4.0 - 4.0


def _sine(t: float, freq: float) -> float:
    """纯正弦波。"""
    return math.sin(2.0 * math.pi * freq * t)


def _noise() -> float:
    """白噪声采样 (-1.0 到 1.0)。"""
    return _random.uniform(-1.0, 1.0)


def _adsr(t: float, attack: float, decay: float, sustain: float,
          release: float, total_dur: float) -> float:
    """ADSR 包络，返回 0.0-1.0 的乘数。"""
    if t < attack:
        return t / attack
    elif t < attack + decay:
        p = (t - attack) / decay
        return 1.0 - (1.0 - sustain) * p
    elif t < total_dur - release:
        return sustain
    elif t < total_dur:
        p = (t - (total_dur - release)) / release
        return sustain * (1.0 - p)
    return 0.0


# ── 构建工具 ────────────────────────────────────────────────────────────────

def _build_sound(duration: float, generator: Callable[[float], float]) -> pygame.mixer.Sound:
    """从采样生成器函数构建 pygame Sound。

    Args:
        duration: 音效时长（秒）
        generator: 接收时间 t（秒），返回 -1.0 到 1.0 的采样值
    """
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        val = generator(t)
        # 限幅
        val = max(-1.0, min(1.0, val))
        samples.append(int(val * MAX_AMP))
    raw = struct.pack(f"<{len(samples)}h", *samples)
    return pygame.mixer.Sound(buffer=raw)


def _mix(*generators: Callable[[float], float]) -> Callable[[float], float]:
    """混合多个采样生成器（等权叠加后归一化）。"""
    n = len(generators)
    def combined(t: float) -> float:
        return sum(g(t) for g in generators) / n
    return combined


# ── 音效生成函数 (17 个) ─────────────────────────────────────────────────────

def make_attack_hit() -> pygame.mixer.Sound:
    """子弹命中音效：噪声+1800Hz 方波，快速衰减 (80ms)。"""
    dur = 0.08
    def gen(t: float):
        env = _adsr(t, 0.0, 0.08, 0.0, 0.0, dur)
        return env * (_noise() * 0.6 + _square(t, 1800, 0.5) * 0.4)
    return _build_sound(dur, gen)


def make_entity_died() -> pygame.mixer.Sound:
    """敌人死亡音效：400→60Hz 三角波下滑音 (300ms)。"""
    dur = 0.30
    def gen(t: float):
        env = _adsr(t, 0.005, 0.05, 0.7, 0.15, dur)
        freq = 400.0 - (340.0 * t / dur)  # 400→60Hz
        return env * _triangle(t, freq)
    return _build_sound(dur, gen)


def make_player_hit() -> pygame.mixer.Sound:
    """玩家受伤音效：120Hz 方波+振幅颤音+噪声冲击 (200ms)。"""
    dur = 0.20
    def gen(t: float):
        env = _adsr(t, 0.0, 0.1, 0.3, 0.1, dur)
        wobble = 1.0 + 0.3 * _sine(t, 30.0)  # 30Hz 振幅颤音
        tone = _square(t, 120.0, 0.5) * wobble
        noise_part = _noise() * max(0, 1.0 - t / 0.05)  # 前 50ms 噪声冲击
        return env * (tone * 0.7 + noise_part * 0.3)
    return _build_sound(dur, gen)


def make_player_died() -> pygame.mixer.Sound:
    """玩家死亡音效：低频三角波+下滑音+噪声爆发 (600ms)。"""
    dur = 0.60
    def gen(t: float):
        env = _adsr(t, 0.01, 0.4, 0.5, 0.2, dur)
        # 80Hz 三角波低频
        bass = _triangle(t, 80.0)
        # 300→40Hz 下滑音
        freq = 300.0 - (260.0 * t / dur)
        slide = _triangle(t, max(10, freq))
        # 前 100ms 噪声爆发
        noise_part = _noise() * max(0, 1.0 - t / 0.1)
        return env * (bass * 0.4 + slide * 0.4 + noise_part * 0.2)
    return _build_sound(dur, gen)


def make_xp_gained() -> pygame.mixer.Sound:
    """经验拾取音效：600→1200Hz 双音上升叮咚 (100ms)。"""
    dur = 0.10
    def gen(t: float):
        if t < 0.05:
            env = max(0, 1.0 - t / 0.05)
            freq = 600.0 + (t / 0.05) * 100.0  # 600→700Hz
        else:
            t2 = t - 0.05
            env = max(0, 1.0 - t2 / 0.05)
            freq = 1000.0 + (t2 / 0.05) * 200.0  # 1000→1200Hz
        return env * _triangle(t, freq)
    return _build_sound(dur, gen)


def make_equipment_dropped() -> pygame.mixer.Sound:
    """装备拾取音效：C5-E5-G5 三音上行琶音 (150ms)。"""
    dur = 0.15
    notes = [523.0, 659.0, 784.0]  # C5, E5, G5
    note_len = dur / len(notes)
    def gen(t: float):
        idx = min(int(t / note_len), len(notes) - 1)
        freq = notes[idx]
        local_t = t - idx * note_len
        env = max(0, 1.0 - local_t / (note_len * 0.8))
        return env * _square(t, freq, 0.25) * 0.7
    return _build_sound(dur, gen)


def make_pickup_collected() -> pygame.mixer.Sound:
    """通用拾取音效：400→1600Hz 单音上升 (80ms)。"""
    dur = 0.08
    def gen(t: float):
        env = _adsr(t, 0.0, 0.08, 0.0, 0.0, dur)
        freq = 400.0 + (1200.0 * t / dur)
        return env * _triangle(t, freq)
    return _build_sound(dur, gen)


def make_upgrade_ready() -> pygame.mixer.Sound:
    """升级音效：C5-E5-G5-C6 四音上行琶音 (500ms)。"""
    dur = 0.50
    notes = [(523.0, 0.1), (659.0, 0.1), (784.0, 0.1), (1047.0, 0.2)]  # C5,E5,G5,C6
    def gen(t: float):
        start = 0.0
        for freq, note_dur in notes:
            if start <= t < start + note_dur:
                local_t = t - start
                env = _adsr(local_t, 0.005, 0.03, 0.8, 0.02, note_dur)
                return env * _square(t, freq, 0.5) * 0.6
            start += note_dur
        return 0.0
    return _build_sound(dur, gen)


def make_door_approached() -> pygame.mixer.Sound:
    """开门音效：带通噪声扫频 300→2000Hz (300ms)。"""
    dur = 0.30
    def gen(t: float):
        env = _adsr(t, 0.02, 0.15, 0.5, 0.13, dur)
        center_freq = 300.0 + (1700.0 * t / dur)
        # 用正弦叠加模拟带通噪声
        result = 0.0
        for mult in [0.8, 1.0, 1.2]:
            result += _sine(t, center_freq * mult + _noise() * 30.0) * 0.33
        return env * result
    return _build_sound(dur, gen)


def make_room_cleared() -> pygame.mixer.Sound:
    """房间清空音效：C4+E4+G4 大三和弦长音 (600ms)。"""
    dur = 0.60
    def gen(t: float):
        env = _adsr(t, 0.1, 0.1, 0.7, 0.2, dur)
        chord = (_square(t, 262.0, 0.5) + _square(t, 330.0, 0.5) + _square(t, 392.0, 0.5)) / 3.0
        return env * chord * 0.6
    return _build_sound(dur, gen)


def make_new_room() -> pygame.mixer.Sound:
    """新房间音效：低频噪声+正弦扫频 100→200Hz (300ms)。"""
    dur = 0.30
    def gen(t: float):
        env = _adsr(t, 0.05, 0.1, 0.4, 0.15, dur)
        freq = 100.0 + (100.0 * t / dur)
        noise_part = _noise() * 0.3
        tone = _sine(t, freq) * 0.7
        return env * (noise_part + tone)
    return _build_sound(dur, gen)


def make_boss_died() -> pygame.mixer.Sound:
    """Boss 死亡音效：35Hz 低频轰鸣+下滑音+噪声+延迟回声 (1000ms)。"""
    dur = 1.00
    def gen(t: float):
        # 主包络
        env = _adsr(t, 0.1, 0.1, 0.7, 0.2, dur)
        # 35Hz 低频方波
        bass = _square(t, 35.0, 0.5) * 0.5
        # 300→30Hz 下滑音
        freq = 300.0 - (270.0 * t / dur)
        slide = _triangle(t, max(10, freq)) * 0.3
        # 前 200ms 噪声
        noise_part = _noise() * max(0, 1.0 - t / 0.2) * 0.2
        # 模拟回声：150/350/550ms 处各加一个衰减副本
        echo = 0.0
        for delay in [0.15, 0.35, 0.55]:
            if t >= delay:
                et = t - delay
                echo_env = max(0, 1.0 - et / 0.3) * 0.15
                echo += echo_env * _square(et, 35.0, 0.5)
        return env * (bass + slide + noise_part) + echo
    return _build_sound(dur, gen)


def make_boss_ground_slam() -> pygame.mixer.Sound:
    """Boss 地震音效：噪声冲击+40Hz 地震低频+振幅摇摆 (500ms)。"""
    dur = 0.50
    def gen(t: float):
        # 前 80ms 噪声冲击
        noise_env = max(0, 1.0 - t / 0.08)
        impact = _noise() * noise_env * 0.7
        # 40Hz 低频方波
        env = _adsr(t, 0.02, 0.4, 0.1, 0.08, dur)
        bass = _square(t, 40.0, 0.5) * 0.5
        # 8Hz 振幅摇摆
        wobble = _sine(t, 8.0) * 0.2
        return impact + env * (bass + wobble)
    return _build_sound(dur, gen)


def make_boss_enrage() -> pygame.mixer.Sound:
    """Boss 狂暴音效：升频滤波噪声+10Hz 脉冲方波 (500ms)。"""
    dur = 0.50
    def gen(t: float):
        # 振幅从 0.5 升至 1.0
        env = 0.5 + 0.5 * (t / dur) if t < dur else 1.0
        env *= _adsr(t, 0.02, 0.3, 0.8, 0.18, dur)
        # 升频带通噪声（正弦叠加模拟）
        center = 100.0 + (700.0 * t / dur)
        noise_tone = 0.0
        for mult in [0.7, 1.0, 1.3, 1.6]:
            noise_tone += _sine(t, center * mult + _noise() * 40.0) * 0.25
        # 10Hz 脉冲
        pulse = _square(t, 10.0, 0.5) * 0.3
        return env * (noise_tone * 0.6 + pulse)
    return _build_sound(dur, gen)


def make_inventory_full() -> pygame.mixer.Sound:
    """背包满音效：80→65Hz 双脉冲低音蜂鸣 (250ms)。"""
    dur = 0.25
    def gen(t: float):
        if t < 0.1:
            env = max(0, 1.0 - t / 0.1)
            freq = 80.0 - (t / 0.1) * 15.0
        elif t < 0.15:
            return 0.0  # 50ms 间隔
        else:
            t2 = t - 0.15
            env = max(0, 1.0 - t2 / 0.1)
            freq = 80.0 - (t2 / 0.1) * 15.0
        return env * _square(t, freq, 0.5) * 0.4
    return _build_sound(dur, gen)


# ── UI 音效 ─────────────────────────────────────────────────────────────────

def make_ui_hover() -> pygame.mixer.Sound:
    """按钮悬停音效：800Hz 三角波短促轻柔 (50ms)。"""
    dur = 0.05
    def gen(t: float):
        env = _adsr(t, 0.0, 0.05, 0.0, 0.0, dur)
        return env * _triangle(t, 800.0) * 0.4
    return _build_sound(dur, gen)


def make_ui_select() -> pygame.mixer.Sound:
    """按钮点击音效：1000→1200Hz 方波上升 (100ms)。"""
    dur = 0.10
    def gen(t: float):
        env = _adsr(t, 0.0, 0.1, 0.0, 0.0, dur)
        freq = 1000.0 + (200.0 * t / dur)
        return env * _square(t, freq, 0.4) * 0.5
    return _build_sound(dur, gen)


# ── 音效生成表 ──────────────────────────────────────────────────────────────

SOUND_BUILDERS: dict[str, Callable[[], pygame.mixer.Sound]] = {
    "attack_hit":        make_attack_hit,
    "entity_died":       make_entity_died,
    "player_hit":        make_player_hit,
    "player_died":       make_player_died,
    "xp_gained":         make_xp_gained,
    "equipment_dropped": make_equipment_dropped,
    "pickup_collected":  make_pickup_collected,
    "upgrade_ready":     make_upgrade_ready,
    "door_approached":   make_door_approached,
    "room_cleared":      make_room_cleared,
    "new_room":          make_new_room,
    "boss_died":         make_boss_died,
    "boss_ground_slam":  make_boss_ground_slam,
    "boss_enrage":       make_boss_enrage,
    "inventory_full":    make_inventory_full,
    "ui_hover":          make_ui_hover,
    "ui_select":         make_ui_select,
}
