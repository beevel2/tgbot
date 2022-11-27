from datetime import datetime

from pydantic import BaseModel


class UserModel(BaseModel):
    first_name: str
    last_name: str
    username: str
    tg_id: int
    balance: int = 0
    date_registration: datetime = datetime.now()
    date_last_login: datetime = datetime.now()
    refer_id: int | None = None
    referral_id: list = []
    referral2_id: list = []
    tasks: list = []
    rejected_tasks: list = []
    date_gift: datetime | None = None
    gifts: list = []
    is_subscribe: bool = False
    payout_request_id: int = 0


class AdminModel(BaseModel):
    tg_id: int
    is_superadmin: bool = False


class TaskModel(BaseModel):
    title: str
    text: str
    cost: int
    link: str
    tg_id: int
    active: bool = True


class GiftModel(BaseModel):
    photo_id: str
    text: str
    buttons: list


class PartnerModel(BaseModel):
    partner_id: int
    visits: int = 0
