"""Editor screens for each config section."""

import pygame
from tools.gui_editor.widgets import (
    Label, Button, TextField, IntField, FloatField,
    ColorSwatchField, List2Field, DropdownField, ScrollList,
    TEXT_PRIMARY, TEXT_SECONDARY, PANEL_BG, BORDER_IDLE, DANGER_BG, DANGER_HOVER,
    WINDOW_SCALE,
)


# ── Field definition tables ──────────────────────────────────────────────

BALANCE_SECTION_FIELDS = {
    "player": [
        ("hp", "int"), ("damage", "int"), ("attack_speed", "float"),
        ("speed", "float"), ("range", "float"), ("projectile_speed", "float"),
        ("projectile_size", "float"), ("invuln_time", "float"), ("xp_to_level", "int"),
    ],
    "drops": [
        ("xp_min", "int"), ("xp_max", "int"), ("health_chance", "float"),
        ("health_amount", "int"), ("equipment_chance", "float"),
    ],
    "difficulty": [
        ("base_mult_per_stage", "float"), ("room_progress_bonus", "float"),
        ("enemy_speed_stage_scale_base", "float"),
        ("enemy_speed_stage_scale_mult", "float"),
    ],
    "stages": [
        ("total_stages", "int"), ("rooms_per_stage", "int"),
    ],
    "pickup": [
        ("magnet_range", "float"), ("xp_magnet_per_level", "float"),
        ("fly_speed", "float"), ("collect_distance", "float"),
    ],
    "enemy_spawn": [
        ("initial_delay", "float"), ("wave_interval_min", "float"),
        ("wave_interval_max", "float"), ("spawn_initial_fraction", "float"),
        ("min_spawn_distance", "float"),
    ],
}

ENEMY_FIELD_LAYOUT = [
    ("sprite_name", "sprite_dropdown"),
    ("ai_mode", "ai_dropdown"),
    ("hp", "int"),
    ("damage", "int"),
    ("speed", "float"),
    ("attack_speed", "float"),
    ("attack_range", "float"),
    ("aggro_range", "float"),
    ("xp_value", "int"),
]

AI_MODE_OPTIONS = ["chase", "ranged", "dash"]

SLOT_OPTIONS = ["weapon", "armor", "accessory"]
RARITY_OPTIONS = ["common", "rare", "epic"]


# ── Chinese display name mappings ────────────────────────────────────────

SECTION_NAMES = {
    "player": "玩家",
    "drops": "掉落",
    "difficulty": "难度",
    "stages": "关卡",
    "pickup": "拾取",
    "enemy_spawn": "敌人生成",
}

FIELD_NAMES = {
    # Balance — player
    "hp": "生命值", "damage": "伤害", "attack_speed": "攻击速度",
    "speed": "移动速度", "range": "射程", "projectile_speed": "弹道速度",
    "projectile_size": "弹道大小", "invuln_time": "无敌时间",
    "xp_to_level": "升级经验",
    # Balance — drops
    "xp_min": "经验最小值", "xp_max": "经验最大值",
    "health_chance": "生命掉落率", "health_amount": "生命回复量",
    "equipment_chance": "装备掉落率",
    # Balance — difficulty
    "base_mult_per_stage": "每关基础倍率",
    "room_progress_bonus": "房间进度加成",
    "enemy_speed_stage_scale_base": "敌人速度基础缩放",
    "enemy_speed_stage_scale_mult": "敌人速度缩放倍率",
    # Balance — stages
    "total_stages": "总关卡数", "rooms_per_stage": "每关房间数",
    # Balance — pickup
    "magnet_range": "磁铁范围", "xp_magnet_per_level": "经验磁铁/级",
    "fly_speed": "飞行速度", "collect_distance": "拾取距离",
    # Balance — enemy_spawn
    "initial_delay": "初始延迟", "wave_interval_min": "波次最小间隔",
    "wave_interval_max": "波次最大间隔", "spawn_initial_fraction": "初始生成比例",
    "min_spawn_distance": "最小生成距离",
    # Enemy fields
    "name": "名称", "size": "大小", "color": "颜色",
    "sprite_name": "精灵", "ai_mode": "AI模式",
    # Upgrade fields
    "label": "标签", "desc": "描述", "key": "键名", "amount": "数值",
    # Equipment
    "slot": "槽位", "rarity": "稀有度", "stats": "属性",
    "common": "普通", "rare": "稀有", "epic": "史诗",
}


def _fn(name: str) -> str:
    """Return Chinese display name for a field/section key, or the key itself."""
    return FIELD_NAMES.get(name, name)


def _sec(name: str) -> str:
    """Return Chinese display name for a section key, or the key itself."""
    return SECTION_NAMES.get(name, name)


# ── Field descriptions (shown in bottom help bar on hover) ────────────

FIELD_DESCRIPTIONS = {
    # Enemy fields
    "sprite_name": "敌人在游戏中的像素画外观，可从预设精灵或自定义PNG中选择",
    "ai_mode": "AI行为模式：chase=追击玩家 / ranged=远程射击 / dash=周期性冲刺",
    "hp": "敌人生命值，归零时死亡",
    "damage": "敌人每次攻击造成的伤害值",
    "speed": "敌人移动速度（像素/秒）",
    "attack_speed": "敌人攻击频率（次/秒），数值越大攻击越快",
    "attack_range": "敌人攻击距离（像素），决定多远开始攻击",
    "aggro_range": "敌人警觉范围（像素），玩家进入此范围后开始追击",
    "xp_value": "击杀该敌人获得的经验值",
    "name": "敌人显示名称",
    "color": "敌人像素画的主色调（RGB）",
    "size": "敌人碰撞体积 [宽, 高]（像素）",
    # Balance — player
    "PlayerSprite": "玩家角色的像素画外观",
    # Balance — drops
    "xp_min": "击杀敌人掉落的最小经验球数量",
    "xp_max": "击杀敌人掉落的最大经验球数量",
    "health_chance": "击杀敌人掉落生命恢复道具的概率（0~1）",
    "health_amount": "生命恢复道具的回复量",
    "equipment_chance": "击杀敌人掉落装备的概率（0~1）",
    # Balance — difficulty
    "base_mult_per_stage": "每通过一关，敌人属性的基础倍率提升",
    "room_progress_bonus": "同一关内每通过一个房间的难度加成",
    "enemy_speed_stage_scale_base": "敌人速度随关卡提升的基础缩放值",
    "enemy_speed_stage_scale_mult": "敌人速度随关卡提升的倍率系数",
    # Balance — stages
    "total_stages": "游戏总关卡数",
    "rooms_per_stage": "每关包含的房间数量",
    # Balance — pickup
    "magnet_range": "自动吸附经验球的基础范围（像素）",
    "xp_magnet_per_level": "每升一级磁铁范围增加的值",
    "fly_speed": "经验球飞向玩家的速度",
    "collect_distance": "玩家手动拾取道具的距离（像素）",
    # Balance — enemy_spawn
    "initial_delay": "进入房间后第一波敌人的延迟（秒）",
    "wave_interval_min": "波次之间的最小间隔（秒）",
    "wave_interval_max": "波次之间的最大间隔（秒）",
    "spawn_initial_fraction": "首波敌人占总数的比例（0~1）",
    "min_spawn_distance": "敌人生成时距离玩家的最小距离（像素）",
    # Equipment
    "icon_sprite": "装备在背包/HUD中显示的图标",
    "pattern": "装备的攻击模式：normal=单发 / scatter=散射 / orbital=环绕 / wave=波形 / impact=撞击",
    "slot": "装备槽位：weapon=武器 / armor=护甲 / accessory=饰品",
    "rarity": "稀有度：common=普通 / rare=稀有 / epic=史诗",
    "stats": "装备提供的属性加成，可添加/修改/删除属性条目",
    # Upgrades
    "label": "升级卡牌上显示的名称",
    "desc": "升级卡牌上的描述文字",
    "key": "升级对应的玩家属性键名",
    "amount": "升级增加的数值",
    "cards_shown": "每次升级时展示的卡牌数量",
    "xp_curve_mult": "经验曲线倍率，越大则每级所需经验越多",
    "crit_chance": "暴击几率（0~0.8），每次攻击有几率造成暴击伤害",
    "crit_mult": "暴击伤害倍率，暴击时伤害 = 基础伤害 × 倍率",
}


