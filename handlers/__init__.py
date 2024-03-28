from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text

import handlers.default as h
import handlers.admin as h_admin

from db.buttons import get_button_text
from states import AddTaskStates, PayoutStates, AddGiftStates, MassSendStates, AddSessionState


def setup_handlers(dp: Dispatcher):

    dp.register_callback_query_handler(h.add_account_step1_command, lambda c: c.data == 'connect_account', state='*')
    dp.register_message_handler(h.add_account_step2_command, state=[AddSessionState.STATE_WAIT_PHONE], content_types=['contact'])
    dp.register_callback_query_handler(h.retry_connection_query, lambda c: c.data.startswith('retry_'),state=[AddSessionState.STATE_WAIT_PHONE])
    dp.register_callback_query_handler(h.add_account_step3_command, lambda c: c.data.startswith('acc_dial_'),state=[AddSessionState.STATE_WAIT_AUTH_CODE])
    dp.register_message_handler(h.add_account_step4_command, state=[AddSessionState.STATE_WAIT_2FA])
    # dp.register_message_handler(h.start_command, commands=['test'], state='*')

    dp.register_message_handler(h.start_command, commands=['start'], state='*') 
    dp.register_message_handler(h.work_command, Text(get_button_text('button_start_work'))) 
    dp.register_message_handler(h.referral_command, Text(get_button_text('button_start_ref')))
    dp.register_message_handler(h.balance_command, Text(get_button_text('button_start_balance')))
    dp.register_message_handler(h.gift_command, Text(get_button_text('button_start_gift')))
    dp.register_message_handler(h.payment_system_command, state=[PayoutStates.STATE_BANK_DETAILS, PayoutStates.STATE_PAYOUT_COST])
    dp.register_callback_query_handler(h.check_main_subscribe, lambda c: c.data == 'check_main_subscribe')
    dp.register_callback_query_handler(h.work_action_subscribe, Text(startswith="task_"))
    dp.register_callback_query_handler(h.payout, Text('payout'))
    dp.register_callback_query_handler(h.payment_system, Text('payment_system'))
    dp.register_callback_query_handler(h.send_next_gift_command, Text('next_gift'))
    dp.register_callback_query_handler(h.next_work_command, Text('next_task'))

    dp.register_message_handler(h_admin.admin_info_command, Text(get_button_text("button_admin_start"))) 
    dp.register_message_handler(h_admin.add_admin_command, commands=['add_admin'])
    dp.register_message_handler(h_admin.add_task_command, commands=['add_task'])
    dp.register_message_handler(h_admin.add_task_command, state=[AddTaskStates.STATE_TITLE, AddTaskStates.STATE_TEXT, AddTaskStates.STATE_LINK, AddTaskStates.STATE_TG_ID, AddTaskStates.STATE_COST])
    dp.register_message_handler(h_admin.add_task_command, lambda x: x.text.isdigit(), state=AddTaskStates.STATE_COST)
    dp.register_message_handler(h_admin.delete_task_command, commands=['delete_task'])
    dp.register_message_handler(h_admin.change_cost_ref1_command, commands=['cost_ref1'])
    dp.register_message_handler(h_admin.change_cost_ref2_command, commands=['cost_ref2'])
    dp.register_message_handler(h_admin.change_min_payment_command, commands=['min_payment'])
    dp.register_message_handler(h_admin.change_min_referal_command, commands=['min_referal'])
    dp.register_message_handler(h_admin.get_balance_all_users_command, commands=['stat_payment'])
    dp.register_message_handler(h_admin.add_gift_command, commands=['add_gift'])
    dp.register_message_handler(h_admin.add_gift_process_command, content_types=['photo', 'text'] , state=[AddGiftStates.STATE_GIFT_POST, AddGiftStates.STATE_GIFT_BUTTONS])
    dp.register_message_handler(h_admin.add_partners_command, commands=['add_partners'])
    dp.register_message_handler(h_admin.stats_partners_command, commands=['stats_partners'])
    dp.register_message_handler(h_admin.stats_command, commands=['stats'])
    dp.register_message_handler(h_admin.mass_send_command, commands=['mass_send'])
    dp.register_message_handler(h_admin.mass_send_process_command, content_types=['photo', 'text'] , state=[MassSendStates.STATE_SEND_BUTTONS, MassSendStates.STATE_SEND_POST])
    dp.register_callback_query_handler(h_admin.confirm_delete_task_command, lambda c: 'delete_task_' in c.data)
