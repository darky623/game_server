from src.game_logic.battle.battle import Battle
from src.game_logic.battle.controllers import CharacterController

team_1 = [CharacterController()]
team_2 = [CharacterController()]

battle = Battle()
battle.start()