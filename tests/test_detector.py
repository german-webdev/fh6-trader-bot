from __future__ import annotations

from pathlib import Path
import unittest

from PIL import Image

from bot.config import load_config
from bot.detector import ScreenDetector
from bot.screens import ScreenName


EXPECTED_REFERENCE_SCREENS = (
    ScreenName.S1_SEARCH_MENU,
    ScreenName.S2_SEARCH_CONFIRM,
    ScreenName.S3A_LIST_PRESENT,
    ScreenName.S3B_LIST_EMPTY,
    ScreenName.S4_LOT_DETAILS,
    ScreenName.S5_BUY_CONFIRM,
    ScreenName.S6_LOADER,
    ScreenName.S7_BUY_SUCCESS,
    ScreenName.S8_FINAL_SUCCESS,
)


class DetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config("config.toml")
        cls.detector = ScreenDetector(cls.config)
        cls.assets = sorted(Path("assets").glob("*.png"))
        cls.debug_frames = {
            path.name: path for path in Path("debug_frames").glob("unknown-*.png")
        }

    def _detect(self, path: Path, *, resize_to: tuple[int, int] | None = None):
        image = Image.open(path).convert("RGB")
        if resize_to is not None:
            image = image.resize(resize_to, Image.Resampling.BILINEAR)
        return self.detector.detect(image)

    def test_reference_assets_detect_expected_screens(self) -> None:
        for path, expected_screen in zip(self.assets, EXPECTED_REFERENCE_SCREENS):
            with self.subTest(screen=expected_screen.value):
                detection = self._detect(path)
                self.assertEqual(detection.screen, expected_screen)
                self.assertGreaterEqual(detection.score, detection.threshold)
                self.assertGreaterEqual(
                    detection.margin,
                    self.config.detector.min_margin,
                )

    def test_reference_assets_detect_expected_screens_at_1080p(self) -> None:
        for path, expected_screen in zip(self.assets, EXPECTED_REFERENCE_SCREENS):
            with self.subTest(screen=expected_screen.value):
                detection = self._detect(path, resize_to=(1920, 1080))
                self.assertEqual(detection.screen, expected_screen)
                self.assertGreaterEqual(detection.score, detection.threshold)

    def test_runtime_search_confirm_frame_stays_within_fast_remap_window(self) -> None:
        detection = self._detect(
            self.debug_frames["unknown-20260619-003421-525970.png"]
        )
        s2_score = detection.scores[ScreenName.S2_SEARCH_CONFIRM.value]
        best_score = max(detection.scores.values())

        self.assertGreaterEqual(s2_score, 0.72)
        self.assertLessEqual(best_score - s2_score, 0.08)


if __name__ == "__main__":
    unittest.main()
