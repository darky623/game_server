from pydantic import BaseModel


class AddChatSchema(BaseModel):
    type: str
    user_ids: list[int]


class ChatSchema(AddChatSchema):
    id: int
