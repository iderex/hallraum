"""Print the predicted memory and step count for a volumetric grid solver.

The model is written down in docs/memory-and-runtime-model.md and it is a
prediction rather than a measurement. Every quantity that is a property of a
scheme rather than of physics is an option with a default, and the defaults are
the assumption set named in that document. Change one on the command line and
the whole table moves with it, which is the point: a table nobody can re-derive
under a different assumption is a number pretending to be a model.

    python docs/memory-model.py

Standard library only. Nothing imports this and it imports nothing beyond the
standard library, so it cannot drift into being part of the software.
"""

import argparse

# Physics rather than scheme. The speed of sound is a function of temperature
# and humidity; 343 m/s is dry air at 20 C and is the value the document
# assumes. Air is issue #41 and this is not the place it is decided.
DEFAULT_C = 343.0

DEFAULT_VOLUMES = [30, 60, 120, 250, 500, 1000, 2000]
DEFAULT_FREQUENCIES = [100, 200, 300, 500, 1000, 2000, 4000, 8000, 16000]

GIB = 1024 ** 3


def spacing(c, points_per_wavelength, f_max):
    """Grid spacing that puts the requested number of points on the shortest
    wavelength in the band. Metres."""
    return c / (points_per_wavelength * f_max)


def surface_area(volume):
    """Bounding area of a cube of this volume, in square metres. A stand-in for
    the shape, and the document says what it costs: a long thin room of the
    same volume has more surface and a room shaped like a sphere has less."""
    return 6.0 * volume ** (2.0 / 3.0)


def memory_bytes(volume, f_max, c, ppw, arrays, value_bytes, boundary_state):
    """Predicted resident bytes: the field arrays over the interior, plus the
    filter state the boundary model keeps at every boundary node."""
    h = spacing(c, ppw, f_max)
    interior = volume / h ** 3
    boundary = surface_area(volume) / h ** 2
    return value_bytes * (arrays * interior + boundary_state * boundary)


def steps(f_max, seconds, c, ppw, courant):
    """Number of time steps for a run of the given length, at the largest step
    the stability limit allows. The limit is derived from the discretisation in
    issue #51 and is a scheme property here."""
    del c  # cancels: dt = courant * h / c and h is proportional to c / f_max
    return seconds * ppw * f_max / courant


def ceiling_frequency(volume, limit, c, ppw, arrays, value_bytes):
    """The upper frequency at which the interior arrays alone reach the limit.
    The boundary term is left out so the answer is a closed form; it is an
    over-estimate of the ceiling by however much the boundary term is worth,
    which the table beside it shows is small in this band."""
    points = limit / (value_bytes * arrays)
    return (c / ppw) * (points / volume) ** (1.0 / 3.0)


def human(n):
    for unit, size in (("GiB", GIB), ("MiB", 1024 ** 2), ("KiB", 1024)):
        if n >= size:
            v = n / size
            fmt = "%.0f" if v >= 100 else ("%.1f" if v >= 10 else "%.2f")
            return (fmt + " %s") % (v, unit)
    return "%d B" % round(n)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--c", type=float, default=DEFAULT_C,
                   help="speed of sound, m/s (physics, not scheme)")
    p.add_argument("--ppw", type=float, default=6.0,
                   help="points per wavelength at the upper frequency (scheme)")
    p.add_argument("--arrays", type=float, default=3.0,
                   help="field arrays kept over the interior (scheme)")
    p.add_argument("--bytes", type=float, default=4.0, dest="value_bytes",
                   help="bytes per stored value (contract, issue #31)")
    p.add_argument("--boundary-state", type=float, default=8.0,
                   help="stored values per boundary node (boundary model)")
    p.add_argument("--courant", type=float, default=1.0 / 3.0 ** 0.5,
                   help="Courant number of the time step (scheme)")
    p.add_argument("--seconds", type=float, default=1.0,
                   help="modelled time interval for the step count, s")
    p.add_argument("--limit", type=float, default=64.0,
                   help="memory figure the plan is written against, GiB")
    p.add_argument("--volumes", type=float, nargs="+", default=DEFAULT_VOLUMES,
                   help="room volumes, cubic metres")
    p.add_argument("--frequencies", type=float, nargs="+",
                   default=DEFAULT_FREQUENCIES, help="upper frequencies, Hz")
    a = p.parse_args()

    limit = a.limit * GIB
    print("c = %g m/s, %g points per wavelength, %g array(s) of %g byte(s),"
          % (a.c, a.ppw, a.arrays, a.value_bytes))
    print("%g stored value(s) per boundary node, Courant %.4f, %g s modelled."
          % (a.boundary_state, a.courant, a.seconds))
    print("Rooms are taken as cubes for their surface area.")
    print("A row marked * exceeds %g GiB." % a.limit)
    print()

    head = "%9s" % "V (m3)"
    for f in a.frequencies:
        head += "%12s" % ("%g Hz" % f)
    print(head)
    for v in a.volumes:
        line = "%9g" % v
        for f in a.frequencies:
            m = memory_bytes(v, f, a.c, a.ppw, a.arrays, a.value_bytes,
                             a.boundary_state)
            cell = human(m) + ("*" if m > limit else "")
            line += "%12s" % cell
        print(line)

    print()
    print("Upper frequency at which the interior arrays alone reach %g GiB,"
          % a.limit)
    print("and the time steps a %g s run costs there:" % a.seconds)
    print()
    print("%9s%14s%16s" % ("V (m3)", "f at limit", "steps at that f"))
    for v in a.volumes:
        f = ceiling_frequency(v, limit, a.c, a.ppw, a.arrays, a.value_bytes)
        print("%9g%12.0f Hz%16.3g" % (v, f, steps(f, a.seconds, a.c, a.ppw,
                                                  a.courant)))

    print()
    print("Grid spacing and step count in the band this project claims:")
    print()
    print("%11s%12s%16s%16s" % ("f (Hz)", "h (m)", "steps per s", "points/m3"))
    for f in a.frequencies:
        h = spacing(a.c, a.ppw, f)
        print("%11g%12.5f%16.4g%16.4g"
              % (f, h, steps(f, 1.0, a.c, a.ppw, a.courant), 1.0 / h ** 3))


if __name__ == "__main__":
    main()
