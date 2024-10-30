from datetime import datetime

from pydantic import BaseModel, Field

from config import game_settings


class EnergyBase(BaseModel):
    user_id: int = Field(..., description="ID пользователя")


class EnergySchema(EnergyBase):
    id: int | None = None  # для обновления существующих записей
    amount: int = Field(..., ge=0, le=100, description="Количество энергии")
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Время последнего обновления"
    )
    next_update: datetime = Field(
        default_factory=lambda: datetime.now() + game_settings.time_add_one_energy,
        description="Время следующего обновления"
    )

    class Config:
        orm_mode = True
