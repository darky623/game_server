from fastapi import APIRouter, Depends, HTTPException
from typing_extensions import Optional

from auth.user_service import get_current_user
from deps import get_services
from game_logic.models.models import SummandParams, MultiplierParams, Item
from game_logic.schemas.item_schema import AddItemSchema, GetItemsSchema, ItemSchema

router = APIRouter(prefix='/items', tags=['items'])


@router.post('', response_model=ItemSchema, dependencies=[Depends(get_current_user)])
async def create_item(add_item: AddItemSchema,
                      services = Depends(get_services)):
    summand_params_model = SummandParams(**add_item.summand_params.model_dump())
    multiplier_params_model = MultiplierParams(**add_item.multiplier_params.model_dump())
    inserted_summand_params = await services.params_service.add(summand_params_model)
    inserted_multiplier_params = await services.params_service.add(multiplier_params_model)
    try:
        item_model = Item(name=add_item.name,
                          level=add_item.level,
                          icon=add_item.icon,
                          tier=add_item.tier,
                          summand_params_id=inserted_summand_params.id,
                          multiplier_params_id=inserted_multiplier_params.id)
        inserted_item = await services.item_service.add(item_model)
        return inserted_item
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.get('', response_model=list[ItemSchema], dependencies=[Depends(get_current_user)])
async def get_items(item_ids: Optional[list[int]] = None,
                    services = Depends(get_services)):
    if not item_ids:
        return await services.item_service.get_all()
    items = await services.item_service.get_by_ids(item_ids)
    return items


@router.get('/{item_id}', response_model=ItemSchema)
async def get_item_by_id(item_id: int,
                         services = Depends(get_services)):
    return await services.item_service.get_by_id(item_id)


@router.delete('/{item_id}', dependencies=[Depends(get_current_user)])
async def delete_item(item_id: int,
                      services = Depends(get_services)):
    result = await services.item_service.delete_by_id(item_id)
    if result:
        return {'message': 'ok'}
    raise HTTPException(400, detail='Something went wrong(')


