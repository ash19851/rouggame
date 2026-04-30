"""弹幕实体工厂 - 创建玩家发射的弹幕，支持直线弹幕、轨道环绕弹幕和波形弹幕。"""

import math
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.render import Sprite
from src.ecs.components.motion import Motion
from src.ecs.components.collision import Collider
from src.ecs.components.combat import Combat
from src.graphics.sprite_atlas import get_projectile_sprite


def create_projectile(
    world: World,
    x: float, y: float,
    dir_x: float, dir_y: float,
    speed: float,
    damage: int,
    color: tuple[int, int, int],
    size: float,
    max_range: float,
    source_eid: int,
    tag_extra: str = "",
) -> int:
    """创建一个直线飞行的弹幕实体。

    Args:
        world: ECS 世界实例
        x, y: 弹幕发射点世界坐标
        dir_x, dir_y: 弹幕飞行方向（单位向量）
        speed: 飞行速度
        damage: 造成的伤害
        color: 弹幕颜色
        size: 弹幕尺寸（半径）
        max_range: 最大飞行距离，超出后销毁
        source_eid: 发射者实体 ID
        tag_extra: 可选的额外标签，用于特殊弹幕模式
    """
    eid = world.create_entity(tag="projectile")

    # 将初始位置沿方向偏移，避免与发射者碰撞体重叠
    world.add_component(eid, Transform(x=x + dir_x * 10, y=y + dir_y * 10))
    world.add_component(eid, Sprite(
        surface=get_projectile_sprite(color, int(size)),
        color=color, width=int(size), height=int(size), layer=6,
    ))
    world.add_component(eid, Motion(vx=dir_x * speed, vy=dir_y * speed, speed=speed))
    world.add_component(eid, Collider(width=size, height=size, layer=2))

    # 可选的特殊弹幕模式标记
    if tag_extra:
        from src.ecs.components.weapon_pattern import WeaponPattern
        world.add_component(eid, WeaponPattern(pattern=tag_extra))

    world.add_component(eid, Combat(
        damage=damage,
        attack_speed=0,
        range=max_range,
        cooldown=0,
        projectile_speed=0,
        projectile_size=0,
        projectile_color=(0, 0, 0),
    ))

    return eid


def create_orbital(
    world: World,
    center_x: float, center_y: float,
    angle: float, radius: float,
    angular_speed: float, lifetime: float,
    damage: int,
    color: tuple[int, int, int],
    size: float,
    source_eid: int = 0,
) -> int:
    """创建一个环绕中心点旋转的轨道弹幕实体。

    Args:
        world: ECS 世界实例
        center_x, center_y: 旋转中心的世界坐标
        angle: 初始角度（弧度）
        radius: 轨道半径
        angular_speed: 角速度（弧度/秒），正值顺时针，负值逆时针
        lifetime: 弹幕存在时间（秒）
        damage: 造成伤害
        color: 弹幕颜色
        size: 弹幕尺寸
        source_eid: 来源实体 ID
    """
    eid = world.create_entity(tag="projectile")

    # 根据角度和半径计算初始位置
    px = center_x + math.cos(angle) * radius
    py = center_y + math.sin(angle) * radius

    world.add_component(eid, Transform(x=px, y=py))
    world.add_component(eid, Sprite(
        surface=get_projectile_sprite(color, int(size)),
        color=color, width=int(size), height=int(size), layer=6,
    ))
    # 轨道弹幕由 Orbital 组件驱动位置，不使用 Motion
    world.add_component(eid, Motion(vx=0.0, vy=0.0, speed=0))
    world.add_component(eid, Collider(width=size, height=size, layer=2))
    from src.ecs.components.orbital import Orbital
    world.add_component(eid, Orbital(
        center_x=center_x, center_y=center_y,
        radius=radius, angle=angle,
        angular_speed=angular_speed, lifetime=lifetime,
        damage=damage,
        source_eid=source_eid,
    ))
    world.add_component(eid, Combat(damage=damage, attack_speed=0, range=9999, cooldown=0))

    return eid


def create_wave_projectile(
    world: World,
    x: float, y: float,
    dir_x: float, dir_y: float,
    speed: float, amplitude: float, frequency: float,
    damage: int,
    color: tuple[int, int, int],
    size: float,
    source_eid: int,
) -> int:
    """创建一个沿主方向飞行但带有正弦波动的弹幕实体。

    Args:
        world: ECS 世界实例
        x, y: 弹幕发射点世界坐标
        dir_x, dir_y: 主飞行方向（单位向量）
        speed: 沿主方向的飞行速度
        amplitude: 波动振幅（垂直于主方向的偏移量）
        frequency: 波动频率
        damage: 造成伤害
        color: 弹幕颜色
        size: 弹幕尺寸
        source_eid: 发射者实体 ID
    """
    eid = world.create_entity(tag="projectile")

    world.add_component(eid, Transform(x=x + dir_x * 10, y=y + dir_y * 10))
    world.add_component(eid, Sprite(
        surface=get_projectile_sprite(color, int(size)),
        color=color, width=int(size), height=int(size), layer=6,
    ))
    # 波形运动由 WaveMotion 组件驱动，不使用 Motion
    world.add_component(eid, Motion(vx=0.0, vy=0.0, speed=0))
    world.add_component(eid, Collider(width=size, height=size, layer=2))
    from src.ecs.components.wave_motion import WaveMotion
    world.add_component(eid, WaveMotion(
        dir_x=dir_x, dir_y=dir_y,
        speed=speed,
        amplitude=amplitude, frequency=frequency,
        elapsed=0.0,
    ))
    world.add_component(eid, Combat(damage=damage, attack_speed=0, range=9999, cooldown=0))

    return eid
