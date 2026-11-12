#!/usr/bin/env python3
"""neo agent hook: PreToolUse(Bash) guard for Claude Code and Codex. Deterministic, no model call.

Reads the agent's hook JSON on stdin ({tool_input:{command}, cwd}); a deny is printed as
{hookSpecificOutput:{permissionDecision:"deny",permissionDecisionReason}} with the fix in the reason.
It decides on a real parse of the command. Input it cannot read as JSON, a command it cannot
tokenise, one nested too deeply or one too large to check is denied. Everything else is judged
against the rules below, which name known shapes: a command the rules do not recognise is
allowed. It is a best-effort guard against agent accidents, not a security boundary (see Limits).

Parsing. The command is tokenised as a shell would (quotes, escapes, operators). It is split into
simple commands at && || ; | & ( ) { } newlines and shell keywords; a function body (f() { } and
function f { }) is read as commands. Command substitutions $(...), `...`, <(...) and >(...) are
parsed as commands of their own, and so are the scripts given to bash/sh/zsh -c, eval, trap,
env -S, watch, PROMPT_COMMAND, a heredoc or here-string fed to a shell, a script file run with
bash, sh, source, --rcfile, BASH_ENV or ENV, and the commands tmux, screen, at, batch and
launchctl submit run later. Wrappers (command, builtin, exec, nohup, time, nice, timeout,
gtimeout, ionice, taskpolicy, setsid, flock, stdbuf, env, sudo, doas, xargs, uv/poetry/pipenv run)
are peeled off and a path to git (/usr/bin/git, \\git) counts as git; expect and
crontab, which the guard cannot read, are refused. xargs -I and find -exec placeholders are
unknown values.
Paths are expanded (~, $HOME, and $TMPDIR with the guard's own value), made absolute against the
tracked cwd, normalised (a /tmp/../x path is x) and resolved through symlinks; a path still holding
another variable or a command substitution is unknown and an unknown target of a rule is denied.
An assignment of TMPDIR earlier in the same command is not followed (see Limits).

Rules.
  1. No rm / unlink / shred / find -delete / find -exec rm / xargs rm outside temp roots:
     deletions go to the Trash. A deletion behind an env prefix or xargs is denied.
  2. No destructive git (reset --hard, checkout -f or -- <paths>, restore, switch -f, clean -f,
     force or delete push, branch -D/-M, rebase, filter-branch/filter-repo, stash drop/clear,
     reflog expire, gc --prune, update-ref -d, prune, worktree remove --force, tag -d) without a
     preflight backup that matches the repository now: a preflight-bak-* commit whose parent is the
     current HEAD (on origin when the repo has one), younger than PREFLIGHT_MAX_AGE_H, with its zip
     still on disk, and no changed path modified after it was taken.
     Exempt: throwaway repos whose worktree AND git common dir live under a temp root; a force push
     from one is exempt only when every remote is itself under a temp root.
     Linked worktrees accept the main repo's preflight; a reset --hard / checkout -f / clean -f
     then still needs the worktree's own preflight when the worktree has changes it would destroy.
     `<installed git-preflight.sh> <repo> ... && <destructive git on that repo>` counts as
     preflighted, only through an unbroken && chain and only when the command is the installed
     preflight script itself.
  3. No push to main (a main destination, --all or --mirror, or a bare push with main checked
     out), no bare --force or +refspec push, no remote repo deletion, no filter-branch -- --all,
     no git -c alias.<name>=!<shell>. main is production and only the owner promotes dev to
     it: an agent never runs `neo release` (its --dry-run is allowed), however it is invoked
     (neo, .neo/neo, a path to it, or a shell given it as its script).
  4. No printing of credentials into the transcript: credential files (.env, .netrc, keys, the gh
     token store, cloud and kube configs, /proc/*/environ), gh auth token, keychain passwords,
     git credential fill, git config listings, printenv or echo of a token-named variable, and
     ps with process environments.
  5. Protocol staging and trailer rules: no git add -A / . / :/ / -u, no commit -a, no staging of
     secrets or build output, no Co-Authored-By: Claude trailer on a commit or through
     interpret-trailers, no commit or push --no-verify in a real repository (the hooks are the
     protocol's gates; commit-msg, land, pre-push and I4 also refuse a human author under an agent
     committer, so a foreign --author never lands). An agent pushes
     no claim tag (v<year>.<n>.<n>) and no --tags / --follow-tags: claim tags come from the claim.
  6. Indirection the guard cannot follow is refused: a shell reading its script from a pipe, a
     run-time value as a git subcommand or option on a destructive-capable subcommand, a command
     set through the git -c and GIT_CONFIG_KEY_n keys and the GIT_PAGER / GIT_SSH_COMMAND style
     variables the guard lists (a config file named by GIT_CONFIG_GLOBAL is not read), a --git-dir or
     GIT_DIR it cannot resolve, transport programs (--upload-pack, --receive-pack, --exec, ext::
     and protocol.*.allow=always), config that disarms a safety (clean.requireForce=false), inline
     or stdin-fed interpreter code (any python*, node*, bun, deno eval, perl, ruby, php, lua,
     osascript, uv run python) that deletes files or runs git or a shell, rsync --delete outside a
     temp root, and a bare environment dump typed by name (env, printenv, export -p, set,
     declare -x; not by path). Git long
     options are matched by unique prefix however short, as git does (--h is --hard), and
     single-letter clusters are split (-fu is -f -u, -Df is -D -f).
  7. In-place destruction of an existing file outside the temp roots: truncate, : > file, dd of=,
     cp /dev/null, mv into /dev/null and git --output over it.
  8. An agent commits as an agent: in a real repository that vendors .neo, git commit, merge,
     cherry-pick, revert, rebase, am and commit-tree must run under an identity whose email is an
     `agent` row of the identity map committed on dev and, for the author, whose name carries a
     model stamp, "<name> (<Model>)". The identity is resolved as git would: the command's env
     prefix, variables exported earlier in the same command line, the agent's own environment,
     git -c user.*, --author, then git config. The deny names the exact prefix to use; a map with
     no agent row is denied with the row a human adds. neo land, neo sync and neo lane --rename /
     --close write commits too and are held to the same rule.
     Identity hook (neo-git n206): when the only fault is that the identity comes from git config
     (the agent's own session sets none), the guard supplies it instead of denying. It rewrites
     the command through PreToolUse updatedInput to start with
       export GIT_AUTHOR_NAME=.. GIT_AUTHOR_EMAIL=.. GIT_COMMITTER_NAME=.. GIT_COMMITTER_EMAIL=..;
     exporting only the fields the command, its exports and the session leave unset, from the agent
     row of dev's map (the only one, or the one NEO_AGENT_EMAIL / git config neo.agentEmail names)
     stamped with the model: NEO_MODEL, NEO_GIT_MODEL, ANTHROPIC_MODEL or the hook input's model
     (claude-opus-* reads Opus; likewise Sonnet, Haiku, Fable). The rewritten command is checked
     again by every rule. No rewrite, and the deny stands, when an explicit identity is wrong, the
     model or the row cannot be told, two repositories would need it, or a commit-writing git in a
     repository without .neo shares the line (the identity would leak into it). Decision: allow in
     bypassPermissions mode or for Codex (NEO_GUARD_AGENT=codex, set by codex-adapter.sh), else ask,
     so the user sees the rewritten command and no permission is widened; NEO_IDENTITY_DECISION=
     allow|ask overrides. An allow outside bypassPermissions mode rewrites only a line of plain git,
     neo, cd, export and true commands with no command substitution (Codex skips its own approval on
     allow); otherwise the deny with the prefix stands.
  9. Safety anchors stay forever: refs/safety/<kind>/<name> (a lane's fork point, written by neo lane) is
     never deleted, moved or hand-written, with or without a preflight: update-ref on it, a push that
     deletes it, forces it or sends anything but the anchor itself to it, and a fetch that prunes or
     forces into it are denied in a real repository.
  Also preflighted as rewrites: reset (any mode) to a commit HEAD does not lead to, amend of a
  pushed commit, checkout of a magic pathspec (:/), interactive clean.
Limits. This is a guard against accidents and casual misuse by an agent, not a sandbox and not
an access control. It matches known command shapes; a shape it does not know (an unlisted wrapper
program, a git transport or plumbing command, a config key, a credential read by another route,
a program the guard cannot read, a path built from a TMPDIR assigned earlier in the same command)
is allowed and can do anything the user's account can. An agent
or input that is hostile is out of scope: contain it with an OS sandbox and server-side rules
(the GitHub rulesets in connected mode). The hook entry sets onFailure "block" (Claude Code 2.1.295+), so a timeout or crash of
the hook blocks the call instead of letting it through.
Config: NEO_BAKS_DIR (bak zips, default $HOME/.neo/baks; NEO_GIT_BAKS_DIR is read as a fallback),
PREFLIGHT_MAX_AGE_H (12), GUARD_TMP_ROOTS (colon list that can only narrow the temp exemption).
"""
import fnmatch
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PF = os.path.join(HERE, "git-preflight.sh")
MAX_CMD = 100000
MAX_DEPTH = 8
MAXH = int(os.environ.get("PREFLIGHT_MAX_AGE_H", "12") or "12")
BAKS = os.environ.get("NEO_BAKS_DIR") or os.environ.get("NEO_GIT_BAKS_DIR") or os.path.join(os.path.expanduser("~"), ".neo", "baks")
HOME = os.path.expanduser("~")
TMPD = (os.environ.get("TMPDIR") or "").rstrip("/")


class Deny(Exception):
    pass


class Unparseable(Exception):
    pass


def deny(reason):
    raise Deny(reason)


# Identity hook state for one hook call (rule 8): the repositories whose git writes need the mapped
# identity supplied, the fields to supply, the deny that stands when it cannot be, whether a
# commit-writing git runs in a repository without .neo, and whether the line holds a command
# other than plain git, neo, cd, export and true.
IDN = {"roots": [], "fields": set(), "why": None, "unmapped": False, "other": False}


def idn_reset():
    IDN.update({"roots": [], "fields": set(), "why": None, "unmapped": False, "other": False})


def emit_deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


# --------------------------------------------------------------------------- tokeniser
OPS = ["&&", "||", ";;", "|&", "&>>", "&>", ">>", "<<<", "<<-", "<<", ">&", "<&", ">|", "<>",
       ";", "|", "&", "(", ")", "<", ">", "\n"]
SEPARATORS = {"&&", "||", ";;", ";", "|", "|&", "&", "(", ")", "\n"}
REDIRS = {">", ">>", ">|", "&>", "&>>", "<", "<>", ">&", "<&", "<<<"}
KEYWORDS = {"if", "then", "elif", "else", "fi", "do", "done", "while", "until", "{", "}", "!",
            "time", "coproc"}


class Word:
    """One shell word: its text with quotes removed, and whether it holds an expansion we
    did not resolve (a variable or a command substitution)."""
    __slots__ = ("text", "dynamic", "raw")

    def __init__(self, text, dynamic, raw):
        self.text, self.dynamic, self.raw = text, dynamic, raw


def _balanced(s, i, open_ch, close_ch):
    """Index just past the close_ch matching s[i] == open_ch, honouring quotes and nesting."""
    depth, j, n = 0, i, len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "'":
            k = s.find("'", j + 1)
            if k < 0:
                raise Unparseable("unterminated single quote")
            j = k + 1
            continue
        if c == '"':
            j = _dq_end(s, j)
            continue
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise Unparseable("unbalanced %s%s" % (open_ch, close_ch))


def _dq_end(s, i):
    j, n = i + 1, len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == '"':
            return j + 1
        if c == "$" and j + 1 < n and s[j + 1] == "(":
            j = _balanced(s, j + 1, "(", ")")
            continue
        if c == "`":
            k = s.find("`", j + 1)
            if k < 0:
                raise Unparseable("unterminated backquote")
            j = k + 1
            continue
        j += 1
    raise Unparseable("unterminated double quote")


