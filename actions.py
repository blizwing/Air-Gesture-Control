"""Windows-specific action functions."""
from __future__ import annotations

import time
import ctypes
from typing import Optional

import win32con
import win32gui
import win32api


VK_CODE = {
    "PGUP": 0x21,
    "PGDN": 0x22,
    "ESC": 0x1B,
}


def _press_key(hexKeyCode: int) -> None:
    win32api.keybd_event(hexKeyCode, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(hexKeyCode, 0, win32con.KEYEVENTF_KEYUP, 0)


def _press_combo(*keys: int) -> None:
    for k in keys:
        win32api.keybd_event(k, 0, 0, 0)
    time.sleep(0.05)
    for k in reversed(keys):
        win32api.keybd_event(k, 0, win32con.KEYEVENTF_KEYUP, 0)


def dismiss_notifications() -> None:
    """Dismiss Windows notifications using Win+V then Esc."""
    MOD_WIN = 0x5B
    _press_combo(MOD_WIN, ord('V'))
    _press_key(VK_CODE["ESC"])


def send_page_down() -> None:
    """Send Page Down keypress."""
    _press_key(VK_CODE["PGDN"])


def send_page_up() -> None:
    """Send Page Up keypress."""
    _press_key(VK_CODE["PGUP"])


def _send_win_number(n: int) -> None:
    nvk = ord(str(n))
    MOD_WIN = 0x5B
    _press_combo(MOD_WIN, nvk)


def _minimize_window(hwnd: int) -> None:
    win32gui.ShowWindow(hwnd, win32con.SW_FORCEMINIMIZE)


def toggle_taskbar_slot(slot: int) -> None:
    """Open or minimize the window in the nth taskbar slot."""
    if slot < 1 or slot > 9:
        return
    before = win32gui.GetForegroundWindow()
    _send_win_number(slot)
    time.sleep(0.2)
    after = win32gui.GetForegroundWindow()
    if before == after:
        _minimize_window(after)
    else:
        win32gui.ShowWindow(after, win32con.SW_SHOWMAXIMIZED)


def scroll_wheel(delta: int) -> None:
    """Scroll mouse wheel by delta units."""
    win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, delta, 0)


