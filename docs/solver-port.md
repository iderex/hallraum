# The solver port

Written 2026-08-08.

Everything above the numerical core is written against this port and not against
a method. Two futures need that and they are both live. A method chosen today is
wrong for some room somebody wants next year, and the survey in
`docs/open-landscape-survey.md` found solvers this project could drive instead
of writing one, which is entry 2 of issue #1 and is not decided here.

This document is the interface. It is written in prose and in a neutral
schematic rather than in a language, because the language decision is issue #17
and is open. A port described in a language nobody has chosen would have to be
rewritten the day that issue lands, and the thing it is trying to fix, which is
callers reaching around it, is not a syntax problem.

## What the port is for

The port is the narrow place. Above it sits everything a user touches. Below it
sits one method. The test of the design is not that it compiles but that three
unlike methods fit behind it without any of them leaking upward, and the
walk-through near the end is where that is checked rather than asserted.

## Units and sign conventions, once

Every quantity crossing the port is in base SI units and this is the only place
that says so. A number crossing the port carries no unit of its own and no
prefix, so a frequency is in hertz and never in kilohertz, and a length is in
metres and never in millimetres.

Pressure is in pascals. Length is in metres. Time is in seconds. Frequency is in
hertz. Density is in kilograms per cubic metre. Temperature is in kelvin.
Relative humidity is a fraction between zero and one, not a percentage.

Specific acoustic impedance is in pascal seconds per metre. It crosses the port
in that form and never normalised, because normalising it hides which
characteristic impedance was used and two documents that assume different air
conditions then disagree silently.

A surface normal points out of the air and into the wall. Every impedance is
stated with respect to that normal. This is a choice and not a fact, and the
reason it is written here is that the two conventions differ by a sign that
turns an absorbing wall into an active one.

The time convention for a complex spectrum is that a harmonic quantity varies as
the real part of a complex amplitude multiplied by e to the power of j omega t,
with omega positive. The conjugate convention appears in parts of this
literature, so a solver behind the port that works internally in the other one
converts at the port and does not export the choice.

A transfer function crossing the port is the complex pressure at a receiver
divided by the source strength that produced it, where the source strength is
whatever the source description below declares it to be. It is not normalised by
distance, by a free-field reference, or by anything else. Every normalisation
people actually want is a presentation decision and lives above the port, where
it can be labelled.

## What crosses, going down

The problem. One value, and every field in it is required unless the text says
otherwise.

The room. Its geometry, in the form issue #10 settles, and its air. Geometry
crosses as surfaces with an identity, not as a mesh, and this is the first place
the port refuses something a caller might expect to send. The issue that asks for
this port describes a discretised room crossing it. That is exactly what must not
cross, because a discretisation carries a grid spacing and a grid spacing is the
method's business. What crosses instead is the geometry and one physical
statement about how finely it must be honoured, described below. The method
meshes it.

Air crosses as temperature, relative humidity and static pressure, and the
solver derives the speed of sound and the density from them. It does not cross
as a speed of sound, because two callers that each computed one from the same
conditions with different formulas would disagree for a reason nobody can see.

The material at every surface. One description per surface identity, and the
port carries all three rungs of issue #8 in one type rather than three:

    rigid                       no parameters
    real absorption             one coefficient per named frequency band
    surface impedance           a complex value per frequency on a declared grid

The port carries what the user has. It does not carry a fitted filter, a set of
pole-residue pairs, or a boundary update rule, because those are how a
particular method turns an impedance into a wall, and a caller that supplied one
would be choosing the method. Fitting happens below the port. What comes back up
about the fit is in the result.

An absorption coefficient carries no phase and a solver that receives one is
being asked to invent the phase it needs. That is not hidden here. The solver
declares what it did, in the result, and issue #68 is where the loss is written
down for a user.

Sources and receivers. Each has a position in metres in the room's own
coordinates, and issues #42 and #43 settle what else. A source carries the
quantity its strength is measured in, so that the transfer function definition
above has a denominator. A receiver is a point. The port has no microphone,
because a microphone is a directivity and a mount and a preamplifier, and none of
those is a thing a solver knows.

