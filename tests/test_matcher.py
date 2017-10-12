import pytest
from rere import frontend
from rere.compiler.nodes import *


RESULT_FAIL = 'fail'
RESULT_SUCCESS = 'success'


def run_machine(machine, input_data, return_mark=False):
    init_state, transitions = machine
    current_state = init_state

    for char in input_data:
        places_to_go_next = transitions.get(current_state, dict())
        if char not in places_to_go_next:
            return RESULT_FAIL
        current_state = places_to_go_next[char]

    what_left = transitions.get(current_state)
    if what_left.get('') is not None:
        return (
            (what_left.get('mark'), RESULT_SUCCESS) if
            return_mark else RESULT_SUCCESS
        )
    else:
        return RESULT_FAIL


def run_machine_with_mark(machine, input_data):
    init_state, transitions = machine
    current_state = init_state

    span_start = 0
    stack = list()
    print(transitions)

    for index, char in enumerate(input_data):
        current_state = transitions.get(current_state, dict()).get(char)

        if current_state is None:
            while stack:
                yield stack.pop()
            return index

        where_to_go = transitions.get(current_state, dict())
        if 'mark' in where_to_go:
            result = (where_to_go['mark'], span_start, index)
            if not stack:
                stack.append(result)
                span_start = index
                continue

            if stack[-1][0] == result[0]:
                old_mark, old_start, old_stop = stack.pop()
                new_res = (old_mark, old_start, index)
                stack.append(new_res)
            else:
                yield stack.pop()
                stack.append(result)

            span_start = index

    yield from stack


