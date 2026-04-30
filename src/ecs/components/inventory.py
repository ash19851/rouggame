"""背包组件 —— 管理实体背包中的物品列表。"""

from dataclasses import dataclass, field
from src.ecs.component import Component


@dataclass
class Inventory(Component):
    """背包组件：存储一个固定容量（默认 6 格）的背包列表，每个格子可为空或存放物品数据。"""
    backpack: list[dict | None] = field(default_factory=lambda: [None] * 6)  # 背包槽位列表，默认 6 格，每格为物品字典或 None
