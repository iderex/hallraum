# Parity with the reference gate

The gate this repository is held to is the one running on
github.com/iderex/jellyfin-plugin-sso. It is public, its ruleset is readable,
and it is a standard that exists rather than one invented here. This document
records, element by element, whether this repository adopts it, adapts it or
drops it, and what it adds that the reference does not have.

Parity is not copying. That gate is for a plugin loaded into somebody else's
process, where the threat is what the plugin does to its host and to the
credentials passing through it. This is a program a person runs on their own
machine against a file they were sent, whose output is a number somebody will
spend money on. Some of that gate does not apply here, and some of what this
project needs is not there at all.

## What each gate requires today

Run at the commit this document landed at.

    gh api repos/iderex/jellyfin-plugin-sso/rulesets --jq '.[] | [.id,.name,.enforcement] | @tsv'
    18802863	Protect main and 5.0	active

    gh api repos/iderex/jellyfin-plugin-sso/rulesets/18802863 --jq '{enforcement, bypass: .bypass_actors, required: [.rules[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context]}'
    {"bypass":[],"enforcement":"active","required":["build","ABI floor build","Package (JPRM) / Build package","Package (JPRM) / Generate SBOM","CodeQL","Analyze (csharp)","DCO sign-off","Deterministic PR-hygiene checks","Enforce greppable invariants","Reject Trojan Source Unicode","Audit workflows (zizmor)","prettier","dependency-review"]}

    gh api repos/iderex/hallraum/rulesets/20527699 --jq '{enforcement, bypass: .bypass_actors, types: [.rules[].type]}'
    {"bypass":[],"enforcement":"active","types":["deletion","non_fast_forward","pull_request"]}

So the distance is the whole list. This repository refuses a deletion, refuses a
non-fast-forward push and requires a pull request, and requires no check to have
passed. Every check already in this tree is advisory, and so is every check the
quality milestone adds until the ruleset names it. #33 is the request that it
does, and it carries the names taken from completed runs.

The lists below are not restated from anywhere. The reference's required
contexts come from the second command above, and its full set of workflows from

    gh api repos/iderex/jellyfin-plugin-sso/contents/.github/workflows --jq '.[].name'

## The required contexts, one at a time

**build.** The reference builds its package through a reusable workflow. Adopted
in substance and delivered by #19, which asks for a build of the whole tree from
a clean checkout with warnings as errors. Waits on the language decision, #17.

**ABI floor build.** The reference builds against the oldest host application
version it claims to support, so that a change using a newer interface is caught
before a user meets it. Dropped. This program is not loaded into anybody else's
process and has no host interface to hold a floor against. What replaces it in
kind, a promise about what a version number means for a result, is #125.

**Package (JPRM) / Build package.** Packaging for a plugin catalogue. Adapted:
the artefact here is a container image and a bundle that runs on one machine,
which are #121 and #122.

**Package (JPRM) / Generate SBOM.** Adopted and delivered by #23. The reference
generates it as part of packaging; here it is asked for on every build, which is
a small deviation upward and is the shape #23 already asks for.

**CodeQL** and **Analyze (csharp).** A code scanning gate, required as two
contexts because the workflow name and the matrix job name are both listed.
Adapted and delivered by #100, which asks for a code scanning gate for whatever
language this repository turns out to be written in. Waits on #17.

**DCO sign-off.** Adopted, and already in this tree. The certificate it asserts
landed in #130 and #25 holds the remaining half, which is the sentence in the
contribution guide.

**Deterministic PR-hygiene checks.** Adopted and delivered by #106.

**Enforce greppable invariants.** The reference runs a pattern lint over its own
tree. Adopted in shape and adapted in content by #105: the invariants worth
refusing here are specific to this project, a physical constant written as a
literal outside the one place constants are defined being the clearest of them.
The check is language independent in mechanism and its content is not, so it
waits on #17 for the parts that name source constructs.

**Reject Trojan Source Unicode.** Adopted, already in this tree, and unchanged
from the reference.

**Audit workflows (zizmor).** Adopted, already in this tree, and unchanged from
the reference.

**prettier.** A formatter for the documents and configuration of one language.
Adapted in two directions. Formatting for every language in the tree is #21,
which waits on #17 because the number of formatters is the number of languages.
Formatting and linting of the documentation is #107, which here carries more
load than at the reference: most of what this project claims about accuracy
lives in prose, and prose that drifts from the software is what this repository
is most exposed to.

**dependency-review.** Adopted, already in this tree, and unchanged from the
reference.

## Elements of the reference gate that are not required contexts

