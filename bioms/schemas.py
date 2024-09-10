from pydantic import BaseModel, Field
from typing import Optional


class BiomeBase(BaseModel):
    name: str = Field(..., max_length=25)
    description: Optional[str] = None
    difficulty_lvl: Optional[int] = Field(1, ge=1)
    reward_id: Optional[int] = None


class BiomeCreateSchema(BiomeBase):
    pass


class BiomeSchema(BiomeBase):
    id: int
    reward_id: Optional[int]

    class Config:
        orm_mode = True


class PlayerProgressBase(BaseModel):
    player: int
    biome_id: int
    biome_level_id: int
    difficult_lvl: Optional[int] = Field(1, ge=1)
    battles: Optional[int] = 0
    victories: Optional[int] = 0
    defeats: Optional[int] = 0
    current_difficulty_level: Optional[int] = Field(1, ge=1)


class PlayerProgressCreateSchema(PlayerProgressBase):
    pass


class PlayerProgressSchema(PlayerProgressBase):
    id: int

    class Config:
        orm_mode = True
