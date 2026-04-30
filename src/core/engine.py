"""
游戏引擎核心模块。

负责主循环、虚拟分辨率管理、画面缩放（letterbox）以及鼠标坐标转换。
所有游戏逻辑在固定虚拟分辨率下运行，渲染时等比缩放到实际窗口。
"""

import pygame
from src.core.state_machine import StateMachine

# 虚拟分辨率（固定的逻辑分辨率）
VIRTUAL_W = 480
VIRTUAL_H = 360
# 初始窗口缩放倍数
INITIAL_SCALE = 2

# 当前帧的缩放与偏移量，用于鼠标坐标转换
_cur_scale: float = float(INITIAL_SCALE)
_cur_offset_x: float = 0.0
_cur_offset_y: float = 0.0


def screen_to_virtual(sx: float, sy: float) -> tuple[float, float]:
    """将窗口像素坐标转换为虚拟像素坐标。"""
    return (sx - _cur_offset_x) / _cur_scale, (sy - _cur_offset_y) / _cur_scale


def _calc_draw_rect(win_w: int, win_h: int) -> tuple[int, int, int, int]:
    """计算 letterbox 绘制区域，保持宽高比，居中显示虚拟表面。"""
    global _cur_scale, _cur_offset_x, _cur_offset_y
    # 选择较小的缩放比例以完整容纳虚拟表面
    _cur_scale = min(win_w / VIRTUAL_W, win_h / VIRTUAL_H)
    draw_w = int(VIRTUAL_W * _cur_scale)
    draw_h = int(VIRTUAL_H * _cur_scale)
    # 计算居中偏移量（左右/上下黑边）
    _cur_offset_x = (win_w - draw_w) / 2
    _cur_offset_y = (win_h - draw_h) / 2
    return int(_cur_offset_x), int(_cur_offset_y), draw_w, draw_h


class Engine:
    """游戏引擎，管理主循环和渲染管线。

    每帧流程：处理输入 -> 更新场景状态机 -> 渲染到虚拟表面 -> 缩放到窗口。
    """

    def __init__(self):
        # 创建可缩放窗口，初始大小为虚拟分辨率 * 初始缩放
        self.screen = pygame.display.set_mode(
            (VIRTUAL_W * INITIAL_SCALE, VIRTUAL_H * INITIAL_SCALE),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption("深渊地牢")
        self.clock = pygame.time.Clock()
        # 虚拟表面：所有渲染都在这个表面上进行，之后统一缩放
        self.virtual_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        self.state_machine = StateMachine()
        self.running = True

    def run(self):
        """启动主循环，持续运行直到退出。"""
        while self.running:
            # 计算帧间隔时间（秒），限制最高 60 FPS
            dt = self.clock.tick(60) / 1000.0
            raw_events = pygame.event.get()
            events = list(raw_events)

            # 检测窗口关闭事件
            for e in raw_events:
                if e.type == pygame.QUIT:
                    self.running = False

            # 将事件分发给当前场景处理
            self.state_machine.handle_events(events)
            self.state_machine.update(dt)

            # 清空虚拟表面，渲染当前场景
            self.virtual_surface.fill((10, 10, 15))
            self.state_machine.render(self.virtual_surface)

            # 将虚拟表面缩放到实际窗口（letterbox 模式）
            win_w, win_h = self.screen.get_size()
            ox, oy, dw, dh = _calc_draw_rect(win_w, win_h)
            scaled = pygame.transform.scale(self.virtual_surface, (dw, dh))
            self.screen.fill((0, 0, 0))
            self.screen.blit(scaled, (ox, oy))
            pygame.display.flip()
