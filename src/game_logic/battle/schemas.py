from pydantic import BaseModel


class BattleSchema(BaseModel):
    team_1: [list[int]]
    team_2: [list[int]]


class StepResultSchema(BaseModel):
    ...


class PhysicalAttackStepSchema(StepResultSchema):
    ...


class AbilityAttackStepSchema(StepResultSchema):
    name: str
    visual: str


class ActionSchema(BaseModel):
    initiator: int
    targets: list[int]
    result: StepResultSchema


class StepLogSchema(BaseModel):
    action: ActionSchema
    result: StepResultSchema


class RoundLogSchema(BaseModel):
    steps: list[StepLogSchema]


class BattleResultSchema(BaseModel):
    battle_log: list[RoundLogSchema]
    result: int

