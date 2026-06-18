from __future__ import annotations

from dataclasses import dataclass

from bot.screens import ScreenName


@dataclass(slots=True)
class StepDecision:
    status: str
    message: str
    actions: tuple[str, ...] = ()
    stop: bool = False


class AuctionStateMachine:
    def __init__(self) -> None:
        self.previous_screen = ScreenName.UNKNOWN
        self.awaiting_purchase_result = False

    def handle(self, screen: ScreenName) -> StepDecision:
        if screen is ScreenName.S8_FINAL_SUCCESS:
            self.previous_screen = screen
            self.awaiting_purchase_result = False
            return StepDecision(
                status="success",
                message="Final success screen detected.",
                stop=True,
            )

        if self.awaiting_purchase_result and screen not in {
            ScreenName.S6_LOADER,
            ScreenName.S7_BUY_SUCCESS,
            ScreenName.S8_FINAL_SUCCESS,
            ScreenName.UNKNOWN,
        }:
            self.awaiting_purchase_result = False
            self.previous_screen = screen
            return StepDecision(
                status="recover",
                message="Buyout failed after loader, returning to search menu.",
                actions=("enter", "esc", "esc"),
            )

        if self.awaiting_purchase_result and screen is ScreenName.UNKNOWN:
            return StepDecision(
                status="wait",
                message="Unknown result after loader, retrying detection.",
            )

        if screen is ScreenName.S1_SEARCH_MENU:
            self.previous_screen = screen
            return StepDecision(
                status="advance",
                message="Search menu detected.",
                actions=("enter",),
            )

        if screen is ScreenName.S2_SEARCH_CONFIRM:
            self.previous_screen = screen
            return StepDecision(
                status="advance",
                message="Search confirmation detected.",
                actions=("enter",),
            )

        if screen is ScreenName.S3A_LIST_PRESENT:
            self.previous_screen = screen
            return StepDecision(
                status="advance",
                message="Auction list with lot detected.",
                actions=("enter",),
            )

        if screen is ScreenName.S3B_LIST_EMPTY:
            self.previous_screen = screen
            return StepDecision(
                status="advance",
                message="Empty auction list detected, returning to search menu.",
                actions=("esc",),
            )

        if screen is ScreenName.S4_LOT_DETAILS:
            self.previous_screen = screen
            return StepDecision(
                status="advance",
                message="Lot details detected, moving to buyout.",
                actions=("down", "enter"),
            )

        if screen is ScreenName.S5_BUY_CONFIRM:
            self.awaiting_purchase_result = True
            self.previous_screen = screen
            return StepDecision(
                status="advance",
                message="Buy confirmation detected.",
                actions=("enter",),
            )

        if screen is ScreenName.S6_LOADER:
            self.awaiting_purchase_result = True
            self.previous_screen = screen
            return StepDecision(
                status="wait",
                message="Loader detected, waiting for buyout result.",
            )

        if screen is ScreenName.S7_BUY_SUCCESS:
            self.previous_screen = screen
            return StepDecision(
                status="advance",
                message="Intermediate success dialog detected.",
                actions=("enter",),
            )

        return StepDecision(
            status="wait",
            message="Screen is unknown, waiting for a stable detection.",
        )
