"""
ECS 世界（World）模块。

Entity-Component-System 架构的核心管理器。负责：
- 实体生命周期管理（创建、销毁）
- 组件存储与查询（支持多组件类型联合查询）
- 系统调度（每帧按注册顺序执行系统）
"""

from typing import Type, Optional, Any
from collections import defaultdict
from src.ecs.component import Component
from src.ecs.entity import Entity


class World:
    """ECS 世界，管理所有实体、组件和系统。

    组件按类型存储：{ComponentType: {entity_id: component_instance}}
    销毁操作延迟到帧末执行（_flush_destroyed），避免迭代中修改集合。
    """

    def __init__(self):
        self._next_id: int = 0
        self.entities: set[int] = set()                      # 所有存活实体 ID
        self._components: dict[type, dict[int, Component]] = defaultdict(dict)  # 类型 -> {实体ID -> 组件}
        self._systems: list[Any] = []                         # 注册的系统列表
        self._destroy_queue: list[int] = []                   # 待销毁实体队列

    @property
    def entity_count(self) -> int:
        """当前存活实体数量。"""
        return len(self.entities)

    def create_entity(self, tag: str = "") -> int:
        """创建新实体并返回其 ID。tag 用于调试标识，目前仅概念性存储。"""
        eid = self._next_id
        self._next_id += 1
        self.entities.add(eid)
        if tag:
            pass  # tag 概念性存储，简化实现
        return eid

    def destroy_entity(self, eid: int):
        """标记实体待销毁。实际删除延迟到 _flush_destroyed 执行。"""
        if eid not in self.entities:
            return
        self._destroy_queue.append(eid)

    def _flush_destroyed(self):
        """清理所有待销毁实体及其组件。在每帧开始和结束时调用。"""
        for eid in self._destroy_queue:
            self.entities.discard(eid)
            # 从所有组件类型中移除该实体的组件
            for comps in self._components.values():
                comps.pop(eid, None)
        self._destroy_queue.clear()

    def add_component(self, eid: int, comp: Component):
        """为实体添加组件实例。同一类型组件会覆盖旧值。"""
        if eid not in self.entities:
            raise ValueError(f"Entity {eid} does not exist")
        self._components[type(comp)][eid] = comp

    def remove_component(self, eid: int, comp_type: type):
        """移除实体的指定类型组件。"""
        self._components.get(comp_type, {}).pop(eid, None)

    def get_component(self, eid: int, comp_type: type) -> Optional[Component]:
        """获取实体的指定类型组件，不存在返回 None。"""
        return self._components.get(comp_type, {}).get(eid)

    def has_component(self, eid: int, comp_type: type) -> bool:
        """检查实体是否拥有指定类型的组件。"""
        return eid in self._components.get(comp_type, {})

    def query(self, *comp_types: type) -> list[int]:
        """查询同时拥有所有指定组件类型的实体 ID 列表。

        优化策略：从拥有最少实例的组件类型开始遍历（最小集优化），
        减少需要检查的实体数量，提升大世界查询效率。
        """
        if not comp_types:
            return list(self.entities)
        # 找出实例数最少的组件类型作为遍历起点
        smallest = min(
            (self._components.get(ct, {}) for ct in comp_types),
            key=lambda d: len(d),
        )
        result = []
        required = set(comp_types)
        # 只检查最小集合中的实体，验证它们是否拥有所有必需组件
        for eid in smallest:
            if all(
                eid in self._components.get(ct, {})
                for ct in required
            ):
                result.append(eid)
        return result

    def add_system(self, system):
        """注册系统。系统按添加顺序在每次 update 时依次执行。"""
        self._systems.append(system)

    def update(self, dt: float):
        """执行一帧：清理待销毁实体，然后依次运行所有系统。

        在系统运行前后各清理一次销毁队列，确保系统不处理已死实体，
        同时系统内部标记的销毁也能及时生效。
        """
        self._flush_destroyed()
        for system in self._systems:
            system.update(self, dt)
        self._flush_destroyed()