def _desc(name: str) -> str:
    """Return Chinese description for a field key, or empty string."""
    return FIELD_DESCRIPTIONS.get(name, "")


def draw_help_bar(surface: pygame.Surface, text: str):
    """Draw a help bar at the bottom of the virtual surface."""
    bar_rect = pygame.Rect(0, 286, 480, 14)
    pygame.draw.rect(surface, (25, 25, 38), bar_rect)
    pygame.draw.line(surface, BORDER_IDLE, (0, 286), (480, 286), 1)
    if text:
        from src.ui.text_renderer import draw_text
        draw_text(surface, text, 240, 293, size=9, color=(180, 180, 200), center=True)


# ── Helper to build back button ─────────────────────────────────────────

def _back_btn(on_click):
    return Button(8, 6, 55, 18, "← 返回", font_size=11, on_click=on_click)


# ══════════════════════════════════════════════════════════════════════════
# MainMenuScreen
# ══════════════════════════════════════════════════════════════════════════

class MainMenuScreen:
    def __init__(self):
        self.buttons = [
            Button(140, 70, 90, 40, "敌人", font_size=15,
                   on_click=self._go_enemies),
            Button(250, 70, 90, 40, "装备", font_size=15,
                   on_click=self._go_equipment),
            Button(140, 120, 90, 40, "升级", font_size=15,
                   on_click=self._go_upgrades),
            Button(250, 120, 90, 40, "平衡", font_size=15,
                   on_click=self._go_balance),
        ]
        self.action_btns = [
            Button(120, 215, 80, 22, "保存全部", font_size=12,
                   on_click=self._save),
            Button(220, 215, 80, 22, "重置全部", font_size=12,
                   danger=True, on_click=self._reset_confirm),
            Button(320, 215, 40, 22, "退出", font_size=12,
                   on_click=self._quit),
        ]
        self._app = None
        self._confirm_reset = False

    def _go_enemies(self):
        self._app.push_screen(EnemiesScreen())

    def _go_equipment(self):
        self._app.push_screen(EquipmentScreen())

    def _go_upgrades(self):
        self._app.push_screen(UpgradesScreen())

    def _go_balance(self):
        self._app.push_screen(BalanceScreen())

    def _save(self):
        self._app.save_all()

    def _reset_confirm(self):
        if self._confirm_reset:
            self._app.reset_all()
            self._confirm_reset = False
        else:
            self._confirm_reset = True

    def _quit(self):
        self._app.running = False

    def handle_events(self, events: list[pygame.event.Event], app):
        self._app = app
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self._confirm_reset:
                    self._confirm_reset = False
            for b in self.buttons + self.action_btns:
                b.handle_event(e)

    def update(self, _dt: float, _app):
        pass

    def render(self, surface: pygame.Surface, app):
        Label(240, 30, "配置编辑器", font_size=22, color=TEXT_PRIMARY,
              center=True).render(surface)
        Label(240, 48, "选择要编辑的类别", font_size=11,
              color=TEXT_SECONDARY, center=True).render(surface)

        for b in self.buttons:
            b.render(surface)

        pygame.draw.line(surface, BORDER_IDLE, (60, 190), (420, 190), 1)

        for b in self.action_btns:
            b.render(surface)

        if self._confirm_reset:
            Label(240, 200, "再次点击重置全部以确认",
                  font_size=11, color=(255, 150, 150), center=True).render(surface)

        draw_help_bar(surface, "将鼠标悬停在字段标签上可查看说明")


# ══════════════════════════════════════════════════════════════════════════
# BalanceScreen
# ══════════════════════════════════════════════════════════════════════════

