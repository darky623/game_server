from pydantic import BaseModel


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
    sender_id: int
    recipient_id: int
    status: bool = False


class RequestToFriendCreate(RequestToFriendBase):
    pass


class RequestToFriendUpdate(RequestToFriendBase):
    pass


class RequestToFriendDelete(RequestToFriendBase):
    pass
