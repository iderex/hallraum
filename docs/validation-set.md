# The validation set

Written 2026-08-08.

A solver that agrees with itself proves nothing. The cases this project is
checked against are chosen here, before the solver exists, because a validation
set assembled afterwards is assembled from the cases that passed.

Four tiers of evidence, and none of them substitutes for another. A closed form
tests the numerics. A closed form with an impedance boundary tests the wall
model against arithmetic. A published benchmark tests it against somebody else's
work. A measurement tests whether the model of the wall resembles a wall, and it
is the noisiest of the four. A project that has only the first tier is a correct
solution to a problem nobody has.

Every case below names what it tests, what it cannot test, where it comes from,
what tolerance it is checked to and why that tolerance is the right one, and
which suite it belongs to.

## The scheme facts the tolerances rest on

Two numbers are used repeatedly below and are derived once here, so that the
tolerances are consequences rather than choices.

The first is the dispersion error of a standard second-order scheme on a
Cartesian grid at the stability limit, as a function of how finely the
wavelength is sampled. It follows from the scheme's own dispersion relation, and
this is the computation:

    lam = 1/sqrt(3)
    axial:    v/c = 2 asin(lam sin(kh/2)) / (kh lam)
    diagonal: v/c = 2 asin(lam sqrt(3) sin(kh/(2 sqrt(3)))) / (kh lam)

    points/wavelength    axial      body diagonal
                    6   -3.128 %          0.000 %
                    8   -1.740 %          0.000 %
                   10   -1.107 %          0.000 %
                   12   -0.767 %          0.000 %
                   16   -0.430 %          0.000 %
                   20   -0.275 %          0.000 %
                   23   -0.208 %          0.000 %

The body diagonal is exactly non-dispersive at the stability limit, which is a
property of that scheme and not a rounding artefact. Along an axis the error is
worst, and an axial mode is exactly what a rectangular room is full of. That is
why the numbers matter here rather than in a note about performance.

The second is what those errors cost in the case below. The rigid shoebox in the
bench set is 5.15 by 3.79 by 2.71 metres, and its own description records that
below 300 Hz the closest pair of axial modes from two different directions is
2.55 Hz apart. At 6 points per wavelength the axial error at 300 Hz is 3.128 per
cent, which is 9.39 Hz. That is nearly four times the distance between two
distinct modes, so at that resolution a solver can put a mode on top of its
neighbour and a test comparing frequencies has nothing left to mean.

The resolution at which the axial error falls below a quarter of that spacing is
23 points per wavelength, where it is 0.208 per cent. That is not expensive:

    python docs/memory-model.py --ppw 23 --volumes 53 --frequencies 300
    53 m3 at 300 Hz: 5.98 MiB

Six megabytes. The strongest tolerance available costs nothing, so no case below
is loosened for cost, and where a tolerance is loose it is loose for a stated
physical reason instead.

## Tier one: a closed form

The answer is known rather than believed. What this tier cannot test is any part
of the wall model beyond a perfectly rigid surface, and it cannot test anything
about a room that is not a box.

### V1, the rigid tube

A one-dimensional rigid-ended tube, driven at one end, pressure read at a point.

Its source is the derivation. The eigenfrequencies of a tube of length L closed
at both ends are n c over 2 L for positive integer n, and the pressure response
is the standard sum over those modes. Nothing beyond that is needed to obtain it
and no publication is being relied on.

What it tests is the time stepping, the stability limit and the dispersion error,
with the geometry removed from the argument entirely. What it cannot test is the
mesher, the voxeliser, the boundary model or anything three-dimensional.

Its tolerance is that each eigenfrequency agrees with the closed form to within
the axial dispersion error predicted for the resolution the case ran at, from the
table above, plus a margin of one half of that error. The reason is that the
error is not a defect and cannot be removed by better code, so a tolerance
tighter than it would fail a correct solver. The margin exists so that the
tolerance measures the prediction rather than restating it: a run that is out by
twice its predicted dispersion has something wrong with it that the prediction
does not cover, and that is exactly the case worth catching. The test reports the
resolution it ran at and the predicted error alongside the verdict, because a
tolerance that changes with resolution is meaningless if the resolution is not
recorded.

Fast suite.

### V2, the rigid shoebox

The rectangular room in `bench/rooms/shoebox-rigid.json`, every surface rigid,
against the modal sum.

Its source is the derivation, and it already exists in this tree as a running
program: `bench/adapters/analytic_modal.py` evaluates the sum and its docstring
records the assumption it has to add, which is that a rigid room is lossless, so
its poles sit on the real axis and its response there is infinite. The sum is
evaluated with a uniform modal damping the room file does not carry. That
assumption is why this case is checked on mode frequencies and not on the
magnitude of the response near a mode.

What it tests is the three-dimensional scheme, the mode frequencies of a real
room shape, and the handling of a fully rigid boundary. What it cannot test is
absorption of any kind, and it cannot test the magnitude at a peak, for the
reason above.

