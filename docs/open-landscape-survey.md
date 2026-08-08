# The open landscape, surveyed

Written 2026-08-08. Every command below was run on that date against the public
API, and every date in it is the date that API reported.

This is a finding and not a decision. The founding description of this project
records that the open landscape here was surveyed less thoroughly than for the
neighbouring work, and that individual wave-based implementations exist. That
was recorded rather than discovered, so the weakness was known. What follows is
the discovery.

Entry 2 of issue #1 is where the finding becomes a decision, and this document
does not answer it. It supplies it facts and stops.

## The nine questions

Each candidate is answered by number, and the numbers mean the same thing every
time.

1. Which method it implements, and in what domain.
2. Whether it takes a room that is not a rectangular box.
3. What it accepts at a wall, and specifically whether that is a complex,
   frequency-dependent surface impedance or only a real absorption coefficient.
4. Whether the boundary model can be extended without forking.
5. What it returns, and whether that can be made into a transfer function.
6. What it needs to build and to run.
7. Its licence, and what that licence does to the licence question here.
8. Whether it is maintained, evidenced by a date rather than an impression.
9. Whether anyone has published a validation of it against something other than
   itself.

Where an answer was not determined, the entry says so and says why. A blank is
not an answer and does not appear.

## The search routes

Four routes, each a command a reader can run again. The first is the starting
list recorded in issue #2, which was not produced here and is treated as given.

The second is the public host's topic index:

    gh search repos --topic room-acoustics --limit 40 --json fullName,stargazersCount,description
    gh search repos --topic acoustics --limit 50 --sort stars --json fullName,stargazersCount,description
    gh search repos --topic fdtd --limit 40 --sort stars --json fullName,stargazersCount,description

The third is free-text search over names and descriptions, which returned very
little and is recorded because a route that returns little is a fact about the
route:

    gh search repos "room acoustics simulation" --limit 40
    gh search repos "FDTD acoustics" --limit 25
    gh search repos "wave based acoustics" --limit 25
    gh search repos "discontinuous galerkin acoustics" --limit 25

Those four free-text queries returned six, three, one and one repository
respectively. The topic index returned far more, so free-text search over
descriptions is not a route to rely on here.

The fourth is a curated list maintained by somebody else, which is how the
Community Hub entry below was found and which no search above surfaced:

    gh api repos/Nitnelav/awesome-acoustic/readme --jq .content | base64 -d

Metadata for every candidate came from one command:

    for r in <the candidates below>; do gh api "repos/$r" --jq '[.full_name, (.license.spdx_id // "none"), (.language // "-"), .pushed_at[0:10]] | @tsv'; done
    bsxfun/pffdtd	MIT	Python	2024-02-08
    Burhanuddin98/PPFFDTD	MIT	Python	2026-05-11
    juuli/ParallelFDTD	MIT	C++	2018-01-24
    AaltoRSE/ParallelFDTD	MIT	C++	2022-11-11
    Building-acoustics-TU-Eindhoven/edg-acoustics	GPL-3.0	Python	2025-10-16
    choras-org/CHORAS	GPL-3.0	Batchfile	2026-07-13
    Building-acoustics-TU-Eindhoven/DG_RoomAcoustics_Matlab	NOASSERTION	MATLAB	2023-04-17
    nantonel/AcFDTD.jl	NOASSERTION	Julia	2020-02-08
    gpuard/pytARD	AGPL-3.0	Python	2022-06-10
    SeicheAcoustics/Seiche	MIT	C++	2026-05-05
    themattrosen/Planeverb	MIT	C++	2022-11-12
    gregzanch/cram	MIT	TypeScript	2023-02-28
    aldalmora/fem4room	GPL-3.0	Python	2020-09-05
    ucl-bug/k-wave	LGPL-3.0	MATLAB	2026-05-05
    waltsims/k-wave-python	LGPL-3.0	Python	2026-07-27
    ucl-bug/jwave	LGPL-3.0	Python	2026-03-22
    optimuslib/optimus	MIT	Jupyter Notebook	2026-02-18
    devitocodes/devito	MIT	Python	2026-08-07
    mfem/mfem	BSD-3-Clause	C++	2026-08-08
    FEniCS/dolfinx	LGPL-3.0	C++	2026-08-08
    NGSolve/ngsolve	LGPL-2.1	C++	2026-08-07
    bempp/bempp-cl	MIT	Python	2026-08-03
    ElmerCSC/elmerfem	NOASSERTION	Fortran	2026-08-07
    LCAV/pyroomacoustics	MIT	Python	2026-07-17
    Universite-Gustave-Eiffel/I-Simpa	GPL-3.0	C++	2026-01-18
    EVERTims/evertims	NOASSERTION	C++	2024-06-17
    Building-acoustics-TU-Eindhoven/acousticDE	GPL-2.0	Python	2026-07-06
    Yhonatangayer/shroom	MIT	Python	2026-07-30

