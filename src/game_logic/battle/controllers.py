import enum
import random
import ast

from src.game_logic.battle.battle import BattleEvent
from src.game_logic.battle.observer.observer import Observer
from src.game_logic.models import TriggerCondition
from src.game_logic.models.models import Character, Ability, SummandParams
from src.game_logic.schemas.params_schema import AddSummandParamsSchema
from src.game_logic.battle.effects import effects_dict, BaseEffect, StartEndEffect, CycleEffect, Paralysis, \
    EffectManager, Immunity
from typing import Type


class CharacterController(Observer):
    def __init__(self, character: Character):
        self._character = character
        self.active_abilities: dict[int, AbilityController] = self.__get_active_abilities()
        self.passive_abilities: list[AbilityController] = self.__get_passive_abilities()
        self.base_params: SummandParams = self.__calculate_base_params()

        self.teammates = []
        self.enemies = []

        self.max_health = self.base_params.vitality
        self.vitality = self.base_params.vitality
        self.physical_damage = self.base_params.damage
        self.evasion = self.base_params.evasion
        self.resistance = self.base_params.resistance
        self.speed = self.base_params.speed
        self.id_in_battle = None
        self.effects = set()
        self.immunities = set()
        self._paralyzed = False

        self.effect_manager = EffectManager()
        self.events_handlers = {
            BattleEvent.NEW_ROUND: self.round_update,
            BattleEvent.START: self.start_update
        }

    def attack(self):
        action = {
            'initiator': self.id_in_battle,
        }
        ability_to_use = self.__get_ability_to_attack()
        if not ability_to_use:
            target = self.__choose_random_enemy()
            result = self.physical_attack(target)
            action['targets'] = [target.id_in_battle]
            action['ability'] = 'physical attack'
            return result
        targets = self._select_target(ability_to_use)
        action['targets'] = [target.id_in_battle for target in targets]
        action['ability'] = ability_to_use.name
        results = []
        for target in targets:
            results.append(ability_to_use.execute(self, target))
        action['result'] = results
        action['icon'] = ability_to_use.icon
        action['visual'] = ability_to_use.visual

        return action

    def physical_attack(self, target: 'CharacterController'):
        damage = self.calculate_damage()
        target.receive_damage(damage)
        result = target.serialize()
        return result

    def ability_attack(self, ability: 'AbilityController', target: 'CharacterController'):
        action = ability.execute(self, target)
        return action

    def use_passive_abilities(self, condition: TriggerCondition | str = None):
        result = []
        if condition:
            for ability in self.passive_abilities:
                if ability.trigger_condition == condition:
                    action = {
                        'initiator': self.id_in_battle,
                        'targets': [self.id_in_battle],
                        'ability': ability.name,
                        'visual': ability.visual,
                        'icon': ability.icon,
                        'result': ability.execute(self, self)
                    }
                    result.append(action)
            return result
        for ability in self.passive_abilities:
            action = {
                'initiator': self.id_in_battle,
                'targets': [self.id_in_battle],
                'ability': ability.name,
                'visual': ability.visual,
                'icon': ability.icon,
                'result': ability.execute(self, self)
            }
            result.append(action)
        return result

    def start_update(self):
        result = self.use_passive_abilities(TriggerCondition.ON_START)
        return result

    def receive_damage(self, damage: int | float):
        action = {'old_health': self.health}
        real_damage = damage / self.base_params.resistance
        self.health -= real_damage
        action['damage'] = damage
        action['real_damage'] = real_damage
        action['resisted'] = damage - real_damage
        action['new_health'] = self.health
        return action

    def receive_healing(self, health: int):
        action = {'old_health': self.health}
        self.health += health
        self.health = min(self.health, self.max_health)
        action['new_health'] = self.health
        action['healing'] = action['new_health'] - action['old_health']
        return action

    def apply_effect(self, effect: BaseEffect):
        if not effect: return 0
        self.effect_manager.add_effect(effect)

    def apply_immunity(self, immunity: Immunity):
        if not immunity: return 0
        self.effect_manager.add_immunity(immunity)

    def calculate_damage(self):
        return self.physical_damage

    def is_dead(self):
        return self.health <= 0

    def is_alive(self):
        return self.health > 0

    def round_update(self):
        self.__decrease_cooldowns()
        self.use_passive_abilities()
        self.effect_manager.update(BattleEvent.NEW_ROUND)

    def __get_ability_to_attack(self):
        for ability in self.active_abilities.values():
            if (random.random() < ability.chance) and (ability.cooldown == 0):
                return ability

    def __get_active_abilities(self):
        result = {}
        for ability in self._character.subclass.abilities:
            result[ability.tier] = AbilityController(ability)
        return result

    def __get_passive_abilities(self):
        result = []
        result.extend([AbilityController(ability) for ability in self._character.character_class.abilities])
        result.extend([AbilityController(ability) for ability in self._character.race.abilities])
        result.extend((AbilityController(ability) for ability in rune.abilities) for rune in self._character.runes)
        return result

    def __choose_random_enemy(self) -> 'CharacterController':
        return random.choice(self.enemies)

    def __choose_teammate(self) -> 'CharacterController':
        return random.choice(self.teammates)

    def __calculate_base_params(self):
        result = self._character.summand_params * (self._character.multiplier_params * self._character.level)
        result += (self._character.character_class.summand_params +
                   self._character.race.summand_params +
                   self._character.subclass.summand_params)

        result *= (self._character.character_class.multiplier_params *
                   self._character.race.multiplier_params *
                   self._character.subclass.multiplier_params)
        # result += sum([item.summand_params for item in self._character.items])
        for item in self._character.items:
            result *= item.multiplier_params

        return result

    def __decrease_cooldowns(self):
        for ability in self.active_abilities.values():
            ability.decrease_cooldown()
        for ability in self.passive_abilities:
            ability.decrease_cooldown()

    def _select_target(self, ability: 'AbilityController') -> list['CharacterController']:
        try:
            rule_parts = ability.get_target_rule().split(':', 2)
            target_type = TargetType(rule_parts[0])
            if target_type == TargetType.SELF: return [self]
            if rule_parts[1] == 'all':
                quantity = len(self.enemies) if target_type == TargetType.ENEMY else len(self.teammates)
            else: quantity = int(rule_parts[1])
            selection_method = rule_parts[2] if len(rule_parts) > 2 else None
        except:
            return []

        if target_type == TargetType.MATE:
            return self._select_teammates(quantity, selection_method)
        elif target_type == TargetType.ENEMY:
            return self._select_enemies(quantity, selection_method)

        return []

    def _select_enemies(self, quantity: int, method: str):
        if method:
            params = method.split(':')
            key = params[0]
            parameter = params[1] if len(params) > 1 else None
            if key == 'random':
                return random.sample(self.enemies, min(quantity, len(self.enemies)))
            if key == 'highest' or key == 'lowest':
                return sorted(self.enemies, key=lambda e: e.__dict__().get(parameter), reverse=(key == 'highest'))[:quantity]
        return random.sample(self.enemies, min(quantity, len(self.enemies)))

    def _select_teammates(self, quantity: int, method: str):
        if method:
            params = method.split(':')
            key = params[0]
            parameter = params[1] if len(params) > 1 else None
            if key == 'random':
                return random.sample(self.teammates, min(quantity, len(self.teammates)))
            if key == 'highest' or key == 'lowest':
                return sorted(self.teammates, key=lambda e: e.__dict__().get(parameter), reverse=(key == 'highest'))[:quantity]
        return random.sample(self.teammates, min(quantity, len(self.teammates)))

    def set_teammates(self, teammates: list['CharacterController']):
        self.teammates = teammates

    def set_enemies(self, enemies: list['CharacterController']):
        self.enemies = enemies

    def set_id_in_battle(self, id_in_battle: int):
        self.id_in_battle = id_in_battle

    def get_class(self):
        return self._character.character_class

    def update(self, event: BattleEvent):
        handler = self.events_handlers.get(event)
        if handler:
            return handler()

    @property
    def health(self):
        return self.base_params.vitality

    @health.setter
    def health(self, value: int):
        self.base_params.vitality = value

    @property
    def paralyzed(self):
        return self._paralyzed

    @paralyzed.setter
    def paralyzed(self, value: bool):
        if not value:
            cnt = 0
            for effect in self.effects:
                if isinstance(effect, Paralysis):
                    cnt += 1
            if cnt > 1: return
        self._paralyzed = value

    def serialize(self):
        return {
            "id": self.id_in_battle,
            "name": self._character.name,
            "class": self._character.character_class.title,
            "subclass": self._character.subclass.title,
            "stars": self._character.stardom,
            "lvl": self._character.level,
            "params": AddSummandParamsSchema.from_orm(self.base_params),
            "imposed": {
                'effects': [effect.serialize() for effect in self.effect_manager.effects],
                'immunity': [immunity.effect.name for immunity in self.effect_manager.immunities],
            },
            "alive": self.is_alive()
        }


