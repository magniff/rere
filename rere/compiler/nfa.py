import sys
from itertools import tee
from collections import namedtuple, defaultdict


from .nodes import Sequence, Char, Repeat, Alternative, EOS


MATCH_DIGIT = 'digit'
MATCH_ANY = 'any'


class MarkedState(int):

    def __hash__(self):
        return hash(int(self))

    def __eq__(self, other):
        return int(self) == int(other)

    def __repr__(self):
        return "%s(%s, %s)" % (
            type(self).__qualname__, int(self), self.caption
        )

    def __new__(cls, value, caption):
        instance = super().__new__(cls, value)
        instance.caption = caption
        return instance


class Epsilon(str):

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        return isinstance(other, type(self))



EPSILON = Epsilon('EPSILON')


NfaBuilderResult = namedtuple("NfaBuilderResult", "g_entry g_exit edges")
nfa_translators = sys.modules[__name__]


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def generate_entry_exit(pool):
    return next(pool), next(pool)


def states_pool():
    current_state = 0
    while True:
        yield current_state
        current_state += 1
    return


def build_nfa_for_regex(regex, pool=None, attach_eos=False):
    pool = pool or states_pool()
    if attach_eos:
        regex = Sequence(regex, EOS())

    builder = getattr(nfa_translators, 'build_%s' % type(regex).__qualname__)
    return builder(regex, pool)


def render_nfa_result(nfa_result):
    graph_entry, graph_exit, edges = nfa_result
    rendered_result = {
        'init_state': graph_entry, 'finish_state': graph_exit
    }

    rendered_result['transitions'] = defaultdict(lambda: defaultdict(list))
    for edge in edges:
        entry_point, exit_point, symbol = edge
        exit_list = rendered_result['transitions'][entry_point][symbol]
        exit_list.append(exit_point)

    # lets get rid of that pesky defaultdicts, hate them
    rendered_result['transitions'] = {
        key: dict(value) for key, value in
        rendered_result['transitions'].items()
    }

    return rendered_result


def build_Char(regex, pool):
    g_entry, g_exit = generate_entry_exit(pool)
    return NfaBuilderResult(
        g_entry=g_entry, g_exit=g_exit,
        edges=[
            (g_entry, g_exit, regex.char),
        ]
    )


def build_Digit(regex, pool):
    g_entry, g_exit = generate_entry_exit(pool)
    return NfaBuilderResult(
        g_entry=g_entry, g_exit=g_exit,
        edges=[
            (g_entry, g_exit, MATCH_DIGIT)
        ]
    )


def build_EOS(regex, pool):
    g_entry, g_exit = generate_entry_exit(pool)
    return NfaBuilderResult(
        g_entry=g_entry, g_exit=g_exit,
        edges=[
            (g_entry, g_exit, regex.char),
        ]
    )



def build_Alternative(regex, pool):
    g_entry, g_exit = generate_entry_exit(pool)
    edges = list()

    for choice in regex.alternatives:
        inner_result = build_nfa_for_regex(choice, pool)
        inner_entry, inner_exit, inner_edges = inner_result

        edges.append((g_entry, inner_entry, EPSILON))
        edges.append((inner_exit, g_exit, EPSILON))
        edges.extend(inner_edges)

    return NfaBuilderResult(g_entry, g_exit, edges)


def build_Sequence(regex, pool):

    if len(regex.sequence) == 1:
        return build_nfa_for_regex(regex.sequence[0], pool)

    edges = list()
    inner_results = list(
        build_nfa_for_regex(inner, pool) for inner in regex.sequence
    )
    first_op, *_, last_op = inner_results
    g_entry = first_op.g_entry
    g_exit = last_op.g_exit

    for first, second in pairwise(inner_results):
        _, first_exit, first_edges = first
        second_entry, _, second_edges = second
        edges.append((first_exit, second_entry, EPSILON))
        edges.extend(first_edges)
        edges.extend(second_edges)

    return NfaBuilderResult(g_entry, g_exit, edges)


def build_Star(regex, pool):
    g_entry, g_exit = generate_entry_exit(pool)
    inner_entry, inner_exit, inner_edges = build_nfa_for_regex(regex.inner, pool)
    edges = [
        (g_entry, inner_entry, EPSILON),
        (inner_exit, g_exit, EPSILON),
        (g_entry, g_exit, EPSILON),
        (inner_exit, inner_entry, EPSILON),
    ]
    edges.extend(inner_edges)
    return NfaBuilderResult(g_entry, g_exit, edges)


def build_Plus(regex, pool):
    g_entry, g_exit = generate_entry_exit(pool)
    inner_entry, inner_exit, inner_edges = build_nfa_for_regex(regex.inner, pool)
    edges = [
        (g_entry, inner_entry, EPSILON),
        (inner_exit, g_exit, EPSILON),
        (inner_exit, inner_entry, EPSILON),
    ]
    edges.extend(inner_edges)
    return NfaBuilderResult(g_entry, g_exit, edges)


def build_Maybe(regex, pool):
    g_entry, g_exit = generate_entry_exit(pool)
    inner_entry, inner_exit, inner_edges = build_nfa_for_regex(regex.inner, pool)
    edges = [
        (g_entry, inner_entry, EPSILON),
        (inner_exit, g_exit, EPSILON),
        (g_entry, g_exit, EPSILON),
    ]
    edges.extend(inner_edges)
    return NfaBuilderResult(g_entry, g_exit, edges)


def build_Word(regex, pool):
    return build_nfa_for_regex(
        regex=Sequence(*(Char(value) for value in regex.word)),
        pool=pool,
    )


def build_Repeat(regex, pool):
    repeat_what, repeat_times = regex.inner, regex.times
    return build_nfa_for_regex(
        Sequence(
            *(repeat_what for _ in range(repeat_times))
        ),
        pool=pool
    )


def build_RepeatFromTo(regex, pool):
    return build_nfa_for_regex(
        Alternative(*(
            Repeat(regex.inner, times=value) for value
            in range(regex.repeat_from, regex.repeat_to+1)
        )),
        pool=pool
    )


def build_Mark(regex, pool):
    g_entry, g_exit = generate_entry_exit(pool)
    g_exit = MarkedState(g_exit, regex.caption)

    inner_entry, inner_exit, inner_edges = build_nfa_for_regex(regex.inner, pool)
    edges = [
        (g_entry, inner_entry, EPSILON),
        (inner_exit, g_exit, EPSILON),
    ]
    edges.extend(inner_edges)

    return NfaBuilderResult(g_entry, g_exit, edges)

