from fastapi import APIRouter, Depends

from auth.user_service import get_current_user
from deps import get_services
from game_logic.models.models import SummandParams, MultiplierParams, Race
from game_logic.schemas.race_schema import AddRaceSchema, RaceSchema

router = APIRouter(prefix='/races', tags=['Races'])


@router.post('', response_model=RaceSchema, dependencies=[Depends(get_current_user)])
async def create_race(add_race: AddRaceSchema,
                      services = Depends(get_services)):
    summand_params_model = SummandParams(**add_race.summand_params.model_dump())
    multiplier_params_model = MultiplierParams(**add_race.multiplier_params.model_dump())
    inserted_summand_params = await services.params_service.add(summand_params_model)
    inserted_multiplier_params = await services.params_service.add(multiplier_params_model)
    race_model = Race(name=add_race.name,
                      summand_params_id=inserted_summand_params.id,
                      multiplier_params_id=inserted_multiplier_params.id)
    inserted_race = await services.race_service.add(race_model)
    return inserted_race


@router.get('', response_model=list[RaceSchema], dependencies=[Depends(get_current_user)])
async def get_all_races(services = Depends(get_services)):
    races = await services.race_service.get_all()
    return races


@router.delete('/{race_id}')
async def delete_race(race_id: int,
                      services = Depends(get_services)):
    await services.race_service.delete_by_id(race_id)
    return {'message': 'ok'}