NOASSERTION is what the API returns where it found a licence file it could not
classify, and it is not the same as no licence. Where it appears below, the
licence answer is that it was not classified and a human has to read the file.

A pushed-at date is the date of the last push to any branch. It is evidence that
something happened and not evidence that the project is healthy, and it is used
here for nothing more.

## Packaged room acoustics solvers

These are the candidates this project could stand on. Each one is a program that
takes a room and returns a response, rather than a toolkit in which such a
program could be written.

### pffdtd

1. Finite-difference time-domain on a regular grid, in the time domain. Its
   readme offers a 13-point face-centred cubic scheme and a 7-point Cartesian
   scheme, and says the face-centred one needs about five times less memory than
   the Cartesian one for the same 1 to 2 per cent dispersion error.
2. Yes. Geometry is a triangle model exported from a commercial sketching tool
   through a plugin it ships. Its readme states the model does not need to be
   watertight and needs at least four triangles, which is a weaker requirement
   than several of the others below.
3. A complex, frequency-dependent impedance. Its readme lists
   "Frequency-dependent impedance boundaries" among its features and says
   absorption or impedance data is fitted to a passive boundary impedance model,
   with a provided routine that fits 11 octave-band absorption coefficients from
   16 Hz to 16 kHz. It also notes that non-rigid boundary nodes carry extra
   state for internal ordinary differential equations, which is what a fitted
   filter at a wall costs.
4. Not determined. The fitting routine is described as simple and as one route
   in, which suggests supplying fitted coefficients directly is possible, but no
   file in that repository was read to confirm it and the answer is not claimed.
5. Monaural room impulse responses, explicitly, plus tooling to remove
   frequencies with too much dispersion error and to resample. A transfer
   function follows from an impulse response by transform, so the answer to the
   second half is yes.
6. Python 3.9 or later for setup and voxelisation, and for the fast engine a C
   and CUDA build needing the vendor toolkit and HDF5 development files. Its
   readme states it is intended for workstations or single-node servers with one
   or more of that vendor's accelerators. The Python engine runs without one and
   is described as being for visualisation and correctness checking.
7. MIT. It puts no constraint on the licence question in entry 1 of issue #1.
8. Last push 2024-02-08. That is the oldest date among the candidates that are
   otherwise serious, and it is a cost that entry 2 of issue #1 has to weigh.
9. Yes, in the sense that the methods it implements are published and
   validated in the literature it cites, including a finite volume treatment
   under general impedance boundary conditions in IEEE/ACM Transactions on
   Audio, Speech and Language Processing 24(1):161 to 173, 2016, and a modelling
   study compared against measurements in Acoustics 2(1):87 to 109, 2020. That
   is a validation of the methods and of one modelled room, and it is not the
   same thing as a published validation of this implementation as shipped. The
   distinction is deliberate.

### PPFFDTD

1. Not a method of its own. Its description says it is a Python wrapper for the
   solver above with a non-intrusive reduced order model, written for the
   Community Hub entry below.
2. Inherited from the solver it wraps.
3. Inherited from the solver it wraps.
4. Not determined. Only its metadata and description were read.
5. Not determined on this route.
6. Not determined on this route.
7. MIT.
8. Last push 2026-05-11.
9. Not determined. Nothing was found and nothing is claimed either way.

### ParallelFDTD, and its fork

1. Finite-difference time-domain on a regular grid, in the time domain,
   accelerated across multiple accelerators and multiple nodes. The solver above
   points at it by name as the route to simulations larger than one node.
