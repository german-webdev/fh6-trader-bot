from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from bot.config import AppConfig
from bot.screens import ScreenName


Region = tuple[float, float, float, float]
MatchMode = Literal["hybrid", "text", "accent"]


@dataclass(slots=True)
class ScreenTrigger:
    region: Region
    weight: float = 1.0
    min_score: float = 0.84
    mode: MatchMode = "hybrid"
    search_radius: float = 0.0


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


@dataclass(slots=True)
class PreparedCrop:
    size: tuple[int, int]
    rgb: np.ndarray
    gray: np.ndarray
    edges: np.ndarray
    binary: np.ndarray


PROFILES: tuple[ScreenProfile, ...] = (
    ScreenProfile(
        screen=ScreenName.S1_SEARCH_MENU,
        filename="1. Поиск аукционов.png",
        triggers=(
            ScreenTrigger(
                (0.040, 0.145, 0.305, 0.255),
                weight=1.5,
                min_score=0.89,
                mode="text",
                search_radius=0.022,
            ),
            ScreenTrigger(
                (0.030, 0.540, 0.300, 0.730),
                weight=2.5,
                min_score=0.88,
                mode="accent",
                search_radius=0.200,
            ),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S2_SEARCH_CONFIRM,
        filename="2. Подтвердить поиск.png",
        triggers=(
            ScreenTrigger(
                (0.288, 0.235, 0.715, 0.360),
                weight=1.7,
                min_score=0.89,
                mode="accent",
                search_radius=0.060,
            ),
            ScreenTrigger(
                (0.280, 0.640, 0.720, 0.780),
                weight=2.3,
                min_score=0.89,
                mode="accent",
                search_radius=0.120,
            ),
            ScreenTrigger(
                (0.300, 0.410, 0.505, 0.690),
                weight=1.0,
                min_score=0.84,
                mode="text",
                search_radius=0.050,
            ),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S3A_LIST_PRESENT,
        filename="3-1. Лот присутствует.png",
        triggers=(
            ScreenTrigger(
                (0.040, 0.145, 0.305, 0.255),
                weight=1.0,
                min_score=0.89,
                mode="text",
                search_radius=0.022,
            ),
            ScreenTrigger(
                (0.505, 0.110, 0.975, 0.210),
                weight=1.7,
                min_score=0.92,
                mode="accent",
                search_radius=0.018,
            ),
            ScreenTrigger(
                (0.030, 0.145, 0.500, 0.310),
                weight=1.0,
                min_score=0.78,
                mode="accent",
                search_radius=0.020,
            ),
            ScreenTrigger(
                (0.735, 0.790, 0.940, 0.895),
                weight=2.0,
                min_score=0.89,
                mode="text",
                search_radius=0.018,
            ),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S3B_LIST_EMPTY,
        filename="3-2. Лот отсутствует.png",
        triggers=(
            ScreenTrigger(
                (0.040, 0.145, 0.305, 0.255),
                weight=1.0,
                min_score=0.89,
                mode="text",
                search_radius=0.022,
            ),
            ScreenTrigger(
                (0.592, 0.485, 0.915, 0.655),
                weight=2.4,
                min_score=0.94,
                mode="text",
                search_radius=0.020,
            ),
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


def _shift_region(region: Region, delta_x: float, delta_y: float) -> Region:
    width = region[2] - region[0]
    height = region[3] - region[1]
    left = min(max(0.0, region[0] + delta_x), 1.0 - width)
    top = min(max(0.0, region[1] + delta_y), 1.0 - height)
    return (left, top, left + width, top + height)


def _fit_size(size: tuple[int, int]) -> tuple[int, int]:
    width, height = size
    max_width = 384
    max_height = 216
    scale = min(max_width / width, max_height / height, 1.0)
    fitted_width = max(64, int(width * scale))
    fitted_height = max(32, int(height * scale))
    return (fitted_width, fitted_height)


def _grayscale_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.autocontrast(
        image.convert("L").resize(size, Image.Resampling.BILINEAR)
    )


def _rgb_array(image: Image.Image, size: tuple[int, int]) -> np.ndarray:
    prepared = image.convert("RGB").resize(size, Image.Resampling.BILINEAR)
    return np.asarray(prepared, dtype=np.float32)


def _gray_array(image: Image.Image, size: tuple[int, int]) -> np.ndarray:
    return np.asarray(_grayscale_image(image, size), dtype=np.float32)


def _edge_array(image: Image.Image, size: tuple[int, int]) -> np.ndarray:
    prepared = _grayscale_image(image, size).filter(ImageFilter.FIND_EDGES)
    return np.asarray(prepared, dtype=np.float32)


def _otsu_threshold(array: np.ndarray) -> int:
    pixels = array.astype(np.uint8).reshape(-1)
    if pixels.size == 0:
        return 127

    histogram = np.bincount(pixels, minlength=256).astype(np.float64)
    total = histogram.sum()
    cumulative_weight = np.cumsum(histogram)
    cumulative_mean = np.cumsum(histogram * np.arange(256, dtype=np.float64))
    global_mean = cumulative_mean[-1]

    denominator = cumulative_weight * (total - cumulative_weight)
    numerator = (global_mean * cumulative_weight - cumulative_mean) ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        variance = np.where(denominator > 0, numerator / denominator, 0.0)

    threshold = int(np.argmax(variance))
    return max(96, min(192, threshold))


def _binary_array(image: Image.Image, size: tuple[int, int]) -> np.ndarray:
    grayscale = _gray_array(image, size)
    threshold = _otsu_threshold(grayscale)
    return np.where(grayscale >= threshold, 255.0, 0.0)


def _prepare_crop(
    image: Image.Image,
    *,
    size: tuple[int, int] | None = None,
) -> PreparedCrop:
    prepared_size = _fit_size(image.size) if size is None else size
    return PreparedCrop(
        size=prepared_size,
        rgb=_rgb_array(image, prepared_size),
        gray=_gray_array(image, prepared_size),
        edges=_edge_array(image, prepared_size),
        binary=_binary_array(image, prepared_size),
    )


def _mean_similarity(current: np.ndarray, reference: np.ndarray) -> float:
    score = 1.0 - (np.abs(current - reference).mean() / 255.0)
    return max(0.0, min(1.0, float(score)))


def _binary_similarity(current: np.ndarray, reference: np.ndarray) -> float:
    current_mask = current >= 128.0
    reference_mask = reference >= 128.0
    score = float((current_mask == reference_mask).mean())
    return max(0.0, min(1.0, score))


def _similarity(
    current: PreparedCrop,
    reference: PreparedCrop,
    mode: MatchMode,
) -> float:
    edge_score = _mean_similarity(current.edges, reference.edges)
    binary_score = _binary_similarity(current.binary, reference.binary)

    if mode == "text":
        score = (binary_score * 0.65) + (edge_score * 0.35)
        return max(0.0, min(1.0, float(score)))

    rgb_score = _mean_similarity(current.rgb, reference.rgb)
    gray_score = _mean_similarity(current.gray, reference.gray)

    if mode == "accent":
        score = (rgb_score * 0.40) + (binary_score * 0.25) + (edge_score * 0.35)
        return max(0.0, min(1.0, float(score)))

    score = (gray_score * 0.25) + (rgb_score * 0.20) + (edge_score * 0.40) + (
        binary_score * 0.15
    )
    return max(0.0, min(1.0, float(score)))


class ScreenDetector:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        base_dir = _resource_dir()
        self.templates = {
            profile.screen: Image.open(base_dir / profile.filename).convert("RGB")
            for profile in PROFILES
        }
        self.reference_crops = {
            profile.screen: tuple(
                _prepare_crop(_crop_region(self.templates[profile.screen], trigger.region))
                for trigger in profile.triggers
            )
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
        total_weight = 0.0
        weighted_score = 0.0
        minimum_trigger_score = 1.0
        all_required_triggers_matched = True

        for index, trigger in enumerate(profile.triggers):
            reference_crop = self.reference_crops[profile.screen][index]
            trigger_score = 0.0
            search_offsets = (0.0,)
            if trigger.search_radius > 0.0:
                search_offsets = (
                    -trigger.search_radius,
                    0.0,
                    trigger.search_radius,
                )

            for delta_y in search_offsets:
                for delta_x in search_offsets:
                    current_crop = _prepare_crop(
                        _crop_region(
                            image,
                            _shift_region(trigger.region, delta_x, delta_y),
                        ),
                        size=reference_crop.size,
                    )
                    candidate_score = _similarity(
                        current_crop,
                        reference_crop,
                        trigger.mode,
                    )
                    trigger_score = max(trigger_score, candidate_score)

            weighted_score += trigger_score * trigger.weight
            total_weight += trigger.weight
            minimum_trigger_score = min(minimum_trigger_score, trigger_score)
            if trigger_score < trigger.min_score:
                all_required_triggers_matched = False

        profile_score = weighted_score / total_weight
        effective_score = profile_score
        if not all_required_triggers_matched:
            effective_score = min(
                profile_score,
                minimum_trigger_score,
                self._screen_threshold(profile.screen) - 0.02,
            )
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
