from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from PIL import Image

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
class PreparedVariants:
    color: np.ndarray
    gray: np.ndarray
    edges: np.ndarray
    binary: np.ndarray


@dataclass(slots=True)
class PreparedTrigger:
    trigger: ScreenTrigger
    template_size: tuple[int, int]
    variants: PreparedVariants


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
                min_score=0.88,
                mode="accent",
                search_radius=0.060,
            ),
            ScreenTrigger(
                (0.280, 0.640, 0.720, 0.780),
                weight=2.3,
                min_score=0.80,
                mode="accent",
                search_radius=0.120,
            ),
            ScreenTrigger(
                (0.300, 0.410, 0.505, 0.690),
                weight=1.0,
                min_score=0.70,
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


def _pil_to_bgr(image: Image.Image) -> np.ndarray:
    rgb = np.asarray(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _region_bounds(width: int, height: int, region: Region) -> tuple[int, int, int, int]:
    left = int(round(width * region[0]))
    top = int(round(height * region[1]))
    right = int(round(width * region[2]))
    bottom = int(round(height * region[3]))
    right = max(left + 1, right)
    bottom = max(top + 1, bottom)
    return (left, top, right, bottom)


def _crop_region(image: np.ndarray, region: Region) -> np.ndarray:
    height, width = image.shape[:2]
    left, top, right, bottom = _region_bounds(width, height, region)
    return image[top:bottom, left:right]


def _expand_region(region: Region, radius: float) -> Region:
    if radius <= 0.0:
        return region

    return (
        max(0.0, region[0] - radius),
        max(0.0, region[1] - radius),
        min(1.0, region[2] + radius),
        min(1.0, region[3] + radius),
    )


def _shift_region(region: Region, delta_x: float, delta_y: float) -> Region:
    width = region[2] - region[0]
    height = region[3] - region[1]
    left = min(max(0.0, region[0] + delta_x), 1.0 - width)
    top = min(max(0.0, region[1] + delta_y), 1.0 - height)
    return (left, top, left + width, top + height)


def _template_scale(width: int, height: int) -> float:
    max_width = 384
    max_height = 216
    return min(max_width / width, max_height / height, 1.0)


def _scaled_size(width: int, height: int, scale: float) -> tuple[int, int]:
    scaled_width = max(48, int(round(width * scale)))
    scaled_height = max(24, int(round(height * scale)))
    return (scaled_width, scaled_height)


def _resize(image: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    interpolation = cv2.INTER_AREA
    if image.shape[1] < size[0] or image.shape[0] < size[1]:
        interpolation = cv2.INTER_LINEAR
    return cv2.resize(image, size, interpolation=interpolation)


def _normalize_color(image: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    l_channel = cv2.equalizeHist(l_channel)
    normalized = cv2.merge((l_channel, a_channel, b_channel))
    return normalized


def _gray(image: np.ndarray) -> np.ndarray:
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.equalizeHist(grayscale)


def _binary(gray: np.ndarray) -> np.ndarray:
    _threshold, binary = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )
    return binary


def _edges(gray: np.ndarray) -> np.ndarray:
    return cv2.Canny(gray, 60, 160)


def _prepare_variants(
    image: np.ndarray,
    size: tuple[int, int],
) -> PreparedVariants:
    resized = _resize(image, size)
    gray = _gray(resized)
    return PreparedVariants(
        color=_normalize_color(resized),
        gray=gray,
        edges=_edges(gray),
        binary=_binary(gray),
    )


def _mean_similarity(current: np.ndarray, reference: np.ndarray) -> float:
    difference = cv2.absdiff(current, reference)
    if difference.ndim == 3:
        score = 1.0 - (float(difference.mean()) / 255.0)
    else:
        score = 1.0 - (float(np.mean(difference)) / 255.0)
    return max(0.0, min(1.0, score))


def _similarity(
    current: PreparedVariants,
    template: PreparedVariants,
    mode: MatchMode,
) -> float:
    edge_score = _mean_similarity(current.edges, template.edges)
    binary_score = _mean_similarity(current.binary, template.binary)

    if mode == "text":
        return max(0.0, min(1.0, (binary_score * 0.65) + (edge_score * 0.35)))

    color_score = _mean_similarity(current.color, template.color)
    gray_score = _mean_similarity(current.gray, template.gray)

    if mode == "accent":
        return max(
            0.0,
            min(
                1.0,
                (color_score * 0.45) + (binary_score * 0.20) + (edge_score * 0.35),
            ),
        )

    return max(
        0.0,
        min(
            1.0,
            (gray_score * 0.25)
            + (color_score * 0.20)
            + (edge_score * 0.40)
            + (binary_score * 0.15),
        ),
    )


class ScreenDetector:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        base_dir = _resource_dir()
        self.templates = {
            profile.screen: _pil_to_bgr(
                Image.open(base_dir / profile.filename).convert("RGB")
            )
            for profile in PROFILES
        }
        self.prepared_triggers = {
            profile.screen: self._prepare_profile(profile)
            for profile in PROFILES
        }

    def _prepare_profile(self, profile: ScreenProfile) -> tuple[PreparedTrigger, ...]:
        template = self.templates[profile.screen]
        prepared: list[PreparedTrigger] = []

        for trigger in profile.triggers:
            template_crop = _crop_region(template, trigger.region)
            scale = _template_scale(template_crop.shape[1], template_crop.shape[0])
            template_size = _scaled_size(
                template_crop.shape[1],
                template_crop.shape[0],
                scale,
            )

            prepared.append(
                PreparedTrigger(
                    trigger=trigger,
                    template_size=template_size,
                    variants=_prepare_variants(template_crop, template_size),
                )
            )

        return tuple(prepared)

    def _screen_threshold(self, screen: ScreenName) -> float:
        if screen is ScreenName.S6_LOADER:
            return self.config.detector.loader_match_threshold
        return self.config.detector.match_threshold

    def _score_profile(
        self,
        image: np.ndarray,
        profile: ScreenProfile,
    ) -> tuple[float, bool]:
        total_weight = 0.0
        weighted_score = 0.0
        minimum_trigger_score = 1.0
        all_required_triggers_matched = True

        for prepared_trigger in self.prepared_triggers[profile.screen]:
            trigger = prepared_trigger.trigger
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
                    current_crop = _crop_region(
                        image,
                        _shift_region(trigger.region, delta_x, delta_y),
                    )
                    current_variants = _prepare_variants(
                        current_crop,
                        prepared_trigger.template_size,
                    )
                    candidate_score = _similarity(
                        current_variants,
                        prepared_trigger.variants,
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
        image_bgr = _pil_to_bgr(image)
        profile_scores: dict[str, float] = {}
        profile_matches: dict[str, bool] = {}

        for profile in PROFILES:
            score, matched = self._score_profile(image_bgr, profile)
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
