"""游戏结束场景 - 展示结算数据和重新开始/返回菜单选项。"""

import pygame
from src.scenes.base_scene import BaseScene
from src.ui.text_renderer import draw_text
from src.ui.button import Button


class GameOverScene(BaseScene):
    """游戏结束画面。

    显示胜利/失败标题、玩家等级、击杀数和关卡等结算信息，
    并提供"重试"和"返回菜单"两个按钮。
    """

    def __init__(self, engine):
        self.engine = engine
        self.buttons: list[Button] = []
        self.stats: dict = {}       # 结算统计数据
        self.alpha: float = 0.0     # 渐显透明度

    def on_enter(self, state_machine, **data):
        """进入场景，接收结算数据并创建按钮。"""
        from src.core.engine import VIRTUAL_W, VIRTUAL_H
        self.state_machine = state_machine
        self.stats = data.get("stats", {})
        self.buttons = [
            Button("重试", VIRTUAL_W / 2, VIRTUAL_H / 2 + 20, 140, 38, font_size=20),
            Button("菜单", VIRTUAL_W / 2, VIRTUAL_H / 2 + 70, 120, 32, font_size=16,
                   color=(50, 50, 50), hover_color=(80, 80, 80)),
        ]
        self.alpha = 0.0

    def handle_events(self, events: list[pygame.event.Event]):
        """处理按钮点击事件。"""
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)
                if btn.is_clicked(event):
                    if btn.text == "重试":
                        from src.scenes.game_scene import GameScene
                        self.state_machine.switch(GameScene(self.engine))
                    elif btn.text == "菜单":
                        from src.scenes.menu_scene import MenuScene
                        self.state_machine.switch(MenuScene(self.engine))

    def update(self, dt: float):
        """更新透明度实现淡入效果。"""
        self.alpha = min(1.0, self.alpha + dt * 2.0)

    def render(self, surface: pygame.Surface):
        """渲染结算界面。"""
        surface.fill((10, 5, 15))

        from src.core.engine import VIRTUAL_W, VIRTUAL_H

        # 半透明覆盖增强氛围
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(100 * self.alpha)))
        surface.blit(overlay, (0, 0))

        # 胜利/失败标题
        victory = self.stats.get("victory", False)
        if victory:
            draw_text(surface, "胜利！", VIRTUAL_W / 2, VIRTUAL_H / 3 - 20,
                      size=36, color=(255, 215, 0), center=True, shadow=True)
        else:
            draw_text(surface, "游戏结束", VIRTUAL_W / 2, VIRTUAL_H / 3 - 20,
                      size=36, color=(220, 80, 80), center=True, shadow=True)

        # 结算属性统计
        level = self.stats.get("level", 1)
        kills = self.stats.get("kills", 0)
        stage = self.stats.get("stage", 1)
        draw_text(surface, f"等级 {level}  |  击杀 {kills}  |  第 {stage} 关",
                  VIRTUAL_W / 2, VIRTUAL_H / 3 + 25, size=16, color=(180, 180, 200), center=True)

        for btn in self.buttons:
            btn.render(surface)
