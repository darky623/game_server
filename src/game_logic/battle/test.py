from src.game_logic.battle.battle import Battle
from src.game_logic.battle.controllers import CharacterController
from src.game_logic.models.models import Character, SummandParams

s_params = SummandParams(damage=10, vitality=50, speed=10, resistance=2, evasion=10)


c1 = Character(name='klkl',
               summand_params=s_params)


team_1 = [CharacterController(c1)]
team_2 = [CharacterController(c1)]

battle = Battle(team_1, team_2)
battle.start()