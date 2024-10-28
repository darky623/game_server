from datetime import datetime

from pydantic import BaseModel, Field


class EnergyBase(BaseModel):
    user_id: int = Field(..., description="ID пользователя")


class EnergySchema(EnergyBase):
    id: int | None = None # для обновления существующих записей
    amount: float = Field(..., ge=0, le=100, description="Количество энергии")

    class Config:
        orm_mode = True


class EnergyUpdateSchema(EnergySchema):
    last_updated: datetime = Field(default_factory=datetime.now, description="Время последнего обновления")