2. Yes, but with a hard condition. Its readme states the geometry has to be
   solid and watertight, that a single plane or a hole breaks the voxeliser's
   inside-outside test, and gives the worked example that a balcony rail has to
   be drawn as a box rather than as a plane.
3. A per-surface list of real coefficients, not a complex impedance. Its
   material handler header defines a fixed count of coefficients per surface and
   two mutually exclusive interpretations of them:

       gh api repos/juuli/ParallelFDTD/contents/src/base/MaterialHandler.h --jq .content | base64 -d
       #define MATERIAL_COEF_NUM 20
       void coefsAreAdmittances() {this->admitance_ = true;};
       void coefsAreReflectances() {this->admitance_ = false;};

   Twenty real numbers per surface, read either as admittances or as reflection
   coefficients. That is a per-band real quantity and it carries no phase, which
   is the thing that decides where a mode sits.
4. Not determined. Extending it to a complex boundary would change the field
   update, and no judgement about how invasive that is was formed from reading
   one header.
5. Not determined on this route. Its Python test bench is named in the search
   results and was not read.
6. A C++ build with a vendor accelerator toolkit, and for the multiple-node path
   a message passing layer. That last one sits against the one machine
   constraint in `docs/one-machine.md` rather than with it.
7. MIT, for both the original and the fork.
8. The original was last pushed 2018-01-24. The fork under an institutional
   account was last pushed 2022-11-11 and reports itself as a fork of the
   original. A project whose most recent activity is in a fork four years behind
   today is a finding about the landscape and is recorded as one.
9. Not determined. The repository cites work by its authors and no published
   validation of the shipped code was located on this route.

### edg-acoustics

1. Nodal discontinuous Galerkin for space, integrated in time with high-order
   explicit schemes. Its readme names the arbitrary high-order derivative
   integration scheme. Time domain.
2. Yes, and more freely than any other candidate here. The room is an
   unstructured mesh built in a general open mesh generator, either directly or
   by exporting from a sketching tool, and boundary faces are tagged as physical
   groups that the setup script maps to boundary conditions.
3. A complex, frequency-dependent impedance, fitted. Its usage guide states that
   a time-domain impedance boundary condition model is used, that the impedance
   data has to be fitted to that model, and that the fitting is done by vector
   fitting, with a script provided:

<!-- doc-check: unresolved-path the path is inside another repository, not this one -->
       gh api repos/Building-acoustics-TU-Eindhoven/edg-acoustics/contents/docs/usage_guide.md --jq .content | base64 -d

   The same guide states that a boundary material with a frequency-independent
   real-valued impedance can instead be given its real reflection coefficient
   directly, so both rungs of the wall model are reachable and the user picks
   per surface. The fitted coefficients are ordinary data in the setup script
   and can be written by hand rather than only produced by the provided script.
4. Partly, and better than the alternatives. Because the fit is data and the
   boundary condition model is fixed, a new material is a new fit and needs no
   fork. A different boundary condition model, an extended reaction wall for
   instance, is not reachable that way.
5. Impulse responses at receivers, saved every N steps to a Matlab-readable or
   a Python-readable file. A transfer function follows by transform.
6. Python, installed from the repository, with a mesh generator, a mesh
   input-output library, a polynomial basis library and the usual numerical
   stack. The fitting script as provided is written for a commercial numerical
   environment, which is a real dependency on the material preparation path and
   not on the solve.
7. GPL-3.0. This is the entry that makes the licence question in entry 1 of
   issue #1 and the solver question in entry 2 the same question. Embedding this
   solver inherits the copyleft. Driving it across a process boundary does not,
   and the difference between those two is a design decision this project would
   be making for licensing reasons.
8. Last push 2025-10-16.
9. Yes. The boundary condition model it implements is published as Wang and
   Hornikx, "Time-domain impedance boundary condition modeling with the
   discontinuous Galerkin method for room acoustics simulations", Journal of the
   Acoustical Society of America 147(4):2534 to 2546, 2020, and the vector
   fitting method it uses is Gustavsen and Semlyen, IEEE Transactions on Power
   Delivery 14(3):1052 to 1061, 1999. As with the entry above, that is
   publication of the method rather than of this implementation as shipped.

