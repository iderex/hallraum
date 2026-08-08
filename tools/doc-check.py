"""Refuse a tracked document that names a path which is not there, that carries
a generated block which is out of date, or that ends a line in whitespace.

    python tools/doc-check.py
    python tools/doc-check.py --selftest

Every refusal is one line naming the rule, the document and the line, so that a
reader is told what was refused and where rather than handed a diff to read.

Standard library only. This is a repository maintenance tool, it is not part of
whatever the software turns out to be written in, and it imports nothing beyond
what a stock interpreter carries.

The three rules and what each one is bounded by:

unresolved-path
    A path written in a document has to be tracked at HEAD, or be a path git
    ignores because something in the tree produces it. Candidates are markdown
    link targets, backtick spans whose whole content is a path, and any token
    carrying one of the extensions in EXTENSIONS. A token with no extension is
    not a candidate, so `repos/owner/name/rulesets` in a pasted API call is not
    read as a path, and neither is a directory named without a trailing slash.
    Where a document has to name a path that is not in the tree, the line before
    it carries an exemption comment with a reason.

stale-generated-block
    A block a document says was produced by a program is produced again and
    compared. The command is not taken as arbitrary: it has to be an
    interpreter invocation of a tracked file, checked below, because a document
    is a thing anybody can send in a pull request and running what it says
    would otherwise be a way to run anything.

trailing-whitespace
    One formatting property, and it is the only one. This does not compare a
    document against a canonical rendering, so two different layouts of the same
    prose both pass. Issue #107 asks for more than that and says so.
"""

import argparse
import os
import re
import subprocess
import sys

EXTENSIONS = ("md", "py", "yml", "yaml", "json", "txt", "toml", "cfg", "sh")

# A whole backtick span that is a path: no spaces, no operators, optionally
# ending in a slash to name a directory.
PATH_SPAN = re.compile(r"^\.?/?[\w.@+-]+(?:/[\w.@+-]+)*/?$")

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
TICK = re.compile(r"`([^`\n]+)`")
WITH_EXTENSION = re.compile(
    r"(?<![\w/.-])(\.?/?(?:[\w.@+-]+/)+[\w.@+-]+\.(?:" + "|".join(EXTENSIONS) + r"))\b"
)

EXEMPT = re.compile(r"<!--\s*doc-check:\s*unresolved-path\s+(.+?)\s*-->")

GENERATED_OPEN = re.compile(r"<!--\s*generated:\s*(.+?)\s*-->")
GENERATED_CLOSE = re.compile(r"<!--\s*end generated\s*-->")

SCHEMES = ("http://", "https://", "mailto:", "ftp://")


class Finding:
    def __init__(self, path, line, rule, detail):
        self.path = path
        self.line = line
        self.rule = rule
        self.detail = detail

    def __str__(self):
        return "%s:%d: %s: %s" % (self.path, self.line, self.rule, self.detail)


def git(*args):
    out = subprocess.run(
        ["git"] + list(args), capture_output=True, check=True
    ).stdout
    return out.decode("utf-8")


def tracked_paths(root):
    """Every tracked path, plus every directory prefix of one, so that a
    document naming a directory resolves."""
    paths = set()
    for line in git("-C", root, "ls-files").split("\n"):
        line = line.strip()
        if not line:
            continue
        paths.add(line)
        parts = line.split("/")
        for i in range(1, len(parts)):
            paths.add("/".join(parts[:i]))
    return paths


def ignored(root, candidate):
    """True where git would ignore this path. A document may name a file the
    tree produces rather than carries, and an ignore rule is the tree's own
    statement that it is such a file."""
    result = subprocess.run(
        ["git", "-C", root, "check-ignore", "-q", "--no-index", candidate],
        capture_output=True,
    )
    return result.returncode == 0


def candidates(line):
    """Path candidates in one line of a document, as (token, reason) pairs."""
    found = []
    for match in LINK.finditer(line):
        target = match.group(1)
        if target.startswith("#") or target.lower().startswith(SCHEMES):
            continue
        found.append(target.split("#", 1)[0])
    for match in TICK.finditer(line):
        span = match.group(1)
        if not PATH_SPAN.match(span):
            continue
        has_extension = span.rsplit(".", 1)[-1] in EXTENSIONS
        if "/" in span or has_extension:
            found.append(span)
    for match in WITH_EXTENSION.finditer(line):
        found.append(match.group(1))
    out = []
    for token in found:
        token = token.strip()
        if not token or token.lower().startswith(SCHEMES):
            continue
        if token not in out:
            out.append(token)
    return out


