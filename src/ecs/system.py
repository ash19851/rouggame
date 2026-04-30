"""
ECS 系统基类模块。

Entity-Component-System 架构中的 System 层。
每个 System 负责特定领域的逻辑，每帧在 World 上运行。
"""

from abc import ABC, abstractmethod
from src.ecs.world import World


class System(ABC):
    """所有系统的抽象基类。

    每帧由 World.update 调用，对拥有特定组件的实体执行逻辑处理。
    """

    @abstractmethod
    def update(self, world: World, dt: float):
        """每帧执行系统逻辑。

        Args:
            world: ECS 世界，用于查询实体和组件
            dt: 帧间隔时间（秒）
        """
        ...