### CHORAS

1. Not a method. It is a packaged front end over two methods, a diffusion
   equation model and the discontinuous Galerkin solver above, delivered as a
   browser interface with a container setup.
2. Inherited from the solver behind it.
3. Inherited from the solver behind it.
4. Not determined. Its own repository is a hub with submodules and the boundary
   model is not in it.
5. An impulse response, with the run configured by named settings including
   impulse response length, upper frequency limit, polynomial order, points per
   wavelength and the stability number.
6. A container runtime. Its readme says the container setup is the supported
   route and the submodules are not needed for it.
7. GPL-3.0.
8. Last push 2026-07-13, the most recent of any candidate that is specifically a
   room acoustics tool rather than a general framework.
9. Not determined for the packaging. The solver behind it carries the
   publications listed above.

   This entry is the one that changes the shape of the argument, and it was
   found only through the curated list. A packaged, container-delivered,
   browser-driven front end over a wave-based room acoustics solver with a
   fitted impedance boundary already exists and was pushed to last month. The
   founding description of this project says the gap is packaging and boundary
   condition modelling. Against this entry, the packaging half of that sentence
   is weaker than it was written, and entry 2 of issue #1 should be answered
   with this in front of it.

### DG_RoomAcoustics_Matlab

1. Discontinuous Galerkin, from the same group as the entry above, in a
   commercial numerical environment.
2. Not determined on this route.
3. Not determined on this route.
4. Not determined on this route.
5. Not determined on this route.
6. A commercial numerical environment, which puts it outside what this project
   can require of a user regardless of its other answers.
7. Not classified by the API, so a human has to read the file.
8. Last push 2023-04-17.
9. Not determined.

### AcFDTD.jl

1. Finite-difference time-domain, time domain, with an interpolated isotropic
   scheme among the choices.
2. No. Its readme constructs a room as a cuboid taking three dimensions.
3. A real, frequency-independent impedance, one number per wall, six numbers for
   a box. Its readme sets it as a six-element vector labelled front wall, rear
   wall, left wall, right wall, floor and ceiling.
4. Not determined, and the question is close to moot given the answer above.
5. Not determined on this route beyond that it computes a room response.
6. A Julia installation, and the installation instruction in its readme uses a
   package manager call that has not been the current spelling for several
   Julia releases.
7. Not classified by the API.
8. Last push 2020-02-08, and its readme opens by declaring the library
   unmaintained in its own title. That is the clearest answer to question 8 in
   this document and it is the project's own.
9. Not determined.

### pytARD

1. Adaptive rectangular decomposition, time domain. The room is divided into
   partitions that are coupled through interfaces.
2. Only as a union of rectangular partitions, which is the method rather than a
   limitation of the implementation.
3. Not a wall impedance in the sense this project needs. Its readme states that
   air partitions reflect waves indefinitely without loss in amplitude, and the
   absorption in the repository is at the interfaces between partitions, in
   files named for verifying interface absorption in one and two dimensions. A
   real per-surface absorption coefficient is the most that can be read from
   this route, and even that is not confirmed.
4. Not determined.
5. Room impulse responses, per its own description.
6. Python, per its readme.
7. AGPL-3.0, which is the most demanding licence in the list. Embedding it would
   push this project to AGPL-3.0 and would extend the obligation to anyone
   offering it over a network.
8. Last push 2022-06-10, and its citation entry is a thesis.
9. Not determined.

### Seiche

1. Not determined precisely. Its source carries a discontinuous Galerkin
   acoustics module in two and three dimensions, so a wave method is present,
   and whether it is the primary path was not established.
2. Not determined on this route.
3. Real octave-band absorption coefficients, and a scattering coefficient. Its
   material type is six bands from 125 Hz to 4 kHz:

       gh api repos/SeicheAcoustics/Seiche/contents/src/core/Material.h --jq .content | base64 -d
       constexpr int NUM_FREQ_BANDS = 6;
       constexpr std::array<int, NUM_FREQ_BANDS> FREQ_BANDS = {125, 250, 500, 1000, 2000, 4000};
       std::array<float, NUM_FREQ_BANDS> absorption = {0.2f, 0.2f, 0.2f, 0.2f, 0.2f, 0.2f};
       float scattering = 0.1f;

   The lowest band is 125 Hz and the presence of a scattering coefficient
   alongside absorption is the signature of a geometrical material model. Both
   facts point away from the range this project is for.
