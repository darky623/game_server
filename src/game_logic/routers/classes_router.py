from fastapi import APIRouter, Depends, HTTPException

from auth.user_service import get_current_user
from src.game_logic.schemas.class_schema import AddCharacterClassSchema, AddCharacterSubclassSchema, CharacterClassSchema, \
    CharacterSubclassSchema
from config.deps import get_services
from src.game_logic.models.models import SummandParams, MultiplierParams, CharacterClass, CharacterSubclass

router = APIRouter(prefix='/classes', tags=['classes'])


@router.post('', response_model=CharacterClassSchema, dependencies=[Depends(get_current_user)])
async def create_class(add_class: AddCharacterClassSchema,
                       services = Depends(get_services)):
    summand_params_model = SummandParams(**add_class.summand_params.model_dump())
    multiplier_params_model = MultiplierParams(**add_class.multiplier_params.model_dump())
    inserted_summand_params = await services.params_service.add(summand_params_model)
    inserted_multiplier_params = await services.params_service.add(multiplier_params_model)
    abilities = await services.ability_service.get_by_ids(add_class.abilities)
    if not all(ability.tier == 0 for ability in abilities):
        raise HTTPException(400, detail='You can use only abilities of 0 tier')
    character_class_model = CharacterClass(title=add_class.title,
                                           icon=add_class.icon,
                                           summand_params_id=inserted_summand_params.id,
                                           multiplier_params_id=inserted_multiplier_params.id)
    character_class_model.abilities = abilities
    inserted_class = await services.class_service.add(character_class_model)
    return inserted_class


@router.get('', response_model=list[CharacterClassSchema], dependencies=[Depends(get_current_user)])
async def get_classes(services = Depends(get_services)):
    classes = await services.class_service.get_all()
    response = [CharacterClassSchema.from_orm(character_class) for character_class in classes]
    return response


@router.get('/{class_id}', response_model=CharacterClassSchema)
async def get_class_by_id(class_id: int,
                          services = Depends(get_services)):
    character_class = await services.class_service.get_by_id(class_id)
    schema = CharacterClassSchema.from_orm(character_class)
    return schema


@router.delete('/{class_id}', dependencies=[Depends(get_current_user)])
async def delete_class(class_id: int,
                       services = Depends(get_services)):
    result = await services.class_service.delete_by_id(class_id)
    if not result:
        raise HTTPException(400, detail='Class does not exist')
    return result


@router.post('/{class_id}/subclasses', response_model=CharacterSubclassSchema, dependencies=[Depends(get_current_user)])
async def create_subclass(class_id: int,
                          add_subclass: AddCharacterSubclassSchema,
                          services = Depends(get_services)):
    existing_class = await services.class_service.get_by_id(class_id)
    if not existing_class:
        raise HTTPException(400, detail='No class with such id')
    summand_params_model = SummandParams(**add_subclass.summand_params.model_dump())
    multiplier_params_model = MultiplierParams(**add_subclass.multiplier_params.model_dump())
    inserted_summand_params = await services.params_service.add(summand_params_model)
    inserted_multiplier_params = await services.params_service.add(multiplier_params_model)
    abilities = await services.ability_service.get_by_ids(add_subclass.abilities)
    if not all(ability.tier != 0 for ability in abilities):
        raise HTTPException(400, detail='You can use only abilities of non-zero tier')
    character_subclass_model = CharacterSubclass(title=add_subclass.title,
                                                 icon=add_subclass.icon,
                                                 multiplier_params_id=inserted_multiplier_params.id,
                                                 summand_params_id=inserted_summand_params.id)
    character_subclass_model.abilities = abilities
    inserted_subclass = await services.class_service.add_subclass(existing_class, character_subclass_model)
    return inserted_subclass


@router.get('/{class_id}/subclasses', response_model=list[CharacterSubclassSchema], dependencies=[Depends(get_current_user)])
async def get_subclasses_of_class(class_id: int,
                                  services = Depends(get_services)):
    return await services.class_service.get_subclasses(class_id)


@router.delete('/{class_id}/subclasses/{subclass_id}', dependencies=[Depends(get_current_user)])
async def delete_subclass(class_id: int, subclass_id: int,
                          services = Depends(get_services)):
    await services.class_service.delete_subclass_by_id(class_id, subclass_id)
    return {'message': 'ok'}