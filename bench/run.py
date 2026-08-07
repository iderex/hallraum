"""Run every adapter against every room and write down what happened.

One command, one result file. The bench measures and records; it does not
judge, it does not rank, and it computes no error against anything, because the
whole point of running candidates that disagree about their input format is to
find out what each one will do before there is any basis for scoring them.

A candidate that is not installed, that will not accept a room, or that dies is
recorded with what it said and the run carries on. Nothing here stops on a
failure: on a field of research codes, stopping on the first failure means
measuring one candidate.

    python bench/run.py --out bench/out/results.json
"""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from bench import adapters as adapter_package  # noqa: E402
from bench import measure  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
REPOSITORY = HERE.parent


def parse_arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rooms", default=str(HERE / "rooms"),
                        help="directory of rooms in the neutral form")
    parser.add_argument("--out", default=str(HERE / "out" / "results.json"),
                        help="the one machine-readable result file")
    parser.add_argument("--work-dir", default=str(HERE / "out" / "runs"),
                        help="where each candidate writes its own output")
    parser.add_argument("--f-start", type=float, default=20.0)
    parser.add_argument("--f-stop", type=float, default=300.0)
    parser.add_argument("--f-step", type=float, default=1.0)
    parser.add_argument("--timeout-s", type=float, default=1800.0,
                        help="per run; honoured on Windows only, see measure.py")
    return parser.parse_args(argv)


def load_rooms(directory):
    rooms = []
    for path in sorted(pathlib.Path(directory).glob("*.json")):
        with open(path, encoding="utf-8") as handle:
            room = json.load(handle)
        room["_path"] = str(path)
        rooms.append(room)
    return rooms


def expected_frequencies(grid):
    count = int(round((grid["stop_hz"] - grid["start_hz"]) / grid["step_hz"])) + 1
    return [grid["start_hz"] + index * grid["step_hz"] for index in range(count)]


def probe_all(adapters):
    """Ask every adapter whether its candidate is here, before running anything.

    A probe that raises anything other than Unavailable is still just a
    candidate that cannot be run, so the reason is recorded in the same field
    and the type of the exception with it.
    """
    probed = {}
    for name, adapter in adapters.items():
        entry = {"summary": getattr(adapter, "SUMMARY", ""), "available": False}
        try:
            entry.update(adapter.probe())
            entry["available"] = True
        except adapter_package.Unavailable as reason:
            entry["unavailable_because"] = str(reason)
        except Exception as reason:  # noqa: BLE001 - a broken probe is a result
            entry["unavailable_because"] = "%s: %s" % (type(reason).__name__,
                                                       reason)
        probed[name] = entry
    return probed


def read_candidate_output(path, frequencies):
    """Read what a candidate wrote and check it is on the grid it was asked for.

    A curve on a different grid is not a comparable answer, so it is a failed
    run rather than a run whose numbers get quietly resampled here.
    """
    with open(path, encoding="utf-8") as handle:
        produced = json.load(handle)
    given = produced.get("frequencies_hz")
    if given is None:
        raise ValueError("output carries no frequencies_hz")
    if len(given) != len(frequencies):
        raise ValueError("output has %d frequencies, the bench asked for %d"
                         % (len(given), len(frequencies)))
    worst = max(abs(a - b) for a, b in zip(given, frequencies))
    if worst > 1e-9:
        raise ValueError("output frequencies differ from the requested grid by "
                         "up to %g Hz" % worst)
    if not produced.get("pairs"):
        raise ValueError("output carries no source and receiver pairs")
    return produced


