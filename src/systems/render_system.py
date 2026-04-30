"""渲染系统 — 将所有带 Sprite 组件的实体按等距深度排序后绘制到屏幕。

渲染特性:
  - 等距投影: 世界坐标转屏幕坐标
  - 深度排序: 先按 layer 层级，再按等距深度 (wx+wy)
  - 粒子支持: 带 alpha 透明度和颜色渐变
  - 目标表面: 支持渲染到指定 surface
"""

import math, pygame
from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.render import Sprite
from src.ecs.components.health import Health
from src.ecs.components.player import Player
from src.ecs.components.particle import Particle
from src.ecs.components.status_effect import StatusEffect
from src.core.camera import Camera
from src.core.isometric import world_to_iso, iso_depth, get_screen_center


class RenderSystem(System):
    """渲染系统：将所有可见精灵按等距深度排序后绘制到屏幕。"""

    def __init__(self, camera: Camera):
        self.camera = camera

    def update(self, world: World, dt: float):
        """渲染到默认屏幕表面。"""
        ox, oy = self.camera.offset
        cx, cy = get_screen_center()

        entities = world.query(Transform, Sprite)

        # 等距深度排序：先按 layer 层级，再按等距深度 (world_x + world_y)
        entities.sort(key=lambda eid: (
            world.get_component(eid, Sprite).layer,
            iso_depth(world.get_component(eid, Transform).x,
                      world.get_component(eid, Transform).y),
        ))

        for eid in entities:
            t = world.get_component(eid, Transform)
            s = world.get_component(eid, Sprite)
            if not s.visible:
                continue

            screen_x, screen_y = world_to_iso(t.x, t.y, ox, oy, cx, cy)

            # 粒子渲染：带 alpha 透明度
            p = world.get_component(eid, Particle)
            if p is not None:
                alpha = int(255 * p.alpha)
                radius = max(1, int(p.size))
                particle_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                color_with_alpha = (*p.color, alpha) if p.fade else (*p.color, 255)
                pygame.draw.circle(particle_surf, color_with_alpha, (radius, radius), radius)
                pygame.display.get_surface().blit(particle_surf, (screen_x - radius, screen_y - radius))
                continue

            # 无敌闪烁：15Hz 快速明灭
            h = world.get_component(eid, Health)
            if h and h._invuln_timer > 0:
                if math.sin(h._invuln_timer * 30.0) <= 0:
                    continue

            if s.surface:
                pygame.display.get_surface().blit(
                    s.surface, (screen_x - s.width // 2, screen_y - s.height // 2)
                )
            else:
                rect = pygame.Rect(
                    screen_x - s.width // 2,
                    screen_y - s.height // 2,
                    s.width,
                    s.height,
                )
                pygame.draw.rect(pygame.display.get_surface(), s.color, rect)

            # 受击闪白
            if h and h._flash_timer > 0:
                alpha = int(180 * (h._flash_timer / 0.08))
                flash_surf = pygame.Surface((s.width, s.height), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, alpha))
                pygame.display.get_surface().blit(flash_surf,
                    (int(screen_x - s.width // 2), int(screen_y - s.height // 2)))

            # 状态效果染色
            se = world.get_component(eid, StatusEffect)
            if se and se.effects:
                for eff in se.effects:
                    if eff["type"] == "poison":
                        tint = pygame.Surface((s.width, s.height), pygame.SRCALPHA)
                        tint.fill((0, 255, 0, 50))
                        pygame.display.get_surface().blit(tint,
                            (int(screen_x - s.width // 2), int(screen_y - s.height // 2)))
                    elif eff["type"] == "slow":
                        tint = pygame.Surface((s.width, s.height), pygame.SRCALPHA)
                        tint.fill((0, 100, 255, 50))
                        pygame.display.get_surface().blit(tint,
                            (int(screen_x - s.width // 2), int(screen_y - s.height // 2)))

    def render_to(self, world: World, surface: pygame.Surface, dt: float):
        """渲染到指定目标表面（如用于小地图或 UI 预览）。"""
        ox, oy = self.camera.offset
        cx, cy = get_screen_center()

        entities = world.query(Transform, Sprite)
        entities.sort(key=lambda eid: (
            world.get_component(eid, Sprite).layer,
            iso_depth(world.get_component(eid, Transform).x,
                      world.get_component(eid, Transform).y),
        ))

        for eid in entities:
            t = world.get_component(eid, Transform)
            s = world.get_component(eid, Sprite)
            if not s.visible:
                continue

            screen_x, screen_y = world_to_iso(t.x, t.y, ox, oy, cx, cy)

            p = world.get_component(eid, Particle)
            if p is not None:
                alpha = int(255 * p.alpha)
                radius = max(1, int(p.size))
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                color_with_alpha = (*p.color, alpha)
                pygame.draw.circle(surf, color_with_alpha, (radius, radius), radius)
                surface.blit(surf, (screen_x - radius, screen_y - radius))
                continue

            h = world.get_component(eid, Health)

            # 无敌闪烁：15Hz 快速明灭
            if h and h._invuln_timer > 0:
                if math.sin(h._invuln_timer * 30.0) <= 0:
                    continue

            if s.surface:
                surface.blit(s.surface, (int(screen_x - s.width // 2), int(screen_y - s.height // 2)))
            else:
                rect = pygame.Rect(
                    int(screen_x - s.width // 2),
                    int(screen_y - s.height // 2),
                    s.width, s.height,
                )
                pygame.draw.rect(surface, s.color, rect)

            # 受击闪白：白色半透明覆盖
            if h and h._flash_timer > 0:
                alpha = int(180 * (h._flash_timer / 0.08))
                flash_surf = pygame.Surface((s.width, s.height), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, alpha))
                surface.blit(flash_surf, (int(screen_x - s.width // 2), int(screen_y - s.height // 2)))

            # 状态效果染色
            se = world.get_component(eid, StatusEffect)
            if se and se.effects:
                for eff in se.effects:
                    if eff["type"] == "poison":
                        tint = pygame.Surface((s.width, s.height), pygame.SRCALPHA)
                        tint.fill((0, 255, 0, 50))
                        surface.blit(tint, (int(screen_x - s.width // 2), int(screen_y - s.height // 2)))
                    elif eff["type"] == "slow":
                        tint = pygame.Surface((s.width, s.height), pygame.SRCALPHA)
                        tint.fill((0, 100, 255, 50))
                        surface.blit(tint, (int(screen_x - s.width // 2), int(screen_y - s.height // 2)))
