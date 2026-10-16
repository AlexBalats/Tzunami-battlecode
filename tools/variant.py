"""Make a parameter variant of a single-file bot, for the arena.

Usage (from the repo root):
    python -I tools/variant.py SRC_BOT NAME KEY=VALUE [KEY=VALUE ...]
    python -I tools/variant.py --from-snapshot bots/_snap-strat-2b8ec86 NAME KEY=VALUE [...]

Copies bots/SRC_BOT/src/main.py (and pyrightconfig.json) to bots/_var-NAME/ (git-ignored) and
rewrites assignments in that one file. Then: python -I tools/arena.py _var-NAME OTHER_BOT

    KEY=VALUE        the first line `KEY = ...` (any indentation: lazy parts are indented inside
                     their _lazy_ function) becomes `KEY = VALUE`, indentation and trailing comment
                     kept. A multi-line right-hand side is replaced whole.
    DICT.ENTRY=VALUE the entry ENTRY of the dict literal assigned by the first `DICT = ...` line,
                     written as dict(ENTRY=...) or {"ENTRY": ...}; e.g. INT_ON.HUNT=True.

VALUE is Python source, pasted verbatim (quote strings: MEM_VARIANT='"B"'). Fails loudly when a
key is not found, and when the rewritten file no longer compiles. Prints the new bot name.
"""
import argparse
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOTS = os.path.join(ROOT, "bots")
OPEN, CLOSE = "([{", ")]}"


def fail(msg):
    sys.exit("variant: " + msg)


def scan_expr(src, i):
    """Index just past the expression starting at src[i]: stop at a top-level ',' or closing bracket or
    (at depth 0) a newline / '#'. Skips strings."""
    depth = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c in "\"'":
            q = src[i:i + 3] if src[i:i + 3] in ('"""', "'''") else c
            j = src.find(q, i + len(q))
            while j != -1 and len(q) == 1 and src[j - 1] == "\\":
                j = src.find(q, j + 1)
            if j == -1:
                fail("unterminated string at offset %d" % i)
            i = j + len(q)
            continue
        if c == "#" and depth == 0:
            return i
        if c == "#":
            i = src.find("\n", i)
            if i == -1:
                return n
            continue
        if c in OPEN:
            depth += 1
        elif c in CLOSE:
            if depth == 0:
                return i
            depth -= 1
        elif c == "," and depth == 0:
            return i
        elif c == "\n" and depth == 0 and src[i - 1] != "\\":
            return i
        i += 1
    return n


def find_assign(src, key):
    m = re.search(r"^([ \t]*)%s[ \t]*=(?!=)[ \t]*" % re.escape(key), src, re.M)
    if not m:
        fail("no line `%s = ...` found" % key)
    return m


def set_top(src, key, value):
    m = find_assign(src, key)
    start = m.end()
    end = scan_expr(src, start)
    rhs = src[start:end].rstrip()
    end = start + len(rhs)
    print("  %s: %s -> %s" % (key, " ".join(rhs.split())[:60], value))
    return src[:start] + value + src[end:]


def set_entry(src, key, entry, value):
    m = find_assign(src, key)
    start = m.end()
    end = scan_expr(src, start)
    body = src[start:end]
    pat = re.compile(r"(?<![\w.])%s[ \t]*=(?!=)[ \t]*|[\"']%s[\"'][ \t]*:[ \t]*" % (re.escape(entry), re.escape(entry)))
    em = pat.search(body)
    if not em:
        fail("no entry %r in the dict assigned to %s (line %d)" % (entry, key, src.count("\n", 0, start) + 1))
    vs = start + em.end()
    ve = scan_expr(src, vs)
    old = src[vs:ve].rstrip()
    ve = vs + len(old)
    print("  %s.%s: %s -> %s" % (key, entry, old, value))
    return src[:vs] + value + src[ve:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from-snapshot", metavar="DIR", help="source bot folder (e.g. bots/_snap-strat-2b8ec86) instead of SRC_BOT")
    ap.add_argument("args", nargs="+", help="[SRC_BOT] NAME KEY=VALUE ...")
    a = ap.parse_args()
    args = list(a.args)
    if a.from_snapshot:
        src_dir = os.path.join(ROOT, a.from_snapshot) if not os.path.isabs(a.from_snapshot) else a.from_snapshot
    else:
        if not args:
            fail("missing SRC_BOT")
        src_dir = os.path.join(BOTS, args.pop(0))
    if not args or "=" in args[0]:
        fail("missing NAME")
    name = args.pop(0)
    if not re.fullmatch(r"[\w.-]+", name):
        fail("NAME may only use letters, digits, '_', '-', '.'")
    if not args:
        fail("give at least one KEY=VALUE")
    main_py = os.path.join(src_dir, "src", "main.py")
    if not os.path.isfile(main_py):
        fail("no single-file bot at %s" % os.path.relpath(main_py, ROOT))
    with open(main_py, encoding="utf-8", newline="") as f:
        src = f.read()

    print("variant of %s:" % os.path.relpath(src_dir, ROOT))
    for kv in args:
        if "=" not in kv:
            fail("expected KEY=VALUE, got %r" % kv)
        key, value = kv.split("=", 1)
        key, value = key.strip(), value.strip()
        if not value:
            fail("empty value for %s" % key)
        if "." in key:
            d, e = key.split(".", 1)
            src = set_entry(src, d, e, value)
        else:
            src = set_top(src, key, value)
    try:
        compile(src, "main.py", "exec")
    except SyntaxError as e:
        fail("the rewritten file does not compile: %s (line %s)" % (e.msg, e.lineno))

    folder = "_var-" + name
    dest = os.path.join(BOTS, folder)
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(os.path.join(dest, "src"))
    with open(os.path.join(dest, "src", "main.py"), "w", encoding="utf-8", newline="") as f:
        f.write(src)
    pyr = os.path.join(src_dir, "pyrightconfig.json")
    if os.path.isfile(pyr):
        shutil.copy(pyr, dest)
    with open(os.path.join(dest, "VARIANT.txt"), "w", encoding="utf-8") as f:
        f.write("from %s\n%s\n" % (os.path.relpath(src_dir, ROOT), "\n".join(args)))
    print(folder)


if __name__ == "__main__":
    main()
