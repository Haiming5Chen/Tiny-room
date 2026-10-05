# Looking again: before the jaws go down, when they are stopped, and when they miss

**Problem.** The Fetch program of ADR 0032 looks once, when the cart stops at the table. Moved
5 cm 2 s later, as the jaws come over it, the cube was missed in 9 of 9 set-ups. The owner
accepted FR-015 on 4 October 2026: when a grasp misses, open the jaws, look again and reach
once more. Built that way first and measured, it looked again in one set-up of nine: in the
other eight the program had failed before its grasp was checked, a reach that could not
settle - traced, the jaws had come down onto the moved cube, a finger on its top. In the one
it reached, the jaws had pushed the cube 7 cm along the table and onto its side before
closing on nothing, and the second look found it beyond the arm's reach. Looking again after
the jaws have touched the cube comes too late.

**Does an existing simulator solve it? Can we wrap it?** What a program does when the world
has changed under it is the program's, not the simulator's. Pick cells check before they
commit and retry a failed pick a bounded number of times; the camera of ADR 0032 is what is
wrapped.

**Unique contribution.** At a stop where the program looked:
- *Before the jaws go down.* An aimed pose that reaches for the object itself - its point
  within 2 cm of where the object was planned (`REACHING`) - takes one more picture before it
  moves. If the object is more than 1 cm from where the look saw it (`MOVED`), or not found -
  a finger over it hides it - the program looks again before touching it.
- *When a reach is stopped.* A pose reaching for the object that cannot settle - the jaws came
  down on something - looks again instead of failing.
- *When the jaws hold nothing.* A grasp check that fails looks again, the jaws first opened:
  the action just before the check, run backwards as long.
- *Looking again* is going back to the stop's approach as ADR 0031 goes back to a stop: the
  pose the machine drove in (the Fetch program's `ready`, where the jaws hide nothing from
  the camera), the drive to the stop (already there), the look, and on. Once per run
  (`REGRASPS`, `Runner(regrasps=)`, `sweep --regrasps`), counted in `Run.regrasped` and in the
  disturbance report's "Looked again"; the runner says why ("Moved since the look", "Blocked
  reaching down", "Nothing held").

**Blueprint and builder.** Programs are unchanged data; looking again is the runner's, as
going back is. A program that does not look never looks again.

**Result.** Fetch, arm on a cart, the disturbance sweep on its nine set-ups again
(docs/sweeps/2026-10-04-fetch-mobile-manipulator-disturbed-looking-again.md):

| Disturbance | looking once (ADR 0032) | looking again | looked again in |
| --- | --- | --- | --- |
| none | 9 of 9 | 9 of 9 | none |
| shoved 4 N s at the table | 9 of 9 | 9 of 9 | none |
| shoved 6 N s at the table | 9 of 9 | 9 of 9 | none |
| cube moved 3 cm sideways | 9 of 9 | 9 of 9 | none |
| cube moved 5 cm sideways | 9 of 9 | 9 of 9 | none |
| cube moved 5 cm sideways, 2 s later | none | **9 of 9**, last goal +2.6 s | 9 |

In all nine the second look found the cube within 1 mm of exactly where it had been put: the
jaws had not touched it. Traced in two of them, the picture before the jaws went down had found
it gone from under them - moved under a finger, which hid it - and the jaws went back. Where
nothing moved after the look, nothing changed: the same results, the same median times and
pushes as ADR 0032 (the extra picture costs no simulated time).

Checked in `tests/test_look_again.py` (5): moved after the look, the cube is seen before the
jaws reach down and they never go down where it had been; a reach that is stopped looks again,
and is not tried a third time; a missed grasp opens the jaws, looks again and reaches where the
cube now is; only once, never without a look, and `regrasps` cannot be negative; and, in full
physics, the cube moved 5 cm 2 s after the cart stopped is fetched. `tests/test_look.py` now
counts the picture before the jaws go down.

**Boundaries.** Once per run: a cube moved again after the second look is missed. The check
before reaching down is one picture, not three. A cube moved while the jaws are already going
down is found only after they stop or miss, and may have been knocked; one knocked beyond
the arm's reach from its stop is seen but not fetched (FR-016). The 2 cm and 1 cm thresholds
are chosen, not measured.
