"""装备数据定义 —— 从 config_loader 重新导出，并提供槽位标签。"""

from src.data.config_loader import EQUIPMENT_DEFS, RARITY_WEIGHTS, RARITY_COLORS

# 装备槽位对应的短标签: weapon=武器, armor=护甲, accessory=饰品
SLOT_LABELS = {"weapon": "武", "armor": "甲", "accessory": "饰"}
