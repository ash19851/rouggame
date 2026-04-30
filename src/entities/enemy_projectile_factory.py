"""
敌人弹幕工厂。
敌人的弹幕以玩家为目标，而非以其他敌人为目标，通过 EnemyProjectile 组件区分。
"""

from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.render import Sprite
from src.ecs.components.motion import Motion
from src.ecs.components.collision import Collider
from src.ecs.components.combat import Combat
from src.ecs.components.enemy_projectile import EnemyProjectile
from src.graphics.sprite_atlas import get_projectile_sprite


def create_enemy_projectile(
    world: World,
    x: float, y: float,
    dir_x: float, dir_y: float,
    speed: float,
    damage: int,
    color: tuple[int, int, int] = (255, 100, 80),
    size: float = 5.0,
) -> int:
    """创建一个敌方弹幕实体。

    Args:
        world: ECS 世界实例
        x, y: 弹幕发射点世界坐标
        dir_x, dir_y: 弹幕飞行方向（单位向量）
        speed: 弹幕飞行速度
        damage: 弹幕造成的伤害值
        color: 弹幕颜色
        size: 弹幕尺寸（半径）
    """
    eid = world.create_entity(tag="enemy_projectile")

    # 将初始位置沿方向偏移一小段距离，避免与发射体重叠
    world.add_component(eid, Transform(x=x + dir_x * 8, y=y + dir_y * 8))
    world.add_component(eid, Sprite(
        surface=get_projectile_sprite(color, int(size)),
        color=color, width=int(size), height=int(size), layer=6,
    ))
    world.add_component(eid, Motion(vx=dir_x * speed, vy=dir_y * speed, speed=speed))
    world.add_component(eid, Collider(width=size, height=size, layer=2))
    world.add_component(eid, Combat(damage=damage, attack_speed=0, range=400, cooldown=0,
                                    projectile_speed=0, projectile_size=0, projectile_color=(0, 0, 0)))
    # EnemyProjectile 组件用于区分敌我弹幕
    world.add_component(eid, EnemyProjectile())

    return eid
