from fastapi import APIRouter

from src.game_logic.routers.player_progress_router import router as player_progress_router
from src.game_logic.routers.biome_router import router as biome_router
from src.game_logic.routers.deck_router import router as deck_router
from src.game_logic.routers.runes_router import router as runes_router
from src.game_logic.routers.classes_router import router as classes_router
from src.game_logic.routers.races_router import router as races_router
from src.game_logic.routers.items_router import router as items_router
from src.game_logic.routers.abilities_router import router as abilities_router
from src.game_logic.routers.character_router import router as characters_router
from src.game_logic.battle.router import router as battle_router
from src.game_logic.routers.inventory_router import router as inventory_router


router = APIRouter(prefix='/game_logic', tags=['Game Logic'])
router.include_router(classes_router)
router.include_router(races_router)
router.include_router(items_router)
router.include_router(abilities_router)
router.include_router(deck_router)
router.include_router(runes_router)
router.include_router(characters_router)
router.include_router(biome_router)
router.include_router(player_progress_router)
router.include_router(battle_router)
router.include_router(inventory_router)
