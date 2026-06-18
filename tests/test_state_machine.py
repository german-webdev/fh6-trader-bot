from __future__ import annotations

import unittest

from bot.screens import ScreenName
from bot.state_machine import AuctionStateMachine


class StateMachineTests(unittest.TestCase):
    def test_empty_list_returns_to_search(self) -> None:
        machine = AuctionStateMachine()
        decision = machine.handle(ScreenName.S3B_LIST_EMPTY)
        self.assertEqual(decision.actions, ("esc",))

    def test_lot_details_moves_to_buyout(self) -> None:
        machine = AuctionStateMachine()
        decision = machine.handle(ScreenName.S4_LOT_DETAILS)
        self.assertEqual(decision.actions, ("down", "enter"))

    def test_success_stops_on_final_screen(self) -> None:
        machine = AuctionStateMachine()
        decision = machine.handle(ScreenName.S8_FINAL_SUCCESS)
        self.assertTrue(decision.stop)

    def test_non_success_after_loader_recovers(self) -> None:
        machine = AuctionStateMachine()
        machine.handle(ScreenName.S5_BUY_CONFIRM)
        decision = machine.handle(ScreenName.S1_SEARCH_MENU)
        self.assertEqual(decision.actions, ("enter", "esc", "esc"))


if __name__ == "__main__":
    unittest.main()
