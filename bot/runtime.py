from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import logging
from pathlib import Path
from typing import Any
import json
import time

from PIL import Image

from bot.config import AppConfig
from bot.capture import capture_window, save_image, save_window_capture
from bot.detector import ScreenDetector
from bot.hotkeys import HotkeyState
from bot.input import InputController
from bot.screens import ScreenName
from bot.state_machine import AuctionStateMachine
from bot.window import find_window


class BotRuntime:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.detector = ScreenDetector(config)
        self.input = InputController(config.timings)
        self.hotkeys = HotkeyState()
        self.logger = self._build_logger()

    def _build_logger(self) -> logging.Logger:
        logger = logging.getLogger("trade_bot")
        logger.setLevel(logging.INFO)
        if logger.handlers:
            return logger

        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        file_handler = logging.FileHandler(logs_dir / "session.log", encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)
        return logger

    def _capture_window_image(self):
        window = find_window(self.config.window.title_contains)
        if window is None:
            return None, None
        return window, capture_window(window)

    def run(self, dry_run: bool = False) -> dict[str, Any]:
        window = find_window(self.config.window.title_contains)
        if window is None:
            return {
                "status": "not_found",
                "message": "Game window was not found.",
            }

        machine = AuctionStateMachine()
        self.input.dry_run = dry_run
        paused = False
        cycles = 0
        unknown_count = 0
        purchase_unknown_count = 0
        start_time = time.monotonic()
        loader_started_at: float | None = None
        self.logger.info("Runtime started")
        time.sleep(self.config.timings.startup_delay_ms / 1000.0)

        while True:
            hotkey = self.hotkeys.poll()
            if hotkey == "stop":
                self.logger.info("Runtime stopped by hotkey")
                return self._run_result(
                    status="stopped",
                    screen=ScreenName.UNKNOWN,
                    cycles=cycles,
                    elapsed_seconds=time.monotonic() - start_time,
                    message="Stopped by F8.",
                )
            if hotkey == "pause":
                paused = not paused
                self.logger.info("Paused toggled: %s", paused)
            if hotkey == "start":
                paused = False
                self.logger.info("Runtime resumed by F6")

            if paused:
                time.sleep(0.1)
                continue

            current_window, image = self._capture_window_image()
            if current_window is None or image is None:
                return self._run_result(
                    status="not_found",
                    screen=ScreenName.UNKNOWN,
                    cycles=cycles,
                    elapsed_seconds=time.monotonic() - start_time,
                    message="Game window disappeared during runtime.",
                )

            detection = self.detector.detect(image)
            screen = detection.screen

            if screen is ScreenName.S1_SEARCH_MENU:
                cycles += 1

            if screen is ScreenName.UNKNOWN:
                unknown_count += 1
                if machine.awaiting_purchase_result:
                    purchase_unknown_count += 1
                if self.config.debug.save_unknown_frames:
                    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                    save_image(
                        image,
                        Path(self.config.debug.output_dir)
                        / f"unknown-{timestamp}.png",
                    )
                if unknown_count >= self.config.detector.unknown_limit:
                    self.logger.error("Too many unknown detections")
                    return self._run_result(
                        status="error",
                        screen=screen,
                        cycles=cycles,
                        elapsed_seconds=time.monotonic() - start_time,
                        message="Too many unknown detections.",
                        score=detection.score,
                    )
            else:
                unknown_count = 0
                purchase_unknown_count = 0

            if screen is ScreenName.S6_LOADER and loader_started_at is None:
                loader_started_at = time.monotonic()
            elif screen is not ScreenName.S6_LOADER:
                loader_started_at = None

            if machine.awaiting_purchase_result and purchase_unknown_count >= 2:
                self.logger.warning(
                    "Unknown post-loader result detected, running recovery sequence"
                )
                self._execute_actions(("enter", "esc", "esc"))
                purchase_unknown_count = 0
                time.sleep(self.config.timings.detect_interval_ms / 1000.0)
                continue

            if (
                loader_started_at is not None
                and (time.monotonic() - loader_started_at) * 1000
                >= self.config.timings.purchase_timeout_ms
            ):
                self.logger.warning("Loader timed out, running recovery sequence")
                self._execute_actions(("enter", "esc", "esc"))
                loader_started_at = None
                time.sleep(self.config.timings.detect_interval_ms / 1000.0)
                continue

            decision = machine.handle(screen)
            self.logger.info(
                "screen=%s score=%.4f status=%s actions=%s message=%s",
                screen.value,
                detection.score,
                decision.status,
                ",".join(decision.actions),
                decision.message,
            )

            if decision.stop:
                return self._run_result(
                    status=decision.status,
                    screen=screen,
                    cycles=cycles,
                    elapsed_seconds=time.monotonic() - start_time,
                    message=decision.message,
                    score=detection.score,
                )

            if not decision.actions:
                time.sleep(self.config.timings.detect_interval_ms / 1000.0)
                continue

            if not dry_run:
                self._execute_actions(decision.actions)

            time.sleep(self.config.timings.detect_interval_ms / 1000.0)

    def detect(self, image_path: str | None = None) -> dict[str, Any]:
        if image_path is not None:
            image = Image.open(image_path).convert("RGB")
            detection = self.detector.detect(image)
            return {
                "status": "ok" if detection.matched else "unknown",
                "screen": detection.screen.value,
                "score": round(detection.score, 4),
                "threshold": detection.threshold,
                "scores": detection.scores if self.config.debug.show_detector_scores else {},
                "message": f"Detection completed for {image_path}.",
            }

        window, image = self._capture_window_image()
        if window is None or image is None:
            return {
                "status": "not_found",
                "screen": ScreenName.UNKNOWN.value,
                "message": "Game window was not found.",
            }

        detection = self.detector.detect(image)
        return {
            "status": "ok" if detection.matched else "unknown",
            "screen": detection.screen.value,
            "score": round(detection.score, 4),
            "threshold": detection.threshold,
            "scores": detection.scores if self.config.debug.show_detector_scores else {},
            "message": (
                "Screen detected."
                if detection.matched
                else "No stable screen match was found."
            ),
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

    def _execute_actions(self, actions: tuple[str, ...]) -> None:
        for action in actions:
            if action == "enter":
                self.input.press_enter()
                continue
            if action == "esc":
                self.input.press_escape()
                continue
            if action == "down":
                self.input.press_down()
                continue
            raise ValueError(f"Unsupported action: {action}")

    def _run_result(
        self,
        *,
        status: str,
        screen: ScreenName,
        cycles: int,
        elapsed_seconds: float,
        message: str,
        score: float | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "status": status,
            "screen": screen.value,
            "cycles": cycles,
            "elapsed_seconds": round(elapsed_seconds, 2),
            "message": message,
        }
        if score is not None:
            result["score"] = round(score, 4)
        return result
