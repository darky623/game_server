from fastapi import Depends, APIRouter
from starlette.responses import JSONResponse

from auth.models import User
from auth.user_service import get_current_user

from config.deps import get_services
from src.game_logic.schemas.energy_schema import EnergySchema
from src.game_logic.services.energy_service import error_handler

from src.game_logic.services.general import Services

router = APIRouter(prefix="/energy", tags=["Energy"])


@error_handler
@router.post("/", dependencies=[Depends(get_current_user)], response_model=None)
async def update_energy(amount: int,
                        overmax: bool = False,
                        user: User = Depends(get_current_user),
                        services: Services = Depends(get_services)
                        ) -> EnergySchema | JSONResponse:
    return await services.energy_service.update_energy(user_id=user.id, amount=amount, overmax=overmax)


