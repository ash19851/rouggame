"""Boss 实体工厂 —— 根据遭遇等级组装 Boss 实体，包含 7 个标准组件 + Boss 组件。"""

from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.render import Sprite
from src.ecs.components.motion import Motion
from src.ecs.components.collision import Collider
from src.ecs.components.health import Health
from src.ecs.components.combat import Combat
from src.ecs.components.ai import AI
from src.ecs.components.boss import Boss
from src.data.config_loader import BOSSES, BOSS_TYPES, ENCOUNTER_TABLE, SKILL_PARAMS, BALANCE
from src.graphics.sprite_atlas import get_sprite


def create_boss(world: World, encounter_level: int, x: float, y: float, stage_mult: float = 1.0) -> int:
    """创建一个 Boss 实体，返回其实体 ID。

    根据遭遇等级从配置中选择 Boss 类型、缩放属性和技能列表。
    装配 Transform/Sprite/Motion/Collider/Health/Combat/AI/Boss 共 8 个组件。

    Args:
        world: ECS 世界实例
        encounter_level: 遭遇等级（1-6）
        x, y: 世界坐标
        stage_mult: 关卡难度系数
    """
    # 将遭遇等级转为字符串键并 clamp 到 1-6
    lv = max(1, min(6, encounter_level))
    encounter = ENCOUNTER_TABLE.get(str(lv), ENCOUNTER_TABLE["1"])
    boss_type = encounter.get("boss_type", "boss_knight")
    type_cfg = BOSS_TYPES.get(boss_type, BOSS_TYPES["boss_knight"])

    # 数值缩放
    hp_mult = encounter.get("hp_mult", 2.0)
    dmg_mult = encounter.get("dmg_mult", 1.2)
    hp_val = int(type_cfg["base_hp"] * hp_mult * stage_mult)
    dmg_val = int(type_cfg["base_damage"] * dmg_mult * stage_mult)

    eid = world.create_entity(tag="boss")

    world.add_component(eid, Transform(x=x, y=y))
    sprite_name = type_cfg.get("sprite_name", boss_type)
    surf = get_sprite(sprite_name)
    size = type_cfg.get("size", [24, 28])
    world.add_component(eid, Sprite(
        surface=surf,
        color=tuple(type_cfg.get("color", [180, 40, 40])),
        width=size[0], height=size[1],
        layer=5,
    ))
    # 移动速度随难度缩放
    diff_cfg = BALANCE["difficulty"]
    speed_scale = diff_cfg["enemy_speed_stage_scale_base"] + stage_mult * diff_cfg["enemy_speed_stage_scale_mult"]
    world.add_component(eid, Motion(speed=type_cfg["base_speed"] * speed_scale))
    world.add_component(eid, Collider(width=size[0], height=size[1], layer=1))
    # 生命值带少量出生无敌帧
    invuln_time = BALANCE.get("boss", {}).get("spawn_invuln_time", 0.8)
    world.add_component(eid, Health(current=hp_val, max=hp_val, invuln_time=invuln_time))
    world.add_component(eid, Combat(
        damage=dmg_val,
        attack_speed=type_cfg["base_attack_speed"],
        range=type_cfg["attack_range"],
        cooldown=0.0,
    ))
    world.add_component(eid, AI(
        mode=type_cfg.get("ai_mode", "chase"),
        aggro_range=type_cfg["aggro_range"],
        attack_range=type_cfg["attack_range"],
        preferred_range=type_cfg.get("preferred_range", 150.0),
    ))

    # Boss 组件：技能列表、冷却初始化
    skills = list(encounter.get("skills", []))
    cooldowns: dict[str, float] = {}
    for sk in skills:
        sp = SKILL_PARAMS.get(sk, {})
        cooldowns[sk] = sp.get("cooldown", 5.0)
    boss_comp = Boss(
        encounter_level=lv,
        skills=skills,
        skill_cooldowns=cooldowns,
        movement_mode=encounter.get("move_mode", "chase"),
        show_name=type_cfg["name"],
        enrage_threshold=encounter.get("enrage_threshold", 0.5),
    )
    world.add_component(eid, boss_comp)

    return eid
