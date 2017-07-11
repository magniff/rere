// Run this before running actual VM
void rpython_startup_code();


typedef struct{
    unsigned long long c_input;
    unsigned long long c_output;
    char c_value;
}RegexTransition;


typedef struct{
    unsigned long long c_regex_id;
    unsigned long long c_init_state;
    unsigned long long c_count;
    RegexTransition* c_transitions;
}Regex;


typedef struct{
    unsigned long long c_count;
    Regex* c_regex;
}RegexList;


int tokenize(
    RegexList* regex_list, char* input_string, long long input_len
);

