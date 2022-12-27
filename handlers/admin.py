import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext

import db.database as db
import db.models as models
from states import AddTaskStates, AddGiftStates, MassSendStates
from utils import replace_in_message
import keyboards as kb
from settings import bot


async def add_admin_command(
        message: types.Message,
        is_superadmin: bool
    ):
    if not is_superadmin:
        return
    if len(message.text.split()) == 2:
        if message.text.split()[-1].isdigit():
            await db.add_admin(models.AdminModel(
                tg_id=int(message.text.split()[-1])
            ))
        

async def delete_admin_command(
        message: types.Message,
        is_superadmin: bool
    ):
    if not is_superadmin:
        return
    if len(message.text.split()) == 2:
        if message.text.split()[-1].isdigit():
            await db.delete_admin(int(message.text.split()[-1]))


async def add_task_command(
        message: types.Message,
        state: FSMContext,
        is_admin: bool
    ):
    if not is_admin:
        return
    _state = await state.get_state()
    if _state is None:
        await message.answer(await db.get_message('message_admin_add_task_title'))
        await state.set_state(AddTaskStates.STATE_TITLE)
    elif _state == AddTaskStates.STATE_TITLE:
        await state.update_data({'task_title': message.html_text})
        await message.answer(await db.get_message('message_admin_add_task_text'))
        await state.set_state(AddTaskStates.STATE_TEXT)
    elif _state == AddTaskStates.STATE_TEXT:
        await state.update_data({'task_text': message.html_text})
        await message.answer(await db.get_message('message_admin_add_task_cost'))
        await state.set_state(AddTaskStates.STATE_COST)
    elif _state == AddTaskStates.STATE_COST:
        await state.update_data({'task_cost': message.text})
        await message.answer(await db.get_message('message_admin_add_task_link'))
        await state.set_state(AddTaskStates.STATE_LINK)
    elif _state == AddTaskStates.STATE_LINK:
        await state.update_data({'task_link': message.text})
        await message.answer(await db.get_message('message_admin_add_task_id'))
        await state.set_state(AddTaskStates.STATE_TG_ID)
    elif _state == AddTaskStates.STATE_TG_ID:
        _state_data = await state.get_data()
        task = models.TaskModel(
            title=_state_data['task_title'],
            text=_state_data['task_text'],
            cost=_state_data['task_cost'],
            link=_state_data['task_link'],
            tg_id=message.text
        )
        task_id = await db.create_task(task)
        text = replace_in_message(
            await db.get_message('message_admin_add_task_success'), 
            'TASK_ID',
            task_id
        )
        await message.answer(text)
        await state.reset_state()


async def delete_task_command(
        message: types.Message,
        is_admin: bool, 
        is_superadmin: bool
    ):
    if not is_admin:
        return
    commands = message.text.split()
    if len(commands) == 2 and commands[-1].isdigit():
        text = replace_in_message(
            await db.get_message('message_admin_delete_task'),
            'TASK_ID',
            commands[-1]
        )
        await message.answer(text, reply_markup=kb.kb_delete_task(commands[-1]))


async def confirm_delete_task_command(callback_query: types.CallbackQuery):
    commands = callback_query.data.split('_')
    task_id = commands[3]
    if commands[2] == 'yes':
        await db.delete_task(task_id)
        text = await db.get_message('message_admin_delete_task_success')
    elif commands[2] == 'no':
        text = await db.get_message('message_admin_delete_task_cancel')
    await bot.edit_message_reply_markup(
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=None
    )
    await bot.send_message(callback_query.message.chat.id, text)


async def change_cost_ref1_command(
        message: types.Message,
        is_admin: bool
    ):
    if not is_admin:
        return
    if message.text.split()[-1].isdigit():
        new_cost = int(message.text.split()[-1])
        text = await db.get_message('message_change_cost_ref_success')
        await db.change_setting('cost_ref1', new_cost)
        await message.answer(text)
    

async def change_cost_ref2_command(
        message: types.Message,
        is_admin: bool
    ):
    if not is_admin:
        return
    if message.text.split()[-1].isdigit():
        new_cost = int(message.text.split()[-1])
        text = await db.get_message('message_change_cost_ref_success')
        await db.change_setting('cost_ref2', new_cost)
        await message.answer(text)


async def change_min_payment_command(
        message: types.Message,
        is_admin: bool
    ):
    if not is_admin:
        return
    if message.text.split()[-1].isdigit():
        new_val = int(message.text.split()[-1])
        await db.change_setting('min_payment', new_val)
    

async def change_min_referal_command(
        message: types.Message,
        is_admin: bool
    ):
    if not is_admin:
        return
    if message.text.split()[-1].isdigit():
        new_val = int(message.text.split()[-1])
        await db.change_setting('min_referal', new_val)


async def get_balance_all_users_command(
        message: types.Message,
        is_admin: bool
    ):
    if not is_admin:
        return
    res = await db.get_balance_all_users()
    text = await db.get_message("message_balance_all_users")
    text = replace_in_message(text, 'SUM', res)
    await message.answer(text)


async def add_gift_command(
        message: types.Message,
        state: FSMContext,
        is_admin: bool
    ):
    if not is_admin:
        return
    text = await db.get_message('message_gift_add_post')
    await state.set_state(AddGiftStates.STATE_GIFT_POST)
    await message.answer(text)


