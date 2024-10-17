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
        from_attributes = True


class PlayerProgressBase(BaseModel):
    player_id: int
    biome_id: int | None = None
    biome_level_id: int | None = None
    difficult_lvl: Optional[int] = Field(1, ge=1)
    battles: Optional[int] = 0
    victories: Optional[int] = 0
    defeats: Optional[int] = 0
    current_difficulty_level: Optional[int] = Field(1, ge=1)


class PlayerProgressCreateSchema(PlayerProgressBase):
    pass


class PlayerProgressUpdateSchema(PlayerProgressBase):
    pass


class PlayerProgressSchema(PlayerProgressBase):
    id: int

    class Config:
        from_attributes = True
