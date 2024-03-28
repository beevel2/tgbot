import os
from pathlib import Path

from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from motor.motor_asyncio import (AsyncIOMotorClient, AsyncIOMotorDatabase)


TOKEN=''

MONGO_DB = ''
MONGO_URI = f''


COLLECTION_ACCOUNT = 'accounts'
COLLECTION_USER = 'users'
COLLECTION_ADMIN = 'admins'
COLLECTION_MESSAGES = 'messages'
COLLECTION_BUTTONS = 'buttons'
COLLECTION_SETTINGS = 'settings'
COLLECTION_TASKS = 'tasks'
COLLECTION_GIFTS = 'gifts'
COLLECTION_PARTNERS = 'partners'


API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
DEVICE_MODEL = 'PC 64bit'
SYSTEM_VERSION = 'Windows 7'
APP_VERSION = '1.9.1'
LANG_CODE = 'en'
SYSTEM_LANG_CODE = 'en-US'
LANG_PACK = 'tdesktop'

PYROGRAM_SESSION_PATH = Path(os.getcwd(), 'sessions')

if not os.path.exists(PYROGRAM_SESSION_PATH):
    os.makedirs(PYROGRAM_SESSION_PATH)


def _connect_to_db() -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    return db


db_connection = _connect_to_db()


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

