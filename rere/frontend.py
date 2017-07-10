from .compiler.nfa import build_nfa_for_regex, render_nfa_result
from .compiler.dfa import clusterize_states, remap_states


RESULT_FAIL = 'fail'
RESULT_SUCCESS = 'success'


def build_regex_matcher(regex):
    return remap_states(
        clusterized_states_iterator=clusterize_states(
            graph=render_nfa_result(
                nfa_result=build_nfa_for_regex(
                    regex, attach_eos=True
                )
            )
        )
    )

