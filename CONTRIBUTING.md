# Contributing

## Before anything else

Every change starts as an issue and lands as a pull request. An issue says what
is wrong, what the evidence is, and what done means. If the evidence is a
number, it carries the command that produced it.

Sign your commits off. Every non-merge commit needs a `Signed-off-by` trailer
matching its author, which `git commit -s` adds and `git rebase --signoff <base>`
adds retroactively to a branch you have not pushed. What you assert by adding it
is in `DCO`. The gate refuses a branch without it, and it refuses every commit
rather than the last one, so this is cheaper to get right the first time than to
repair afterwards.

Sign your commits as well, which is a different thing from signing them off. A
sign-off is a sentence you assert; a signature is what makes the history
attributable. Every commit on the default branch is verified today and nothing
requires it:

    gh api 'repos/iderex/hallraum/commits?per_page=100' --jq '[.[] | .commit.verification.verified] | {commits: length, verified: (map(select(.)) | length)}'
    {"commits":26,"verified":26}

    gh api repos/iderex/hallraum/rulesets/20527699 --jq '[.rules[].type]'
    ["deletion","non_fast_forward","pull_request"]

So this is practice rather than a rule, and issue #109 is the request that the
ruleset carry it. `PROSE, NOT ENFORCEMENT` until that is granted.

When signing fails, fix the signing. Do not turn it off, in either spelling:

    git commit --no-gpg-sign
    git -c commit.gpgsign=false commit

Neither is refused by anything here, which is exactly why the rule is written
down. Nothing in this tree reads a signature, so a bypassed commit builds and
reads like any other and the only thing that would say otherwise is the merge,
at the end of the line. Once #109 is granted, the repair for a branch carrying
one unsigned commit is to re-sign every commit onto a fresh branch and open the
landing again, not an exception, and that cost is paid after the work is
finished rather than before it.

## Building

There is nothing to build. This repository holds documents, a bench that
measures other people's solvers, and the tools that guard its own text. No
language has been chosen for the software itself; that is issue #17 and it waits
on the decisions in issue #1.

That is a fact about today rather than a plan, and it is checkable:

    git ls-files '*.csproj' '*.sln' 'go.mod' 'Cargo.toml' 'pyproject.toml' 'CMakeLists.txt'

When issue #17 lands and issue #19 adds the build check, this section says how to
build and what to expect, and the sentence above comes out.

## Testing

There is no test suite for software that does not exist. What runs today is the
guards, each of which proves itself before it judges anything, and the bench.

    python tools/doc-check.py --selftest
    python tools/doc-check.py --root .
    python tools/text-guard.py --self-test
    python tools/text-guard.py
    python bench/run.py --out bench/out/results.json

The two `--self-test` runs are not decoration. Each guard runs every one of its
rules against the smallest violation of that rule and against a near neighbour
it must not refuse, and fails if either answer moves. They run before the tree
scan so that a broken rule is reported as a broken rule rather than as a clean
tree.

Issue #20 adds the unit test check and issue #32 separates the fast suite from
the slow one. Issue #30 decides how a numerical result is compared, and until it
lands, no test in this repository should invent a tolerance of its own.

Nothing here needs elevation, an accelerator or a network. If a check ever does,
it does not belong in the gate: issue #129 is where work that needs real
hardware goes, and it is named for that.

## What the gate checks

The workflows are in `.github/workflows/` and each says at the top of its file
what it refuses and why. Read the file rather than a list here, because a list in
a document drifts against the thing it describes. What the workflow directory
holds today is printed by

    git ls-files .github/workflows/

Every one of them is read-only and none pushes. A job that reformats your work
and pushes the result hides the fact that your clone is configured differently
from the tree, which is the thing the text guard exists to make visible.

All checks have to be green before a merge.

## What a pull request body has to contain

The template in `.github/pull_request_template.md` has the headings and says
under each one what belongs there. Fill in every heading. A heading with nothing
under it is an unanswered question rather than one that does not apply.

The body is where a change is argued. If the body is wrong, incomplete or out of
date, edit the body rather than adding a comment underneath it.

## Every asserted fact carries the command that produced it

Run at the commit being pushed, and against the reference the reader will have
rather than against your working tree. Reading your own checkout and reporting it
as the mainline is the canonical form of this mistake and it is the largest
defect class the practice here is written against.

For a project whose output is numbers the rule has a sharper form and there is
no discretion in it.

A claim about accuracy carries the case, the tolerance and the command. "The
solver agrees with the closed form" is not a claim; "V2 of `docs/validation-set.md`,
tolerance 0.64 Hz on every mode below 300 Hz, achieved 0.21 Hz, from this
command" is.

A claim about speed or memory carries the machine, and it says whether the figure
was measured or predicted. Those are different words for different things:
`docs/memory-and-runtime-model.md` predicts, and its predictions are not
measurements of anything until issue #82 and issue #85 measure them.

A claim about another repository carries how you looked. A licence, a language
and a date from an API call are facts; "actively maintained" is an impression.
`docs/open-landscape-survey.md` is where that distinction is worked through at
length, including the places it answers "not determined" and says why.

Where a claim cannot be backed by a command, write it as a claim and say so. The
word "verified", the word "not measured" and the phrase "not evaluated on this
route" mean three different things and are not interchangeable.

## The means check

Before an artefact is built, whether the chosen means fits is argued in the issue
or in the pull request body. The means is the language, the format, the tool or
the runtime, whatever the thing will be made of. Every time, and never carried
over from the last change, because a means that was right for the last artefact
is an assumption about this one.

What recording the answer looks like is one or two sentences naming the means and
the reason it fits. The bench does it in its own readme: standard library Python
running each candidate as a child process, because the bench has to launch
foreign programs and time them, and because it must exist before the language
decision it is deliberately outside of. That is the shape. Not a checkbox, and
not a paragraph about how much you like a language.

What is checkable is that the question was asked, and only because the answer is
written down. Whether the answer was right is a judgement, no check makes it, and
the review is where a wrong one is caught.

## When a document states a rule and nothing refuses a violation

Mark it. Write `PROSE, NOT ENFORCEMENT` where a reader will see it, name the
issue that owes the mechanism, and open that issue if it does not exist.

A sentence in a document is not a rule; it is an explanation of one. If you
cannot name the check that refuses a thing, the mark is what keeps a reader from
believing something is enforced when it is not. Some rules can have no mechanism
here at all, and for those the mark is the end state rather than a placeholder.
Say which kind you are marking.

This document carries such a mark itself. Nothing reads the mark: it is a string
no check matches. Nothing in this repository judges whether a pull request body
contains the command behind its claims, whether a means check was recorded, or
whether a commit message says what failure it prevents. All of that is read by a
person or not at all, and this paragraph is the disclosure rather than a promise
that it will change.

## Style

English in artefacts. Commit messages state what changed and what failure it
prevents, and where a correction is being made they say what was wrong and how it
was found. One topic per commit and per pull request.

Text in this repository is UTF-8, stored with LF, with a final newline.
`.gitattributes` makes that true and `tools/text-guard.py` refuses the
departures, reading what git holds rather than what your checkout produced. A
fixture that has to carry a byte the normalisation would remove is stored
encoded, with the reason at the site.

A negative disclosure never becomes a positive assurance. If a passage admits
something was not done, that admission survives every later edit, and if anything
it gets sharper.
