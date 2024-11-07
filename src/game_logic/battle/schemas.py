from pydantic import BaseModel


class BattleSchema(BaseModel):
    team_1: list[int]
    team_2: list[int]


class RoundLogSchema(BaseModel):
    id: int
    steps: list


class BattleResultSchema(BaseModel):
    rounds: list[RoundLogSchema]
    result: dict | int

