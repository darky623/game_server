from datetime import datetime

from pydantic import BaseModel, Field

from config import game_settings


class EnergyBase(BaseModel):
    user_id: int = Field(..., description="ID пользователя")


class EnergySchema(EnergyBase):
    id: int  # для обновления существующих записей
    amount: int = Field(..., ge=game_settings.energy["energy_min"],
                        le=game_settings.energy["energy_max"],
                        description="Количество энергии")
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Время последнего обновления"
    )
    next_update: datetime | None = Field(
        default_factory=lambda: datetime.now() + game_settings.time_add_one_energy,
        description="Время следующего обновления"
    )

    class Config:
        from_attributes = True
