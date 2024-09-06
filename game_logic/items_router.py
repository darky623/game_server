from fastapi import APIRouter, Depends

from auth.user_service import get_current_user
from schemas import AddItemTierSchema, ItemTierSchema, AddItemSchema, ItemSchema

router = APIRouter(prefix='/items', tags=['items'])


@router.post('', response_model=ItemSchema, dependencies=[Depends(get_current_user)])
async def create_item(add_item: AddItemSchema):
    ...


@router.get('', response_model=list[ItemSchema], dependencies=[Depends(get_current_user)])
async def get_items():
    ...


@router.patch('', response_model=ItemSchema, dependencies=[Depends(get_current_user)])
async def update_item(edit_item: ItemSchema):
    ...


@router.post('/tiers', response_model=ItemTierSchema, dependencies=[Depends(get_current_user)])
async def create_item_tier(add_item_tier: AddItemTierSchema):
    ...


@router.get('/tiers', response_model=list[ItemTierSchema], dependencies=[Depends(get_current_user)])
async def get_tiers():
    ...
