from __future__ import annotations

import unittest

from bot.config import load_config
from bot.runtime import BotRuntime


class RuntimeGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = BotRuntime(load_config("config.toml"))

    def test_success_score_can_beat_empty_list_side_score(self) -> None:
        self.assertFalse(
            self.runtime._search_list_beats_success(
                s3b_score=0.84,
                s3c_score=0.0,
                s7_score=0.90,
            )
        )

    def test_empty_list_score_still_rejects_false_success(self) -> None:
        self.assertTrue(
            self.runtime._search_list_beats_success(
                s3b_score=0.90,
                s3c_score=0.0,
                s7_score=0.82,
            )
        )


if __name__ == "__main__":
    unittest.main()
