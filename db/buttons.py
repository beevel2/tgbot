import asyncio

from settings import db_connection, COLLECTION_BUTTONS


def get_button_text(button_id):
    for btn in BUTTONS:
        if btn['_id'] == button_id:
            return btn['text']
    return ''


def load_buttons():
    async def _load():
        return await db_connection[COLLECTION_BUTTONS].find({}).to_list(999)
    task = asyncio.ensure_future(_load())
    return asyncio.get_event_loop().run_until_complete(task)


BUTTONS = load_buttons()