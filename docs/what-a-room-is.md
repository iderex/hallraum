# What a room is allowed to be

Written 2026-08-08.

The set of rooms this software accepts is the decision that sets the meshing
work, the accuracy story and the size of the audience. It is settled here so
that the geometry work has a scope to take rather than a scope to invent, and so
that a user is refused by a documented rule rather than by whatever the reader
happened to be able to parse.

## The tiers

Named once, cheapest first, and used by name for the rest of this document.

A rectangular box. A box with rectangular niches and steps, which is most real
rooms. A closed polyhedron with flat faces, which is a slanted ceiling, a
splayed wall and a corner cut off. Anything with curvature.

## What the first release accepts

A closed polyhedron with flat faces, which is the third tier, and the first two
tiers are special cases of it rather than separate paths through the code.

The reason is that the step from the second tier to the third costs a mesher or
a voxeliser that the first two tiers already needed, and the step from the third
to curvature is the one that changes the method conversation rather than adding
work to it. A curved surface has to be either meshed with curved elements, which
is a different discretisation, or approximated by flat facets, in which case the
software is holding an approximation it did not tell anyone about. The first is
out of scope for a first release and the second is dishonest, so the line is
drawn between them.

Both method families the survey in `docs/open-landscape-survey.md` found take
flat faces. A regular grid voxelises them and pays a staircase error at every
face that is not aligned to it, and one of the candidates ships a surface area
correction for exactly that. An unstructured mesh follows them exactly and pays
for a mesher instead. Neither family is excluded by this tier, which is why the
tier can be settled while the method decision in issue #5 is still open. A
method that could only do boxes would make this document wrong, and this is the
sentence that would have to be revisited.

`bench/rooms/slanted-ceiling.json` is already in the bench set for this reason
and is the cheapest room that is not a box. If the tier here were the second
one, that room would have to come out of the bench, and the candidates would
stop being separated by the thing that separates them.

## What is refused, and how

Curvature is refused. So is a surface that is not part of a closed volume, and
so is a geometry whose faces do not bound one.

A refusal names the surface and says which rule it broke, and it says what the
user can do, which is to supply the curve as flat facets they chose themselves.
That is the same approximation the software would otherwise have made silently,
with the difference that the user made it, can see how coarse it is, and can
refine it. Where the user does that, the software is not told a curve was ever
involved and does not claim otherwise.

Refusing is the whole answer here rather than a fallback, and this document is
where it is stated so that it is a rule and not a limitation somebody discovers.
Issue #35 is where a file that is not a room is refused on the way in, and issue
#36 is where a geometry that does not close is either made watertight or has the
place it fails named. Both take their scope from this section.

Refused means the run does not start. It does not mean the software may not
first close a gap that falls inside a tolerance somebody wrote down, and issue
#36 is where those checks and their tolerances are set. What this section fixes
is the end state and the disclosure. What reaches the solver bounds a closed
volume, and every difference between it and the file the user wrote is carried
into the result rather than only into a log. A weld nobody was told about is the
one outcome refused outright, because a result about a room that was quietly
altered is a result about a room that does not exist.

Later tiers are reachable in this order. Curved surfaces meshed as curves, which
needs the method to support them and is therefore behind issue #5 rather than
behind any geometry work. Nothing else is planned above them.

## An opening, and a room that is not alone

A room with a wide doorway into the next space is one air volume below 300 Hz
whatever the floor plan calls it, and a room with a closed door in a wall is
not. The tier above answers both, the answer was never written down, and issue
#36 and issue #38 were each left to invent one.

A closed door, a window and a hatch are faces like any other and carry their own
material. There is nothing special about them.

Two spaces joined by an opening are described as one closed polyhedron with no
face across the opening. There is no second room type, no coupling coefficient
and nothing new in the file. The pair is a single non-convex room, which is the
third tier, and the opening is where the user placed no face. What it costs is
that the second space has to be modelled too, with its own surfaces and its own
materials, and that cost is the answer rather than a limitation of it.

An opening onto a space that is not modelled is refused in the first release.
That is a place where the room ends and no face exists, and any face put there
would be a boundary condition the software invented. Sound leaving and not
coming back is a termination, not a material, and the two are decided elsewhere:
issue #56 is where a domain that does not end at a wall is terminated, and issue
#8 is where what an impedance means at a wall is settled. Until both land there
is no defensible number to put on that face, and a refusal says so where a
default would not.

## What is inside the room

A sofa, a bookshelf, a cabinet and a person are volumes, not surfaces. Below
300 Hz a large cabinet is a wall, and a room modelled as empty when it is not is
wrong in the band this project is about.

