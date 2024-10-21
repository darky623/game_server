from fastapi import HTTPException
from sqlalchemy import select, delete

from src.game_logic.models.models import Ability, AbilityType
from src.game_logic.schemas.ability_schema import AddAbilityTypeSchema
from src.game_logic.services.service import Service


class AbilityService(Service):
    async def get_all(self):
        result = await self.session.execute(select(Ability))
        abilities = result.unique().scalars().all()
        return abilities

    async def get_by_id(self, id: int):
        result = await self.session.execute(select(Ability).where(Ability.id == id))
        ability = result.scalars().first()
        if not ability:
            raise HTTPException(400, detail='No ability with such id')
        return ability

    async def get_by_ids(self, ability_ids: list[int]):
        if not ability_ids: return []
        result = await self.session.execute(select(Ability).where(Ability.id.in_(ability_ids)))
        return result.scalars().all()

    async def delete(self, ability: Ability):
        await self.session.delete(ability)
        await self.session.commit()

    async def delete_by_id(self, id: int):
        result = await self.session.execute(delete(Ability).where(Ability.id == id))
        if result.rowcount == 0:
            raise HTTPException(400, detail='No ability with such id')
        await self.session.commit()
        return result

    async def add_type(self, add_type: AddAbilityTypeSchema) -> AbilityType:
        ability_type = AbilityType(**add_type.model_dump())
        self.session.add(ability_type)
        await self.session.commit()
        await self.session.refresh(ability_type)
        return ability_type

    async def delete_type_by_id(self, id: int):
        result = await self.session.execute(delete(AbilityType).where(AbilityType.id == id))
        if result.rowcount == 0:
            raise HTTPException(400, detail='No ability type with such id')
        await self.session.commit()
        return result

    async def get_type_by_id(self, id: int):
        result = await self.session.execute(select(AbilityType).where(AbilityType.id == id))
        ability_type = result.scalars().first()
        if not ability_type:
            raise HTTPException(400, detail='No ability type with such id')
        return ability_type

    async def get_all_types(self):
        result = await self.session.execute(select(AbilityType))
        ability_types = result.unique().scalars().all()
        return ability_types