from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(slots=True)
class WindowConfig:
    title_contains: str
    monitor_index: int
    required_width: int
    required_height: int


@dataclass(slots=True)
class ControlConfig:
    start_hotkey: str
    pause_hotkey: str
    stop_hotkey: str


@dataclass(slots=True)
class TimingConfig:
    after_enter_ms: int
    after_esc_ms: int
    after_down_ms: int
    buyout_selection_wait_ms: int
    buyout_down_retry_ms: int
    buyout_selection_timeout_ms: int
    detect_interval_ms: int
    search_timeout_ms: int
    purchase_timeout_ms: int
    startup_delay_ms: int


@dataclass(slots=True)
class DetectorConfig:
    match_threshold: float
    loader_match_threshold: float
    unknown_limit: int
    success_confirmations: int
    min_margin: float
    start_confirmations: int


@dataclass(slots=True)
class DebugConfig:
    save_unknown_frames: bool
    show_detector_scores: bool
    output_dir: str


@dataclass(slots=True)
class FlowConfig:
    trusted_start_search: bool
    fast_restart_search: bool


@dataclass(slots=True)
class AppConfig:
    window: WindowConfig
    controls: ControlConfig
    timings: TimingConfig
    detector: DetectorConfig
    debug: DebugConfig
    flow: FlowConfig


def load_config(config_path: str | Path) -> AppConfig:
    path = Path(config_path)
    raw = tomllib.loads(path.read_text(encoding="utf-8"))

    return AppConfig(
        window=WindowConfig(**raw["window"]),
        controls=ControlConfig(**raw["controls"]),
        timings=TimingConfig(**raw["timings"]),
        detector=DetectorConfig(**raw["detector"]),
        debug=DebugConfig(**raw["debug"]),
        flow=FlowConfig(**raw["flow"]),
    )
