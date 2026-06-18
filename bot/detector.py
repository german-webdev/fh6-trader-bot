from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from bot.config import AppConfig
from bot.screens import ScreenName


Region = tuple[float, float, float, float]


@dataclass(slots=True)
class ScreenTrigger:
    region: Region
    weight: float = 1.0
    min_score: float = 0.84


@dataclass(slots=True)
class ScreenProfile:
    screen: ScreenName
    filename: str
    triggers: tuple[ScreenTrigger, ...]


@dataclass(slots=True)
class DetectionResult:
    screen: ScreenName
    score: float
    threshold: float
    margin: float
    scores: dict[str, float]

    @property
    def matched(self) -> bool:
        return self.screen is not ScreenName.UNKNOWN


PROFILES: tuple[ScreenProfile, ...] = (
    ScreenProfile(
        screen=ScreenName.S1_SEARCH_MENU,
        filename="1. Поиск аукционов.png",
        triggers=(
            ScreenTrigger((0.03, 0.10, 0.27, 0.18), weight=1.2, min_score=0.88),
            ScreenTrigger((0.02, 0.47, 0.25, 0.58), weight=1.8, min_score=0.90),
            ScreenTrigger((0.03, 0.92, 0.24, 0.99), weight=1.0, min_score=0.86),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S2_SEARCH_CONFIRM,
        filename="2. Подтвердить поиск.png",
        triggers=(
            ScreenTrigger((0.23, 0.23, 0.57, 0.37), weight=1.3, min_score=0.88),
            ScreenTrigger((0.23, 0.73, 0.58, 0.84), weight=1.8, min_score=0.90),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S3A_LIST_PRESENT,
        filename="3-1. Лот присутствует.png",
        triggers=(
            ScreenTrigger((0.03, 0.10, 0.27, 0.18), weight=1.0, min_score=0.88),
            ScreenTrigger((0.51, 0.11, 0.98, 0.20), weight=1.5, min_score=0.88),
            ScreenTrigger((0.54, 0.69, 0.70, 0.82), weight=1.2, min_score=0.84),
            ScreenTrigger((0.54, 0.80, 0.74, 0.92), weight=1.5, min_score=0.84),
            ScreenTrigger((0.79, 0.80, 0.97, 0.92), weight=1.8, min_score=0.84),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S3B_LIST_EMPTY,
        filename="3-2. Лот отсутствует.png",
        triggers=(
            ScreenTrigger((0.03, 0.10, 0.27, 0.18), weight=1.0, min_score=0.88),
            ScreenTrigger((0.58, 0.46, 0.95, 0.64), weight=2.0, min_score=0.90),
            ScreenTrigger((0.03, 0.92, 0.20, 0.99), weight=1.0, min_score=0.86),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S4_LOT_DETAILS,
        filename="4. Экран с выбраной кнопкой выкупа.png",
        triggers=(
            ScreenTrigger((0.03, 0.10, 0.24, 0.19), weight=1.2, min_score=0.88),
            ScreenTrigger((0.03, 0.84, 0.22, 0.95), weight=2.0, min_score=0.90),
            ScreenTrigger((0.03, 0.92, 0.22, 0.99), weight=1.0, min_score=0.86),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S5_BUY_CONFIRM,
        filename="5. Экран подтверждения.png",
        triggers=(
            ScreenTrigger((0.26, 0.32, 0.55, 0.40), weight=1.2, min_score=0.90),
            ScreenTrigger((0.34, 0.40, 0.66, 0.48), weight=1.0, min_score=0.86),
            ScreenTrigger((0.26, 0.48, 0.54, 0.59), weight=2.0, min_score=0.92),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S6_LOADER,
        filename="6. Экран с лоадером.png",
        triggers=(
            ScreenTrigger((0.26, 0.32, 0.55, 0.40), weight=1.0, min_score=0.88),
            ScreenTrigger((0.32, 0.40, 0.67, 0.55), weight=2.1, min_score=0.90),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S7_BUY_SUCCESS,
        filename="7. Экран успешного выкупа.png",
        triggers=(
            ScreenTrigger((0.26, 0.34, 0.55, 0.42), weight=1.4, min_score=0.90),
            ScreenTrigger((0.28, 0.41, 0.67, 0.56), weight=1.8, min_score=0.88),
            ScreenTrigger((0.03, 0.95, 0.13, 0.99), weight=0.8, min_score=0.82),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S8_FINAL_SUCCESS,
        filename="8. Финальный экран.png",
        triggers=(
            ScreenTrigger((0.03, 0.10, 0.26, 0.19), weight=1.0, min_score=0.88),
            ScreenTrigger((0.03, 0.26, 0.27, 0.41), weight=1.2, min_score=0.84),
            ScreenTrigger((0.03, 0.81, 0.34, 0.96), weight=2.4, min_score=0.84),
        ),
    ),
)


def _resource_dir() -> Path:
    return Path(resources.files("bot").joinpath("resources", "reference"))


def _crop_region(image: Image.Image, region: Region) -> Image.Image:
    width, height = image.size
    left = int(width * region[0])
    top = int(height * region[1])
    right = int(width * region[2])
    bottom = int(height * region[3])
    return image.crop((left, top, right, bottom))


def _fit_size(size: tuple[int, int]) -> tuple[int, int]:
    width, height = size
    max_width = 320
    max_height = 180
    scale = min(max_width / width, max_height / height, 1.0)
    fitted_width = max(48, int(width * scale))
    fitted_height = max(24, int(height * scale))
    return (fitted_width, fitted_height)


def _to_array(image: Image.Image, size: tuple[int, int]) -> np.ndarray:
    prepared = ImageOps.autocontrast(
        image.convert("L").resize(size, Image.Resampling.BILINEAR)
    )
    return np.asarray(prepared, dtype=np.float32)


def _to_edge_array(image: Image.Image, size: tuple[int, int]) -> np.ndarray:
    prepared = ImageOps.autocontrast(
        image.convert("L")
        .resize(size, Image.Resampling.BILINEAR)
        .filter(ImageFilter.FIND_EDGES)
    )
    return np.asarray(prepared, dtype=np.float32)


def _similarity(current: Image.Image, reference: Image.Image) -> float:
    size = _fit_size(reference.size)
    current_gray = _to_array(current, size)
    reference_gray = _to_array(reference, size)
    current_edges = _to_edge_array(current, size)
    reference_edges = _to_edge_array(reference, size)

    gray_score = 1.0 - (np.abs(current_gray - reference_gray).mean() / 255.0)
    edge_score = 1.0 - (np.abs(current_edges - reference_edges).mean() / 255.0)
    score = (gray_score * 0.35) + (edge_score * 0.65)
    return max(0.0, min(1.0, float(score)))


class ScreenDetector:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        base_dir = _resource_dir()
        self.templates = {
            profile.screen: Image.open(base_dir / profile.filename).convert("RGB")
            for profile in PROFILES
        }

    def _screen_threshold(self, screen: ScreenName) -> float:
        if screen is ScreenName.S6_LOADER:
            return self.config.detector.loader_match_threshold
        return self.config.detector.match_threshold

    def _score_profile(
        self,
        image: Image.Image,
        profile: ScreenProfile,
    ) -> tuple[float, bool]:
        reference = self.templates[profile.screen]
        total_weight = 0.0
        weighted_score = 0.0
        minimum_trigger_score = 1.0
        all_required_triggers_matched = True

        for trigger in profile.triggers:
            current_crop = _crop_region(image, trigger.region)
            reference_crop = _crop_region(reference, trigger.region)
            trigger_score = _similarity(current_crop, reference_crop)
            weighted_score += trigger_score * trigger.weight
            total_weight += trigger.weight
            minimum_trigger_score = min(minimum_trigger_score, trigger_score)
            if trigger_score < trigger.min_score:
                all_required_triggers_matched = False

        profile_score = weighted_score / total_weight
        effective_score = profile_score
        if not all_required_triggers_matched:
            effective_score = min(profile_score, minimum_trigger_score)
        return (float(effective_score), all_required_triggers_matched)

    def detect(self, image: Image.Image) -> DetectionResult:
        profile_scores: dict[str, float] = {}
        profile_matches: dict[str, bool] = {}

        for profile in PROFILES:
            score, matched = self._score_profile(image, profile)
            profile_scores[profile.screen.value] = score
            profile_matches[profile.screen.value] = matched

        ordered = sorted(profile_scores.items(), key=lambda item: item[1], reverse=True)
        best_screen_value, best_score = ordered[0]
        second_best = ordered[1][1] if len(ordered) > 1 else 0.0
        margin = best_score - second_best

        best_screen = ScreenName(best_screen_value)
        threshold = self._screen_threshold(best_screen)
        if (
            best_score < threshold
            or margin < self.config.detector.min_margin
            or not profile_matches[best_screen.value]
        ):
            return DetectionResult(
                screen=ScreenName.UNKNOWN,
                score=best_score,
                threshold=threshold,
                margin=margin,
                scores=profile_scores,
            )

        return DetectionResult(
            screen=best_screen,
            score=best_score,
            threshold=threshold,
            margin=margin,
            scores=profile_scores,
        )
