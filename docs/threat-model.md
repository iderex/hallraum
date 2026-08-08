# Threat model

Written 2026-08-08.

Who this software has to defend against, what they are able to do, and what is
deliberately not defended against. Every security decision on this board is
argued against this document rather than against instinct, and a threat that is
accepted is accepted here in writing with the reason beside it.

## The shape, which is not the usual one

This is not a network service. It is a program a person runs on their own
machine, on a file somebody sent them, and what comes out is a number that
decides where money goes. The attacker is therefore not on the network. The
attacker is the author of the input, and the first asset below is the one a
threat model for a service would not have.

Almost none of that program exists yet:

    git ls-files | grep -cvE '^(\.github/|docs/|bench/|tools/|README|NOTICE|CONTRIBUTING|DCO|\.gitattributes)'
    0

So most of the mitigations named here are issues rather than code, and each one
says which it is. Writing the model first is deliberate: a threat model written
after the reader exists is a description of the reader.

Two surfaces in the tree today do take input from outside, and they are treated
below as real rather than as future. The bench launches other people's solvers
as child processes, and the documentation checker runs a command that a document
names.

## The assets

**The correctness of the result.** First, and an asset in its own right rather
than a quality attribute of another one. A result that is quietly wrong is a
successful attack on a tool whose output decides whether somebody spends money
on treatment, and the way to produce one is a crafted input rather than a
crafted packet. A tool that refuses has not been compromised. A tool that
returns a plausible curve for a room it misread has.

**The machine the run happens on.** An ordinary asset reached by an unusual
path. The input is a file format nobody has hardened, read by numerical code,
and the run is long enough that nobody is watching it while it happens.

**The room, the materials and any measurement.** A room geometry is a floor plan
of somebody's home, a material list says how a building is put together, and a
measurement made in a room can contain speech. Issue #113 states that as a claim
the software has to make true. This document states it as a thing worth taking.

**The integrity of what is published.** An operator is asked to run this on
their own hardware, which means they are asked to trust that what they fetched
is what was built. Issues #121 and #126 carry the mechanisms.

**Not the availability of a run.** Named here so that its absence from the
threats below is a decision rather than an oversight. A run that stops is
visible to the person who started it, and there is no service behind it whose
users would notice instead.

## The attacker positions

**The author of an input file.** First, and the position most of this document
is about. They choose every byte of a room file, a material table, a measured
impedance file or a result file handed to a reading command. They do not need an
account anywhere, and the user who opens the file has no reason to distrust it,
because a floor plan from a colleague is an ordinary thing to be sent.

**The author of a change proposed to this repository.** They choose the bytes of
a document, a workflow or, once there is code, the code. They cannot merge, but
what they send is read and in two cases executed.

**Whoever can publish a version of something this project depends on.** Nothing
is declared as a dependency today, which is measured under the dependency threat
below rather than assumed here.

**Somebody who already runs code as the user who runs this.** Mostly out of
scope, and the reason is under the exclusions.

**A network position.** Empty by construction today, because nothing here opens
a connection. Whether it stays empty is not settled: entry 4 of issue #1 decides
whether a computation may ever be offloaded, and entry 6 decides telemetry.
Until both are answered this position is empty by absence rather than by
decision, and that is a weaker statement.

## The threats

Each one names what would go wrong, then the mitigation and the issue that
delivers it, or says it is accepted and why.

**A crafted room file reaching memory corruption or code execution in the
reader.** The reader takes bytes from a stranger and is the first thing that
touches them. Mitigated by issue #35, which refuses a file that is not a room,
by issue #45, which puts hostile files in a unit suite over the reader, and by
issue #104, which fuzzes the surfaces that take bytes from strangers. All three
wait on the language decision in issue #17, and what a room is allowed to be is
already settled in `docs/what-a-room-is.md`, so the refusal has a rule to refuse
against before the reader is written.

**A room file that is accepted and produces a quietly wrong number.** The
attack on the first asset, and the one that needs no memory error at all.
Geometry that is not watertight, a material extrapolated below the lowest band
that has data, a run that ended before the field decayed, a receiver reported at
a position it was not evaluated at. Mitigated by issue #44, which validates the
problem before solving it and fails closed, by issue #36 for watertightness, and
by issue #97, which reports the conditions that explain a disagreement from the
result file alone. The rule that decides between refusing and marking is issue
#15, which waits on entry 3 of issue #1.

**A room file whose cost is the attack.** A geometry and an upper frequency
whose grid does not fit in the memory of the machine, submitted so that the run
exhausts it. Mitigated by issue #84, which refuses a run that will not fit
before it starts, against the prediction in `docs/memory-and-runtime-model.md`
and the ceiling in `docs/one-machine.md`.

**A crafted result file read by a command that inspects it.** A result file is
the thing people send each other, so the reading side is a second input surface
with the same attacker in front of it. Issues #92 and #97 own it. Recorded here
because it is easy to harden the room reader and forget that the result reader
takes bytes from the same stranger.

