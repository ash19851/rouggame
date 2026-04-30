"""装备存档 —— 将玩家已装备物品和背包存储到 JSON 文件，支持读写。"""

import json
import os


def _get_save_path() -> str:
    """获取装备存档文件路径。"""
    return os.path.join(
        os.path.dirname(__file__), "..", "..", "assets", "configs", "equipment.json"
    )


def load_equipment() -> dict:
    """从 JSON 加载装备数据，返回 {"equipped": {...}, "inventory": [...]} 字典。"""
    path = _get_save_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        equipped = data.get("equipped", {})
        inventory = data.get("inventory", [])
        return {"equipped": equipped, "inventory": inventory}
    except (json.JSONDecodeError, OSError):
        return {}


def save_equipment(equipped: dict[str, dict], inventory: list[dict | None]) -> None:
    """将已装备物品和背包列表保存到 JSON 文件。"""
    path = _get_save_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    serialized_inv = [item for item in inventory]
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"equipped": equipped, "inventory": serialized_inv}, f, indent=2, ensure_ascii=False)
