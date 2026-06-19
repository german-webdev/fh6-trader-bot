from __future__ import annotations

from enum import Enum


class ScreenName(str, Enum):
    S1_SEARCH_MENU = "s1_search_menu"
    S2_SEARCH_CONFIRM = "s2_search_confirm"
    S3A_LIST_PRESENT = "s3a_list_present"
    S3_LIST_LOADING = "s3_list_loading"
    S3B_LIST_EMPTY = "s3b_list_empty"
    S3C_LIST_SOLD = "s3c_list_sold"
    S4_LOT_LOADING = "s4_lot_loading"
    S4_LOT_DETAILS = "s4_lot_details"
    S4_BUYOUT_SELECTED = "s4_buyout_selected"
    S4_LOT_SOLD = "s4_lot_sold"
    S5_BUY_CONFIRM = "s5_buy_confirm"
    S6_LOADER = "s6_loader"
    S7_BUY_SUCCESS = "s7_buy_success"
    S8_FINAL_SUCCESS = "s8_final_success"
    UNKNOWN = "unknown"
