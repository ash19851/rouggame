"""
ECS 实体模块。

实体本身不包含数据，只是一个唯一标识符（整数 ID）和可选的标签。
数据通过组件关联到实体上，由 World 管理实体与组件的映射关系。
"""


class Entity:
    """ECS 实体：轻量级包装，仅包含整数 ID 和可选标签。

    使用 __slots__ 减少内存开销。
    实体通过 __hash__ 和 __eq__ 实现以 ID 为基准的比较和哈希。
    """
    __slots__ = ('_id', 'tag')

    def __init__(self, eid: int, tag: str = ""):
        self._id = eid
        self.tag = tag

    @property
    def id(self) -> int:
        """实体的唯一标识整数 ID。"""
        return self._id

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self._id == other._id
        return False

    def __repr__(self):
        return f"Entity({self._id}, tag={self.tag!r})"
