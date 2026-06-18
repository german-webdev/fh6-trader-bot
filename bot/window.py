from __future__ import annotations

from dataclasses import dataclass
import ctypes
from ctypes import wintypes


user32 = ctypes.windll.user32


@dataclass(slots=True)
class WindowInfo:
    hwnd: int
    title: str
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)


def _get_window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value.strip()


def _get_window_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    return (rect.left, rect.top, rect.right, rect.bottom)


def _enum_visible_windows() -> list[WindowInfo]:
    windows: list[WindowInfo] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True

        title = _get_window_text(hwnd)
        if not title:
            return True

        rect = _get_window_rect(hwnd)
        if rect is None:
            return True

        left, top, right, bottom = rect
        if right <= left or bottom <= top:
            return True

        windows.append(
            WindowInfo(
                hwnd=hwnd,
                title=title,
                left=left,
                top=top,
                right=right,
                bottom=bottom,
            )
        )
        return True

    user32.EnumWindows(callback, 0)
    return windows


def find_window(title_contains: str) -> WindowInfo | None:
    needle = title_contains.casefold()
    matches = [
        window
        for window in _enum_visible_windows()
        if needle in window.title.casefold()
    ]
    if not matches:
        return None

    matches.sort(key=lambda item: (item.width * item.height), reverse=True)
    return matches[0]


def get_foreground_window() -> int | None:
    hwnd = user32.GetForegroundWindow()
    if hwnd == 0:
        return None
    return hwnd


def is_foreground_window(hwnd: int) -> bool:
    foreground = get_foreground_window()
    if foreground is None:
        return False
    return foreground == hwnd
