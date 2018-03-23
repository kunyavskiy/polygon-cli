import ast
import re

def get_decimal_or_variable_value(token, variables):
    if (token.isdecimal()):
        return int(token)
    assert(token in variables)
    return variables[token]


def parse_freemarker_assign_expr(full_expr, variables):
    full_expr = full_expr.decode("ascii")
    pos_eq = full_expr.find("=")
    assert(pos_eq != -1)
    var = full_expr[: pos_eq].strip()
    assert(re.search(r"^\w+$", var))

    expr = full_expr[pos_eq + 1:].strip()
    pos = 0

    # TODO: Replace my parser by parser from ast

    ops = [
            {
                "+": lambda x, y: x + y,
                "-": lambda x, y: x - y
            },
            {
                "*": lambda x, y: x * y,
                "/": lambda x, y: x // y
            }
        ]

    def skip_spaces():
        nonlocal pos
        while pos < len(expr) and expr[pos].isspace():
            pos += 1

    def parse_binary(lvl):
        nonlocal pos
        if lvl == 2:
            return parse_unary()

        ret = parse_binary(lvl + 1)
        while True:
            if pos == len(expr) or not expr[pos] in ops[lvl]:
                skip_spaces()
                return ret

            f = ops[lvl][expr[pos]]
            pos += 1
            skip_spaces()

            tmp = parse_binary(lvl + 1)

            ret = f(ret, tmp)

    def parse_unary():
        nonlocal pos
        assert(pos < len(expr))
        if expr[pos] == "(":
            pos += 1
            skip_spaces()
            ret = parse_binary(0)
            assert(expr[pos] == ")")
            pos += 1
            skip_spaces()
            return ret

        if expr[pos] == "-":
            pos += 1
            skip_spaces()
            return -parse_unary()

        token = ""
        while pos < len(expr) and not expr[pos].isspace():
            token += expr[pos]
            pos += 1

        skip_spaces()
        return get_decimal_or_variable_value(token, variables)

    val = parse_binary(0)
    
    assert(pos == len(expr))

    return [var, val]


def parse_freemarker_list_as(s, variables):
    s = s.decode("ascii").strip()
    match = re.search(r"(.*)\bas\b(.*)", s)
    assert(match)
    arr, var = map(lambda x: x.strip(), match.groups())
    assert(re.search(r"^\w+$", var))
    if ".." in arr:
        assert(arr.count("..") == 1)
        left_part, right_part = map(lambda x: x.strip(), arr.split(".."))
        from_value = get_decimal_or_variable_value(left_part, variables)
        to_value = get_decimal_or_variable_value(right_part, variables)
        assert(from_value <= to_value)
        return [var, range(from_value, to_value + 1)]

    assert(arr[0] == "[" and arr[-1] == "]")
    ret = ast.literal_eval(arr)
    return [var, ret]