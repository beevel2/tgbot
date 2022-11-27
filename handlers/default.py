import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext

import db.database as db
import db.models as models

import keyboards as kb
from settings import bot
import utils
from states import PayoutStates

from datetime import datetime
from random import randint


async def start_command(message: types.Message, is_admin: bool):
    if is_admin:
        text = await db.get_message('message_start')
        await message.answer(text, reply_markup=kb.kb_admin_start)
        return
    ref = message.text.split()
    if len(ref) == 2 and ref[-1].isdigit():
        ref = int(ref[-1])
    else:
        ref = None
    user_in_db = await db.get_user_by_tg_id(message.from_user.id)
    if user_in_db is None:
        user = models.UserModel(
            first_name=message.from_user.first_name or '',
            last_name=message.from_user.last_name or '',
            username=message.from_user.username or '',
            tg_id=message.from_user.id,
            refer_id=ref if ref and ref > 10000 else None
        )
        await db.create_user(user)
    if ref and ref < 10000:
        await db.add_partner_visit(ref)
    elif ref and ref != message.from_user.id:
        refs = await db.write_refs(message.from_user.id, ref)
        text1 = await db.get_message("message_ref1")
        text2 = await db.get_message("message_ref2")
        cost_ref1 = await db.get_setting("cost_ref1")
        cost_ref2 = await db.get_setting("cost_ref2")

        await db.update_balance(ref, cost_ref1)
        _user = await db.get_user_by_tg_id(ref)
        text_send = utils.replace_in_message(text1, 'COST_REF1', cost_ref1)
        text_send = utils.replace_in_message(text_send, 'COUNT_REFERRAL', len(_user['referral_id']))
        text_send = utils.replace_in_message(text_send, 'BALANCE', _user['balance'])
        await bot.send_message(ref, text_send)

        for _ref in refs:
            await db.update_balance(_ref, cost_ref2)
            _user = await db.get_user_by_tg_id(_ref)
            text_send = utils.replace_in_message(text2, 'COST_REF2', cost_ref2)
            text_send = utils.replace_in_message(text_send, 'COUNT_REFERRAL', len(_user['referral2_id']))
            text_send = utils.replace_in_message(text_send, 'BALANCE', _user['balance'])
            await bot.send_message(ref, text_send)

    text = await db.get_message('message_start')
    await message.answer(text, reply_markup=kb.kb_start)


async def check_main_subscribe(callback_query: types.CallbackQuery):
    link = await db.get_setting("main_public_link")
    check = await utils.check_user_subscribe(link, callback_query.message.chat.id)
    if check:
        text = await db.get_message('message_check_subscribe_success')
        await bot.send_message(callback_query.message.chat.id, text)
        await db.set_user_is_subscribe(callback_query.message.chat.id)
    else:
        text = await db.get_message('message_check_subscribe_error')
        await bot.send_message(callback_query.message.chat.id, text)
        await send_error_main_subscribe(
            callback_query.message.chat.id,
            callback_query.message.chat.full_name,
            callback_query.message.chat.first_name,
            callback_query.message.chat.last_name
        )


async def send_error_main_subscribe(tg_id, full_name, first_name, last_name):
    text = await db.get_message('message_start_check_subscribe')
    if full_name:
        name = full_name
    elif first_name:
        first_name
    elif last_name:
        name = last_name
    else:
        name = await db.get_message('message_username')
    chat_id = await db.get_setting('main_public_link')
    text = utils.replace_in_message(text, 'USER', name)
    text = utils.replace_in_message(text, 'LINK', chat_id)
    link = f"t.me/{chat_id.split('@')[-1]}"
    await bot.send_message(
        tg_id, text, reply_markup=kb.kb_first_message(link)
    )


async def send_work_task(tg_id: int):
    tasks = await db.get_active_tasks()
    user = await db.get_user_by_tg_id(tg_id)
    free_task = list(set(tasks) - set(user['tasks']) - set(user['rejected_tasks']))
    free_reject_task = user['rejected_tasks']
    if len(free_task) > 0:
        task_id = free_task[0]
    elif len(free_reject_task) > 0:
        task_id = free_reject_task[0]
        await db.remove_task_from_reject(tg_id, task_id)
    else:
        text = await db.get_message('message_tasks_finished')
        await bot.send_message(tg_id, text)
        return
    task = await db.get_task(task_id)
    text = f"{task['title']}\n{task['text']}"
    await bot.send_message(
        tg_id, text, reply_markup=kb.kb_check_task(task_id, task['link']),
        parse_mode=types.ParseMode.HTML
    )


async def work_command(message: types.Message, is_admin: bool):
    if is_admin:
        return
    await send_work_task(message.from_user.id)


async def work_action_subscribe(callback_query: types.CallbackQuery):
    _, operator, task_id = callback_query.data.split('_')
    await bot.edit_message_reply_markup(
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=None
    )
    if operator == 'check':
        task = await db.get_task(task_id)
        check = await utils.check_user_subscribe(task['tg_id'], callback_query.message.chat.id)
        if check:
            await db.update_balance(callback_query.message.chat.id, task['cost'])
            await db.complite_task(callback_query.message.chat.id, task_id)
            text = await db.get_message('message_tasks_success')
            user = await db.get_user_by_tg_id(callback_query.message.chat.id)
            text = utils.replace_in_message(text, 'COST', task['cost'])
            text = utils.replace_in_message(text, 'BALANCE', user['balance'])
            await bot.send_message(callback_query.message.chat.id, text, reply_markup=kb.kb_next_task)
        else:
            text = await db.get_message('message_tasks_error')
            await bot.send_message(callback_query.message.chat.id, text)
            await send_work_task(callback_query.message.chat.id)
    elif operator == 'skip':
        await db.reject_task(callback_query.message.chat.id, task_id)
        await send_work_task(callback_query.message.chat.id)


