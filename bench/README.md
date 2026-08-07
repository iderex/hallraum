# The bench

A survey that reads documentation returns opinions. This runs the candidates
instead: the same rooms, the same materials, the same question, and a record of
what each one did with them.

It measures and it does not judge. There is no score in the result file, no
error against a reference, and no ranking. Ranking needs a decision about what
matters that has not been made yet, and a number produced before that decision
would be quoted long after it.

## Running it

    python bench/run.py --out bench/out/results.json

One command, one machine-readable result file. Nothing is installed and nothing
is downloaded. A candidate that is not on the machine is recorded as not on the
machine and the rest of the run continues.

The frequency grid defaults to 20 Hz to 300 Hz in 1 Hz steps and is set with
`--f-start`, `--f-stop` and `--f-step`. Whatever it is, every candidate is asked
for the same one, and a candidate returning a curve on a different grid is a
failed run rather than one whose numbers get quietly resampled.

## What is in the result file

The commit the bench ran at, and whether the working tree was dirty when it ran.
The machine, without a hostname or a user name, because neither says anything
about the measurement and the file is written to be pasted into an issue. The
grid. Every room with its description. Every candidate with the version that was
found and how it was found. Then one record per candidate and room, with a
status:

    ran             the candidate produced a curve on the requested grid
    refused         the candidate would not accept the room, and said why
    failed          it exited non-zero, produced nothing, or produced something
                    unusable, with what it printed
    timed-out       it was still running when the limit was reached
    unavailable     the candidate is not on this machine
    not-translated  the adapter has no translation for this room yet

Every record that reached a process carries the wall clock time and the peak
resident memory of that process, and says which interface the memory figure came
from. The units are not the same on every platform and the field says which one
was used, so a number is never read as bytes because it looked like bytes.

## The rooms

`bench/rooms/` holds the set in the bench's neutral form. Each file carries its
own paragraph saying what it is and why it is in the set, so the reason travels
with the room rather than living in a list here that drifts.

The neutral form is the bench's own. It exists so that four candidates that
agree about nothing can be asked the same question, and it decides nothing about
what this project will accept from a user. That is a separate decision on the
tracker and it is not made here.

## Adapters

`bench/adapters/` holds one module per candidate. The interface is documented in
`bench/adapters/__init__.py`, which is also where the runner finds them: the
runner carries no list, so adding a candidate is adding a file. Nothing here
imports a candidate or calls into one. Each adapter hands back an argv, the
runner launches it as a child process, and the memory figure therefore belongs
to the candidate rather than to the bench.

An adapter that fails to import is not an error either. It becomes a candidate
that cannot run, with the import failure as the reason, so one broken dependency
cannot take the other candidates down with it.

## What it does not do

It does not compare curves to each other. It does not say which candidate is
right. It does not install anything, and it will not guess an input format from
documentation: an adapter with no translation written says so in place of
producing one that has never been executed.

## The means

Python, from the standard library only, running each candidate as a child
process. The bench has to launch foreign programs, time them, read a memory
high-water mark the operating system keeps, and reshape a curve onto a common
grid, and all four are in the standard library on every platform the candidates
target. Nothing is added to the tree that has to be maintained, and no candidate
is easier or harder to reach because of the choice, since none of them is
imported.

This says nothing about the language this project is written in. The bench is a
measuring instrument that has to exist before that decision is made, and it is
deliberately outside whatever the answer turns out to be.