def tokenize(s, subs):
    """Split shell text into Word and operator tokens. Command substitutions are appended to
    `subs` (their inner text) and leave the word dynamic."""
    toks, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in " \t":
            i += 1
            continue
        if c == "\\" and i + 1 < n and s[i + 1] == "\n":
            i += 2
            continue
        if c == "#" and (not toks or isinstance(toks[-1], str)):
            k = s.find("\n", i)
            i = n if k < 0 else k
            continue
        op = next((o for o in OPS if s.startswith(o, i)), None)
        if op and not (op in ("<", ">") and i + 1 < n and s[i + 1] == "(" ):
            toks.append(op)
            i += len(op)
            continue
        # a word
        text, raw_start, dynamic = [], i, False
        while i < n:
            c = s[i]
            if c in " \t\n" or (any(s.startswith(o, i) for o in OPS) and not (c in "<>" and i + 1 < n and s[i + 1] == "(")):
                break
            if c == "\\":
                if i + 1 < n:
                    text.append(s[i + 1])
                i += 2
                continue
            if c == "'":
                k = s.find("'", i + 1)
                if k < 0:
                    raise Unparseable("unterminated single quote")
                text.append(s[i + 1:k])
                i = k + 1
                continue
            if c == "$" and i + 1 < n and s[i + 1] == "'":
                k = s.find("'", i + 2)
                if k < 0:
                    raise Unparseable("unterminated $'' quote")
                text.append(s[i + 2:k])
                i = k + 1
                continue
            if c == '"':
                k = _dq_end(s, i)
                inner = s[i + 1:k - 1]
                sub_text, dyn = _expand_dq(inner, subs)
                text.append(sub_text)
                dynamic = dynamic or dyn
                i = k
                continue
            if c == "$" and i + 1 < n and s[i + 1] == "(":
                k = _balanced(s, i + 1, "(", ")")
                inner = s[i + 2:k - 1]
                if inner.startswith("("):  # $(( arithmetic ))
                    text.append("0")
                else:
                    subs.append(inner)
                    text.append("$(...)")
                    dynamic = True
                i = k
                continue
            if c in "<>" and i + 1 < n and s[i + 1] == "(":
                k = _balanced(s, i + 1, "(", ")")
                subs.append(s[i + 2:k - 1])
                text.append("/dev/fd/63")
                dynamic = True
                i = k
                continue
            if c == "`":
                k = s.find("`", i + 1)
                if k < 0:
                    raise Unparseable("unterminated backquote")
                subs.append(s[i + 1:k])
                text.append("$(...)")
                dynamic = True
                i = k + 1
                continue
            if c == "$":
                m = re.match(r"\$(\{[^}]*\}|[A-Za-z_][A-Za-z0-9_]*|[0-9#?$!@*-])", s[i:])
                if m:
                    text.append(m.group(0))
                    i += len(m.group(0))
                    continue
            text.append(c)
            i += 1
        toks.append(Word("".join(text), dynamic, s[raw_start:i]))
    return toks


def _expand_dq(inner, subs):
    """Text of a double-quoted string with substitutions recorded; variables are kept as
    written ($HOME, ${TMPDIR}) for the path expander."""
    out, j, n, dyn = [], 0, len(inner), False
    while j < n:
        c = inner[j]
        if c == "\\" and j + 1 < n and inner[j + 1] in '$`"\\\n':
            out.append(inner[j + 1])
            j += 2
            continue
        if c == "$" and j + 1 < n and inner[j + 1] == "(":
            k = _balanced(inner, j + 1, "(", ")")
            body = inner[j + 2:k - 1]
            if not body.startswith("("):
                subs.append(body)
                out.append("$(...)")
                dyn = True
            else:
                out.append("0")
            j = k
            continue
        if c == "`":
            k = inner.find("`", j + 1)
            subs.append(inner[j + 1:k])
            out.append("$(...)")
            dyn = True
            j = k + 1
            continue
        out.append(c)
        j += 1
    return "".join(out), dyn


# --------------------------------------------------------------------------- heredocs
HEREDOC_RE = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "mksh", "fish"}


def split_heredocs(c):
    """Return (command text without heredoc bodies, [(line_text, body)])."""
    lines = c.split("\n")
    out, docs, i = [], [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        for m in HEREDOC_RE.finditer(line):
            tag, strip = m.group(3), m.group(1) == "-"
            body = []
            while i < len(lines) and (lines[i].lstrip("\t") if strip else lines[i]).strip() != tag:
                body.append(lines[i])
                i += 1
            i += 1
            docs.append((line, "\n".join(body)))
    return "\n".join(out), docs


# --------------------------------------------------------------------------- paths
TEMP_DEFAULTS = ["/tmp", "/private/tmp", "/var/folders", "/private/var/folders"]


def _real(p):
    """realpath of the deepest existing ancestor, with the rest appended (normalised)."""
    p = os.path.normpath(p)
    head, tail = p, []
    while head not in ("/", "") and not os.path.exists(head):
        head, t = os.path.split(head)
        tail.insert(0, t)
    base = os.path.realpath(head) if head else "/"
    return os.path.normpath(os.path.join(base, *tail)) if tail else base


def _temp_roots():
    roots = set()
    for r in TEMP_DEFAULTS + ([TMPD] if TMPD else []):
        roots.add(os.path.normpath(r))
        roots.add(_real(r))
    narrow = [x for x in (os.environ.get("GUARD_TMP_ROOTS") or "").split(":") if x]
    if narrow:
        kept = set()
        for r in narrow:
            rr = _real(r)
            if any(_under(rr, t) for t in roots):
                kept.add(rr)
        return roots, kept
    return roots, None


def _under(p, root):
    return p != root and (p + "/").startswith(root.rstrip("/") + "/")


def is_tmp(p, narrowed=True):
    roots, narrow = TEMP_ROOTS
    if not narrowed:
        narrow = None
    rp = _real(p)
    # Judged by where the path really is (a symlink under /tmp to anywhere
    # is not a temp path; re-audit H6).
    if not any(_under(rp, r) for r in roots):
        return False
    if narrow is None:
        return True
    return any(_under(rp, r) for r in narrow)


# Placeholders xargs -I / find -exec substitute at run time ({} and the -I string); a word
# holding one is unknown (round 2 L4).
PLACEHOLDERS = set()


def expand(word, cwd, env):
    """Absolute normalised path for a word, or None when it holds anything unresolved."""
    if word.dynamic or any(ph in word.text for ph in PLACEHOLDERS):
        return None
    t = word.text
    home = env.get("HOME", HOME)
    t = t.replace("${HOME}", home).replace("$HOME", home)
    tmp = env.get("TMPDIR", TMPD) if "TMPDIR" in env else TMPD
    tmp = (tmp or "").rstrip("/")
    if tmp:
        t = t.replace("${TMPDIR}", tmp).replace("$TMPDIR", tmp)
    if t.startswith("~/") or t == "~":
        t = home + t[1:]
    if "$" in t or t.startswith("~"):
        return None
    # Brace expansion ({a,b}, {1..3}) yields other paths at run time (re-audit H6).
    if re.search(r"\{[^{}]*(,|\.\.)[^{}]*\}", t):
        return None
    if not t.startswith("/"):
        if cwd is None:
            return None
        t = os.path.join(cwd, t)
    return os.path.normpath(t)


# --------------------------------------------------------------------------- git helpers
def git(*args, cwd=None):
    try:
        r = subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True, text=True, timeout=8)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


# --------------------------------------------------------------------------- rules
SECRET_RE = re.compile(r"(\.gcm/store|\.credentials\.json|(^|/)\.auth(/|$)|(^|/)keys/|\.p8$|\.p12$|\.pem$|\.pfx$|\.key$|"
                       r"(^|/)\.env(\.(?!example$|sample$|template$|dist$)[^/]*)?$|(^|/)\.netrc$|(^|/)\.git-credentials$|(^|/)\.npmrc$|(^|/)\.pypirc$|"
                       r"(^|/)id_(rsa|ed25519|ecdsa|dsa)$|(^|/)\.aws/credentials$|(^|/)\.docker/config\.json$|(^|/)\.pgpass$|"
                       r"(^|/)kube-?config$|(^|/)\.kube/config$|(^|/)\.config/gh/hosts\.yml$|(^|/)\.config/git/credentials$|"
                       r"(^|/)\.vault-token$|application_default_credentials\.json$|(^|/)\.config/gcloud/|"
                       r"(^|/)\.ssh/(?!.*\.pub$|known_hosts|config$)|^/proc/[^/]+/environ$|(^|/)token\.json$)")
# Environment variable names that hold a credential (rule 4).
SECRET_VAR_RE = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|PRIVATE_?KEY|OAUTH|CREDENTIAL|_AUTH\b|AUTH_)", re.I)
READERS = {"cat", "less", "more", "head", "tail", "bat", "strings", "base64", "xxd", "od", "hexdump", "grep", "rg",
           "awk", "sed", "cut", "jq", "python", "python3", "node", "ruby", "perl", "open", "pbcopy", "curl", "tac",
           "nl", "tee", "diff", "cmp", "sort", "uniq", "zcat", "gzip"}
BANNED_STAGE_RE = re.compile(r"(\.DS_Store$|(^|/)\.auth(/|$)|(^|/)keys(/|$)|\.p8$|\.p12$|\.cer$|\.pem$|\.provisionprofile$|"
                             r"\.mobileprovision$|(^|/)build(-[^/]+)?(/|$)|(^|/)node_modules(/|$)|(^|/)\.env$|\.zip$|\.bak$)")
WRAPPERS_NOARG = {"command", "builtin", "exec", "nohup", "time", "caffeinate", "unbuffer", "noglob"}
# Interpreters and the flags that carry inline code.
INTERPRETERS = {"python": ("-c",), "python3": ("-c",), "python2": ("-c",), "perl": ("-e", "-E"),
                "ruby": ("-e",), "node": ("-e", "--eval", "-p", "--print"), "osascript": ("-e",),
                "php": ("-r",), "lua": ("-e",), "Rscript": ("-e",)}
INTERP_DANGER = re.compile(r"rmtree|os\.remove|os\.unlink|os\.rmdir|unlink|rm\s+-|\brm\b|rmdir|\bgit\b|subprocess|os\.system|"
                           r"popen|system\(|exec[lv]?p?e?\(|spawn|child_process|do shell script|`|fs\.rm|rimraf|File\.delete|"
                           r"FileUtils\.rm|shutil|rm(dir)?Sync|unlinkSync|removeSync|Deno\.(remove|run|Command)|execSync|"
                           r"execFile|\.rm\(|\.remove\(|Bun\.(spawn|\$|write)|\$`|truncate|os\.exec|pathlib|"
                           r"\bpty\b|ctypes|__import__|importlib|eval\(|exec\(", re.I)
# Interpreter names by pattern (python3.12, node22, nodejs ...) and the flags that carry code.
INTERP_PATTERNS = [(re.compile(r"python[0-9.]*|pypy[0-9.]*"), ("-c",)), (re.compile(r"node(js)?[0-9]*"), ("-e", "--eval", "-p", "--print")),
                   (re.compile(r"perl[0-9.]*"), ("-e", "-E")), (re.compile(r"ruby[0-9.]*"), ("-e",)),
                   (re.compile(r"php[0-9.]*"), ("-r",)), (re.compile(r"lua(jit)?[0-9.]*"), ("-e",)),
                   (re.compile(r"bun"), ("-e", "--eval", "-p", "--print")), (re.compile(r"osascript"), ("-e",)),
                   (re.compile(r"Rscript"), ("-e",)), (re.compile(r"pwsh|powershell"), ("-c", "-Command", "-command")),
                   (re.compile(r"tclsh|wish"), ()), (re.compile(r"swift"), ("-e",))]
# Runners that put a command under another name and come back later or elsewhere.
RUN_WRAPPERS = {"uv": {"run"}, "uvx": None, "poetry": {"run"}, "pipenv": {"run"}, "pdm": {"run"}, "rye": {"run"},
                "hatch": {"run"}, "conda": {"run"}, "pixi": {"run"}, "mise": {"exec", "x"}, "asdf": {"exec"}}
FRAMEWORK_PARTS = ("/.neo/",)


def _glob_hits_secret(t):
    """A glob that can expand onto a secret file name (cat .en*, cat *.pem)."""
    if not re.search(r"[*?\[]", t):
        return False
    base = os.path.basename(t)
    for name in (".env", ".env.local", ".env.production", ".netrc", ".git-credentials", ".npmrc", ".pypirc",
                 ".pgpass", "id_rsa", "id_ed25519", "key.pem", "cert.p12", "service.p8", "credentials.json", "kubeconfig"):
        if fnmatch.fnmatchcase(name, base):
            return True
    return False


def check_script_file(word, ctx, env, depth, exec_only=False):
    """Read a shell script run by path and check it like an inline script (re-audit M1).
    The framework's own tools and the installed hooks are trusted as shipped; anything the
    guard cannot read or resolve is refused when it is run as a shell script."""
    p = expand(word, ctx.cwd, env)
    if p is None:
        if exec_only:
            return
        deny("A shell script given by a run-time path blocked (neo guard). Offending: %s" % ctx.raw)
    rp = _real(p)
    if any(part in rp + "/" for part in FRAMEWORK_PARTS) or rp.startswith(_real(HERE) + "/"):
        return
    try:
        with open(rp, "rb") as f:
            head = f.read(200001)
    except OSError:
        if exec_only:
            return
        deny("A shell script the guard cannot read blocked (neo guard): %s. Offending: %s" % (p, ctx.raw))
    if exec_only and not re.match(rb"#!\s*\S*(/|env\s+)(ba|z|da|k)?sh\b", head):
        return
    if len(head) > 200000:
        deny("A shell script over 200 kB blocked (neo guard): too large to check. Offending: %s" % ctx.raw)
    parse_script(head.decode("utf-8", "replace"), Ctx(os.path.dirname(rp), ctx.raw), depth + 1)


