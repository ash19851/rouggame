"""Boss 组件 —— 存储 Boss 实体的专属状态：技能列表、冷却、遭遇等级和移动模式。"""

from dataclasses import dataclass, field
from src.ecs.component import Component


@dataclass
class Boss(Component):
    """Boss 组件：追踪 Boss 的技能、冷却、阶段和遭遇等级。

    Attributes:
        encounter_level: 遭遇等级（1-6），决定技能数和缩放
        skills: 当前拥有的技能键列表
        skill_cooldowns: 技能名 → 剩余冷却秒数
        skill_active: 当前执行中的技能名（空字符串表示空闲）
        skill_timer: 活跃技能剩余时间
        movement_mode: 移动模式（chase/hover/charge/teleport_move）
        show_name: Boss 血条上显示的名称
        enrage_threshold: 狂暴触发的血量比例（默认 0.5）
        enraged: 是否已进入狂暴状态
        charge_dir_x/charge_dir_y: charge 移动模式的冲撞方向
    """
    encounter_level: int = 1
    skills: list[str] = field(default_factory=list)
    skill_cooldowns: dict[str, float] = field(default_factory=dict)
    skill_active: str = ""
    skill_timer: float = 0.0
    movement_mode: str = "chase"
    show_name: str = ""
    enrage_threshold: float = 0.5
    enraged: bool = False
    charge_dir_x: float = 0.0
    charge_dir_y: float = 0.0


@dataclass
class BossMinion(Component):
    """Boss 召唤物标记：标识实体为 Boss 的分裂克隆或召唤小怪。

    Attributes:
        parent_boss_eid: 生成此单位的 Boss 实体 ID
    """
    parent_boss_eid: int = -1
