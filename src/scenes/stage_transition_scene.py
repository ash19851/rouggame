"""关卡过渡场景 - 关卡之间的简报画面，展示氛围文字并支持自动/手动推进。"""

import pygame
from src.scenes.base_scene import BaseScene
from src.core.engine import VIRTUAL_W, VIRTUAL_H
from src.ui.text_renderer import draw_text
from src.ui.button import Button


# 各关卡的氛围文字
STAGE_FLAVOR = {
    1: "地牢震颤……\n更深处的大厅在等待。",
    2: "深入黑暗之中。\n空气愈发寒冷。",
    3: "你征服了深渊。\n地牢不复存在。",
}


class StageTransitionScene(BaseScene):
    """关卡过渡过场。

    在玩家完成一个关卡后显示，展示氛围文字和"管理仓库"按钮。
    3 秒后自动前进，或由玩家按键/点击跳过。
    """

    def __init__(self, engine):
        self.engine = engine
        self.stage_cleared: int = 1
        self.total_stages: int = 3
        self._timer: float = 0.0                      # 计时器
        self._auto_advance_delay: float = 3.0          # 自动前进延迟（秒）
        self._next_stage: int = 1
        self._callback = None                          # 完成后的回调
        self._stash_btn: Button | None = None          # 仓库管理按钮

    def on_enter(self, state_machine, **data):
        """进入过渡场景，接收关卡数据并初始化仓库按钮。"""
        self.state_machine = state_machine
        self.stage_cleared = data.get("stage_cleared", 1)
        self.total_stages = data.get("total_stages", 3)
        self._next_stage = data.get("next_stage", 2)
        self._callback = data.get("callback")
        self._timer = 0.0
        self._stash_btn = Button("管理仓库", VIRTUAL_W / 2, VIRTUAL_H - 50,
                                 130, 28, font_size=14,
                                 color=(50, 50, 80), hover_color=(70, 70, 120))

    def handle_events(self, events: list[pygame.event.Event]):
        """处理事件：仓库按钮点击、任意按键/点击跳过过渡。"""
        for event in events:
            if self._stash_btn:
                self._stash_btn.handle_event(event)
                if self._stash_btn.is_clicked(event):
                    from src.scenes.stash_scene import StashScene
                    self.state_machine.push(StashScene(self.engine))
                    return
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self._finish()

    def update(self, dt: float):
        """计时后自动推进。"""
        self._timer += dt
        if self._timer >= self._auto_advance_delay:
            self._finish()

    def _finish(self):
        """过渡完成，调用回调并弹出当前场景。"""
        if self._callback:
            self._callback(self._next_stage)
        self.state_machine.pop()

    def render(self, surface: pygame.Surface):
        """渲染过渡画面：遮罩、关卡完成信息、氛围文字和继续提示。"""
        # 暗色遮罩
        dim = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        surface.blit(dim, (0, 0))

        if self._next_stage > self.total_stages:
            # 全部通关
            draw_text(surface, "胜利！", VIRTUAL_W / 2, VIRTUAL_H / 2 - 40,
                      size=32, color=(255, 215, 0), center=True, shadow=True)
            draw_text(surface, "地牢已被征服。",
                      VIRTUAL_W / 2, VIRTUAL_H / 2,
                      size=14, color=(200, 200, 200), center=True)
        else:
            # 继续下一关
            draw_text(surface, f"第 {self.stage_cleared} 关 完成！",
                      VIRTUAL_W / 2, VIRTUAL_H / 2 - 30,
                      size=24, color=(255, 215, 0), center=True, shadow=True)

            # 氛围描述文字
            flavor = STAGE_FLAVOR.get(self.stage_cleared, "")
            lines = flavor.split("\n")
            for i, line in enumerate(lines):
                draw_text(surface, line, VIRTUAL_W / 2, VIRTUAL_H / 2 + 10 + i * 18,
                          size=12, color=(180, 180, 200), center=True)

        if self._stash_btn:
            self._stash_btn.render(surface)

        # 脉冲闪烁的"点击继续"提示
        alpha_pulse = 0.5 + 0.5 * abs(pygame.time.get_ticks() % 1200 / 600.0 - 1.0)
        c = int(160 * alpha_pulse)
        draw_text(surface, "点击或按任意键继续",
                  VIRTUAL_W / 2, VIRTUAL_H - 20,
                  size=11, color=(c, c, c), center=True)
