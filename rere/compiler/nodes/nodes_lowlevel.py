import watch


class BaseRegex(watch.WatchMe):

    def __add__(self, other):
        return Sequence(self, other)

    def __mul__(self, value):
        return Sequence(*(self for _ in range(value)))

    def __or__(self, other):
        return Alternative(self, other)



class Char(BaseRegex):
    char = watch.Pred(
        lambda value: isinstance(value, str) and len(value) == 1
    )

    def __init__(self, char):
        self.char = char


class EOS(BaseRegex):
    char = watch.builtins.EqualsTo('')

    def __init__(self):
        self.char = ''


class Alternative(BaseRegex):
    alternatives = watch.ArrayOf(watch.builtins.InstanceOf(BaseRegex))

    def __init__(self, *alternatives):
        self.alternatives = alternatives


class Sequence(BaseRegex):
    sequence = watch.CombineFrom(
        watch.ArrayOf(watch.builtins.InstanceOf(BaseRegex)),
        watch.Pred(lambda array: bool(array))
    )

    def __init__(self, *sequence):
        self.sequence = sequence


class Wrapper(BaseRegex):
    inner = watch.builtins.InstanceOf(BaseRegex)

    def __init__(self, inner):
        self.inner = inner


class Star(Wrapper):
    pass


class Plus(Wrapper):
    pass


class Maybe(Wrapper):
    pass


class Mark(Wrapper):
    caption = watch.builtins.InstanceOf(str)

    def __init__(self, inner, caption):
        super().__init__(inner)
        self.caption = caption