class BalanceScreen:
    SECTIONS = list(BALANCE_SECTION_FIELDS.keys())
    SECTION_DISPLAY = [_sec(k) for k in SECTIONS]
    ROW_H = 42       # label(15px) + gap(2px) + field(22px) + gap(3px)

    def __init__(self):
        self._section_list = ScrollList(
            8, 34, 115, 254, self.SECTION_DISPLAY,
            row_height=26, font_size=12, on_select=self._on_section_select)
        self._selected_section = "player"
        self._section_list.select_index(0)
        self._field_widgets: dict[str, object] = {}
        self._form_x = 138
        self._form_y = 60
        self._back_btn = _back_btn(self._go_back)
        self._app = None
        self._form_clip = pygame.Rect(135, 44, 338, 248)
        self._form_scroll = 0
        self._form_content_h = 0
        self._base_y: dict[str, int] = {}
        self._sprite_drop = None
        self._sprite_drop_base_y = 0
        self._help_text = ""

    def _go_back(self):
        if self._app:
            self._app.pop_screen()

    def _on_section_select(self, section_display: str):
        if self._app:
            self._app.clear_focus()
            self._sync_to_data()
        for k, v in SECTION_NAMES.items():
            if v == section_display:
                self._selected_section = k
                break
        else:
            self._selected_section = section_display
        self._form_scroll = 0
        self._build_form()
        self._populate_form()

    def _build_form(self):
        self._field_widgets.clear()
        self._base_y.clear()
        fields = BALANCE_SECTION_FIELDS[self._selected_section]
        for i, (fname, ftype) in enumerate(fields):
            row_y = self._form_y + i * self.ROW_H
            # field goes below the label
            field_y = row_y + 14
            self._base_y[fname] = field_y
            if ftype == "int":
                w = IntField(self._form_x, field_y, 180, 22, font_size=12)
            else:
                w = FloatField(self._form_x, field_y, 180, 22, font_size=12)
            self._field_widgets[fname] = w
        if self._selected_section == "player":
            from src.graphics.sprite_atlas import list_enemy_sprites, list_custom_sprites
            sprite_options = ["player"] + list_enemy_sprites() + list_custom_sprites()
            drop_y = self._form_y + len(fields) * self.ROW_H + 4
            self._sprite_drop_base_y = drop_y
            self._sprite_drop = DropdownField(self._form_x, drop_y, 100, 18, sprite_options,
                                               font_size=11)
        else:
            self._sprite_drop = None

        total_rows = len(fields) + (1 if self._sprite_drop else 0)
        self._form_content_h = total_rows * self.ROW_H
        self._form_scroll = 0

    def _apply_scroll(self):
        for fname, w in self._field_widgets.items():
            w.rect.y = self._base_y.get(fname, w.rect.y) - self._form_scroll
        if self._sprite_drop:
            self._sprite_drop.rect.y = self._sprite_drop_base_y - self._form_scroll

    def _populate_form(self):
        data = self._app.data["balance"][self._selected_section]
        for fname, w in self._field_widgets.items():
            if fname in data:
                w.set_value(data[fname])
        if self._sprite_drop and self._selected_section == "player":
            from src.graphics.sprite_atlas import list_enemy_sprites, list_custom_sprites
            self._sprite_drop.options = ["player"] + list_enemy_sprites() + list_custom_sprites()
            self._sprite_drop.set_value(data.get("sprite_name", "player"))

    def handle_events(self, events: list[pygame.event.Event], app):
        self._app = app
        for e in events:
            self._back_btn.handle_event(e)
            self._section_list.handle_event(e)

            if e.type == pygame.MOUSEWHEEL:
                mx = (e.pos[0] if hasattr(e, 'pos') else pygame.mouse.get_pos()[0]) // WINDOW_SCALE
                my = (e.pos[1] if hasattr(e, 'pos') else pygame.mouse.get_pos()[1]) // WINDOW_SCALE
                if self._form_clip.collidepoint(mx, my):
                    max_scroll = max(0, self._form_content_h - self._form_clip.height)
                    self._form_scroll -= e.y * 22
                    self._form_scroll = max(0, min(max_scroll, self._form_scroll))
                    self._apply_scroll()

            for w in self._field_widgets.values():
                w.handle_event(e, app)
            if self._sprite_drop:
                self._sprite_drop.handle_event(e, app)

    def update(self, dt: float, _app):
        self._app = _app
        if not self._field_widgets:
            self._build_form()
            self._populate_form()
        for w in self._field_widgets.values():
            w.update(dt)

    def render(self, surface: pygame.Surface, app):
        mx = pygame.mouse.get_pos()[0] // WINDOW_SCALE
        my = pygame.mouse.get_pos()[1] // WINDOW_SCALE
        self._help_text = ""

        Label(240, 8, "平衡", font_size=17, color=TEXT_PRIMARY,
              center=True).render(surface)
        self._back_btn.render(surface)
        self._section_list.render(surface)

        Label(self._form_x, 34, _sec(self._selected_section), font_size=13,
              color=TEXT_PRIMARY).render(surface)

        surface.set_clip(self._form_clip)
        for fname, w in self._field_widgets.items():
            fy = w.rect.y
            label_y = fy - 17
            if fy + 22 > self._form_clip.y and label_y < self._form_clip.bottom:
                if pygame.Rect(self._form_x, label_y, 100, 15).collidepoint(mx, my):
                    self._help_text = _desc(fname)
                Label(self._form_x, label_y, _fn(fname), font_size=11,
                      color=TEXT_SECONDARY).render(surface)
                w.render(surface, app)
        if self._sprite_drop:
            sy = self._sprite_drop.rect.y
            if sy + 18 > self._form_clip.y and sy < self._form_clip.bottom:
                if pygame.Rect(self._form_x, sy - 15, 100, 15).collidepoint(mx, my):
                    self._help_text = _desc("PlayerSprite")
                Label(self._form_x, sy - 15, _fn("sprite_name"), font_size=11,
                      color=TEXT_SECONDARY).render(surface)
                self._sprite_drop.render(surface, app)
        surface.set_clip(None)

        # Scrollbar
        if self._form_content_h > self._form_clip.height:
            sb_h = max(20, int(self._form_clip.height * self._form_clip.height / self._form_content_h))
            sb_y = self._form_clip.y + int(
                self._form_scroll / max(1, self._form_content_h - self._form_clip.height)
                * (self._form_clip.height - sb_h))
            sb_rect = pygame.Rect(self._form_clip.right - 5, sb_y, 4, sb_h)
            pygame.draw.rect(surface, BORDER_IDLE, sb_rect, border_radius=2)

        if app._focused_field is None:
            self._sync_to_data()

        draw_help_bar(surface, self._help_text)

    def _sync_to_data(self):
        data = self._app.data["balance"].get(self._selected_section, {})
        for fname, w in self._field_widgets.items():
            if isinstance(w, IntField):
                data[fname] = w.int_value
            elif isinstance(w, FloatField):
                data[fname] = w.float_value
        if self._sprite_drop and self._selected_section == "player" and self._sprite_drop.options:
            data["sprite_name"] = self._sprite_drop.get_value()


# ══════════════════════════════════════════════════════════════════════════
# EnemiesScreen
# ══════════════════════════════════════════════════════════════════════════

