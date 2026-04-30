"""场景基类 - 定义所有场景必须实现的接口，供状态机统一调度。"""

from abc import ABC, abstractmethod
import pygame


class BaseScene(ABC):
    """场景抽象基类。

    所有场景（菜单、游戏、背包等）均继承此类，实现生命周期方法。
    场景状态机通过 on_enter/on_exit/push/pop 管理场景栈。
    """

    def on_enter(self, state_machine, **data):
        """进入场景时调用，可接收上一场景传递的数据。"""
        pass

    def on_exit(self):
        """退出场景时调用，用于清理资源。"""
        pass

    def on_pause(self):
        """场景被暂停（新场景 push 到栈顶）时调用。"""
        pass

    def on_resume(self):
        """场景恢复（上层场景 pop 后）时调用。"""
        pass

    @abstractmethod
    def handle_events(self, events: list[pygame.event.Event]):
        """处理输入事件，每帧调用。"""
        ...

    @abstractmethod
    def update(self, dt: float):
        """更新场景逻辑，每帧调用。

        Args:
            dt: 距上一帧的时间间隔（秒）
        """
        ...

    @abstractmethod
    def render(self, surface: pygame.Surface):
        """渲染场景到目标 surface。

        Args:
            surface: 目标渲染表面（通常是虚拟屏幕）
        """
        ...
