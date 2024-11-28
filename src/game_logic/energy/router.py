from fastapi import Depends, APIRouter
from starlette.responses import JSONResponse

from auth.models import User
from auth.user_service import get_current_user
from config.database import AsyncSessionFactory
from src.game_logic.energy.energy_service import EnergyService, error_handler
from src.game_logic.energy.schema import EnergySchema

router = APIRouter(prefix="/energy", tags=["Energy"])

energy_service = EnergyService(AsyncSessionFactory)


@error_handler
@router.post("/", dependencies=[Depends(get_current_user)], response_model=None)
async def update_energy(amount: int,
                        overmax: bool = False,
                        user: User = Depends(get_current_user)
                        ) -> EnergySchema | JSONResponse:
    return await energy_service.update_energy(user_id=user.id, amount=amount, overmax=overmax)


