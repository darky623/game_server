from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from chat.schemas import ChatSchema


class ClanSchemaBase(BaseModel):
    name: str = Field(..., max_length=25)
    short_name: str = Field(..., max_length=3)
    avatar: str = Field(...)
    rang: int = 1
    is_public: bool = True
    is_ghost: bool = False
    description: Optional[str] = None


class SubscribeToClanSchemaBase(BaseModel):
    role: str = Field(..., enum=['Head',
                                 'Deputy',
                                 'Elder',
                                 'Officer',
                                 'Participant'])
    status: bool = False


class SubscribeToClanSchemaCreate(SubscribeToClanSchemaBase):
    user_id: int = Field(...)
    clan_id: int = Field(...)


class SubscribeToClanSchema(SubscribeToClanSchemaBase):
    id: int
    user_id: int
    clan_id: int
    date_create: datetime = None


class SubscribeToClanSchemaUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[bool] = None


class RequestToClanSchemaBase(BaseModel):
    status: bool = False


class RequestToClanSchemaCreate(RequestToClanSchemaBase):
    user_id: int = Field(...)
    clan_id: int = Field(...)


class RequestToClanSchema(RequestToClanSchemaBase):
    id: int
    user_id: int
    clan_id: int
    date_create: datetime


class RequestToClanSchemaUpdate(BaseModel):
    status: Optional[bool] = None


class ClanSchemaCreate(ClanSchemaBase):
    pass


class ClanSchema(ClanSchemaBase):
    id: int
    name: str = Field(..., min_length=3, max_length=20)
    short_name: Optional[str] = None
    avatar: Optional[str] = None
    description: str = Field(..., max_length=200)
    created_at: datetime
    chat: Optional[ChatSchema] = None
    subscribers: Optional[list[SubscribeToClanSchema]] = None
    requests: Optional[list[RequestToClanSchema]] = None


class ClanSchemaUpdate(BaseModel):

    rang: Optional[int] = None
    is_public: Optional[bool] = True
    is_ghost: Optional[bool] = False
