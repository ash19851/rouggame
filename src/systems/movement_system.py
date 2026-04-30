"""移动系统 — 根据 Motion 组件更新实体位置，并处理轨道球、波形弹、粒子重力等特殊运动。

运动类型:
  - 普通: 按速度向量线性移动
  - 轨道球 (Orbital): 绕源实体旋转
  - 波形弹 (WaveMotion): 正弦波路径
  - 粒子: 支持重力加速度
"""

import math
from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.motion import Motion
from src.ecs.components.particle import Particle
from src.ecs.components.orbital import Orbital
from src.ecs.components.wave_motion import WaveMotion


class MovementSystem(System):
    """移动系统：每帧更新所有带 Motion 组件的实体位置。"""

    def update(self, world: World, dt: float):
        """遍历所有实体，按运动类型更新坐标。"""
        entities = world.query(Transform, Motion)

        for eid in entities:
            t = world.get_component(eid, Transform)
            m = world.get_component(eid, Motion)
            p = world.get_component(eid, Particle)

            # 轨道球运动：绕源实体旋转，计算世界坐标
            orb = world.get_component(eid, Orbital)
            if orb is not None:
                orb.angle += orb.angular_speed * dt
                orb.lifetime -= dt
                if orb.lifetime <= 0:
                    world.destroy_entity(eid)
                    continue
                if orb.source_eid != 0:
                    src_t = world.get_component(orb.source_eid, Transform)
                    if src_t:
                        orb.center_x = src_t.x
                        orb.center_y = src_t.y
                t.x = orb.center_x + math.cos(orb.angle) * orb.radius
                t.y = orb.center_y + math.sin(orb.angle) * orb.radius
                continue

            # 波形弹运动：沿主方向前进，同时垂直于方向的偏移按正弦波变化
            wm = world.get_component(eid, WaveMotion)
            if wm is not None:
                wm.elapsed += dt
                prev_offset = wm.amplitude * math.sin(2 * math.pi * wm.frequency * (wm.elapsed - dt))
                new_offset = wm.amplitude * math.sin(2 * math.pi * wm.frequency * wm.elapsed)
                delta_offset = new_offset - prev_offset
                # 垂直方向单位向量
                perp_x = -wm.dir_y
                perp_y = wm.dir_x
                # 主方向位移 + 垂直方向正弦偏移
                t.x += wm.dir_x * wm.speed * dt + perp_x * delta_offset
                t.y += wm.dir_y * wm.speed * dt + perp_y * delta_offset
            else:
                # 普通线性移动
                t.x += m.vx * dt
                t.y += m.vy * dt

            # 粒子重力：每帧累加到速度
            if p is not None and p.gravity != 0:
                m.vy += p.gravity * dt

            # 边界限制，防止实体飞出太远
            if t.x < -100:
                t.x = -100
            if t.x > 2000:
                t.x = 2000
            if t.y < -100:
                t.y = -100
            if t.y > 2000:
                t.y = 2000
