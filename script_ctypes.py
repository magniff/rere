import ctypes
from rere.frontend import build_regex_matcher
from rere.compiler.nodes import *


lib = ctypes.cdll.LoadLibrary("./rere/build/librere.so")


class RegexTransition(ctypes.Structure):
    _fields_ = [
        ('input', ctypes.c_ulonglong),
        ('output', ctypes.c_ulonglong),
        ('value', ctypes.c_char),
    ]


class Regex(ctypes.Structure):
    _fields_ = [
        ('regex_id', ctypes.c_ulonglong),
        ('init_state', ctypes.c_ulonglong),
        ('count', ctypes.c_ulonglong),
        ('transitions', ctypes.POINTER(RegexTransition))
    ]


class RegexList(ctypes.Structure):
    _fields_ = [
        ('count', ctypes.c_ulonglong),
        ('regex', ctypes.POINTER(Regex))
    ]


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
    ll_edges = (RegexTransition * len(edges))()

    for edge, ll_edge in zip(edges, ll_edges):
        in_node, out_node, sym = edge
        ll_edge.input = in_node
        ll_edge.output = out_node
        ll_edge.value = sym.encode() or b'\00'

    return len(ll_edges), ll_edges


def build_ll_token_repr(tokens):
    ll_regex_list = RegexList()
    ll_regex_array = (Regex * len(tokens))()

    ll_regex_list.count = len(tokens)
    ll_regex_list.regex = ll_regex_array

    for (token_id, hl_token), ll_token in zip(tokens, ll_regex_array):
        token_init, transitions = build_regex_matcher(hl_token)
        transitions_count, ll_transitions = build_ll_token_transitions(transitions)

        ll_token.transitions = ll_transitions
        ll_token.init_state = token_init
        ll_token.count = transitions_count
        ll_token.regex_id = token_id

    return ctypes.pointer(ll_regex_list)


lib.rpython_startup_code()
lib.tokenize(
    build_ll_token_repr(tokens),
    ctypes.c_char_p(b'he'),
    ctypes.c_ulonglong(2)
)
