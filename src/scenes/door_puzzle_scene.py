"""门谜题场景 - 玩家需要在限定时间内按顺序按下按键来打开门。"""

import random, pygame
from src.scenes.base_scene import BaseScene
from src.ui.text_renderer import draw_text
from src.core.keyboard import is_key_down


class DoorPuzzleScene(BaseScene):
    """门谜题覆盖层场景。

    玩家必须在时间限制内按顺序按下 4-6 个指定按键才能打开门。
    难度越高，序列越长，时间限制越短。
    """

    def __init__(self, engine):
        self.engine = engine
        self._sequence: list[str] = []   # 按键序列
        self._index: int = 0             # 当前期望的按键索引
        self._timer: float = 0.0         # 已用时间
        self._time_limit: float = 5.0    # 时间限制
        self._solved: bool = False       # 是否已解开
        self._failed: bool = False       # 是否已失败
        self._callback = None            # 结果回调函数
        # 支持的按键映射
        self._key_map = {
            pygame.K_w: "W", pygame.K_a: "A", pygame.K_s: "S", pygame.K_d: "D",
            pygame.K_UP: "↑", pygame.K_DOWN: "↓", pygame.K_LEFT: "←", pygame.K_RIGHT: "→",
        }
        self._keys_held: dict[int, bool] = {}  # 按键按住状态
        self._last_key: str = ""               # 上一次按下的键，用于防抖

    def on_enter(self, state_machine, **data):
        """进入谜题场景，根据难度生成随机按键序列。"""
        self._callback = data.get("callback")
        difficulty = data.get("difficulty", 0)
        seq_len = 4 + difficulty  # 难度越高，序列越长
        all_keys = ["W", "A", "S", "D"]
        self._sequence = random.choices(all_keys, k=min(seq_len, 6))
        self._index = 0
        self._timer = 0.0
        self._time_limit = max(2.5, 5.0 - difficulty * 0.5)  # 难度越高，时间越短
        self._solved = False
        self._failed = False
        self._last_key = ""
        self._keys_held = {k: is_key_down(k) for k in self._key_map}

    def on_exit(self):
        pass

    def handle_events(self, events: list[pygame.event.Event]):
        """处理输入事件，ESC 直接失败。"""
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._fail()
                return

    def update(self, dt: float):
        """每帧更新：检测超时，轮询按键状态变化。"""
        if self._solved or self._failed:
            return
        self._timer += dt
        if self._timer >= self._time_limit:
            self._fail()
            return

        # 检测按键按下（rising edge），避免重复触发
        for key_code, key_name in self._key_map.items():
            now = is_key_down(key_code)
            prev = self._keys_held.get(key_code, False)
            if now and not prev:
                self._on_key(key_name)
            self._keys_held[key_code] = now

    def _on_key(self, key_name: str):
        """处理单次按键输入，含防抖逻辑。"""
        # 防抖：忽略最后按键的重复触发，除非序列期望重复同一按键
        if key_name == self._last_key:
            if self._sequence[self._index] != key_name:
                return
        else:
            self._last_key = key_name

        if key_name == self._sequence[self._index]:
            self._index += 1
            if self._index >= len(self._sequence):
                self._solve()
        else:
            self._fail()

    def render(self, surface: pygame.Surface):
        """渲染谜题界面：遮罩、标题、时间条、序列和进度指示。"""
        # 半透明遮罩覆盖游戏画面
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        surface.blit(dim, (0, 0))

        vw, vh = surface.get_size()
        cx, cy = vw // 2, vh // 2

        draw_text(surface, "门谜题", cx, cy - 50, size=24, color=(255, 220, 100), center=True, shadow=True)

        # 时间进度条
        bar_w, bar_h = 200, 8
        bar_x, bar_y = cx - bar_w // 2, cy - 10
        time_pct = 1.0 - self._timer / self._time_limit
        # 剩余时间少于 30% 时变橙
        bar_color = (100, 255, 100) if time_pct > 0.3 else (255, 150, 50)
        pygame.draw.rect(surface, (40, 40, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, int(bar_w * time_pct), bar_h))

        # 按键序列显示
        seq_str = "  ".join(self._sequence)
        draw_text(surface, seq_str, cx, cy + 20, size=28, color=(200, 200, 220), center=True, shadow=True)

        # 进度指示器：已完成的用 []，当前期待的用 ><，未到的只显示
        progress = ""
        for i, key in enumerate(self._sequence):
            if i < self._index:
                progress += f"[{key}] "
            elif i == self._index:
                progress += f">{key}< "
            else:
                progress += f" {key}  "
        draw_text(surface, progress.strip(), cx, cy + 55, size=16, color=(180, 180, 200), center=True)

        draw_text(surface, "按顺序按键！", cx, cy + 80, size=12, color=(140, 140, 160), center=True)

        # 成功/失败提示
        if self._solved:
            draw_text(surface, "成功！", cx, cy + 100, size=20, color=(100, 255, 100), center=True, shadow=True)
        elif self._failed:
            draw_text(surface, "失败！", cx, cy + 100, size=20, color=(255, 100, 100), center=True, shadow=True)

    def _solve(self):
        """谜题解开，调用回调通知成功。"""
        self._solved = True
        if self._callback:
            self._callback(True)

    def _fail(self):
        """谜题失败，调用回调通知失败。"""
        self._failed = True
        if self._callback:
            self._callback(False)
