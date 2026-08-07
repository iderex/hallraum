"""The adapter interface, and how the runner finds adapters.

An adapter is one module in this package. It translates a room in the bench's
neutral form into whatever its candidate wants, and translates the candidate's
output back into a transfer function on the frequency grid the bench asked for.
It answers three things and nothing else:

    NAME        a short identifier, unique in this package
    SUMMARY     one sentence saying what candidate this drives
    probe()     the exact version of the candidate, or Unavailable with the
                reason it cannot be run on this machine
    command(room_path, out_path, grid)
                the argv the runner should launch, which must write the result
                file itself

The runner never imports a candidate and never calls into one. It launches the
argv as a child process, because the memory figure has to belong to the
candidate rather than to the bench, and because a candidate that dies has to
take nothing with it.

A candidate that will not accept a room exits with EXIT_REFUSED and says why on
stderr. Any other non-zero exit is a failure. The runner records both and goes
on to the next pair.

Adding an adapter is adding a file here. The runner has no list of adapters in
it, which is the property the survey depends on: a candidate that arrives late
must not need the harness changed to be measured beside the others.
"""

import importlib
import pkgutil


class Unavailable(Exception):
    """The candidate cannot be run on this machine, with the reason.

    Raised by probe(). It is a result, not an error: the most common outcome
    when a stranger runs a bench over a field of research codes is that most of
    them do not build.
    """


def discover():
    """Every adapter module in this package, by NAME.

    Import failure is caught and turned into a stub whose probe() raises
    Unavailable, so one adapter with a missing dependency at module scope
    cannot stop the others from being measured.
    """
    found = {}
    for module in pkgutil.iter_modules(__path__):
        if module.name.startswith("_"):
            continue
        try:
            loaded = importlib.import_module("%s.%s" % (__name__, module.name))
        except Exception as exc:  # noqa: BLE001 - any import failure is a result
            found[module.name] = _Broken(module.name, exc)
            continue
        missing = [a for a in ("NAME", "SUMMARY", "probe", "command")
                   if not hasattr(loaded, a)]
        if missing:
            found[module.name] = _Broken(
                module.name,
                RuntimeError("adapter is missing %s" % ", ".join(missing)))
            continue
        found[loaded.NAME] = loaded
    return dict(sorted(found.items()))


class _Broken:
    """An adapter that could not be loaded, presented as one that cannot run."""

    def __init__(self, name, exc):
        self.NAME = name
        self.SUMMARY = "adapter did not load"
        self._exc = exc

    def probe(self):
        raise Unavailable("%s: %s" % (type(self._exc).__name__, self._exc))

    def command(self, room_path, out_path, grid):
        raise Unavailable("%s: %s" % (type(self._exc).__name__, self._exc))
