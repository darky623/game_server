from datetime import datetime

from pydantic import BaseModel


class AddChatSchema(BaseModel):
    type: str
    user_ids: list[int]


class ChatSchema(AddChatSchema):
    id: int

    class Meta:
        orm_mode = True


class MessageSchema(BaseModel):
    id: int
    text: str
    chat_id: int
    user_id: int
    timestamp: datetime

    class Meta:
        orm_mode = True


