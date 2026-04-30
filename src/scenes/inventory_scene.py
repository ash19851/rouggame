"""背包/装备场景 - 管理背包物品和已装备栏位。Tab/Esc 关闭。"""

import pygame
from src.scenes.base_scene import BaseScene
from src.core.engine import screen_to_virtual
from src.core.keyboard import is_key_down
from src.ui.text_renderer import draw_text
from src.data.equipment_defs import RARITY_COLORS, SLOT_LABELS, EQUIPMENT_DEFS
from src.ecs.components.equipment import Equipment
from src.ecs.components.inventory import Inventory
from src.graphics.sprite_atlas import get_sprite

# 布局常量
SLOT_SIZE = 52
SLOT_GAP = 8
GRID_COLS = 3
GRID_ROWS = 2
GRID_X = 90
GRID_Y = 80
EQ_X = 288
EQ_Y = 80
EQ_LABEL_X = 268
INFO_Y = 260
HINT_Y = 330


class InventoryScene(BaseScene):
    """背包管理覆盖层场景。

    左侧显示 3x2 背包网格，右侧显示装备栏位（武器/护甲/饰品）。
    支持左键选择/装备、右键卸下、拖拽交换物品。
    """

    def __init__(self, engine):
        self.engine = engine
        self._world = None
        self._player_eid: int = -1
        self._eq_system = None
        self._selected_inv: int = -1       # -1 = 无选中, 0-5 = 背包格
        self._hovered_inv: int = -1        # 悬停的背包格索引
        self._hovered_eq: str | None = None  # 悬停的装备栏位 ("weapon"/"armor"/"accessory")
        self._close_cooldown: float = 0.0  # 关闭冷却，防止打开瞬间又被关闭

    def on_enter(self, state_machine, **data):
        """进入场景，接收世界实例和玩家数据。"""
        self.state_machine = state_machine
        self._world = data["world"]
        self._player_eid = data["player_eid"]
        self._eq_system = data["equipment_system"]
        self._selected_inv = -1
        self._hovered_inv = -1
        self._hovered_eq = None
        self._close_cooldown = 0.3

    def on_exit(self):
        pass

    def handle_events(self, events: list[pygame.event.Event]):
        """处理鼠标交互：左键选择/装备/交换、右键卸下装备。"""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = screen_to_virtual(*event.pos)
                if event.button == 1:  # 左键
                    # 检查是否点击了装备栏位
                    eq_slot = self._eq_slot_at(mx, my)
                    if eq_slot:
                        if self._selected_inv >= 0:
                            # 尝试将选中的背包物品装备到该栏位
                            item = self._get_backpack_slot(self._selected_inv)
                            if item and item.get("slot") == eq_slot:
                                self._eq_system.equip_item(self._world, self._player_eid, self._selected_inv)
                            self._selected_inv = -1
                        else:
                            # 点击空/不兼容的装备栏位 → 取消选择
                            pass
                        return

                    # 检查是否点击了背包格子
                    inv_slot = self._inv_slot_at(mx, my)
                    if inv_slot >= 0:
                        item = self._get_backpack_slot(inv_slot)
                        if item:
                            # 选中该背包格（再次点击取消选中）
                            self._selected_inv = inv_slot if self._selected_inv != inv_slot else -1
                        elif self._selected_inv >= 0:
                            # 将选中的物品移动到空槽位（简单的背包内排序）
                            self._move_inv_item(self._selected_inv, inv_slot)
                            self._selected_inv = -1
                        else:
                            self._selected_inv = -1
                        return

                    # 点击其他区域 → 取消选择
                    self._selected_inv = -1

                elif event.button == 3:  # 右键
                    mx, my = screen_to_virtual(*event.pos)
                    # 右键背包格 → 销毁物品
                    inv_slot = self._inv_slot_at(mx, my)
                    if inv_slot >= 0:
                        item = self._get_backpack_slot(inv_slot)
                        if item:
                            self._destroy_backpack_item(inv_slot)
                            if self._selected_inv == inv_slot:
                                self._selected_inv = -1
                            return
                    # 右键装备栏位 → 卸下装备
                    eq_slot = self._eq_slot_at(mx, my)
                    if eq_slot:
                        self._eq_system.unequip_item(self._world, self._player_eid, eq_slot)
                        return

            elif event.type == pygame.MOUSEMOTION:
                mx, my = screen_to_virtual(*event.pos)
                self._hovered_inv = self._inv_slot_at(mx, my)
                self._hovered_eq = self._eq_slot_at(mx, my)

    def _inv_slot_at(self, mx: float, my: float) -> int:
        """返回鼠标位置对应的背包格索引 (0-5)，未命中返回 -1。"""
        col = int((mx - GRID_X) // (SLOT_SIZE + SLOT_GAP))
        row = int((my - GRID_Y) // (SLOT_SIZE + SLOT_GAP))
        # 检查是否在格子内部（而非缝隙）
        sx = GRID_X + col * (SLOT_SIZE + SLOT_GAP)
        sy = GRID_Y + row * (SLOT_SIZE + SLOT_GAP)
        if sx <= mx < sx + SLOT_SIZE and sy <= my < sy + SLOT_SIZE:
            if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                return row * GRID_COLS + col
        return -1

    def _eq_slot_at(self, mx: float, my: float) -> str | None:
        """返回鼠标位置对应的装备栏位名称，未命中返回 None。"""
        slots = [("weapon", 0), ("armor", 1), ("accessory", 2)]
        mx_int, my_int = int(mx), int(my)
        for name, idx in slots:
            sy = EQ_Y + idx * (SLOT_SIZE + SLOT_GAP)
            if EQ_X <= mx_int < EQ_X + SLOT_SIZE and sy <= my_int < sy + SLOT_SIZE:
                return name
        return None

    def _get_backpack_slot(self, idx: int) -> dict | None:
        """获取指定索引处的背包物品。"""
        inv = self._world.get_component(self._player_eid, Inventory)
        if inv and 0 <= idx < len(inv.backpack):
            return inv.backpack[idx]
        return None

    def _move_inv_item(self, from_idx: int, to_idx: int):
        """交换两个背包格子中的物品。"""
        inv = self._world.get_component(self._player_eid, Inventory)
        if inv:
            inv.backpack[from_idx], inv.backpack[to_idx] = inv.backpack[to_idx], inv.backpack[from_idx]

    def _destroy_backpack_item(self, idx: int):
        """销毁指定背包格中的物品，后续物品前移填充空位。"""
        inv = self._world.get_component(self._player_eid, Inventory)
        if inv and 0 <= idx < len(inv.backpack):
            inv.backpack[idx] = None
            # 压缩空位：将后面非空物品前移
            non_empty = [item for item in inv.backpack if item is not None]
            while len(non_empty) < len(inv.backpack):
                non_empty.append(None)
            inv.backpack[:] = non_empty

    def update(self, dt: float):
        """冷却期间不处理关闭按键，防止 Tab 打开背包后立即关闭。"""
        if self._close_cooldown > 0:
            self._close_cooldown -= dt
            return
        if is_key_down(pygame.K_TAB) or is_key_down(pygame.K_ESCAPE) or is_key_down(pygame.K_i):
            self.state_machine.pop()

    def render(self, surface: pygame.Surface):
        """渲染背包界面：遮罩、标题、背包网格、装备栏位和物品详情。"""
        # 半透明遮罩
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surface.blit(dim, (0, 0))

        vw, vh = surface.get_size()
        cx = vw // 2

        # 标题
        draw_text(surface, "背包", cx, 28, size=24, color=(255, 215, 0), center=True, shadow=True)

        # 绘制背包格子
        draw_text(surface, "背包", GRID_X + (GRID_COLS * (SLOT_SIZE + SLOT_GAP) - SLOT_GAP) // 2,
                  GRID_Y - 18, size=12, color=(160, 160, 160), center=True)
        for i in range(GRID_ROWS * GRID_COLS):
            col = i % GRID_COLS
            row = i // GRID_COLS
            sx = GRID_X + col * (SLOT_SIZE + SLOT_GAP)
            sy = GRID_Y + row * (SLOT_SIZE + SLOT_GAP)
            item = self._get_backpack_slot(i)
            self._draw_slot(surface, sx, sy, item, highlight=(i == self._selected_inv))

        # 绘制装备栏位
        draw_text(surface, "已装备", EQ_X + SLOT_SIZE // 2, GRID_Y - 18,
                  size=12, color=(160, 160, 160), center=True)
        eq = self._world.get_component(self._player_eid, Equipment)
        eq_slots = [("weapon", 0), ("armor", 1), ("accessory", 2)]
        for name, idx in eq_slots:
            sy = EQ_Y + idx * (SLOT_SIZE + SLOT_GAP)
            label = SLOT_LABELS.get(name, "?")
            draw_text(surface, f"[{label}]", EQ_LABEL_X, sy + SLOT_SIZE // 2 - 5,
                      size=12, color=(140, 140, 160))
            item = eq.items.get(name) if eq else None
            highlight = name == self._hovered_eq and self._selected_inv < 0
            self._draw_slot(surface, EQ_X, sy, item, highlight=highlight)

        # 物品详情/提示
        self._draw_info(surface)

        # 操作说明
        draw_text(surface, "[Tab/Esc] 关闭  [左键] 选择/装备  [右键背包] 销毁  [右键装备] 卸下",
                  cx, HINT_Y, size=10, color=(120, 120, 140), center=True)

    def _draw_slot(self, surface, x: int, y: int, item: dict | None, highlight: bool = False):
        """绘制单个物品槽位（背景、稀有度边框、图标、名称和栏位标签）。"""
        # 槽位背景
        bg_color = (35, 35, 45) if item else (25, 25, 30)
        pygame.draw.rect(surface, bg_color, (x, y, SLOT_SIZE, SLOT_SIZE))

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
        pygame.draw.rect(surface, border_color, (x, y, SLOT_SIZE, SLOT_SIZE), border_width)

        if item:
            rarity_color = tuple(RARITY_COLORS.get(item.get("rarity", "common"), (200, 200, 200)))

            # 图标精灵（居中显示）
            icon_name = item.get("icon_sprite", "")
            if icon_name:
                icon_surf = get_sprite(icon_name)
                if icon_surf:
                    ix = x + (SLOT_SIZE - icon_surf.get_width()) // 2
                    iy = y + (SLOT_SIZE - icon_surf.get_height()) // 2 - 2
                    surface.blit(icon_surf, (ix, iy))

            # 物品名称（截断显示，在图标下方）
            name = item["name"]
            draw_text(surface, name[:10], x + SLOT_SIZE // 2, y + SLOT_SIZE - 6,
                      size=8, color=rarity_color, center=True)

            # 栏位类型标签（左上角）
            slot_label = SLOT_LABELS.get(item.get("slot", ""), "?")
            draw_text(surface, slot_label, x + 4, y + 4, size=8, color=(120, 120, 140))

    def _draw_info(self, surface):
        """绘制物品详细信息面板。

        优先级：选中背包物品 > 悬停背包物品 > 悬停装备。
        显示物品名称、稀有度和属性加成。
        """
        item = None
        source = ""

        # 优先级：选中背包 > 悬停背包 > 悬停装备
        if self._selected_inv >= 0:
            item = self._get_backpack_slot(self._selected_inv)
            source = "Backpack"
        elif self._hovered_inv >= 0:
            item = self._get_backpack_slot(self._hovered_inv)
            source = "Backpack"
        elif self._hovered_eq:
            eq = self._world.get_component(self._player_eid, Equipment)
            if eq:
                item = eq.items.get(self._hovered_eq)
                source = SLOT_LABELS.get(self._hovered_eq, self._hovered_eq)

        if item is None:
            # 选中物品与悬停装备栏位不匹配时给出提示
            if self._hovered_eq and self._selected_inv >= 0:
                sel_item = self._get_backpack_slot(self._selected_inv)
                if sel_item and sel_item.get("slot") != self._hovered_eq:
                    slot_name = {"weapon": "武器", "armor": "护甲", "accessory": "饰品"}.get(self._hovered_eq, self._hovered_eq)
                    draw_text(surface, f"槽位不匹配：{sel_item['name']} 不是{slot_name}槽位",
                              surface.get_width() // 2, INFO_Y, size=10, color=(255, 150, 100), center=True)
            return

        # 显示物品名称（稀有度颜色）
        rarity_color = tuple(RARITY_COLORS.get(item.get("rarity", "common"), (200, 200, 200)))
        draw_text(surface, f"[{source}] {item['name']}", surface.get_width() // 2, INFO_Y,
                  size=12, color=rarity_color, center=True)

        # 显示物品属性
        stats = item.get("stats", {})
        stat_lines = []
        for k, v in stats.items():
            label = {
                "max_hp": "最大生命", "damage": "伤害", "attack_speed": "攻击速度",
                "move_speed": "移动速度", "range": "范围",
                "projectile_speed": "弹射速度", "projectile_size": "弹射尺寸",
            }.get(k, k)
            sign = "+" if v > 0 else ""
            stat_lines.append(f"{label}: {sign}{v}")

        if stat_lines:
            draw_text(surface, "  ".join(stat_lines), surface.get_width() // 2, INFO_Y + 18,
                      size=9, color=(180, 180, 180), center=True)