Its tolerance is 0.64 Hz on every mode frequency below 300 Hz, which is a
quarter of the 2.55 Hz closest spacing in this room. The reason is that at half
the spacing two modes could be exchanged and the test would still pass, which
would let a solver be wrong in the way that matters most and be recorded as
right. A quarter leaves a factor of two against that failure. Meeting it needs 23
points per wavelength, which costs 5.98 MiB, computed above.

Fast suite.

## Tier two: a closed form with an impedance boundary

This is the tier that actually tests the wall model, and the project is named for
the wall model. What it cannot test is whether the impedance supplied resembles
any real material, which is tier four's job and nothing else's.

### V3, the tube with a real resistive termination

The same tube as V1, one end rigid, the other end given a real, frequency
independent normalised specific impedance.

Its source is the derivation. A plane wave meeting a termination of normalised
impedance z reflects with coefficient (z - 1) over (z + 1), and the response of
the tube follows in closed form from that one number. Everything else in the case
is exact.

What it tests is the boundary implementation and nothing else, which is why it is
first in this tier. If V1 passes and V3 fails, the wall is where the defect is,
with no other candidate. What it cannot test is any frequency dependence, any
fitting, or any geometry at a wall.

Its tolerance is one per cent on the magnitude of the reflection coefficient
recovered from the response, at every frequency in the band. The reason it is
stated on the reflection coefficient rather than on the response is that the
response near a resonance is sensitive to the damping in a way that turns a small
boundary error into a large pressure error, so a tolerance on pressure would be
measuring the resonance rather than the wall. The reason it is one per cent is
that this is the tier where nothing else is approximate, so the only error left
is the boundary implementation, and a boundary implementation that is out by more
than one per cent on a single real number is wrong rather than imprecise.

Fast suite.

### V4, the shoebox with one absorbing wall

The room in `bench/rooms/shoebox-one-absorbing-wall.json`: one end wall with a
real, frequency independent normalised surface impedance, every other surface
rigid.

Its source is the derivation. With one wall of uniform impedance the eigenvalue
problem separates, and the wavenumber in the direction across that wall is the
root of a transcendental equation rather than a multiple of pi over the length.
The roots are complex, which is the point: the imaginary part is the damping the
wall introduces, and it is the quantity the whole wall model exists to get right.
The equation and its roots are obtained by separation of variables and no
publication is being relied on. Kuttruff's Room Acoustics is where the standard
treatment can be found by a reader who wants one, and no page is cited because no
copy was consulted here.

What it tests is a wall model in three dimensions, and specifically whether the
damping it introduces is the damping the impedance implies. What it cannot test
is frequency dependence or a fitted filter.

Its tolerance is two parts. On the real part of each eigenfrequency, the same
0.64 Hz as V2, for the same reason. On the imaginary part, five per cent. The
reason the second is looser is that the damping is a small difference between
larger quantities and is therefore the more sensitive of the two to the
discretisation of the surface, and the reason it is not looser still is that five
per cent of a decay rate is about half a decibel over a decay of ten, which is at
the edge of what a listener and a measurement can tell apart. A tolerance wider
than that stops being a statement about the wall.

Fast suite.

### V5, the tube with a frequency dependent impedance

The tube of V3, terminated with an impedance that has one pole, so that it is a
filter rather than a number.

Its source is the derivation, evaluated twice, and how it is evaluated is the
substance of this case. The closed form is computed with the impedance the solver
actually used after fitting, not with the impedance that was asked for. The two
differ by the fit error, and comparing against the target instead would add the
fit error and the solve error together and report the sum, which is the shape of
test that passes a broken solver with a good fit and fails a good solver with a
poor one. The fit error is reported separately, as its own number, against the
target.

What it tests is the fitted boundary path end to end: the fit, the stability of
the resulting filter, and the passivity issue #64 asks to be proved. What it
cannot test is whether the target impedance describes a material.

Its tolerance is the same one per cent as V3, on the same quantity, for the same
reason, plus a separate and stated bound on the fit error which belongs to issue
#63 rather than to this case.

Fast suite.

## Tier three: a published benchmark

Numbers somebody else computed and released. What this tier cannot test is
anything the benchmark's own authors got wrong, and agreement with it is
agreement with a community rather than with nature.

### V6, the computational acoustics benchmark platform

The platform described in Hornikx, Kaltenbacher and Marburg, "A Platform for
Benchmark Cases in Computational Acoustics", Acta Acustica united with Acustica
101 (2015), pages 811 to 820, DOI 10.3813/aaa.918875, run by the computational
acoustics technical committee of the European Acoustics Association and hosted at
https://eaa-bench.mec.tuwien.ac.at/main/ . Cases and submitted results are open.

What is determined about it here is that it exists, that it is the right kind of
object, that it categorises cases as bounded or unbounded and as time domain or
frequency domain, and that a bounded interior problem is the category this
project sits in.

