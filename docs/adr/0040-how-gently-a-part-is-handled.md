# How gently: the forces on a handled part, its lean and its fall, beside success

**Problem.** A field's goals say where a part ended, not how it got there. A Fetch that pressed
the cube into the table, or let it fall into the bin, meets its goals as well as one that set
it down; in a lab the cube is a vial. Nothing measured how a part was handled: no run recorded
a force on the cube, how far it leaned or how far it fell. FR-020, accepted by the owner on 9
October 2026.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo's contact solver finds every
contact force each step and gives it back (`mj_contactForce`); wrapped through the adapter. The
weekly reading of 5 October named the question (*ManiPhysicsBench*, arXiv 2610.02802; *Is
Success All You Need?*, arXiv 2610.01351 - by their titles).

**Unique contribution.**
- *Forces on a body, by what touches it.* `MujocoBackend.contact_forces(body)`: for each
  contact on it, the other body and the force on this one, in the world, as the solver applied
  it.
- *A part watched through every run.* `inventory/handling.py`: the parts a field's goals carry
  (the Fetch cube) are followed through each run (`Run.handled`): for each thing that touched
  one - the machine, the table, the bin - the hardest push on it from any one of its bodies (a
  jaw, the table, the bin's floor; two jaws squeezing from either side cancel in a sum, and
  each still presses), in any one step and averaged over 50 ms, as a force sensor reading 20
  times a second would show it; the most it leaned from how it stood; and how far it fell after
  the machine last touched it. The varied sweep's report adds a table of these (median, least,
  most), the disturbance report a row for each disturbance.
- *The instrument's own question.* A soft contact's force in one step depends on the step, so
  a run can be made at another timestep (`sweep.run(timestep=)`, the settling time kept in
  seconds) and the two compared.

**Blueprint and builder.** Untouched.

**Result.**

The instrument: the forces the table puts on the resting cube add up to its weight, 0.159 N,
within 0.01 % (the test asks 1 %).

Halving the step, from 2 ms to 1 ms, as designed and in the two cases below:

| | 2 ms | 1 ms |
| --- | --- | --- |
| squeeze, in a step / over 50 ms | 5.12 / 4.67 N | 4.90 / 4.51 N |
| the bin's landing, in a step / over 50 ms | 1.99 / 0.561 N | 1.75 / 0.564 N |
| blind, the table pressed, over 50 ms | 4.79 N | 4.78 N |
| looking, cube moved, squeeze over 50 ms | 3.87 N | 3.78 N |
| as designed: leaned / fell when let go | 16 deg / 6.8 cm | 13 deg / 4.2 cm |

The force in a step moved by up to 12 % and the force over 50 ms by up to 4 %, so both are
reported. The lean and the fall moved more: they follow the cube sliding off the opening pads,
a few milliseconds earlier or later.

As designed and over 59 drawn set-ups, every one meeting every goal
([report](../sweeps/2026-10-09-fetch-handling-59.md)): the jaws squeeze the cube at 4.8 N over
50 ms (median; 3.7 to 6.7) - thirty times its weight; they let it go 5.8 cm above the bin's floor
(3.1 to 7.0), and it lands at 1.9 N in a step, 0.57 N over 50 ms, leaning 9 degrees (median).
Hidden in those successes: in 4 of the 59 drawn set-ups (2 to 17 %) the jaws pressed the cube
into the table, the table pushing back at 0.6 to 2.0 N over 50 ms, and in 2 it leaned more than
20 degrees; carrying 0.5 kg, a chosen corner, it was pressed at 2.3 N and tipped over onto its
side (101 degrees at most) before coming to rest in the bin (OPEN LW-024, LW-025).

The rough case, the cube moved 5 cm as the cart stops, on the nine set-ups
([blind](../sweeps/2026-10-09-fetch-blind-moved-handling.md),
[looking](../sweeps/2026-10-09-fetch-mobile-manipulator-disturbed-handling.md)): blind, a jaw
came down on the cube and pressed it into the table at 5.1 N over 50 ms (median; 32 times its
weight), once knocking it over; looking, the table only ever carried it. From the machine's side
the two read alike, a press and a squeeze of 4 to 5 N, so it is the table's push that tells them
apart. Under every disturbance, looking, the squeeze was 3.5 to 4.7 N; moved 2 s after the look,
a jaw that came down on the moved cube pressed it into the table at up to 3.1 N before rising
off it (ADR 0037); the camera faults left it untouched.

Held by `tests/test_handling.py` (5): what touched the part named as a report names it; the
bookkeeping on made-up steps (a squeeze counted, not cancelled; a one-step knock is a
twenty-fifth of itself over 50 ms; the lean; the fall); runs summed up as a report shows them;
the resting cube weighs what it weighs; and the jaws brought down on the moved cube press it
into the table at thirty times its weight, where the table only carries a fetched one.

**Boundaries.** The forces are MuJoCo's soft contacts: the force in a step moved by up to 12 %
when the step was halved, the 50 ms force by up to 4 %; the lean and the fall, which come from how the
cube slides off the opening pads, moved more. Nothing here says what a part can bear: no
fragility is sourced, and the kit gripper's force rating is not published, so the report
measures and does not judge. Only the parts the goals carry are watched.
