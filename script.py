from _rere import lib, ffi
from rere.frontend import build_regex_matcher
from rere.compiler.nodes import *


lib.rpython_startup_code()


tokens = [
    (0, Word('hello world')),
    (1, Word('more stuff')),
]

def compile_tokens(tokens):
    for token_name, token in tokens:
        yield (token_name, build_regex_matcher(token))


def unpack_token_transitions(transitions_dict):
    for in_node, description in transitions_dict.items():
        for sym, out_node in description.items():
            yield in_node, out_node, sym


def build_ll_token_transitions(transitions):
    edges = list(unpack_token_transitions(transitions))
    ll_edges = ffi.new('RegexTransition[]', len(edges))

    for edge, ll_edge in zip(edges, ll_edges):
        in_node, out_node, sym = edge
        ll_edge.input = in_node
        ll_edge.output = out_node
        ll_edge.value = sym.encode() or b'\00'

    return len(ll_edges), ll_edges


def build_ll_token_repr(tokens):
    ll_regex_list = ffi.new('RegexList *')
    ll_regexes = ffi.new('Regex[]', len(tokens))
    ll_regex_list.regex = ll_regexes
    ll_regex_list.count = len(tokens)

    for (token_id, hl_token), ll_token in zip(tokens, ll_regexes):
        token_init, transitions = build_regex_matcher(hl_token)
        transitions_count, ll_transitions = build_ll_token_transitions(transitions)

        ll_token.transitions = ll_transitions
        ll_token.init_state = token_init
        ll_token.count = transitions_count
        ll_token.regex_id = token_id

    return ll_regex_list


word = b'more stuff there'
lib.tokenize(
    build_ll_token_repr(tokens), word, len(word)
)

