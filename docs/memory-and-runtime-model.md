# The memory and runtime model, written before it is measured

Written 2026-08-08. This is a prediction. Nothing in it has been measured on
any machine, and the numbers below come from the formulas below and from
nothing else. Issue #82 measures memory against frequency and volume, #85
measures runtime, and both are asked to report the difference against this
document rather than to replace it. A model fitted to the measurement
afterwards explains everything and predicts nothing, which is why the order is
this way round.

## What method this is written for

The model is written for a method that carries field values on a volumetric
grid over the whole room: the count of unknowns is the volume divided by the
cube of a grid spacing, and the spacing is set by the shortest wavelength in
the band. Finite difference and finite volume schemes in the time domain are
that shape, and so is a finite element discretisation in the frequency domain
as far as the count of unknowns goes.

The method is not chosen. That is issue #5, and it waits on entry 2 of #1,
whether this project writes a solver at all:

    gh api repos/iderex/hallraum/issues/1/comments --jq 'length'
    0

If #5 chooses a method that is not of this shape, this document does not
apply and has to be written again rather than adjusted. A modal decomposition
stores modes and not a grid, and a boundary element method stores a dense
matrix over the surface rather than a sparse field over the volume. Both would
invert the conclusion at the end of this document.

## The symbols

Physics, or a property of the problem the user brings:

    V         room volume                                    m^3
    S         area of the surfaces bounding the room         m^2
    c         speed of sound in the air in the room          m/s
    f_max     highest frequency the run claims               Hz
    T         modelled time interval of a time domain run    s
    N_freq    number of frequencies of a frequency domain run

Properties of the scheme rather than of physics. Each one is an assumption
until #5 lands, the value used below is stated, and where it came from is
stated with it:

    n_ppw     grid points per wavelength at f_max. Assumed 6. It is not
              measured here and it is not a constant of any scheme: it is
              whatever holds the dispersion error at the top of the band,
              which is what issue #52 is for. Six is a middle value for a
              second order scheme and it is used here because a table needs
              one, not because it has been shown to be enough.
    n_f       field arrays kept over the interior at once. Assumed 3, which
              is two pressure time levels and one scratch array. A staggered
              pressure and velocity scheme keeps four and a scheme with a
              higher order time integrator keeps more.
    C         Courant number of the time step, dt = C h / c. Assumed
              1/sqrt(3) = 0.5774, the limit for the standard seven point
              scheme in three dimensions. The real limit is derived from the
              discretisation in #51 rather than configured, and until that
              lands this is an assumption.
    n_s       stored values per boundary node held by the wall model.
              Assumed 8, which is a fourth order rational fit of a surface
              impedance keeping two state values per order. #63 is where the
              fit is decided and #61 is the design note, so the number is a
              placeholder with a reason and not a result.

A contract rather than a scheme:

    b         bytes per stored value. Assumed 4, single precision. What is
              actually allowed to differ between two runs is #31, and if that
              lands on double precision every figure below doubles.

Derived:

    h         grid spacing, m
    N_i       interior grid points
    N_b       boundary nodes
    M         predicted resident bytes
    N_t       time steps

## The spacing

    h = c / (n_ppw * f_max)

This is the wavelength term and it is the one the cube law comes from. It is
not the whole story, and the part it leaves out is the part that decides
whether this project is expensive. The grid also has to resolve the geometry:
a step, a niche, a door reveal or a porous layer that the model is supposed to
represent has to be several cells across, whatever the wavelength is. So

    h = min( c / (n_ppw * f_max) , d_min / n_geom )

where `d_min` is the smallest feature the software undertakes to represent and
`n_geom` is the cells it needs across it. Neither is fixed here. What a room is
allowed to be is #10, and it is the issue that owes `d_min`; how the room is
discretised and what is lost doing it is #37.

In the band this project names, the second term is the one that is likely to
bind. At 300 Hz the wavelength term gives a spacing of 0.19 m, and a room
whose 5 cm skirting or 10 cm absorber layer is supposed to be present needs a
spacing an order of magnitude smaller than that. Every figure below uses the
wavelength term alone, so every figure below is a floor rather than an
estimate.

## Memory

    N_i = V / h^3
    N_b = S / h^2
    M   = b * ( n_f * N_i  +  n_s * N_b )

