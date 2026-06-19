"""Keyboard input with randomized timing."""
from __future__ import annotations
import logging
import random
import time
import win32api
import win32gui
import win32con
from pynput.keyboard import Key, Controller

log = logging.getLogger("fh6.actions")

_DEFAULT_KEYBOARD = Controller()


def get_hwnd(window_title="Forza Horizon 6"):
    """Get the window handle for the Forza Horizon 6 game window."""
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        log.warning("Forza Horizon 6 window not found")
    return hwnd


KEY_MAP = {
    "enter": Key.enter,
    "esc": Key.esc,
    "up": Key.up,
    "down": Key.down,
    "y": "y",
}

VK_CODES = {
    "enter": 0x0D,
    "esc": 0x1B,
    "up": 0x26,
    "down": 0x28,
    "y": 0x59,
}

_EXTENDED_KEYS = {"up", "down"}


def _rand_seconds(ms_range) -> float:
    return random.uniform(ms_range[0], ms_range[1]) / 1000.0


def press_key(name, key_hold_ms, between_keys_ms,
              use_win32=False, keyboard=_DEFAULT_KEYBOARD,
              sleep=time.sleep, window_title="Forza Horizon 6") -> None:
    if use_win32:
        press_key_vk(name, key_hold_ms, between_keys_ms, sleep, window_title)
    else:
        press_key_fg(name, key_hold_ms, between_keys_ms, keyboard, sleep)


def press_key_fg(name, key_hold_ms, between_keys_ms,
                 keyboard=_DEFAULT_KEYBOARD, sleep=time.sleep) -> None:
    """Press one key with a randomized hold and post-press gap."""
    key = KEY_MAP[name]
    keyboard.press(key)
    sleep(_rand_seconds(key_hold_ms))
    keyboard.release(key)
    sleep(_rand_seconds(between_keys_ms))


def press_key_vk(name, key_hold_ms, between_keys_ms,
                 sleep=time.sleep, window_title="Forza Horizon 6") -> None:
    """Press one key with a randomized hold and post-press gap using win32 API."""
    hwnd = get_hwnd(window_title)
    if not hwnd:
        return
    vk_code = VK_CODES[name]
    scan_code = win32api.MapVirtualKey(vk_code, 0)
    lparam_down = 1 | (scan_code << 16)
    lparam_up = lparam_down | (1 << 30) | (1 << 31)
    if name in _EXTENDED_KEYS:
        lparam_down |= 1 << 24
        lparam_up |= 1 << 24
    try:
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, lparam_down)
    except Exception as exc:
        log.warning("failed to post keydown to %r: %s", window_title, exc)
        return
    sleep(_rand_seconds(key_hold_ms))
    try:
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, lparam_up)
    except Exception as exc:
        log.warning("failed to post keyup to %r: %s", window_title, exc)
    sleep(_rand_seconds(between_keys_ms))


def tap_key(name, times, key_hold_ms, between_keys_ms,
            use_win32=False, keyboard=_DEFAULT_KEYBOARD,
            sleep=time.sleep, window_title="Forza Horizon 6") -> None:
    """Press a key `times` times."""
    for _ in range(times):
        press_key(name, key_hold_ms, between_keys_ms,
                  use_win32, keyboard, sleep, window_title)
