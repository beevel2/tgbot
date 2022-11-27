from datetime import datetime, timedelta

import pymongo

from settings import db_connection, COLLECTION_MESSAGES, \
    COLLECTION_USER, COLLECTION_BUTTONS, COLLECTION_ADMIN, COLLECTION_SETTINGS, \
    COLLECTION_TASKS, COLLECTION_GIFTS, COLLECTION_PARTNERS
import db.models as models


async def create_user(user: models.UserModel):
    col = db_connection[COLLECTION_USER]
    await col.insert_one(user.dict())


async def get_user_by_tg_id(tg_id: int):
    col = db_connection[COLLECTION_USER]
    return await col.find_one(filter={'tg_id': tg_id})


async def get_admin_by_tg_id(tg_id: int):
    col = db_connection[COLLECTION_ADMIN]
    return await col.find_one(filter={'tg_id': tg_id})


async def update_user_date_last_login(tg_id: int):
    col = db_connection[COLLECTION_USER]
    await col.find_one_and_update(
        {'tg_id': tg_id}, {'$set': {'date_last_login': datetime.now()}}
    )


async def set_user_is_subscribe(tg_id: int):
    col = db_connection[COLLECTION_USER]
    await col.find_one_and_update(
        {'tg_id': tg_id}, {'$set': {'is_subscribe': True}}
    )

async def get_message(msg_id: str):
    col = db_connection[COLLECTION_MESSAGES]
    res = await col.find_one(filter={'_id': msg_id})
    return res['text'].replace(r"\n", "\n") if res else ''


async def get_setting(setting_id):
    col = db_connection[COLLECTION_SETTINGS]
    res = await col.find_one(filter={'_id': setting_id})
    return res['value'] if res else ''


async def get_all_buttons():
    col = db_connection[COLLECTION_BUTTONS]
    return await col.find({}).to_list(9999)


async def create_task(task: models.TaskModel):
    col = db_connection[COLLECTION_TASKS]
    last_task = await col.find_one({}, sort=[('task_id', pymongo.DESCENDING)])
    if last_task:
        task_id = last_task['task_id'] + 1
    else:
        task_id = 1
    task = task.dict()
    task['task_id'] = task_id
    await col.insert_one(task)
    return task_id


async def delete_task(task_id: int):
    col = db_connection[COLLECTION_TASKS]
    await col.find_one_and_update(
        {'task_id': int(task_id)}, {'$set': {'active': False}}
    )


async def get_task(task_id: int):
    col = db_connection[COLLECTION_TASKS]
    return await col.find_one({'task_id': int(task_id)})


async def get_active_tasks():
    col = db_connection[COLLECTION_TASKS]
    return await col.find({"active": True}).distinct('task_id')


async def reject_task(user_id: int, task_id: int):
    col = db_connection[COLLECTION_USER]
    await col.find_one_and_update(
        {'tg_id': int(user_id)}, {"$push": {"rejected_tasks": int(task_id)}}
    )


async def complite_task(user_id: int, task_id: int):
    col = db_connection[COLLECTION_USER]
    await col.find_one_and_update(
        {'tg_id': int(user_id)}, {"$push": {"tasks": int(task_id)}}
    )


async def remove_task_from_reject(user_id: int, task_id: int):
    col = db_connection[COLLECTION_USER]
    await col.find_one_and_update(
        {'tg_id': int(user_id)}, {"$pull": {"rejected_tasks": int(task_id)}}
    )


async def update_balance(user_id: int, cost: int):
    col = db_connection[COLLECTION_USER]
    await col.find_one_and_update(
        {'tg_id': int(user_id)}, {"$inc": {"balance": int(cost)}}
    )


async def write_refs(tg_id: int, ref_id: int):
    col = db_connection[COLLECTION_USER]
    await col.find_one_and_update(
        {'tg_id': int(ref_id)}, {"$push": {"referral_id": int(tg_id)}}
    )
    ids = await col.find({'referral_id': {"$in" : [int(ref_id)]}}).distinct('tg_id')

    for _id in ids:
        await col.find_one_and_update(
            {'tg_id': _id}, {"$push": {"referral2_id": int(tg_id)}}
        )

    return ids


