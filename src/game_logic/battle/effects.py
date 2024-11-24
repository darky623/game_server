from typing import Type

from src.game_logic.battle.battle import BattleEvent


class BaseEffect:
    name: str = 'base_effect'
    lifetime = 10
    def __init__(self, target, *args, **kwargs):
        self._target = target
        self.lifetime = kwargs.get('lifetime', self.lifetime)
        self.description = kwargs.get('description', '')
        self.icon = kwargs.get('icon', '#')

    def decrease_lifetime(self):
        self.lifetime -= 1
        return self.lifetime

    def increase_lifetime(self):
        self.lifetime += 1
        return self.lifetime

    def serialize(self):
        return {
            'title': self.name,
            'description': self.description,
            'icon': self.icon,
            'cooldown': self.lifetime,

        }


class StartEndEffect(BaseEffect):
    def apply_start(self):
        raise NotImplementedError

    def apply_end(self):
        raise NotImplementedError

class CycleEffect(BaseEffect):
    def apply(self):
        if self.lifetime > 0:
            result = self._apply()
            self.decrease_lifetime()
            return result

    def _apply(self):
        raise NotImplementedError


class Bleeding(CycleEffect):
    damage: int = 0
    name: str = 'bleeding'
    def __init__(self, target, *args, **kwargs):
        super().__init__(target, *args, **kwargs)
        self.damage = kwargs.get('damage', self.damage)

    def _apply(self):
        self._target.receive_damage(self.damage)


class Paralysis(StartEndEffect):
    name: str = 'paralysis'
    def apply_start(self):
        self._target.paralyzed = True

    def apply_end(self):
        self._target.paralyzed = False


class BuffEffect(StartEndEffect):
    ...


class DeBuffEffect(StartEndEffect):
    ...


class ShieldEffect(StartEndEffect):
    ...


class Immunity:
    def __init__(self, effect: Type[BaseEffect], lifetime: int = 1):
        self._effect: Type[BaseEffect] = effect
        self._lifetime = lifetime

    def decrease_lifetime(self):
        self._lifetime -= 1
        return self.lifetime

    def increase_lifetime(self):
        self._lifetime += 1
        return self.lifetime

    @property
    def effect(self):
        return self._effect

    @property
    def lifetime(self):
        return self._lifetime

    @lifetime.setter
    def lifetime(self, lifetime):
        self._lifetime = lifetime


class EffectManager:
    def __init__(self):
        self._effects: set[BaseEffect] = set()
        self._immunities: set[Immunity] = set()

    def add_effect(self, effect):
        for immunity in self._immunities:
            if isinstance(effect, immunity.effect):
                return False
        self._effects.add(effect)

    def add_immunity(self, immunity):
        self._immunities.add(immunity)
        self.__remove_by_immunity(immunity)

    def remove_immunity(self, immunity):
        self._immunities.remove(immunity)

    def remove_effect(self, effect):
        self._effects.discard(effect)

    def __remove_ended(self):
        to_remove = []
        for effect in self._effects:
            if effect.lifetime <= 0:
                to_remove.append(effect)
        for immunity in self._immunities:
            if immunity.lifetime <= 0:
                to_remove.append(immunity)
        for effect in to_remove:
            self.remove_effect(effect)
            self.remove_immunity(effect)

    def __remove_by_immunity(self, immunity):
        to_remove = []
        for effect in self._effects:
            if isinstance(effect, immunity.effect):
                to_remove.append(effect)
        for effect in to_remove:
            self.remove_effect(effect)

    def update(self, event: BattleEvent = BattleEvent.NEW_ROUND):
        if event == BattleEvent.NEW_ROUND:
            for effect in self._effects:
                if isinstance(effect, CycleEffect):
                    effect.apply()
                if isinstance(effect, StartEndEffect):
                    if effect.lifetime <= 0:
                        effect.apply_end()
            for immunity in self._immunities:
                immunity.decrease_lifetime()
        self.__remove_ended()

    @property
    def immunities(self):
        return self._immunities

    @property
    def effects(self):
        return self._effects


effects_dict = {
    'bleeding': Bleeding,
    'paralyzed': Paralysis,
    'buff': BuffEffect,
    'debuff': DeBuffEffect,
    'shield': ShieldEffect,
    'immunity': Immunity
}