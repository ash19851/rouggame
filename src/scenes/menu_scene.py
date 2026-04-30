"""主菜单场景 - 游戏入口界面，提供开始游戏、仓库管理和退出选项。"""

import pygame
from src.scenes.base_scene import BaseScene
from src.ui.text_renderer import draw_text
from src.ui.button import Button


class MenuScene(BaseScene):
    """游戏主菜单。

    包含三个按钮："New Game" 开始新游戏、"Stash" 打开仓库管理、"Quit" 退出。
    标题带有淡入动画效果。
    """

    def __init__(self, engine, sound_manager=None):
        self.engine = engine
        self.sound_manager = sound_manager
        self.buttons: list[Button] = []
        self.title_alpha: float = 0.0  # 标题淡入透明度
        self._prev_hovered: str | None = None  # 上一帧悬浮的按钮文字

    def on_enter(self, state_machine, **data):
        """进入菜单，创建按钮并重置标题透明度。"""
        from src.core.engine import VIRTUAL_W, VIRTUAL_H
        self.state_machine = state_machine
        self.buttons = [
            Button("新游戏", VIRTUAL_W / 2, VIRTUAL_H / 2 - 30, 160, 40, font_size=22),
            Button("仓库", VIRTUAL_W / 2, VIRTUAL_H / 2 + 25, 120, 34, font_size=18,
                   color=(60, 60, 100), hover_color=(80, 80, 140)),
            Button("退出", VIRTUAL_W / 2, VIRTUAL_H / 2 + 70, 120, 34, font_size=18,
                   color=(80, 40, 40), hover_color=(120, 50, 50)),
        ]
        self.title_alpha = 0.0

    def handle_events(self, events: list[pygame.event.Event]):
        """处理按钮点击事件。"""
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)
                if btn.is_clicked(event):
                    if self.sound_manager:
                        self.sound_manager.play("ui_select", 0.8)
                    if btn.text == "新游戏":
                        from src.scenes.game_scene import GameScene
                        self.state_machine.switch(GameScene(self.engine, self.sound_manager))
                    elif btn.text == "仓库":
                        from src.scenes.stash_scene import StashScene
                        self.state_machine.push(StashScene(self.engine))
                    elif btn.text == "退出":
                        self.engine.running = False

    def update(self, dt: float):
        """更新标题淡入动画和按钮悬浮音效。"""
        self.title_alpha = min(1.0, self.title_alpha + dt * 1.5)
        # 检测按钮悬浮变化，播放入场音效
        if self.sound_manager:
            current_hovered = None
            for btn in self.buttons:
                if btn._hovered:
                    current_hovered = btn.text
                    break
            if current_hovered != self._prev_hovered and current_hovered is not None:
                self.sound_manager.play("ui_hover", 0.5)
            self._prev_hovered = current_hovered

    def render(self, surface: pygame.Surface):
        """渲染菜单界面。"""
        surface.fill((10, 10, 20))

        from src.core.engine import VIRTUAL_W, VIRTUAL_H

        # 标题（带淡入动画）
        title_color = (220, 200, 100)
        if self.title_alpha < 1.0:
            c = int(220 * self.title_alpha)
            title_color = (c, int(200 * self.title_alpha), int(100 * self.title_alpha))
        draw_text(surface, "深渊地牢", VIRTUAL_W / 2, VIRTUAL_H / 3,
                  size=40, color=title_color, center=True, shadow=True)

        for btn in self.buttons:
            btn.render(surface)

        # 操作提示
        draw_text(surface, "WASD: 移动 | 鼠标: 瞄准 | 点击: 攻击",
                  VIRTUAL_W / 2, VIRTUAL_H - 20, size=13, color=(120, 120, 140), center=True)
