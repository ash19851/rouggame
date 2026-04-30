"""GUI widgets for the config editor."""

import pygame
from src.ui.text_renderer import draw_text, get_font

WINDOW_SCALE = 3

# ── Colors ──────────────────────────────────────────────────────────────

BG = (15, 15, 25)
PANEL_BG = (22, 22, 38)
WIDGET_BG = (35, 35, 55)
WIDGET_FOCUS = (50, 50, 80)
BORDER_IDLE = (60, 60, 100)
BORDER_FOCUS = (120, 120, 220)
BORDER_HOVER = (90, 90, 150)
TEXT_PRIMARY = (220, 220, 240)
TEXT_SECONDARY = (140, 140, 170)
BTN_BG = (50, 50, 100)
BTN_HOVER = (70, 70, 140)
DANGER_BG = (120, 40, 40)
DANGER_HOVER = (180, 50, 50)
SAVE_BG = (40, 100, 40)
SAVE_HOVER = (50, 140, 50)
SELECTED = (60, 60, 120)


def draw_toast(surface: pygame.Surface, text: str, timer: float):
    """Draw a centered fading toast message."""
    alpha = min(1.0, timer / 0.3) * 200
    if alpha <= 0:
        return
    font = get_font(18)
    surf = font.render(text, True, (220, 255, 220))
    surf.set_alpha(int(alpha))
    r = surf.get_rect(center=(240, 250))
    surface.blit(surf, r)


# ── Label ───────────────────────────────────────────────────────────────

class Label:
    def __init__(self, x, y, text, font_size=13, color=TEXT_PRIMARY, center=False):
        self.x = x
        self.y = y
        self.text = text
        self.font_size = font_size
        self.color = color
        self.center = center

    def set_text(self, text):
        self.text = text

    def render(self, surface: pygame.Surface, _app=None):
        draw_text(surface, self.text, self.x, self.y,
                  size=self.font_size, color=self.color, center=self.center)


# ── Button ──────────────────────────────────────────────────────────────

