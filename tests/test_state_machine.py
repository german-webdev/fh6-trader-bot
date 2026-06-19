from __future__ import annotations

import unittest

from bot.screens import ScreenName
from bot.state_machine import AuctionStateMachine


class StateMachineTests(unittest.TestCase):
    def test_empty_list_returns_to_search(self) -> None:
        machine = AuctionStateMachine(fast_restart_search=True)
        decision = machine.handle(ScreenName.S3B_LIST_EMPTY)
        self.assertEqual(decision.actions, ("esc",))

    def test_lot_details_moves_to_buyout(self) -> None:
        machine = AuctionStateMachine()
        decision = machine.handle(ScreenName.S4_LOT_DETAILS)
        self.assertEqual(
            decision.actions,
            ("down", "wait_buyout_selection", "enter"),
        )

    def test_sold_lot_returns_to_search(self) -> None:
        machine = AuctionStateMachine(fast_restart_search=True)
        decision = machine.handle(ScreenName.S3C_LIST_SOLD)
        self.assertEqual(decision.actions, ("esc",))

    def test_sold_lot_after_buy_attempt_returns_to_search(self) -> None:
        machine = AuctionStateMachine(fast_restart_search=True)
        machine.awaiting_purchase_result = True
        decision = machine.handle(ScreenName.S3C_LIST_SOLD)
        self.assertEqual(decision.actions, ("esc",))
        self.assertFalse(machine.awaiting_purchase_result)

    def test_lot_loading_waits_for_details(self) -> None:
        machine = AuctionStateMachine()
        decision = machine.handle(ScreenName.S4_LOT_LOADING)
        self.assertEqual(decision.status, "wait")
        self.assertEqual(decision.actions, ())

    def test_success_stops_on_final_screen(self) -> None:
        machine = AuctionStateMachine()
        decision = machine.handle(ScreenName.S8_FINAL_SUCCESS)
        self.assertTrue(decision.stop)

    def test_success_dialog_confirms_and_stops(self) -> None:
        machine = AuctionStateMachine()
        machine.handle(ScreenName.S5_BUY_CONFIRM)
        decision = machine.handle(ScreenName.S7_BUY_SUCCESS)
        self.assertEqual(decision.actions, ())
        self.assertTrue(decision.stop)
        self.assertFalse(machine.awaiting_purchase_result)

    def test_buy_confirmation_can_repeat_while_waiting_for_result(self) -> None:
        machine = AuctionStateMachine()
        machine.awaiting_purchase_result = True
        decision = machine.handle(ScreenName.S5_BUY_CONFIRM)
        self.assertEqual(decision.actions, ("enter",))
        self.assertTrue(machine.awaiting_purchase_result)

    def test_non_success_after_loader_recovers(self) -> None:
        machine = AuctionStateMachine(fast_restart_search=True)
        machine.handle(ScreenName.S5_BUY_CONFIRM)
        decision = machine.handle(ScreenName.S1_SEARCH_MENU)
        self.assertEqual(
            decision.actions,
            ("enter", "esc", "esc", "enter", "enter"),
        )

    def test_search_menu_can_chain_into_saved_search(self) -> None:
        machine = AuctionStateMachine()
        decision = machine.handle(ScreenName.S1_SEARCH_MENU)
        self.assertEqual(decision.actions, ("enter",))


if __name__ == "__main__":
    unittest.main()