The first term is cubic in `f_max` and linear in volume, which is the sentence
in the readme:

    git show HEAD:README.md | grep -o "Memory scales with the cube of frequency."
    Memory scales with the cube of frequency.

The second term is the one people forget. A frequency dependent impedance in
the time domain is a filter and not a number, and a filter has state at every
node it runs at. It is quadratic in `f_max` rather than cubic, so it is a
constant share of nothing at high frequency and a visible share at the bottom
of the range, where the surface has relatively more nodes than the volume.

`S` depends on the shape and not only on the volume. Every figure below takes
the room as a cube, so `S = 6 * V^(2/3)`. A long thin room of the same volume
has more surface than that and a compact one has less. The error this
introduces is confined to the second term.

## Runtime

Time domain. The step follows the spacing through the stability limit, so
the step count carries `f_max` a fourth time:

    dt  = C * h / c
    N_t = T / dt = T * n_ppw * f_max / C

The speed of sound cancels out of `N_t`, which is worth noticing: how long a
run takes in steps does not depend on how fast sound travels, only on how
finely the band is sampled and for how long the room is modelled.

    work    = N_t * N_i * w
    runtime = N_t * N_i / R

`w` is arithmetic per grid point per step, a scheme property, and it is left
symbolic because it is not what decides the answer. `R` is grid point updates
per second on the machine, and it is a measurement rather than a prediction:
in practice it is set by memory bandwidth rather than by arithmetic, because a
seven point stencil reads far more than it computes. #85 is where `R` is
measured, and nothing here should be read as a claim about it.

Putting the two together, and holding `T` fixed:

    runtime  is proportional to  V * f_max^4

`T` is not a free choice. The run has to be long enough for the modes to
settle, which is #54, and the interval that requires is set by the decay of
the least damped mode rather than by the frequency. A hard room needs a longer
`T` than a damped one at the same `f_max`, so two rooms of one volume can cost
very differently.

Frequency domain. The step count is replaced by a count of solves:

    work = N_freq * (cost of one solve over N_i unknowns)

and `N_freq` is set by the frequency resolution the result needs rather than
by the stability limit. The cost of one solve is not a formula that can be
written here without the method: a sparse direct factorisation costs more than
linearly in `N_i` because of fill-in and keeps the factors in memory, which
would add a term to the memory formula larger than anything above, while an
iterative solve costs the iteration count times something linear in `N_i` and
adds only a few vectors. Which of the two applies is not decided, and neither
is whether this project works in the time domain at all, which is #7.

## The table

Produced at this commit by the program beside this document:

    python docs/memory-model.py

<!-- generated: python docs/memory-model.py -->

    c = 343 m/s, 6 points per wavelength, 3 array(s) of 4 byte(s),
    8 stored value(s) per boundary node, Courant 0.5774, 1 s modelled.
    Rooms are taken as cubes for their surface area.
    A row marked * exceeds 64 GiB.

       V (m3)      100 Hz      200 Hz      300 Hz      500 Hz     1000 Hz     2000 Hz     4000 Hz     8000 Hz    16000 Hz
           30    7.42 KiB    37.2 KiB     101 KiB     374 KiB    2.38 MiB    16.9 MiB     126 MiB     976 MiB    7.49 GiB
           60    12.6 KiB    65.3 KiB     181 KiB     690 KiB    4.53 MiB    32.8 MiB     249 MiB    1.89 GiB    14.9 GiB
          120    21.5 KiB     116 KiB     329 KiB    1.26 MiB    8.71 MiB    64.3 MiB     492 MiB    3.76 GiB    29.7 GiB
          250    38.5 KiB     217 KiB     628 KiB    2.47 MiB    17.5 MiB     131 MiB    1016 MiB    7.80 GiB    61.8 GiB
          500    67.5 KiB     395 KiB    1.14 MiB    4.71 MiB    34.2 MiB     259 MiB    1.97 GiB    15.5 GiB    123 GiB*
         1000     120 KiB     731 KiB    2.16 MiB    9.06 MiB    66.9 MiB     512 MiB    3.92 GiB    31.0 GiB    246 GiB*
         2000     217 KiB    1.34 MiB    4.11 MiB    17.5 MiB     131 MiB    1016 MiB    7.80 GiB    61.8 GiB    492 GiB*

    Upper frequency at which the interior arrays alone reach 64 GiB,
    and the time steps a 1 s run costs there:

       V (m3)    f at limit steps at that f
           30       32916 Hz        3.42e+05
           60       26125 Hz        2.72e+05
          120       20736 Hz        2.15e+05
          250       16235 Hz        1.69e+05
          500       12886 Hz        1.34e+05
         1000       10228 Hz        1.06e+05
         2000        8118 Hz        8.44e+04

    Grid spacing and step count in the band this project claims:

         f (Hz)       h (m)     steps per s       points/m3
            100     0.57167            1039           5.353
            200     0.28583            2078           42.82
            300     0.19056            3118           144.5
            500     0.11433            5196           669.1
           1000     0.05717       1.039e+04            5353
           2000     0.02858       2.078e+04       4.282e+04
           4000     0.01429       4.157e+04       3.426e+05
           8000     0.00715       8.314e+04       2.741e+06
          16000     0.00357       1.663e+05       2.192e+07