class EnemiesScreen:
    def __init__(self):
        self._back_btn = _back_btn(self._go_back)
        self._app = None
        self._enemy_keys: list[str] = []
        self._selected_key: str | None = None

        self._list = ScrollList(
            8, 34, 125, 230, [],
            row_height=22, font_size=12, on_select=self._on_enemy_select)

        self._label_x = 150
        self._field_x = 285
        self._name_field = TextField(self._field_x, 50, 95, 18, font_size=11,
                                      default_value="",
                                      on_commit=self._on_name_changed)
        self._field_widgets = {}
        self._base_y: dict[str, int] = {}
        self._form_clip = pygame.Rect(135, 44, 340, 236)
        self._form_scroll = 0
        self._form_content_h = 0
        self._color_field = ColorSwatchField(self._field_x, 224, on_commit=self._on_color_changed)
        self._size_field = List2Field(self._field_x + 85, 224, on_commit=self._on_size_changed)
        self._color_base_y = 224
        self._size_base_y = 224
        self._btn_base_y = 270

        self._btn_new = Button(30, 270, 75, 22, "+ 新建", font_size=12,
                                on_click=self._new_enemy)
        self._btn_delete = Button(0, 0, 42, 20, "删除", font_size=11,
                                   danger=True, on_click=self._delete_enemy)
        self._btn_duplicate = Button(0, 0, 42, 20, "复制", font_size=11,
                                      on_click=self._duplicate_enemy)
        self._help_text = ""

    def _go_back(self):
        self._save_current()
        if self._app:
            self._app.pop_screen()

    def _on_enemy_select(self, key: str):
        if self._app:
            self._app.clear_focus()
        self._save_current()
        self._selected_key = key
        self._build_form()

    def _on_name_changed(self, new_name: str):
        if not self._selected_key or not self._app:
            return
        data = self._app.data["enemies"]
        if self._selected_key in data and new_name.strip():
            old = data.pop(self._selected_key)
            self._selected_key = new_name
            data[self._selected_key] = old
            self._name_field.set_value(new_name)
            self._refresh_list()

    def _on_color_changed(self, _rgb):
        if self._selected_key:
            self._app.data["enemies"][self._selected_key]["color"] = \
                self._color_field.get_rgb()

    def _on_size_changed(self, _vals):
        if self._selected_key:
            self._app.data["enemies"][self._selected_key]["size"] = \
                self._size_field.get_vals()

    def _refresh_list(self):
        self._enemy_keys = sorted(self._app.data["enemies"].keys())
        self._list.set_items(self._enemy_keys)
        if self._selected_key in self._enemy_keys:
            self._list.select_index(self._enemy_keys.index(self._selected_key))

    def _save_current(self, _val=None):
        if not self._selected_key or not self._app:
            return
        e_data = self._app.data["enemies"].get(self._selected_key)
        if not e_data:
            return
        e_data["name"] = self._name_field.value
        for fname, w in self._field_widgets.items():
            if isinstance(w, DropdownField):
                e_data[fname] = w.get_value()
            elif isinstance(w, IntField):
                e_data[fname] = w.int_value
            elif isinstance(w, FloatField):
                e_data[fname] = w.float_value
        e_data["color"] = self._color_field.get_rgb()
        e_data["size"] = self._size_field.get_vals()

    def _build_form(self):
        self._field_widgets.clear()
        self._base_y.clear()
        self._form_scroll = 0
        if not self._selected_key or not self._app:
            return
        e_data = self._app.data["enemies"].get(self._selected_key)
        if not e_data:
            return

        self._name_field.set_value(e_data.get("name", ""))

        from src.graphics.sprite_atlas import list_enemy_sprites, list_custom_sprites
        sprite_options = list_enemy_sprites() + list_custom_sprites()

        y = 72
        for fname, ftype in ENEMY_FIELD_LAYOUT:
            self._base_y[fname] = y
            if ftype == "sprite_dropdown":
                if not sprite_options:
                    sprite_options = ["player", "skeleton"]
                cur_sprite = e_data.get(fname, sprite_options[0])
                w = DropdownField(self._field_x, y, 90, 18, sprite_options,
                                  font_size=11, on_change=self._save_current)
                w.set_value(cur_sprite)
            elif ftype == "ai_dropdown":
                cur_ai = e_data.get(fname, "chase")
                w = DropdownField(self._field_x, y, 80, 18, AI_MODE_OPTIONS,
                                  font_size=11, on_change=self._save_current)
                w.set_value(cur_ai)
            elif ftype == "int":
                val = e_data.get(fname, 0)
                w = IntField(self._field_x, y, 60, 18, font_size=11, default_value=val)
            else:
                val = e_data.get(fname, 0)
                w = FloatField(self._field_x, y, 60, 18, font_size=11, default_value=val)
            self._field_widgets[fname] = w
            y += 22

        # Color field — on its own row
        self._color_base_y = y
        for w in self._color_field.widgets:
            w.rect.y = y
        self._color_field._swatch.y = y + 1
        self._color_field.set_rgb(e_data.get("color", [255, 255, 255]))

        # Size field — on next row below color
        y += 24
        self._size_base_y = y
        for w in self._size_field.widgets:
            w.rect.y = y
        self._size_field.set_vals(e_data.get("size", [20, 28]))

        # Buttons — below size field
        y += 24
        self._btn_base_y = y
        self._btn_delete.rect.x = self._field_x
        self._btn_delete.rect.y = y
        self._btn_duplicate.rect.x = self._field_x + 48
        self._btn_duplicate.rect.y = y

        self._form_content_h = y + 24 - self._form_clip.y

    def _apply_scroll(self):
        offset = -self._form_scroll
        for fname, w in self._field_widgets.items():
            base_y = self._base_y.get(fname, w.rect.y)
            w.rect.y = base_y + offset
        for w in self._color_field.widgets:
            w.rect.y = self._color_base_y + offset
        self._color_field._swatch.y = self._color_base_y + offset + 1
        for w in self._size_field.widgets:
            w.rect.y = self._size_base_y + offset
        self._btn_delete.rect.y = self._btn_base_y + offset
        self._btn_duplicate.rect.y = self._btn_base_y + offset

    def _delete_enemy(self):
        if not self._selected_key or not self._app:
            return
        if len(self._app.data["enemies"]) <= 1:
            return
        del self._app.data["enemies"][self._selected_key]
        self._selected_key = None
        self._field_widgets.clear()
        self._refresh_list()

    def _duplicate_enemy(self):
        if not self._selected_key or not self._app:
            return
        from copy import deepcopy
        base = self._app.data["enemies"][self._selected_key]
        new_key = self._selected_key + "_copy"
        i = 1
        while new_key in self._app.data["enemies"]:
            new_key = f"{self._selected_key}_copy{i}"
            i += 1
        self._app.data["enemies"][new_key] = deepcopy(base)
        self._refresh_list()
        self._list.select_index(self._enemy_keys.index(new_key))
        self._selected_key = new_key
        self._build_form()

    def _new_enemy(self):
        if not self._app:
            return
        key = "new_enemy"
        i = 1
        while key in self._app.data["enemies"]:
            key = f"new_enemy_{i}"
            i += 1
        self._app.data["enemies"][key] = {
            "name": "新敌人", "sprite_name": "skeleton", "ai_mode": "chase",
            "color": [200, 200, 200], "size": [20, 20],
            "hp": 20, "damage": 5, "speed": 60.0, "attack_speed": 1.0,
            "attack_range": 30.0, "aggro_range": 150.0, "xp_value": 10,
        }
        self._refresh_list()
        self._list.select_index(self._enemy_keys.index(key))
        self._selected_key = key
        self._build_form()

    def handle_events(self, events: list[pygame.event.Event], app):
        self._app = app
        if not self._enemy_keys:
            self._refresh_list()
        for e in events:
            self._back_btn.handle_event(e)
            self._list.handle_event(e)

            if e.type == pygame.MOUSEWHEEL and self._selected_key:
                mx = (e.pos[0] if hasattr(e, 'pos') else pygame.mouse.get_pos()[0]) // WINDOW_SCALE
                my = (e.pos[1] if hasattr(e, 'pos') else pygame.mouse.get_pos()[1]) // WINDOW_SCALE
                if self._form_clip.collidepoint(mx, my):
                    max_scroll = max(0, self._form_content_h - self._form_clip.height)
                    self._form_scroll -= e.y * 22
                    self._form_scroll = max(0, min(max_scroll, self._form_scroll))
                    self._apply_scroll()

            self._name_field.handle_event(e, app)
            for w in self._field_widgets.values():
                w.handle_event(e, app)
            self._color_field.handle_event(e, app)
            self._size_field.handle_event(e, app)
            self._btn_delete.handle_event(e)
            self._btn_duplicate.handle_event(e)
            self._btn_new.handle_event(e)

    def update(self, dt: float, _app):
        self._app = _app
        self._name_field.update(dt)
        for w in self._field_widgets.values():
            w.update(dt)
        self._color_field.update(dt)
        self._size_field.update(dt)

        if _app._focused_field is None and self._selected_key:
            self._save_current()

    def render(self, surface: pygame.Surface, app):
        mx = pygame.mouse.get_pos()[0] // WINDOW_SCALE
        my = pygame.mouse.get_pos()[1] // WINDOW_SCALE
        self._help_text = ""

        Label(240, 8, "敌人", font_size=17, color=TEXT_PRIMARY,
              center=True).render(surface)
        self._back_btn.render(surface)

        Label(8, 28, "类型", font_size=10, color=TEXT_SECONDARY).render(surface)
        self._list.render(surface)

        self._btn_new.render(surface)

        if not self._selected_key:
            Label(195, 100, "选择一个敌人类型", font_size=13,
                  color=TEXT_SECONDARY).render(surface)
            draw_help_bar(surface, self._help_text)
            return

        Label(195, 34, self._selected_key, font_size=13, color=TEXT_PRIMARY).render(surface)

        # Name label hover
        if pygame.Rect(self._label_x, 53, 50, 12).collidepoint(mx, my):
            self._help_text = _desc("name")
        Label(self._label_x, 53, _fn("name"), font_size=10, color=TEXT_SECONDARY).render(surface)
        self._name_field.render(surface, app)

        surface.set_clip(self._form_clip)
        offset = -self._form_scroll
        y = 72 + offset
        for fname, _ in ENEMY_FIELD_LAYOUT:
            w = self._field_widgets.get(fname)
            ly = y + 5
            if ly + 12 > self._form_clip.y and y < self._form_clip.bottom:
                label_rect = pygame.Rect(self._label_x, ly, 60, 12)
                if label_rect.collidepoint(mx, my):
                    self._help_text = _desc(fname)
                Label(self._label_x, ly, _fn(fname), font_size=10, color=TEXT_SECONDARY).render(surface)
                if w and not isinstance(w, DropdownField):
                    w.render(surface, app)
            y += 22

        color_y = self._color_field._r.rect.y
        if color_y + 18 > self._form_clip.y and color_y < self._form_clip.bottom:
            if pygame.Rect(self._label_x, color_y + 2, 60, 12).collidepoint(mx, my):
                self._help_text = _desc("color")
            Label(self._label_x, color_y + 2, _fn("color"), font_size=10, color=TEXT_SECONDARY).render(surface)
            self._color_field.render(surface, app)

        size_y = self._size_field._a.rect.y
        if size_y + 18 > self._form_clip.y and size_y < self._form_clip.bottom:
            if pygame.Rect(self._label_x, size_y + 2, 60, 12).collidepoint(mx, my):
                self._help_text = _desc("size")
            Label(self._label_x, size_y + 2, _fn("size"), font_size=10, color=TEXT_SECONDARY).render(surface)
            self._size_field.render(surface, app)

        btn_y = self._btn_delete.rect.y
        if btn_y + 20 > self._form_clip.y and btn_y < self._form_clip.bottom:
            self._btn_delete.render(surface)
            self._btn_duplicate.render(surface)
        surface.set_clip(None)

        # Dropdowns rendered after clip so expanded options draw on top
        y = 72 + offset
        for fname, _ in ENEMY_FIELD_LAYOUT:
            w = self._field_widgets.get(fname)
            if isinstance(w, DropdownField):
                ly = y + 5
                if ly + 12 > self._form_clip.y and y < self._form_clip.bottom:
                    w.render(surface, app)
            y += 22

        # Scrollbar indicator
        if self._form_content_h > self._form_clip.height:
            sb_h = max(20, int(self._form_clip.height * self._form_clip.height / self._form_content_h))
            sb_y = self._form_clip.y + int(
                self._form_scroll / max(1, self._form_content_h - self._form_clip.height)
                * (self._form_clip.height - sb_h))
            sb_rect = pygame.Rect(self._form_clip.right - 5, sb_y, 4, sb_h)
            pygame.draw.rect(surface, BORDER_IDLE, sb_rect, border_radius=2)

        draw_help_bar(surface, self._help_text)


