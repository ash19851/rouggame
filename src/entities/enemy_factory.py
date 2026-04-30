"""敌人实体工厂 - 根据敌人类型和难度系数创建完整的敌人实体。"""

from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.render import Sprite
from src.ecs.components.motion import Motion
from src.ecs.components.collision import Collider
from src.ecs.components.health import Health
from src.ecs.components.combat import Combat
from src.ecs.components.ai import AI
from src.data.config_loader import ENEMIES, BALANCE
from src.graphics.sprite_atlas import get_enemy_sprite


def create_enemy(world: World, enemy_type: str, x: float, y: float, stage_mult: float = 1.0) -> int:
    """创建一个敌人实体，返回其实体 ID。

    Args:
        world: ECS 世界实例
        enemy_type: 敌人类型名称，对应配置中的 key
        x, y: 世界坐标
        stage_mult: 关卡难度系数，影响生命、伤害等数值
    """
    # 从配置中读取敌人数据，找不到则回退到 skeleton 的默认值
    cfg = ENEMIES.get(enemy_type, ENEMIES.get("skeleton", {}))
    if not cfg:
        cfg = {"name": "Skeleton", "color": [200, 180, 160], "size": [14, 20],
               "hp": 25, "damage": 8, "speed": 70.0, "attack_speed": 0.8,
               "attack_range": 30.0, "aggro_range": 180.0, "xp_value": 10}

    eid = world.create_entity(tag="enemy")

    world.add_component(eid, Transform(x=x, y=y))
    sprite_name = cfg.get("sprite_name", enemy_type)
    surf = get_enemy_sprite(sprite_name)
    color = tuple(cfg["color"])
    collision_size = cfg.get("size", [14, 20])
    world.add_component(eid, Sprite(
        surface=surf,
        color=color,
        width=collision_size[0],
        height=collision_size[1],
        layer=4,
    ))
    # 根据难度配置计算速度缩放比例
    diff_cfg = BALANCE["difficulty"]
    speed_scale = diff_cfg["enemy_speed_stage_scale_base"] + stage_mult * diff_cfg["enemy_speed_stage_scale_mult"]
    world.add_component(eid, Motion(speed=cfg["speed"] * speed_scale))
    world.add_component(eid, Collider(width=collision_size[0], height=collision_size[1], layer=1))
    # 生命值和伤害随关卡难度缩放
    world.add_component(eid, Health(
        current=int(cfg["hp"] * stage_mult),
        max=int(cfg["hp"] * stage_mult),
    ))
    world.add_component(eid, Combat(
        damage=int(cfg["damage"] * stage_mult),
        attack_speed=cfg["attack_speed"],
        range=cfg["attack_range"],
        cooldown=0.0,
    ))
    world.add_component(eid, AI(
        mode=cfg.get("ai_mode", "chase"),
        aggro_range=cfg["aggro_range"],
        attack_range=cfg["attack_range"],
        preferred_range=cfg.get("preferred_range", 150.0),
        dash_cooldown=cfg.get("dash_cooldown", 3.0),
        dash_speed_mult=cfg.get("dash_speed_mult", 3.0),
        dash_duration=cfg.get("dash_duration", 0.3),
        burst_damage=cfg.get("burst_damage", 0),
        burst_radius=cfg.get("burst_radius", 0.0),
    ))

    return eid
