# coding: utf8
# WARNING: This file is RPython, be aware.


import os
from collections import namedtuple

from rpython.rlib.entrypoint import entrypoint_highlevel
from rpython.rlib.runicode import str_decode_utf_8
from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform


RESULT_FAIL = 1
RESULT_SUCCESS = 0


Token = namedtuple('Token', 'token_id start end status')
INVALID_NEXT_STATE = -1


eci = ExternalCompilationInfo(
    includes=['vm_headers.h',],
    include_dirs=['/home/magniff/workspace/rere/rere/build',]
)


RegexTransition = rffi_platform.Struct(
    'RegexTransition',
    [
        ('input', rffi.ULONGLONG),
        ('output', rffi.ULONGLONG),
        ('value', rffi.CHAR),
    ]
)


Regex = rffi_platform.Struct(
    'Regex',
    [
        ('regex_id', rffi.ULONGLONG),
        ('init_state', rffi.ULONGLONG),
        ('count', rffi.ULONGLONG),
        ('transitions', rffi.VOIDP),
    ]
)


RegexList = rffi_platform.Struct(
    'RegexList',
    [
        ('count', rffi.ULONGLONG),
        ('regex', rffi.VOIDP),
    ]
)


class Config:
    _compilation_info_ = eci
    regex_transition = RegexTransition
    regex = Regex
    regex_list = RegexList


config = rffi_platform.configure(Config())


def run_machine(machine, input_data):
    token_id, init_state, transitions = machine
    current_state = init_state

    for char in input_data:
        places_to_go_next = transitions.get(current_state, {})
        if char not in places_to_go_next:
            return RESULT_FAIL
        current_state = places_to_go_next[char]

    what_left = transitions.get(current_state, {})

    next_state = what_left.get(chr(0), INVALID_NEXT_STATE)
    if next_state != INVALID_NEXT_STATE:
        return RESULT_SUCCESS
    else:
        return RESULT_FAIL


def run_several(tokens, input_data):
    for token in tokens:
        token_id, init_state, transitions = token
        print(token_id, run_machine(token, input_data))
    return 0


ArrayOfTransitions = rffi.CArrayPtr(config['regex_transition'])
def unpack_transitions_list(regex):
    unpacked_transitions = {}

    transitions = rffi.cast(ArrayOfTransitions, regex.c_transitions)
    for index in range(regex.c_count):
        current_transition = transitions[index]
        paths_with_this_input = unpacked_transitions.get(
            current_transition.c_input, {}
        )

        paths_with_this_input[current_transition.c_value] = current_transition.c_output
        unpacked_transitions[current_transition.c_input] = paths_with_this_input

    return unpacked_transitions


ArrayOfRegex = rffi.CArrayPtr(config['regex'])
def unpack_regex_list(regex_list):
    unpacked_result = []

    regexes = rffi.cast(ArrayOfRegex, regex_list.c_regex)
    for index in range(regex_list.c_count):
        current_regex = regexes[index]

        unpacked_result.append(
            (
                current_regex.c_regex_id,
                current_regex.c_init_state,
                unpack_transitions_list(current_regex),
            )
        )

    return unpacked_result


@entrypoint_highlevel(
    key='main', c_name='tokenize',
    argtypes=[lltype.Ptr(config['regex_list']), rffi.CCHARP, rffi.LONGLONG]
)
def tokenize(regex_list, input_bytes, input_len):
    input_string = rffi.charp2strn(input_bytes, input_len)
    return run_several(unpack_regex_list(regex_list), input_string)


def main(args):
    return 0


def target(*args):
    return main, None

