from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from motor.motor_asyncio import (AsyncIOMotorClient, AsyncIOMotorDatabase)


TOKEN=''

MONGO_DB = 'telegram-bot'
MONGO_URI = f'mongodb://'

COLLECTION_USER = 'users'
COLLECTION_ADMIN = 'admins'
COLLECTION_MESSAGES = 'messages'
COLLECTION_BUTTONS = 'buttons'
COLLECTION_SETTINGS = 'settings'
COLLECTION_TASKS = 'tasks'
COLLECTION_GIFTS = 'gifts'
COLLECTION_PARTNERS = 'partners'


def _connect_to_db() -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    return db


db_connection = _connect_to_db()


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())