async def get_count_referals(tg_id: int):
    col = db_connection[COLLECTION_USER]
    refs1 = await col.find({'refer_id': int(tg_id)}).distinct('tg_id')
    print(refs1)
    refs2 = 0
    for ref in refs1:
        _refs2 = await col.find_one({'tg_id': ref})
        refs2 += len(_refs2['referral_id'])
    return {'refs1': len(refs1), 'refs2': refs2}


async def get_new_payout_request_id(tg_id: int):
    col = db_connection[COLLECTION_USER]
    user = await col.find_one_and_update(
        {'tg_id': int(tg_id)}, {"$inc": {"payout_request_id": 1}},
        return_document = pymongo.ReturnDocument.AFTER
    )
    return user['payout_request_id']


async def change_setting(setting_id: str, value):
    col = db_connection[COLLECTION_SETTINGS]
    await col.find_one_and_update(
        {'_id': setting_id}, {'$set': {'value': value}}
    )


async def get_balance_all_users():
    col = db_connection[COLLECTION_USER]
    cursor = col.find({})
    total_sum = sum([x['balance'] async for x in cursor])
    return total_sum


async def create_gift(gift: models.GiftModel):
    col = db_connection[COLLECTION_GIFTS]
    await col.insert_one(gift.dict())


async def update_user_date_gift(tg_id: int, date):
    col = db_connection[COLLECTION_USER]
    await col.find_one_and_update(
        {'tg_id': tg_id}, {'$set': {'date_gift': date}}
    )


async def get_next_gift(tg_id: int):
    user = await get_user_by_tg_id(tg_id)
    col = db_connection[COLLECTION_GIFTS]
    col_user = db_connection[COLLECTION_USER]
    gifts = await col.find({}).to_list(9999)
    for gift in gifts:
        if not gift['_id'] in user['gifts']:
            await col_user.find_one_and_update(
                {'tg_id': tg_id}, {"$push": {"gifts": gift['_id']}}
            )
            return gift
    
    await col_user.find_one_and_update(
        {'tg_id': tg_id}, {"$set": {"gifts": [gift['_id']]}}
    )
    return gift


async def get_stats(days=-1):
    col = db_connection[COLLECTION_USER]
    users = await col.find({}).to_list(9999)
    if days > 0:
        users = list(
            filter(lambda x: datetime.now() - timedelta(days=days) < x['date_registration'], users)
        )
    user_ids = [x['tg_id'] for x in users]
    print(user_ids)
    count_users = len(users)
    count_ref1 = set()
    count_ref2 = set()
    for u in users:
        for u1 in u['referral_id']:
            if u1 in user_ids:
                count_ref1.add(u1)
        for u2 in u['referral2_id']:
            if u2 in user_ids:
                count_ref2.add(u2)
    return {
        "count_users": count_users,
        "count_ref1": len(count_ref1),
        "count_ref2": len(count_ref2)
    }


async def create_partner(p: models.PartnerModel):
    col = db_connection[COLLECTION_PARTNERS]
    await col.insert_one(p.dict())


async def get_all_partners():
    col = db_connection[COLLECTION_PARTNERS]
    return await col.find({}).to_list(9999)


async def add_partner_visit(partner_id: int):
    col = db_connection[COLLECTION_PARTNERS]
    await col.find_one_and_update(
        {'partner_id': int(partner_id)}, {"$inc": {"visits": 1}}
    )


async def add_admin(admin: models.AdminModel):
    col = db_connection[COLLECTION_ADMIN]
    await col.insert_one(admin.dict())


async def delete_admin(admin_id: int):
    col = db_connection[COLLECTION_ADMIN]
    await col.delete_one({'tg_id': admin_id})


async def get_id_all_users():
    col = db_connection[COLLECTION_USER]
    users = await col.find({}).to_list(9999)
    return [x['tg_id'] for x in users]