# ══════════════════════════════════════════════════════════════════════════
# UpgradesScreen
# ══════════════════════════════════════════════════════════════════════════

class UpgradesScreen:
    def __init__(self):
        self._back_btn = _back_btn(self._go_back)
        self._app = None
        self._selected_idx = -1

        self._cards_field = IntField(120, 34, 40, 17, font_size=11,
                                      default_value=3, on_commit=self._on_top_changed)
        self._xp_field = FloatField(220, 34, 50, 17, font_size=11,
                                     default_value=1.35, on_commit=self._on_top_changed)

        self._choice_list = ScrollList(
            8, 60, 464, 180, [],
            row_height=36, font_size=12, on_select=self._on_choice_select)

        self._edit_fields = {
            "label": TextField(60, 250, 120, 17, font_size=11,
                                default_value="", on_commit=self._save_choice),
            "desc": TextField(200, 250, 130, 17, font_size=11,
                               default_value="", on_commit=self._save_choice),
            "key": TextField(350, 250, 80, 17, font_size=11,
                              default_value="", on_commit=self._save_choice),
            "amount": FloatField(130, 274, 60, 17, font_size=11,
                                  default_value=0.0, on_commit=self._save_choice),
        }

        self._btn_delete = Button(200, 278, 50, 18, "删除", font_size=10,
                                   danger=True, on_click=self._delete_choice)
        self._btn_new = Button(260, 278, 50, 18, "+ 新建", font_size=10,
                                on_click=self._new_choice)

        self._populated = False
        self._help_text = ""

    def _go_back(self):
        self._save_choice("")
        if self._app:
            self._app.pop_screen()

    def _populate(self):
        if not self._app:
            return
        data = self._app.data["upgrades"]
        self._cards_field.set_value(data.get("cards_shown", 3))
        self._xp_field.set_value(data.get("xp_curve_mult", 1.35))
        self._refresh_choice_list()
        self._populated = True

    def _refresh_choice_list(self):
        choices = self._app.data["upgrades"].get("choices", [])
        labels = [f"{i+1}. {c.get('label', '?')} — {c.get('desc', '')}"
                  for i, c in enumerate(choices)]
        self._choice_list.set_items(labels)

    def _on_top_changed(self, _val):
        if not self._app:
            return
        self._app.data["upgrades"]["cards_shown"] = self._cards_field.int_value
        self._app.data["upgrades"]["xp_curve_mult"] = self._xp_field.float_value

    def _on_choice_select(self, _label):
        if self._app:
            self._app.clear_focus()
        self._save_choice("")
        self._selected_idx = -1
        for i, c in enumerate(self._app.data["upgrades"].get("choices", [])):
            display = f"{i+1}. {c.get('label', '?')} — {c.get('desc', '')}"
            if display == _label:
                self._selected_idx = i
                break
        self._load_choice_form()

    def _load_choice_form(self):
        choices = self._app.data["upgrades"].get("choices", [])
        if 0 <= self._selected_idx < len(choices):
            ch = choices[self._selected_idx]
            self._edit_fields["label"].set_value(ch.get("label", ""))
            self._edit_fields["desc"].set_value(ch.get("desc", ""))
            self._edit_fields["key"].set_value(ch.get("key", ""))
            self._edit_fields["amount"].set_value(ch.get("amount", 0))
        else:
            for f in self._edit_fields.values():
                f.set_value("")

    def _save_choice(self, _val):
        if not self._app:
            return
        choices = self._app.data["upgrades"].get("choices", [])
        if 0 <= self._selected_idx < len(choices):
            ch = choices[self._selected_idx]
            ch["label"] = self._edit_fields["label"].value
            ch["desc"] = self._edit_fields["desc"].value
            ch["key"] = self._edit_fields["key"].value
            orig = ch.get("amount", 0)
            amt = self._edit_fields["amount"].float_value
            if isinstance(orig, int) and amt == int(amt):
                ch["amount"] = int(amt)
            else:
                ch["amount"] = amt
            self._refresh_choice_list()

    def _delete_choice(self):
        if not self._app:
            return
        choices = self._app.data["upgrades"].get("choices", [])
        if 0 <= self._selected_idx < len(choices):
            del choices[self._selected_idx]
            self._selected_idx = -1
            self._load_choice_form()
            self._refresh_choice_list()

    def _new_choice(self):
        if not self._app:
            return
        choices = self._app.data["upgrades"].get("choices", [])
        new_ch = {"label": "新选项", "desc": "描述", "key": "stat", "amount": 0}
        choices.append(new_ch)
        self._selected_idx = len(choices) - 1
        self._refresh_choice_list()
        self._load_choice_form()

    def handle_events(self, events: list[pygame.event.Event], app):
        self._app = app
        if not self._populated:
            self._populate()
        for e in events:
            self._back_btn.handle_event(e)
            self._cards_field.handle_event(e, app)
            self._xp_field.handle_event(e, app)
            self._choice_list.handle_event(e)
            for f in self._edit_fields.values():
                f.handle_event(e, app)
            self._btn_delete.handle_event(e)
            self._btn_new.handle_event(e)

    def update(self, dt: float, _app):
        self._app = _app
        self._cards_field.update(dt)
        self._xp_field.update(dt)
        for f in self._edit_fields.values():
            f.update(dt)

    def render(self, surface: pygame.Surface, app):
        mx = pygame.mouse.get_pos()[0] // WINDOW_SCALE
        my = pygame.mouse.get_pos()[1] // WINDOW_SCALE
        self._help_text = ""

        Label(240, 8, "升级", font_size=17, color=TEXT_PRIMARY,
              center=True).render(surface)
        self._back_btn.render(surface)

        if pygame.Rect(8, 37, 70, 15).collidepoint(mx, my):
            self._help_text = _desc("cards_shown")
        Label(8, 37, "卡牌数量:", font_size=11, color=TEXT_SECONDARY).render(surface)
        self._cards_field.render(surface, app)
        if pygame.Rect(168, 37, 70, 15).collidepoint(mx, my):
            self._help_text = _desc("xp_curve_mult")
        Label(168, 37, "经验曲线:", font_size=11, color=TEXT_SECONDARY).render(surface)
        self._xp_field.render(surface, app)

        Label(8, 54, "选项列表", font_size=10, color=TEXT_SECONDARY).render(surface)
        self._choice_list.render(surface)

        if 0 <= self._selected_idx < len(
                self._app.data["upgrades"].get("choices", [])):
            for label, key in [("标签:", "label"), ("描述:", "desc"),
                               ("键名:", "key")]:
                f = self._edit_fields[key]
                if pygame.Rect(f.rect.x - 40, f.rect.y + 3, 40, 15).collidepoint(mx, my):
                    self._help_text = _desc(key)
                Label(f.rect.x - 40, f.rect.y + 3,
                      label, font_size=11, color=TEXT_SECONDARY).render(surface)
            for f in self._edit_fields.values():
                f.render(surface, app)

            if pygame.Rect(95, 277, 40, 15).collidepoint(mx, my):
                self._help_text = _desc("amount")
            Label(95, 277, "数值:", font_size=11, color=TEXT_SECONDARY).render(surface)
            self._btn_delete.render(surface)
            self._btn_new.render(surface)
        else:
            Label(240, 250, "选择一个选项来编辑", font_size=12,
                  color=TEXT_SECONDARY, center=True).render(surface)
            self._btn_new.render(surface)

        draw_help_bar(surface, self._help_text)


