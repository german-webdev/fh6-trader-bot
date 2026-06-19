from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Iterable, Literal

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
                min_score=0.84,
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
                min_score=0.84,
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
                (0.030, 0.085, 0.290, 0.165),
                weight=1.0,
                min_score=0.90,
                mode="accent",
                search_radius=0.022,
            ),
            ScreenTrigger(
                (0.580, 0.500, 0.930, 0.670),
                weight=2.4,
                min_score=0.78,
                mode="accent",
                search_radius=0.020,
            ),
            ScreenTrigger(
                (0.030, 0.935, 0.270, 0.995),
                weight=1.1,
                min_score=0.88,
                mode="accent",
                search_radius=0.010,
            ),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S4_LOT_LOADING,
        filename="4a. Загрузка описания аукциона.png",
        triggers=(
            ScreenTrigger(
                (0.400, 0.170, 0.850, 0.285),
                weight=1.8,
                min_score=0.83,
                mode="accent",
                search_radius=0.020,
            ),
            ScreenTrigger(
                (0.410, 0.405, 0.805, 0.505),
                weight=1.3,
                min_score=0.76,
                mode="text",
                search_radius=0.025,
            ),
            ScreenTrigger(
                (0.575, 0.600, 0.695, 0.760),
                weight=1.0,
                min_score=0.72,
                mode="accent",
                search_radius=0.025,
            ),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S4_LOT_DETAILS,
        filename="4. Экран с выбраной кнопкой выкупа.png",
        triggers=(
            ScreenTrigger(
                (0.040, 0.145, 0.345, 0.255),
                weight=1.4,
                min_score=0.84,
                mode="text",
                search_radius=0.022,
            ),
            ScreenTrigger(
                (0.040, 0.245, 0.345, 0.335),
                weight=1.2,
                min_score=0.78,
                mode="accent",
                search_radius=0.025,
            ),
            ScreenTrigger(
                (0.035, 0.835, 0.355, 0.995),
                weight=2.5,
                min_score=0.82,
                mode="accent",
                search_radius=0.025,
            ),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S5_BUY_CONFIRM,
        filename="5. Экран подтверждения.png",
        triggers=(
            ScreenTrigger(
                (0.325, 0.420, 0.680, 0.530),
                weight=1.8,
                min_score=0.84,
                mode="accent",
                search_radius=0.018,
            ),
            ScreenTrigger(
                (0.395, 0.535, 0.615, 0.605),
                weight=1.0,
                min_score=0.74,
                mode="text",
                search_radius=0.018,
            ),
            ScreenTrigger(
                (0.325, 0.585, 0.685, 0.675),
                weight=2.2,
                min_score=0.82,
                mode="accent",
                search_radius=0.020,
            ),
            ScreenTrigger(
                (0.350, 0.675, 0.685, 0.740),
                weight=0.8,
                min_score=0.76,
                mode="hybrid",
                search_radius=0.018,
            ),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S6_LOADER,
        filename="6. Экран с лоадером.png",
        triggers=(
            ScreenTrigger(
                (0.325, 0.420, 0.680, 0.530),
                weight=1.6,
                min_score=0.84,
                mode="accent",
                search_radius=0.018,
            ),
            ScreenTrigger(
                (0.400, 0.545, 0.625, 0.620),
                weight=1.2,
                min_score=0.72,
                mode="text",
                search_radius=0.018,
            ),
            ScreenTrigger(
                (0.465, 0.600, 0.565, 0.765),
                weight=1.3,
                min_score=0.70,
                mode="accent",
                search_radius=0.025,
            ),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S7_BUY_SUCCESS,
        filename="7. Экран успешного выкупа.png",
        triggers=(
            ScreenTrigger(
                (0.325, 0.445, 0.690, 0.555),
                weight=1.8,
                min_score=0.84,
                mode="accent",
                search_radius=0.018,
            ),
            ScreenTrigger(
                (0.365, 0.545, 0.685, 0.665),
                weight=1.2,
                min_score=0.72,
                mode="text",
                search_radius=0.018,
            ),
            ScreenTrigger(
                (0.000, 0.950, 0.120, 0.995),
                weight=0.8,
                min_score=0.78,
                mode="accent",
                search_radius=0.010,
            ),
        ),
    ),
    ScreenProfile(
        screen=ScreenName.S8_FINAL_SUCCESS,
        filename="8. Финальный экран.png",
        triggers=(
            ScreenTrigger(
                (0.040, 0.145, 0.345, 0.255),
                weight=1.0,
                min_score=0.82,
                mode="text",
                search_radius=0.022,
            ),
            ScreenTrigger(
                (0.040, 0.755, 0.290, 0.815),
                weight=1.5,
                min_score=0.76,
                mode="accent",
                search_radius=0.020,
            ),
            ScreenTrigger(
                (0.035, 0.815, 0.310, 0.970),
                weight=2.4,
                min_score=0.80,
                mode="accent",
                search_radius=0.020,
            ),
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


def _crop_pixels(
    image: np.ndarray,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> np.ndarray:
    return image[top:bottom, left:right]


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


def _template_match_score(search: np.ndarray, template: np.ndarray) -> float:
    if (
        search.shape[0] < template.shape[0]
        or search.shape[1] < template.shape[1]
        or template.size == 0
    ):
        return 0.0

    result = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
    return max(0.0, min(1.0, float(result.max())))


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

        sold_source = _pil_to_bgr(
            Image.open(base_dir / "sold_badge_source.png").convert("RGB")
        )
        sold_badge = _crop_pixels(sold_source, 24, 6, 252, 104)
        self.sold_badge_template = _edges(_gray(sold_badge))
        self.sold_badge_color_template = _normalize_color(sold_badge)

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
        if screen is ScreenName.S3_LIST_LOADING:
            return 0.86
        if screen is ScreenName.S4_LOT_SOLD:
            return 0.60
        if screen is ScreenName.S3C_LIST_SOLD:
            return 0.56
        if screen is ScreenName.S4_LOT_LOADING:
            return 0.80
        if screen is ScreenName.S4_BUYOUT_SELECTED:
            return 0.82
        if screen in {
            ScreenName.S4_LOT_DETAILS,
            ScreenName.S5_BUY_CONFIRM,
            ScreenName.S7_BUY_SUCCESS,
            ScreenName.S8_FINAL_SUCCESS,
        }:
            return 0.80
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
        if profile.screen is ScreenName.S4_LOT_DETAILS:
            ready_score = self._score_lot_details_ready(image)
            if ready_score < 0.80:
                return (
                    float(min(profile_score, ready_score, self._screen_threshold(profile.screen) - 0.02)),
                    False,
                )

        effective_score = profile_score
        if not all_required_triggers_matched:
            effective_score = min(
                profile_score,
                minimum_trigger_score,
                self._screen_threshold(profile.screen) - 0.02,
            )
        return (float(effective_score), all_required_triggers_matched)

    def _score_sold_badge(self, image: np.ndarray) -> float:
        search_regions: tuple[Region, ...] = (
            (0.040, 0.165, 0.165, 0.305),
        )
        scales = (0.70, 0.82, 0.94, 1.06, 1.18)
        best_score = 0.0

        for region in search_regions:
            search_crop = _crop_region(image, region)
            search_edges = _edges(_gray(search_crop))
            search_color = _normalize_color(search_crop)
            search_gray = _gray(search_crop)
            hsv = cv2.cvtColor(search_crop, cv2.COLOR_BGR2HSV)
            yellow_mask = cv2.inRange(
                hsv,
                np.array([16, 110, 150], dtype=np.uint8),
                np.array([42, 255, 255], dtype=np.uint8),
            )
            kernel = np.ones((5, 5), dtype=np.uint8)
            yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
            yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)

            contours, _hierarchy = cv2.findContours(
                yellow_mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            crop_area = float(search_crop.shape[0] * search_crop.shape[1])
            for contour in contours:
                area = float(cv2.contourArea(contour))
                if crop_area <= 0 or area / crop_area < 0.015:
                    continue

                rect = cv2.minAreaRect(contour)
                width, height = rect[1]
                if width < 1.0 or height < 1.0:
                    continue

                aspect_ratio = max(width, height) / min(width, height)
                if aspect_ratio < 1.6 or aspect_ratio > 5.5:
                    continue

                angle = float(rect[2])
                if width < height:
                    angle += 90.0
                normalized_angle = abs(angle)
                if normalized_angle < 8.0 or normalized_angle > 35.0:
                    continue

                x, y, w, h = cv2.boundingRect(contour)
                contour_mask = yellow_mask[y : y + h, x : x + w]
                dark_pixels = np.count_nonzero(
                    (search_gray[y : y + h, x : x + w] < 95) & (contour_mask > 0)
                )
                filled_pixels = max(1, np.count_nonzero(contour_mask))
                dark_ratio = dark_pixels / filled_pixels
                if dark_ratio < 0.06:
                    continue

                area_score = min(1.0, (area / crop_area) / 0.12)
                ratio_score = min(1.0, aspect_ratio / 3.5)
                dark_score = min(1.0, dark_ratio / 0.20)
                angle_score = min(1.0, normalized_angle / 18.0)
                best_score = max(
                    best_score,
                    (area_score * 0.35)
                    + (ratio_score * 0.15)
                    + (dark_score * 0.25)
                    + (angle_score * 0.25),
                )

            for scale in scales:
                width = max(24, int(round(self.sold_badge_template.shape[1] * scale)))
                height = max(16, int(round(self.sold_badge_template.shape[0] * scale)))
                edge_template = cv2.resize(
                    self.sold_badge_template,
                    (width, height),
                    interpolation=cv2.INTER_LINEAR,
                )
                color_template = cv2.resize(
                    self.sold_badge_color_template,
                    (width, height),
                    interpolation=cv2.INTER_LINEAR,
                )
                edge_score = _template_match_score(search_edges, edge_template)
                color_score = _template_match_score(search_color, color_template)
                best_score = max(
                    best_score,
                    (edge_score * 0.55) + (color_score * 0.45),
                )

        return best_score

    def _score_list_loading(self, image: np.ndarray) -> float:
        bands: tuple[Region, ...] = (
            (0.040, 0.150, 0.490, 0.310),
            (0.040, 0.340, 0.490, 0.520),
            (0.040, 0.535, 0.490, 0.700),
            (0.040, 0.715, 0.490, 0.890),
        )
        white_ratios: list[float] = []

        for band in bands:
            crop = _crop_region(image, band)
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            _threshold, white_mask = cv2.threshold(
                gray,
                220,
                255,
                cv2.THRESH_BINARY,
            )
            white_ratios.append(
                np.count_nonzero(white_mask) / max(1, white_mask.size)
            )

        average_white = sum(white_ratios) / len(white_ratios)
        minimum_white = min(white_ratios)
        filled_bands = sum(1 for ratio in white_ratios if ratio >= 0.93)

        average_score = min(1.0, average_white / 0.96)
        minimum_score = min(1.0, minimum_white / 0.90)
        bands_score = filled_bands / len(white_ratios)

        return float(
            (average_score * 0.45)
            + (minimum_score * 0.35)
            + (bands_score * 0.20)
        )

    def _score_lot_details_ready(self, image: np.ndarray) -> float:
        bottom_crop = _crop_region(image, (0.035, 0.835, 0.355, 0.995))
        bottom_hsv = cv2.cvtColor(bottom_crop, cv2.COLOR_BGR2HSV)
        bottom_gray = cv2.cvtColor(bottom_crop, cv2.COLOR_BGR2GRAY)

        lime_mask = cv2.inRange(
            bottom_hsv,
            np.array([30, 60, 100], dtype=np.uint8),
            np.array([95, 255, 255], dtype=np.uint8),
        )
        _threshold, white_mask = cv2.threshold(
            bottom_gray,
            200,
            255,
            cv2.THRESH_BINARY,
        )
        _threshold, dark_mask = cv2.threshold(
            bottom_gray,
            60,
            255,
            cv2.THRESH_BINARY_INV,
        )

        lime_ratio = np.count_nonzero(lime_mask) / max(1, lime_mask.size)
        white_ratio = np.count_nonzero(white_mask) / max(1, white_mask.size)
        dark_ratio = np.count_nonzero(dark_mask) / max(1, dark_mask.size)

        if lime_ratio < 0.015:
            return 0.0

        lime_score = min(1.0, lime_ratio / 0.025)
        white_score = min(1.0, white_ratio / 0.035)
        dark_score = min(1.0, dark_ratio / 0.65)

        return float(
            (dark_score * 0.45)
            + (white_score * 0.35)
            + (lime_score * 0.20)
        )

    def _score_buyout_selected(self, image: np.ndarray) -> float:
        buyout_crop = _crop_region(image, (0.032, 0.795, 0.285, 0.885))
        bid_crop = _crop_region(image, (0.032, 0.735, 0.285, 0.815))

        buyout_hsv = cv2.cvtColor(buyout_crop, cv2.COLOR_BGR2HSV)
        bid_hsv = cv2.cvtColor(bid_crop, cv2.COLOR_BGR2HSV)
        buyout_gray = cv2.cvtColor(buyout_crop, cv2.COLOR_BGR2GRAY)

        lime_lower = np.array([30, 95, 130], dtype=np.uint8)
        lime_upper = np.array([88, 255, 255], dtype=np.uint8)
        buyout_lime_mask = cv2.inRange(buyout_hsv, lime_lower, lime_upper)
        bid_lime_mask = cv2.inRange(bid_hsv, lime_lower, lime_upper)

        red_mask_1 = cv2.inRange(
            buyout_hsv,
            np.array([0, 85, 130], dtype=np.uint8),
            np.array([12, 255, 255], dtype=np.uint8),
        )
        red_mask_2 = cv2.inRange(
            buyout_hsv,
            np.array([170, 85, 130], dtype=np.uint8),
            np.array([179, 255, 255], dtype=np.uint8),
        )
        yellow_mask = cv2.inRange(
            buyout_hsv,
            np.array([18, 90, 130], dtype=np.uint8),
            np.array([42, 255, 255], dtype=np.uint8),
        )
        _threshold, white_mask = cv2.threshold(
            buyout_gray,
            185,
            255,
            cv2.THRESH_BINARY,
        )
        _threshold, dark_mask = cv2.threshold(
            buyout_gray,
            80,
            255,
            cv2.THRESH_BINARY_INV,
        )

        buyout_lime_ratio = np.count_nonzero(buyout_lime_mask) / max(
            1,
            buyout_lime_mask.size,
        )
        bid_lime_ratio = np.count_nonzero(bid_lime_mask) / max(
            1,
            bid_lime_mask.size,
        )
        red_ratio = (
            np.count_nonzero(red_mask_1 | red_mask_2) / max(1, red_mask_1.size)
        )
        yellow_ratio = np.count_nonzero(yellow_mask) / max(1, yellow_mask.size)
        white_ratio = np.count_nonzero(white_mask) / max(1, white_mask.size)
        dark_ratio = np.count_nonzero(dark_mask) / max(1, dark_mask.size)

        if buyout_lime_ratio < 0.030:
            return 0.0
        if buyout_lime_ratio <= bid_lime_ratio * 1.20:
            return 0.0

        lime_score = min(1.0, buyout_lime_ratio / 0.050)
        selected_delta_score = min(
            1.0,
            (buyout_lime_ratio - bid_lime_ratio) / 0.035,
        )
        dark_score = min(1.0, dark_ratio / 0.45)
        text_score = min(1.0, (white_ratio + red_ratio + yellow_ratio) / 0.18)

        return float(
            (lime_score * 0.35)
            + (selected_delta_score * 0.30)
            + (dark_score * 0.20)
            + (text_score * 0.15)
        )

    def _score_lot_sold_detail(self, image: np.ndarray) -> float:
        status_crop = _crop_region(image, (0.165, 0.680, 0.285, 0.755))
        full_left_crop = _crop_region(image, (0.030, 0.120, 0.290, 0.760))

        status_hsv = cv2.cvtColor(status_crop, cv2.COLOR_BGR2HSV)
        status_gray = cv2.cvtColor(status_crop, cv2.COLOR_BGR2GRAY)
        full_left_gray = cv2.cvtColor(full_left_crop, cv2.COLOR_BGR2GRAY)

        green_mask = cv2.inRange(
            status_hsv,
            np.array([42, 70, 80], dtype=np.uint8),
            np.array([85, 255, 255], dtype=np.uint8),
        )
        _threshold, white_mask = cv2.threshold(
            status_gray,
            190,
            255,
            cv2.THRESH_BINARY,
        )
        _threshold, dark_mask = cv2.threshold(
            full_left_gray,
            80,
            255,
            cv2.THRESH_BINARY_INV,
        )

        green_ratio = np.count_nonzero(green_mask) / max(1, green_mask.size)
        white_ratio = np.count_nonzero(white_mask) / max(1, white_mask.size)
        dark_ratio = np.count_nonzero(dark_mask) / max(1, dark_mask.size)

        green_score = min(1.0, green_ratio / 0.28)
        white_score = min(1.0, white_ratio / 0.11)
        panel_score = min(1.0, dark_ratio / 0.55)

        return float(
            (green_score * 0.45)
            + (white_score * 0.35)
            + (panel_score * 0.20)
        )

    def _score_empty_auction_message(self, image: np.ndarray) -> float:
        search_crop = _crop_region(image, (0.550, 0.460, 0.910, 0.620))
        gray = cv2.cvtColor(search_crop, cv2.COLOR_BGR2GRAY)
        _threshold, white_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        kernel = np.ones((3, 3), dtype=np.uint8)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)

        white_ratio = np.count_nonzero(white_mask) / max(1, white_mask.size)
        contours, _hierarchy = cv2.findContours(
            white_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        character_boxes: list[tuple[int, int, int, int]] = []
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            if area > 20 and 3 < width < 90 and 8 < height < 90:
                character_boxes.append((x, y, width, height))

        if not character_boxes:
            return 0.0

        centers_y = [y + (height / 2.0) for _x, y, _width, height in character_boxes]
        line_histogram = np.histogram(
            centers_y,
            bins=8,
            range=(0, search_crop.shape[0]),
        )[0]
        text_lines = sum(1 for value in line_histogram if value >= 4)

        white_score = min(1.0, white_ratio / 0.08)
        character_score = min(1.0, len(character_boxes) / 25.0)
        line_score = 1.0 if text_lines >= 2 else 0.0

        return float(
            (white_score * 0.45)
            + (character_score * 0.35)
            + (line_score * 0.20)
        )

    def detect(
        self,
        image: Image.Image,
        candidates: Iterable[ScreenName] | None = None,
    ) -> DetectionResult:
        image_bgr = _pil_to_bgr(image)
        profile_scores: dict[str, float] = {}
        profile_matches: dict[str, bool] = {}
        candidate_set = set(candidates) if candidates is not None else None

        for profile in PROFILES:
            if candidate_set is not None and profile.screen not in candidate_set:
                continue

            score, matched = self._score_profile(image_bgr, profile)
            profile_scores[profile.screen.value] = score
            profile_matches[profile.screen.value] = matched

        should_score_empty_message = (
            candidate_set is None or ScreenName.S3B_LIST_EMPTY in candidate_set
        )
        if should_score_empty_message:
            empty_message_score = self._score_empty_auction_message(image_bgr)
            current_score = profile_scores.get(ScreenName.S3B_LIST_EMPTY.value, 0.0)
            profile_scores[ScreenName.S3B_LIST_EMPTY.value] = max(
                current_score,
                empty_message_score,
            )
            profile_matches[ScreenName.S3B_LIST_EMPTY.value] = (
                profile_scores[ScreenName.S3B_LIST_EMPTY.value]
                >= self._screen_threshold(ScreenName.S3B_LIST_EMPTY)
            )

        should_score_list_loading = (
            candidate_set is None or ScreenName.S3_LIST_LOADING in candidate_set
        )
        if should_score_list_loading:
            list_loading_score = self._score_list_loading(image_bgr)
            profile_scores[ScreenName.S3_LIST_LOADING.value] = list_loading_score
            profile_matches[ScreenName.S3_LIST_LOADING.value] = (
                list_loading_score
                >= self._screen_threshold(ScreenName.S3_LIST_LOADING)
            )

            if list_loading_score >= self._screen_threshold(ScreenName.S3_LIST_LOADING):
                best_other_score = max(
                    (
                        score
                        for screen, score in profile_scores.items()
                        if screen != ScreenName.S3_LIST_LOADING.value
                    ),
                    default=0.0,
                )
                return DetectionResult(
                    screen=ScreenName.S3_LIST_LOADING,
                    score=float(list_loading_score),
                    threshold=self._screen_threshold(ScreenName.S3_LIST_LOADING),
                    margin=max(
                        self.config.detector.min_margin,
                        float(list_loading_score - best_other_score),
                    ),
                    scores=profile_scores,
                )

        should_score_buyout_selected = (
            candidate_set is None or ScreenName.S4_BUYOUT_SELECTED in candidate_set
        )
        if should_score_buyout_selected:
            buyout_selected_score = self._score_buyout_selected(image_bgr)
            profile_scores[ScreenName.S4_BUYOUT_SELECTED.value] = buyout_selected_score
            profile_matches[ScreenName.S4_BUYOUT_SELECTED.value] = (
                buyout_selected_score
                >= self._screen_threshold(ScreenName.S4_BUYOUT_SELECTED)
            )

            best_other_score = max(
                (
                    score
                    for screen, score in profile_scores.items()
                    if screen != ScreenName.S4_BUYOUT_SELECTED.value
                ),
                default=0.0,
            )
            if (
                buyout_selected_score
                >= self._screen_threshold(ScreenName.S4_BUYOUT_SELECTED)
                and buyout_selected_score >= best_other_score
            ):
                return DetectionResult(
                    screen=ScreenName.S4_BUYOUT_SELECTED,
                    score=float(buyout_selected_score),
                    threshold=self._screen_threshold(ScreenName.S4_BUYOUT_SELECTED),
                    margin=max(
                        self.config.detector.min_margin,
                        float(buyout_selected_score - best_other_score),
                    ),
                    scores=profile_scores,
                )

        should_score_lot_sold = (
            candidate_set is None or ScreenName.S4_LOT_SOLD in candidate_set
        )
        if should_score_lot_sold:
            lot_sold_score = self._score_lot_sold_detail(image_bgr)
            profile_scores[ScreenName.S4_LOT_SOLD.value] = lot_sold_score
            profile_matches[ScreenName.S4_LOT_SOLD.value] = (
                lot_sold_score >= self._screen_threshold(ScreenName.S4_LOT_SOLD)
            )

            if lot_sold_score >= self._screen_threshold(ScreenName.S4_LOT_SOLD):
                best_other_score = max(
                    (
                        score
                        for screen, score in profile_scores.items()
                        if screen != ScreenName.S4_LOT_SOLD.value
                    ),
                    default=0.0,
                )
                return DetectionResult(
                    screen=ScreenName.S4_LOT_SOLD,
                    score=float(lot_sold_score),
                    threshold=self._screen_threshold(ScreenName.S4_LOT_SOLD),
                    margin=max(
                        self.config.detector.min_margin,
                        float(lot_sold_score - best_other_score),
                    ),
                    scores=profile_scores,
                )

        should_score_sold = (
            candidate_set is None or ScreenName.S3C_LIST_SOLD in candidate_set
        )
        if should_score_sold:
            sold_score = self._score_sold_badge(image_bgr)
            list_score = profile_scores.get(ScreenName.S3A_LIST_PRESENT.value, 0.0)
            profile_scores[ScreenName.S3C_LIST_SOLD.value] = sold_score
            profile_matches[ScreenName.S3C_LIST_SOLD.value] = (
                sold_score >= self._screen_threshold(ScreenName.S3C_LIST_SOLD)
                and list_score >= 0.70
            )

            if sold_score >= self._screen_threshold(ScreenName.S3C_LIST_SOLD):
                if list_score >= 0.70:
                    return DetectionResult(
                        screen=ScreenName.S3C_LIST_SOLD,
                        score=float(sold_score),
                        threshold=self._screen_threshold(ScreenName.S3C_LIST_SOLD),
                        margin=max(
                            self.config.detector.min_margin,
                            float(sold_score - list_score),
                        ),
                        scores=profile_scores,
                    )

        if not profile_scores:
            return DetectionResult(
                screen=ScreenName.UNKNOWN,
                score=0.0,
                threshold=self.config.detector.match_threshold,
                margin=0.0,
                scores=profile_scores,
            )

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
