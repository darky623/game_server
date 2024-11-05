from datetime import datetime

from pydantic import BaseModel, Field

from config import game_settings


class EnergyBase(BaseModel):
    user_id: int = Field(..., description="ID пользователя")


class EnergySchema(EnergyBase):
    id: int  # для обновления существующих записей
    amount: int
    last_updated: datetime
    overmax: bool

    class Config:
        from_attributes = True