class Ctx:
    """State carried across the simple commands of one command line."""

    def __init__(self, cwd, raw):
        self.cwd = cwd
        self.raw = raw
        self.pf_roots = set()      # repo roots preflighted earlier through an unbroken && chain
        self.has_commit = False
        self.piped = False         # the current simple command reads a pipe on stdin
        self.in_pipeline = False   # the current simple command runs in a pipeline (a subshell)
        self.exports = {}          # variables exported earlier in this command line (identity, rule 8)


def parse_script(text, ctx, depth=0, inherited_chain=False):
    if depth > MAX_DEPTH:
        deny("Command too deeply nested to check (neo guard fails closed); split it into plain commands.")
    body, docs = split_heredocs(text)
    subs = []
    toks = tokenize(body, subs)
    for inner in subs:
        parse_script(inner, Ctx(ctx.cwd, ctx.raw), depth + 1)
    # heredocs fed to a shell are commands too
    for line, doc in docs:
        lt = tokenize(line.split("<<")[0], [])
        words = [t.text for t in lt if isinstance(t, Word)]
        if words and any(os.path.basename(w) in SHELLS for w in words):
            parse_script(doc, Ctx(ctx.cwd, ctx.raw), depth + 1)
    seg, sep, stack = [], "^", []
    for t in toks + ["\n"]:
        if isinstance(t, str) and t in SEPARATORS:
            if seg:
                ctx.piped = sep == "|"
                ctx.in_pipeline = ctx.piped or t in ("|", "|&")
                run_segment(seg, sep, ctx, depth)
                ctx.piped = ctx.in_pipeline = False
            seg = []
            # A ( ... ) subshell keeps its directory changes to itself (re-audit H6).
            if t == "(":
                stack.append(ctx.cwd)
            elif t == ")" and stack:
                ctx.cwd = stack.pop()
            sep = "&&" if t == "&&" else ("|" if t in ("|", "|&") else ";")
            continue
        seg.append(t)


def split_redirs(seg):
    words, redirs, i = [], [], 0
    while i < len(seg):
        t = seg[i]
        if isinstance(t, str):
            if t in REDIRS or t in ("<<", "<<-"):
                target = seg[i + 1] if i + 1 < len(seg) and isinstance(seg[i + 1], Word) else None
                redirs.append((t, target))
                i += 2
                continue
            i += 1
            continue
        # fd-number redirections: the number is glued to the operator in shell (2>&1)
        if re.fullmatch(r"[0-9]+", t.raw) and i + 1 < len(seg) and isinstance(seg[i + 1], str) and seg[i + 1] in REDIRS:
            i += 1
            continue
        words.append(t)
        i += 1
    return words, redirs


def run_segment(seg, sep, ctx, depth):
    if sep != "&&":
        ctx.pf_roots = set()
    words, redirs = split_redirs(seg)
    # drop shell keywords that open a compound command; `function NAME` opens a body whose
    # commands follow in this segment and the next ones, so only the two words go (round 2 H1)
    while words:
        if words[0].text in KEYWORDS and not words[0].dynamic:
            words = words[1:]
        elif words[0].text == "function" and not words[0].dynamic:
            words = words[2:]
        else:
            break
    if not words:
        check_truncating_redirs(redirs, ctx, {})
        return
    if words[0].text in ("for", "select", "case") or re.fullmatch(r"[^()]+\)", words[0].text):
        return
    env, envprefix = {}, False
    while words and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0].text, re.S):
        k, v = words[0].text.split("=", 1)
        env[k] = v
        envprefix = True
        words = words[1:]
    if not words:
        return
    check_command(words, redirs, env, envprefix, ctx, depth, xargs=False)


def peel(words, env):
    """Strip wrappers; returns (words, env, xargs, script_texts)."""
    xargs = False
    while words:
        name = os.path.basename(words[0].text)
        if name in WRAPPERS_NOARG:
            words = words[1:]
            while words and words[0].text.startswith("-") and words[0].text != "-":
                words = words[1:]
            continue
        if name == "nice":
            words = words[1:]
            if words and words[0].text == "-n":
                words = words[2:]
            elif words and re.fullmatch(r"-[0-9]+", words[0].text):
                words = words[1:]
            continue
        if name == "timeout":
            words = words[1:]
            while words and words[0].text.startswith("-"):
                words = words[2:] if words[0].text in ("-s", "-k", "--signal", "--kill-after") else words[1:]
            words = words[1:]  # duration
            continue
        if name == "script":
            # script [-aqkF...] [-t time] [file [command ...]]: the command runs (re-audit M1)
            words = words[1:]
            while words and words[0].text.startswith("-"):
                words = words[2:] if words[0].text in ("-t", "-T") else words[1:]
            words = words[1:]  # the typescript file
            continue
        if name == "stdbuf":
            words = words[1:]
            while words and words[0].text.startswith("-"):
                words = words[1:]
            continue
        if name in ("sudo", "doas"):
            words = words[1:]
            while words and words[0].text.startswith("-"):
                words = words[2:] if words[0].text in ("-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-U") else words[1:]
            continue
        if name == "env":
            words = words[1:]
            while words:
                t = words[0].text
                if t in ("-u", "--unset", "-C", "--chdir"):
                    words = words[2:]
                elif t in ("-S", "--split-string") and len(words) > 1:
                    return words[2:], env, xargs, [words[1].text + " " + " ".join(w.raw for w in words[2:])]
                elif t.startswith("-"):
                    words = words[1:]
                elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", t, re.S):
                    k, v = t.split("=", 1)
                    env[k] = v
                    words = words[1:]
                else:
                    break
            continue
        if name == "xargs":
            xargs = True
            words = words[1:]
            while words and words[0].text.startswith("-"):
                t = words[0].text
                if t in ("-I", "--replace") and len(words) > 1:
                    PLACEHOLDERS.add(words[1].text)
                elif t.startswith("-I") and len(t) > 2:
                    PLACEHOLDERS.add(t[2:])
                elif t == "-i" or t.startswith("--replace="):
                    PLACEHOLDERS.add(t.split("=", 1)[1] if "=" in t else "{}")
                words = words[2:] if t in ("-I", "-n", "-P", "-L", "-d", "-E", "-s", "-a", "--max-args", "--max-procs",
                                           "--delimiter", "--arg-file", "--replace") else words[1:]
            continue
        # deferred and detached runners (round 2 M5): the command they run is the rest
        if name in ("gtimeout",):
            words = words[1:]
            while words and words[0].text.startswith("-"):
                words = words[2:] if words[0].text in ("-s", "-k", "--signal", "--kill-after") else words[1:]
            words = words[1:]
            continue
        if name in ("ionice", "taskpolicy", "chrt", "setsid", "flock", "cpulimit", "unshare", "firejail", "systemd-run",
                    "chpst", "daemonize", "faketime", "torsocks", "proxychains", "proxychains4", "catchsegv", "valgrind",
                    "strace", "ltrace", "dtruss", "lldb", "gdb"):
            words = words[1:]
            while words and words[0].text.startswith("-"):
                t = words[0].text
                words = words[2:] if t in ("-c", "-n", "-p", "-b", "-t", "-g", "-l", "-u", "-e", "-o", "-w", "-E") \
                    and len(words) > 1 and not words[1].text.startswith("-") else words[1:]
            if name in ("flock", "chrt", "faketime") and words:
                words = words[1:]  # the lock file, priority or time
            continue
        if name in RUN_WRAPPERS:
            subs = RUN_WRAPPERS[name]
            words = words[1:]
            if subs is not None:
                if not words or words[0].text not in subs:
                    break
                words = words[1:]
            while words and words[0].text.startswith("-"):
                words = words[1:]
            continue
        break
    return words, env, xargs, []


