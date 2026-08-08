"""Refuse tracked text that is not deterministic.

This project compares text against stored text. The input files are text, the
expected outputs will be text, and a comparison against a stored expectation is
a test that quietly depends on a checkout setting unless the bytes in the
repository are fixed. This program fixes them by refusing the departures.

    python tools/text-guard.py              scan the tracked tree
    python tools/text-guard.py --self-test  run the cases that prove it bites

It judges the bytes git holds, taken from the index, and never the bytes in the
working tree. A checkout that converts line endings puts carriage returns in the
working tree that the stored blob does not have, so a guard reading the working
tree fails over the whole tree on such a clone for a reason that is the clone
rather than the change. That is a defect this program is written not to have.

One thing here is not read from the index and cannot be: git check-attr
resolves a path's attributes from the .gitattributes in the working tree, so
the text and eol answers below come from that file rather than from the stored
one. Where the two differ the guard is judging the working tree, and the case
that exposed it was removing .gitattributes from the index while leaving it on
disk, which left every path still resolving and every rule still silent. The
hole is closed by refusing a tree whose .gitattributes is not tracked at all,
which is the attributes-not-tracked rule, rather than by pretending check-attr
reads the index.

Standard library only, and git is called as a child process rather than
imported, so nothing is added to the tree that has to be maintained.
"""

import argparse
import subprocess
import sys

BOM = b"\xef\xbb\xbf"

# Every rule, with the failure it prevents. The id is what a refusal prints and
# what the self-test names, so the two cannot drift apart.
RULES = {
    "carriage-return":
        "a stored carriage return makes a comparison against this file depend "
        "on the checkout that produced it",
    "byte-order-mark":
        "a leading byte order mark is invisible in a diff and is read as data "
        "by a parser that starts at the first byte",
    "not-utf-8":
        "a file that is not UTF-8 decodes differently depending on the locale "
        "of whoever reads it",
    "missing-final-newline":
        "a missing final newline makes the next change touch a line it did not "
        "change",
    "attr-text-unspecified":
        "a path no rule in .gitattributes reaches is normalised by whatever "
        "the clone was configured with",
    "attr-eol-not-lf":
        "a path checked out with anything but LF gives two contributors two "
        "different files under one name",
    "binary-without-reason":
        "a pattern that turns normalisation off is how a fixture stops being "
        "text, and one with no reason beside it cannot be reviewed",
    "attributes-not-tracked":
        "with no tracked .gitattributes every clone normalises by its own "
        "configuration, and the attributes the rules above read then come from "
        "a working tree file nobody has to have",
}


def git(*args):
    r = subprocess.run(("git",) + args, capture_output=True)
    if r.returncode != 0:
        sys.stderr.write("git %s failed: %s\n"
                         % (" ".join(args), r.stderr.decode("utf-8", "replace")))
        raise SystemExit(2)
    return r.stdout


def tracked():
    """Every tracked path with the object git holds for it. Reading the id from
    the index rather than naming the path to cat-file keeps a path that looks
    like an option or a revision from being read as one."""
    out = git("ls-files", "-s", "-z").split(b"\0")
    for entry in out:
        if not entry:
            continue
        meta, _, path = entry.partition(b"\t")
        fields = meta.split()
        yield path.decode("utf-8", "surrogateescape"), fields[1].decode()


def attributes(paths):
    """The text and eol attributes git resolves for each path."""
    stdin = "\0".join(paths).encode("utf-8", "surrogateescape")
    r = subprocess.run(["git", "check-attr", "-z", "--stdin", "text", "eol"],
                       input=stdin, capture_output=True)
    if r.returncode != 0:
        sys.stderr.write("git check-attr failed: %s\n"
                         % r.stderr.decode("utf-8", "replace"))
        raise SystemExit(2)
    fields = r.stdout.split(b"\0")
    resolved = {p: {} for p in paths}
    for i in range(0, len(fields) - 2, 3):
        path = fields[i].decode("utf-8", "surrogateescape")
        resolved.setdefault(path, {})[fields[i + 1].decode()] = \
            fields[i + 2].decode()
    return resolved


def check_attrs(attrs):
    """Refusals that come from what .gitattributes says about a path."""
    found = []
    text = attrs.get("text", "unspecified")
    if text == "unspecified":
        found.append(("attr-text-unspecified", "no text attribute is set"))
        return found
    if text == "false":
        # Declared not text on purpose. The reason for that declaration is
        # checked at .gitattributes rather than here, and the byte rules below
        # do not apply to it.
        return found
    eol = attrs.get("eol", "unspecified")
    if eol != "lf":
        found.append(("attr-eol-not-lf", "eol is %s" % eol))
    return found


def check_bytes(data):
    """Refusals that come from the bytes git holds."""
    found = []
    if b"\r" in data:
        found.append(("carriage-return",
                      "%d carriage return(s)" % data.count(b"\r")))
    if data.startswith(BOM):
        found.append(("byte-order-mark", "starts with EF BB BF"))
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        found.append(("not-utf-8", "byte %d does not decode" % exc.start))
    if data and not data.endswith(b"\n"):
        found.append(("missing-final-newline", "last byte is not LF"))
    return found


