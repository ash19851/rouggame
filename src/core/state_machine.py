"""
场景状态机模块。

使用栈结构管理游戏场景（菜单、游戏内、暂停等）。
支持 push/pop/switch 操作，栈顶场景为当前活动场景。
"""

from typing import Optional
from src.scenes.base_scene import BaseScene


class StateMachine:
    """场景状态机，基于栈管理场景切换。

    - push: 暂停当前场景，压入新场景（用于子菜单、弹窗等）
    - pop: 退出当前场景，恢复上一个场景
    - switch: 替换当前场景（用于场景切换）
    """

    def __init__(self):
        self.stack: list[BaseScene] = []

    def push(self, scene: BaseScene, **transition_data):
        """压入新场景。暂停当前栈顶场景，调用新场景的 on_enter。"""
        if self.stack:
            self.stack[-1].on_pause()
        self.stack.append(scene)
        scene.on_enter(self, **transition_data)

    def pop(self) -> Optional[dict]:
        """弹出当前场景。调用其 on_exit，恢复下面场景的 on_resume。"""
        if not self.stack:
            return None
        outgoing = self.stack.pop()
        outgoing.on_exit()
        if self.stack:
            self.stack[-1].on_resume()
        return None

    def switch(self, scene: BaseScene, **transition_data):
        """替换栈顶场景。弹出当前并压入新场景。"""
        if self.stack:
            self.stack.pop().on_exit()
        self.stack.append(scene)
        scene.on_enter(self, **transition_data)

    def current(self) -> Optional[BaseScene]:
        """返回栈顶场景（当前活动场景），栈空返回 None。"""
        return self.stack[-1] if self.stack else None

    def update(self, dt: float):
        """更新栈顶场景的逻辑。"""
        if self.stack:
            self.stack[-1].update(dt)

    def handle_events(self, events: list):
        """将输入事件分发给栈顶场景。"""
        if self.stack:
            self.stack[-1].handle_events(events)

    def render(self, surface):
        """渲染栈中所有场景（从底到顶），实现叠加效果。"""
        for scene in self.stack:
            scene.render(surface)
