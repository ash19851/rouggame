"""伤害数字系统 —— 每帧更新浮空伤害数字的上浮、淡出和渲染。"""

import pygame
from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.damage_number import DamageNumber
from src.core.camera import Camera
from src.core.isometric import world_to_iso, get_screen_center


class DamageNumberSystem(System):
    """伤害数字系统：管理浮空战斗文字的更新和渲染。"""

    def __init__(self, camera: Camera):
        self.camera = camera
        self._font_cache: dict[int, pygame.font.Font] = {}

    def _get_font(self, size: int) -> pygame.font.Font:
        if size not in self._font_cache:
            self._font_cache[size] = pygame.font.Font(None, size)
        return self._font_cache[size]

    def update(self, world: World, dt: float):
        """更新位置、老化、销毁，然后渲染到屏幕。"""
        ox, oy = self.camera.offset
        cx, cy = get_screen_center()
        screen = pygame.display.get_surface()

        for eid in list(world.query(Transform, DamageNumber)):
            t = world.get_component(eid, Transform)
            dn = world.get_component(eid, DamageNumber)
            if t is None or dn is None:
                continue

            dn.age += dt
            if dn.age >= dn.lifetime:
                world.destroy_entity(eid)
                continue

            # 上浮
            t.y += dn.float_speed * dt

            # 计算 alpha（淡出）
            progress = dn.age / dn.lifetime
            alpha = int(255 * (1.0 - progress))

            # 弹出缩放：前 0.1s 放大，之后正常
            scale = 1.0
            if progress < 0.1:
                scale = 1.0 + (progress / 0.1) * 0.3

            # 屏幕坐标
            sx, sy = world_to_iso(t.x, t.y, ox, oy, cx, cy)

            # 渲染文本
            font = self._get_font(int(dn.font_size * scale))
            text_surf = font.render(dn.text, True, dn.color)
            text_surf.set_alpha(alpha)

            # 暴击加阴影
            if dn.is_crit:
                shadow = font.render(dn.text, True, (0, 0, 0))
                shadow.set_alpha(alpha // 2)
                screen.blit(shadow, (sx - text_surf.get_width() // 2 + 1,
                                     sy - text_surf.get_height() // 2 + 1))

            screen.blit(text_surf, (sx - text_surf.get_width() // 2,
                                    sy - text_surf.get_height() // 2))
