from sqlalchemy.ext.asyncio import AsyncSession

from game_logic.services.ability_service import AbilityService
from game_logic.services.character_service import CharacterService
from game_logic.services.class_service import ClassService
from game_logic.services.item_service import ItemService
from game_logic.services.params_service import ParamsService
from game_logic.services.race_service import RaceService


class Services:
    def __init__(self, session: AsyncSession):
        self.__session = session
        self.ability_service: AbilityService = AbilityService(self.__session)
        self.class_service: ClassService = ClassService(self.__session)
        self.race_service: RaceService = RaceService(self.__session)
        self.params_service: ParamsService = ParamsService(self.__session)
        self.item_service: ItemService = ItemService(self.__session)
        self.character_service: CharacterService = CharacterService(self.__session)