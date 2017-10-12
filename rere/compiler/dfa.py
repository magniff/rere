from collections import deque, defaultdict
from .nfa import EPSILON, MarkedState


def follow_epsilon(transitions, node_id, visited=None):
    visited = visited or list()
    visited.append(node_id)

    yield node_id
    epsilon_for_this_node = transitions.get(node_id, dict()).get(EPSILON, list())
    for node in epsilon_for_this_node:
        if node in visited:
            continue
        yield from follow_epsilon(transitions, node, visited)


def extract_alphabet(transitions):
    for transition_dict in transitions.values():
        for symbol in transition_dict.keys():
            yield symbol


def follow_epsilon_for_set(transitions, exit_state, state_set):
    for state in state_set:
        if state != exit_state:
            yield from follow_epsilon(transitions, state)


def clusterize_states(graph):
    init_state = graph['init_state']
    finish_state = graph['finish_state']
    transitions = graph['transitions']

    alphabet = set(extract_alphabet(transitions)) - set([EPSILON])

    queue = deque()
    visited = list()

    queue.append(set([init_state]))
    while queue:
        # take first in queue and saturate it with epsilon reachable
        current_state_set = queue.popleft()
        current_state_set |= set(
            follow_epsilon_for_set(
                transitions, finish_state, current_state_set
            )
        )

        if current_state_set in visited:
            continue

        # just iterate over the alphabet to clusterize states and build edges
        for symbol in alphabet:
            state_set_for_symbol = set()
            for state in current_state_set:
                if state != finish_state:
                    states_to_go_next = transitions[state].get(symbol, tuple())
                    state_set_for_symbol |= set(tuple(states_to_go_next))

            # if set is not empty then yield it
            if state_set_for_symbol:
                if state_set_for_symbol not in visited:
                    queue.append(state_set_for_symbol)

                state_set_for_symbol |= set(
                    follow_epsilon_for_set(
                        transitions, finish_state, state_set_for_symbol
                    )
                )

                yield (
                    frozenset(current_state_set),
                    frozenset(state_set_for_symbol),
                    symbol
                )

        visited.append(current_state_set)


def fetch_mark_from_set(state_set):
    marked_states = [
        state for state in state_set if isinstance(state, MarkedState)
    ]

    if len(marked_states) > 1:
        raise ValueError("Too many marked states in set %s" % state_set)

    return None if not marked_states else marked_states[0].caption



def remap_states(clusterized_states_iterator):
    marks = dict()

    states_map = defaultdict(lambda: len(states_map))
    remaped_states = defaultdict(dict)

    # lets examine the very first edge, its input should be considered as a
    # machine init state
    global_init, first_seen_out, symbol = next(clusterized_states_iterator)
    remaped_states[states_map[global_init]][symbol] = states_map[first_seen_out]
    marks[states_map[first_seen_out]] = fetch_mark_from_set(first_seen_out)

    for st_in, st_out, symbol in clusterized_states_iterator:
        remaped_states[states_map[st_in]][symbol] = states_map[st_out]
        marks[states_map[st_out]] = fetch_mark_from_set(st_out)

    for state, mark in marks.items():
        if mark is None:
            continue
        remaped_states[state]['mark'] = mark

    return states_map[global_init], dict(remaped_states)