4. No, not without changing that type and everything that reads it.
5. Not determined on this route.
6. A C++ build.
7. MIT.
8. Last push 2026-05-05.
9. Not determined.

### Planeverb

1. Finite-difference time-domain in two dimensions, for real-time use in games.
2. Two dimensional, so the question does not apply in the form asked.
3. Nothing usable here. Its public type header offers exactly two boundary
   types for the grid, absorbing and reflecting, and the reflecting one is
   marked as not supported:

       gh api repos/themattrosen/Planeverb/contents/ProjectPlaneverb/include/PvTypes.h --jq .content | base64 -d
       pv_AbsorbingBoundary,	// walls of the grid absorb acoustic energy
       pv_ReflectingBoundary,	// walls of the grid reflect acoustic energy - !!! Not supported !!!

   Those are the edges of the computational domain rather than the surfaces of a
   room, and the impedance constants in the same file are the characteristic
   impedance of air and zero.
4. No.
5. Perceptual parameters for a game audio engine rather than a response.
6. A C++ build.
7. MIT.
8. Last push 2022-11-12.
9. Not determined.

### cram

1. Not determined. Its description says it is a computational room acoustics
   module to simulate and explore acoustic properties, and which method or
   methods it implements was not established on this route.
2. Not determined.
3. Not determined. A code search that would have answered it returned an API
   rate limit rather than a result, and the answer is therefore absent rather
   than negative.
4. Not determined.
5. Not determined.
6. A browser and a TypeScript toolchain.
7. MIT.
8. Last push 2023-02-28.
9. Not determined.

### fem4room

1. Finite element method, per its description. Domain not determined.
2. Not determined.
3. Not determined.
4. Not determined.
5. Not determined.
6. Python.
7. GPL-3.0.
8. Last push 2020-09-05.
9. Not determined. It is a small package with three stars and is listed for
   completeness rather than as a candidate to stand on.

## Frameworks a solver could be built in

None of these is a room acoustics tool. Each is a general apparatus in which the
solver for this project could be written, which makes the answer to question 3
the same for all of them and worth stating once: a framework does not accept a
wall model, it accepts whatever weak form or update rule you write, so the
frequency-dependent impedance boundary is work this project would be doing
rather than work it would be inheriting. That is the whole point of the group
and it is why building here is a different proposition from wrapping above.

The answers that do differ are recorded per entry, and the ones that do not are
not repeated.

k-Wave, and its Python interface. Pseudospectral time domain for acoustic wave
fields, written for ultrasound and photoacoustics rather than for rooms. It
absorbs at the domain edge with a perfectly matched layer, which is a
termination and not a wall, so question 3 is answered by the field it comes
from. LGPL-3.0 for both. Last pushes 2026-05-05 and 2026-07-27. The Python
package is an interface to compiled binaries, which is a distribution question
this project would inherit.

jwave. The same discretisations in a differentiable numerical framework,
LGPL-3.0, last push 2026-03-22. Its interest here is that it is differentiable,
which matters for fitting a boundary rather than for solving a room, and that is
a use this board has not asked for.

devito. A symbolic finite difference compiler rather than a solver, MIT, last
push 2026-08-07. Writing the scheme in it would give the stencil optimisation
and the parallel execution for free and would leave every acoustic decision,
including the whole boundary model, to be made here.

mfem, dolfinx and ngsolve. Finite element frameworks, BSD-3-Clause, LGPL-3.0 and
LGPL-2.1, all pushed within the last two days. Any of them will carry an
impedance boundary as a Robin condition in the weak form, which is the honest
version of the sentence "the boundary model is extensible": it is extensible
because you write it. The licence spread across the three is the reason entry 1
of issue #1 says the licence choice is constrained by the solver choice.

bempp-cl and optimus. Boundary element method, MIT for both, last pushes
2026-08-03 and 2026-02-18. The boundary element method is the one where the wall
is the primary object rather than an afterthought, and it is a frequency-domain
method, which is entry material for issue #7 rather than for this document.

