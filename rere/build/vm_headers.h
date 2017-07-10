// Run this before running actual VM
void rpython_startup_code();


typedef struct{
    unsigned long long input;
    unsigned long long output;
    char value;
}RegexTransition;


typedef struct{
    unsigned long long regex_id;
    unsigned long long init_state;
    unsigned long long count;
    RegexTransition* transitions;
}Regex;


typedef struct{
    unsigned long long count;
    Regex* regex;
}RegexList;


typedef struct{
    unsigned long long regex_id;
    unsigned long long span_from;
    unsigned long long span_to;
}ResultItem;


typedef struct{
    unsigned long long count;
    ResultItem* result;
}ResultList;


ResultList* tokenize(
    RegexList* regex_list, char* input_string, long long input_len
);

