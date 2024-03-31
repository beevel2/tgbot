import asyncio
import os
import json
from pathlib import Path

from aiogram import types
from aiogram.dispatcher import FSMContext

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PasswordHashInvalidError

import db.database as db
import db.models as models

import keyboards as kb
from settings import bot
import utils
import settings
from utils import logger
from states import *

from datetime import datetime
from random import randint

clients_dicts = {}

async def start_command(message: types.Message, state: FSMContext, is_admin: bool):
    await state.finish()
    if is_admin:
        text = await db.get_message('message_start')
        await message.answer(text, reply_markup=kb.kb_admin_start)
        return
    ref = message.text.split()
    if len(ref) == 2 and ref[-1].isdigit():
        ref = int(ref[-1])
    else:
        ref = None
    print(f'REF_ID: {ref}')
    user_in_db = await db.get_user_by_tg_id(message.from_user.id)
    new_user = False
    if user_in_db is None:
        user = models.UserModel(
            first_name=message.from_user.first_name or '',
            last_name=message.from_user.last_name or '',
            username=message.from_user.username or '',
            tg_id=message.from_user.id,
            refer_id=ref if ref and ref > 10000 else None
        )
        await db.create_user(user)
        new_user = True
    if ref and ref < 10000:
        await db.add_partner_visit(ref)
    elif ref and ref != message.from_user.id and new_user:
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
            await bot.send_message(_ref, text_send)

    text = await db.get_message('message_start')
    await message.answer(text, reply_markup=kb.kb_start)


async def add_account_step1_command(
    query: types.CallbackQuery,
    state: FSMContext
):
    await query.answer()
    await state.set_state(AddSessionState.STATE_WAIT_PHONE)
    await query.message.delete()
    await bot.send_message(chat_id=query.from_user.id, text='Отправьте свой номер телефона, используя кнопку в меню ниже', reply_markup=kb.phone_kb)
async def add_account_step2_command(
    message: types.Message,
    state: FSMContext,
):

    await state.update_data(proxy=await db.fetch_proxy())

    state_data = await state.get_data()
    
    try:
        phone = message.contact.phone_number
    except AttributeError:
        await message.reply(text='Пожалуйста, отправьте ваш номер телефона, используя кнопку в меню ниже')
        return

    acc_in_db = await db.get_account_by_phone(phone)
    if acc_in_db:
        await message.answer(f'Аккаунт с номером {phone} - уже добавлен!')
        return

    session_path = os.path.join(settings.PYROGRAM_SESSION_PATH, datetime.today().strftime("%d.%m.%Y"))
    if not os.path.exists(session_path):
        os.makedirs(session_path)

    try:
        client = TelegramClient(
            os.path.join(session_path, f'client_{phone}.session'),
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            app_version=settings.APP_VERSION,
            device_model=settings.DEVICE_MODEL,
            system_version=settings.SYSTEM_VERSION,
            lang_code=settings.LANG_CODE,
            proxy=state_data['proxy'],
        )

        [status, _] = await asyncio.gather(
                                        asyncio.create_task(connect_acc(client, phone), name=f'connect_{phone}'),
                                        asyncio.create_task(cancel_connection(phone), name=f'cancel_{phone}')
            )

        if status == 1:
            await message.reply(text='При подключении возникла ошибка, скорее всего проблема в прокси(неправильно введены данные, либо прокси недоступен). Попробовать подключиться еще раз?',
                                reply_markup=await kb.retry_connection(phone))
            return
        sCode = await client.send_code_request(phone)

        await state.update_data(
            {
                'phone': phone,
                'phone_hash_code': sCode.phone_code_hash
            }
        )
        await state.set_state(AddSessionState.STATE_WAIT_AUTH_CODE)

        clients_dicts[message.from_user.id] = client

        await message.answer('Введите код для авторизации, используя клавиатуру под сообщением', reply_markup=kb.acc_dial)
        await state.update_data(dial_code='')
    except ConnectionError:
        await message.answer('Ошибка авторизации аккаунта из-за проблемы с подключением к прокси, проверьте данные, доступность прокси и попробуйте ещё раз')

    except Exception as e:
        logger.exception(msg='error while connectiong')
        await message.answer('Ошибка авторизации аккаунта, проверьте данные и попробуйте ещё раз. Если все данные верны, а ошибка остается - свяжитесь с администратором')
        await message.answer(f'Ошибка: {e}')

