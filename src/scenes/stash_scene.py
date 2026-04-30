"""仓库管理场景 - 在持久仓库（12格）和背包（6格）之间交换装备物品。"""

import pygame
from src.scenes.base_scene import BaseScene
from src.core.engine import VIRTUAL_W, VIRTUAL_H, screen_to_virtual
from src.ui.text_renderer import draw_text
from src.data.stash_store import load_stash, save_stash
from src.data.equipment_store import load_equipment, save_equipment
from src.data.equipment_defs import RARITY_COLORS, SLOT_LABELS
from src.graphics.sprite_atlas import get_sprite

# 布局常量
SLOT = 52
GAP = 8
STASH_COLS = 4
STASH_ROWS = 3
STASH_X = 22
STASH_Y = 60
BACKPACK_COLS = 3
BACKPACK_ROWS = 2
BACKPACK_X = 286
BACKPACK_Y = 90


class StashScene(BaseScene):
    """仓库管理覆盖层场景。

    左侧 4x3 仓库（持久化存储），右侧 3x2 背包（来自 equipment.json）。
    支持在仓库和背包之间点击交换物品。可从主菜单和关卡过渡中进入。
    """

    def __init__(self, engine):
        self.engine = engine
        self._stash: list[dict | None] = []       # 仓库物品列表（12格）
        self._backpack: list[dict | None] = []    # 背包物品列表（6格）
        self._equipped: dict[str, dict] = {}      # 已装备物品
        self._selected_type: str = ""             # 选中的区域: "stash" 或 "backpack"
        self._selected_idx: int = -1              # 选中的格子索引
        self._hovered_type: str = ""              # 悬停的区域
        self._hovered_idx: int = -1               # 悬停的格子索引
        self._toast: str = ""
        self._toast_timer: float = 0.0
        self._done_rect = pygame.Rect(0, 0, 100, 30)  # "Done" 按钮矩形

    def on_enter(self, state_machine, **data):
        """进入场景，加载仓库和背包数据。"""
        self.state_machine = state_machine
        self._stash = load_stash()
        eq_data = load_equipment()
        self._equipped = eq_data.get("equipped", {})
        inv_raw = eq_data.get("inventory", [])
        # 确保背包始终有 6 个槽位
        self._backpack = list(inv_raw)
        while len(self._backpack) < 6:
            self._backpack.append(None)
        self._backpack = self._backpack[:6]
        self._selected_type = ""
        self._selected_idx = -1
        self._toast = ""
        self._toast_timer = 0.0

    def on_exit(self):
        pass

    def _slot_rect(self, slot_type: str, idx: int) -> pygame.Rect | None:
        """返回仓库或背包指定格子索引的 Rect 对象。"""
        if slot_type == "stash":
            col = idx % STASH_COLS
            row = idx // STASH_COLS
            sx = STASH_X + col * (SLOT + GAP)
            sy = STASH_Y + row * (SLOT + GAP)
            return pygame.Rect(sx, sy, SLOT, SLOT)
        elif slot_type == "backpack":
            col = idx % BACKPACK_COLS
            row = idx // BACKPACK_COLS
            sx = BACKPACK_X + col * (SLOT + GAP)
            sy = BACKPACK_Y + row * (SLOT + GAP)
            return pygame.Rect(sx, sy, SLOT, SLOT)
        return None

    def _slot_at(self, mx: float, my: float) -> tuple[str, int]:
        """返回鼠标位置命中的 (区域类型, 格子索引)，未命中返回 ("", -1)。"""
        for idx in range(12):
            r = self._slot_rect("stash", idx)
            if r and r.collidepoint(int(mx), int(my)):
                return ("stash", idx)
        for idx in range(6):
            r = self._slot_rect("backpack", idx)
            if r and r.collidepoint(mx, my):
                return ("backpack", idx)
        return ("", -1)

    def _get_items(self, slot_type: str) -> list[dict | None]:
        """返回指定区域的物品列表。"""
        return self._stash if slot_type == "stash" else self._backpack

    def _move_item(self, from_type: str, from_idx: int, to_type: str, to_idx: int):
        """在两个格子之间移动/交换物品。

        同区域内操作为交换，跨区域操作为搬移。
        """
        src = self._get_items(from_type)
        dst = self._get_items(to_type)
        item = src[from_idx]
        if to_idx >= len(dst):
            return
        other = dst[to_idx]
        if from_type == to_type:
            # 同区域内交换
            src[from_idx], src[to_idx] = other, item
        else:
            # 跨区域搬移（保留目标位置原物品到源位置）
            src[from_idx] = other
            dst[to_idx] = item

    def handle_events(self, events: list[pygame.event.Event]):
        """处理鼠标交互：选中/交换物品，Done 按钮保存退出。"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_TAB):
                    self.state_machine.pop()
                    return

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = screen_to_virtual(*event.pos)

                # Done 按钮：保存并退出
                if self._done_rect.collidepoint(mx, my):
                    self._save_and_exit()
                    return

                st, si = self._slot_at(mx, my)
                if st:
                    if self._selected_type:
                        # 从选中格子移动到点击格子
                        self._move_item(self._selected_type, self._selected_idx, st, si)
                        self._selected_type = ""
                        self._selected_idx = -1
                    else:
                        # 选中该格子（仅当有物品时）
                        items = self._get_items(st)
                        if si < len(items) and items[si] is not None:
                            self._selected_type = st
                            self._selected_idx = si
                else:
                    # 点击空白区域 → 取消选择
                    self._selected_type = ""
                    self._selected_idx = -1

            elif event.type == pygame.MOUSEMOTION:
                mx, my = screen_to_virtual(*event.pos)
                self._hovered_type, self._hovered_idx = self._slot_at(mx, my)

    def _save_and_exit(self):
        """保存仓库和装备数据到文件，并退出场景。"""
        save_stash(self._stash)
        save_equipment(equipped=self._equipped, inventory=self._backpack)
        self.state_machine.pop()

    def update(self, dt: float):
        """更新提示消息计时器。"""
        if self._toast_timer > 0:
            self._toast_timer -= dt

    def render(self, surface: pygame.Surface):
        """渲染仓库界面。"""
        surface.fill((12, 12, 22))

        cx = VIRTUAL_W // 2

        # 标题
        draw_text(surface, "仓库", cx, 24, size=22, color=(255, 215, 0), center=True, shadow=True)

        # 分区标签
        stash_cx = STASH_X + (STASH_COLS * (SLOT + GAP) - GAP) // 2
        bp_cx = BACKPACK_X + (BACKPACK_COLS * (SLOT + GAP) - GAP) // 2
        draw_text(surface, "仓库", stash_cx, STASH_Y - 14, size=12, color=(160, 160, 160), center=True)
        draw_text(surface, "背包", bp_cx, BACKPACK_Y - 14, size=12, color=(160, 160, 160), center=True)

        # 绘制仓库格子（12格）
        for i in range(12):
            r = self._slot_rect("stash", i)
            if r:
                highlight = (self._selected_type == "stash" and self._selected_idx == i)
                self._draw_slot(surface, r.x, r.y, self._stash[i], highlight)

        # 绘制背包格子（6格）
        for i in range(6):
            r = self._slot_rect("backpack", i)
            if r:
                highlight = (self._selected_type == "backpack" and self._selected_idx == i)
                self._draw_slot(surface, r.x, r.y, self._backpack[i], highlight)

        # 物品详情信息
        self._draw_info(surface)

        # Done 按钮
        self._done_rect.centerx = cx
        self._done_rect.y = VIRTUAL_H - 42
        mx, my = screen_to_virtual(*pygame.mouse.get_pos())
        # 悬停时高亮
        btn_color = (80, 80, 140) if not self._done_rect.collidepoint(mx, my) else (100, 100, 180)
        pygame.draw.rect(surface, btn_color, self._done_rect, border_radius=4)
        pygame.draw.rect(surface, (120, 120, 200), self._done_rect, 2, border_radius=4)
        draw_text(surface, "完成", self._done_rect.centerx, self._done_rect.centery,
                  size=16, center=True, shadow=True)

    def _draw_slot(self, surface, x: int, y: int, item: dict | None, highlight: bool):
        """绘制单个物品槽位（背景、稀有度边框、图标、名称）。"""
        # 槽位背景
        bg_color = (35, 35, 45) if item else (25, 25, 30)
        pygame.draw.rect(surface, bg_color, (x, y, SLOT, SLOT))

        # 边框：高亮 → 金色，有物品 → 稀有度颜色，空 → 灰色
        if highlight:
            border_color = (255, 215, 0)
            border_width = 2
        elif item:
            rarity = item.get("rarity", "common")
            border_color = tuple(RARITY_COLORS.get(rarity, (100, 100, 100)))
            border_width = 1
        else:
            border_color = (60, 60, 70)
            border_width = 1
        pygame.draw.rect(surface, border_color, (x, y, SLOT, SLOT), border_width)

        if item:
            rarity_color = tuple(RARITY_COLORS.get(item.get("rarity", "common"), (200, 200, 200)))

            # 图标精灵（居中）
            icon_name = item.get("icon_sprite", "")
            if icon_name:
                icon_surf = get_sprite(icon_name)
                if icon_surf:
                    ix = x + (SLOT - icon_surf.get_width()) // 2
                    iy = y + (SLOT - icon_surf.get_height()) // 2 - 2
                    surface.blit(icon_surf, (ix, iy))

            # 物品名称（截断）
            name = item["name"]
            draw_text(surface, name[:10], x + SLOT // 2, y + SLOT - 6,
                      size=8, color=rarity_color, center=True)

            # 栏位标签
            slot_label = SLOT_LABELS.get(item.get("slot", ""), "?")
            draw_text(surface, slot_label, x + 4, y + 4, size=8, color=(120, 120, 140))

    def _draw_info(self, surface):
        """绘制选中或悬停物品的详细信息（名称、稀有度、属性加成）。"""
        item = None
        source = ""

        # 优先级：选中 > 悬停
        if self._selected_type:
            items = self._get_items(self._selected_type)
            if self._selected_idx < len(items):
                item = items[self._selected_idx]
                source = self._selected_type
        elif self._hovered_type:
            items = self._get_items(self._hovered_type)
            if self._hovered_idx < len(items):
                item = items[self._hovered_idx]
                source = self._hovered_type

        if item is None:
            draw_text(surface, "点击选择，再点击目标位置移动",
                      VIRTUAL_W // 2, VIRTUAL_H - 72, size=10, color=(120, 120, 140), center=True)
            return

        rarity_color = tuple(RARITY_COLORS.get(item.get("rarity", "common"), (200, 200, 200)))
        draw_text(surface, f"[{source}] {item['name']}", VIRTUAL_W // 2, VIRTUAL_H - 72,
                  size=11, color=rarity_color, center=True)

        # 属性加成列表
        stats = item.get("stats", {})
        stat_strs = []
        for k, v in stats.items():
            label = {"max_hp": "最大生命", "damage": "伤害", "attack_speed": "攻击速度",
                     "move_speed": "移动速度", "range": "范围",
                     "projectile_speed": "弹射速度", "projectile_size": "弹射尺寸"}.get(k, k)
            stat_strs.append(f"{label}: +{v}" if v > 0 else f"{label}: {v}")
        if stat_strs:
            draw_text(surface, "  ".join(stat_strs), VIRTUAL_W // 2, VIRTUAL_H - 56,
                      size=9, color=(180, 180, 180), center=True)
