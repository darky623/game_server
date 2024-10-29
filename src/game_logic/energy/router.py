from fastapi import Depends, APIRouter
from starlette.responses import JSONResponse

from auth.models import User
from auth.user_service import get_current_user
from config.database import AsyncSessionFactory
from src.game_logic.energy.energy_service import EnergyService
from src.game_logic.energy.schema import EnergySchema

router = APIRouter(prefix="/energy", tags=["Energy"])

energy_service = EnergyService(AsyncSessionFactory)


@router.get("", dependencies=[Depends(get_current_user)])
async def get_energy(user: User = Depends(get_current_user)) -> EnergySchema:
    return await energy_service.get_energy(user.id)


@router.post("", dependencies=[Depends(get_current_user)])
async def update_energy(amount: int, user: User = Depends(get_current_user)) -> EnergySchema | JSONResponse:
    return await energy_service.update_energy(user_id=user.id, amount=amount)
