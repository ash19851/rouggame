"""粒子组件 —— 管理粒子特效的生命周期、外观和物理属性。"""

from dataclasses import dataclass
from src.ecs.component import Component


@dataclass
class Particle(Component):
    """粒子组件：定义粒子的存活时间、颜色、大小、运动、淡出和重力等参数。"""
    lifetime: float = 1.0  # 粒子最大存活时间（秒）
    age: float = 0.0  # 粒子已存活时间（秒）
    color: tuple[int, int, int] = (255, 255, 255)  # 粒子颜色 (R, G, B)
    size: float = 4.0  # 粒子大小（像素）
    vx: float = 0.0  # X 轴速度（像素/秒）
    vy: float = 0.0  # Y 轴速度（像素/秒）
    fade: bool = True  # 是否随时间淡出
    shrink: bool = True  # 是否随时间缩小
    gravity: float = 0.0  # 重力加速度（像素/秒²）

    @property
    def alive(self) -> bool:
        """粒子是否存活（年龄未超过最大存活时间）。"""
        return self.age < self.lifetime

    @property
    def alpha(self) -> float:
        """当前透明度（0.0 ~ 1.0），根据年龄和 lifetime 线性衰减。"""
        if not self.fade:
            return 1.0
        return max(0.0, 1.0 - self.age / self.lifetime)
