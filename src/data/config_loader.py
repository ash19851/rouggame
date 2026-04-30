"""配置加载器 —— 从 JSON 文件读取游戏配置（敌人、装备、升级、平衡数据），缺失时使用内建默认值。"""

import json
import os

_CONFIG_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "assets", "configs"
)


def _load_json(filename: str, default: dict) -> dict:
    """从 JSON 文件加载配置，文件不存在或解析失败时返回默认值。"""
    path = os.path.join(_CONFIG_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return default


def _save_json(filename: str, data) -> None:
    """将配置数据写入 JSON 文件，自动创建目录。"""
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    path = os.path.join(_CONFIG_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --- 敌人配置 ---------------------------------------------------------------

_ENEMIES_DEFAULT = {
    "skeleton": {
        "name": "骷髅", "sprite_name": "skeleton",
        "color": [200, 180, 160], "size": [14, 20],
        "hp": 25, "damage": 8, "speed": 70.0, "attack_speed": 0.8,
        "attack_range": 30.0, "aggro_range": 180.0, "xp_value": 10,
        "ai_mode": "chase",
    },
    "slime": {
        "name": "史莱姆", "sprite_name": "slime",
        "color": [100, 220, 100], "size": [10, 10],
        "hp": 12, "damage": 4, "speed": 45.0, "attack_speed": 1.0,
        "attack_range": 22.0, "aggro_range": 140.0, "xp_value": 5,
        "ai_mode": "chase",
    },
    "archer": {
        "name": "弓箭手", "sprite_name": "archer",
        "color": [140, 200, 100], "size": [12, 18],
        "hp": 18, "damage": 6, "speed": 55.0, "attack_speed": 1.2,
        "attack_range": 200.0, "aggro_range": 220.0, "xp_value": 15,
        "ai_mode": "ranged", "preferred_range": 150.0,
        "projectile_speed": 220.0, "projectile_color": [255, 150, 80],
    },
    "ghost": {
        "name": "幽灵", "sprite_name": "ghost",
        "color": [200, 210, 240], "size": [10, 12],
        "hp": 15, "damage": 12, "speed": 60.0, "attack_speed": 0.6,
        "attack_range": 25.0, "aggro_range": 200.0, "xp_value": 15,
        "ai_mode": "dash", "dash_cooldown": 2.5,
        "dash_speed_mult": 3.5, "dash_duration": 0.25,
    },
    "spriggan": {
        "name": "树精", "sprite_name": "spriggan",
        "color": [180, 130, 80], "size": [12, 16],
        "hp": 30, "damage": 10, "speed": 50.0, "attack_speed": 0.7,
        "attack_range": 28.0, "aggro_range": 180.0, "xp_value": 20,
        "ai_mode": "chase", "burst_damage": 25, "burst_radius": 70.0,
    },
}

ENEMIES = _load_json("enemies.json", _ENEMIES_DEFAULT)


# --- 装备配置 ---------------------------------------------------------------

_EQUIPMENT_ITEMS_DEFAULT = {
    # Normal weapons
    "rusty_sword":  {"name": "锈剑",   "slot": "weapon", "rarity": "common",
                     "icon_sprite": "icon_sword",
                     "pattern": "normal", "stats": {"damage": 2}},
    "sharp_blade":  {"name": "利刃",   "slot": "weapon", "rarity": "rare",
                     "icon_sprite": "icon_sword",
                     "pattern": "normal", "stats": {"damage": 5, "attack_speed": 0.15}},
    "flame_reaper": {"name": "焰镰",  "slot": "weapon", "rarity": "epic",
                     "icon_sprite": "icon_sword",
                     "pattern": "normal", "stats": {"damage": 8, "attack_speed": 0.25, "projectile_size": 3}},
    # Pattern weapons
    "scatter_bow":      {"name": "散射弓",      "slot": "weapon", "rarity": "rare",
                         "icon_sprite": "icon_bow",
                         "pattern": "scatter", "stats": {"damage": 3},
                         "spread_count": 3, "spread_angle": 15.0},
    "splitter_crossbow": {"name": "分裂弩", "slot": "weapon", "rarity": "epic",
                         "icon_sprite": "icon_bow",
                         "pattern": "impact_scatter", "stats": {"damage": 5},
                         "frag_count": 4},
    "orbiting_orb":     {"name": "环绕法球",     "slot": "weapon", "rarity": "rare",
                         "icon_sprite": "icon_orb",
                         "pattern": "orbital", "stats": {"damage": 3},
                         "orbital_radius": 40.0, "orbital_speed": 4.0, "orbital_max": 5, "orbital_lifetime": 3.0},
    "wave_staff":       {"name": "波纹法杖",       "slot": "weapon", "rarity": "epic",
                         "icon_sprite": "icon_staff",
                         "pattern": "wave", "stats": {"damage": 6},
                         "wave_amplitude": 15.0, "wave_frequency": 8.0},
    # Armor
    "leather_vest": {"name": "皮背心",  "slot": "armor",  "rarity": "common",
                     "icon_sprite": "icon_armor",
                     "stats": {"max_hp": 15}},
    "iron_mail":    {"name": "铁锁甲",     "slot": "armor",  "rarity": "rare",
                     "icon_sprite": "icon_armor",
                     "stats": {"max_hp": 30, "move_speed": -5}},
    "dragon_plate": {"name": "龙鳞甲",  "slot": "armor",  "rarity": "epic",
                     "icon_sprite": "icon_armor",
                     "stats": {"max_hp": 50, "move_speed": -5}},
    # Accessories
    "wood_ring":    {"name": "木戒指",     "slot": "accessory", "rarity": "common",
                     "icon_sprite": "icon_ring",
                     "stats": {"move_speed": 10}},
    "silver_ring":  {"name": "银戒指",   "slot": "accessory", "rarity": "rare",
                     "icon_sprite": "icon_ring",
                     "stats": {"attack_speed": 0.2, "move_speed": 15}},
    "phoenix_eye":  {"name": "凤凰眼",   "slot": "accessory", "rarity": "epic",
                     "icon_sprite": "icon_ring",
                     "stats": {"damage": 5, "attack_speed": 0.3, "move_speed": 20}},
}

_EQUIPMENT_DEFAULTS = {
    "items": _EQUIPMENT_ITEMS_DEFAULT,
    "rarity_weights": {"common": 60, "rare": 30, "epic": 10},
    "rarity_colors": {
        "common": [160, 160, 160],
        "rare":   [80, 160, 255],
        "epic":   [200, 80, 255],
    },
}

_eq_data = _load_json("equipment_defs.json", _EQUIPMENT_DEFAULTS)
EQUIPMENT_DEFS = _eq_data.get("items", _EQUIPMENT_ITEMS_DEFAULT)
RARITY_WEIGHTS = _eq_data.get("rarity_weights", {"common": 60, "rare": 30, "epic": 10})
RARITY_COLORS = _eq_data.get("rarity_colors", {
    "common": [160, 160, 160], "rare": [80, 160, 255], "epic": [200, 80, 255],
})


# --- 升级配置 ---------------------------------------------------------------

_UPGRADES_DEFAULT = {
    "choices": [
        {"label": "+20 最大生命",  "desc": "提升最大生命值", "key": "max_hp",        "amount": 20},
        {"label": "+攻击速度",  "desc": "攻击更快",       "key": "attack_speed",  "amount": 0.2},
        {"label": "+移动速度", "desc": "移动更快",         "key": "move_speed",    "amount": 15.0},
        {"label": "+4 伤害",   "desc": "造成更多伤害",          "key": "damage",        "amount": 4},
        {"label": "完全回复",   "desc": "恢复全部生命",      "key": "heal",          "amount": 0},
        {"label": "+弹射速度", "desc": "弹射物飞行更快", "key": "projectile_speed", "amount": 80.0},
        {"label": "+攻击范围",  "desc": "射程更远",       "key": "range",         "amount": 30.0},
        {"label": "+弹射尺寸",  "desc": "弹射物体积更大",  "key": "projectile_size", "amount": 2.0},
        {"label": "+磁铁",     "desc": "从更远处拾取物品", "key": "magnet",   "amount": 20.0},
        {"label": "+护甲",      "desc": "减少 2 点伤害",  "key": "armor",         "amount": 2},
        {"label": "+生命回复", "desc": "每秒回复 0.5 生命", "key": "regen",         "amount": 0.5},
        {"label": "+暴击率", "desc": "+10% 暴击概率", "key": "crit_chance", "amount": 0.1},
        {"label": "+暴击伤害", "desc": "暴击伤害 +25%", "key": "crit_mult",   "amount": 0.25},
    ],
    "cards_shown": 4,
    "xp_curve_mult": 1.35,
}

_upg_data = _load_json("upgrades.json", _UPGRADES_DEFAULT)
UPGRADE_CHOICES = _upg_data.get("choices", _UPGRADES_DEFAULT["choices"])
UPGRADE_CARDS_SHOWN = _upg_data.get("cards_shown", 3)
UPGRADE_XP_CURVE_MULT = _upg_data.get("xp_curve_mult", 1.35)


# --- 平衡性配置 ------------------------------------------------------------

_BALANCE_DEFAULT = {
    "player": {
        "hp": 100, "damage": 15, "attack_speed": 3.5, "speed": 140.0,
        "range": 300.0, "projectile_speed": 500.0, "projectile_size": 6.0,
        "invuln_time": 0.3, "xp_to_level": 30,
        "sprite_name": "player",
    },
    "drops": {
        "xp_min": 3, "xp_max": 10, "health_chance": 0.2, "health_amount": 15,
        "equipment_chance": 0.05,
    },
    "difficulty": {
        "base_mult_per_stage": 1.0, "room_progress_bonus": 0.25,
        "enemy_speed_stage_scale_base": 0.9, "enemy_speed_stage_scale_mult": 0.1,
    },
    "stages": {
        "total_stages": 3, "rooms_per_stage": 6,
    },
    "pickup": {
        "magnet_range": 40.0, "xp_magnet_per_level": 8.0,
        "fly_speed": 200.0, "collect_distance": 12.0,
    },
    "enemy_spawn": {
        "initial_delay": 0.5, "wave_interval_min": 1.5, "wave_interval_max": 4.0,
        "spawn_initial_fraction": 0.5, "min_spawn_distance": 80.0,
    },
    "inventory_size": 6,
}

BALANCE = _load_json("balance.json", _BALANCE_DEFAULT)


# --- Boss 配置 ---------------------------------------------------------------

_BOSSES_DEFAULT = {
    "boss_types": {
        "boss_knight": {
            "name": "骸骨骑士", "sprite_name": "boss_knight",
            "color": [180, 40, 40], "size": [24, 28],
            "base_hp": 150, "base_damage": 18, "base_speed": 80.0,
            "base_attack_speed": 0.6, "attack_range": 40.0, "aggro_range": 300.0,
            "xp_value": 80,
        },
        "boss_lich": {
            "name": "地穴巫妖", "sprite_name": "boss_lich",
            "color": [100, 60, 180], "size": [24, 28],
            "base_hp": 180, "base_damage": 22, "base_speed": 65.0,
            "base_attack_speed": 0.7, "attack_range": 250.0, "aggro_range": 300.0,
            "xp_value": 150, "ai_mode": "ranged", "preferred_range": 160.0,
            "projectile_speed": 200.0, "projectile_color": [160, 100, 240],
        },
        "boss_dragon": {
            "name": "幽冥龙", "sprite_name": "boss_dragon",
            "color": [60, 60, 70], "size": [32, 36],
            "base_hp": 280, "base_damage": 30, "base_speed": 55.0,
            "base_attack_speed": 0.5, "attack_range": 45.0, "aggro_range": 350.0,
            "xp_value": 300,
        },
    },
    "encounter_table": {
        "1": {"hp_mult": 1.5, "dmg_mult": 1.2, "skills": ["dash_charge"], "move_mode": "chase", "boss_type": "boss_knight"},
        "2": {"hp_mult": 2.0, "dmg_mult": 1.4, "skills": ["dash_charge", "split_self"], "move_mode": "chase", "boss_type": "boss_knight"},
        "3": {"hp_mult": 2.3, "dmg_mult": 1.6, "skills": ["dash_charge", "split_self", "projectile_barrage"], "move_mode": "hover", "boss_type": "boss_lich"},
        "4": {"hp_mult": 2.7, "dmg_mult": 1.8, "skills": ["dash_charge", "projectile_barrage", "summon_minions", "ground_slam"], "move_mode": "charge", "boss_type": "boss_lich"},
        "5": {"hp_mult": 3.0, "dmg_mult": 2.1, "skills": ["dash_charge", "projectile_barrage", "summon_minions", "ground_slam", "teleport"], "move_mode": "charge", "boss_type": "boss_dragon"},
        "6": {"hp_mult": 3.5, "dmg_mult": 2.5, "skills": ["dash_charge", "split_self", "projectile_barrage", "summon_minions", "ground_slam", "enrage"], "move_mode": "teleport_move", "boss_type": "boss_dragon", "enrage_threshold": 0.5, "enrage_speed_mult": 1.5, "enrage_dmg_mult": 1.5},
    },
    "skill_params": {
        "dash_charge":        {"cooldown": 5.0, "speed_mult": 3.5, "duration": 0.4},
        "split_self":         {"cooldown": 8.0, "clone_count": 2, "clone_hp_ratio": 0.15, "clone_dmg_ratio": 0.3},
        "knockback_wind":     {"cooldown": 4.0, "force": 300.0, "duration": 0.5},
        "summon_minions":     {"cooldown": 10.0, "count": 3, "spread_radius": 80.0},
        "projectile_barrage": {"cooldown": 3.0, "burst_count": 12, "waves": 3, "proj_speed": 180.0, "proj_dmg_ratio": 0.5},
        "ground_slam":        {"cooldown": 5.0, "slam_mult": 1.5, "slam_radius": 90.0, "windup": 0.4},
        "teleport":           {"cooldown": 6.0, "min_dist": 80.0, "max_dist": 150.0},
        "enrage":             {"speed_mult": 1.5, "dmg_mult": 1.5},
    },
}

BOSSES = _load_json("bosses.json", _BOSSES_DEFAULT)

# 从 BOSSES 中提取子字典方便直接访问
BOSS_TYPES = BOSSES.get("boss_types", _BOSSES_DEFAULT["boss_types"])
ENCOUNTER_TABLE = BOSSES.get("encounter_table", _BOSSES_DEFAULT["encounter_table"])
SKILL_PARAMS = BOSSES.get("skill_params", _BOSSES_DEFAULT["skill_params"])


# --- 辅助函数 ---------------------------------------------------------------

def save_all_defaults() -> None:
    """从内建默认值重新生成所有 JSON 配置文件。"""
    _save_json("enemies.json", _ENEMIES_DEFAULT)
    _save_json("equipment_defs.json", _EQUIPMENT_DEFAULTS)
    _save_json("upgrades.json", _UPGRADES_DEFAULT)
    _save_json("balance.json", _BALANCE_DEFAULT)
    _save_json("bosses.json", _BOSSES_DEFAULT)
    print("Config files regenerated from defaults.")
