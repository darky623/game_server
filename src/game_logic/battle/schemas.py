from pydantic import BaseModel


class BattleSchema(BaseModel):
    team_1: list[int]
    team_2: list[int]


class RoundLogSchema(BaseModel):
    steps: list


class BattleResultSchema(BaseModel):
    battle_log: list[RoundLogSchema]
    result: dict | int