elmerfem. A general multiphysics finite element package, licence not classified
by the API, last push 2026-08-07. Included because it is one of the largest and
oldest open finite element codes and because a survey that lists three finite
element frameworks and not this one has chosen its list rather than found it.

## Tools that are in the list only to be excluded

These are not candidates. Each is here because it appears in the same searches
and a reader who does not find it here will wonder whether it was missed.

pyroomacoustics, MIT, last push 2026-07-17. Geometrical, image source and ray
tracing, which is the method this project exists because of rather than a
candidate to stand on. It is the reference for what a packaged and pleasant
interface looks like and for nothing else.

I-Simpa, GPL-3.0, last push 2026-01-18, and evertims, licence not classified,
last push 2024-06-17. Geometrical sound propagation and beam tracing
respectively. Same exclusion, same reason.

acousticDE, GPL-2.0, last push 2026-07-06. A diffusion equation model, from the
group behind the discontinuous Galerkin solver above. The diffusion equation is
an energy method and carries no phase, so it is outside the range this project
names, and it is listed because it is one of the two methods the Community Hub
entry packages.

shroom, MIT, last push 2026-07-30. Room acoustics through spherical harmonics
and ambisonics, which is a spatial representation of a response rather than a
way of computing one.

## Where the search stopped

Named, because a survey that does not say what it did not cover is read as one
that covered everything.

One public code host was searched, through its topic index and its free-text
repository search, and one curated list hosted on it was read. That is the
whole of the automated coverage.

Not searched, deliberately, and each with its reason.

Other code hosts. At least one candidate named in the curated list lives on a
different host, and general-purpose finite element packages are hosted across
several. Nothing here reached them.

Publication archives and the code attached to papers. A wave-based room
acoustics implementation released alongside a journal article, with a digital
object identifier and no repository on the host searched, is invisible to every
route above. This is the largest known gap and it is the one most likely to hide
a serious candidate, because this field publishes that way.

Institute and national laboratory codes that are not publicly hosted. The
founding description of this project says wave-based methods live in institute
codes, so the class most likely to contain a mature solver is the class least
reachable by any command in this document.

Commercial products. Out of scope by the shape of the project rather than by
oversight.

Anything not written in English or not indexed under an English topic.

The route that failed rather than being skipped is recorded separately: the
code search API returned a rate limit part way through, which is why two of the
question 3 answers above are absent rather than negative. Re-running those
searches is cheap and would close that gap.

## The finding

A usable open solver exists for the range this project targets. Two of them, on
different methods, and one packaged front end over one of them.

The strongest by the measure that matters here is edg-acoustics. It is the only
candidate that takes an arbitrary unstructured mesh and a fitted, complex,
frequency-dependent impedance at a wall, which is both of the things the gap
this project names is about, and its boundary condition model is published in a
journal. It is GPL-3.0 and it was last pushed 2025-10-16.

The next is pffdtd. It also fits a frequency-dependent passive impedance, it is
MIT, and its geometry route is more forgiving than most. It was last pushed
2024-02-08 and it wants a vendor accelerator for anything large.

The packaging half of this project's founding premise is the part the survey
damages most. CHORAS is a container-delivered browser interface over the
discontinuous Galerkin solver, it exposes the settings a user would need, and it
was pushed to in the last month. It was not visible from any repository search
run here and was found only in a list somebody else maintains, which is itself a
finding about how thin the earlier survey could have been.

What this does not find. No candidate here offers an extended reaction wall
model, so the deepest rung of issue #8 is unclaimed by everything surveyed. No
candidate was found with a published validation of the shipped implementation as
distinct from the method it implements, which is the gap issue #14 is written
against and which this project would face whether it writes or wraps.

What follows from this is entry 2 of issue #1 and belongs to the maintainer.
This document says only that the option of wrapping is real and has at least two
concrete objects behind it, that choosing the strongest of them decides the
licence question in entry 1 at the same time, and that the case for writing a
solver here is now a case that has to be made against named alternatives rather
than in their absence.

Issue #4 is where these claims stop being documentation. Every candidate above
that can be built is run there, on the same rooms, and where this document says
a candidate refuses a room or a wall, that issue is where it either does or does
not.
