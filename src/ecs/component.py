"""
ECS 组件基类模块。

Entity-Component-System 架构中的 Component 层。
所有数据组件均为 @dataclass 子类，纯数据、无逻辑。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Component:
    """所有组件的基类。组件只存储数据，由 System 处理逻辑。

    子类应使用 @dataclass 装饰器定义字段。
    """
    pass