def check_command(words, redirs, env, envprefix, ctx, depth, xargs):
    bare = [w.text for w in words]
    if bare in (["env"], ["printenv"], ["export", "-p"], ["export"], ["set"], ["declare", "-x"]):
        deny("Printing the whole environment blocked (neo guard): it carries tokens into the transcript. Print the "
             "one variable you need. Offending: %s" % ctx.raw)
    words, env, wx, scripts = peel(words, env)
    xargs = xargs or wx
    for sc in scripts:
        parse_script(sc, Ctx(ctx.cwd, ctx.raw), depth + 1)
    if not words:
        return
    first = words[0]
    name = os.path.basename(first.text)
    if first.dynamic or "$" in name:
        deny("Command name is computed at run time (%s); the neo guard cannot check it. Run the command directly." % first.raw)
    args = words[1:]

    # rule 8: remember the identity exported earlier in this command line
    if name == "export":
        for w in args:
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", w.text, re.S):
                k, v = w.text.split("=", 1)
                ctx.exports[k] = None if (w.dynamic or "$" in v or "`" in v) else v
        return
    if name == "unset":
        for w in args:
            ctx.exports[w.text] = ""
        return

    if name not in ("git", "neo", "cd", "pushd", "export", "true") and not first.text.endswith(".neo/neo"):
        IDN["other"] = True

    # rule 3: main is production; only the owner promotes dev to main
    if (name == "neo" or first.text.endswith(".neo/neo")) and _neo_release(args):
        deny(RELEASE_MSG % ctx.raw)
    # rule 8: neo land, neo sync and neo lane --rename / --close write commits (a merge, a rebase, a
    # rewritten lane, a parking note)
    if (name == "neo" or first.text.endswith(".neo/neo")) and args and args[0].text in NEO_WRITERS \
            and (args[0].text != "lane" or (len(args) > 1 and args[1].text in ("--rename", "--close"))) \
            and not any(w.text in ("-h", "--help") for w in args[1:]) and ctx.cwd and not is_tmp(ctx.cwd):
        check_agent_identity("neo " + args[0].text, [], env, {}, ctx, ctx.cwd, ctx.raw,
                             authors=args[0].text == "land")

    # Shell start-up files and prompt hooks run code before the command (round 2 M5).
    for k in ("BASH_ENV", "ENV", "PROMPT_COMMAND", "ZDOTDIR", "PS4"):
        if k in env:
            if k == "PROMPT_COMMAND":
                parse_script(env[k], Ctx(ctx.cwd, ctx.raw), depth + 1)
            elif k == "PS4":
                if "$(" in env[k] or "`" in env[k]:
                    deny("PS4 with a command substitution runs code (neo guard). Offending: %s" % ctx.raw)
            else:
                check_script_file(Word(env[k], "$" in env[k], env[k]), ctx, env, depth)

    # trap bodies run later in this shell: read them like eval (round 2 H1)
    if name == "trap":
        rest = [w for w in args if w.text not in ("--",)]
        if rest and rest[0].text not in ("-l", "-p", "-"):
            if rest[0].dynamic:
                deny("A trap with a run-time body blocked (neo guard): the guard cannot check it. Offending: %s" % ctx.raw)
            parse_script(rest[0].text, Ctx(ctx.cwd, ctx.raw), depth + 1)
        return

    # Detached and scheduled runners (round 2 M5): their command is read like any other.
    if name == "tmux":
        _check_tmux(args, ctx, depth)
        return
    if name == "screen":
        rest, i = list(args), 0
        while rest and rest[0].text.startswith("-"):
            t = rest[0].text
            if t in ("-X", "-Q"):
                deny("screen -X sends keystrokes or commands the guard cannot check (neo guard). Offending: %s" % ctx.raw)
            rest = rest[2:] if t in ("-S", "-c", "-p", "-t", "-e", "-h", "-T", "-s", "-Logfile") else rest[1:]
        if rest:
            check_command(rest, [], dict(env), envprefix, ctx, depth, xargs)
        return
    if name in ("at", "batch"):
        texts = [w.text for w in args]
        if "-f" in texts and texts.index("-f") + 1 < len(args):
            check_script_file(args[texts.index("-f") + 1], ctx, env, depth)
        here = [t for op, t in redirs if op == "<<<" and t is not None]
        src = [t for op, t in redirs if op == "<" and t is not None]
        if here:
            parse_script(here[0].text, Ctx(ctx.cwd, ctx.raw), depth + 1)
        elif src:
            check_script_file(src[0], ctx, env, depth)
        elif ctx.piped:
            deny("%s reading its job from a pipe blocked (neo guard): the guard cannot see it. Offending: %s" % (name, ctx.raw))
        return
    if name == "launchctl" and args and args[0].text in ("submit", "asuser", "bsexec"):
        texts = [w.text for w in args]
        rest = args[texts.index("--") + 1:] if "--" in texts else (args[2:] if args[0].text in ("asuser", "bsexec") else [])
        if not rest:
            deny("launchctl %s runs a program the guard cannot see (neo guard). Offending: %s" % (args[0].text, ctx.raw))
        check_command(rest, [], dict(env), envprefix, ctx, depth, xargs)
        return
    if name == "launchctl" and args and args[0].text == "getenv" and any(SECRET_VAR_RE.search(w.text) for w in args[1:]):
        deny("Printing a credential variable blocked (neo guard, rule 4). Offending: %s" % ctx.raw)
    if name in ("expect", "unbuffer") and args and name == "expect":
        deny("expect runs a script the guard cannot check (neo guard); run the commands directly. Offending: %s" % ctx.raw)
    if name in ("crontab",) and any(w.text not in ("-l",) for w in args):
        deny("crontab installs commands that run later; the guard cannot check them (neo guard). Offending: %s" % ctx.raw)

    # rule 4: commands whose output is a credential (round 2 M6)
    if name == "gh" and [w.text for w in args[:2]] == ["auth", "token"] or \
            name == "gh" and [w.text for w in args[:2]] == ["auth", "status"] and any(w.text in ("-t", "--show-token") for w in args):
        deny("Printing the gh token blocked (neo guard, rule 4): let gh use it, or read it into a variable. Offending: %s" % ctx.raw)
    if name == "security" and args and re.match(r"find-(generic|internet)-password|dump-keychain|export", args[0].text) \
            and (any(w.text in ("-w", "-g") for w in args) or args[0].text in ("dump-keychain", "export")):
        deny("Printing a keychain secret blocked (neo guard, rule 4). Offending: %s" % ctx.raw)
    if name == "printenv" and any(SECRET_VAR_RE.search(w.text) for w in args):
        deny("Printing a credential variable blocked (neo guard, rule 4): use it, never print it. Offending: %s" % ctx.raw)
    if name in ("echo", "printf", "print") and any(re.search(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)", w.raw)
                                                   and SECRET_VAR_RE.search(" ".join(re.findall(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)", w.raw)))
                                                   for w in args):
        to_file = any(op in (">", ">>", ">|") and tgt is not None and tgt.text not in ("/dev/stdout", "/dev/stderr", "/dev/tty")
                      for op, tgt in redirs)
        if not to_file and not ctx.piped and not ctx.in_pipeline:
            deny("Printing a credential variable blocked (neo guard, rule 4): use it, never print it. Offending: %s" % ctx.raw)
    if name == "ps" and any((not w.text.startswith("-") and re.fullmatch(r"[a-zA-Z]*e[a-zA-Z]*", w.text))
                            or re.fullmatch(r"-[a-zA-Z]*E[a-zA-Z]*", w.text)
                            or (sys.platform == "darwin" and re.fullmatch(r"-[a-zA-Z]*e[a-zA-Z]*", w.text)) for w in args):
        deny("ps with process environments blocked (neo guard, rule 4): it prints other processes' tokens. Offending: %s" % ctx.raw)

    # In-place destruction of an existing file outside the temp roots (round 2 L3).
    if name in (":", "true", "false"):
        check_truncating_redirs(redirs, ctx, env)
    if name == "truncate":
        _check_clobber([w for w in args if not w.text.startswith("-") and not re.fullmatch(r"[0-9]+[KMGkmg]?", w.text)],
                       ctx, env, "truncate")
    if name == "dd":
        _check_clobber([Word(w.text[3:], w.dynamic, w.raw) for w in args if w.text.startswith("of=")], ctx, env, "dd of=")
    if name == "cp" and any(w.text == "/dev/null" for w in args):
        _check_clobber([w for w in args if not w.text.startswith("-") and w.text != "/dev/null"][-1:], ctx, env, "cp /dev/null")
    if name == "mv" and args and args[-1].text == "/dev/null":
        check_deletion([w for w in args[:-1] if not w.text.startswith("-")], ctx, env, envprefix, xargs, words)

    # interpreters given a script
    if name in SHELLS or name in ("eval", "source", ".", "watch"):
        script, sfile = None, None
        if name == "eval" or name == "watch":
            rest = [w for w in args if not (name == "watch" and w.text.startswith("-"))]
            if any(w.dynamic for w in rest):
                deny("eval of a run-time value blocked (neo guard): the guard cannot check it. Offending: %s" % ctx.raw)
            script = " ".join(w.text for w in rest)
        elif name in ("source", "."):
            sfile = args[0] if args else None
        else:
            # Shell options: clusters (-ec, -lec, +x), -o/+o NAME pairs and -- may precede
            # the script (re-audit H1); -c anywhere in a cluster makes the first operand a script.
            i, have_c, stdin_flag, done = 0, False, False, False
            while i < len(args):
                t = args[i].text
                if not done and t == "--":
                    done = True
                    i += 1
                    continue
                if not done and t in ("--rcfile", "--init-file") and i + 1 < len(args):
                    check_script_file(args[i + 1], ctx, env, depth)
                    i += 2
                    continue
                if not done and t in ("-o", "+o", "-O", "+O"):
                    i += 2
                    continue
                if not done and re.fullmatch(r"[-+][A-Za-z]+", t):
                    if t[0] == "-" and "c" in t[1:]:
                        have_c = True
                    if t[0] == "-" and "s" in t[1:]:
                        stdin_flag = True
                    i += 1
                    continue
                if not done and t.startswith("--"):
                    i += 1
                    continue
                if have_c:
                    if args[i].dynamic:
                        deny("A shell script computed at run time blocked (neo guard). Offending: %s" % ctx.raw)
                    script = args[i].text
                elif not stdin_flag:
                    sfile = args[i]
                break
            if script is None and sfile is None:
                # The script comes from stdin: a here-string is checked, a pipe or a file the guard
                # cannot see is refused (echo ... | bash, curl ... | sh; re-audit H1).
                here = [t for op, t in redirs if op == "<<<" and t is not None]
                src = [t for op, t in redirs if op == "<" and t is not None]
                if here:
                    if here[0].dynamic:
                        deny("A shell fed a run-time value blocked (neo guard). Offending: %s" % ctx.raw)
                    script = here[0].text
                elif src:
                    sfile = src[0]
                elif ctx.piped:
                    deny("A shell reading its script from a pipe blocked (neo guard): the guard cannot see what it "
                         "runs. Write the commands out, or save the script and run it as a file. Offending: %s" % ctx.raw)
        if script:
            parse_script(script, Ctx(ctx.cwd, ctx.raw), depth + 1)
        if sfile is not None and sfile.text.endswith(".neo/neo"):
            rest = args[[w is sfile for w in args].index(True) + 1:] if any(w is sfile for w in args) else []
            if _neo_release(rest):
                deny(RELEASE_MSG % ctx.raw)
        if sfile is not None:
            check_script_file(sfile, ctx, env, depth)
        return

    # A script run by its path is read like an inline script (re-audit M1); the
    # framework's own tools and the installed hooks are trusted as shipped.
    if "/" in first.text and not first.dynamic:
        check_script_file(first, ctx, env, depth, exec_only=True)

    # Other interpreters given inline code: refuse code that deletes or runs git or a
    # shell, which the guard cannot check (re-audit M1).
    flags = INTERPRETERS.get(name)
    if flags is None:
        for pat, fl in INTERP_PATTERNS:
            if pat.fullmatch(name):
                flags = fl
                break
    if name == "deno" and args and args[0].text == "eval":
        flags = ("eval",)
    if flags is not None:
        code = []
        letters = {f[1] for f in flags if re.fullmatch(r"-[A-Za-z]", f)}
        for j, w in enumerate(args):
            if (w.text in flags or (re.fullmatch(r"-[A-Za-z]{2,}", w.text) and set(w.text[1:]) & letters)) and j + 1 < len(args):
                if args[j + 1].dynamic:
                    deny("Inline %s code computed at run time blocked (neo guard). Offending: %s" % (name, ctx.raw))
                code.append(args[j + 1].text)
            elif any(w.text.startswith(f + "=") for f in flags if f.startswith("--")):
                code.append(w.text.split("=", 1)[1])
        # code on stdin: python3 - <<< '...', node < file, echo ... | python3 (round 2 M4)
        operands = [w for w in args if not w.text.startswith("-") or w.text == "-"]
        if not code and (not operands or operands[0].text == "-"):
            here = [t for op, t in redirs if op == "<<<" and t is not None]
            src = [t for op, t in redirs if op == "<" and t is not None]
            if here:
                code.append(here[0].text)
            elif src:
                pth = expand(src[0], ctx.cwd, env)
                try:
                    code.append(open(pth, errors="replace").read(200000) if pth else "")
                except OSError:
                    deny("%s reading code the guard cannot open blocked (neo guard). Offending: %s" % (name, ctx.raw))
            elif ctx.piped:
                deny("%s reading its code from a pipe blocked (neo guard): the guard cannot see it. Offending: %s"
                     % (name, ctx.raw))
        if any(INTERP_DANGER.search(c) for c in code):
            deny("Inline %s code that deletes files or runs git or a shell blocked (neo guard): the guard cannot "
                 "check it. Run the equivalent shell command directly. Offending: %s" % (name, ctx.raw))

    # rsync --delete removes files under its destination (re-audit M1)
    if name == "rsync" and any(w.text.startswith("--del") or w.text in ("--remove-source-files",) for w in args):
        pos = [w for w in args if not w.text.startswith("-")]
        check_deletion(pos[-1:] if pos else [], ctx, env, envprefix, xargs, words)

    # cd tracking. In a pipeline each command runs in a subshell, so a cd there moves
    # nothing; cd -, popd and run-time targets leave the directory unknown (re-audit H6).
    if name in ("cd", "pushd", "popd"):
        if ctx.in_pipeline:
            return
        if name == "popd" or (args and args[0].text in ("-", "+", "-0", "+0")):
            ctx.cwd = None
        elif args:
            ctx.cwd = expand(args[0], ctx.cwd, env)
        else:
            ctx.cwd = HOME
        return

    # chained preflight: the installed git-preflight.sh itself, never a word that merely names it
    if name == "git-preflight.sh":
        p = expand(first, ctx.cwd, env) if "/" in first.text else None
        if p and _same_file(p, PF) and args:
            r = expand(args[0], ctx.cwd, env)
            root = git("rev-parse", "--show-toplevel", cwd=r) if r and os.path.isdir(r) else None
            if root:
                ctx.pf_roots.add(_real(root))
        return

    # rule 4: credential echo
    if name in READERS:
        to_file = any(op in (">", ">>", ">|", "&>", "&>>") and tgt is not None and not tgt.text.startswith("&")
                      and tgt.text not in ("/dev/stdout", "/dev/stderr", "/dev/tty", "/dev/fd/1", "/dev/fd/2")
                      for op, tgt in redirs)
        inputs = [t for op, t in redirs if op == "<" and t is not None]
        for w in list(args) + inputs:
            if (SECRET_RE.search(w.text) or _glob_hits_secret(w.text)) and not to_file:
                deny("Credential echo blocked: '%s' on a secret path would print the secret into the transcript. "
                     "Read it into a shell variable or let the consuming tool read the file itself. Offending: %s"
                     % (name, " ".join(x.raw for x in words)))

    # rule 6: shell writes into a vendored framework copy
    check_bash_writes(name, args, redirs, ctx, env)

    # find: -delete and -exec
    if name == "find":
        texts = [w.text for w in args]
        if "-delete" in texts:
            check_deletion([w for w in args if not w.text.startswith("-") and w.text not in ("(", ")", "!")][:1] or args[:1],
                           ctx, env, envprefix, True, words)
        for i, t in enumerate(texts):
            if t in ("-exec", "-execdir", "-ok", "-okdir"):
                PLACEHOLDERS.add("{}")
                inner = []
                for w in args[i + 1:]:
                    if w.text in (";", "+"):
                        break
                    inner.append(w)
                if inner:
                    check_command(inner, [], dict(env), envprefix, ctx, depth, xargs=True)
        return

    # rule 1: deletions
    if name in ("rm", "unlink", "shred", "srm"):
        targets = [w for w in args if not (w.text.startswith("-") and len(w.text) > 1)]
        check_deletion(targets, ctx, env, envprefix, xargs, words)
        return

    # rule 3: remote repo deletion
    if name == "gh":
        t = [w.text for w in args]
        joined = " ".join(t)
        if t[:2] == ["repo", "delete"] or (t[:1] == ["api"] and re.search(r"(-X|--method)\s*=?\s*DELETE", joined, re.I)
                                           and re.search(r"(^|\s)/?repos/[^/\s]+/[^/\s]+/?(\s|$)", joined)):
            deny("Remote repo deletion blocked (neo data-loss prevention): only the repo owner deletes a repo, by name, "
                 "by hand. Offending: %s" % " ".join(w.raw for w in words))
        return

    if name == "git":
        check_git(args, env, envprefix, ctx, words)


ID_SUBS = ("commit", "merge", "cherry-pick", "revert", "rebase", "am", "commit-tree")
STAMP_RE = re.compile(r" \([A-Za-z0-9][A-Za-z0-9 ._-]*\)$")


NEO_WRITERS = ("land", "sync", "lane")
ID_FIELDS = ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")


def _ident_src(key, env, cfg, ctx, gdir):
    """(value, explicit) git would use for GIT_<AUTHOR|COMMITTER>_<NAME|EMAIL>; value None when it is
    computed at run time; explicit False when only git config (or nothing) supplies it."""
    if key in env:
        v = env[key]
        return (None if "$" in v or "`" in v else v), True
    if key in ctx.exports:
        if ctx.exports[key] is None:
            return None, True
        if ctx.exports[key] != "":
            return ctx.exports[key], True
    elif os.environ.get(key):
        return os.environ[key], True
    part = "user.name" if key.endswith("_NAME") else "user.email"
    if part in cfg:
        return cfg[part], True
    return git("config", "--get", part, cwd=gdir) or "", False


def _ident(key, env, cfg, ctx, gdir):
    """The value git would use for GIT_<AUTHOR|COMMITTER>_<NAME|EMAIL>; None when it is computed at run time."""
    return _ident_src(key, env, cfg, ctx, gdir)[0]


def _agent_rows(root):
    """(email, name) of every agent row in the identity map committed on dev (the work tree's when dev has none)."""
    text = git("show", "dev:.neo/identity-map", cwd=root)
    if text is None:
        try:
            text = open(os.path.join(root, ".neo", "identity-map"), errors="replace").read()
        except OSError:
            text = ""
    rows = []
    for line in text.splitlines():
        f = line.split()
        if len(f) >= 3 and not f[0].startswith("#") and f[-1] == "agent":
            rows.append((f[0], " ".join(f[1:-1])))
    return rows


def check_agent_identity(sub, sargs, env, cfg, ctx, gdir, raw, authors=None):
    """Rule 8: in a repository that vendors .neo an agent writes commits only as a stamped agent row.
    A fault that comes only from git config is recorded for the identity hook (main), not denied here."""
    root = git("rev-parse", "--show-toplevel", cwd=gdir) if os.path.isdir(gdir) else None
    if not root or not os.path.isfile(os.path.join(root, ".neo", "neo")):
        if root and not sub.startswith("neo "):
            IDN["unmapped"] = True
        return
    rows = _agent_rows(root)
    if not rows:
        deny("neo guard: this repository's .neo/identity-map has no agent row, so an agent cannot commit here as itself. "
             "A human lands the row '<email> <name> agent' through a lane. Offending: %s" % raw)
    emails = {e for e, _ in rows}
    e0, n0 = rows[0]
    fix = ("Prefix the command with GIT_AUTHOR_NAME='%s (<Model>)' GIT_AUTHOR_EMAIL=%s GIT_COMMITTER_NAME='%s (<Model>)' "
           "GIT_COMMITTER_EMAIL=%s (or export them first in the same command)" % (n0, e0, n0, e0))
    src = {k: _ident_src(k, env, cfg, ctx, gdir) for k in ID_FIELDS}
    an, ae, ce = src["GIT_AUTHOR_NAME"][0], src["GIT_AUTHOR_EMAIL"][0], src["GIT_COMMITTER_EMAIL"][0]
    explicit = {k for k, (_, x) in src.items() if x}
    for j, a in enumerate(sargs):
        v = None
        if a == "--author" and j + 1 < len(sargs):
            v = sargs[j + 1]
        elif a.startswith("--author="):
            v = a.split("=", 1)[1]
        if v is not None:
            m = re.fullmatch(r"\s*(.*?)\s*<([^>]*)>\s*", v)
            an, ae = (m.group(1), m.group(2)) if m else (None, None)
            explicit |= {"GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL"}
    if authors is None:
        authors = sub in ("merge", "revert", "commit-tree") or (sub == "commit" and (
            "--amend" not in sargs or "--reset-author" in sargs or any(a == "--author" or a.startswith("--author=") for a in sargs)))
    if ce is None or (authors and (ae is None or an is None)):
        deny("neo guard: the identity of this git %s is computed at run time, so the guard cannot tell it is an agent's. "
             "%s. Offending: %s" % (sub, fix, raw))
    faults = set()
    if ce not in emails:
        faults |= {"GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"}
        why = ("neo guard: an agent commits as an agent row of .neo/identity-map; this git %s would commit as '%s'. "
               "%s. Offending: %s" % (sub, ce or "<none>", fix, raw))
    if authors and (ae not in emails or not STAMP_RE.search(an or "")):
        faults |= {"GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL"}
        why = ("neo guard: an agent authors as an agent row with a model stamp, '<name> (<Model>)'; this git %s would author "
               "as '%s <%s>'. %s. Offending: %s" % (sub, an or "", ae or "", fix, raw))
    if not faults:
        return
    if faults & explicit:
        deny(why)
    # the identity comes from git config alone: the identity hook supplies every field left unset
    IDN["roots"].append(root)
    IDN["fields"] |= set(ID_FIELDS) - explicit
    IDN["why"] = IDN["why"] or why


MODEL_NAMES = (("opus", "Opus"), ("sonnet", "Sonnet"), ("haiku", "Haiku"), ("fable", "Fable"))


def _model(hook_model):
    """The model stamp: NEO_MODEL, NEO_GIT_MODEL, ANTHROPIC_MODEL, then the hook input's model."""
    for v in (os.environ.get("NEO_MODEL"), os.environ.get("NEO_GIT_MODEL"), os.environ.get("ANTHROPIC_MODEL"), hook_model):
        if isinstance(v, dict):
            v = v.get("id") or v.get("display_name")
        if not isinstance(v, str) or not v.strip():
            continue
        low = v.lower()
        for k, n in MODEL_NAMES:
            if k in low:
                return n
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._-]*", v.strip()):
            return v.strip()
    return None


def identity_rewrite(inp, cmd, cwd):
    """The identity hook: the hook output that runs CMD under the mapped, stamped agent identity, or a deny."""
    why = IDN["why"]
    roots = set(IDN["roots"])
    if len(roots) > 1:
        return None, why + " (two repositories in one line: run each one's commits as its own command)"
    if IDN["unmapped"]:
        return None, why + " (a commit in a repository without .neo shares the line; split the command)"
    root = roots.pop()
    rows = _agent_rows(root)
    pick = os.environ.get("NEO_AGENT_EMAIL") or git("config", "--get", "neo.agentEmail", cwd=root) or ""
    row = [r for r in rows if r[0] == pick] if pick else (rows if len(rows) == 1 else [])
    if not row:
        return None, why + (" (the map has several agent rows: set NEO_AGENT_EMAIL or git config neo.agentEmail to yours)"
                            if not pick else " (NEO_AGENT_EMAIL / neo.agentEmail '%s' is not an agent row)" % pick)
    model = _model(inp.get("model"))
    if not model:
        return None, why + " (the model is unknown: set NEO_MODEL, e.g. NEO_MODEL=Opus)"
    email, name = row[0][0], "%s (%s)" % (row[0][1], model)
    val = {"GIT_AUTHOR_NAME": name, "GIT_COMMITTER_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_COMMITTER_EMAIL": email}
    q = lambda v: "'" + v.replace("'", "'\\''") + "'"
    fields = [f for f in ID_FIELDS if f in IDN["fields"]]
    new_cmd = "export " + " ".join("%s=%s" % (f, q(val[f])) for f in fields) + "; " + cmd
    decision = os.environ.get("NEO_IDENTITY_DECISION", "")
    bypass = inp.get("permission_mode") == "bypassPermissions"
    if decision not in ("allow", "ask"):
        decision = "allow" if bypass or os.environ.get("NEO_GUARD_AGENT") == "codex" else "ask"
    if decision == "allow" and not bypass and (IDN["other"] or re.search(r"\$\(|`|<\(|>\(", cmd)):
        return None, why + " (an allowed rewrite holds plain git, neo, cd and export commands only)"
    # the rewritten line is checked again by every rule, with the supplied identity as the session's
    saved = {f: os.environ.get(f) for f in fields}
    try:
        for f in fields:
            os.environ[f] = val[f]
        idn_reset()
        parse_script(new_cmd, Ctx(os.path.normpath(cwd), new_cmd))
        if IDN["roots"]:
            return None, why
    finally:
        for f, v in saved.items():
            if v is None:
                os.environ.pop(f, None)
            else:
                os.environ[f] = v
    ti = dict(inp.get("tool_input") or {})
    ti["command"] = new_cmd
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
            "permissionDecisionReason": "neo guard: commit identity %s <%s> exported for this git write (identity map)"
            % (name, email), "updatedInput": ti}}, None


