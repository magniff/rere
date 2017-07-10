# coding: utf8
# WARNING: This file is RPython, be aware.


import os
from rpython.rlib.entrypoint import entrypoint_highlevel
from rpython.rlib.runicode import str_decode_utf_8
from rpython.rtyper.lltypesystem import rffi, lltype


RegexTransition = rffi.CStruct(
    'RegexTransition',
    ('input', rffi.ULONGLONG),
    ('output', rffi.ULONGLONG),
    ('value', rffi.CHAR),
)


Regex = rffi.CStruct(
    'Regex',
    ('regex_id', rffi.ULONGLONG),
    ('init_state', rffi.ULONGLONG),
    ('count', rffi.ULONGLONG),
    ('transitions', lltype.Ptr(rffi.CArray(RegexTransition))),
)


rlist = rffi.CStruct(
    'RegexList',
    ('count', rffi.ULONGLONG),
    ('regex', lltype.Ptr(rffi.CArray(Regex))),
)


RegexList = lltype.Ptr(rlist)


ResultItem = lltype.Struct(
    'ResultItem',
    ('regex_id', rffi.ULONGLONG),
    ('span_from', rffi.ULONGLONG),
    ('span_to', rffi.ULONGLONG),
)


ResultList = lltype.Ptr(
    lltype.Struct(
        'ResultList',
        ('count', rffi.ULONGLONG),
        ('result', lltype.Ptr(lltype.Array(ResultItem))),
    )
)


def run_token(token, input_data, index):
    pass


def run_tokenizer(regex_list, input_data):

    input_counter = 0
    tokens = list()

    while input_counter < len(input_data):
        for token_name, regex in regex_list:
            result, index = run(regex, input_data, index)
            if result == True:
                tokens.append((token_name, input_counter, index))
                input_counter = index
            else:
                continue

    return tokens


def unpack_transitions_list(regex):
    unpacked_transitions = {}

    for index in range(regex.count):
        current_transition = regex.transitions[index]
        paths_with_this_input = unpacked_transitions.get(
            current_transition.input, {}
        )
        paths_with_this_input[current_transition.value] = current_transition.output
        unpacked_transitions[current_transition.input] = paths_with_this_input

    return unpacked_transitions


def unpack_regex_list(regex_list):
    unpacked_result = []

    for index in range(regex_list.count):
        current_regex = regex_list.regex[index]
        unpacked_result.append(
            (
                current_regex.regex_id,
                current_regex.init_state,
                unpack_transitions_list(current_regex),
            )
        )

    return unpacked_result


@entrypoint_highlevel(
    key='main', c_name='tokenize',
    argtypes=[RegexList, rffi.CCHARP, rffi.LONGLONG]
)
def tokenize(regex_list, input_bytes, input_len):
    input_string = rffi.charp2strn(input_bytes, input_len)
    return 0


def main(args):
    return 0


def target(*args):
    return main, None