<!-- end generated -->

The marked cells are the ones above 64 GiB, and the mark is on the cell rather
than on the row because within one row the frequency decides it. 64 GiB is
2^36 bytes and it is not the same as 64 GB, which is 7 per cent smaller; the
figure this board is written against is quoted in the issues as sixty-four
gigabytes without saying which, and this document reads it as the binary one
because that is what a machine reports its memory as. #16 is where the figure
itself is argued.

## What the table says, which is not what was expected

In the band this project claims, memory is not the constraint. A 2000 m^3 hall
at 300 Hz predicts 4.11 MiB, which is five orders of magnitude below the
figure the plan is written against. Under this assumption set the interior
arrays do not reach 64 GiB until roughly 8 kHz in that hall and roughly 21 kHz
in a 120 m^3 room, and both are far above the range the readme describes.

The cube law is real and the figure is real. What is wrong is the implicit
join between them: they meet at full audio bandwidth, not at the top of the
modal region. Three things follow, and none of them is a decision this
document may make.

The first is that if memory is the reason to stop at 300 Hz, it is the wrong
reason, and the ceiling issue #11 should say what the real one is. Runtime is
a candidate, because it carries `f_max` a fourth time rather than a third, and
so is the accuracy of the wall model, which is what this project exists for and
which does not improve with frequency.

The second is that the geometric term in the spacing above, not the wavelength
term, is what actually sets the grid in this band, so the cost of this project
is decided by what #10 says a room is allowed to contain rather than by
`f_max`. A 120 m^3 room resolved to 1 cm because a skirting board is in the
model has 1.2e8 interior points regardless of the frequency, which is 1.3 GiB
of field arrays under this assumption set.

The third is that these are predictions from an assumption set that has four
unmeasured members, and any of them can move the answer. The interior term is cubic
in `n_ppw`, so at 12 points per wavelength rather than 6 it is 8 times larger,
and the 2000 m^3 hall at 300 Hz becomes 29.7 MiB rather than 4.11 MiB:

    python docs/memory-model.py --ppw 12 --volumes 2000 --frequencies 300
       V (m3)      300 Hz
         2000    29.7 MiB

That is a little under 8 times because the boundary term is quadratic rather
than cubic and grows only fourfold. Still not 64 GiB. That is the sense in
which the conclusion is robust: it survives a factor of 8 in the quantity it is
most sensitive to.

## What this model does not carry

It does not carry the halo, padding or alignment a real implementation adds,
nor index and material arrays over the grid, nor whatever the output holds:
a transfer function at a handful of receivers is negligible against the field,
and a room impulse response stored at every node is not, and nothing here
decides which is stored.

It does not carry the memory a frequency domain factorisation would keep, for
the reason given above.

It does not carry an accelerator. Whether a vendor specific path is supported
at all is entry 8 of #1 and has no answer, and a device with its own memory
turns one figure into two with a transfer between them.

It does not carry the working set. A run whose arrays do not fit in memory
does not run 10 per cent slower, it stops being the same computation, and
where that boundary sits is a measurement.

It says nothing about what a user waits. That is `R` above, and `R` is not
predicted here.

## What refers to this

#82 measures memory against frequency and volume and reports the difference.
#85 does the same for runtime and is where `R` first exists. #83 publishes the
ceiling that comes out of both. #84 refuses a run that will not fit before it
starts, and the formula it needs is the one above with the assumption set
replaced by measured values. #16 carries the one machine constraint this
document supplies the numbers for.