RELEASE_MSG = ("neo release blocked (neo guard): main is production and promotion to main is the owner's decision; "
               "an agent never releases. Report that dev is ready (neo release --dry-run shows what would ship). "
               "Offending: %s")


def _neo_release(args):
    """True when neo's arguments are a real release: the verb release without --dry-run."""
    texts = [w.text for w in args]
    if not texts or texts[0] != "release":
        return False
    if any(w.dynamic for w in args[1:]):
        return True
    return "--dry-run" not in texts[1:]


def _same_file(a, b):
    try:
        if os.path.realpath(a) == os.path.realpath(b):
            return True
        with open(a, "rb") as fa, open(b, "rb") as fb:
            return fa.read() == fb.read()
    except OSError:
        return False


def _check_clobber(targets, ctx, env, what):
    """An existing file outside the temp roots whose content would be destroyed in place."""
    for w in targets:
        p = expand(w, ctx.cwd, env)
        if p is None:
            deny("%s on a path given by a run-time value blocked (neo guard). Offending: %s" % (what, ctx.raw))
        if p.startswith("/dev/") or is_tmp(p, narrowed=False):
            continue
        if os.path.isfile(p) and os.path.getsize(p) > 0:
            deny("%s would destroy the content of %s in place (neo guard): move it to the Trash first, or write a "
                 "new file. Offending: %s" % (what, p, ctx.raw))


def check_truncating_redirs(redirs, ctx, env):
    """: > file and a bare > file empty an existing file (round 2 L3); called only for an empty
    command or the no-op builtins, never for a command that writes output."""
    _check_clobber([t for op, t in redirs if op in (">", ">|", "&>") and t is not None and not t.text.startswith("&")],
                   ctx, env, "emptying redirect")


def _check_tmux(args, ctx, depth):
    """tmux runs a shell command for new sessions, windows, panes, run-shell, if-shell and
    send-keys types into a shell (round 2 M5): every such argument is read as a script."""
    if not args:
        return
    sub = args[0].text
    runs = {"new", "new-session", "new-window", "neww", "split-window", "splitw", "respawn-pane", "respawnp",
            "respawn-window", "respawnw", "run-shell", "run", "if-shell", "if", "display-popup", "popup",
            "send-keys", "send", "pipe-pane", "pipep"}
    if sub not in runs:
        return
    value_flags = {"-s", "-n", "-c", "-t", "-x", "-y", "-e", "-F", "-l", "-p", "-T", "-w", "-h", "-d", "-b", "-N", "-K",
                   "-X", "-R", "-M", "-H", "-E"}
    takes = {"-s", "-n", "-c", "-t", "-x", "-y", "-e", "-F", "-l", "-p", "-T", "-w", "-h", "-N"}
    rest, i = args[1:], 0
    text = []
    while i < len(rest):
        t = rest[i].text
        if t.startswith("-") and t in value_flags | takes:
            i += 2 if t in takes else 1
            continue
        if rest[i].dynamic:
            deny("tmux %s with a run-time command blocked (neo guard). Offending: %s" % (sub, ctx.raw))
        text.append(t)
        i += 1
    if sub in ("send-keys", "send"):
        text = [t for t in text if not re.fullmatch(r"(C|M|S)-.|Enter|KPEnter|Escape|Tab|Space|BSpace|Up|Down|Left|Right", t)]
        if text:
            parse_script(" ".join(text), Ctx(None, ctx.raw), depth + 1)
        return
    for t in text:
        parse_script(t, Ctx(ctx.cwd, ctx.raw), depth + 1)


def check_deletion(targets, ctx, env, envprefix, xargs, words):
    raw = " ".join(w.raw for w in words)
    msg = ("Deletion blocked (neo data-loss prevention): move it to the Trash (macOS: '/usr/bin/trash <path>', "
           "Linux: 'gio trash <path>') so it stays recoverable. Only absolute paths under /tmp, /private/tmp or "
           "$TMPDIR may be rm'd, never through xargs, -exec or an env prefix. Offending: %s" % raw)
    if envprefix or xargs or not targets:
        deny(msg)
    for w in targets:
        p = expand(w, ctx.cwd, env)
        if p is None or not is_tmp(p, narrowed=False):
            deny(msg)


