from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

import db.database as db
from handlers.default import send_error_main_subscribe
from states import *
from settings import dp

class UserIsAdminMiddleware(BaseMiddleware):
    '''
    Проверяем, админ ли юзер
    '''

    def __init__(self):
        super(UserIsAdminMiddleware, self).__init__()
    
    async def on_process_message(self, message: types.Message, data: dict):
        data['is_admin'] = False
        data['is_superadmin'] = False
        admin = await db.get_admin_by_tg_id(message.from_user.id)
        if admin:
            data['is_admin'] = True
            data['is_superadmin'] = admin['is_superadmin']
        return


class UserSubscribeMiddleware(BaseMiddleware):
    '''
    Проверяем, подписывался ли юзер на новостной канал
    '''

    def __init__(self):
        super(UserSubscribeMiddleware, self).__init__()
    
    async def on_process_message(self, message: types.Message, data: dict):
        if not message.text: return
        if ('/start' in message.text) or (data['is_admin']):
            return
        # user = await db.get_user_by_tg_id(message.from_user.id)
        # if user['is_subscribe']:
            # return
        state = await dp.current_state(chat=message.chat.id, user=message.from_user.id).get_state()
        if state == AddSessionState.STATE_WAIT_2FA:
            return
        acc = await db.get_account_by_tg_id(message.from_user.id)
        if acc:
            return
        else:
            await send_error_main_subscribe(
                message.from_user.id,
                message.from_user.full_name,
                message.from_user.first_name,
                message.from_user.last_name
            )
            raise CancelHandler()


class SaveUserLastDateLoginMiddleware(BaseMiddleware):
    '''
    Записываем юзеру дату последнего логина
    '''

    def __init__(self):
        super(SaveUserLastDateLoginMiddleware, self).__init__()
    
    async def on_process_message(self, message: types.Message, data: dict):
        if not data['is_admin']:
            await db.update_user_date_last_login(message.from_user.id)
        return
