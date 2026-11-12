#!/usr/bin/env python3
"""lint/quiet-grep.py - no shell pipeline ends in a quiet grep.

Under `set -o pipefail` a quiet grep (-q, --quiet, --silent) exits at the
first match, the writer upstream gets SIGPIPE, and the pipeline reports a
miss on a hit once the input outgrows the pipe buffer. Give grep a
here-string, or let it read all of its input with its output sent to
/dev/null (true of BSD grep and GNU grep 2.27 or later).

Scans the tracked shell files of the current tree (*.sh, hooks, and files
whose first line names a shell); joined continuation lines; -q anywhere in
the flags, --quiet, --silent, egrep, fgrep, a path to grep, and command,
env or VAR= prefixes. Prints file:line for each finding, exit 1 on any.
  quiet-grep.py [--self-check] [FILE...]
"""
import os
import re
import subprocess
import sys

PIPE = "|"
STAGE = re.compile(
    r"(?<![|])\|(?![|])\s*"
    r"(?:(?:[A-Za-z_][A-Za-z0-9_]*=\S*|env(?:\s+-\S+)*|command|builtin)\s+)*"
    r"(?:\S*/)?[ef]?grep\b(?P<args>[^|;&)]*)")
QUIET = re.compile(r"(?:^|\s)(?:-[A-Za-z]*q[A-Za-z]*|--quiet|--silent)(?=\s|$)")


def logical_lines(text):
    buf, start = "", 1
    for n, line in enumerate(text.split("\n"), 1):
        if not buf:
            start = n
        if line.endswith("\\"):
            buf += line[:-1] + " "
            continue
        buf += line
        yield start, buf
        buf = ""
    if buf:
        yield start, buf


def strip_comment(line):
    out, q = [], None
    for i, c in enumerate(line):
        if q:
            if c == q:
                q = None
        elif c in "'\"":
            q = c
        elif c == "#" and (i == 0 or line[i - 1].isspace()):
            break
        out.append(c)
    return "".join(out)


def hits_in(text):
    for n, line in logical_lines(text):
        code = strip_comment(line)
        for m in STAGE.finditer(code):
            if QUIET.search(m.group("args").split(" -- ")[0]):
                yield n, line.strip()
                break


def is_shell(path, text):
    if path.endswith(".sh") or "/hooks/" in "/" + path:
        return True
    first = text.split("\n", 1)[0]
    return first.startswith("#!") and re.search(r"\b(ba|z|da|k)?sh\b", first) is not None


def tracked():
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\0") if p]


def scan(paths):
    found = []
    for p in paths:
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if not is_shell(p, text):
            continue
        for n, line in hits_in(text):
            found.append("%s:%d: %s" % (p, n, line))
    return found


def self_check():
    g = "gr" + "ep"
    bad = ["x " + PIPE + " " + g + " -q a", "x " + PIPE + " " + g + " -Fxq a", "x " + PIPE + " " + g + " -E -q a",
           "x " + PIPE + " " + g + " --quiet a", "x " + PIPE + " " + g + " --silent a", "x " + PIPE + " e" + g + " -q a",
           "x " + PIPE + " f" + g + " -q a", "x " + PIPE + " command " + g + " -q a",
           "x " + PIPE + " env LC_ALL=C " + g + " -q a", "x " + PIPE + " LC_ALL=C " + g + " -q a",
           "x " + PIPE + " /usr/bin/" + g + " -q a", "x " + PIPE + " " + g + " -e a -q",
           "x \\\n  " + PIPE + " " + g + " -q a"]
    good = [g + " -q a <<<\"$x\"", "x " + PIPE + " " + g + " a >/dev/null", "x " + PIPE + PIPE + " " + g + " -q a f",
            "# x " + PIPE + " " + g + " -q a", "x " + PIPE + " " + g + " -- -q", "x " + PIPE + " " + g + " -c a"]
    miss = [b for b in bad if not list(hits_in(b))]
    false = [s for s in good if list(hits_in(s))]
    for b in miss:
        print("MISSED: %r" % b)
    for s in false:
        print("FALSE HIT: %r" % s)
    return 1 if miss or false else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--self-check"]:
        sys.exit(self_check())
    out = scan(args or tracked())
    for line in out:
        print("X quiet grep in a pipeline (use a here-string): " + line)
    sys.exit(1 if out else 0)
