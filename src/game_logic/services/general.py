from sqlalchemy.ext.asyncio import AsyncSession

from src.game_logic.services.ability_service import AbilityService
from src.game_logic.services.biome_service import BiomeService
from src.game_logic.services.character_service import CharacterService
from src.game_logic.services.class_service import ClassService
from src.game_logic.services.crafting_service import CraftingService
from src.game_logic.services.deck_service import DeckService
from src.game_logic.services.inventory_service import InventoryService
from src.game_logic.services.item_service import ItemService
from src.game_logic.services.params_service import ParamsService
from src.game_logic.services.player_progress_service import PlayerProgressService
from src.game_logic.services.race_service import RaceService
from src.game_logic.services.rune_service import RuneService


class Services:
    def __init__(self, session: AsyncSession):
        self.__session = session
        self.ability_service: AbilityService = AbilityService(self.__session)
        self.class_service: ClassService = ClassService(self.__session)
        self.race_service: RaceService = RaceService(self.__session)
        self.params_service: ParamsService = ParamsService(self.__session)
        self.item_service: ItemService = ItemService(self.__session)
        self.character_service: CharacterService = CharacterService(self.__session)
        self.deck_service: DeckService = DeckService(self.__session)
        self.rune_service: RuneService = RuneService(self.__session)
        self.biome_service: BiomeService = BiomeService(self.__session)
        self.player_progress_service: PlayerProgressService = PlayerProgressService(self.__session)
        self.inventory_service: InventoryService = InventoryService(self.__session)
        self.crafting_service: CraftingService = CraftingService(self.__session)
