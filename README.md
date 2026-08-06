# hallraum

Established room acoustics tools compute geometrically, which is justified above the Schroeder frequency and physically wrong below it where individual modes dominate, and that is the range deciding whether a room booms. Wave-based methods solve it but live in institute codes. Missing is a packaged tool taking room geometry plus wall impedances to a transfer function below roughly 300 Hz behind an interface that presupposes no numerics degree. The open landscape here was surveyed less thoroughly than for the sibling boards and individual FDTD implementations exist, so the first task is a proper survey: if a usable open solver is found, this board becomes the boundary conditions and the interface around it. Memory scales with the cube of frequency.

Planning happens on the issue tracker first. Every decision that shapes
the architecture is written down there with its reasons before the code
that depends on it exists.

See [NOTICE.md](NOTICE.md) for the intended-use notice.
