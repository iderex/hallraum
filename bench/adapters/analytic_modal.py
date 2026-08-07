"""The closed form for a rigid rectangular room, driven as a candidate.

This is a candidate rather than a check. It is in the field because a bench
whose every entry is an approximation cannot tell a candidate that is wrong
from a bench that is wrong, and because it runs everywhere, so a run of the
whole bench on a machine where nothing else builds still produces one curve.

It accepts one room shape and one wall model, and it refuses everything else
loudly. That is most of what it contributes: the set of rooms it turns down is
the set where no closed form is available to argue from.

What it adds to the room, and what a reader has to know before quoting a number
from it: a rigid room is lossless, its poles sit on the real frequency axis, and
its response there is infinite. The sum below is evaluated with a uniform modal
damping so that the curve exists at all. The room file does not carry that
damping and does not ask for it. It is the candidate's assumption, it is written
into the result file, and it is the reason a magnitude near a mode from this
candidate is not a measurement of anything.
"""

import json
import math
import os
import sys

NAME = "analytic-modal-rigid-box"
SUMMARY = "Modal sum for a rigid rectangular room, evaluated in double precision."

# The room has no losses, so the sum has to be given some. A reverberation time
# of three seconds is a lightly damped real room and is stated here rather than
# chosen per room, because a per-room value would be a modelling knob the bench
# has no basis to set.
ASSUMED_T60_S = 3.0

# Modes are summed past the top of the band because a mode above it still
# contributes below it. Twice the top is the rule; it is stated in the result
# file with the count it produced, so a reader can see what was truncated.
MODE_CEILING_FACTOR = 2.0

STANDARD_PRESSURE_PA = 101325.0
SPECIFIC_GAS_CONSTANT = 287.058


def probe():
    """This candidate is this file, so its version is the interpreter it runs on
    plus the content of the file itself."""
    return {
        "version": "python %s, %s" % (sys.version.split()[0], _self_digest()),
        "how_version_was_obtained": "sha256 of this adapter file, truncated",
    }


def command(room_path, out_path, grid):
    return [
        sys.executable,
        os.path.abspath(__file__),
        "--room", str(room_path),
        "--out", str(out_path),
        "--f-start", repr(grid["start_hz"]),
        "--f-stop", repr(grid["stop_hz"]),
        "--f-step", repr(grid["step_hz"]),
    ]


