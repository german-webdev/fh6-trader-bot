from __future__ import annotations

import ctypes


VK_F6 = 0x75
VK_F7 = 0x76
VK_F8 = 0x77


def _pressed(vk_code: int) -> bool:
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x0001)


class HotkeyState:
    def poll(self) -> str | None:
        if _pressed(VK_F8):
            return "stop"
        if _pressed(VK_F7):
            return "pause"
        if _pressed(VK_F6):
            return "start"
        return None
