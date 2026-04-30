"""玩家组件 —— 管理玩家实体的瞄准方向、经验等级、属性和生存状态。"""

from dataclasses import dataclass
from src.ecs.component import Component


@dataclass
class Player(Component):
    """玩家组件：存储玩家的瞄准方向、经验/等级、护甲、恢复以及暴击属性。"""
    aim_x: float = 1.0  # 瞄准方向 X 分量（归一化向量）
    aim_y: float = 0.0  # 瞄准方向 Y 分量（归一化向量）
    xp: int = 0  # 当前经验值
    xp_to_level: int = 30  # 升级所需经验值
    level: int = 1  # 当前等级
    is_alive: bool = True  # 玩家是否存活
    armor: int = 0  # 护甲值（减免伤害）
    regen: float = 0.0  # 生命恢复速度（点/秒）
    magnet_bonus: float = 0.0  # 磁吸范围加成（像素）
    crit_chance: float = 0.0  # 暴击概率（0.0 ~ 1.0）
    crit_mult: float = 1.5  # 暴击伤害倍率
