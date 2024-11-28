from fastapi import APIRouter, Depends

from auth.models import User
from auth.schemas import UserSchema
from auth.user_service import get_current_user_with_related

router = APIRouter(prefix='/summary', tags=['summary'])


@router.get('', response_model=UserSchema)
async def summary(user: User = Depends(get_current_user_with_related)):
    summary_result = UserSchema.from_orm(user)
    return summary_result