from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import json

from bot.config import AppConfig


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
        return {
            "status": "scaffold",
            "window_title_contains": self.config.window.title_contains,
            "required_resolution": {
                "width": self.config.window.required_width,
                "height": self.config.window.required_height,
            },
            "message": "Window detection is not implemented yet.",
        }

    def save_debug_shot(self) -> Path:
        output_dir = Path(self.config.debug.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "debug-shot-placeholder.json"
        payload = {
            "status": "scaffold",
            "message": "Frame capture is not implemented yet.",
            "config": asdict(self.config),
        }
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return output_path
