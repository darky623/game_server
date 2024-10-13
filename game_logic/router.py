from fastapi import APIRouter

from game_logic.routers.deck_router import router as deck_router
from game_logic.routers.classes_router import router as classes_router
from game_logic.routers.races_router import router as races_router
from game_logic.routers.items_router import router as items_router
from game_logic.routers.abilities_router import router as abilities_router
from game_logic.routers.character_router import router as characters_router


router = APIRouter(prefix='/game_logic', tags=['Game Logic'])
router.include_router(classes_router)
router.include_router(races_router)
router.include_router(items_router)
router.include_router(abilities_router)
router.include_router(characters_router)
router.include_router(deck_router)
