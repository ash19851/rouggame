"""输入系统 — 处理键盘 WASD 移动和鼠标瞄准输入，将屏幕坐标转换为等距世界坐标。

输入映射:
  - W/↑: 上移
  - S/↓: 下移
  - A/←: 左移
  - D/→: 右移
  - 鼠标: 瞄准方向（通过等距逆变换转换到世界坐标）
"""

import math
import sys
import pygame
from src.ecs.system import System
from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.motion import Motion
from src.ecs.components.player import Player
from src.core.camera import Camera
from src.core.isometric import iso_to_world, get_screen_center
from src.core.keyboard import is_key_down


class InputSystem(System):
    """输入系统：读取键盘和鼠标事件，更新玩家移动速度和瞄准方向。"""

    def __init__(self, camera: Camera):
        self.camera = camera
        self.mouse_buttons: dict[int, bool] = {}
        self.mouse_x: float = 0.0
        self.mouse_y: float = 0.0
        self._events: list[pygame.event.Event] = []

    def set_events(self, events: list[pygame.event.Event]):
        """设置当前帧的 pygame 事件列表。"""
        self._events = events

    def update(self, world: World, dt: float):
        """每帧处理事件队列和键鼠状态，更新 WASD 移动和鼠标瞄准。"""
        # Process mouse events
        for event in self._events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_buttons[event.button] = True
                from src.core.engine import screen_to_virtual
                self.mouse_x, self.mouse_y = screen_to_virtual(*event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse_buttons[event.button] = False
            elif event.type == pygame.MOUSEMOTION:
                from src.core.engine import screen_to_virtual
                self.mouse_x, self.mouse_y = screen_to_virtual(*event.pos)

        players = world.query(Transform, Motion, Player)
        for eid in players:
            t = world.get_component(eid, Transform)
            m = world.get_component(eid, Motion)
            p = world.get_component(eid, Player)

            # WASD 移动（优先 Windows API，pygame 为后备）
            dx = 0.0
            dy = 0.0
            if is_key_down(pygame.K_w) or is_key_down(pygame.K_UP):
                dy = -1.0
            if is_key_down(pygame.K_s) or is_key_down(pygame.K_DOWN):
                dy = 1.0
            if is_key_down(pygame.K_a) or is_key_down(pygame.K_LEFT):
                dx = -1.0
            if is_key_down(pygame.K_d) or is_key_down(pygame.K_RIGHT):
                dx = 1.0

            # 归一化移动方向，避免斜向移动更快
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                m.vx = (dx / length) * m.speed
                m.vy = (dy / length) * m.speed
            else:
                m.vx = 0.0
                m.vy = 0.0

            # 鼠标瞄准方向：通过等距逆变换将屏幕坐标转为世界坐标
            ox, oy = self.camera.offset
            cx, cy = get_screen_center()
            world_mx, world_my = iso_to_world(self.mouse_x, self.mouse_y, ox, oy, cx, cy)
            aim_dx = world_mx - t.x
            aim_dy = world_my - t.y
            aim_len = math.sqrt(aim_dx * aim_dx + aim_dy * aim_dy)
            if aim_len > 0:
                p.aim_x = aim_dx / aim_len
                p.aim_y = aim_dy / aim_len

    def is_mouse_pressed(self, button: int = 1) -> bool:
        """检查鼠标按钮是否按下（1=左键）。"""
        return self.mouse_buttons.get(button, False)

    def is_key_pressed(self, key: int) -> bool:
        """检查键盘按键是否按下。"""
        return is_key_down(key)
