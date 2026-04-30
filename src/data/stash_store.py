"""仓库存档 —— 跨角色共享的储藏箱，12 个槽位，支持 JSON 读写。"""

import json
import os


def _get_stash_path() -> str:
    """获取仓库存档文件路径。"""
    return os.path.join(
        os.path.dirname(__file__), "..", "..", "assets", "configs", "stash.json"
    )


def load_stash() -> list[dict | None]:
    """从 JSON 加载仓库物品。返回长度为 12 的列表，每个元素为物品字典或 None。"""
    path = _get_stash_path()
    if not os.path.exists(path):
        return [None] * 12
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        stash = data.get("items", [])
        # 确保精确 12 个槽位
        while len(stash) < 12:
            stash.append(None)
        return stash[:12]
    except (json.JSONDecodeError, OSError):
        return [None] * 12


def save_stash(items: list[dict | None]) -> None:
    """将仓库物品列表保存到 JSON 文件。"""
    path = _get_stash_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    serialized = [item for item in items]
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"items": serialized}, f, indent=2, ensure_ascii=False)