async def next_work_command(callback_query: types.CallbackQuery):
    await send_work_task(callback_query.message.chat.id)


async def referral_command(message: types.Message, is_admin: bool):
    if is_admin:
        return
    cost_ref1 = await db.get_setting('cost_ref1')
    cost_ref2 = await db.get_setting('cost_ref2')
    text = await db.get_message('message_referral_main')
    text = utils.replace_in_message(text, 'COST_REF1', cost_ref1)
    text = utils.replace_in_message(text, 'COST_REF2', cost_ref2)
    me = await bot.get_me()
    link_me = f"https://t.me/{me.username}?start={message.from_user.id}"
    text = utils.replace_in_message(text, 'LINK_ME', link_me)
    await message.answer(text)


async def balance_command(message: types.Message, is_admin: bool):
    if is_admin:
        return
    refs = await db.get_count_referals(message.from_user.id)
    text = await db.get_message('message_balance')
    user = await db.get_user_by_tg_id(message.from_user.id)
    text = utils.replace_in_message(text, 'BALANCE', user['balance'])
    text = utils.replace_in_message(text, 'COUNT_REFERRAL', refs['refs1'])
    text = utils.replace_in_message(text, 'COUNT_REFERRAL2', refs['refs2'])
    await message.answer(text, reply_markup=kb.kb_payout)


async def payout(callback_query: types.CallbackQuery):
    await bot.edit_message_reply_markup(
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=None
    )
    user = await db.get_user_by_tg_id(callback_query.from_user.id)
    min_payment = await db.get_setting('min_payment')
    min_referal = await db.get_setting('min_referal')
    if user['balance'] < min_payment:
        text = await db.get_message("message_payment_error_balance")
        text = utils.replace_in_message(text, "BALANCE", user['balance'])
        text = utils.replace_in_message(text, "MIN_PAYMENT", min_payment)
        await bot.send_message(callback_query.message.chat.id, text)
    elif len(user['referral_id']) < min_referal:
        text = await db.get_message("message_payment_error_referal")
        text = utils.replace_in_message(text, "MIN_REFERAL", min_referal)
        await bot.send_message(callback_query.message.chat.id, text)
    else:
        text = await db.get_message("message_check_payment_system")
        await bot.send_message(callback_query.message.chat.id, text, reply_markup=kb.kb_payment_system)


async def payment_system(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_reply_markup(
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=None
    )
    await state.set_state(PayoutStates.STATE_BANK_DETAILS)
    text = await db.get_message("message_bank_details")
    await bot.send_message(callback_query.message.chat.id, text)


async def payment_system_command(message: types.Message, state: FSMContext, is_admin: bool):
    if is_admin:
        return
    _state = await state.get_state()
    if _state == PayoutStates.STATE_BANK_DETAILS:
        await state.set_state(PayoutStates.STATE_PAYOUT_COST)
        text = await db.get_message("message_payout_cost")
        await bot.send_message(message.chat.id, text)
    elif _state == PayoutStates.STATE_PAYOUT_COST:
        mes = message.text
        if mes.isdigit():
            mes = int(mes)
            user = await db.get_user_by_tg_id(message.from_user.id)
            min_payment = await db.get_setting('min_payment')
            if mes < min_payment or mes > user['balance']:
                text = await db.get_message("message_payout_error")
                await bot.send_message(message.chat.id, text)
            else:
                await state.reset_state()
                num = await db.get_new_payout_request_id(message.from_user.id)
                text = await db.get_message("message_payout_success_create")
                text = utils.replace_in_message(text, "NUM", num)
                await bot.send_message(message.chat.id, text)
                await asyncio.sleep(60*60)
                text = await db.get_message("message_payout_success")
                text = utils.replace_in_message(text, "NUM", num)
                await bot.send_message(message.chat.id, text)
    

async def gift_command(message: types.Message, is_admin: bool):
    if is_admin:
        return
    user = await db.get_user_by_tg_id(message.from_user.id)
    date = datetime.now()
    if (user['date_gift'] is None) or ((date-user['date_gift']).days >= 1):
        text = await db.get_message('message_gift')
        min_cost = await db.get_setting('min_gift_cost')
        max_cost = await db.get_setting('max_gift_cost')
        cost = randint(min_cost, max_cost)
        await db.update_balance(message.from_user.id, cost)
        await db.update_user_date_gift(message.from_user.id, date)
        text = utils.replace_in_message(text, 'SUM', cost)
        await message.answer(text, reply_markup=kb.kb_next_gift())
    else:
        await send_next_gift(message.from_user.id)
    

async def send_next_gift(tg_id):
    gift = await db.get_next_gift(tg_id)
    if not gift: return
    await bot.send_photo(
        tg_id, 
        gift['photo_id'], 
        caption=gift['text'],
        parse_mode=types.ParseMode.HTML,
        reply_markup=kb.kb_next_gift(gift['buttons']))


async def send_next_gift_command(callback_query: types.CallbackQuery):
    await send_next_gift(callback_query.message.chat.id)
