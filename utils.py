from settings import bot
import logging

logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def replace_in_message(message: str, s_from:str, s_to: str) -> str:
    return message.replace(f'<{s_from}>', str(s_to))


async def check_user_subscribe(chat_id: str, user_id: int) -> bool:
    print(chat_id, user_id)
    try:
        user_channel_status = await bot.get_chat_member(chat_id=str(chat_id), user_id=user_id)
    except Exception:
        return False
    if user_channel_status["status"] != 'left':
        return True
    else:
        return False
