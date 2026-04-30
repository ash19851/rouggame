"""装备组件 —— 管理实体身上各装备槽位的物品数据。"""

from dataclasses import dataclass, field
from src.ecs.component import Component


@dataclass
class Equipment(Component):
    """装备组件：以字典形式存储各槽位（slot）对应的装备物品数据。"""
    items: dict[str, dict] = field(default_factory=dict)  # 槽位名 -> 物品数据字典
