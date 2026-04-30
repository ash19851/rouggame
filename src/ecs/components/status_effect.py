"""状态效果组件 —— 追踪实体身上活跃的持续伤害、减速等效果。"""

from dataclasses import dataclass, field
from src.ecs.component import Component


@dataclass
class StatusEffect(Component):
    """状态效果组件：存储实体当前所有活跃的状态效果（中毒、减速等），每帧 tick 更新。"""
    effects: list[dict] = field(default_factory=list)  # 活跃效果列表
    # 每个效果字典格式：{"type": "poison"|"slow", "tick_interval": float, "tick_timer": float,
    #                    "remaining_ticks": int, "damage": int, "slow_pct": float, "duration": float}
    # type: 效果类型（poison=中毒, slow=减速）
    # tick_interval: 每次触发间隔（秒）
    # tick_timer: 距离下次触发的剩余时间（秒）
    # remaining_ticks: 剩余触发次数
    # damage: 每次触发造成的伤害
    # slow_pct: 减速百分比
    # duration: 总持续时间（秒）
