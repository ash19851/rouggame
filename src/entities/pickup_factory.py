"""可拾取物品实体工厂 - 创建经验球、生命恢复包和装备掉落物。"""

from src.ecs.world import World
from src.ecs.components.transform import Transform
from src.ecs.components.render import Sprite
from src.ecs.components.collision import Collider
from src.ecs.components.pickup import Pickup
from src.data.config_loader import BALANCE, EQUIPMENT_DEFS
from src.graphics.sprite_atlas import get_pickup_sprite, get_sprite


# 不同拾取物类型的颜色映射
PICKUP_COLORS = {
    "xp": (100, 255, 100),       # 经验球 - 绿色
    "health": (255, 100, 100),   # 生命 - 红色
    "equipment": (255, 215, 0),  # 装备 - 金色
}


def create_pickup(world: World, pickup_type: str, value: int, x: float, y: float,
                  equipment_id: str = "") -> int:
    """创建一个可拾取物品实体。

    Args:
        world: ECS 世界实例
        pickup_type: 拾取物类型 ("xp", "health", "equipment")
        value: 物品数值（经验量、生命量等）
        x, y: 世界坐标
        equipment_id: 装备 ID（仅装备类型有效）
    """
    eid = world.create_entity(tag="pickup")

    color = PICKUP_COLORS.get(pickup_type, (255, 255, 255))
    # 装备掉落物尺寸稍大，便于识别
    size = 6 if pickup_type != "equipment" else 8

    # 优先使用装备的图标精灵，否则使用默认拾取物精灵
    surf = None
    if pickup_type == "equipment" and equipment_id:
        eq_def = EQUIPMENT_DEFS.get(equipment_id, {})
        icon_name = eq_def.get("icon_sprite", "")
        if icon_name:
            surf = get_sprite(icon_name)
    if surf is None:
        surf = get_pickup_sprite(pickup_type)

    world.add_component(eid, Transform(x=x, y=y))
    world.add_component(eid, Sprite(
        surface=surf,
        color=color, width=size, height=size, layer=3,
    ))
    # 碰撞体略大于显示尺寸，便于玩家吸附
    world.add_component(eid, Collider(width=size + 6, height=size + 6, layer=3))
    world.add_component(eid, Pickup(pickup_type=pickup_type, value=value,
                                    magnet_range=BALANCE["pickup"]["magnet_range"],
                                    equipment_id=equipment_id))

    return eid
