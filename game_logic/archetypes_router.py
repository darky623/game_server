from fastapi import APIRouter, Depends
from auth.models import User
from schemas import AddArchetypeSchema, ArchetypeSchema
from auth.user_service import get_current_user

router = APIRouter(prefix='/archetypes', tags=['archetypes'])


@router.post('', response_model=ArchetypeSchema, dependencies=[Depends(get_current_user)])
async def create_archetype(add_archetype: AddArchetypeSchema):
    ...


@router.get('', response_model=list[ArchetypeSchema], dependencies=[Depends(get_current_user)])
async def get_archetypes():
    ...


@router.delete('/{archetype_id}', response_model=ArchetypeSchema, dependencies=[Depends(get_current_user)])
async def delete_archetype(archetype_id: int):
    ...
