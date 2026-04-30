"""敌方投射物组件 —— 标记实体为敌方投射物，使其攻击玩家而非敌人。"""

from dataclasses import dataclass
from src.ecs.component import Component


@dataclass
class EnemyProjectile(Component):
    """敌方投射物标记组件：拥有此组件的投射物会碰撞并伤害玩家，而非敌人。"""
    pass