def _self_digest():
    import hashlib
    with open(os.path.abspath(__file__), "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


# Everything below runs in the child process.

def _refuse(message):
    sys.stderr.write(message + "\n")
    raise SystemExit(_exit_refused())


def _exit_refused():
    """The refusal code the interface defines, taken from it rather than
    repeated here, so the two cannot drift apart."""
    from bench.measure import EXIT_REFUSED
    return EXIT_REFUSED


def _read_room(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _check(room):
    """Accept a rigid box, refuse anything else and say which part was refused."""
    geometry = room["geometry"]
    if geometry.get("kind") != "box":
        _refuse("refused: geometry.kind is %r; this candidate is the closed form "
                "for a rectangular room and has nothing to say about any other "
                "shape" % geometry.get("kind"))
    for surface in room["surfaces"]:
        kind = surface["model"].get("kind")
        if kind != "rigid":
            _refuse("refused: surface %r has model.kind %r; the closed form used "
                    "here holds for rigid walls only, and an absorbing wall moves "
                    "the eigenvalues into the complex plane rather than damping "
                    "the existing ones" % (surface["id"], kind))
    for source in room["sources"]:
        if source.get("kind") != "point_volume_velocity":
            _refuse("refused: source %r has kind %r, and this candidate models a "
                    "point volume velocity source only"
                    % (source["id"], source.get("kind")))


def _air(room):
    celsius = room["air"]["temperature_c"]
    kelvin = 273.15 + celsius
    speed = 20.05 * math.sqrt(kelvin)
    density = STANDARD_PRESSURE_PA / (SPECIFIC_GAS_CONSTANT * kelvin)
    return speed, density


def _modes(dimensions, speed, ceiling_hz):
    """Every mode whose eigenfrequency is at or below the ceiling.

    Returned as (indices, wavenumber, normalisation), where normalisation is the
    integral of the mode shape squared over the room.
    """
    lx, ly, lz = dimensions
    volume = lx * ly * lz
    limits = [int(2.0 * ceiling_hz * length / speed) + 1 for length in dimensions]
    modes = []
    for nx in range(limits[0] + 1):
        for ny in range(limits[1] + 1):
            for nz in range(limits[2] + 1):
                k_n = math.pi * math.sqrt((nx / lx) ** 2 + (ny / ly) ** 2
                                          + (nz / lz) ** 2)
                if k_n * speed / (2.0 * math.pi) > ceiling_hz:
                    continue
                weight = volume
                for index in (nx, ny, nz):
                    if index:
                        weight *= 0.5
                modes.append(((nx, ny, nz), k_n, weight))
    return modes


def _shape(indices, position, dimensions):
    value = 1.0
    for index, coordinate, length in zip(indices, position, dimensions):
        value *= math.cos(index * math.pi * coordinate / length)
    return value


def _inside(position, dimensions):
    return all(0.0 <= coordinate <= length
               for coordinate, length in zip(position, dimensions))


def _transfer(room, frequencies):
    _check(room)
    dimensions = room["geometry"]["dimensions_m"]
    speed, density = _air(room)
    decay = 3.0 * math.log(10.0) / ASSUMED_T60_S
    ceiling = MODE_CEILING_FACTOR * max(frequencies)
    modes = _modes(dimensions, speed, ceiling)

    for point in room["sources"] + room["receivers"]:
        if not _inside(point["position_m"], dimensions):
            _refuse("refused: %r at %s is outside the room" %
                    (point["id"], point["position_m"]))

    pairs = []
    for source in room["sources"]:
        strength = source["strength_m3_s"]
        source_shape = [_shape(indices, source["position_m"], dimensions)
                        for indices, _, _ in modes]
        for receiver in room["receivers"]:
            receiver_shape = [_shape(indices, receiver["position_m"], dimensions)
                              for indices, _, _ in modes]
            real, imaginary = [], []
            for frequency in frequencies:
                omega = 2.0 * math.pi * frequency
                k = omega / speed
                total = 0j
                for index, (_, k_n, weight) in enumerate(modes):
                    denominator = (k * k - k_n * k_n
                                   - 2j * k_n * decay / speed)
                    total += (source_shape[index] * receiver_shape[index]
                              / (weight * denominator))
                pressure = 1j * omega * density * strength * total
                real.append(pressure.real)
                imaginary.append(pressure.imag)
            pairs.append({
                "source": source["id"],
                "receiver": receiver["id"],
                "pressure_pa_re": real,
                "pressure_pa_im": imaginary,
            })
    return pairs, modes, speed, density


def main(argv):
    options = dict(zip(argv[::2], argv[1::2]))
    room = _read_room(options["--room"])
    start = float(options["--f-start"])
    stop = float(options["--f-stop"])
    step = float(options["--f-step"])
    count = int(round((stop - start) / step)) + 1
    frequencies = [start + index * step for index in range(count)]

    pairs, modes, speed, density = _transfer(room, frequencies)

    with open(options["--out"], "w", encoding="utf-8", newline="\n") as handle:
        json.dump({
            "candidate": NAME,
            "room": room["id"],
            "frequencies_hz": frequencies,
            "quantity": "complex sound pressure in pascals at the receiver, for "
                        "the source volume velocity given in the room file",
            "assumptions": {
                "modal_damping_t60_s": ASSUMED_T60_S,
                "why": "the room in the file is lossless, so its response at a "
                       "mode is infinite; this damping is added by the candidate "
                       "and is not in the room",
                "modes_summed": len(modes),
                "mode_ceiling_hz": MODE_CEILING_FACTOR * max(frequencies),
                "speed_of_sound_m_s": speed,
                "air_density_kg_m3": density,
                "arithmetic": "double precision, modes summed in index order",
            },
            "pairs": pairs,
        }, handle, indent=1)
        handle.write("\n")


if __name__ == "__main__":
    # Run by absolute path rather than as a package module, so the repository
    # root is put on the path here and nowhere else. The only thing taken from
    # the package is the refusal exit code.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    main(sys.argv[1:])
