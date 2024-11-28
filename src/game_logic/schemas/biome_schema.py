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

