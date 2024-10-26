from random import random
import random
from src.game_logic.models.models import Character, Ability, character_items, SummandParams


class CharacterController:
    def __init__(self, character: Character):
        self._character = character
        self.active_abilities: dict[int, AbilityController] = self.__get_active_abilities()
        self.passive_abilities: list[AbilityController] = self.__get_passive_abilities()
        self.base_params: SummandParams = self.__calculate_base_params()

        self.teammates = []
        self.enemies = []

        self.max_health = self.base_params.vitality
        self.health = self.max_health
        self.physical_damage = self.base_params.damage
        self.evasion = self.base_params.evasion
        self.resistance = self.base_params.resistance
        self.speed = self.base_params.speed

        self.effects = []

    def attack(self):
        target = self.__choose_target()
        ability_to_use = self.__get_ability_to_attack()
        if not ability_to_use:
            result = self.physical_attack(target)
        else: result = self.ability_attack(ability_to_use, target)

        return result

    def physical_attack(self, target: 'CharacterController'):
        damage = self.calculate_damage()
        result = target.receive_damage(damage)
        return result

    def ability_attack(self, ability: 'AbilityController', target: 'CharacterController'):
        action = ability.execute(self, target)
        return action

    def use_passive_abilities(self):
        result = []
        for ability in self.passive_abilities:
            result.append(ability.execute(self, None))

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

    def apply_effect(self, effect, target: 'CharacterController'):
        effect.apply(target._character)

    def calculate_damage(self):
        return self.physical_damage

    def is_dead(self):
        return self.health <= 0

    def is_alive(self):
        return self.health > 0

    def round_update(self):
        self.__decrease_cooldowns()
        self.use_passive_abilities()

    def __get_ability_to_attack(self):
        for ability in self.active_abilities.values():
            if random() < ability.get_chance() and ability.cooldown == 0:
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
        result.extend(AbilityController(ability) for ability in self._character.runes.abilities)
        return result

    def __choose_target(self) -> 'CharacterController':
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
                   self._character.subclass.summand_params)
        result += sum([item.summand_params for item in self._character.items])
        for item in self._character.items:
            result *= item.multiplier_params

        return result

    def __decrease_cooldowns(self):
        for ability in self.active_abilities.values():
            ability.decrease_cooldown()
        for ability in self.passive_abilities:
            ability.decrease_cooldown()

    def set_teammates(self, teammates: list['CharacterController']):
        self.teammates = teammates

    def set_enemies(self, enemies: list['CharacterController']):
        self.enemies = enemies


class AbilityController:
    def __init__(self, ability: Ability):
        self._ability = ability
        self.cooldown = 0

    def execute(self, user: CharacterController, target: CharacterController):
        action = {'ability_name': self._ability.name}


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

    def log_action(self, user: CharacterController, target: CharacterController, success=True):
        action_desc = {'action': f'{user._character.name} использовал {self._ability.name} на {target._character.name}.'}
        if success:
            if self._ability.damage > 0:
                action_desc['damage'] = f' Нанесено {self._ability.damage} урона.'
            if self._ability.healing > 0:
                action_desc['healing'] = f' Исцелено {self._ability.healing}.'
        else:
            action_desc['success'] = False

        user.log_action(action_desc)

    def increase_cooldown(self, cooldown: int = 1):
        self.cooldown += cooldown

    def decrease_cooldown(self, cooldown: int = 1):
        self.cooldown -= cooldown
        self.cooldown = max(self.cooldown, 0)

    def get_chance(self):
        return self._ability.chance


class EffectController:
    def __init__(self):
        ...


