from __future__ import annotations

from pathlib import Path
import unittest

from PIL import Image

from bot.config import load_config
from bot.detector import ScreenDetector
from bot.screens import ScreenName


EXPECTED = {
    "1. Поиск аукционов.png": ScreenName.S1_SEARCH_MENU,
    "2. Подтвердить поиск.png": ScreenName.S2_SEARCH_CONFIRM,
    "3-1. Лот присутствует.png": ScreenName.S3A_LIST_PRESENT,
    "3-2. Лот отсутствует.png": ScreenName.S3B_LIST_EMPTY,
    "4. Экран с выбраной кнопкой выкупа.png": ScreenName.S4_LOT_DETAILS,
    "5. Экран подтверждения.png": ScreenName.S5_BUY_CONFIRM,
    "6. Экран с лоадером.png": ScreenName.S6_LOADER,
    "7. Экран успешного выкупа.png": ScreenName.S7_BUY_SUCCESS,
    "8. Финальный экран.png": ScreenName.S8_FINAL_SUCCESS,
}


class DetectorTests(unittest.TestCase):
    def test_reference_images_match_expected_screens(self) -> None:
        detector = ScreenDetector(load_config("config.toml"))
        base_dir = Path("bot/resources/reference")

        for filename, expected in EXPECTED.items():
            with self.subTest(filename=filename):
                image = Image.open(base_dir / filename).convert("RGB")
                result = detector.detect(image)
                self.assertEqual(result.screen, expected)
                self.assertGreaterEqual(result.score, result.threshold)


if __name__ == "__main__":
    unittest.main()
