
class BaseEffect:
    def __init__(self, target):
        self._target = target


class StartEndEffect(BaseEffect):
    def apply_start(self):
        raise NotImplementedError

    def apply_end(self):
        raise NotImplementedError

class CycleEffect(BaseEffect):
    def apply(self):
        raise NotImplementedError


class Bleeding(CycleEffect):
    def __init__(self, target, *args):
        super().__init__(target)
        self.damage = args[0]

    def apply(self):
        self._target.receive_damage(self.damage)


class Paralysis(StartEndEffect):
    ...


class BuffEffect(StartEndEffect):
    ...


class DeBuffEffect(StartEndEffect):
    ...


class ShieldEffect(StartEndEffect):
    ...


effects_dict = {
    'bleeding': Bleeding,
    'paralyzed': Paralysis,
    'buff': BuffEffect,
    'debuff': DeBuffEffect,
    'shield': ShieldEffect
}