async def add_gift_process_command(
        message: types.Message,
        state: FSMContext,
        is_admin: bool
    ):
    if not is_admin:
        return
    _state = await state.get_state()
    try:
        if _state == AddGiftStates.STATE_GIFT_POST:
            await state.set_data(
                {
                    "photo_id": message.photo[0].file_id,
                    "text": message.html_text
                }
            )
            text = await db.get_message("message_gift_add_buttons")
            await message.answer(text)
            await state.set_state(AddGiftStates.STATE_GIFT_BUTTONS)
        elif _state == AddGiftStates.STATE_GIFT_BUTTONS:
            _state_data = await state.get_data()
            buttons = []
            if message.text != '0':
                for s in message.text.split('\n'):
                    if len(s.split('-')) < 2: continue
                    _text = s.split('-')[0]
                    _url = '-'.join(s.split('-')[1:])
                    buttons.append({
                        "text": _text.strip(),
                        "url": _url.strip()
                    })
            await db.create_gift(models.GiftModel(
                photo_id=_state_data['photo_id'],
                text=_state_data["text"],
                buttons=buttons
            ))
            text = await db.get_message("message_gift_add_success")
            await message.answer(text)
            await state.reset_data()
            await state.reset_state()
    except Exception:
        await state.reset_data()
        await state.reset_state()


async def stats_command(
        message: types.Message,
        is_admin: bool
    ):
    if not is_admin:
        return
    days = -1
    if len(message.text.split()) == 2:
        if message.text.split()[-1].isdigit():
            days = int(message.text.split()[-1])
    text = await db.get_message("message_stats")
    data = await db.get_stats(days)
    text = replace_in_message(text, "USERS", data['count_users'])
    text = replace_in_message(text, "REF1", data['count_ref1'])
    text = replace_in_message(text, "REF2", data['count_ref2'])
    await message.answer(text)


async def add_partners_command(
        message: types.Message,
        is_admin: bool
    ):
    if not is_admin:
        return
    if len(message.text.split()) != 2:
        return
    if message.text.split()[-1].isdigit():
        partner_id = int(message.text.split()[-1])
        await db.create_partner(models.PartnerModel(
            partner_id=partner_id
        ))
        text = await db.get_message("message_partner_add")
        me = await bot.get_me()
        link = f"https://t.me/{me.username}?start={partner_id}"
        await message.answer(f"{text} {link}")


async def stats_partners_command(
        message: types.Message,
        is_admin: bool
    ):
    if not is_admin:
        return
    text = await db.get_message("message_stats_partner")
    partners = await db.get_all_partners()
    text_dict = []
    for p in partners:
        _text = replace_in_message(text, "PARTNER_ID", p['partner_id'])
        _text = replace_in_message(_text, "USERS_COUNT", p['visits'])
        text_dict.append(_text)
    text = '\n'.join(text_dict)
    if text:
        await message.answer(text)


async def mass_send_command(
        message: types.Message,
        state: FSMContext,
        is_admin: bool
    ):
    if not is_admin:
        return
    text = await db.get_message('message_gift_add_post')
    await state.set_state(MassSendStates.STATE_SEND_POST)
    await message.answer(text)


async def mass_send_process_command(
        message: types.Message,
        state: FSMContext,
        is_admin: bool
    ):
    if not is_admin:
        return
    _state = await state.get_state()
    success_send = 0
    try:
        if _state == MassSendStates.STATE_SEND_POST:
            await state.set_data(
                {
                    "photo_id": message.photo[0].file_id,
                    "text": message.html_text
                }
            )
            text = await db.get_message("message_mass_send_inline")
            await message.answer(text)
            await state.set_state(MassSendStates.STATE_SEND_BUTTONS)
        elif _state == MassSendStates.STATE_SEND_BUTTONS:
            _state_data = await state.get_data()
            buttons = []
            if message.text != '0':
                for s in message.text.split('\n'):
                    if len(s.split('-')) < 2: continue
                    _text = s.split('-')[0]
                    _url = '-'.join(s.split('-')[1:])
                    buttons.append({
                        "text": _text.strip(),
                        "url": _url.strip()
                    })
            
            user_ids = await db.get_id_all_users()
            for _user in user_ids:
                _kb = kb.kb_mass_send(buttons) if buttons else None
                try:
                    await bot.send_photo(
                        _user,
                        _state_data['photo_id'],
                        caption=_state_data['text'],
                        parse_mode=types.ParseMode.HTML,
                        reply_markup=_kb
                    )
                    await asyncio.sleep(0.5)
                    success_send += 1
                except Exception as e:
                    print(f"ERROR MASS SEND: {e}")
                
            text = await db.get_message("message_mass_send_success")
            await message.answer(text)

            await state.reset_data()
            await state.reset_state()
    except Exception as e:
        await state.reset_data()
        await state.reset_state()
        print(f"ERROR BIG MASS SEND: {e}")
    
    try:
        await message.answer(f"Успешно отправлено {success_send} из {len(user_ids)} сообщений")
    except Exception:
        await message.answer(f"Ошибка при выполнении рассылки")


async def admin_info_command(message: types.Message, is_admin: bool):
    if not is_admin:
        return
    text = await db.get_message("message_admin_start")
    await message.answer(text)