class Button:
    def __init__(self, x, y, width, height, text, font_size=13,
                 color=BTN_BG, hover_color=BTN_HOVER, text_color=TEXT_PRIMARY,
                 on_click=None, danger=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font_size = font_size
        self.color = DANGER_BG if danger else color
        self.hover_color = DANGER_HOVER if danger else hover_color
        self.text_color = text_color
        self.on_click = on_click
        self._hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return True if clicked."""
        if event.type == pygame.MOUSEMOTION:
            mx = event.pos[0] // WINDOW_SCALE
            my = event.pos[1] // WINDOW_SCALE
            self._hovered = self.rect.collidepoint(mx, my)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx = event.pos[0] // WINDOW_SCALE
            my = event.pos[1] // WINDOW_SCALE
            if self.rect.collidepoint(mx, my):
                if self.on_click:
                    self.on_click()
                return True
        return False

    def render(self, surface: pygame.Surface, _app=None):
        c = self.hover_color if self._hovered else self.color
        pygame.draw.rect(surface, c, self.rect, border_radius=5)
        pygame.draw.rect(surface, BORDER_IDLE, self.rect, 1, border_radius=5)
        draw_text(surface, self.text, self.rect.centerx, self.rect.centery + 1,
                  size=self.font_size, color=self.text_color, center=True)


# ── TextField ───────────────────────────────────────────────────────────

class TextField:
    def __init__(self, x, y, width, height, font_size=13, default_value="",
                 validator=None, on_commit=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.font_size = font_size
        self.value = str(default_value)
        self._edit_text = str(default_value)
        self._cursor = len(self._edit_text)
        self._focused = False
        self._blink = 0.0
        self.validator = validator  # callable(str) -> bool
        self.on_commit = on_commit  # callable(str) after commit

    @property
    def focused(self):
        return self._focused

    def set_value(self, val):
        s = str(val)
        self.value = s
        self._edit_text = s
        self._cursor = len(s)

    def commit(self):
        if self._edit_text != self.value:
            self.value = self._edit_text
            if self.on_commit:
                self.on_commit(self.value)

    def cancel(self):
        self._edit_text = self.value
        self._cursor = len(self._edit_text)

    def handle_event(self, event: pygame.event.Event, app) -> bool:
        """Return True if event was consumed (click inside)."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx = event.pos[0] // WINDOW_SCALE
            my = event.pos[1] // WINDOW_SCALE
            if self.rect.collidepoint(mx, my):
                app.request_focus(self)
                # Place cursor at approximate click position
                self._cursor = self._char_at_x(mx - self.rect.x - 6)
                return True
            elif self._focused:
                app.clear_focus()
                return False

        elif event.type == pygame.KEYDOWN and self._focused:
            return self._handle_key(event, app)

        return False

    def _handle_key(self, event: pygame.event.Event, app) -> bool:
        if event.key == pygame.K_LEFT:
            self._cursor = max(0, self._cursor - 1)
            return True
        elif event.key == pygame.K_RIGHT:
            self._cursor = min(len(self._edit_text), self._cursor + 1)
            return True
        elif event.key == pygame.K_HOME:
            self._cursor = 0
            return True
        elif event.key == pygame.K_END:
            self._cursor = len(self._edit_text)
            return True
        elif event.key == pygame.K_BACKSPACE:
            if self._cursor > 0:
                self._edit_text = (self._edit_text[:self._cursor - 1]
                                   + self._edit_text[self._cursor:])
                self._cursor -= 1
            return True
        elif event.key == pygame.K_DELETE:
            if self._cursor < len(self._edit_text):
                self._edit_text = (self._edit_text[:self._cursor]
                                   + self._edit_text[self._cursor + 1:])
            return True
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.commit()
            app.clear_focus()
            return True
        elif event.key == pygame.K_TAB:
            self.commit()
            app.clear_focus()
            return True
        elif event.key == pygame.K_ESCAPE:
            self.cancel()
            app.clear_focus()
            return True
        elif event.unicode and event.unicode.isprintable():
            ch = event.unicode
            if self.validator is None or self.validator(self._edit_text + ch):
                self._edit_text = (self._edit_text[:self._cursor] + ch
                                   + self._edit_text[self._cursor:])
                self._cursor += 1
            return True
        return False

    def _char_at_x(self, px: int) -> int:
        """Approximate char index from pixel x offset."""
        if px <= 0:
            return 0
        font = get_font(self.font_size)
        best = 0
        best_dist = 9999
        for i in range(len(self._edit_text) + 1):
            w = font.size(self._edit_text[:i])[0]
            dist = abs(px - w)
            if dist < best_dist:
                best_dist = dist
                best = i
        return best

    def update(self, dt: float):
        if self._focused:
            self._blink += dt

    def render(self, surface: pygame.Surface, _app=None):
        bg = WIDGET_FOCUS if self._focused else WIDGET_BG
        border = BORDER_FOCUS if self._focused else BORDER_IDLE
        pygame.draw.rect(surface, bg, self.rect, border_radius=4)
        pygame.draw.rect(surface, border, self.rect, 1, border_radius=4)

        # Vertically centered text, left-aligned
        text = self._edit_text
        font = get_font(self.font_size)
        text_surf = font.render(text, True, TEXT_PRIMARY)
        text_y = self.rect.y + (self.rect.height - text_surf.get_height()) // 2 + 1
        clip = pygame.Rect(self.rect.x + 2, self.rect.y + 2,
                           self.rect.width - 4, self.rect.height - 4)
        surface.set_clip(clip)
        surface.blit(text_surf, (self.rect.x + 6, text_y))
        surface.set_clip(None)

        # Blinking cursor
        if self._focused and (self._blink % 1.0) < 0.5:
            cursor_x = self.rect.x + 6 + font.size(self._edit_text[:self._cursor])[0]
            pygame.draw.line(surface, (255, 255, 255),
                             (cursor_x, self.rect.y + 3),
                             (cursor_x, self.rect.bottom - 3), 1)


# ── IntField ────────────────────────────────────────────────────────────

class IntField(TextField):
    def __init__(self, x, y, width, height, font_size=13, default_value=0,
                 on_commit=None):
        super().__init__(x, y, width, height, font_size,
                         default_value=str(default_value),
                         validator=self._validate_int,
                         on_commit=on_commit)
        self.int_value = default_value

    @staticmethod
    def _validate_int(text: str) -> bool:
        if not text:
            return True
        if text == "-":
            return True
        return text.lstrip("-").isdigit()

    def set_value(self, val):
        self.int_value = int(val)
        super().set_value(val)

    def commit(self):
        if self._edit_text != self.value:
            self.value = self._edit_text
            # Parse
            t = self._edit_text.strip()
            if t in ("", "-"):
                self.int_value = 0
            else:
                try:
                    self.int_value = int(t)
                except ValueError:
                    self.int_value = 0
            if self.on_commit:
                self.on_commit(self.value)


# ── FloatField ──────────────────────────────────────────────────────────

class FloatField(TextField):
    def __init__(self, x, y, width, height, font_size=13, default_value=0.0,
                 on_commit=None):
        super().__init__(x, y, width, height, font_size,
                         default_value=str(default_value),
                         validator=self._validate_float,
                         on_commit=on_commit)
        self.float_value = default_value

    @staticmethod
    def _validate_float(text: str) -> bool:
        if not text:
            return True
        if text == "-":
            return True
        try:
            float(text)
            return True
        except ValueError:
            return False

    def set_value(self, val):
        self.float_value = float(val)
        super().set_value(val)

    def commit(self):
        if self._edit_text != self.value:
            self.value = self._edit_text
            t = self._edit_text.strip()
            if t in ("", "-", "."):
                self.float_value = 0.0
            else:
                try:
                    self.float_value = float(t)
                except ValueError:
                    self.float_value = 0.0
            if self.on_commit:
                self.on_commit(self.value)


# ── ColorSwatchField ────────────────────────────────────────────────────

class ColorSwatchField:
    def __init__(self, x, y, default_rgb=(255, 255, 255), on_commit=None):
        self._r = IntField(x, y, 34, 17, font_size=11, default_value=default_rgb[0])
        self._g = IntField(x + 40, y, 34, 17, font_size=11, default_value=default_rgb[1])
        self._b = IntField(x + 80, y, 34, 17, font_size=11, default_value=default_rgb[2])
        self._swatch = pygame.Rect(x + 120, y + 1, 15, 15)
        self.on_commit = on_commit

    @property
    def widgets(self):
        return [self._r, self._g, self._b]

    def get_rgb(self):
        return [self._r.int_value, self._g.int_value, self._b.int_value]

    def set_rgb(self, rgb):
        self._r.set_value(rgb[0])
        self._g.set_value(rgb[1])
        self._b.set_value(rgb[2])

    def handle_event(self, event: pygame.event.Event, app) -> bool:
        for w in self.widgets:
            if w.handle_event(event, app):
                if self.on_commit:
                    self.on_commit(self.get_rgb())
                return True
        return False

    def update(self, dt: float):
        for w in self.widgets:
            w.update(dt)

    def render(self, surface: pygame.Surface, app=None):
        for w in self.widgets:
            w.render(surface, app)
        rgb = self.get_rgb()
        clamped = tuple(max(0, min(255, c)) for c in rgb)
        pygame.draw.rect(surface, clamped, self._swatch, border_radius=3)
        pygame.draw.rect(surface, BORDER_IDLE, self._swatch, 1, border_radius=3)


# ── List2Field (for [w, h]) ─────────────────────────────────────────────

class List2Field:
    def __init__(self, x, y, default_vals=(20, 28), on_commit=None):
        self._a = IntField(x, y, 34, 17, font_size=11, default_value=default_vals[0])
        self._b = IntField(x + 40, y, 34, 17, font_size=11, default_value=default_vals[1])
        self.on_commit = on_commit

    @property
    def widgets(self):
        return [self._a, self._b]

    def get_vals(self):
        return [self._a.int_value, self._b.int_value]

    def set_vals(self, vals):
        self._a.set_value(vals[0])
        self._b.set_value(vals[1])

    def handle_event(self, event: pygame.event.Event, app) -> bool:
        for w in self.widgets:
            if w.handle_event(event, app):
                if self.on_commit:
                    self.on_commit(self.get_vals())
                return True
        return False

    def update(self, dt: float):
        for w in self.widgets:
            w.update(dt)

    def render(self, surface: pygame.Surface, app=None):
        for w in self.widgets:
            w.render(surface, app)


# ── DropdownField ───────────────────────────────────────────────────────

class DropdownField:
    _expanded_instance: 'DropdownField | None' = None

    def __init__(self, x, y, width, height, options: list[str],
                 default_index=0, font_size=12, on_change=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = default_index
        self.font_size = font_size
        self.on_change = on_change
        self.expanded = False
        self._hovered = False
        self._option_rects = []

    def get_value(self):
        if not self.options:
            return ""
        if self.selected_index >= len(self.options):
            self.selected_index = 0
        return self.options[self.selected_index]

    def set_value(self, val):
        try:
            self.selected_index = self.options.index(val)
        except ValueError:
            self.selected_index = 0

    def update(self, dt: float):
        pass

    def handle_event(self, event: pygame.event.Event, _app=None) -> bool:
        mx = event.pos[0] // WINDOW_SCALE if hasattr(event, 'pos') else 0
        my = event.pos[1] // WINDOW_SCALE if hasattr(event, 'pos') else 0

        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(mx, my)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.expanded:
                for i, r in enumerate(self._option_rects):
                    if r.collidepoint(mx, my):
                        self.selected_index = i
                        self.expanded = False
                        DropdownField._expanded_instance = None
                        if self.on_change:
                            self.on_change(self.get_value())
                        return True
                self.expanded = False
                DropdownField._expanded_instance = None
                return True
            elif self.rect.collidepoint(mx, my):
                if DropdownField._expanded_instance and DropdownField._expanded_instance is not self:
                    DropdownField._expanded_instance.expanded = False
                self.expanded = True
                DropdownField._expanded_instance = self
                return True
            else:
                self.expanded = False
                if DropdownField._expanded_instance is self:
                    DropdownField._expanded_instance = None

        return False

    def render(self, surface: pygame.Surface, _app=None):
        bg = BTN_HOVER if self._hovered or self.expanded else WIDGET_BG
        pygame.draw.rect(surface, bg, self.rect, border_radius=4)
        pygame.draw.rect(surface, BORDER_IDLE, self.rect, 1, border_radius=4)

        val = self.options[self.selected_index]
        font = get_font(self.font_size)
        val_surf = font.render(val, True, TEXT_PRIMARY)
        val_y = self.rect.y + (self.rect.height - val_surf.get_height()) // 2 + 1
        surface.blit(val_surf, (self.rect.x + 8, val_y))

        # Arrow
        arrow = "v" if not self.expanded else "^"
        arrow_surf = get_font(11).render(arrow, True, TEXT_SECONDARY)
        arrow_y = self.rect.y + (self.rect.height - arrow_surf.get_height()) // 2 + 1
        surface.blit(arrow_surf, (self.rect.right - 14, arrow_y))

        if self.expanded:
            self._option_rects.clear()
            for i, opt in enumerate(self.options):
                oy = self.rect.bottom + 2 + i * 20
                or_rect = pygame.Rect(self.rect.x, oy, self.rect.width, 19)
                self._option_rects.append(or_rect)
                obg = SELECTED if i == self.selected_index else WIDGET_FOCUS
                pygame.draw.rect(surface, obg, or_rect, border_radius=3)
                opt_surf = get_font(self.font_size).render(opt, True, TEXT_PRIMARY)
                opt_y = or_rect.y + (or_rect.height - opt_surf.get_height()) // 2 + 1
                surface.blit(opt_surf, (or_rect.x + 8, opt_y))


# ── ScrollList ──────────────────────────────────────────────────────────

class ScrollList:
    def __init__(self, x, y, width, height, items: list[str],
                 row_height=20, font_size=12, on_select=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.items = items
        self.row_height = row_height
        self.font_size = font_size
        self.on_select = on_select
        self.scroll_offset = 0
        self.selected_index = -1
        self._hovered_row = -1
        self.visible_count = max(1, height // row_height)

    def set_items(self, items: list[str]):
        self.items = items
        self.selected_index = -1
        self.scroll_offset = 0

    def get_selected_key(self) -> str | None:
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def select_index(self, idx: int):
        self.selected_index = idx
        # Ensure visible
        if idx >= 0:
            if idx < self.scroll_offset:
                self.scroll_offset = idx
            elif idx >= self.scroll_offset + self.visible_count:
                self.scroll_offset = idx - self.visible_count + 1

    def handle_event(self, event: pygame.event.Event, _app=None) -> bool:
        mx = event.pos[0] // WINDOW_SCALE if hasattr(event, 'pos') else 0
        my = event.pos[1] // WINDOW_SCALE if hasattr(event, 'pos') else 0

        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(mx, my):
                rel_y = my - self.rect.y
                idx = self.scroll_offset + rel_y // self.row_height
                if 0 <= idx < len(self.items):
                    self._hovered_row = idx
                else:
                    self._hovered_row = -1
            else:
                self._hovered_row = -1

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mx, my):
                rel_y = my - self.rect.y
                idx = self.scroll_offset + rel_y // self.row_height
                if 0 <= idx < len(self.items):
                    self.selected_index = idx
                    if self.on_select:
                        self.on_select(self.items[idx])
                    return True

        elif event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(
                    pygame.mouse.get_pos()[0] // WINDOW_SCALE,
                    pygame.mouse.get_pos()[1] // WINDOW_SCALE):
                self.scroll_offset -= event.y
                max_scroll = max(0, len(self.items) - self.visible_count)
                self.scroll_offset = max(0, min(max_scroll, self.scroll_offset))

        return False

    def update(self, _dt: float):
        pass

    def render(self, surface: pygame.Surface, _app=None):
        pygame.draw.rect(surface, PANEL_BG, self.rect)
        pygame.draw.rect(surface, BORDER_IDLE, self.rect, 1, border_radius=3)

        clip = self.rect.copy()
        surface.set_clip(clip)

        for i in range(self.scroll_offset,
                       min(self.scroll_offset + self.visible_count, len(self.items))):
            item = self.items[i]
            row_y = self.rect.y + (i - self.scroll_offset) * self.row_height
            row_rect = pygame.Rect(self.rect.x, row_y, self.rect.width, self.row_height)

            if i == self.selected_index:
                pygame.draw.rect(surface, SELECTED, row_rect)
            elif i == self._hovered_row:
                pygame.draw.rect(surface, (45, 45, 75), row_rect)

            item_surf = get_font(self.font_size).render(item, True, TEXT_PRIMARY)
            item_y = row_y + (self.row_height - item_surf.get_height()) // 2 + 1
            surface.blit(item_surf, (self.rect.x + 8, item_y))

        surface.set_clip(None)

        # Scrollbar
        total = len(self.items)
        if total > self.visible_count:
            sb_h = max(16, int(self.rect.height * self.visible_count / total))
            sb_y = self.rect.y + int(
                self.scroll_offset / max(1, total - self.visible_count)
                * (self.rect.height - sb_h))
            sb_rect = pygame.Rect(self.rect.right - 6, sb_y, 5, sb_h)
            pygame.draw.rect(surface, BORDER_IDLE, sb_rect, border_radius=2)
