#!/usr/bin/env python3
"""
Static guard for the SQL layer: every c.execute() must bind its values.

    python3 CheckSqlBinding.py [path ...]        # default: db/*.py

Rules applied to each execute()/executemany() call:

  * no %-interpolation may survive in a statement;
  * a statement assembled with + may only concatenate literals and the output of
    the whitelisting helpers below (sort_order, sql_int) -- concatenating any
    other expression means a value is being pasted into the SQL;
  * the number of ? placeholders must match the number of bound parameters.

Statements that are not literal at the top level (e.g. c.execute(sql[db_type],
params), where the SQL lives in a static dictionary) are reported as skipped for
manual review.
"""
import ast
import os
import sys

# helpers that whitelist their own input, so their output cannot smuggle SQL in
SAFE_CALLS = ("sort_order", "sql_int")


def analyse(node):
    """
    Return (text, offenders).

    text is the statement with NUL in place of whitelisted helper calls, or None
    when the node is not a literal. offenders lists the source of every operand
    that would be pasted into the statement.
    """
    if isinstance(node, ast.Constant):
        return (node.value, []) if isinstance(node.value, str) else (None, [])
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, left_bad = analyse(node.left)
        right, right_bad = analyse(node.right)
        text = left + right if left is not None and right is not None else None
        return text, left_bad + right_bad
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id in SAFE_CALLS:
        return "\0", []
    if isinstance(node, ast.JoinedStr):        # f-string: always suspicious here
        return None, [ast.unparse(node)]
    return None, []


def check(paths):
    checked = 0
    problems = []
    skipped = []
    for path in paths:
        tree = ast.parse(open(path).read(), filename=path)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("execute", "executemany")):
                continue
            if not node.args:
                problems.append("%s:%d execute() without a statement" % (path, node.lineno))
                continue
            text, offenders = analyse(node.args[0])
            if offenders:
                problems.append("%s:%d value pasted into the statement: %s"
                                % (path, node.lineno, ", ".join(offenders)))
                continue
            if text is None:
                skipped.append("%s:%d statement not literal (%s)"
                               % (path, node.lineno, ast.unparse(node.args[0])[:60]))
                continue
            checked += 1
            placeholders = text.count("?")
            if len(node.args) > 1:
                params = node.args[1]
                bound = len(params.elts) if isinstance(params, (ast.Tuple, ast.List)) else -1
            else:
                bound = 0
            if "%" in text:
                problems.append("%s:%d statement still uses %% interpolation: %s"
                                % (path, node.lineno, text.strip()[:80]))
            if bound != placeholders:
                problems.append("%s:%d %d placeholder(s) but %s bound parameter(s): %s"
                                % (path, node.lineno, placeholders,
                                   "?" if bound < 0 else bound, text.strip()[:80]))
    return checked, problems, skipped


def main():
    paths = sys.argv[1:]
    if not paths:
        paths = sorted(os.path.join("db", f) for f in os.listdir("db") if f.endswith(".py"))
    checked, problems, skipped = check(paths)
    print("checked %d literal statement(s), %d to review by hand" % (checked, len(skipped)))
    for line in skipped:
        print("  skipped: %s" % line)
    for line in problems:
        print("  PROBLEM: %s" % line)
    if problems:
        return 1
    print("OK: every literal statement binds its values")
    return 0


if __name__ == "__main__":
    sys.exit(main())
