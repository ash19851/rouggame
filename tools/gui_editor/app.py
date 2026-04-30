"""GUI Config Editor — App class with main loop, screen stack, focus management."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pygame
from copy import deepcopy
from src.data.config_loader import (
    _CONFIG_DIR, _ENEMIES_DEFAULT, _EQUIPMENT_DEFAULTS,
    _UPGRADES_DEFAULT, _BALANCE_DEFAULT, _save_json, save_all_defaults,
)

VIRTUAL_W = 480
VIRTUAL_H = 300
WINDOW_SCALE = 3


class App:
    VIRTUAL_W = VIRTUAL_W
    VIRTUAL_H = VIRTUAL_H
    WINDOW_SCALE = WINDOW_SCALE

    def __init__(self):
        pygame.init()
        from src.graphics.sprite_atlas import init_sprites
        init_sprites()
        self.screen = pygame.display.set_mode(
            (VIRTUAL_W * WINDOW_SCALE, VIRTUAL_H * WINDOW_SCALE))
        pygame.display.set_caption("配置编辑器")
        self.clock = pygame.time.Clock()
        self.virtual_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        self.running = True

        self.data = self._load_all_configs()
        self._screens = []
        self._focused_field = None
        self._toast_text = ""
        self._toast_timer = 0.0

        from tools.gui_editor.screens import MainMenuScreen
        self.push_screen(MainMenuScreen())

    # ── Data ──────────────────────────────────────────────────────────

    def _load_all_configs(self) -> dict:
        return {
            "enemies": self._load_json_file("enemies.json", deepcopy(_ENEMIES_DEFAULT)),
            "equipment": self._load_json_file("equipment_defs.json", deepcopy(_EQUIPMENT_DEFAULTS)),
            "upgrades": self._load_json_file("upgrades.json", deepcopy(_UPGRADES_DEFAULT)),
            "balance": self._load_json_file("balance.json", deepcopy(_BALANCE_DEFAULT)),
        }

    def _load_json_file(self, filename: str, default: dict) -> dict:
        import json
        path = os.path.join(_CONFIG_DIR, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return default

    def save_all(self):
        _save_json("enemies.json", self.data["enemies"])
        _save_json("equipment_defs.json", self.data["equipment"])
        _save_json("upgrades.json", self.data["upgrades"])
        _save_json("balance.json", self.data["balance"])
        self._toast_text = "已保存！"
        self._toast_timer = 1.0

    def reset_all(self):
        save_all_defaults()
        self.data = self._load_all_configs()
        self._screens = self._screens[:1]  # back to main menu
        self._toast_text = "已重置为默认值！"
        self._toast_timer = 1.5

    # ── Screen stack ──────────────────────────────────────────────────

    def push_screen(self, screen):
        self._screens.append(screen)

    def pop_screen(self):
        if len(self._screens) > 1:
            self.clear_focus()
            self._screens.pop()

    # ── Focus management ──────────────────────────────────────────────

    def request_focus(self, field):
        if self._focused_field is not None and self._focused_field is not field:
            self._focused_field.commit()
            self._focused_field._focused = False
        self._focused_field = field
        if field is not None:
            field._focused = True

    def clear_focus(self):
        if self._focused_field is not None:
            self._focused_field.commit()
            self._focused_field._focused = False
        self._focused_field = None

    # ── Main loop ─────────────────────────────────────────────────────

    def run(self):
        while self.running:
            dt = min(self.clock.tick(60) / 1000.0, 0.1)
            events = pygame.event.get()

            for e in events:
                if e.type == pygame.QUIT:
                    self.running = False

            if self._screens:
                self._screens[-1].handle_events(events, self)

                # Update — widgets need this for cursor blink
                self._screens[-1].update(dt, self)

                # Toast timer
                if self._toast_timer > 0:
                    self._toast_timer -= dt

            # Render
            self.virtual_surface.fill((15, 15, 25))
            if self._screens:
                self._screens[-1].render(self.virtual_surface, self)

            # Re-render expanded dropdown on top of everything
            from tools.gui_editor.widgets import DropdownField
            if DropdownField._expanded_instance:
                DropdownField._expanded_instance.render(self.virtual_surface)

            # Toast
            if self._toast_timer > 0:
                from tools.gui_editor.widgets import draw_toast
                draw_toast(self.virtual_surface, self._toast_text, self._toast_timer)

            scaled = pygame.transform.scale(
                self.virtual_surface,
                (VIRTUAL_W * WINDOW_SCALE, VIRTUAL_H * WINDOW_SCALE))
            self.screen.blit(scaled, (0, 0))
            pygame.display.flip()

        pygame.quit()