async def retry_connection_query(query: types.CallbackQuery, state: FSMContext):
    await query.answer(text='Повторяю попытку....')
    query.message.text = query.data.split('_')[-1]
    await add_account_step2_command(query.message, state, True)

async def connect_acc(client, phone):
    try:
        await client.connect()
        for task in asyncio.all_tasks():
            if task.get_name() == f'cancel_{phone}':
                task.cancel()
        return 0
    except asyncio.exceptions.CancelledError:
        return 1

async def cancel_connection(phone):
    try:
        await asyncio.sleep(60)
        for task in asyncio.all_tasks():
            if task.get_name() == f'connect_{phone}':
                task.cancel()
    except asyncio.exceptions.CancelledError:
        pass


async def add_account_step3_command(
    query: types.CallbackQuery,
    state: FSMContext,
):
    await query.answer()
    state_data = await state.get_data()
    if query.data.endswith('delete'):
        try:
            code = state_data['dial_code']
            code = code[:-1]
        except:
            logger.exception('a')
        finally:
            try:
                await state.update_data(dial_code=code)
                await query.message.edit_text(text='Код: ' + code, reply_markup=kb.acc_dial)
                return
            except:
                logger.exception('b')
                return
    elif not query.data.endswith('submit'):
        try:
            code = state_data['dial_code']
            code += query.data.split('_')[-1]
            await state.update_data(dial_code=code)    
            await query.message.edit_text(text='Код: ' + code, reply_markup=kb.acc_dial)
            return
        except:
            return
    else:
        await state.update_data({'code': state_data['dial_code']})

    try:
        state_data = await state.get_data()
        client = clients_dicts[query.from_user.id]
        try:
            print('BEFORE SING_IN')
            await client.sign_in(
                phone=state_data['phone'],
                phone_code_hash=state_data['phone_hash_code'],
                code=state_data['code']
            )
            print('BEFORE_2FA')
            
        except SessionPasswordNeededError:
            await bot.send_message(chat_id=query.from_user.id, text='Введить пароль 2FA')
            await state.set_state(AddSessionState.STATE_WAIT_2FA)
            return
        me = await client.get_me()
        session_path = os.path.join(settings.PYROGRAM_SESSION_PATH, datetime.today().strftime("%d.%m.%Y"))
        if not os.path.exists(session_path):
            os.makedirs(session_path)
        client_data = dict(app_id=settings.API_ID,
                           app_hash=settings.API_HASH,
                           sdk=settings.SYSTEM_VERSION,
                           device=settings.DEVICE_MODEL,
                           app_version=settings.APP_VERSION,
                           lang_pack=me.lang_code,
                           system_lang_pack=settings.LANG_CODE,
                           twoFA=None,
                           id=me.id,
                           phone=state_data['phone'],
                           username=me.username,
                           # date_of_birth=,
                           # date_of_birth_integrity=,
                           is_premium=me.premium ,
                           first_name=me.first_name,
                           last_name=me.last_name,
                           has_profile_pic=me.photo is not None,
                           spamblock="free",
                           session_file=f"client_{state_data['phone']}",)
        with open(os.path.join(session_path, f"client_{state_data['phone']}.json"), 'w') as file:
            json.dump(client_data, file, ensure_ascii=False, indent=2)
        try:
            await client.disconnect()
        except Exception:
            print('error disconnect')
        del clients_dicts[query.from_user.id]
        acc_id = await db.create_account(state_data['phone'], me.id, state_data['proxy'], query.from_user.id)
        await bot.send_message(chat_id=query.from_user.id, text=f'Аккаунт {state_data["phone"]} успешно авторизован.')
        await state.reset_data()
        await state.reset_state()
    except PasswordHashInvalidError as e:
        logger.exception(msg='error at sign_in')
        await bot.send_message(chat_id=query.from_user.id, text='Ошибка авторизации аккаунта, проверьте данные и попробуйте ещё раз. Если все данные верны, а ошибка остается - свяжитесь с администратором')
        await bot.send_message(chat_id=query.from_user.id, text=f'Введен неверный код авторизации,пожалуйста повторите ввод.')
    except Exception as e:
        logger.exception(msg='error at sign_in')
        await bot.send_message(chat_id=query.from_user.id, text='Ошибка авторизации аккаунта, проверьте данные и попробуйте ещё раз. Если все данные верны, а ошибка остается - свяжитесь с администратором')
        await bot.send_message(chat_id=query.from_user.id, text=f'Ошибка: {e}')
        await state.reset_data()
        await state.reset_state()


