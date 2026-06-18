from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import json

from bot.config import AppConfig
from bot.capture import save_window_capture
from bot.window import find_window


class BotRuntime:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def run(self) -> dict[str, Any]:
        return {
            "status": "scaffold",
            "message": "Runtime loop is not implemented yet.",
            "window_title_contains": self.config.window.title_contains,
        }

    def detect(self) -> dict[str, Any]:
        return {
            "status": "scaffold",
            "screen": "unknown",
            "message": "Screen detector is not implemented yet.",
        }

    def check_window(self) -> dict[str, Any]:
        window = find_window(self.config.window.title_contains)
        if window is None:
            return {
                "status": "not_found",
                "window_title_contains": self.config.window.title_contains,
                "message": "Game window was not found.",
            }

        resolution_matches = (
            window.width == self.config.window.required_width
            and window.height == self.config.window.required_height
        )
        return {
            "status": "ok" if resolution_matches else "mismatch",
            "window_found": True,
            "title": window.title,
            "hwnd": window.hwnd,
            "bbox": {
                "left": window.left,
                "top": window.top,
                "right": window.right,
                "bottom": window.bottom,
            },
            "actual_resolution": {
                "width": window.width,
                "height": window.height,
            },
            "window_title_contains": self.config.window.title_contains,
            "required_resolution": {
                "width": self.config.window.required_width,
                "height": self.config.window.required_height,
            },
            "message": (
                "Game window found and resolution matches."
                if resolution_matches
                else "Game window found, but resolution does not match config."
            ),
        }

    def save_debug_shot(self) -> Path:
        output_dir = Path(self.config.debug.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        window = find_window(self.config.window.title_contains)
        if window is None:
            output_path = output_dir / "debug-shot-placeholder.json"
            payload = {
                "status": "not_found",
                "message": "Game window was not found.",
                "config": asdict(self.config),
            }
            output_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return output_path

        return save_window_capture(window, output_dir / "debug-shot.png")