def check_paths(path, text, resolves):
    """resolves(token) -> bool. Returns findings for every named path that does
    not resolve and is not exempted by the line above it."""
    findings = []
    lines = text.split("\n")
    for number, line in enumerate(lines, 1):
        previous = lines[number - 2] if number >= 2 else ""
        exemption = EXEMPT.search(previous) or EXEMPT.search(line)
        for token in candidates(line):
            normalised = token[2:] if token.startswith("./") else token
            normalised = normalised.rstrip("/")
            if not normalised:
                continue
            if resolves(normalised):
                continue
            if exemption:
                continue
            findings.append(
                Finding(
                    path,
                    number,
                    "unresolved-path",
                    "names %s, which is neither tracked nor ignored" % token,
                )
            )
    return findings


def check_trailing_whitespace(path, text):
    findings = []
    for number, line in enumerate(text.split("\n"), 1):
        if line and line != line.rstrip():
            findings.append(
                Finding(
                    path,
                    number,
                    "trailing-whitespace",
                    "line ends in whitespace",
                )
            )
    return findings


def command_is_allowed(command, tracked):
    """A generated block may only name an interpreter running a tracked file in
    this repository, with no shell metacharacters. Anything else is refused as
    the block rather than run."""
    parts = command.split()
    if len(parts) < 2:
        return False, "is not an interpreter and a script"
    if parts[0] not in ("python", "python3"):
        return False, "does not start with python"
    if parts[1] not in tracked:
        return False, "runs %s, which is not tracked" % parts[1]
    for part in parts:
        if any(character in part for character in ";|&><$`\\"):
            return False, "carries a shell metacharacter"
    return True, ""


def generated_blocks(text):
    """(open_line, command, indent, body_lines) for every marked block."""
    blocks = []
    lines = text.split("\n")
    number = 0
    while number < len(lines):
        opening = GENERATED_OPEN.search(lines[number])
        if not opening:
            number += 1
            continue
        start = number
        command = opening.group(1)
        body = []
        number += 1
        while number < len(lines) and not GENERATED_CLOSE.search(lines[number]):
            body.append(lines[number])
            number += 1
        if number >= len(lines):
            blocks.append((start + 1, command, None, None))
            break
        blocks.append((start + 1, command, body, None))
        number += 1
    return blocks


def check_generated(path, text, root, tracked, run):
    findings = []
    for opened_at, command, body, _ in generated_blocks(text):
        if body is None:
            findings.append(
                Finding(
                    path,
                    opened_at,
                    "stale-generated-block",
                    "opens a generated block that is never closed",
                )
            )
            continue
        allowed, why = command_is_allowed(command, tracked)
        if not allowed:
            findings.append(
                Finding(
                    path,
                    opened_at,
                    "stale-generated-block",
                    "names the command %r, which %s" % (command, why),
                )
            )
            continue
        try:
            produced = run(command, root)
        except subprocess.CalledProcessError as failure:
            findings.append(
                Finding(
                    path,
                    opened_at,
                    "stale-generated-block",
                    "names the command %r, which exited %d rather than producing "
                    "the block" % (command, failure.returncode),
                )
            )
            continue
        # The block is written indented, which is how this tree writes output
        # inside a document. Compare on the unindented text and ignore the
        # blank lines the markers are separated by.
        have = [line[4:] if line.startswith("    ") else line for line in body]
        while have and not have[0].strip():
            have.pop(0)
        while have and not have[-1].strip():
            have.pop()
        want = produced.replace("\r\n", "\n").split("\n")
        while want and not want[-1].strip():
            want.pop()
        for index in range(max(len(have), len(want))):
            mine = have[index] if index < len(have) else None
            theirs = want[index] if index < len(want) else None
            if mine == theirs:
                continue
            if mine is None:
                detail = "is %d line(s) short of what %r produces; the first missing line is %r" % (
                    len(want) - len(have),
                    command,
                    theirs,
                )
            elif theirs is None:
                detail = "carries %d line(s) that %r does not produce; the first is %r" % (
                    len(have) - len(want),
                    command,
                    mine,
                )
            else:
                detail = "line %d of the block differs from %r: document has %r, the command produced %r" % (
                    index + 1,
                    command,
                    mine,
                    theirs,
                )
            findings.append(
                Finding(path, opened_at, "stale-generated-block", detail)
            )
            break
    return findings


