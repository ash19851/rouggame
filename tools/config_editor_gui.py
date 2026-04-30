#!/usr/bin/env python3
"""GUI configuration editor for game balance data.

Usage:
    python tools/config_editor_gui.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.gui_editor.app import App


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
