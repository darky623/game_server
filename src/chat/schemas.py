from pydantic import BaseModel, validator


class AddChatSchema(BaseModel):
    type: str
    user_ids: list[int]


class ChatSchema(BaseModel):
    id: int
    type: str

    class Config:
        from_attributes = True