def run_command(command, root):
    parts = command.split()
    if parts[0] in ("python", "python3"):
        parts[0] = sys.executable
    result = subprocess.run(
        parts, cwd=root, capture_output=True, check=True
    )
    return result.stdout.decode("utf-8")


def documents(root):
    names = [
        name
        for name in git("-C", root, "ls-files").split("\n")
        if name.strip().endswith(".md")
    ]
    return sorted(names)


def check_tree(root):
    tracked = tracked_paths(root)
    findings = []

    def resolves(token):
        if token in tracked:
            return True
        return ignored(root, token)

    for name in documents(root):
        with open(os.path.join(root, name), "r", encoding="utf-8") as handle:
            text = handle.read()
        findings.extend(check_trailing_whitespace(name, text))
        findings.extend(check_paths(name, text, resolves))
        findings.extend(check_generated(name, text, root, tracked, run_command))
    return findings


SELFTEST = [
    (
        "unresolved-path",
        "A link to [the notice](docs/no-such-file.md) is refused.\n",
        1,
    ),
    (
        "unresolved-path",
        "The reader lives in `internal/reader/` and is refused.\n",
        1,
    ),
    (
        "unresolved-path",
        "Run tools/absent.py to see nothing happen.\n",
        1,
    ),
    (
        "unresolved-path-exempted",
        "<!-- doc-check: unresolved-path the release writes it -->\n"
        "The run writes dist/report.json.\n",
        0,
    ),
    (
        "unresolved-path-not-a-path",
        "The area is `S = 6 * V^(2/3)` and the route is repos/owner/name/rulesets.\n",
        0,
    ),
    ("trailing-whitespace", "A line that ends in a space \n", 1),
    ("trailing-whitespace-clean", "A line that does not.\n", 0),
]


def selftest():
    """Every rule is given the smallest realistic violation and asserted to
    refuse it, and a near neighbour that it must not refuse."""
    failures = 0

    def resolves(token):
        return token in ("docs/present.md",)

    for name, text, expected in SELFTEST:
        if name.startswith("trailing-whitespace"):
            found = check_trailing_whitespace("fixture.md", text)
        else:
            found = check_paths("fixture.md", text, resolves)
        if len(found) != expected:
            failures += 1
            print(
                "selftest %s: expected %d finding(s), got %d: %s"
                % (name, expected, len(found), [str(f) for f in found])
            )
        else:
            print("selftest %s: %d finding(s), as required" % (name, expected))

    stale = check_generated(
        "fixture.md",
        "<!-- generated: python tools/fake.py -->\n"
        "    one\n"
        "    two\n"
        "<!-- end generated -->\n",
        ".",
        {"tools/fake.py"},
        lambda command, root: "one\nthree\n",
    )
    if len(stale) != 1:
        failures += 1
        print("selftest stale-generated-block: expected 1 finding, got %d" % len(stale))
    else:
        print("selftest stale-generated-block: 1 finding, as required")
        print("  " + str(stale[0]))

    fresh = check_generated(
        "fixture.md",
        "<!-- generated: python tools/fake.py -->\n"
        "    one\n"
        "    two\n"
        "<!-- end generated -->\n",
        ".",
        {"tools/fake.py"},
        lambda command, root: "one\ntwo\n",
    )
    if fresh:
        failures += 1
        print("selftest fresh-generated-block: expected 0 findings, got %d" % len(fresh))
    else:
        print("selftest fresh-generated-block: 0 findings, as required")

    refused = check_generated(
        "fixture.md",
        "<!-- generated: curl https://example.invalid -->\n"
        "    anything\n"
        "<!-- end generated -->\n",
        ".",
        set(),
        lambda command, root: (_ for _ in ()).throw(AssertionError("was run")),
    )
    if len(refused) != 1:
        failures += 1
        print("selftest disallowed-command: expected 1 finding, got %d" % len(refused))
    else:
        print("selftest disallowed-command: 1 finding, as required")
        print("  " + str(refused[0]))

    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", default=".", help="repository root to check, default the cwd"
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="run each rule against a fixture that violates it and one that does not",
    )
    arguments = parser.parse_args()

    if arguments.selftest:
        failures = selftest()
        if failures:
            print("%d selftest(s) failed" % failures)
            return 1
        print("every rule refused its fixture and passed its neighbour")
        return 0

    findings = check_tree(arguments.root)
    for finding in findings:
        print(str(finding))
    if findings:
        print(
            "%d refusal(s) across %d document(s)"
            % (len(findings), len({f.path for f in findings}))
        )
        return 1
    print("%d document(s) checked, nothing refused" % len(documents(arguments.root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
