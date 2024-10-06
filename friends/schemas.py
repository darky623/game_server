from fastapi import Depends
from pydantic import BaseModel

from auth.user_service import get_current_user


class FriendBase(BaseModel):
    owner_id: int
    friend_id: int | None = None
    chat_id: int | None = None
    request_to_add_id: int | None = None


class FriendCreate(FriendBase):
    pass


class FriendUpdate(FriendBase):
    pass


class RequestToFriendBase(BaseModel):

    sender_id: int | None = None
    recipient_id: int
    status: bool = False


class RequestToFriendCreate(RequestToFriendBase):
    pass


class RequestToFriendUpdate(RequestToFriendBase):
    id: int


class RequestToFriendDelete(RequestToFriendBase):
    pass