# --------------------------------------------------------------------------- git
GIT_GLOBAL_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--super-prefix",
                       "--config-env", "--list-cmds"}
# Config keys whose value git runs as a command (re-audit H7), and the values that run nothing.
GIT_CMD_KEYS = re.compile(r"^(core\.(pager|fsmonitor|sshcommand|editor|askpass|gitproxy|alternaterefscommand)|pager\..+|"
                          r"alias\..+|credential\.(.+\.)?helper|diff\.external|diff\..+\.(command|textconv)|"
                          r"merge\..+\.driver|filter\..+\.(clean|smudge|process)|sequence\.editor|gpg\.(.+\.)?program|"
                          r"uploadpack\.packobjectshook|remote\..+\.(uploadpack|receivepack|vcs)|core\.hookspath|"
                          r"include\.path|includeif\..+\.path)$", re.I)
GIT_CMD_ENV = {"GIT_PAGER", "PAGER", "GIT_SSH_COMMAND", "GIT_SSH", "GIT_EXTERNAL_DIFF", "GIT_EDITOR", "EDITOR", "VISUAL",
               "GIT_SEQUENCE_EDITOR", "GIT_ASKPASS", "SSH_ASKPASS", "GIT_CONFIG_PARAMETERS", "GIT_PROXY_COMMAND"}
SAFE_CMD_VALUES = {"", "true", ":", "cat", "less", "less -R", "more", "false", "/dev/null", "vi", "vim", "nano"}
# Long options git accepts by unique prefix (re-audit H3), dangerous first.
GIT_LONG = ["--force", "--force-with-lease", "--force-if-includes", "--hard", "--delete", "--prune", "--mirror", "--all",
            "--discard-changes", "--move", "--remove", "--merge", "--keep", "--soft", "--mixed", "--amend",
            "--no-verify", "--tags", "--follow-tags", "--set-upstream", "--dry-run", "--staged", "--worktree", "--update",
            "--file", "--interactive", "--output", "--upload-pack", "--receive-pack", "--exec", "--rebase", "--author"]
# Single-letter options that take a value, per subcommand: a cluster stops at them (round 2 H2).
GIT_CLUSTER_ARGS = {"push": "o", "branch": "u", "checkout": "bB", "switch": "cC", "reset": "", "clean": "e",
                    "tag": "mFuS", "rm": "", "restore": "s", "stash": "m", "worktree": "b", "commit": "mFcCt",
                    "fetch": "", "pull": "", "clone": "bcou", "merge": "mFsX", "rebase": "sXx"}
GIT_RISKY_SUBS = {"push", "reset", "clean", "branch", "checkout", "switch", "restore", "rebase", "tag", "update-ref",
                  "filter-branch", "filter-repo", "stash", "worktree", "gc", "prune", "reflog", "rm", "config", "symbolic-ref"}


def _git_long(a):
    """--forc -> --force, --h -> --hard: git takes any unambiguous prefix, however short; an
    ambiguous one resolves to the most dangerous candidate here, the safe reading for the guard."""
    if not a.startswith("--") or a == "--":
        return a
    name, eq, val = a.partition("=")
    if name in GIT_LONG:
        return a
    cands = [k for k in GIT_LONG if k.startswith(name)]
    return (cands[0] + eq + val) if cands else a


def _expand_clusters(sargs, argletters):
    """-fu -> -f -u, -Df -> -D -f; a letter that takes a value ends the cluster (-mfoo -> -m foo)."""
    out, seen_dd = [], False
    for a in sargs:
        if seen_dd or a == "--":
            seen_dd = True
            out.append(a)
            continue
        if re.fullmatch(r"-[A-Za-z][A-Za-z0-9]+", a):
            body = a[1:]
            for k, ch in enumerate(body):
                out.append("-" + ch)
                if ch in argletters:
                    if body[k + 1:]:
                        out.append(body[k + 1:])
                    break
            continue
        out.append(a)
    return out


def _git_worktree_of(gd):
    """The worktree git uses for --git-dir/GIT_DIR=gd with no work tree given (round 2 H4):
    core.worktree, or the directory holding a .git dir, or the worktree a linked gitdir names.
    None when it cannot be known (bare, or a plain directory whose work tree is the cwd)."""
    if not os.path.isdir(gd):
        return None
    wt = git("--git-dir", gd, "config", "--get", "core.worktree", cwd="/")
    if wt:
        return os.path.normpath(os.path.join(gd, wt))
    if os.path.basename(gd.rstrip("/")) == ".git":
        return os.path.dirname(gd.rstrip("/"))
    link = os.path.join(gd, "gitdir")
    if os.path.isfile(link):
        try:
            target = open(link).read().strip()
            return os.path.dirname(os.path.normpath(os.path.join(gd, target)))
        except OSError:
            return None
    return None


def _cmd_value_ok(v):
    return v.strip() in SAFE_CMD_VALUES


