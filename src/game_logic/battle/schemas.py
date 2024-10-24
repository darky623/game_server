from pydantic import BaseModel


class BattleSchema(BaseModel):
    team_1: [list[int]]
    team_2: [list[int]]


class BattleResultSchema(BaseModel):
    battle_log: dict
    result: int