The frequency range. A lowest and a highest frequency in hertz, and the
frequencies at which an answer is wanted. The port carries the wanted
frequencies explicitly rather than a count and a spacing, so that a caller asking
for a third-octave grid and a caller asking for one hertz steps are the same call.

The smallest feature the geometry must honour, in metres. This is the physical
half of what a grid spacing usually smuggles across. It says how much geometric
detail matters, which is a statement about the room and about what the user
wants to know. What spacing that implies is the method's arithmetic.

The accuracy target. What issue #15 settles, expressed as a bound on the error
in the returned response, and the band over which the bound applies. It crosses
as a requirement and not as a tolerance on an iteration, because the second one
is a method's internal knob wearing the first one's name.

## What crosses, coming back

The result. It is one of two things and a caller has to handle both, which is
the point of stating it here rather than in a paragraph about errors.

An answer. The complex response at every receiver at every requested frequency,
in the units above. An error estimate the solver is willing to stand behind, per
frequency, with the word for how it was obtained: derived, meaning it follows
from the discretisation and the scheme; measured, meaning it comes from a
refinement study this run performed; or estimated, meaning neither, and then the
solver says what it is. A cost record: wall clock time, peak memory, and what
the run actually did, which is what issues #82 and #85 measure against. And a
statement of what the solver did with each material description it was given,
including the phase it invented for any real absorption coefficient and the
error of any impedance fit.

A refusal. The solver could not meet the accuracy target, and says so instead of
returning a number. A refusal carries which part of the problem it could not
meet, the bound it could actually reach if it were allowed to try, and what
would have to change for it to succeed, in the vocabulary of the problem the
caller sent rather than in the method's own. A lower upper frequency, a coarser
smallest feature, a smaller room, a material description it can represent. Those
are the levers `docs/one-machine.md` already names, and a refusal names the ones
that apply.

A refusal is a value and not an exception. A method that cannot reach the target
is the ordinary case near the top of the band, it is what issue #52 is about, and
a design that makes it an exception makes the caller's happy path a lie. It is
also the same shape as the refusal in issue #84, which happens before a run
starts rather than after, and the two are deliberately the same type so that the
user-facing code has one path.

## The operations

Three, and no more.

Ask what a solver can do, given nothing. It returns what it is, what material
descriptions it accepts, whether it can answer at all in the frequency domain
directly, and the limits it knows about itself before seeing a problem. This
exists so that the layer above can refuse early and can tell a user which solver
is behind it without running one.

Ask what a problem would cost, given a problem. It returns the memory and the
time it predicts, or a refusal, and it does not solve. This is what issue #84
calls before it starts anything and what the sizing guide in issue #124 is
generated from. A solver that cannot predict says so here rather than returning a
guess, and the layer above then knows it is flying blind.

Solve, given a problem. It returns the result above. It reports progress, because
issue #91 needs a run of hours to say what is happening, and progress is a
fraction and a phase name and nothing richer, since anything richer would be the
method's internals crossing the port. It can be asked to stop, and stopping
yields a refusal that says it was stopped rather than a partial answer, because a
partial answer with no label is the worst thing this port could hand upward.

Checkpointing, which issue #59 asks for, is inside solve and does not appear as
an operation. A checkpoint is a method's own state, it is meaningless to anyone
else, and a port that carried it would be carrying the method.

## What deliberately does not cross, and why

Grid spacing, element size, and polynomial order. They are the method's
arithmetic, derived from the smallest feature and the upper frequency that do
cross. A caller who set one would have to know which method is behind the port,
and the port would have bought nothing.

The time step. Issue #51 says it is derived from the discretisation and not
configured, and letting it cross would contradict that at the interface.

Solver tolerances and iteration counts. They exist only in some methods. A port
carrying them would be shaped like the methods that have them, and the modal
method in the walk-through below has neither.