**A document in a proposed change making the documentation checker run
something.** Live today, and mitigated today. A generated block names the
command that produced it and the checker runs that command, so a document is a
route to execution on the runner unless the command is constrained. It is:

    python tools/doc-check.py --selftest

`command_is_allowed` in `tools/doc-check.py` accepts only `python` or `python3`
followed by a path that is tracked in this repository, and refuses any argument
carrying a shell metacharacter. A block naming anything else is reported as a
refusal rather than run. The bound is that a tracked script is trusted once it
is tracked, so this constrains a document and not a change that adds a script.

**A candidate solver run by the bench doing something to the machine.**
Accepted, with the reason at the surface. `bench/adapters/__init__.py` states
that the runner never imports a candidate and launches it as a child process
instead, which is there for measurement rather than for containment, and it does
bound the blast radius. Beyond that, running a research code on your own machine
is what the bench is for, and a sandbox around it would be a second apparatus
for a tool that is deliberately outside the software this project ships.
Whoever runs the bench chooses the candidates.

**Invisible characters in tracked text changing what a reader believes it
says.** Mitigated and running, in `.github/workflows/unicode-guard.yml`.

**Stored bytes differing between clones, so that what one reader reviews is not
what another gets.** Mitigated and running, in `tools/text-guard.py` and
`.github/workflows/text-guard.yml`, which read what git holds rather than what a
checkout produced.

**A workflow with more permission than it needs, or one that interpolates
untrusted input into a shell.** Mitigated and running, in
`.github/workflows/zizmor.yml`.

**A dependency arriving with a known advisory.** `.github/workflows/dependency-review.yml`
runs on every pull request. It is green today because there is nothing declared
for it to review rather than because anything was checked, which is measured on
issue #23. Issue #23 also owes the bill of materials and the licence gate.

**A change reaching the default branch that nobody can attribute.** Accepted
today, and the request to stop accepting it is issue #109. Every commit on the
default branch is signed, but nothing requires that, so the property holds by
practice.

**A red check not stopping a merge.** The largest live gap in this list, and it
undercuts every mitigation above that is a workflow. The ruleset requires a pull
request and refuses a force push and a deletion, and it requires no check to
have passed:

    gh api repos/iderex/hallraum/rulesets/20527699 --jq '{enforcement, bypass: .bypass_actors, types: [.rules[].type]}'
    {"bypass":[],"enforcement":"active","types":["deletion","non_fast_forward","pull_request"]}

Accepted until issue #33 is granted, which is a repository setting rather than a
change to this tree. Every check named in this document as mitigating something
is advisory until then.

**A published artefact that is not what the source builds.** Mitigated by issue
#121, which asks that two builds from the same source produce the same digest,
and by issue #126, which signs and publishes the release artefacts.

**A room leaving the host.** Nothing here opens a connection and nothing can
today. Whether that becomes a property or stays an accident is entry 4 of issue
#1, and the statement that has to be made true is issue #113, which asks for a
test asserting no endpoint is contacted during a full run.

## Deliberately out of scope

**An attacker who already runs code as the user who runs this.** Everything this
tool would protect from them is already theirs: the room files are in their home
directory and the results are written with their rights. A defence would have to
assume the operating system is on our side against its own user, which it is
not.

**Multi-tenant isolation.** Nobody shares an instance of this, because there is
no instance to share. If entry 4 of issue #1 is ever answered by allowing
offload, this exclusion is void and the model is rewritten before that lands
rather than after.

**A network attacker.** No connection is opened, so there is nothing in the
middle to attack. This exclusion depends on the previous one and on entry 6 of
issue #1 staying answered the same way.

**Denial of service.** Covered under the assets: a run that stops is visible to
the person who started it, and no third party is waiting on it. The one case
that is in scope is the cost attack above, and it is in scope because refusing
early is cheap rather than because the stopped run matters.

**A side channel from the run to another process on the same machine.** Timing
and memory pressure during a run do leak something about the size of the room.
The attacker who could read it is the one already excluded above.

**Whether published material data is physically right.** A correctness question
rather than a threat, and it belongs to the validation work in
`docs/validation-set.md`. It becomes a threat only if the project ships data it
did not measure, which is entry 5 of issue #1.

## What this document does not reach yet

Issue #115 asks that the security documentation and the reader hardening work
both point here. Neither exists. There is no security policy in the tree, which
is issue #116, and the reader is issue #35 and waits on issue #17. So that
condition is outstanding, and it is outstanding on other issues landing rather
than on anything missing from this document.

The threats above are mapped to issues, which is what the issue asks for and is
weaker than being mapped to code. An issue is a plan. The mitigations that are
running today are named as running and the rest are named as owed, and the
difference between those two words is the whole value of the list.

Nothing here has been read by a second person. The commands are in place of that
rather than beside it.
