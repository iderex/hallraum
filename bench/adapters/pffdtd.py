"""An external finite difference time domain candidate.

This adapter exists to be a second one. The runner holds no list of adapters,
and the way to show that is to add a file and watch it appear in the result
without the runner changing.

It is also the ordinary case. Most entries in a field of research codes are not
installed on the machine somebody runs a bench on, and what the bench owes there
is a recorded reason rather than a gap. probe() says what it looked for and what
it found.

The translation from the neutral room form into this candidate's input is not
written. That is deliberate and it is not a placeholder that was forgotten. The
translation would have to be written against documentation, since the candidate
cannot be run here to check it, and a translation nobody has executed is exactly
the kind of claim this bench was built to stop the survey from making. It gets
written by whoever first has the candidate installed, and command() says so
where a reader will meet it.
"""

import importlib.util
import shutil

NAME = "pffdtd"
SUMMARY = "External finite difference time domain solver for room acoustics."

MODULE = "pffdtd"
EXECUTABLE = "pffdtd"


def probe():
    from . import Unavailable

    found = importlib.util.find_spec(MODULE)
    if found is not None:
        version = getattr(importlib.import_module(MODULE), "__version__", None)
        return {
            "version": version or "importable, no __version__ attribute",
            "how_version_was_obtained": "%s.__version__" % MODULE,
        }
    on_path = shutil.which(EXECUTABLE)
    if on_path:
        return {
            "version": "found at %s, version not read" % on_path,
            "how_version_was_obtained": "shutil.which only; no version command "
                                        "is known to this adapter",
        }
    raise Unavailable(
        "not installed: no importable module %r and no %r on PATH"
        % (MODULE, EXECUTABLE))


def command(room_path, out_path, grid):
    from . import Unavailable

    del room_path, out_path, grid
    raise Unavailable(
        "the room translation for this candidate is not written; it needs the "
        "candidate present to be checked against, and this adapter will not "
        "guess an input format from documentation")
