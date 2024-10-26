import json
import random

from src.game_logic.battle.controllers import AbilityController, CharacterController


class Battle:
    def __init__(self,
                 team1: list[CharacterController],
                 team2: list[CharacterController],
                 max_rounds: int = 10):
        self.team1 = team1
        self.team2 = team2
        self.max_rounds = max_rounds
        self.current_round = 0
        self.order = 0 # 0 - 1 команда, 1 - вторая команда
        self.battle_log = BattleLog()

    def start(self):
        while not self.is_battle_over():
            self.play_round()

        self.export_log()

    def get_turn_order(self):
        return self.team1 if self.order == 0 else self.team2

    def play_round(self):
        for character in self.get_turn_order():
            if character.health > 0:
                result = character.attack()
                self.battle_log.log_event({'usage': f'{character._character.name} использовал {ability_controller._ability.name}'})

    def is_battle_over(self):
        return all(c.health <= 0 for c in self.team1) or all(c.health <= 0 for c in self.team2)

    def __set_teammates(self):
        for character in self.team1:
            character.set_teammates([ch for ch in self.team1 if ch != character])
            character.set_enemies(self.team2)
        for character in self.team2:
            character.set_enemies(self.team1)
            character.set_teammates([ch for ch in self.team2 if ch != character])


    def export_log(self):
        print(self.battle_log.export_to_json())


class BattleLog:
    def __init__(self):
        self.events = []

    def log_event(self, event: dict):
        self.events.append(event)

    def export_to_json(self):
        return json.dumps(self.events, ensure_ascii=False, indent=4)


class LogEvent:
    ...