TEST_MATCH = [
    (
        Char('a'),
        [
            ('a', RESULT_SUCCESS),
            ('b', RESULT_FAIL),
            ('aa', RESULT_FAIL),
        ]
    ),

    (
        Sequence(Char('a'), Char('b')),
        [
            ('ab', RESULT_SUCCESS),
            ('ac', RESULT_FAIL),
            ('ba', RESULT_FAIL),
            ('abc', RESULT_FAIL),
        ]
    ),

    (
        Alternative(Char('a'), Char('b')),
        [
            ('a', RESULT_SUCCESS),
            ('b', RESULT_SUCCESS),
            ('aa', RESULT_FAIL),
            ('c', RESULT_FAIL),
        ]
    ),


    (
        Char('a') | Char('b'),
        [
            ('a', RESULT_SUCCESS),
            ('b', RESULT_SUCCESS),
            ('aa', RESULT_FAIL),
            ('c', RESULT_FAIL),
        ]
    ),

    (
        Word('h'),
        [
            ('h', RESULT_SUCCESS),
        ]
    ),

    (
        Word('hello world'),
        [
            ('hello world', RESULT_SUCCESS),
            ('hello worlt', RESULT_FAIL),
            ('hello worlda', RESULT_FAIL),
            ('some', RESULT_FAIL),
        ]
    ),

    (
        Word('hello world') | Word('hello world'),
        [
            ('hello world', RESULT_SUCCESS),
            ('hello worlt', RESULT_FAIL),
            ('hello worlda', RESULT_FAIL),
            ('some', RESULT_FAIL),
        ]
    ),

    (
        Word('hello') + Word('world'),
        [
            ('helloworld', RESULT_SUCCESS),
            ('helloworlt', RESULT_FAIL),
            ('helloworlda', RESULT_FAIL),
            ('some', RESULT_FAIL),
        ]
    ),

    (
        Plus(Char('a')),
        [
            ('a', RESULT_SUCCESS),
            ('b', RESULT_FAIL),
            ('123', RESULT_FAIL),
            ('aa', RESULT_SUCCESS),
            ('aaaaaaaaaaaaaaaaa', RESULT_SUCCESS),
            ('aaaaaaaaaaaaaaaaab', RESULT_FAIL),
        ]
    ),

    (
        Plus(Plus(Plus(Char('a')))),
        [
            ('a', RESULT_SUCCESS),
            ('b', RESULT_FAIL),
            ('123', RESULT_FAIL),
            ('aa', RESULT_SUCCESS),
            ('aaaaaaaaaaaaaaaaa', RESULT_SUCCESS),
            ('aaaaaaaaaaaaaaaaab', RESULT_FAIL),
        ]
    ),

    (
        Sequence(
            Plus(Plus(Plus(Char('a')))),
            Char('b')
        ),
        [
            ('ab', RESULT_SUCCESS),
            ('aaaaaaaaaaaaaaaaaaaaab', RESULT_SUCCESS),
            ('a'*8000, RESULT_FAIL),
            ('a'*8000 + 'b', RESULT_SUCCESS),
        ]
    ),

    (
        Alternative(Word('hello'), Word('helo')),
        [
            ('hello', RESULT_SUCCESS),
            ('helo', RESULT_SUCCESS),
            ('helllo', RESULT_FAIL),
            ('hellohello', RESULT_FAIL),
        ]
    ),

    (
        Alternative(
            Word('hello'), Word('world'),
            Plus(Word('kokoko')),
        ),
        [
            ('hello', RESULT_SUCCESS),
            ('world', RESULT_SUCCESS),
            ('kokoko', RESULT_SUCCESS),
            ('kokokokokoko', RESULT_SUCCESS),
            ('kokokokoko', RESULT_FAIL),
            ('hellohello', RESULT_FAIL),
            ('hellokokoko', RESULT_FAIL),
        ]
    ),

    (
        (
            Word('hello') | Word('world') |
            Plus(Word('kokoko'))
        ),
        [
            ('hello', RESULT_SUCCESS),
            ('world', RESULT_SUCCESS),
            ('kokoko', RESULT_SUCCESS),
            ('kokokokokoko', RESULT_SUCCESS),
            ('kokokokoko', RESULT_FAIL),
            ('hellohello', RESULT_FAIL),
            ('hellokokoko', RESULT_FAIL),
        ]
    ),

    (
        Plus(Alternative(Word('hello'), Word('helo'))),
        [
            ('hello', RESULT_SUCCESS),
            ('hellohello', RESULT_SUCCESS),
            ('helohellohello', RESULT_SUCCESS),
            ('helohellohelllo', RESULT_FAIL),
            ('helllo', RESULT_FAIL),
        ]
    ),

    # This case is totally pathological for backtrackers
    # (a+)*b+
    (
        Star(Plus(Char('a'))) + Plus(Char('b')),
        [
            ('ab', RESULT_SUCCESS),
            ('bbbbbbbbbbbbbbbbbbbbb', RESULT_SUCCESS),
            ('b', RESULT_SUCCESS),
            ('aaab', RESULT_SUCCESS),
            ('aaaaaaaaaaaaaaaaaaaab', RESULT_SUCCESS),
            ('aaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbb', RESULT_SUCCESS),
            ('a' * 800, RESULT_FAIL),
            ('a' * 800 + 'b' * 1500, RESULT_SUCCESS),
            ('aaaaaaaaaaaaaaaaaaaa', RESULT_FAIL),
            ('aaaaaaaabaaaaaaaaaaaa', RESULT_FAIL),
        ]
    ),

    (
        Repeat(Char('a'), 5),
        [
            ('a'*5, RESULT_SUCCESS),
            ('a'*4, RESULT_FAIL),
            ('a'*6, RESULT_FAIL),
            ('b'*5, RESULT_FAIL),
        ]
    ),

    (
        Repeat(Char('a'), 1),
        [
            ('a'*1, RESULT_SUCCESS),
            ('a'*2, RESULT_FAIL),
        ]
    ),

    (
        Char('a') * 5,
        [
            ('a'*5, RESULT_SUCCESS),
            ('a'*4, RESULT_FAIL),
            ('a'*6, RESULT_FAIL),
            ('b'*5, RESULT_FAIL),
        ]
    ),

    (
        Repeat(Word('python'), 3),
        [
            ('python'*3, RESULT_SUCCESS),
            ('python'*2, RESULT_FAIL),
            ('python'*3 + 'p', RESULT_FAIL),
        ]
    ),

    (
        Word('python') * 3,
        [
            ('python'*3, RESULT_SUCCESS),
            ('python'*2, RESULT_FAIL),
            ('python'*3 + 'p', RESULT_FAIL),
        ]
    ),

    (
        RepeatFromTo(Word('python'), 3, 7),
        [
            ('python'*8, RESULT_FAIL),
            ('python'*7, RESULT_SUCCESS),
            ('python'*4, RESULT_SUCCESS),
            ('python'*3, RESULT_SUCCESS),
            ('python'*2, RESULT_FAIL),
        ]
    ),

    (
        (
            Word('python') * 3 | Word('python') * 4 |
            Word('python') * 5 | Word('python') * 6 |
            Word('python') * 7
        ),
        [
            ('python'*8, RESULT_FAIL),
            ('python'*7, RESULT_SUCCESS),
            ('python'*4, RESULT_SUCCESS),
            ('python'*3, RESULT_SUCCESS),
            ('python'*2, RESULT_FAIL),
        ]
    ),

    (
        Maybe(Char('a')),
        [
            ('a', RESULT_SUCCESS),
            ('aa', RESULT_FAIL),
            ('b', RESULT_FAIL),
            ('', RESULT_SUCCESS),
        ]
    ),

    (
        Plus(Maybe(Char('a'))),
        [
            ('a', RESULT_SUCCESS),
            ('aaaa', RESULT_SUCCESS),
            ('b', RESULT_FAIL),
            ('', RESULT_SUCCESS),
        ]
    ),

    (
        Maybe(Plus(Word('hello'))),
        [
            ('hello', RESULT_SUCCESS),
            ('hellohello', RESULT_SUCCESS),
            ('', RESULT_SUCCESS),
            ('helloo', RESULT_FAIL),
        ]
    ),

    (
        Plus(Word('hello') | Plus(Word('more'))),
        [
            ('hello', RESULT_SUCCESS),
            ('hellohello', RESULT_SUCCESS),
            ('hellomoremorehello', RESULT_SUCCESS),
            ('', RESULT_FAIL),
        ]
    ),
]


TEST_MARK = [
    (
        Mark(Plus(Char('a')), 'foo'),
        [
            ('aaaa', [('foo', 0, 3)]),
            ('a', [('foo', 0, 0)]),
            ('', []),
        ]
    ),

    (
        Plus(Mark(Word('hello'), 'foo')),
        [
            ('hello', [('foo', 0, 4)]),
            ('hellohello', [('foo', 0, 4), ('foo', 4, 7)]),
        ]
    ),

#    (
#        Plus(Mark(Plus(Char('a')), 'foo') | Mark(Plus(Char('b')), 'bar')),
#        [
#            ('aaaa', [('foo', 0, 3)]),
#            ('bbb', [('bar', 0, 2)]),
#            ('aaabbb', [('foo', 0, 2), ('bar', 3, 5)]),
#        ]
#    ),
]


@pytest.mark.parametrize('regex,input_result', TEST_MATCH)
def test_matcher(regex, input_result):
    machine = frontend.build_regex_matcher(regex)
    for test_input, test_result in input_result:
        assert run_machine(machine, test_input) == test_result


@pytest.mark.parametrize('regex,input_result', TEST_MARK)
def test_mark(regex, input_result):
    machine = frontend.build_regex_matcher(regex)
    for test_input, test_result in input_result:
        assert list(run_machine_with_mark(machine, test_input)) == test_result