def check_git(args, env, envprefix, ctx, words):
    raw = " ".join(w.raw for w in words)
    gdir = ctx.cwd
    git_dir = env.get("GIT_DIR")
    for k, v in env.items():
        if k in GIT_CMD_ENV and not _cmd_value_ok(v):
            deny("%s=%s runs a command inside git (neo guard): the guard cannot check it. Offending: %s" % (k, v, raw))
    # GIT_CONFIG_COUNT/KEY_n/VALUE_n set config like git -c
    for k, v in env.items():
        m = re.fullmatch(r"GIT_CONFIG_KEY_([0-9]+)", k)
        if m and GIT_CMD_KEYS.match(v) and not _cmd_value_ok(env.get("GIT_CONFIG_VALUE_" + m.group(1), "")):
            deny("GIT_CONFIG_KEY_%s=%s runs a command inside git (neo guard). Offending: %s" % (m.group(1), v, raw))
        if m:
            _check_disarm(v, env.get("GIT_CONFIG_VALUE_" + m.group(1), ""), raw)
    if "GIT_ALLOW_PROTOCOL" in env and "ext" in env["GIT_ALLOW_PROTOCOL"].split(":"):
        deny("GIT_ALLOW_PROTOCOL with ext lets a URL run a command (neo guard). Offending: %s" % raw)
    cfg = {}
    i = 0
    while i < len(args):
        t = args[i].text
        if not t.startswith("-") or t == "-":
            break
        key, val = t, None
        if "=" in t and t.split("=", 1)[0] in GIT_GLOBAL_WITH_ARG:
            key, val = t.split("=", 1)
            i += 1
        elif t in GIT_GLOBAL_WITH_ARG:
            val = args[i + 1].text if i + 1 < len(args) else None
            if i + 1 < len(args) and args[i + 1].dynamic:
                val = None
                gdir = None
            i += 2
        else:
            i += 1
        if key == "-C" and gdir is not None:
            if val is None:
                gdir = None
            else:
                p = expand(args[i - 1], gdir, env) if not val.startswith("/") else os.path.normpath(val)
                gdir = p
        elif key == "-c" and val is not None:
            ck, _, cv = val.partition("=")
            cfg[ck.lower()] = None if (args[i - 1].dynamic or "$" in cv) else cv
            _check_disarm(ck, cv, raw)
            if GIT_CMD_KEYS.match(ck) and not _cmd_value_ok(cv):
                deny("git -c %s runs a command or hides one inside git (neo guard): the guard cannot check it. Run the "
                     "command directly. Offending: %s" % (ck, raw))
        elif key == "--git-dir":
            git_dir = val
            if val is None:
                gdir = None
        elif key == "--work-tree":
            gdir = os.path.normpath(os.path.join(gdir or "/", val)) if val else None
    # --git-dir / GIT_DIR / GIT_WORK_TREE name the repository acted on, not the cwd (re-audit H5).
    wt = env.get("GIT_WORK_TREE")
    if wt is not None:
        gdir = os.path.normpath(os.path.join(ctx.cwd or "/", wt)) if "$" not in wt else None
    elif git_dir is not None:
        if "$" in git_dir:
            gdir = None
        else:
            gd = os.path.normpath(os.path.join(ctx.cwd or "/", git_dir))
            # git acts on gd's refs; its work tree is never looked up from the cwd here
            # (that answered the cwd's repository; round 2 H4).
            gdir = _git_worktree_of(gd)
    rest = args[i:]
    if not rest:
        return
    sub = rest[0].text
    if rest[0].dynamic or "$" in sub:
        deny("A git subcommand computed at run time blocked (neo guard). Offending: %s" % raw)
    # Arguments computed at run time ($VAR, $(...), `...`) can name main or --hard; the guard
    # compares literals, so a risky subcommand with one is refused (re-audit H2).
    if sub in GIT_RISKY_SUBS and any(w.dynamic or "$" in w.text or "`" in w.text for w in rest[1:]):
        deny("git %s with an argument computed at run time blocked (neo guard): write the value out. Offending: %s"
             % (sub, raw))
    sargs = [_git_long(w.text) for w in rest[1:]]
    if sub in GIT_CLUSTER_ARGS:
        sargs = _expand_clusters(sargs, GIT_CLUSTER_ARGS[sub])
    if sub == "config":
        pos = [a for a in sargs if not a.startswith("-")]
        if len(pos) >= 2 and GIT_CMD_KEYS.match(pos[0]) and not _cmd_value_ok(" ".join(pos[1:])):
            deny("git config %s sets a command git will run (neo guard): the guard cannot check it later. Offending: %s"
                 % (pos[0], raw))
        if len(pos) >= 2:
            _check_disarm(pos[0], " ".join(pos[1:]), raw)
        # listing config prints the tokens it holds (extraheader, credential URLs; round 2 M6)
        opts = [a for a in sargs if a.startswith("-")]
        if any(o in ("-l", "--list") for o in opts) or (any(o == "--get-regexp" for o in opts) and pos and
                re.search(pos[0], "http.https://github.com/.extraheader remote.origin.url credential.helper", re.I)):
            deny("Listing git config blocked (neo guard, rule 4): it can print tokens (http.extraheader, credential "
                 "URLs). Ask for the one key you need with git config --get. Offending: %s" % raw)
    if sub == "credential" and sargs[:1] and sargs[0] in ("fill", "get"):
        deny("git credential fill prints a stored credential (neo guard, rule 4). Offending: %s" % raw)
    # transport programs run as commands (round 2 M1)
    for j, a in enumerate(sargs):
        name_, _, val_ = a.partition("=")
        if sub in ("fetch", "pull", "clone", "ls-remote", "archive", "push", "submodule") and \
                name_ in ("--upload-pack", "--receive-pack", "--exec") or (sub in ("fetch", "clone", "ls-remote") and a == "-u"):
            v = val_ if "=" in a else (sargs[j + 1] if j + 1 < len(sargs) else "")
            if v and not re.fullmatch(r"(/[\w./-]+/)?git[- ](upload|receive)-pack|git-upload-archive", v):
                deny("%s runs %s as a program (neo guard): the guard cannot check it. Offending: %s" % (name_, v, raw))
        if "ext::" in a or a.startswith("fd::"):
            deny("An ext:: or fd:: URL runs a command (neo guard). Offending: %s" % raw)
    # --output writes to any path (round 2 L3)
    for j, a in enumerate(sargs):
        if a == "--output" or a.startswith("--output="):
            v = a.split("=", 1)[1] if "=" in a else (sargs[j + 1] if j + 1 < len(sargs) else "")
            _check_clobber([Word(v, "$" in v, v)], ctx, env, "git --output")
    temp_repo = bool(gdir) and is_tmp(gdir)
    # hooks are the protocol's gates: an agent never skips them in a real repo (round 2 L5)
    if not temp_repo and sub in ("commit", "push", "merge") and any(a == "--no-verify" or (sub == "commit" and a == "-n")
                                                                     for a in _opts(sargs)):
        deny("git %s --no-verify blocked (neo guard): the hooks are the protocol's gates. Fix what they refuse. "
             "Offending: %s" % (sub, raw))
    # the proof note says "this clone ran the gates on this merge"; only neo land writes it (round 3 L9)
    if not temp_repo and any("neo-proof" in a for a in sargs) and (
            sub == "update-ref" or (sub == "notes" and any(a in ("add", "append", "copy", "edit", "merge", "remove", "prune")
                                                            for a in _pos(sargs)))):
        deny("Writing the neo-proof note blocked (neo guard): neo land writes it after the gates pass; a hand-written "
             "note would skip pre-push's gate rerun. Offending: %s" % raw)
    # safety anchors stay forever (owner rule): never deleted, moved or forged, preflight or not
    if not temp_repo:
        check_anchor(sub, sargs, raw)
    if sub == "interpret-trailers" and re.search(r"co-authored-by:?\s*.*claude", re.sub(r"['\"]", "", " ".join(sargs)), re.I):
        deny("Co-Authored-By: Claude trailer blocked (neo protocol, githooks/commit-msg). Offending: %s" % raw)

    if sub == "commit":
        ctx.has_commit = True
        flat = re.sub(r"['\"\\]", "", ctx.raw)
        if re.search(r"co-authored-by:\s*claude", flat, re.I) or any(re.search(r"co-authored-by:\s*claude", re.sub(r"['\"]", "", a), re.I) for a in sargs):
            deny("Co-Authored-By: Claude trailer blocked (neo protocol, githooks/commit-msg): commit without the trailer.")
        for j, a in enumerate(sargs):
            if a in ("-F", "--file") and j + 1 < len(sargs) or a.startswith("--file="):
                fp = sargs[j + 1] if a in ("-F", "--file") else a.split("=", 1)[1]
                full = fp if fp.startswith("/") else os.path.join(gdir or "/", fp)
                try:
                    if re.search(r"co-authored-by:\s*claude", open(full, errors="replace").read(), re.I):
                        deny("Co-Authored-By: Claude trailer blocked (neo protocol, githooks/commit-msg): commit without the trailer.")
                except OSError:
                    pass
        if any(re.fullmatch(r"-[a-zA-Z]*a[a-zA-Z]*", a) and not a.startswith("--") for a in _opts(sargs)) or "--all" in _opts(sargs):
            deny("git commit -a blocked (neo protocol): stage files by name, then commit. Offending: %s" % raw)

    if sub in ("add", "stage"):
        opts, paths = _split_dashdash(sargs)
        dry = any(o == "--dry-run" or re.fullmatch(r"-[A-Za-z]*n[A-Za-z]*", o) for o in opts)
        if not dry:
            if any(o in ("-A", "--all", "-u", "--update", "--no-ignore-removal") or re.fullmatch(r"-[A-Za-z]*[Au][A-Za-z]*", o)
                   for o in opts) or any(p in (".", "./", ":/", ":", "*", ":(top)") for p in paths):
                deny("git add -A / git add . blocked (neo protocol): stage files by name. Offending: %s" % raw)
        if any(BANNED_STAGE_RE.search(p) for p in paths):
            deny("Staging a banned file blocked (neo protocol: .DS_Store, .auth/, keys/, certificates, build/, "
                 "node_modules/, .env, *.zip, *.bak). Offending: %s" % raw)

    if sub in ID_SUBS and gdir and not temp_repo:
        check_agent_identity(sub, sargs, env, cfg, ctx, gdir, raw)

    if sub == "filter-branch" and "--all" in sargs:
        deny("git filter-branch -- --all blocked (neo protocol). Offending: %s" % raw)

    destructive = None
    if sub == "push":
        destructive = check_push(sargs, gdir, raw)
    elif sub == "reset" and "--hard" in sargs:
        destructive = "git reset --hard"
    elif sub == "reset" and _reset_moves_back(sargs, gdir):
        destructive = "history rewrite (reset moves the branch off its commits)"
    elif sub == "commit" and "--amend" in sargs and _head_published(gdir):
        destructive = "history rewrite (amend of a pushed commit)"
    elif sub == "checkout" and (any(a in ("-f", "--force") for a in sargs) or "--" in sargs or "." in sargs
                                or any(a.startswith(":") for a in _pos(sargs)) or _checkout_paths(sargs, gdir)):
        destructive = "git checkout --force"
    elif sub == "restore" and not ("--staged" in sargs and "--worktree" not in sargs and "-W" not in sargs):
        destructive = "git restore"
    elif sub == "switch" and any(a in ("-f", "--force", "--discard-changes") for a in sargs):
        destructive = "git switch --discard-changes"
    elif sub == "clean" and any(re.fullmatch(r"-[a-zA-Z]*[fi][a-zA-Z]*", a) or a in ("--force", "--interactive")
                                for a in sargs):
        destructive = "git clean -f"
    elif sub == "branch" and (any(a in ("-D", "-M", "-C") for a in sargs) or
                              (any(a in ("-d", "--delete", "-m", "--move") for a in sargs) and any(a in ("-f", "--force") for a in sargs))):
        destructive = "git branch -D"
    elif sub in ("rebase", "filter-branch", "filter-repo"):
        destructive = "history rewrite (%s)" % sub
    elif sub == "stash" and sargs[:1] and sargs[0] in ("drop", "clear"):
        destructive = "git stash drop/clear"
    elif (sub == "reflog" and sargs[:1] == ["expire"]) or (sub == "gc" and any(a.startswith("--prune") for a in sargs)) \
            or (sub == "update-ref" and "-d" in sargs) or sub == "prune":
        destructive = "ref/reflog pruning"
    elif sub == "worktree" and sargs[:1] == ["remove"] and any(a in ("-f", "-ff", "--force") for a in sargs):
        destructive = "git worktree remove --force"
    elif sub == "tag" and any(a in ("-d", "--delete") for a in sargs):
        destructive = "git tag -d"
    # Forms that discard work or move an existing branch away from its
    # commits, found after the v2026.0.194 re-audit.
    elif sub == "read-tree" and any(a in ("-u",) for a in sargs) and any(a in ("--reset", "-m") for a in sargs):
        destructive = "git read-tree -u (overwrites the working tree)"
    elif sub == "checkout-index" and any(a in ("-f", "--force") or re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", a) for a in sargs):
        destructive = "git checkout-index -f (overwrites the working tree)"
    elif sub == "submodule" and sargs[:1] == ["deinit"] and any(a in ("-f", "--force") for a in sargs):
        destructive = "git submodule deinit -f"
    elif sub == "rm" and any(a in ("-f", "--force") or re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", a) for a in _opts(sargs)) \
            and "--cached" not in sargs:
        destructive = "git rm -f (drops uncommitted changes)"
    elif sub == "branch" and any(a in ("-f", "--force") for a in sargs) and _moves_branch(sargs, ("-f", "--force"), gdir):
        destructive = "git branch -f (moves an existing branch)"
    elif sub in ("checkout", "switch") and _moves_branch(sargs, ("-B", "-C", "--force-create"), gdir):
        destructive = "git %s -B/-C (resets an existing branch)" % sub
    elif sub == "update-ref" and not any(a in ("-d", "--stdin") for a in sargs) and _pos(sargs)[:1] \
            and _pos(sargs)[0].startswith("refs/heads/") and _branch_exists(_pos(sargs)[0], gdir):
        destructive = "git update-ref (moves an existing branch)"
    elif sub == "fetch" and any(re.match(r"^\+.*:(refs/heads/|[^/:]+$)", a) for a in _pos(sargs)):
        destructive = "forced fetch into local branches"
    elif sub == "pull" and any(a in ("-r", "--rebase") or a.startswith("--rebase=") and a != "--rebase=false" for a in sargs):
        destructive = "history rewrite (pull --rebase)"
    if not destructive:
        return
    require_preflight(destructive, gdir, git_dir, sargs, sub, ctx, raw)


def _check_disarm(key, val, raw):
    """-c keys that switch a safety off or let a URL run a program (round 2 M1, M2)."""
    k, v = key.lower(), val.strip().lower()
    if k == "clean.requireforce" and v in ("false", "no", "off", "0"):
        deny("clean.requireForce=false disarms git clean's safety (neo guard). Offending: %s" % raw)
    if re.fullmatch(r"protocol\.(ext\.|fd\.)?allow", k) and v == "always" or k == "protocol.allow" and v == "always":
        deny("%s=always lets a URL run a command (neo guard). Offending: %s" % (key, raw))
    if k in ("receive.denynonfastforwards", "receive.denydeletes") and v in ("false", "no", "off", "0"):
        deny("%s=false disarms a server-side safety (neo guard). Offending: %s" % (key, raw))


def _reset_moves_back(sargs, gdir):
    """git reset (soft, mixed, keep, merge) to a commit HEAD is not an ancestor of leaves the
    branch's newer commits only in the reflog: a history rewrite like branch -f (round 2 M3).
    Unstaging (reset, reset HEAD, reset -- paths) and moving forward are not."""
    opts, pos = _split_dashdash(sargs)
    if "--" in sargs:
        pos = [a for a in sargs[:sargs.index("--")] if not a.startswith("-")]
    if not pos or not gdir or not os.path.isdir(gdir):
        return False
    target = git("rev-parse", "--verify", "-q", pos[0] + "^{commit}", cwd=gdir)
    head = git("rev-parse", "--verify", "-q", "HEAD", cwd=gdir)
    if not target or not head or target == head:
        return False
    return subprocess.run(["git", "merge-base", "--is-ancestor", head, target], cwd=gdir,
                          capture_output=True, timeout=8).returncode != 0


def _head_published(gdir):
    """HEAD is on a remote-tracking branch: amending it rewrites published history."""
    if not gdir or not os.path.isdir(gdir):
        return False
    return bool(git("branch", "-r", "--contains", "HEAD", cwd=gdir))


def _pos(sargs):
    return [a for a in sargs if not a.startswith("-")]


def _branch_exists(name, gdir):
    ref = name if name.startswith("refs/") else "refs/heads/" + name
    return bool(gdir and os.path.isdir(gdir) and git("rev-parse", "--verify", "-q", ref, cwd=gdir))


def _moves_branch(sargs, flags, gdir):
    """The branch named after one of FLAGS (or the first operand for branch -f) already exists."""
    for j, a in enumerate(sargs):
        if a in flags:
            if a in ("-f", "--force"):
                pos = _pos(sargs)
                return bool(pos) and _branch_exists(pos[0], gdir)
            return j + 1 < len(sargs) and _branch_exists(sargs[j + 1], gdir)
    return False


def _checkout_paths(sargs, gdir):
    """git checkout <x> where x is no revision but an existing path discards its changes (re-audit M3)."""
    if any(a in ("-b", "-B", "--orphan") for a in sargs) or not gdir or not os.path.isdir(gdir):
        return False
    for a in [a for a in sargs if not a.startswith("-")]:
        if git("rev-parse", "--verify", "-q", a + "^{commit}", cwd=gdir):
            continue
        if os.path.exists(os.path.join(gdir, a)):
            return True
    return False


def _opts(sargs):
    return _split_dashdash(sargs)[0]


def _split_dashdash(sargs):
    if "--" in sargs:
        k = sargs.index("--")
        return [a for a in sargs[:k] if a.startswith("-")], [a for a in sargs[:k] if not a.startswith("-")] + sargs[k + 1:]
    return [a for a in sargs if a.startswith("-")], [a for a in sargs if not a.startswith("-")]


ANCHOR_RE = re.compile(r"^(\+)?([^:]*):?(.*)$")


def check_anchor(sub, sargs, raw):
    """refs/safety/* (a lane's fork point) is written by neo only and never deleted or moved."""
    why = ("Safety anchors stay forever (neo rule): refs/safety/<kind>/<name> keeps a lane's fork point for the life "
           "of the repository; neo lane writes it and nothing deletes, moves or hand-writes it, with or without a "
           "preflight. To park a lane use neo lane --close <reason>. Offending: %s" % raw)
    touches = [a for a in sargs if "refs/safety" in a or a.startswith("safety/")]
    if not touches:
        return
    if sub in ("update-ref", "symbolic-ref", "pack-refs", "replace"):
        deny(why)
    if sub == "push":
        opts = [a for a in sargs if a.startswith("-")]
        if any(o in ("-d", "--delete", "-f", "--force", "--prune", "--mirror") or o.startswith("--force-with-lease")
               for o in opts):
            deny(why)
        for r in [a for a in sargs if not a.startswith("-")]:
            m = ANCHOR_RE.match(r)
            src, dst = m.group(2), (m.group(3) or m.group(2))
            if "refs/safety" in dst and (m.group(1) or src == "" or "refs/safety" not in src or src != dst):
                deny(why)
    if sub == "fetch":
        if any(a in ("-p", "--prune", "-f", "--force", "--prune-tags") for a in sargs) or \
                any(a.startswith("+") and "refs/safety" in a.split(":", 1)[-1] for a in sargs):
            deny(why)


def check_push(sargs, gdir, raw):
    opts, pos, j = [], [], 0
    while j < len(sargs):
        a = sargs[j]
        if a in ("-o", "--push-option", "--repo", "--receive-pack", "--exec"):
            opts.append(a)
            j += 2
            continue
        (opts if a.startswith("-") else pos).append(a)
        j += 1
    force = any(o in ("-f", "--force") for o in opts)
    lease = any(o.startswith("--force-with-lease") for o in opts)
    # Claim tags are minted only by the claim flow (round 2 L6): an agent pushes no v<year>.<n>.<n>
    # tag and no --tags / --follow-tags bulk tag push.
    if any(o in ("--tags", "--follow-tags") for o in opts) or any(
            re.search(r"(^|:|refs/tags/)v[0-9]{4}\.[0-9]+\.[0-9]+$", r.lstrip("+")) for r in pos[1:]):
        deny("Pushing claim tags blocked (neo guard): v<year>.<n>.<n> tags come only from the claim flow "
             "(scripts/claim-dev-merge.sh). Offending: %s" % raw)
    if force and not lease:
        deny("Bare --force blocked (neo protocol): use --force-with-lease after a preflight. Offending: %s" % raw)
    refspecs = pos[1:]
    if any(o in ("--all", "--mirror") for o in opts):
        deny("Push to main blocked: --all / --mirror would push main; push the named branch. Offending: %s" % raw)
    if "--prune" in opts:
        deny("git push --prune deletes remote branches (neo guard); delete a branch by name after a preflight. "
             "Offending: %s" % raw)
    cur = git("symbolic-ref", "--short", "-q", "HEAD", cwd=gdir) if gdir and os.path.isdir(gdir) else None
    plus = False
    delete = any(o in ("-d", "--delete") for o in opts)
    for r in refspecs:
        if r.startswith("+"):
            plus = True
            r = r[1:]
        dst = r.split(":", 1)[1] if ":" in r else r
        if r.startswith(":"):
            delete = True
        if "*" in r:
            deny("A wildcard refspec can push or overwrite main (neo guard); push branches by name. Offending: %s" % raw)
        if dst in ("HEAD", "@"):
            dst = cur or "HEAD"
            if cur is None:
                deny("git push of HEAD with no branch checked out blocked (neo guard): name the branch. Offending: %s" % raw)
        if dst in ("main", "refs/heads/main"):
            deny("Push to main blocked: main is production and advances only through neo release, which the owner "
                 "runs, never by a direct push. Offending: %s" % raw)
    if plus and not lease:
        deny("A +refspec is a bare force push (neo protocol): use --force-with-lease after a preflight. Offending: %s" % raw)
    if not refspecs and gdir:
        cur = git("symbolic-ref", "--short", "HEAD", cwd=gdir) if os.path.isdir(gdir) else None
        if cur == "main":
            deny("Push to main blocked: main is checked out in %s and a bare 'git push' would advance it. Switch to a "
                 "lane; main is production and only the owner promotes it with neo release." % gdir)
    if lease or plus:
        return "force push"
    if delete:
        return "remote branch deletion"
    return None


def require_preflight(destructive, gdir, git_dir, sargs, sub, ctx, raw):
    if gdir is None or (git_dir and not os.path.isabs(git_dir) and gdir is None):
        deny("Destructive git blocked (neo preflight): %s on a repository given by a run-time value; the guard "
             "cannot check its preflight. Run it with a literal path (git -C <repo>). Offending: %s" % (destructive, raw))
    root = git("rev-parse", "--show-toplevel", cwd=gdir) if os.path.isdir(gdir) else None
    if not root:
        deny("Destructive git blocked (neo preflight): %s but %s is not inside a git repo, so the preflight cannot be "
             "checked. Run it from inside the repo (cd <repo> && ...) or with git -C <repo>. Offending: %s" % (destructive, gdir, raw))
    root_p = _real(root)
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=root)
    gitdir = git("rev-parse", "--path-format=absolute", "--git-dir", cwd=root)
    common_p = _real(common) if common else ""
    gitdir_p = _real(gitdir) if gitdir else ""
    linked = bool(common_p) and common_p != gitdir_p
    mainroot = common_p[:-5] if common_p.endswith("/.git") else common_p

    if is_tmp(root_p) and common_p and is_tmp(common_p):
        if destructive not in ("force push", "remote branch deletion"):
            return
        remote_ok = not any(re.search(r"://|^[^/\s]+@[^\s]+:", a) for a in sargs)
        cfg = git("config", "--get-regexp", r"^remote\..*\.(url|pushurl)$", cwd=root) or ""
        for line in cfg.splitlines():
            url = line.split(None, 1)[1] if " " in line else ""
            u = url[7:] if url.startswith("file://") else url
            if not u.startswith("/"):
                u = os.path.join(root_p, u)
            if not is_tmp(_real(u)):
                remote_ok = False
        if remote_ok:
            return

    def wt_dirty():
        if destructive in ("git reset --hard", "git checkout --force", "git restore", "git switch --discard-changes",
                           "git read-tree -u (overwrites the working tree)", "git checkout-index -f (overwrites the working tree)",
                           "git rm -f (drops uncommitted changes)"):
            return git("status", "--porcelain", "--untracked-files=no", cwd=root) or ""
        if destructive == "git clean -f":
            ignored = any(re.fullmatch(r"-[a-zA-Z]*[xX][a-zA-Z]*", a) for a in sargs)
            st = git("status", "--porcelain", "--untracked-files=all", *(["--ignored"] if ignored else []), cwd=root) or ""
            return "\n".join(l for l in st.splitlines() if l.startswith("??") or l.startswith("!!"))
        return ""

    wt_deny = ("Destructive git blocked (neo preflight): %s in linked worktree %s, whose uncommitted changes the main "
               "repo's preflight does not cover. Run first: \"%s\" \"%s\" \"before %s\"  then retry the exact command."
               % (destructive, root, PF, root, destructive))
    if root_p in ctx.pf_roots:
        return
    if linked and mainroot in ctx.pf_roots:
        if not wt_dirty():
            return
        deny(wt_deny)

    ok, why = preflight_matches(root, root_p)
    if ok:
        return
    if linked:
        ok_main, _ = preflight_matches(mainroot, mainroot)
        if ok_main:
            if not wt_dirty():
                return
            deny(wt_deny)
    deny("Destructive git blocked (neo preflight): %s on %s: %s. Run first: \"%s\" \"%s\" \"before %s\"  then retry "
         "the exact command, or chain both in one command (\"%s\" \"%s\" \"...\" && <command>)."
         % (destructive, root, why, PF, root, destructive, PF, root))


def preflight_matches(root, root_p):
    """(True, "") when a preflight backup covers the repository as it is now."""
    has_origin = git("remote", "get-url", "origin", cwd=root) is not None
    pattern = "refs/remotes/origin/" if has_origin else "refs/heads/"
    where = "on origin" if has_origin else "locally (repo has no origin)"
    refs = git("for-each-ref", "--sort=-committerdate", "--format=%(committerdate:unix) %(refname)", pattern, cwd=root) or ""
    head = git("rev-parse", "--verify", "-q", "HEAD", cwd=root) or ""
    now, limit = time.time(), MAXH * 3600
    changed = None
    for line in refs.splitlines():
        ts, ref = line.split(" ", 1)
        if "/preflight-bak-" not in ref:
            continue
        ts = int(ts)
        if now - ts > limit:
            return False, "no preflight-bak-* ref %s within %dh" % (where, MAXH)
        parent = git("rev-parse", "--verify", "-q", ref + "^1", cwd=root) or ""
        if parent != head:
            continue
        body = git("log", "-1", "--format=%B", ref, cwd=root) or ""
        m = re.search(r"^Zip: (.+)$", body, re.M)
        zipf = m.group(1).strip() if m else ""
        name = os.path.basename(root)
        # the preflight is of this repository (a linked worktree's own, not its main repo's)
        if not os.path.basename(zipf).startswith(name + "-bak-"):
            continue
        if not os.path.isfile(zipf) or now - os.path.getmtime(zipf) > limit:
            return False, "no %s-bak-*.zip in %s within %dh" % (name, BAKS, MAXH)
        if changed is None:
            st = git("status", "--porcelain", "--untracked-files=all", "-z", cwd=root) or ""
            changed = [e[3:] for e in st.split("\0") if len(e) > 3]
        for path in changed:
            full = os.path.join(root, path)
            try:
                if os.path.getmtime(full) > ts + 1:
                    return False, "%s changed after the newest matching preflight" % path
            except OSError:
                continue
        return True, ""
    return False, "no preflight-bak-* ref %s for the current HEAD within %dh" % (where, MAXH)


VENDORED_MSG = ("Write blocked (neo protocol): a vendored .neo copy is never edited; change the canonical "
                "framework repo, then run 'neo setup --upgrade <source>' on a lane here. Path: %s")


def vendored(path):
    """True when an absolute path lies inside a vendored .neo copy: the real path (symlinks
    resolved, compared case-insensitively) is under a namespace dir whose repo does not commit the
    FRAMEWORK_REPO marker (an untracked marker someone just created does not count)."""
    rp = _real(path)
    parts = rp.split("/")
    low = [x.lower() for x in parts]
    if ".neo" not in low:
        return False
    k = low.index(".neo")
    root = "/".join(parts[:k]) or "/"
    # conf and identity-map are the consumer's own files inside .neo
    if low[k + 1:] in (["conf"], ["identity-map"]):
        return False
    marker = ".neo/FRAMEWORK"
    if os.path.isfile(os.path.join(root, marker)) and git("ls-files", "--error-unmatch", marker, cwd=root) is not None:
        return False
    return True


WRITE_CMDS = {"tee", "touch", "truncate", "cp", "mv", "install", "ln", "rsync", "dd", "sed", "perl", "patch"}


def check_bash_writes(name, args, redirs, ctx, env):
    targets = [t for op, t in redirs if op in (">", ">>", ">|", "&>", "&>>", "<>") and t is not None]
    texts = [w.text for w in args]
    if name in ("tee", "touch", "truncate"):
        targets += [w for w in args if not w.text.startswith("-")]
    elif name in ("cp", "mv", "install", "ln", "rsync"):
        pos = [w for w in args if not w.text.startswith("-")]
        if "-t" in texts and texts.index("-t") + 1 < len(args):
            targets.append(args[texts.index("-t") + 1])
        elif pos:
            targets.append(pos[-1])
    elif name in ("sed", "perl") and any(t == "-i" or t.startswith("-i") or t.startswith("--in-place") or re.fullmatch(r"-[a-zA-Z]*i[a-zA-Z]*", t) for t in texts):
        targets += [w for w in args if not w.text.startswith("-")][1:]
    elif name == "dd":
        targets += [Word(w.text[3:], w.dynamic, w.raw) for w in args if w.text.startswith("of=")]
    for w in targets:
        p = expand(w, ctx.cwd, env)
        if p is not None and vendored(p):
            deny(VENDORED_MSG % p)


def main_write():
    """PreToolUse(Write|Edit|NotebookEdit) entry: deny a write into a vendored namespace copy."""
    try:
        inp = json.loads(sys.stdin.read())
        ti = inp.get("tool_input") or {}
        fp = ti.get("file_path") or ti.get("notebook_path")
        cwd = inp.get("cwd") or os.getcwd()
    except (ValueError, AttributeError):
        emit_deny("neo guard: the hook input is not valid JSON; the write was not checked, so it is refused.")
        return
    if not fp:
        return
    path = fp if fp.startswith("/") else os.path.join(cwd, fp)
    try:
        if vendored(os.path.normpath(path)):
            emit_deny(VENDORED_MSG % fp)
    except Exception as e:
        emit_deny("neo guard: internal error (%s: %s); the write was refused." % (type(e).__name__, e))


TEMP_ROOTS = None


def main():
    global TEMP_ROOTS
    data = sys.stdin.read()
    try:
        inp = json.loads(data)
        cmd = (inp.get("tool_input") or {}).get("command")
        cwd = inp.get("cwd") or os.getcwd()
    except (ValueError, AttributeError):
        emit_deny("neo guard: the hook input is not valid JSON; the command was not checked, so it is refused.")
        return
    if isinstance(cmd, list):
        cmd = " ".join(str(x) for x in cmd)
    if not cmd:
        return
    if len(cmd) > MAX_CMD:
        emit_deny("neo guard: the command is %d characters, more than the %d the guard checks; split it into "
                  "smaller commands." % (len(cmd), MAX_CMD))
        return
    TEMP_ROOTS = _temp_roots()
    ctx = Ctx(os.path.normpath(cwd), cmd)
    idn_reset()
    try:
        parse_script(cmd, ctx)
        if IDN["roots"]:
            out, why = identity_rewrite(inp, cmd, cwd)
            if out is None:
                emit_deny(why)
            else:
                print(json.dumps(out))
    except Deny as d:
        emit_deny(str(d))
    except Unparseable as u:
        emit_deny("neo guard: the command could not be parsed (%s), so it is refused; fix the quoting or split it." % u)
    except Exception as e:  # fail closed on any defect of the guard itself
        emit_deny("neo guard: internal error (%s: %s); the command was refused. Report it with the command." %
                  (type(e).__name__, e))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write"]:
        TEMP_ROOTS = _temp_roots()
        main_write()
    else:
        main()
