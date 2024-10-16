from pydantic import BaseModel


class AddMultiplierParamsSchema(BaseModel):
    damage: float = 1
    vitality: float = 1
    speed: float = 1
    resistance: float = 1
    evasion: float = 1

    class Config:
        from_attributes = True


class AddSummandParamsSchema(BaseModel):
    damage: float = 0
    vitality: float = 0
    speed: float = 0
    resistance: float = 0
    evasion: float = 0

    class Config:
        from_attributes = True
