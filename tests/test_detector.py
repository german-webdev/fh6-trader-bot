from __future__ import annotations

from pathlib import Path
import unittest

from PIL import Image

from bot.config import load_config
from bot.detector import ScreenDetector, _pil_to_bgr
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
        cls.reference_dir = Path("bot/resources/reference")
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

    def test_runtime_search_menu_return_frame_stays_within_fast_remap_window(self) -> None:
        detection = self._detect(
            self.debug_frames["unknown-20260619-024900-099941.png"]
        )
        s1_score = detection.scores[ScreenName.S1_SEARCH_MENU.value]
        best_score = max(detection.scores.values())

        self.assertGreaterEqual(s1_score, 0.78)
        self.assertLessEqual(best_score - s1_score, 0.10)

    def test_runtime_single_lot_frame_stays_within_s3a_remap_window(self) -> None:
        screenshots_root = Path(r"C:\Users\musiq\OneDrive")
        screenshot_path = next(
            path for path in screenshots_root.rglob("*.png") if "030718" in path.name
        )
        detection = self._detect(screenshot_path)
        s3a_score = detection.scores[ScreenName.S3A_LIST_PRESENT.value]
        best_score = max(detection.scores.values())

        self.assertGreaterEqual(s3a_score, 0.82)
        self.assertLessEqual(best_score - s3a_score, 0.03)

    def test_runtime_empty_list_frame_stays_within_s3b_fast_path(self) -> None:
        screenshots_root = Path(r"C:\Users\musiq\OneDrive")
        screenshot_path = next(
            path for path in screenshots_root.rglob("*.png") if "052737" in path.name
        )
        detection = self._detect(screenshot_path)
        s3a_score = detection.scores[ScreenName.S3A_LIST_PRESENT.value]
        s3b_score = detection.scores[ScreenName.S3B_LIST_EMPTY.value]
        s7_score = detection.scores[ScreenName.S7_BUY_SUCCESS.value]

        self.assertEqual(detection.screen, ScreenName.S3B_LIST_EMPTY)
        self.assertGreaterEqual(s3b_score, 0.72)
        self.assertLess(s3a_score, 0.72)
        self.assertLess(s7_score, 0.90)

    def test_runtime_list_loading_frame_waits_for_lots(self) -> None:
        screenshots_root = Path(r"C:\Users\musiq\OneDrive")
        screenshot_path = next(
            path for path in screenshots_root.rglob("*.png") if "190016" in path.name
        )
        detection = self._detect(screenshot_path)

        self.assertEqual(detection.screen, ScreenName.S3_LIST_LOADING)
        self.assertGreaterEqual(
            detection.scores[ScreenName.S3_LIST_LOADING.value],
            self.detector._screen_threshold(ScreenName.S3_LIST_LOADING),
        )

    def test_lot_details_requires_ready_bid_panel(self) -> None:
        ready_image = Image.open(next(self.reference_dir.glob("4.*.png"))).convert("RGB")
        loading_image = Image.open(next(self.reference_dir.glob("4a*.png"))).convert("RGB")

        self.assertGreaterEqual(
            self.detector._score_lot_details_ready(_pil_to_bgr(ready_image)),
            0.80,
        )
        self.assertLess(
            self.detector._score_lot_details_ready(_pil_to_bgr(loading_image)),
            0.80,
        )

    def test_runtime_sold_lot_frame_detects_s3c(self) -> None:
        screenshots_root = Path(r"C:\Users\musiq\OneDrive")
        screenshot_path = next(
            path for path in screenshots_root.rglob("*.png") if "054647" in path.name
        )
        detection = self._detect(screenshot_path)

        self.assertEqual(detection.screen, ScreenName.S3C_LIST_SOLD)
        self.assertGreaterEqual(
            detection.scores[ScreenName.S3C_LIST_SOLD.value],
            self.detector._screen_threshold(ScreenName.S3C_LIST_SOLD),
        )

    def test_runtime_sold_lot_details_frame_recovers_to_search(self) -> None:
        screenshots_root = Path(r"C:\Users\musiq\OneDrive")
        screenshot_path = next(
            path for path in screenshots_root.rglob("*.png") if "032031" in path.name
        )
        detection = self._detect(screenshot_path)

        self.assertEqual(detection.screen, ScreenName.S4_LOT_SOLD)
        self.assertGreaterEqual(
            detection.scores[ScreenName.S4_LOT_SOLD.value],
            self.detector._screen_threshold(ScreenName.S4_LOT_SOLD),
        )

    def test_reference_lot_loading_frame_detects_expected_screen(self) -> None:
        detection = self._detect(self.reference_dir / "4a. Загрузка описания аукциона.png")
        self.assertEqual(detection.screen, ScreenName.S4_LOT_LOADING)
        self.assertGreaterEqual(detection.score, detection.threshold)

    def test_lot_open_phase_does_not_detect_loading_as_sold(self) -> None:
        image = Image.open(next(self.reference_dir.glob("4a*.png"))).convert("RGB")
        detection = self.detector.detect(
            image,
            candidates=(
                ScreenName.S4_LOT_LOADING,
                ScreenName.S4_LOT_DETAILS,
                ScreenName.S3C_LIST_SOLD,
            ),
        )

        self.assertEqual(detection.screen, ScreenName.S4_LOT_LOADING)
        self.assertNotEqual(detection.screen, ScreenName.S3C_LIST_SOLD)

    def test_runtime_transition_frame_does_not_remap_to_empty_or_sold(self) -> None:
        detection = self._detect(
            self.debug_frames["unknown-20260619-041247-420101.png"]
        )
        s3b_score = detection.scores[ScreenName.S3B_LIST_EMPTY.value]
        s3c_score = detection.scores[ScreenName.S3C_LIST_SOLD.value]

        self.assertLess(s3b_score, 0.85)
        self.assertLess(
            s3c_score,
            self.detector._screen_threshold(ScreenName.S3C_LIST_SOLD),
        )

    def test_regular_list_frame_does_not_trigger_sold_badge(self) -> None:
        image = Image.open(sorted(Path("assets").glob("*.png"))[2]).convert("RGB")
        score = self.detector._score_sold_badge(_pil_to_bgr(image))
        self.assertLess(score, 0.40)

    def test_sold_badge_scores_strongly_in_list_thumbnail_region(self) -> None:
        canvas = Image.new("RGB", (2048, 1152), (24, 24, 24))
        sold_source = Image.open(
            self.reference_dir / "sold_badge_source.png"
        ).convert("RGB")
        badge = sold_source.crop((24, 6, 252, 104))
        overlay = badge.resize((170, 82), Image.Resampling.BILINEAR)
        canvas.paste(overlay, (88, 184))

        score = self.detector._score_sold_badge(_pil_to_bgr(canvas))

        self.assertGreaterEqual(
            score,
            self.detector._screen_threshold(ScreenName.S3C_LIST_SOLD),
        )


if __name__ == "__main__":
    unittest.main()
