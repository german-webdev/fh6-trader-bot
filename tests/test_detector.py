from __future__ import annotations

from pathlib import Path
import unittest

from PIL import Image

from bot.config import load_config
from bot.detector import ScreenDetector
from bot.screens import ScreenName


class DetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config("config.toml")
        cls.detector = ScreenDetector(cls.config)
        cls.assets = sorted(Path("assets").glob("*.png"))
        cls.debug_frames = {
            path.name: path for path in Path("debug_frames").glob("unknown-*.png")
        }

    def _detect(self, path: Path):
        image = Image.open(path).convert("RGB")
        return self.detector.detect(image)

    def test_reference_search_assets_detect_cleanly(self) -> None:
        expectations = {
            0: ScreenName.S1_SEARCH_MENU,
            1: ScreenName.S2_SEARCH_CONFIRM,
            2: ScreenName.S3A_LIST_PRESENT,
            3: ScreenName.S3B_LIST_EMPTY,
        }

        for index, expected_screen in expectations.items():
            with self.subTest(screen=expected_screen.value):
                detection = self._detect(self.assets[index])
                self.assertEqual(detection.screen, expected_screen)
                self.assertGreaterEqual(
                    detection.margin,
                    self.config.detector.min_margin,
                )

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