What is not determined is which specific cases in it are bounded interior
problems in the band below 300 Hz with a non-rigid boundary, whether their
reference data is in a form this project can compare against, and what tolerance
each publishes. The case list was not read, and the attempt is recorded rather
than the intention: the address above redirects to the hosting institute's site,
and the two pages reached from there give four categories, of which linear
acoustics is the relevant one, without the individual cases under them. So no
case identifier and no tolerance is quoted, because quoting one would be
inventing it. This tier is therefore named and not populated, which is the one
place in this document where a tier has a source and no case.

Long run rather than fast suite, because the geometry of a benchmark case is not
chosen to be cheap. The harness is issue #73.

## Tier four: a measurement

The only evidence that the model of the wall resembles a wall. What it cannot
test is anything cleanly, which is the price of it being the only tier that
touches reality.

### V7, the benchmark for room acoustical simulation

Brinkmann, Aspöck, Ackermann, Opdam, Vorländer and Weinzierl, "A benchmark for
room acoustical simulation. Concept and database", Applied Acoustics 176 (2021),
article 107867, DOI 10.1016/j.apacoust.2020.107867. The database is published by
the Technical University of Berlin's repository at
https://depositonce.tu-berlin.de/items/457e9d28-8ce0-4f57-a6b2-08b1f57efa53 and
is a set of acoustical scenes, each carrying a geometry, source and receiver
positions and characteristics, a material description, and measured single
channel and binaural impulse responses. Some scenes are deliberately simple and
isolate one phenomenon; others are whole rooms.

What it tests, for this project, is whether a modelled room agrees with the room
it was modelled from. What it cannot test is the impedance model directly, and
this is the entry's most important limitation: the material descriptions in that
database are absorption and scattering coefficients, not complex surface
impedances. Feeding them to this solver means climbing down to the weakest rung
of the wall model in issue #8, or inventing a phase, and either way part of any
disagreement belongs to that step rather than to the solver.

Its tolerance is not stated as a single number and this is deliberate. What is
compared is the frequency of each identifiable mode below 300 Hz and the decay
rate in each third-octave band, against the same quantities extracted from the
measured response by a documented procedure. The reason a tighter statement is
withheld is that the uncertainty of the comparison is dominated by the material
data rather than by either the solver or the measurement, and a number chosen
before that uncertainty is quantified would be convenient rather than right.
Quantifying it is part of the work of this case and issue #78 is where the
result and what did not match are recorded.

Long run, and the harness is issue #73.

### What would have to be true for a disagreement to be the solver's fault

Stated in advance, because after a disagreement everybody's judgement about this
gets worse.

The geometry as built has to match the geometry as modelled to better than the
grid spacing of the run, which at 300 Hz and 23 points per wavelength is about
five centimetres. A room that has been repainted, refurnished or re-glazed since
it was measured does not qualify and no amount of care in the solver recovers it.

The impedance of every surface has to be known independently of the measurement
being compared against. An impedance fitted so that the simulation matches the
measurement makes the comparison circular, and a table value looked up for
"plaster" is not knowledge of that wall.

Source and receiver positions have to be known to a small fraction of a
wavelength, which at 300 Hz is a wavelength of 1.14 metres, so a few centimetres.
A modal null moves fast and a receiver in the wrong place disagrees with a
correct solver.

The measurement has to have usable signal to noise at the modal frequencies,
which is the hardest part of the band to excite and to measure, and the noise
floor has to be reported rather than assumed.

The air temperature and the relative humidity at the time of measurement have to
be recorded, because the speed of sound moves the modes and a two degree error is
visible at the tolerances above.

Where any of those fails, the disagreement is not attributable and the honest
record says so. That sentence is the one this section exists to make it possible
to write.

## Which suite each case runs in

V1 through V5 run in the fast suite. All of them are one-dimensional or the 53
cubic metre shoebox at 23 points per wavelength, the largest of them predicted at
5.98 MiB, and none needs an accelerator or any privilege. Issue #32 is where the
fast suite is separated from the slow one and issue #73 is where these are put
into it.

V6 and V7 need a long run and are not in the fast suite. Their harness is issue
#73, named for what it is: a validation harness that runs cases too large for the
gate. Where a case needs real hardware rather than only time, it goes to issue
#129 instead, which is the hardware integration harness and is named for that.
Nothing in this document currently needs it.

## What this set does not cover

There is no case here for a room that is not a box. Every closed form in tiers
one and two is separable and separability is what a box gives, so the third
geometry tier accepted in `docs/what-a-room-is.md` has no closed-form check at
all. The only evidence available for it is convergence under refinement, which is
issue #76, and comparison against a second method, which is issue #77. Neither is
in this set because neither is a case with an answer that is not ours, and
pretending otherwise would be the exact failure this document exists against.

There is no case here for an extended reaction wall, because no method surveyed
offers one and issue #8 has not decided whether this project will.

Tier three is named but not populated, and the paragraph in V6 says exactly which
part was not done.
