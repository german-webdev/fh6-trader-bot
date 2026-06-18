from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bot.config import load_config
from bot.runtime import BotRuntime


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trade-bot",
        description="Desktop bot for auction search and buyout automation.",
    )
    parser.add_argument(
        "--config",
        default="config.toml",
        help="Path to the bot configuration file.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Start the bot runtime.")
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate flow without sending key presses.",
    )
    detect_parser = subparsers.add_parser("detect", help="Detect the current screen state.")
    detect_parser.add_argument(
        "--image",
        help="Optional path to a PNG file for offline screen detection.",
    )
    subparsers.add_parser("check-window", help="Validate game window settings.")
    subparsers.add_parser("debug-shot", help="Save a debug placeholder artifact.")

    return parser


def _load_runtime(config_path: str) -> BotRuntime:
    config = load_config(config_path)
    return BotRuntime(config)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        parser.error(f"Config file not found: {config_path}")

    runtime = _load_runtime(str(config_path))

    if args.command == "run":
        _print_json(runtime.run(dry_run=args.dry_run))
        return 0

    if args.command == "detect":
        _print_json(runtime.detect(image_path=args.image))
        return 0

    if args.command == "check-window":
        _print_json(runtime.check_window())
        return 0

    if args.command == "debug-shot":
        output_path = runtime.save_debug_shot()
        _print_json(
            {
                "status": "ok",
                "artifact": str(output_path),
            }
        )
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
