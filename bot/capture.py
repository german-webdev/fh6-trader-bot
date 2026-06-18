from __future__ import annotations

from pathlib import Path

from PIL import ImageGrab

from bot.window import WindowInfo


def capture_window(window: WindowInfo):
    return ImageGrab.grab(bbox=window.bbox, all_screens=True)


def save_window_capture(window: WindowInfo, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image = capture_window(window)
    image.save(path)
    return path


def save_image(image, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return path
