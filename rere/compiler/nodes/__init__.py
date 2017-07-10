import watch
from .nodes_lowlevel import (
    Char, Sequence, Alternative, Maybe, Plus, Star, EOS, Wrapper,
    BaseRegex, Mark
)


PositiveInt = watch.Pred(lambda value: isinstance(value, int) and value > 0)


class Word(BaseRegex):
    word = watch.builtins.InstanceOf(str)

    def __init__(self, word):
        self.word = word


class Repeat(Wrapper):
    times = PositiveInt

    def __init__(self, inner, times):
        super().__init__(inner)
        self.times = times


class RepeatFromTo(Wrapper):
    repeat_from = PositiveInt
    repeat_to = PositiveInt

    def __init__(self, inner, repeat_from, repeat_to):
        super().__init__(inner)
        self.repeat_from = repeat_from
        self.repeat_to = repeat_to


class Digit(BaseRegex):
    pass


class Any(BaseRegex):
    pass


class Range(BaseRegex):
    pass

