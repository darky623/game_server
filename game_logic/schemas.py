from typing import Optional

from pydantic import BaseModel


class AddMultiplierParamsSchema(BaseModel):
    damage: float = 1.0
    vitality: float = 1.0
    strength: float = 1.0
    agility: float = 1.0
    intelligence: float = 1.0
    speed: float = 1.0
    physical_resistance: float = 1.0
    magical_resistance: float = 1.0
    critical_hit_chance: float = 1.0
    evasion: float = 1.0
    true_damage: float = 1.0
    accuracy: float = 1.0
    spirit: float = 1.0


class AddSummandParamsSchema(BaseModel):
    damage: float = 0.0
    vitality: float = 0.0
    strength: float = 0.0
    agility: float = 0.0
    intelligence: float = 0.0
    speed: float = 0.0
    physical_resistance: float = 0.0
    magical_resistance: float = 0.0
    critical_hit_chance: float = 0.0
    evasion: float = 0.0
    true_damage: float = 0.0
    accuracy: float = 0.0
    spirit: float = 0.0


class AddItemTierSchema(BaseModel):
    name: str


class ItemTierSchema(AddItemTierSchema):
    id: int


class AddItemSchema(BaseModel):
    name: str
    level: int
    icon: str
    tier_id: int
    summand_params: AddSummandParamsSchema
    multiplier_params: AddMultiplierParamsSchema


class ItemSchema(AddItemSchema):
    id: int


class AddRaceSchema(BaseModel):
    name: str

    summand_params: AddSummandParamsSchema
    multiplier_params: AddMultiplierParamsSchema


class AddAbilityTierSchema(BaseModel):
    name: str


class AbilityTierSchema(AddAbilityTierSchema):
    id: int


class AddAbilityTypeSchema(BaseModel):
    name: str


class AbilityTypeSchema(AddAbilityTypeSchema):
    id: int


class AddAbilitySchema(BaseModel):
    name: str
    icon: str
    ability_type_id: int
    ability_tier_id: int
    chance: float

    summand_params: Optional[AddSummandParamsSchema] = None
    multiplier_params: Optional[AddMultiplierParamsSchema] = None

    summoned_character_id: Optional[int] = None
    summoned_quantity: int
    damage: int = 0
    healing: int = 0


class AddArchetypeSchema(BaseModel):
    title: str
    summand_params: AddSummandParamsSchema
    multiplier_params: AddMultiplierParamsSchema


class ArchetypeSchema(AddArchetypeSchema):
    id: int


class AddCharacterTypeSchema(BaseModel):
    name: str


class CharacterTypeSchema(AddCharacterTypeSchema):
    id: int


class AddCharacterSchema(BaseModel):
    name: str
    avatar: str
    stardom: int
    level: int
    user_id: int

    character_type_id: int
    archetype_id: int
    race_id: int

    summand_params: AddSummandParamsSchema
    multiplier_params: AddMultiplierParamsSchema

    item_ids: list[int]
    ability_ids: list[int]


class CharacterSchema(AddCharacterSchema):
    id: int



