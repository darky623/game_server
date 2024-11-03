from datetime import datetime

from pydantic import BaseModel, Field

from config import game_settings


class EnergyBase(BaseModel):
    user_id: int = Field(..., description="ID пользователя")


class EnergySchema(EnergyBase):
    id: int  # для обновления существующих записей
    amount: int = Field(..., description="Количество энергии")
    last_updated: datetime = Field(..., description="Время последнего обновления")
    overmax: bool = Field(..., description="Признак переполнения энергии")

    class Config:
        from_attributes = True
