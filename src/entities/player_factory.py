"""玩家实体工厂 - 根据游戏平衡配置创建玩家实体及所有必要组件。"""

from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.render import Sprite
from src.ecs.components.motion import Motion
from src.ecs.components.collision import Collider
from src.ecs.components.health import Health
from src.ecs.components.combat import Combat
from src.ecs.components.player import Player
from src.ecs.components.equipment import Equipment
from src.ecs.components.inventory import Inventory
from src.ecs.components.weapon_pattern import WeaponPattern
from src.data.config_loader import BALANCE
from src.graphics.sprite_atlas import get_sprite


def create_player(world: World, x: float, y: float) -> int:
    """创建玩家实体，返回其实体 ID。

    玩家实体包含变换、渲染、运动、碰撞、生命、战斗、装备、
    背包和武器模式等全套组件，所有数值从 BALANCE 配置中读取。

    Args:
        world: ECS 世界实例
        x, y: 玩家初始世界坐标
    """
    cfg = BALANCE["player"]
    eid = world.create_entity(tag="player")

    world.add_component(eid, Transform(x=x, y=y))
    sprite_name = cfg.get("sprite_name", "player")
    world.add_component(eid, Sprite(
        surface=get_sprite(sprite_name),
        color=(80, 160, 255),
        width=12,
        height=16,
        layer=5,
    ))
    world.add_component(eid, Motion(speed=cfg["speed"]))
    world.add_component(eid, Collider(width=10, height=10, layer=0))
    world.add_component(eid, Health(
        current=cfg["hp"], max=cfg["hp"], invuln_time=cfg["invuln_time"]))
    world.add_component(eid, Combat(
        damage=cfg["damage"],
        attack_speed=cfg["attack_speed"],
        range=cfg["range"],
        cooldown=0.0,
        projectile_speed=cfg["projectile_speed"],
        projectile_size=cfg["projectile_size"],
        projectile_color=(100, 200, 255),
    ))
    # 玩家特有的角色属性组件
    world.add_component(eid, Player(
        xp=0,
        xp_to_level=cfg["xp_to_level"],
        level=1,
    ))
    world.add_component(eid, Equipment())
    world.add_component(eid, Inventory())
    world.add_component(eid, WeaponPattern(pattern="normal"))

    return eid
