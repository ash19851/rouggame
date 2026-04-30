"""
事件总线模块。

提供发布/订阅（Pub/Sub）模式的事件系统，用于模块间解耦通信。
各模块通过 subscribe 注册回调，通过 emit 触发事件。
"""

from collections import defaultdict
from typing import Callable, Any


class EventBus:
    """事件总线，管理事件的订阅与分发。

    使用字符串类型标识事件，支持任意关键字参数传递数据。
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable):
        """订阅指定类型的事件。callback 接收 (event_type, data_dict) 两个参数。"""
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅指定事件。"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def emit(self, event_type: str, **data: Any):
        """触发事件，将所有订阅者回调逐一调用。"""
        for cb in self._subscribers.get(event_type, []):
            cb(event_type, data)

    def clear(self):
        """清除所有订阅关系。"""
        self._subscribers.clear()
