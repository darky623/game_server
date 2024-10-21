from fastapi import APIRouter, HTTPException
from fastapi import Depends

from config.deps import get_services
from src.game_logic.models.models import SummandParams, MultiplierParams, Rune
from src.game_logic.schemas.rune_schema import RuneSchema, AddRuneSchema
from src.game_logic.services.general import Services

router = APIRouter(prefix='/runes', tags=['runes'])


@router.get('', response_model=list[RuneSchema])
async def get_runes(services: Services = Depends(get_services)):
    runes = await services.rune_service.get_all()
    return runes


@router.post('', response_model=RuneSchema)
async def create_rune(add_rune: AddRuneSchema,
                      services: Services = Depends(get_services)):
    summand_params_model = SummandParams(**add_rune.summand_params.model_dump())
    multiplier_params_model = MultiplierParams(**add_rune.multiplier_params.model_dump())
    inserted_summand_params = await services.params_service.add(summand_params_model)
    inserted_multiplier_params = await services.params_service.add(multiplier_params_model)
    race_model = Rune(name=add_rune.name,
                      level=add_rune.level,
                      summand_params_id=inserted_summand_params.id,
                      multiplier_params_id=inserted_multiplier_params.id)

    abilities = await services.ability_service.get_by_ids(add_rune.ability_ids)
    for ability in abilities:
        if ability.tier != 0:
            raise HTTPException(400, f'Two abilities of non-zero tier cannot be used')
    race_model.abilities.extend(abilities)
    inserted_race = await services.race_service.add(race_model)
    return inserted_race


@router.delete('/{rune_id}')
async def delete_rune(rune_id: int,
                      services: Services = Depends(get_services)):
    result = await services.rune_service.delete_by_id(rune_id)
    return {'message': 'ok'}
