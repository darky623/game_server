from typing import List

from fastapi import APIRouter, Depends, status

from auth.models import User
from auth.user_service import get_current_user
from deps import get_services
from game_logic.services.general import Services

from game_logic.schemas.deck_schema import Deck as DeckSchema

router = APIRouter(prefix="/userdecks", tags=["userdecks"])


@router.post("/", response_model=DeckSchema, status_code=status.HTTP_201_CREATED)
async def create_user_deck(character_ids: List[int],
                           user: User = Depends(get_current_user),
                           services: Services = Depends(get_services)):
    """ Создает новую колоду. """
    return await services.deck_service.create_deck(user.id, character_ids)


@router.get("/{deck_id}", response_model=DeckSchema)
async def get_deck(deck_id: int,
                   services: Services = Depends(get_services)):
    """ Возвращает колоду по идентификатору. """
    return await services.deck_service.get_deck(deck_id)


@router.get("/user/{user_id}", response_model=List[DeckSchema])
async def get_user_decks(user: User = Depends(get_current_user),
                         services: Services = Depends(get_services)):
    """ Возвращает все колоды пользователя. """
    return await services.deck_service.get_user_decks(user.id)


@router.get("/user/{user_id}/deck/{deck_index}", response_model=DeckSchema)
async def get_user_deck_by_index(deck_index: int,
                                 user: User = Depends(get_current_user),
                                 services: Services = Depends(get_services)):
    """ Возвращает колоду пользователя по индексу. """
    return await services.deck_service.get_user_deck_by_index(user.id, deck_index)


@router.put("/{user_id}/deck/{deck_index}", response_model=DeckSchema)
async def update_user_deck(deck_index: int,
                           character_ids: List[int],
                           user: User = Depends(get_current_user),
                           services: Services = Depends(get_services),
                           is_active: bool = False
                           ):
    """ Обновляет колоду пользователя. """
    return await services.deck_service.update_deck(user.id, deck_index, character_ids, is_active)


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(deck_id: int,
                      user: User = Depends(get_current_user),
                      services: Services = Depends(get_services)):
    """ Удаляет колоду пользователя по идентификатору. """
    return await services.deck_service.delete_deck_by_index(user.id, deck_id)


@router.get("/active/{user_id}", response_model=DeckSchema)
async def get_active_deck(user: User = Depends(get_current_user),
                          services: Services = Depends(get_services)):
    """ Возвращает активную колоду пользователя. """
    return await services.deck_service.get_active_deck(user.id)
