"""粒子实体工厂 - 创建临时粒子效果、粒子爆发、伤害数字和特殊死亡效果。"""

import random, math
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.render import Sprite
from src.ecs.components.motion import Motion
from src.ecs.components.particle import Particle


def create_particle(
    world: World,
    x: float, y: float,
    vx: float, vy: float,
    color: tuple[int, int, int],
    size: float = 3.0,
    lifetime: float = 0.5,
    fade: bool = True,
    shrink: bool = True,
    gravity: float = 0.0,
) -> int:
    """创建一个单个粒子实体，支持淡出、缩小和重力效果。

    Args:
        world: ECS 世界实例
        x, y: 粒子初始世界坐标
        vx, vy: 粒子初始速度
        color: 粒子颜色
        size: 粒子大小
        lifetime: 粒子存在时间（秒）
        fade: 是否随时间淡出
        shrink: 是否随时间缩小
        gravity: 重力加速度（向下为正）
    """
    eid = world.create_entity(tag="particle")

    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, Sprite(color=color, width=int(size * 2), height=int(size * 2), layer=10))
    world.add_component(eid, Motion(vx=vx, vy=vy))
    world.add_component(eid, Particle(
        lifetime=lifetime,
        age=0.0,
        color=color,
        size=size,
        vx=vx,
        vy=vy,
        fade=fade,
        shrink=shrink,
        gravity=gravity,
    ))

    return eid


def emit_burst(
    world: World,
    x: float, y: float,
    count: int,
    color: tuple[int, int, int],
    speed: float = 80.0,
    lifetime: float = 0.4,
    size: float = 3.0,
    gravity: float = 0.0,
):
    """在指定位置发射一组粒子爆发，粒子向四周均匀随机扩散。

    Args:
        world: ECS 世界实例
        x, y: 爆发中心坐标
        count: 粒子数量
        color: 粒子颜色
        speed: 粒子基础速度
        lifetime: 粒子存在时间（秒）
        size: 粒子大小
        gravity: 重力加速度（向下为正），默认 0
    """
    import random, math
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        spd = random.uniform(speed * 0.5, speed)
        vx = math.cos(angle) * spd
        vy = math.sin(angle) * spd
        create_particle(world, x, y, vx, vy, color, size, lifetime, gravity=gravity)


def emit_boss_death_burst(world: World, x: float, y: float):
    """Boss 死亡大爆炸粒子：外环螺旋 + 内层爆发 + 大块碎片。"""
    import random, math
    particle_count = 40
    colors = [(255, 200, 50), (255, 100, 30), (200, 50, 50), (255, 220, 100)]
    for i in range(particle_count):
        angle = (i / particle_count) * 2 * math.pi + random.uniform(-0.1, 0.1)
        speed = random.uniform(100, 200)
        color = random.choice(colors)
        create_particle(world, x, y,
                       math.cos(angle) * speed,
                       math.sin(angle) * speed,
                       color, size=4.0, lifetime=0.8)
    emit_burst(world, x, y, 20, (255, 255, 200), speed=60, lifetime=0.3, size=6.0)


def emit_death_dissolve(world: World, x: float, y: float, sprite_color: tuple[int, int, int]):
    """敌人死亡溶解：有色碎片粒子 + 核心爆发，带重力下落感。"""
    import math
    r, g, b = sprite_color
    fade_color = (max(20, r - 40), max(20, g - 40), max(20, b - 40))
    # 8 个有色溶解碎片
    for i in range(8):
        angle = (i / 8) * 2 * math.pi + random.uniform(-0.2, 0.2)
        speed = random.uniform(30, 70)
        create_particle(world, x, y,
                       math.cos(angle) * speed,
                       math.sin(angle) * speed,
                       fade_color, size=random.uniform(1.5, 3.0),
                       lifetime=random.uniform(0.2, 0.45),
                       fade=True, shrink=True, gravity=30.0)
    # 6 个核心爆发粒子
    emit_burst(world, x, y, 6, sprite_color, speed=50.0, lifetime=0.3, size=2.5)


def emit_player_death_burst(world: World, x: float, y: float):
    """玩家死亡大爆炸：蓝白色调，三层粒子效果。"""
    import math
    palette = [(80, 160, 255), (200, 220, 255), (150, 200, 255), (100, 180, 255)]
    # 外环 30 个蓝白粒子
    for i in range(30):
        angle = (i / 30) * 2 * math.pi + random.uniform(-0.15, 0.15)
        speed = random.uniform(120, 250)
        color = random.choice(palette)
        create_particle(world, x, y,
                       math.cos(angle) * speed,
                       math.sin(angle) * speed,
                       color, size=random.uniform(3.0, 6.0),
                       lifetime=random.uniform(0.5, 0.9),
                       fade=True, shrink=True, gravity=0.0)
    # 内层核心 12 个白色大粒子
    emit_burst(world, x, y, 12, (255, 255, 255), speed=40, lifetime=0.3, size=5.0)
    # 延迟中环爆发
    emit_burst(world, x, y, 16, (120, 180, 255), speed=80, lifetime=0.45, size=4.0)


def emit_ambient_dust(world: World, room_w: float, room_h: float):
    """房间环境微尘：随机位置的暖灰色微小漂浮粒子。"""
    count = random.randint(3, 5)
    for _ in range(count):
        x = random.uniform(64, room_w - 64)
        y = random.uniform(64, room_h - 64)
        vx = random.uniform(-5, 5)
        vy = random.uniform(-8, -3)
        create_particle(world, x, y, vx, vy,
                       (180, 170, 150),
                       size=random.uniform(0.8, 1.5),
                       lifetime=random.uniform(2.0, 4.0),
                       fade=True, shrink=False, gravity=-2.0)


def emit_damage_number(world: World, x: float, y: float, amount: int, is_crit: bool = False):
    """创建浮空伤害数字实体。"""
    from src.ecs.components.damage_number import DamageNumber
    eid = world.create_entity(tag="damage_number")
    color = (255, 215, 0) if is_crit else (255, 200, 200)
    text = f"CRIT! {amount}" if is_crit else f"-{amount}"
    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, DamageNumber(
        text=text, color=color, lifetime=0.8,
        float_speed=-45.0, font_size=16 if is_crit else 12,
        is_crit=is_crit,
    ))