**A coverage bar.** The reference enforces a threshold on the modules that
decide security outcomes rather than on the whole codebase, so that a thin
non-critical path cannot trip it and a regression on a decision path cannot slip
through it. Adopted in exactly that shape by #102, with the surface that decides
a number standing where the reference puts the surface that decides an
authorisation. Waits on #17.

**Mutation testing.** Reporting rather than gating, on a weekly schedule at the
reference. Adopted with the same posture by #103.

**Fuzzing.** On a weekly schedule at the reference. Adopted by #104, aimed at
the surfaces that take bytes from strangers, which here is the geometry and
material reader rather than an authentication path.

**An end to end run.** The reference logs in against a real host application on
a daily schedule. Adapted rather than dropped: the equivalent here is a run of
the whole tool on a room, which is #95 as an example a user can follow and #128
as the release readiness check. Neither needs a second application to be present.

**Documentation lint on a schedule.** The reference lints its wiki weekly.
Adapted into #107, which runs in the gate rather than on a schedule, because the
documents here are in the repository rather than in a separate wiki.

**Scorecard.** Adopted and already in this tree. It is deliberately not on the
required list, for the reason recorded in #33: it never appears on a pull
request.

**A second analyser with a different lens.** The reference runs a pattern based
analyser beside its code scanning one. Adopted by #101.

**Publication machinery.** The reference carries a release publish workflow, a
nightly beta dispatch, a manifest regeneration, a manifest freshness assertion
and an alert on a failed publish. The manifest elements are dropped: they keep a
plugin catalogue truthful and there is no catalogue here. Publishing and signing
release artefacts is adopted as #126, and #112 covers the third party notices
that ship with them.

**A workflow failure alert on the default branch.** Adopted in intent by #80,
which asks that a failure of the scheduled validation raise something a person
sees. Nothing else on this board holds the general case, and it is not claimed
here that it does.

## What this repository adds that the reference does not have

**A validation gate.** The reference has no equivalent, because its output is a
behaviour rather than a number. Cases with an answer that is not ours are the
whole of milestone M5, and #80 guards those numbers against regression on a
schedule. This is the largest deviation upward in this document.

**A memory and runtime regression guard.** A change that doubles the cost of a
run is a defect here and is nothing at the reference. #82 and #85 measure, #87
soaks a long run, and #84 refuses a run that will not fit before it starts.

**Determinism of the test harness.** Fixed seeds, injected time, no network, and
a statement of which code paths are bit reproducible. #29, with the floating
point contract it depends on in #31. The reference has no arithmetic to be
reproducible about.

**A stated way of comparing two curves.** #30. A suite whose every test invents
its own tolerance is a suite nobody can defend, and this is the failure mode the
reference cannot have.

**Two suites, named for what they are.** #32. A convergence study and a run long
enough for a lightly damped mode to decay are real tests that do not belong on
every pull request, and a test that is in neither suite is refused.

**Verified signatures on the protected branch.** A deviation upward, asked for
in #109. The reference ruleset output above carries no signature requirement.

**Architecture rules as tests.** #108, which the reference does not have.

**Deterministic text in the tree.** #28 fixes line endings and encoding, which
matters more here than at the reference because the inputs and the expected
outputs are both text and a stored expectation would otherwise depend on a
checkout setting.

## What waits on a decision rather than being dropped

Every element above marked as waiting on #17, the language and toolchain choice,
waits through it on entry 2 of #1, whether this project writes a solver at all.
That entry has no answer:

    gh api repos/iderex/hallraum/issues/1/comments --jq 'length'
    0

The elements concerned are the build check, the formatter and lint checks, the
static analysis and code scanning gates, the coverage bar, and the source
construct half of the greppable invariants. None of them is dropped and none of
them can be written against a language that has not been chosen.

The accelerator path is the second decision that reaches this document. Whether
a vendor specific toolchain is a supported path is entry 8 of the same issue, and
it decides whether the build check has one configuration or two and whether the
integration harness in #129 has hardware to run on.

## What this document does not do

It records a mapping and it does not deliver any of it. Every element above that
is adopted or adapted names an issue on this board, and naming one is not the
same as that issue being done: at the time this landed, none of the checks it
maps had been added.

The list of what this repository adds is derived from what this board already
holds, milestone by milestone. Something this project will need and has no issue
for does not appear in it, and would not have been noticed by writing this.

It is also a comparison made from the reference's ruleset and workflow files
rather than from watching its gate refuse anything. What each of its checks
actually catches is not established here, and where this document says an
element is adopted in substance, that is a judgement about intent rather than a
measurement of behaviour.
