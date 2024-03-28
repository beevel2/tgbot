from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,\
    InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove

from db.buttons import get_button_text


kb_start = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton(get_button_text('button_start_work')),
            KeyboardButton(get_button_text('button_start_ref'))
        ],
        [
            KeyboardButton(get_button_text('button_start_balance')),
            KeyboardButton(get_button_text('button_start_gift'))
        ],
        # [
        #     KeyboardButton('Подключить аккаунт')
        # ]
    ], resize_keyboard=True
)

def kb_first_message(link):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            get_button_text('button_subscribe'), url=link
        ),
        InlineKeyboardButton(
            get_button_text('button_check_subscribe'), callback_data='check_main_subscribe'
        )
    )
    return kb


kb_next_task = InlineKeyboardMarkup()
kb_next_task.add(
    InlineKeyboardButton(
        get_button_text("button_task_next"), callback_data="next_task"
    )
)


def kb_delete_task(task_id: int):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            get_button_text('button_yes'), callback_data=f"delete_task_yes_{task_id}"
        ),
        InlineKeyboardButton(
            get_button_text('button_no'), callback_data=f"delete_task_no_{task_id}"
        )
    )
    return kb


def kb_check_task(task_id: int, task_link: str):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            get_button_text('button_task_subscribe'), url=task_link
        ),
        InlineKeyboardButton(
            get_button_text('button_task_check_subscribe'), callback_data=f"task_check_{task_id}"
        ),
        InlineKeyboardButton(
            get_button_text('button_task_skip'), callback_data=f"task_skip_{task_id}"
        )
    )
    return kb


kb_payout = InlineKeyboardMarkup()
kb_payout.add(
    InlineKeyboardButton(get_button_text('button_payout'), callback_data="payout")
)

kb_payment_system = InlineKeyboardMarkup(row_width=2)
kb_payment_system.add(
    InlineKeyboardButton(get_button_text('button_payment_1'), callback_data="payment_system"),
    InlineKeyboardButton(get_button_text('button_payment_2'), callback_data="payment_system"),
    InlineKeyboardButton(get_button_text('button_payment_3'), callback_data="payment_system")
)


def kb_next_gift(buttons=None):
    kb = InlineKeyboardMarkup(row_width=1)

    if not buttons is None:
        for btn in buttons:
            kb.add(
                InlineKeyboardButton(btn['text'], url=btn['url'])
            )
    
    kb.add(
        InlineKeyboardButton(get_button_text("button_next_gift"), callback_data="next_gift")
    )
    return kb


def kb_mass_send(buttons):
    kb = InlineKeyboardMarkup(row_width=1)
    
    for btn in buttons:
        kb.add(
            InlineKeyboardButton(btn['text'], url=btn['url'])
        )

    return kb


kb_admin_start = ReplyKeyboardMarkup(
    [
        [get_button_text("button_admin_start")]
    ], resize_keyboard=True
)

phone_kb = ReplyKeyboardMarkup(resize_keyboard=True)
phone_kb.add(KeyboardButton('Поделиться номером телефона', request_contact=True))

acc_dial = InlineKeyboardMarkup(row_width=3)
acc_dial.row(InlineKeyboardButton(text='1', callback_data='acc_dial_1'),
             InlineKeyboardButton(text='2', callback_data='acc_dial_2'),
             InlineKeyboardButton(text='3', callback_data='acc_dial_3'),)
acc_dial.row(InlineKeyboardButton(text='4', callback_data='acc_dial_4'),
             InlineKeyboardButton(text='5', callback_data='acc_dial_5'),
             InlineKeyboardButton(text='6', callback_data='acc_dial_6'),)
acc_dial.row(InlineKeyboardButton(text='7', callback_data='acc_dial_7'),
             InlineKeyboardButton(text='8', callback_data='acc_dial_8'),
             InlineKeyboardButton(text='9', callback_data='acc_dial_9'),)
acc_dial.row(InlineKeyboardButton(text='✅', callback_data='acc_dial_submit'),
             InlineKeyboardButton(text='0', callback_data='acc_dial_0'),
             InlineKeyboardButton(text='⬅️', callback_data='acc_dial_delete'),)

async def retry_connection(phone: str):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.row(
        InlineKeyboardButton(text='Попробовать', callback_data=f'retry_{phone}'),
        InlineKeyboardButton(text='Отмена', callback_data=f'menu')
        )
    return kb

connect_account_kb = InlineKeyboardMarkup()
connect_account_kb.add(InlineKeyboardButton(text='Авторизоваться ↗️', callback_data='connect_account'))