from aiogram.utils.helper import Helper, HelperMode, Item


class AddTaskStates(Helper):
    mode = HelperMode.snake_case

    STATE_TITLE = Item()
    STATE_TEXT = Item()
    STATE_COST = Item()
    STATE_LINK = Item()
    STATE_TG_ID = Item()


class PayoutStates(Helper):
    mode = HelperMode.snake_case

    STATE_BANK_DETAILS = Item()
    STATE_PAYOUT_COST = Item()


class AddGiftStates(Helper):
    mode = HelperMode.snake_case

    STATE_GIFT_POST = Item()
    STATE_GIFT_BUTTONS = Item()


class MassSendStates(Helper):
    mode = HelperMode.snake_case

    STATE_SEND_POST = Item()
    STATE_SEND_BUTTONS = Item()