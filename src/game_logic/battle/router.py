from datetime import time

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from starlette import status
import time

from auth.models import User
from auth.user_service import get_current_user
from config.deps import get_services
from src.game_logic.battle.battle import Battle
from src.game_logic.battle.controllers import CharacterController
from src.game_logic.battle.schemas import BattleSchema
from src.game_logic.energy.energy_decorators import require_energy
from src.game_logic.services.general import Services

router = APIRouter(prefix='/battle', tags=['Battle'])


def time_decorator(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(end_time - start_time)
        return result
    return wrapper


@router.post('')
@require_energy(energy_amount=10)  # Требуется 10 единиц энергии для начала сражения
async def create_battle(battle_create: BattleSchema,
                        user: User = Depends(get_current_user),
                        services: Services = Depends(get_services)):
    character_ids = battle_create.team_1 + battle_create.team_2
    characters = await services.character_service.get_many_by_ids(character_ids)
    team_1 = characters[:len(battle_create.team_1)]
    team_2 = characters[len(battle_create.team_1):]
    if not all(character.user_id == user.id for character in team_1):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed to create battle team, while you are not owner')
    if all(character.user_id is None for character in team_2):
        team_1_controllers = [CharacterController(character) for character in team_1]
        team_2_controllers = [CharacterController(character) for character in team_2]
        battle = Battle(team_1_controllers, team_2_controllers)
        return battle.start()
    team_1_controllers = [CharacterController(character) for character in team_1]
    team_2_controllers = [CharacterController(character) for character in team_2]
    battle = Battle(team_1_controllers, team_2_controllers)
    return battle.start()
    # raise HTTPException(status_code=400, detail='You are not allowed to create battle team')


@router.get('/{battle_id}')
async def get_battle_result(battle_id: int,
                            user: User = Depends(get_current_user)):
    ...