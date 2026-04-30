"""
键盘输入检测模块。

提供跨平台的按键检测功能。在 Windows 上使用 Win32 API 的 GetAsyncKeyState
获取实时按键状态（比 pygame 轮询更可靠），其他平台回退到 pygame 内置方法。
"""

import sys
import pygame
import ctypes

# Windows 虚拟键码映射表（pygame 键值 -> Win32 VK 码）
_VK_MAP = {
    pygame.K_w: 0x57,
    pygame.K_a: 0x41,
    pygame.K_s: 0x53,
    pygame.K_d: 0x44,
    pygame.K_UP: 0x26,
    pygame.K_DOWN: 0x28,
    pygame.K_LEFT: 0x25,
    pygame.K_RIGHT: 0x27,
    pygame.K_TAB: 0x09,
    pygame.K_ESCAPE: 0x1B,
    pygame.K_i: 0x49,
}


def is_key_down(key: int) -> bool:
    """检测按键是否处于按下状态。

    在 Windows 平台使用 Win32 API GetAsyncKeyState 获取实时状态
    （不受窗口焦点限制），其他平台使用 pygame 的按键轮询。
    """
    if sys.platform == "win32" and key in _VK_MAP:
        # GetAsyncKeyState 返回值的高位表示键是否按下
        return ctypes.windll.user32.GetAsyncKeyState(_VK_MAP[key]) & 0x8000 != 0
    return pygame.key.get_pressed()[key]
