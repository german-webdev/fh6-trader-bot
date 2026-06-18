from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import numpy as np
from PIL import Image

from bot.config import AppConfig
from bot.screens import ScreenName


Region = tuple[float, float, float, float]


@dataclass(slots=True)
class ScreenTemplate:
    screen: ScreenName
    filename: str
    regions: tuple[Region, ...]


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


TEMPLATES: tuple[ScreenTemplate, ...] = (
    ScreenTemplate(
        screen=ScreenName.S1_SEARCH_MENU,
        filename="1. Поиск аукционов.png",
        regions=((0.02, 0.10, 0.22, 0.29), (0.02, 0.50, 0.24, 0.76)),
    ),
    ScreenTemplate(
        screen=ScreenName.S2_SEARCH_CONFIRM,
        filename="2. Подтвердить поиск.png",
        regions=((0.20, 0.20, 0.80, 0.84),),
    ),
    ScreenTemplate(
        screen=ScreenName.S3A_LIST_PRESENT,
        filename="3-1. Лот присутствует.png",
        regions=((0.02, 0.11, 0.40, 0.36), (0.40, 0.10, 0.99, 0.92)),
    ),
    ScreenTemplate(
        screen=ScreenName.S3B_LIST_EMPTY,
        filename="3-2. Лот отсутствует.png",
        regions=((0.43, 0.27, 0.90, 0.68),),
    ),
    ScreenTemplate(
        screen=ScreenName.S4_LOT_DETAILS,
        filename="4. Экран с выбраной кнопкой выкупа.png",
        regions=((0.02, 0.11, 0.22, 0.59), (0.02, 0.74, 0.22, 0.92)),
    ),
    ScreenTemplate(
        screen=ScreenName.S5_BUY_CONFIRM,
        filename="5. Экран подтверждения.png",
        regions=((0.25, 0.30, 0.77, 0.72),),
    ),
    ScreenTemplate(
        screen=ScreenName.S6_LOADER,
        filename="6. Экран с лоадером.png",
        regions=((0.25, 0.31, 0.77, 0.71),),
    ),
    ScreenTemplate(
        screen=ScreenName.S7_BUY_SUCCESS,
        filename="7. Экран успешного выкупа.png",
        regions=((0.25, 0.31, 0.77, 0.71),),
    ),
    ScreenTemplate(
        screen=ScreenName.S8_FINAL_SUCCESS,
        filename="8. Финальный экран.png",
        regions=((0.02, 0.56, 0.22, 0.77), (0.02, 0.75, 0.22, 0.87)),
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


def _to_gray_array(image: Image.Image, size: tuple[int, int] = (320, 180)) -> np.ndarray:
    prepared = image.convert("L").resize(size, Image.Resampling.BILINEAR)
    return np.asarray(prepared, dtype=np.float32)


def _region_similarity(current: Image.Image, template: Image.Image, region: Region) -> float:
    current_arr = _to_gray_array(_crop_region(current, region))
    template_arr = _to_gray_array(_crop_region(template, region))
    diff = np.abs(current_arr - template_arr).mean()
    similarity = 1.0 - (diff / 255.0)
    return max(0.0, min(1.0, similarity))


class ScreenDetector:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        base_dir = _resource_dir()
        self.templates = {
            template.screen: Image.open(base_dir / template.filename).convert("RGB")
            for template in TEMPLATES
        }

    def _score_template(self, image: Image.Image, template: ScreenTemplate) -> float:
        reference = self.templates[template.screen]
        scores = [
            _region_similarity(image, reference, region)
            for region in template.regions
        ]
        return float(sum(scores) / len(scores))

    def detect(self, image: Image.Image) -> DetectionResult:
        template_scores = {
            template.screen.value: self._score_template(image, template)
            for template in TEMPLATES
        }
        ordered = sorted(template_scores.items(), key=lambda item: item[1], reverse=True)
        best_screen_value, best_score = ordered[0]
        second_best = ordered[1][1] if len(ordered) > 1 else 0.0
        margin = best_score - second_best

        best_screen = ScreenName(best_screen_value)
        threshold = (
            self.config.detector.loader_match_threshold
            if best_screen is ScreenName.S6_LOADER
            else self.config.detector.match_threshold
        )
        if best_score < threshold or margin < self.config.detector.min_margin:
            return DetectionResult(
                screen=ScreenName.UNKNOWN,
                score=best_score,
                threshold=threshold,
                margin=margin,
                scores=template_scores,
            )

        return DetectionResult(
            screen=best_screen,
            score=best_score,
            threshold=threshold,
            margin=margin,
            scores=template_scores,
        )