The choice of time domain or frequency domain. Issue #7 decides what the answer
is expressed in, and the port fixes that as a complex response at requested
frequencies. How a solver gets there, whether by running in time and
transforming or by solving at each frequency, is behind the port. A time-domain
solver's impulse response does not cross, because then every caller would have to
know whether it had one.

A fitted boundary filter. Stated above and repeated here because it is the most
likely thing to leak: it is the one piece of the wall model that is method-shaped,
and the moment it crosses, the material table above the port becomes a table for
one method.

Threading, device selection and accelerator choice. One machine is the ceiling
and that is a deployment decision, not a problem statement. Where it has to be
expressible at all it belongs beside the solver's construction and not in the
problem.

The random seed. Issue #29 requires the harness to be deterministic and none of
the methods named below is stochastic. If a stochastic method ever sits behind
this port, this is the line that has to be revisited, and it is recorded so that
the revisit is visible rather than silent.

## Three methods behind it

The test the issue sets is that the specification survives three implementations
without change. Here is each one, and where it is a poor fit, because a
walk-through that finds no friction has not been done honestly.

A regular-grid finite-difference time-domain scheme, the shape of the survey's
first candidate. It takes the geometry and voxelises it, derives its spacing from
the upper frequency and the smallest feature, derives its time step from its
stability limit, fits each impedance to its own passive boundary model, runs, and
transforms the receiver signals to the requested frequencies. Where it fits
poorly: its error is dominated by dispersion and by staircase approximation of
surfaces, and the second of those depends on how the room happens to be oriented
on the grid. An error estimate it stands behind is therefore harder to produce
than the port's result type makes it look, and the honest answer for such a
solver is often the word derived over the band where dispersion dominates and
the word estimated near the top. The port allows that, which is why the word is
in the type.

A modal summation on a rectangular box with locally reacting walls. It ignores
the smallest feature entirely, because it does not mesh anything. It answers
directly at the requested frequencies, which is the case the port was shaped
for, and its error estimate is genuinely derived, from the truncation of the mode
sum. Where it fits poorly: it refuses almost every problem. Anything that is not
a box, and any wall it cannot handle, is a refusal, and the refusal has nothing
useful to suggest, because no lever the caller has will turn a room with a
slanted ceiling into a box. This is the method that proves the refusal must
carry a reason and not only a list of levers, and it is the one the validation
work in issue #74 needs anyway.

A wrapped external solver, driven across a process boundary. This is the case
entry 2 of issue #1 may choose and the survey found concrete objects for. The
adapter below the port writes the foreign input files, launches a child process,
waits, reads the foreign output, and maps it back. Where it fits poorly, and
this is the entry with the most friction. Its cost prediction is somebody else's
and may not exist, so the second operation often returns the honest admission
rather than a number. Its accuracy target is not something it accepts, so the
adapter has to translate a target into whatever knobs the foreign solver does
take and then decide, after the fact, whether the target was met, which means a
refusal can only be issued late. Its material model may accept less than the
port carries, and then the adapter refuses at the port rather than quietly
degrading an impedance to an absorption coefficient. And it may not be
interruptible, so the stop request becomes a kill and the refusal says so.

None of those three needed a change to the specification above, and the friction
each one has is friction the port makes visible rather than friction it creates.
That is the claim this section is making and it is a claim about a design, held
open to being wrong until code sits behind it.

## What this document does not settle

It does not choose the method. That is issue #5 and it waits on entry 2 of issue
#1.

It does not fix the geometry tier, the material vocabulary, the source and
receiver descriptions or the accuracy target. Those are issues #10, #40, #42,
#43 and #15, and the port carries whatever they settle. Where this document has
had to assume something about them in order to say anything at all, it has said
so at the point of assuming.

It is also not yet proven. The last condition issue #6 sets is that the fake
which computes nothing and the first real implementation are both written
against this document and that neither changes it. Neither exists: issue #47 and
issue #49 are open. Until they land, this is a specification that has never been
implemented, which is exactly the state in which interface documents are usually
wrong, and it is recorded as that rather than as a finished thing.
