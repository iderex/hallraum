# One machine is the ceiling

Written 2026-08-08.

This project is for somebody who has a computer. Everything on this board is
planned so that the useful case fits in one address space on commodity
hardware, and the point where it does not is stated in advance and refused
politely rather than discovered by a run that swaps for a week and then fails.

That is a constraint on the design and not an observation about whatever
hardware is to hand. Written down, it stops the plan drifting toward a solver
that only runs somewhere else, which is the drift that put wave based room
acoustics in institute codes in the first place.

## The figure, and what it is

The figure this board is written against is sixty-four gigabytes. It is
recorded in the issues rather than derived here:

    gh issue view 12 --repo iderex/hallraum --json body --jq '.body' | grep -c "sixty-four gigabytes"
    2
    gh issue view 16 --repo iderex/hallraum --json body --jq '.body' | grep -c "Sixty-four gigabytes"
    1

Both entries attribute it to the founding description of this project, as the
amount that makes the interesting range reachable on one machine. That is the
reason on the record and this document does not have a better one. It is not a
measurement of any machine, no machine here has been measured, and it is not
the memory of the machine the bench ran on. It is a planning figure: the
largest single address space the project assumes a reader can be expected to
have, and the number every prediction and every refusal is written against so
that they agree with each other.

Read as 64 GiB, which is 2^36 bytes, because that is what a machine reports.
The distinction from 64 GB costs about 7 per cent and is stated so that two
documents do not quietly disagree by that much.

## What the model says about the figure

`docs/memory-and-runtime-model.md` predicts the memory a volumetric grid method
needs as a function of room volume and upper frequency. In the band this
project names it does not come close to the figure. A 2000 m^3 hall at 300 Hz
predicts 4.11 MiB, and the interior arrays do not reach 64 GiB in that hall
until roughly 8 kHz.

So the one machine constraint is not, in the claimed band, a constraint about
that number. What binds first is elsewhere: the grid spacing set by the
geometric detail the model is asked to carry rather than by the wavelength,
the runtime, which carries the upper frequency a fourth time rather than a
third, and the accuracy of the wall model, which does not improve when the
machine gets bigger.

The constraint survives that unchanged, because it is about where the
computation happens and not about which resource runs out first. What moves is
what the ceiling documentation may claim: whichever resource binds, #83
publishes it from measurement, and a sentence that says memory without having
measured it would be the shape of claim this repository is least able to
afford.

## What the constraint forbids

Named, so that a later change that does one of these can be recognised as
crossing a line rather than as an optimisation.

A solve that spans more than one machine. #57 asks for the whole machine, and
the whole machine is where it stops. A distributed decomposition, a job
scheduler, or a message passing layer across hosts as a required path is
outside this plan.

A default path that relies on storage standing in for memory. A run whose
working set does not fit does not become slower, it becomes a different
computation with different arithmetic behaviour, and the honest response is to
refuse it rather than to start it. #59 is not this: a checkpoint that lets a
long run be resumed writes state deliberately at a chosen point, and it is
allowed.

A gate that needs a machine the plan does not assume. The unit suite in #20
runs on a stock runner with no accelerator and no elevation, which means
nothing that must run in the gate may need more than that. #129 is where
anything needing real hardware goes, named for what it is.

A sizing claim that is not about one machine. #124 generates the sizing guide
from the measured figures and takes the constraint from this document. #84
refuses a run that will not fit, and the thing it compares against is one
machine's memory rather than a pool.

What the constraint does not forbid is worth stating too, because both of the
obvious readings are wrong. It does not settle whether a vendor specific
accelerator path is supported: an accelerator sits in one machine, so entry 8
of #1 is untouched by this document and stays open. It also does not by itself
answer whether a room geometry may leave the host, which is the next section.

## Above the ceiling

Whatever the binding resource turns out to be, the behaviour is the same and it
is decided here rather than at the point of failure.

The run is refused before it starts, which is #84. What the software says is
the room and the upper frequency it was asked for, what the model predicts that
combination needs, and what is available on this machine, so that the numbers
are in front of the user rather than in a manual. #123 is the first run
equivalent for the operator, which reports what the machine has before any room
is loaded.

What it suggests is the levers that exist, and only those. A lower upper
frequency, which is cubic in memory and fourth power in runtime and is by a
long way the largest one. A coarser smallest represented feature, where the
geometric term is what set the spacing. A smaller room, where the user is
modelling more than they need. Each of those is a smaller question, not a
smaller answer, and what accuracy each one costs belongs with the accuracy
target in #15.

Where none of them helps, the software says so plainly: this room at this
frequency is not a case this tool computes on one machine, and no setting in it
changes that. Suggesting a cluster the user does not have, or starting a run
that cannot finish, are both worse than the sentence. There are rooms and
frequencies for which no amount of care makes one machine enough, and for those
this is not the right tool.

## Whether work may leave the host

Entry 4 of #1 asks whether room geometry may ever leave the host, and it is a
maintainer decision that is not answered here and is not assumed here:

    gh api repos/iderex/hallraum/issues/1/comments --jq 'length'
    0

The entry matters to this document because two of its three options change what
this document is. Under the first, the software never talks to a machine the
operator did not configure, and everything above is a property of the software.
Under the second and third an offload path exists, and everything above becomes
a statement about a default rather than about the software, with the ceiling
being where the offload starts rather than where the tool stops.

This document is written for the first option because that is the state the
project is in today, having no network path of any kind. It says so rather than
claiming it as a policy, and if the entry is answered differently the sections
above are the ones that change.

## What this does not do

It sets no number beyond the planning figure, and it measures nothing. The
memory figures it quotes are predictions from `docs/memory-and-runtime-model.md`
and carry that document's assumption set with them. What is actually reached on
a machine is #82, #85 and #83, and where those disagree with this, they are
right.

It also does not decide the upper frequency this project claims. That is #11,
and this document supplies it a constraint rather than an answer.