def check_attributes_file(text):
    """A pattern that turns normalisation off needs its reason on the line
    above it. Marking a fixture binary is how a byte this guard removes gets
    kept deliberately, and a reader has to be able to see why."""
    found = []
    previous = ""
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        turns_off = (stripped and not stripped.startswith("#")
                     and any(token in stripped.split()[1:]
                             for token in ("-text", "binary")))
        if turns_off and not previous.strip().startswith("#"):
            found.append(("binary-without-reason",
                          ".gitattributes:%d: %s" % (number, stripped)))
        previous = line
    return found


def check_attributes_tracked(paths):
    """The attributes file has to be in the index. check-attr answers from the
    working tree, so a tree that carries .gitattributes on disk and not in git
    resolves every path and refuses nothing, while a fresh clone of it has no
    normalisation at all. This is the rule that refuses that tree."""
    if ".gitattributes" in paths:
        return []
    return [("attributes-not-tracked", "no .gitattributes is tracked")]


def scan():
    paths = list(tracked())
    resolved = attributes([p for p, _ in paths])
    refusals = []
    for path, blob in paths:
        attrs = resolved.get(path, {})
        found = check_attrs(attrs)
        if attrs.get("text", "unspecified") not in ("false",):
            found += check_bytes(git("cat-file", "blob", blob))
        refusals += [(path, rule, detail) for rule, detail in found]
    names = {p for p, _ in paths}
    absent = check_attributes_tracked(names)
    refusals += [(".gitattributes", rule, detail) for rule, detail in absent]
    if not absent:
        text = git("show", ":.gitattributes").decode("utf-8")
        refusals += [(".gitattributes", rule, detail)
                     for rule, detail in check_attributes_file(text)]
    for path, rule, detail in refusals:
        print("%s: %s: %s" % (path, rule, detail))
        print("    %s" % RULES[rule])
    print("%d tracked file(s) examined, %d refusal(s)."
          % (len(paths), len(refusals)))
    return 1 if refusals else 0


# Each rule gets a case that must be refused and a neighbour that must not.
# The neighbour is the one-character mistake somebody would actually make:
# a carriage return written as two characters, a byte order mark that is not
# at the start, a file that is empty rather than unterminated.
BYTE_CASES = [
    ("carriage-return", b"one\r\ntwo\n", b"one\\r\\ntwo\n"),
    ("byte-order-mark", BOM + b"one\n", b"one" + BOM + b"\n"),
    ("not-utf-8", b"\xff\xfe\x00o\n", b"\xc3\xa4\n"),
    ("missing-final-newline", b"one", b""),
]

ATTR_CASES = [
    ("attr-text-unspecified", {}, {"text": "auto", "eol": "lf"}),
    ("attr-eol-not-lf", {"text": "auto", "eol": "crlf"}, {"text": "false"}),
]

TRACKED_CASES = [
    ("attributes-not-tracked", {"README.md"}, {"README.md", ".gitattributes"}),
]

ATTRIBUTES_CASES = [
    ("binary-without-reason",
     "*.raw -text\n",
     "# The fixture below is bytes on purpose, and the reason is here.\n"
     "*.raw -text\n"),
]


def self_test():
    failures = 0
    for rule, refused, allowed in BYTE_CASES:
        failures += report(rule, "refused", rule in ids(check_bytes(refused)))
        failures += report(rule, "neighbour",
                           rule not in ids(check_bytes(allowed)))
    for rule, refused, allowed in ATTR_CASES:
        failures += report(rule, "refused", rule in ids(check_attrs(refused)))
        failures += report(rule, "neighbour",
                           rule not in ids(check_attrs(allowed)))
    for rule, refused, allowed in TRACKED_CASES:
        failures += report(rule, "refused",
                           rule in ids(check_attributes_tracked(refused)))
        failures += report(rule, "neighbour",
                           rule not in ids(check_attributes_tracked(allowed)))
    for rule, refused, allowed in ATTRIBUTES_CASES:
        failures += report(rule, "refused",
                           rule in ids(check_attributes_file(refused)))
        failures += report(rule, "neighbour",
                           rule not in ids(check_attributes_file(allowed)))
    missing = sorted(set(RULES) - covered())
    for rule in missing:
        failures += report(rule, "has a case", False)
    print("%d case(s), %d failure(s)."
          % (2 * len(BYTE_CASES + ATTR_CASES + ATTRIBUTES_CASES + TRACKED_CASES)
             + len(missing), failures))
    return 1 if failures else 0


def covered():
    return {rule for rule, _, _ in
            BYTE_CASES + ATTR_CASES + ATTRIBUTES_CASES + TRACKED_CASES}


def ids(found):
    return {rule for rule, _ in found}


def report(rule, leg, ok):
    print("%-24s %-10s %s" % (rule, leg, "ok" if ok else "FAILED"))
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--self-test", action="store_true",
                   help="run the cases that prove each rule bites")
    a = p.parse_args()
    return self_test() if a.self_test else scan()


if __name__ == "__main__":
    raise SystemExit(main())