async def add_account_step4_command(
    message: types.Message,
    state: FSMContext
):

    try:
        state_data = await state.get_data()
        client = clients_dicts[message.from_user.id]
        await message.answer(f'Вы ввели {message.text}')
        await client.sign_in(
            password=message.text
        )
        me = await client.get_me()
        client_data = dict(app_id=settings.API_ID,
                   app_hash=settings.API_HASH,
                   sdk=settings.SYSTEM_VERSION,
                   device=settings.DEVICE_MODEL,
                   app_version=settings.APP_VERSION,
                   lang_pack=me.lang_code,
                   system_lang_pack=settings.LANG_CODE,
                   twoFA=message.text,
                   id=me.id,
                   phone=state_data['phone'],
                   username=me.username,
                   # date_of_birth=,
                   # date_of_birth_integrity=,
                   is_premium=me.premium ,
                   first_name=me.first_name,
                   last_name=me.last_name,
                   has_profile_pic=me.photo is not None,
                   spamblock="free",
                   session_file=f"client_{state_data['phone']}",)
        session_path = os.path.join(settings.PYROGRAM_SESSION_PATH, datetime.today().strftime("%d.%m.%Y"))
        if not os.path.exists(session_path):
            os.makedirs(session_path)
        with open(os.path.join(session_path, f"client_{state_data['phone']}.json"), 'w') as file:
            json.dump(client_data, file, ensure_ascii=False, indent=2)
        try:
            await client.disconnect()
        except Exception:
            print('error disconnect')
        del clients_dicts[message.from_user.id]
        acc_id = await db.create_account(state_data['phone'], me.id, state_data['proxy'], message.from_user.id)
        await message.answer(f'Аккаунт {state_data["phone"]} успешно авторизован.')
        await state.reset_data()
        await state.reset_state()
    except PasswordHashInvalidError as e:
        logger.exception(msg='error at sign_in 2fa')
        await message.answer('Ошибка авторизации аккаунта, проверьте данные и попробуйте ещё раз. Если все данные верны, а ошибка остается - свяжитесь с администратором')
        await message.answer(f'Введен неверный код авторизации,пожалуйста повторите ввод.')
    except Exception as e:
        logger.exception(msg='error at sign_in 2fa')
        await message.answer('Ошибка авторизации аккаунта, проверьте данные и попробуйте ещё раз. Если все данные верны, а ошибка остается - свяжитесь с администратором')
        await message.answer(f'Ошибка: {e}')
        await state.reset_data()
        await state.reset_state()


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
    text = 'Для того чтобы пользоваться ботом необходимо авторизовать свой аккаунт телеграм'
    # await bot.send_message(
    #     tg_id, text, reply_markup=kb.kb_first_message(link)
    # )
    await bot.send_message(tg_id, text, reply_markup=kb.connect_account_kb)

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
    if len(user['referral_id']) < min_referal:
        text = await db.get_message("message_payment_error_referal")
        text = utils.replace_in_message(text, "MIN_REFERAL", min_referal)
        await bot.send_message(callback_query.message.chat.id, text)
    elif user['balance'] < min_payment:
        text = await db.get_message("message_payment_error_balance")
        text = utils.replace_in_message(text, "BALANCE", user['balance'])
        text = utils.replace_in_message(text, "MIN_PAYMENT", min_payment)
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
