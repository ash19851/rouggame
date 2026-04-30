#!/usr/bin/env python3
"""CLI configuration editor for game balance data.

Usage:
    python tools/config_editor.py            # interactive mode
    python tools/config_editor.py --defaults  # regenerate all configs from defaults
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data.config_loader import (
    _CONFIG_DIR, _ENEMIES_DEFAULT, _EQUIPMENT_DEFAULTS,
    _UPGRADES_DEFAULT, _BALANCE_DEFAULT, _save_json,
)


def get_input(prompt: str, current_value) -> str:
    """Prompt for a value, showing current. Empty input keeps current."""
    raw = input(f"  {prompt} [{current_value}]: ").strip()
    return raw if raw else str(current_value)


def validate_number(raw: str, current) -> object:
    """Convert input to the same type as current value."""
    if raw == str(current):
        return current
    try:
        if isinstance(current, bool):
            return raw.lower() in ("true", "1", "yes", "y")
        if isinstance(current, int):
            return int(raw)
        if isinstance(current, float):
            return float(raw)
        return raw
    except (ValueError, TypeError):
        print(f"  Invalid value, keeping {current}")
        return current


def validate_list(raw: str, current: list) -> list:
    """Parse a JSON-like list input."""
    raw = raw.strip()
    if not raw or raw == str(current):
        return current
    try:
        val = json.loads(raw)
        if isinstance(val, list):
            return val
    except json.JSONDecodeError:
        pass
    print(f"  Invalid list format, use JSON like [1, 2, 3]. Keeping {current}")
    return current


def validate_dict(raw: str, current: dict) -> dict:
    """Parse a JSON-like dict input."""
    raw = raw.strip()
    if not raw or raw == str(current):
        return current
    try:
        val = json.loads(raw)
        if isinstance(val, dict):
            return val
    except json.JSONDecodeError:
        pass
    print(f"  Invalid dict format, use JSON like {{'key': 'val'}}. Keeping {current}")
    return current


def edit_dict(data: dict, path: str = "") -> dict:
    """Interactive editor for a dict. Edits in-place. Returns data."""
    items = list(data.items())
    while True:
        print(f"\n  --- {path or 'root'} ---")
        for i, (key, val) in enumerate(items, 1):
            if isinstance(val, dict):
                display = f"{{{len(val)} keys}}"
            elif isinstance(val, list):
                display = f"[{len(val)} items]"
            elif isinstance(val, float):
                display = f"{val:.2f}" if val == int(val) else f"{val}"
            else:
                display = str(val)
            print(f"  {i}. {key} = {display}")
        print(f"  {len(items) + 1}. Back")

        choice = input("  Select > ").strip()
        if choice == str(len(items) + 1) or choice.lower() == "b":
            return data
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                key, val = items[idx]
                if isinstance(val, dict):
                    edit_dict(val, f"{path}.{key}")
                elif isinstance(val, list):
                    edit_list(val, f"{path}.{key}")
                elif isinstance(val, bool):
                    raw = get_input(f"{key} (true/false)", val)
                    data[key] = validate_number(raw, val)
                elif isinstance(val, int):
                    raw = get_input(key, val)
                    data[key] = validate_number(raw, val)
                elif isinstance(val, float):
                    raw = get_input(key, val)
                    data[key] = validate_number(raw, val)
                elif isinstance(val, str):
                    raw = get_input(key, val)
                    data[key] = raw if raw != str(val) else val
        except (ValueError, IndexError):
            print("  Invalid selection")


def edit_list(data: list, path: str = "") -> list:
    """Interactive editor for a list of dicts."""
    while True:
        print(f"\n  --- {path or 'list'} [{len(data)} items] ---")
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                label = item.get("label", item.get("name", item.get("key", f"item {i}")))
                print(f"  {i}. {label}")
            else:
                print(f"  {i}. {item}")
        print(f"  {len(data) + 1}. Back")

        choice = input("  Select > ").strip()
        if choice == str(len(data) + 1) or choice.lower() == "b":
            return data
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(data):
                if isinstance(data[idx], dict):
                    edit_dict(data[idx], f"{path}[{idx}]")
                else:
                    raw = get_input("value", data[idx])
                    val = data[idx]
                    if isinstance(val, bool):
                        data[idx] = validate_number(raw, val)
                    elif isinstance(val, int):
                        data[idx] = validate_number(raw, val)
                    elif isinstance(val, float):
                        data[idx] = validate_number(raw, val)
                    elif isinstance(val, str):
                        data[idx] = raw if raw != str(val) else val
        except (ValueError, IndexError):
            print("  Invalid selection")


def edit_enemies():
    data = _load_json_file("enemies.json", _ENEMIES_DEFAULT)
    edit_dict(data, "enemies")
    _save_json("enemies.json", data)
    print("  [Saved enemies.json]")


def edit_equipment():
    data = _load_json_file("equipment_defs.json", _EQUIPMENT_DEFAULTS)
    while True:
        print("\n  --- Equipment ---")
        print("  1. Edit Items")
        print("  2. Edit Rarity Weights")
        print("  3. Edit Rarity Colors")
        print("  4. Back")
        choice = input("  Select > ").strip()
        if choice == "1":
            edit_dict(data.setdefault("items", _EQUIPMENT_DEFAULTS["items"]), "items")
        elif choice == "2":
            edit_dict(data.setdefault("rarity_weights", _EQUIPMENT_DEFAULTS["rarity_weights"]), "rarity_weights")
        elif choice == "3":
            edit_dict(data.setdefault("rarity_colors", _EQUIPMENT_DEFAULTS["rarity_colors"]), "rarity_colors")
        elif choice == "4" or choice.lower() == "b":
            break
    _save_json("equipment_defs.json", data)
    print("  [Saved equipment_defs.json]")


def edit_upgrades():
    data = _load_json_file("upgrades.json", _UPGRADES_DEFAULT)
    while True:
        print("\n  --- Upgrades ---")
        print("  1. Edit Choices")
        print(f"  2. Cards Shown = {data.get('cards_shown', 3)}")
        print(f"  3. XP Curve Mult = {data.get('xp_curve_mult', 1.35)}")
        print("  4. Back")
        choice = input("  Select > ").strip()
        if choice == "1":
            edit_list(data.setdefault("choices", _UPGRADES_DEFAULT["choices"]), "choices")
        elif choice == "2":
            raw = get_input("cards_shown", data.get("cards_shown", 3))
            data["cards_shown"] = validate_number(raw, data.get("cards_shown", 3))
        elif choice == "3":
            raw = get_input("xp_curve_mult", data.get("xp_curve_mult", 1.35))
            data["xp_curve_mult"] = validate_number(raw, data.get("xp_curve_mult", 1.35))
        elif choice == "4" or choice.lower() == "b":
            break
    _save_json("upgrades.json", data)
    print("  [Saved upgrades.json]")


def edit_balance():
    data = _load_json_file("balance.json", _BALANCE_DEFAULT)
    while True:
        print("\n  --- Balance ---")
        for i, section in enumerate(data.keys(), 1):
            print(f"  {i}. {section}")
        print(f"  {len(data) + 1}. Back")
        choice = input("  Select > ").strip()
        if choice == str(len(data) + 1) or choice.lower() == "b":
            break
        try:
            idx = int(choice) - 1
            keys = list(data.keys())
            if 0 <= idx < len(keys):
                edit_dict(data[keys[idx]], f"balance.{keys[idx]}")
        except (ValueError, IndexError):
            print("  Invalid selection")
    _save_json("balance.json", data)
    print("  [Saved balance.json]")


def _load_json_file(filename: str, default: dict) -> dict:
    path = os.path.join(_CONFIG_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return dict(default)  # shallow copy


def main():
    if "--defaults" in sys.argv:
        from src.data.config_loader import save_all_defaults
        save_all_defaults()
        return

    while True:
        print("\n===== Config Editor =====")
        print("1. Edit Enemies")
        print("2. Edit Equipment")
        print("3. Edit Upgrades")
        print("4. Edit Balance")
        print("5. Reset All to Defaults")
        print("6. Exit")
        choice = input("> ").strip()

        if choice == "1":
            edit_enemies()
        elif choice == "2":
            edit_equipment()
        elif choice == "3":
            edit_upgrades()
        elif choice == "4":
            edit_balance()
        elif choice == "5":
            confirm = input("  Reset all configs to defaults? (y/n): ").strip().lower()
            if confirm == "y":
                from src.data.config_loader import save_all_defaults
                save_all_defaults()
        elif choice == "6" or choice.lower() in ("q", "quit", "exit"):
            print("Done.")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