class AbilityController:
    def __init__(self, ability: Ability):
        self._ability = ability
        self._target = ability.target
        self._effect: dict = ast.literal_eval(self._ability.effect)
        self._cooldown = 0
        try:
            self.effect_class: Type[BaseEffect] = effects_dict.get(self._effect.pop('effect'))
            self.effect_params = effects_dict
        except KeyError:
            self.effect_class, self.effect_params = None, None
        try:
            self.immunity_effect = self._effect.pop('immunity')
            self.immunity = Immunity(effects_dict.get(self.immunity_effect))
        except KeyError:
            self.immunity, self.immunity_effect = None, None

    def execute(self, user: CharacterController, target: CharacterController):
        damage_result, healing_result = None, None
        if self._ability.damage > 0:
            damage_result = target.receive_damage(self._ability.damage)
        if self._ability.healing > 0:
            healing_result = target.receive_healing(self._ability.healing)
        if self.effect_class:
            effect_instance = self.effect_class(
                target,
                **self.effect_params,
                description=self.description,
                icon=self.icon,

            )
            result_effect = target.apply_effect(effect_instance)
        if self.immunity:
            result_immunity = target.apply_immunity(self.immunity)


        return target.serialize()

    def is_successful(self):
        import random
        return random.random() <= self._ability.chance

    def apply_damage(self, user: CharacterController, target: CharacterController):
        damage = self.calculate_damage(user)
        target.receive_damage(damage)

    def apply_healing(self, user: CharacterController, target: CharacterController):
        healing = self.calculate_healing(user)
        target.receive_healing(healing)

    def summon_character(self, user: CharacterController):
        ...

    def calculate_damage(self, user: CharacterController):
        base_damage = self._ability.damage
        multiplier = user._character.multiplier_params.attack_multiplier or 1
        return base_damage * multiplier

    def calculate_healing(self, user: CharacterController):
        base_healing = self._ability.healing
        multiplier = user._character.multiplier_params.healing_multiplier or 1
        return base_healing * multiplier

    def increase_cooldown(self, cooldown: int = 1):
        self._cooldown += cooldown

    def decrease_cooldown(self, cooldown: int = 1):
        self._cooldown -= cooldown
        self._cooldown = max(self._cooldown, 0)

    def get_target_rule(self):
        return self._target

    @property
    def effect(self):
        return self._ability.effect

    @property
    def chance(self):
        return self._ability.chance

    @property
    def name(self):
        return self._ability.name

    @property
    def icon(self):
        return self._ability.icon

    @property
    def visual(self):
        return self._ability.visual

    @property
    def trigger_condition(self):
        return self._ability.trigger_condition

    @property
    def cooldown(self):
        return self._cooldown

    @property
    def description(self):
        return self._ability.description


class TargetType(enum.Enum):
    SELF = 'self'
    ENEMY = 'enemy'
    MATE = 'mate'