The first release does one thing with them, and it is the least it can do
honestly. An object is accepted as part of the geometry, meaning the user models
it as flat-faced surfaces bounding a volume that is not air, with a material on
its faces like any other surface. It is then a wall that happens to be in the
middle of the room. Nothing else about it is modelled: not what is inside it,
not the sound that passes through it, and not any absorption that depends on its
depth.

What is refused is an object described as a bulk absorber, meaning a volume with
an absorption per cubic metre rather than a surface with an impedance. That is
the model a deep porous layer and a seated audience actually need, it is what
issue #39 asks about, and it is not in the first release because the volumetric
absorber and the extended reaction wall in issue #8 are the same physics and
should be decided together rather than half each.

A person is not modelled at all. There is no shape, no impedance and no
scattering for a human body in this software, and the software says so when
asked rather than accepting a box labelled person. Issue #39 is where that
either changes or is written down for a user.

The volume an accepted object occupies is removed from the air. This matters
more than it sounds: the modal frequencies of a room follow from the air volume
and its bounding surfaces, so an object modelled as a surface with no volume
removed would leave the air where the object is and shift every mode. Issue #37
reports what the discretisation lost, and the volume removed by objects is part
of what it reports.

A source or a receiver placed inside an accepted object is not in the air, and a
run that puts one there is asking for the pressure inside a wardrobe. Issue #44
is where an assembled problem is checked before anything expensive starts, and
this is one of the checks it owes.

## The scale limits

Two numbers, and both are consequences of things decided elsewhere rather than
choices made here.

The smallest feature the software will represent is the grid spacing implied by
the upper frequency, for a volumetric grid method, and it is not a free
parameter. The prediction is generated rather than quoted:

<!-- generated: python docs/memory-model.py --volumes 30 250 2000 --frequencies 100 300 -->

    c = 343 m/s, 6 points per wavelength, 3 array(s) of 4 byte(s),
    8 stored value(s) per boundary node, Courant 0.5774, 1 s modelled.
    Rooms are taken as cubes for their surface area.
    A row marked * exceeds 64 GiB.

       V (m3)      100 Hz      300 Hz
           30    7.42 KiB     101 KiB
          250    38.5 KiB     628 KiB
         2000     217 KiB    4.11 MiB

    Upper frequency at which the interior arrays alone reach 64 GiB,
    and the time steps a 1 s run costs there:

       V (m3)    f at limit steps at that f
           30       32916 Hz        3.42e+05
          250       16235 Hz        1.69e+05
         2000        8118 Hz        8.44e+04

    Grid spacing and step count in the band this project claims:

         f (Hz)       h (m)     steps per s       points/m3
            100     0.57167            1039           5.353
            300     0.19056            3118           144.5

<!-- end generated -->

At 300 Hz that spacing is 0.19 metres. A step in a wall shallower than that, a
window reveal, a skirting board and a door handle are all below it and are not
represented, whatever the geometry file says about them. The software accepts
the geometry and reports what the discretisation dropped, which is issue #37,
rather than refusing a room for carrying detail it will not use.

A user who needs a feature smaller than that is asking for a finer grid than the
frequency requires, and that is the second field the port in `docs/solver-port.md`
carries: the smallest feature the geometry must honour, in metres, stated by the
user and paid for in memory and time. It is a lever with a price and this
document does not cap it. Where the price cannot be paid, the run is refused
before it starts, which is issue #84.

The largest room is not a number this document sets either. It is wherever the
combination of volume and upper frequency stops fitting on one machine, which is
`docs/one-machine.md`, and the frequency at which it stops is issue #11 and issue
#83. The rows above are a prediction and not a measurement, and where the
measurement in issue #82 disagrees with them, the measurement is right. What is
settled here is only that the limit is expressed as a pair, a volume and an upper
frequency, and never as a room size alone, because a room size alone is not a
statement anybody can act on.

## What this document does not settle

It does not settle the file format a room arrives in, which is issue #35. It
does not settle the material vocabulary at a surface, which is issue #40 and
issue #8. It does not settle the upper frequency, which is issue #11 and is
where the numbers above get their meaning.

It did not govern the work it is written for on the day it landed, because every
geometry issue in the room milestone was written before it existed. Each has
since been read against it, and the result is on issue #10, one entry per issue,
saying what that issue takes from here and what it still has to add. Three of
the passages above came out of that reading: the section on openings, the
paragraph saying what refused means, and the sentence about a source inside an
object. Nothing the reading found moved the tier.
