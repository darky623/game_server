from pydantic import BaseModel


class CreateCharacterSchema(BaseModel):
    name: str
    archetype_id: int
