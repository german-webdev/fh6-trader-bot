from __future__ import annotations

import ctypes
import time

from bot.config import TimingConfig


VK_RETURN = 0x0D
VK_ESCAPE = 0x1B
VK_DOWN = 0x28
KEYEVENTF_KEYUP = 0x0002


def _press_vk(vk_code: int) -> None:
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.03)
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


class InputController:
    def __init__(self, timings: TimingConfig, dry_run: bool = False) -> None:
        self.timings = timings
        self.dry_run = dry_run

    def press_enter(self) -> None:
        self._press(VK_RETURN, self.timings.after_enter_ms)

    def press_escape(self) -> None:
        self._press(VK_ESCAPE, self.timings.after_esc_ms)

    def press_down(self) -> None:
        self._press(VK_DOWN, self.timings.after_down_ms)

    def _press(self, vk_code: int, delay_ms: int) -> None:
        if not self.dry_run:
            _press_vk(vk_code)
        time.sleep(delay_ms / 1000.0)
