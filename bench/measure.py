"""Run one child process and measure what it cost.

The bench compares candidates that agree about nothing, so the only figures it
can take are the ones the operating system keeps about a process: how long it
ran and how much memory it held at its worst moment. Both are measured for the
child, never for the bench, so a candidate that leaks or that allocates its
whole grid up front is visible.

Peak resident memory has no portable interface in the standard library, so
there are two implementations and they are not equivalent. Read what each one
returns before quoting a number from it.
"""

import os
import platform
import subprocess
import sys
import tempfile
import time

# What the runner does with an exit status. A candidate that will not accept a
# room is not the same event as one that broke, and collapsing the two would
# lose the most common result in practice.
EXIT_REFUSED = 2


class Measured:
    """One child run, with what it printed and what it cost."""

    def __init__(self, argv, returncode, stdout, stderr, seconds, peak_rss_bytes,
                 peak_rss_source):
        self.argv = argv
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.seconds = seconds
        self.peak_rss_bytes = peak_rss_bytes
        self.peak_rss_source = peak_rss_source

    def as_dict(self):
        return {
            "argv": self.argv,
            "returncode": self.returncode,
            "wall_clock_s": round(self.seconds, 6),
            "peak_rss_bytes": self.peak_rss_bytes,
            "peak_rss_source": self.peak_rss_source,
            "stderr_tail": tail(self.stderr),
        }


def tail(text, limit=2000):
    """The end of a message, which is where a failure says what happened."""
    text = (text or "").strip()
    return text if len(text) <= limit else "..." + text[-limit:]


def run(argv, cwd=None, timeout_s=None):
    """Run argv to completion and return a Measured.

    Output goes to temporary files rather than to pipes so that a candidate
    printing more than a pipe buffer holds cannot deadlock the bench.
    """
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as out, \
            tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as err:
        started = time.perf_counter()
        if os.name == "nt":
            returncode, peak, source = _run_windows(argv, cwd, out, err, timeout_s)
        else:
            returncode, peak, source = _run_posix(argv, cwd, out, err, timeout_s)
        seconds = time.perf_counter() - started
        out.seek(0)
        err.seek(0)
        return Measured(list(argv), returncode, out.read(), err.read(), seconds,
                        peak, source)


def _run_windows(argv, cwd, out, err, timeout_s):
    """PeakWorkingSetSize of the child, read after it exits.

    The process handle stays valid after exit until it is closed, and the
    counters stay readable with it, so this is the child's own high-water mark
    and not a sample taken while it ran.
    """
    import ctypes
    from ctypes import wintypes

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    child = subprocess.Popen(argv, cwd=cwd, stdout=out, stderr=err,
                             stdin=subprocess.DEVNULL)
    try:
        returncode = child.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait()
        returncode = None

    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(counters)
    ok = ctypes.WinDLL("psapi").GetProcessMemoryInfo(
        int(child._handle), ctypes.byref(counters), counters.cb)
    peak = int(counters.PeakWorkingSetSize) if ok else None
    return returncode, peak, "GetProcessMemoryInfo.PeakWorkingSetSize"


def _run_posix(argv, cwd, out, err, timeout_s):
    """ru_maxrss of the child, from wait4.

    subprocess offers no way to reach the child's rusage, so the child is
    spawned directly. There is no timeout on this path: os.wait4 blocks, and a
    timeout that killed the child would also lose the rusage the call returns.
    A candidate that hangs hangs the bench here, which is stated rather than
    worked around.
    """
    del timeout_s
    file_actions = [
        (os.POSIX_SPAWN_DUP2, out.fileno(), 1),
        (os.POSIX_SPAWN_DUP2, err.fileno(), 2),
    ]
    pid = os.posix_spawnp(argv[0], list(argv), _environ_for(cwd),
                          file_actions=file_actions)
    _, status, usage = os.wait4(pid, 0)
    returncode = os.waitstatus_to_exitcode(status)
    # ru_maxrss is kilobytes on Linux and bytes on macOS. Anywhere else it is
    # not established, so the unit travels with the number instead of being
    # assumed by whoever reads the result file.
    if sys.platform == "darwin":
        return returncode, int(usage.ru_maxrss), "wait4.ru_maxrss (bytes)"
    if sys.platform.startswith("linux"):
        return returncode, int(usage.ru_maxrss) * 1024, "wait4.ru_maxrss (KiB)"
    return returncode, None, "wait4.ru_maxrss (unit unknown on %s)" % sys.platform


def _environ_for(cwd):
    """posix_spawnp has no cwd argument, so a candidate needing one is refused
    here rather than silently run in the wrong directory."""
    if cwd is not None and os.path.abspath(cwd) != os.path.abspath(os.getcwd()):
        raise NotImplementedError(
            "an adapter asking for a working directory is not supported on this "
            "platform; give the candidate absolute paths instead")
    return dict(os.environ)


def machine():
    """What the numbers above were measured on.

    No hostname and no user name: this file is written to be pasted into an
    issue, and neither of those says anything about the measurement.
    """
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
        "python": platform.python_version(),
    }