def run_one(adapter, room, grid, frequencies, work_dir, timeout_s):
    """One candidate against one room. Returns a record, never raises."""
    record = {"candidate": adapter.NAME, "room": room["id"]}
    out_path = pathlib.Path(work_dir) / ("%s__%s.json" % (room["id"], adapter.NAME))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    try:
        argv = adapter.command(room["_path"], str(out_path), grid)
    except adapter_package.Unavailable as reason:
        record.update(status="not-translated", detail=str(reason))
        return record
    except Exception as reason:  # noqa: BLE001
        record.update(status="failed",
                      detail="building the command raised %s: %s"
                             % (type(reason).__name__, reason))
        return record

    try:
        measured = measure.run(argv, timeout_s=timeout_s)
    except Exception as reason:  # noqa: BLE001 - a candidate cannot kill the run
        record.update(status="failed",
                      detail="launching the candidate raised %s: %s"
                             % (type(reason).__name__, reason))
        return record

    record["cost"] = measured.as_dict()

    if measured.returncode is None:
        record.update(status="timed-out",
                      detail="killed after %g s" % timeout_s)
        return record
    if measured.returncode == measure.EXIT_REFUSED:
        record.update(status="refused", detail=measure.tail(measured.stderr))
        return record
    if measured.returncode != 0:
        record.update(status="failed",
                      detail="exit %d: %s" % (measured.returncode,
                                              measure.tail(measured.stderr)))
        return record
    if not out_path.exists():
        record.update(status="failed",
                      detail="exit 0 but no result file at %s" % out_path)
        return record

    try:
        produced = read_candidate_output(out_path, frequencies)
    except Exception as reason:  # noqa: BLE001
        record.update(status="failed",
                      detail="unusable output: %s: %s" % (type(reason).__name__,
                                                          reason))
        return record

    record.update(
        status="ran",
        quantity=produced.get("quantity"),
        assumptions=produced.get("assumptions"),
        pairs=produced["pairs"],
        raw_output=os.path.relpath(out_path, REPOSITORY).replace("\\", "/"),
        raw_output_sha256=_digest(out_path),
    )
    return record


def _digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def bench_commit():
    """The commit the bench ran at, so a result file can be placed in history.

    A tree with uncommitted changes says so, because a figure measured from an
    edited working tree is not a figure measured at any commit.
    """
    try:
        head = subprocess.run(["git", "-C", str(REPOSITORY), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=30)
        dirty = subprocess.run(["git", "-C", str(REPOSITORY), "status",
                                "--porcelain"],
                               capture_output=True, text=True, timeout=30)
    except Exception as reason:  # noqa: BLE001
        return "unknown: %s: %s" % (type(reason).__name__, reason)
    if head.returncode != 0:
        return "unknown: git rev-parse exited %d" % head.returncode
    commit = head.stdout.strip()
    return commit if not dirty.stdout.strip() else commit + " (working tree dirty)"


def main(argv=None):
    options = parse_arguments(sys.argv[1:] if argv is None else argv)
    grid = {"start_hz": options.f_start, "stop_hz": options.f_stop,
            "step_hz": options.f_step}
    frequencies = expected_frequencies(grid)
    rooms = load_rooms(options.rooms)
    adapters = adapter_package.discover()
    probed = probe_all(adapters)

    runs = []
    for room in rooms:
        for name, adapter in adapters.items():
            if not probed[name]["available"]:
                runs.append({"candidate": name, "room": room["id"],
                             "status": "unavailable",
                             "detail": probed[name]["unavailable_because"]})
                continue
            runs.append(run_one(adapter, room, grid, frequencies,
                                options.work_dir, options.timeout_s))

    result = {
        "bench_commit": bench_commit(),
        "machine": measure.machine(),
        "grid_hz": grid,
        "rooms": [{"id": room["id"], "description": room["description"],
                   "path": os.path.relpath(room["_path"], REPOSITORY).replace(
                       "\\", "/")}
                  for room in rooms],
        "candidates": probed,
        "runs": runs,
    }

    out_path = pathlib.Path(options.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=1)
        handle.write("\n")

    counted = {}
    for run in runs:
        counted[run["status"]] = counted.get(run["status"], 0) + 1
    print("%d room(s), %d candidate(s), %d run(s): %s"
          % (len(rooms), len(adapters), len(runs),
             ", ".join("%s %d" % pair for pair in sorted(counted.items()))))
    print("result file: %s" % out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
