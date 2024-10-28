from src.game_logic.models.models import Character, Ability, character_items


class CharacterController:
    def __init__(self, character: Character):
        self.character = character
        self.active_abilities: dict[int, AbilityController] = self.get_active_abilities()
        self.passive_abilities: list = self.get_passive_abilities()
        self.base_params = character.base_params.copy()
        self.log = []
        self.health = 0
        self.physical_damage = 0

    def attack(self, target: 'CharacterController', ability: Ability):
        damage = self.calculate_damage(ability)

        target.receive_damage(damage)

        self.log_action({
            'attack': f'{self.character.name} атаковал {target.character.name} с использованием {ability.name}, нанес урон: {damage}'
        })

    def use_passive_abilities(self):
        ...

    def receive_damage(self, damage: int):
        self.health -= damage
        self.log_action({'damage': f'{self.character.name} получил {damage} урона'})

    def receive_healing(self, health: int):
        self.health += health
        self.log_action({'healing': f'{self.character.name} восстановил {health} хп'})

    def apply_effect(self, effect, target: 'CharacterController'):
        effect.apply(target.character)
        self.log_action({'effect': f'{self.character.name} применил {effect.name} на {target.character.name}'})

    def calculate_damage(self, ability: Ability):
        return ability.damage * (self.character.multiplier_params.attack_multiplier or 1)

    def log_action(self, action_description: dict):
        self.log.append(action_description)

    def is_dead(self):
        return self.health <= 0

    def is_alive(self):
        return self.health > 0

    def get_battle_log(self):
        return self.log

    def get_active_abilities(self):
        result = {}
        for ability in self.character.subclass.abilities:
            result[ability.tier] = AbilityController(ability)
        return result

    def get_passive_abilities(self):
        result = []
        result.extend([AbilityController(ability) for ability in self.character.character_class.abilities])
        result.extend([AbilityController(ability) for ability in self.character.race.abilities])
        result.extend(AbilityController(ability) for ability in self.character.runes.abilities)
        return result


class AbilityController:
    def __init__(self, ability: Ability):
        self.ability = ability

    def execute(self, user: CharacterController, target: CharacterController):
        if self.is_successful():
            if self.ability.damage > 0:
                self.apply_damage(user, target)
            if self.ability.healing > 0:
                self.apply_healing(user, target)
            if self.ability.summoned_character:
                self.summon_character(user)
            self.log_action(user, target)
        else:
            self.log_action(user, target, success=False)


    def is_successful(self):
        import random
        return random.random() <= self.ability.chance


    def apply_damage(self, user: CharacterController, target: CharacterController):
        damage = self.calculate_damage(user)
        target.receive_damage(damage)


    def apply_healing(self, user: CharacterController, target: CharacterController):
        healing = self.calculate_healing(user)
        target.receive_healing(healing)


    def summon_character(self, user: CharacterController):
        ...


    def calculate_damage(self, user: CharacterController):
        base_damage = self.ability.damage
        multiplier = user.character.multiplier_params.attack_multiplier or 1
        return base_damage * multiplier


    def calculate_healing(self, user: CharacterController):

        base_healing = self.ability.healing
        multiplier = user.character.multiplier_params.healing_multiplier or 1
        return base_healing * multiplier


    def log_action(self, user: CharacterController, target: CharacterController, success=True):
        action_desc = {'action': f'{user.character.name} использовал {self.ability.name} на {target.character.name}.'}
        if success:
            if self.ability.damage > 0:
                action_desc['damage'] = f' Нанесено {self.ability.damage} урона.'
            if self.ability.healing > 0:
                action_desc['healing'] = f' Исцелено {self.ability.healing}.'
        else:
            action_desc['success'] = False

        user.log_action(action_desc)


class EffectController:
    def __init__(self):
        ...