# ══════════════════════════════════════════════════════════════════════════
# EquipmentScreen
# ══════════════════════════════════════════════════════════════════════════

class EquipmentScreen:
    def __init__(self):
        self._back_btn = _back_btn(self._go_back)
        self._app = None
        self._tab = "items"
        self._selected_key: str | None = None
        self._tab_btns = [
            Button(120, 30, 60, 18, "物品", font_size=11,
                   on_click=lambda: self._switch_tab("items")),
            Button(184, 30, 70, 18, "权重", font_size=11,
                   on_click=lambda: self._switch_tab("weights")),
            Button(258, 30, 60, 18, "颜色", font_size=11,
                   on_click=lambda: self._switch_tab("colors")),
        ]

        # Items tab
        self._eq_label_x = 155
        self._eq_field_x = 265
        self._item_list = ScrollList(8, 56, 135, 225, [],
                                      row_height=22, font_size=11,
                                      on_select=self._on_item_select)
        self._name_field = TextField(self._eq_field_x, 62, 100, 17, font_size=11,
                                      default_value="",
                                      on_commit=self._save_item)
        self._slot_drop = DropdownField(self._eq_field_x, 86, 80, 17, SLOT_OPTIONS,
                                         font_size=11, on_change=self._save_item)
        self._rarity_drop = DropdownField(self._eq_field_x + 90, 86, 70, 17, RARITY_OPTIONS,
                                           font_size=11, on_change=self._save_item)
        self._icon_drop = DropdownField(0, 0, 80, 17, [],
                                         font_size=11, on_change=self._save_item)
        self._pattern_drop = DropdownField(0, 0, 80, 17, [],
                                            font_size=11, on_change=self._save_item)
        self._stat_rows: list[tuple[TextField, FloatField, Button]] = []
        self._btn_add_stat = Button(self._eq_field_x, 230, 50, 17, "+ 属性", font_size=10,
                                     on_click=self._add_stat)
        self._btn_del_item = Button(self._eq_field_x + 55, 230, 45, 17, "删除", font_size=10,
                                     danger=True, on_click=self._delete_item)
        self._btn_new_item = Button(self._eq_field_x + 105, 230, 50, 17, "+ 新建", font_size=10,
                                     on_click=self._new_item)

        # Weights tab
        self._weight_fields = {}
        # Colors tab
        self._color_widgets = {}

        self._populated = False
        self._help_text = ""

    def _go_back(self):
        self._save_item("")
        if self._app:
            self._app.pop_screen()

    def _switch_tab(self, tab: str):
        self._save_item("")
        self._tab = tab
        if tab == "weights":
            self._build_weights()
        elif tab == "colors":
            self._build_colors()

    def _items_dict(self) -> dict:
        return self._app.data["equipment"].get("items", {})

    def _populate(self):
        if not self._app:
            return
        keys = sorted(self._items_dict().keys())
        self._item_list.set_items(keys)
        self._populated = True

    # ── Items tab ─────────────────────────────────────────────────────

    def _on_item_select(self, key: str):
        if self._app:
            self._app.clear_focus()
        self._save_item("")
        self._selected_key = key
        self._load_item_form()

    def _load_item_form(self):
        self._stat_rows.clear()
        if not self._selected_key:
            return
        item = self._items_dict().get(self._selected_key)
        if not item:
            return
        self._name_field.set_value(item.get("name", ""))
        self._slot_drop.set_value(item.get("slot", "weapon"))
        self._rarity_drop.set_value(item.get("rarity", "common"))

        from src.graphics.sprite_atlas import list_icon_sprites, list_pattern_sprites
        icon_options = list_icon_sprites()
        if not icon_options:
            icon_options = ["icon_sword"]
        self._icon_drop.options = icon_options
        self._icon_drop.set_value(item.get("icon_sprite", icon_options[0]))
        pattern_options = list_pattern_sprites()
        if not pattern_options:
            pattern_options = ["pattern_normal"]
        self._pattern_drop.options = pattern_options
        self._pattern_drop.set_value(item.get("pattern", pattern_options[0]))

        stats = item.get("stats", {})
        for sk, sv in stats.items():
            self._add_stat_row(sk, sv)
        self._place_dropdowns()

    def _add_stat_row(self, key="", val=0):
        y = 86 + len(self._stat_rows) * 20
        kf = TextField(self._eq_field_x, y, 55, 16, font_size=10, default_value=key,
                        on_commit=lambda v: self._save_item(v))
        vf = FloatField(self._eq_field_x + 60, y, 45, 16, font_size=10, default_value=val,
                         on_commit=lambda v: self._save_item(v))
        xb = Button(self._eq_field_x + 110, y, 14, 16, "x", font_size=9, danger=True,
                     on_click=lambda: self._remove_stat_row(len(self._stat_rows)))
        self._stat_rows.append((kf, vf, xb))
        # stash button anchor y for repositioning later
        self._btn_add_stat.rect.y = y + 22
        self._btn_del_item.rect.y = y + 22
        self._btn_new_item.rect.y = y + 22

    def _place_dropdowns(self):
        """Position icon/pattern, slot/rarity, and buttons below stat rows."""
        anchor_y = self._btn_add_stat.rect.y
        # Icon / Pattern on first row
        row1_y = anchor_y + 8
        self._icon_drop.rect.x = self._eq_field_x
        self._icon_drop.rect.y = row1_y
        self._pattern_drop.rect.x = self._eq_field_x + 90
        self._pattern_drop.rect.y = row1_y
        # Slot / Rarity on second row
        row2_y = row1_y + 26
        self._slot_drop.rect.y = row2_y
        self._rarity_drop.rect.y = row2_y
        # Buttons below
        btn_y = row2_y + 26
        self._btn_add_stat.rect.y = btn_y
        self._btn_del_item.rect.y = btn_y
        self._btn_new_item.rect.y = btn_y

    def _add_stat(self):
        self._save_item("")
        self._add_stat_row("new_stat", 0)
        self._place_dropdowns()

    def _remove_stat_row(self, idx: int):
        self._save_item("")
        if 0 <= idx < len(self._stat_rows):
            self._stat_rows.pop(idx)
        item = self._items_dict().get(self._selected_key, {})
        stats = item.get("stats", {})
        self._stat_rows.clear()
        for sk, sv in stats.items():
            self._add_stat_row(sk, sv)

    def _save_item(self, _val):
        if not self._selected_key or not self._app:
            return
        item = self._items_dict().get(self._selected_key)
        if not item:
            return
        item["name"] = self._name_field.value
        item["slot"] = self._slot_drop.get_value()
        item["rarity"] = self._rarity_drop.get_value()
        if self._icon_drop.options:
            item["icon_sprite"] = self._icon_drop.get_value()
        if self._pattern_drop.options:
            item["pattern"] = self._pattern_drop.get_value()

        new_stats = {}
        for kf, vf, _ in self._stat_rows:
            k = kf.value.strip()
            if k:
                new_stats[k] = vf.float_value
                if vf.float_value == int(vf.float_value):
                    new_stats[k] = int(vf.float_value)
        item["stats"] = new_stats

    def _delete_item(self):
        if not self._selected_key or not self._app:
            return
        items = self._items_dict()
        if len(items) <= 1:
            return
        del items[self._selected_key]
        self._selected_key = None
        self._stat_rows.clear()
        self._item_list.set_items(sorted(items.keys()))

    def _new_item(self):
        if not self._app:
            return
        items = self._items_dict()
        key = "new_item"
        i = 1
        while key in items:
            key = f"new_item_{i}"
            i += 1
        items[key] = {"name": "新物品", "slot": "weapon", "rarity": "common",
                       "stats": {}}
        self._item_list.set_items(sorted(items.keys()))
        self._selected_key = key
        self._load_item_form()

    # ── Weights tab ──────────────────────────────────────────────────

    def _build_weights(self):
        self._weight_fields.clear()
        weights = self._app.data["equipment"].get("rarity_weights", {})
        x = 140
        for i, key in enumerate(["common", "rare", "epic"]):
            y = 80 + i * 40
            f = IntField(x + 80, y, 50, 17, font_size=12,
                          default_value=weights.get(key, 60),
                          on_commit=lambda v, k=key: self._save_weight(k, v))
            self._weight_fields[key] = f

    def _save_weight(self, key: str, _val):
        if not self._app:
            return
        w = self._weight_fields.get(key)
        if w:
            self._app.data["equipment"]["rarity_weights"][key] = w.int_value

    # ── Colors tab ───────────────────────────────────────────────────

    def _build_colors(self):
        self._color_widgets.clear()
        colors = self._app.data["equipment"].get("rarity_colors", {})
        for i, key in enumerate(["common", "rare", "epic"]):
            y = 70 + i * 55
            cw = ColorSwatchField(220, y, default_rgb=colors.get(key, [160, 160, 160]),
                                   on_commit=lambda rgb, k=key: self._save_color(k, rgb))
            self._color_widgets[key] = cw

    def _save_color(self, key: str, _rgb):
        cw = self._color_widgets.get(key)
        if cw:
            self._app.data["equipment"]["rarity_colors"][key] = cw.get_rgb()

    # ── Event handling ───────────────────────────────────────────────

    def handle_events(self, events: list[pygame.event.Event], app):
        self._app = app
        if not self._populated:
            self._populate()

        for e in events:
            self._back_btn.handle_event(e)
            for b in self._tab_btns:
                b.handle_event(e)

            if self._tab == "items":
                self._item_list.handle_event(e)
                self._name_field.handle_event(e, app)
                self._slot_drop.handle_event(e, app)
                self._rarity_drop.handle_event(e, app)
                self._icon_drop.handle_event(e, app)
                self._pattern_drop.handle_event(e, app)
                for kf, vf, xb in self._stat_rows:
                    kf.handle_event(e, app)
                    vf.handle_event(e, app)
                    xb.handle_event(e)
                self._btn_add_stat.handle_event(e)
                self._btn_del_item.handle_event(e)
                self._btn_new_item.handle_event(e)

            elif self._tab == "weights":
                if not self._weight_fields:
                    self._build_weights()
                for f in self._weight_fields.values():
                    f.handle_event(e, app)

            elif self._tab == "colors":
                if not self._color_widgets:
                    self._build_colors()
                for cw in self._color_widgets.values():
                    cw.handle_event(e, app)

    def update(self, dt: float, _app):
        self._app = _app
        if self._tab == "items":
            self._name_field.update(dt)
            for kf, vf, _ in self._stat_rows:
                kf.update(dt)
                vf.update(dt)
        elif self._tab == "weights":
            for f in self._weight_fields.values():
                f.update(dt)
        elif self._tab == "colors":
            for cw in self._color_widgets.values():
                cw.update(dt)

    def render(self, surface: pygame.Surface, app):
        self._help_text = ""

        Label(240, 8, "装备", font_size=17, color=TEXT_PRIMARY,
              center=True).render(surface)
        self._back_btn.render(surface)

        for b in self._tab_btns:
            b.render(surface)

        if self._tab == "items":
            self._render_items_tab(surface, app)
        elif self._tab == "weights":
            self._render_weights_tab(surface, app)
        elif self._tab == "colors":
            self._render_colors_tab(surface, app)

        draw_help_bar(surface, self._help_text)

    def _render_items_tab(self, surface: pygame.Surface, app):
        mx = pygame.mouse.get_pos()[0] // WINDOW_SCALE
        my = pygame.mouse.get_pos()[1] // WINDOW_SCALE

        Label(8, 50, "物品", font_size=10, color=TEXT_SECONDARY).render(surface)
        self._item_list.render(surface)

        if not self._selected_key:
            Label(220, 120, "选择一个物品", font_size=13,
                  color=TEXT_SECONDARY).render(surface)
            self._btn_new_item.render(surface)
            return

        Label(200, 34, self._selected_key, font_size=13, color=TEXT_PRIMARY).render(surface)

        if pygame.Rect(self._eq_label_x, 65, 50, 12).collidepoint(mx, my):
            self._help_text = _desc("name")
        Label(self._eq_label_x, 65, _fn("name"), font_size=10, color=TEXT_SECONDARY).render(surface)
        self._name_field.render(surface, app)

        # Stats (before slot/rarity dropdowns)
        if pygame.Rect(self._eq_label_x, 80, 50, 12).collidepoint(mx, my):
            self._help_text = _desc("stats")
        Label(self._eq_label_x, 80, _fn("stats"), font_size=10, color=TEXT_SECONDARY).render(surface)
        for kf, vf, xb in self._stat_rows:
            kf.render(surface, app)
            vf.render(surface, app)
            xb.render(surface)

        # Icon / Pattern — first row below stats
        ic_y = self._icon_drop.rect.y
        if pygame.Rect(self._eq_label_x, ic_y + 2, 50, 12).collidepoint(mx, my):
            self._help_text = _desc("icon_sprite")
        Label(self._eq_label_x, ic_y + 2, "图标", font_size=10, color=TEXT_SECONDARY).render(surface)
        self._icon_drop.render(surface, app)
        if pygame.Rect(self._eq_label_x + 90, ic_y + 2, 50, 12).collidepoint(mx, my):
            self._help_text = _desc("pattern")
        Label(self._eq_label_x + 90, ic_y + 2, "模式", font_size=10, color=TEXT_SECONDARY).render(surface)
        self._pattern_drop.render(surface, app)

        # Slot / Rarity — placed after icon/pattern
        sd_y = self._slot_drop.rect.y
        if pygame.Rect(self._eq_label_x, sd_y + 2, 50, 12).collidepoint(mx, my):
            self._help_text = _desc("slot")
        Label(self._eq_label_x, sd_y + 2, _fn("slot"), font_size=10, color=TEXT_SECONDARY).render(surface)
        self._slot_drop.render(surface, app)
        if pygame.Rect(self._eq_label_x + 90, sd_y + 2, 50, 12).collidepoint(mx, my):
            self._help_text = _desc("rarity")
        Label(self._eq_label_x + 90, sd_y + 2, _fn("rarity"), font_size=10, color=TEXT_SECONDARY).render(surface)
        self._rarity_drop.render(surface, app)

        self._btn_add_stat.render(surface)
        self._btn_del_item.render(surface)
        self._btn_new_item.render(surface)

    def _render_weights_tab(self, surface: pygame.Surface, app):
        mx = pygame.mouse.get_pos()[0] // WINDOW_SCALE
        my = pygame.mouse.get_pos()[1] // WINDOW_SCALE
        Label(240, 55, "稀有度权重 — 控制各稀有度装备的掉落概率", font_size=14, color=TEXT_PRIMARY,
              center=True).render(surface)
        for key, f in self._weight_fields.items():
            if pygame.Rect(f.rect.x - 55, f.rect.y + 1, 50, 15).collidepoint(mx, my):
                self._help_text = _desc(key)
            Label(f.rect.x - 55, f.rect.y + 1, _fn(key), font_size=12,
                  color=TEXT_SECONDARY).render(surface)
            f.render(surface, app)

    def _render_colors_tab(self, surface: pygame.Surface, app):
        mx = pygame.mouse.get_pos()[0] // WINDOW_SCALE
        my = pygame.mouse.get_pos()[1] // WINDOW_SCALE
        Label(240, 55, "稀有度颜色 — 控制装备名称和边框的显示颜色", font_size=14, color=TEXT_PRIMARY,
              center=True).render(surface)
        for key, cw in self._color_widgets.items():
            if pygame.Rect(cw._r.rect.x - 55, cw._r.rect.y + 1, 50, 15).collidepoint(mx, my):
                self._help_text = _desc(key)
            Label(cw._r.rect.x - 55, cw._r.rect.y + 1, _fn(key), font_size=12,
                  color=TEXT_SECONDARY).render(surface)
            cw.render(surface, app)
