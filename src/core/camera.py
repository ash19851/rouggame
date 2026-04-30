"""
相机模块。

管理等轴测视角的相机位置和屏幕震动效果。
相机跟随目标（通常是玩家），渲染时将世界坐标减去相机偏移进行投影。
"""


class Camera:
    """2D 世界空间相机，用于等轴测投影。

    相机位置直接表示屏幕中心在世界空间中的对应点。
    支持屏幕震动效果（受击、爆炸等反馈）。
    """

    def __init__(self, width: int, height: int):
        self.x: float = 0.0
        self.y: float = 0.0
        self.width = width
        self.height = height
        # 屏幕震动相关
        self.shake_amount: float = 0.0   # 震动幅度（像素）
        self.shake_duration: float = 0.0 # 震动总时长
        self._shake_timer: float = 0.0   # 震动剩余时间

    def follow(self, target_x: float, target_y: float):
        """让相机中心跟随目标位置。在等轴测投影中，目标将被投影到屏幕中心。"""
        self.x = target_x
        self.y = target_y

    def shake(self, amount: float, duration: float):
        """触发屏幕震动。amount 为像素偏移幅度，duration 为持续时间（秒）。"""
        self.shake_amount = amount
        self.shake_duration = duration
        self._shake_timer = duration

    def update(self, dt: float):
        """更新震动计时器，震动结束后自动归零震动幅度。"""
        if self._shake_timer > 0:
            self._shake_timer -= dt
        else:
            self.shake_amount = 0.0

    @property
    def offset(self) -> tuple[float, float]:
        """当前帧的相机偏移（含震动偏移）。

        震动期间每一帧随机偏移，产生抖动效果。
        """
        import random
        if self._shake_timer > 0:
            # 在震动幅度范围内随机偏移
            sx = random.uniform(-self.shake_amount, self.shake_amount)
            sy = random.uniform(-self.shake_amount, self.shake_amount)
            return (self.x + sx, self.y + sy)
        return (self.x, self.y)
