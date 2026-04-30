"""生命值组件 —— 管理实体的生命值、受伤、无敌帧和存活状态。"""

from dataclasses import dataclass
from src.ecs.component import Component


@dataclass
class Health(Component):
    """生命值组件：存储当前/最大生命值，提供受伤、无敌判定和存活检查。"""
    current: int = 100  # 当前生命值
    max: int = 100  # 最大生命值
    invuln_time: float = 0.0  # 受伤后无敌时间（秒）
    _invuln_timer: float = 0.0  # 无敌计时器（内部使用，秒）
    _flash_timer: float = 0.0   # 受击闪白计时器（秒）

    @property
    def alive(self) -> bool:
        """实体是否存活（当前生命值 > 0）。"""
        return self.current > 0

    @property
    def fraction(self) -> float:
        """当前生命值占最大生命值的比例（0.0 ~ 1.0）。"""
        return self.current / self.max if self.max > 0 else 0.0

    def take_damage(self, amount: int) -> bool:
        """对实体造成伤害。若处于无敌状态则无效，返回是否成功造成伤害。"""
        if self._invuln_timer > 0:
            return False
        self.current = max(0, self.current - amount)
        if amount > 0:
            self._invuln_timer = self.invuln_time
            self._flash_timer = 0.08  # 受击闪白 80ms
        return True

    def tick(self, dt: float):
        """每帧更新无敌计时器和闪白计时器。"""
        if self._invuln_timer > 0:
            self._invuln_timer -= dt
        if self._flash_timer > 0:
            self._flash_timer -= dt
