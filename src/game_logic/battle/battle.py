from enum import Enum, auto
import json
from fastapi import HTTPException

from src.game_logic.battle.observer.subject import Subject
from src.game_logic.battle.schemas import RoundLogSchema, BattleResultSchema


class Battle(Subject):
    def __init__(self, team1: list, team2: list, max_rounds: int = 10):
        super().__init__()
        if not len(team1) or not len(team2):
            raise HTTPException(status_code=400, detail='В команде должен быть хотя бы один герой')

        self.team1 = team1
        self.team2 = team2
        self.max_rounds = max_rounds
        self.current_round = 0
        self.order = False # 0 - первая команда, 1 - вторая команда
        self.battle_log = BattleLog()

        self.rounds = []
        self.set_battle_ids()
        self.__set_teammates()

    def start(self):
        while not self.is_battle_over():
            self.rounds.append(self.play_round())
            self.round_update()

        return BattleResultSchema(rounds=self.rounds, result=self.__get_result())

    def get_turn_order(self):
        return self.team1 if self.order == 0 else self.team2

    def play_round(self):
        round = []
        teams = [self.team1, self.team2]
        total_turns = len(self.team1) + len(self.team2)
        turns_taken = 0
        step_id = 1
        while turns_taken < total_turns:
            current_team = teams[self.order]
            for character in current_team:
                if character.health > 0:
                    step = character.attack()
                    step['id'] = step_id
                    step_id += 1
                    round.append(step)
                    self.order = 1 - self.order
                    turns_taken += 1
                    break
                else:
                    continue

        self.current_round += 1
        return RoundLogSchema(id=self.current_round, steps=round)

    def is_battle_over(self):
        return all(c.is_dead() for c in self.team1) or all(c.is_dead() for c in self.team2) or (len(self.rounds) >= self.max_rounds)

    def __set_teammates(self):
        for character in self.team1:
            character.set_teammates([ch for ch in self.team1 if ch != character])
            character.set_enemies(self.team2)
        for character in self.team2:
            character.set_enemies(self.team1)
            character.set_teammates([ch for ch in self.team2 if ch != character])

    def set_battle_ids(self):
        i = 0
        for character in self.team1:
            character.set_id_in_battle(i)
            i += 1
        for character in self.team2:
            character.set_id_in_battle(i)
            i += 1

    def round_update(self):
        result = self.notify(BattleEvent.NEW_ROUND)
        for character in self.team1:
            character.round_update()
        for character in self.team2:
            character.round_update()

    def __get_result(self):
        if self.is_battle_over():
            return {'winner': ('team_1' if any(c.is_alive() > 0 for c in self.team1) and all(c.is_dead() <= 0 for c in self.team2) else 'team_2')}
        return {'winner': 'team_2'}


class BattleEvent(Enum):
    NEW_ROUND = auto()
    DAMAGED = auto()
    HEALING = auto()
    IMPOSED = auto()
    BUFF = auto()
    DEBUFF = auto()


class BattleLog:
    def __init__(self):
        self.events = []

    def log_event(self, event: dict):
        self.events.append(event)

    def export_to_json(self):
        return json.dumps(self.events, ensure_ascii=False, indent=4)


class LogEvent:
    ...