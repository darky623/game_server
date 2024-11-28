from fastapi import APIRouter, Depends, HTTPException
from config.deps import get_services
from auth.user_service import get_current_user
from src.game_logic.models.models import SummandParams, MultiplierParams, Ability, TriggerCondition
from src.game_logic.schemas.ability_schema import AddAbilityTypeSchema, AbilityTypeSchema, AbilitySchema, AddAbilitySchema

router = APIRouter(prefix='/abilities', tags=['Abilities'], dependencies=[Depends(get_current_user)])


@router.get('', response_model=list[AbilitySchema])
async def get_abilities(services = Depends(get_services)):
    abilities = await services.ability_service.get_all()
    return abilities


@router.get('/{ability_id}', response_model=AbilitySchema)
async def get_ability(ability_id: int,
                      services = Depends(get_services)):
    ability = await services.ability_service.get_by_id(ability_id)
    return ability


@router.post('', response_model=AbilitySchema)
async def create_ability(add_ability: AddAbilitySchema,
                         services = Depends(get_services)):
    inserted_summand_params_id = None
    inserted_multiplier_params_id = None
    if add_ability.summand_params:
        summand_params_model = SummandParams(**add_ability.summand_params.model_dump())
        inserted_summand_params = await services.params_service.add(summand_params_model)
        inserted_summand_params_id = inserted_summand_params.id
    if add_ability.multiplier_params:
        multiplier_params_model = MultiplierParams(**add_ability.multiplier_params.model_dump())
        inserted_multiplier_params = await services.params_service.add(multiplier_params_model)
        inserted_multiplier_params_id = inserted_multiplier_params.id
    ability_type = await services.ability_service.get_type_by_id(add_ability.ability_type_id)
    try:
        ability_model = Ability(name=add_ability.name,
                                icon=add_ability.icon,
                                visual=add_ability.visual,
                                tier=add_ability.tier,
                                ability_type_id=ability_type.id,
                                trigger_condition=TriggerCondition(add_ability.trigger_condition),
                                summand_params_id=inserted_summand_params_id,
                                multiplier_params_id=inserted_multiplier_params_id,
                                summoned_character_id=add_ability.summoned_character_id,
                                summoned_quantity=add_ability.summoned_quantity,
                                effect=str(add_ability.effect),
                                chance=add_ability.chance,
                                damage=add_ability.damage,
                                healing=add_ability.healing)
        inserted_ability = await services.ability_service.add(ability_model)
        return inserted_ability
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.patch('/{ability_id}')
async def edit_ability(services = Depends(get_services)):
    ...


@router.delete('/{ability_id}')
async def delete_ability(ability_id: int,
                         services = Depends(get_services)):
    result = await services.ability_service.delete_by_id(ability_id)
    return {'message': 'ok'}


@router.post('/types', response_model=AbilityTypeSchema)
async def create_ability_type(add_type: AddAbilityTypeSchema,
                              services = Depends(get_services)):
    inserted_type = await services.ability_service.add_type(add_type)
    return inserted_type


@router.get('/types/', response_model=list[AbilityTypeSchema])
async def get_ability_types(services = Depends(get_services)):
    types = await services.ability_service.get_all_types()
    return types


@router.delete('/types/{ability_type_id}')
async def delete_ability_type(ability_type_id: int,
                              services = Depends(get_services)):
    result = await services.ability_service.delete_type_by_id(ability_type_id)
    return {'message': 'ok'}