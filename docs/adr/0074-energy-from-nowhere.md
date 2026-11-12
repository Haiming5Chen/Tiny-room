# Energy from nowhere: every run checks that no contact gave back more than it took

**Problem.** Every result here assumes that MuJoCo behaved as physics does, and nothing checked
it during a run. The weekly reading of 9 November brought an audit of a simulated benchmark in
which 12 of 100 episodes were the engine's doing - geometry 1 to 2 cm apart reported 2 cm deep,
parts flung at metres a second, the policy blamed for each ([arXiv 2610.41857](https://arxiv.org/abs/2610.41857);
FR-040, first in that reading's ranking). Nothing in this project had looked.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo reports each contact's force and
its constraint Jacobian (`efc_force`, `mj_mulJacVec`); it does not say whether a contact made
energy. The audit's tool watches for an object that starts moving faster than its contact forces
explain - in MuJoCo the soft contact's force includes the push of its own penetration, so a part
pushed out of a table is explained by its contact force: the check has to be about energy. It is
built here from MuJoCo's own numbers.

**Unique contribution.**
- *A contact can only give back what it took.* A contact is a spring and a damper: as two bodies
  press into each other it takes energy, as they part it gives some back. From the moment they
  touch, the work it has done on them can only be zero or less - unless the engine made energy.
  `MujocoBackend.contact_work` reads it each step for each pair of touching bodies: each contact
  row's force times how fast its two points move apart along it, at the step's mean speeds. (At
  the step's new speeds the semi-implicit step overstates a force's work by F²dt²/2m - 6.3 of the
  40 mJ a block dropped 5 cm gives a slab - and on the Push field that drifted to 6.6 times the
  line on a crate the cart pushes for 10 s; at the mean speeds the contacts' work is the bodies'
  own energy change, to 1 %.) It reads the step and changes nothing (tested, to the last bit).
  Driven or not does not matter: a jaw's or a roller's motor works on the bodies, not on the
  contact between them.
- *The watch* (`inventory/artifacts.py`) adds it up for each touch and flags one whose contacts
  gave back more than lifting the lighter body 2 mm takes (`GIVE`); the lighter is weighed as
  what a push on it sets moving (`moving_mass`): the whole cart for one of its wheels.
- *Everywhere a run is:* every sweep run (`Run.physics`) and its report ("Physics check"); in the
  window the drive panel's line under "touching", live, and the run's report after Stop. What's
  new: "Energy from nowhere" drives the kit cart at the Curb run's curbs.
- *In the evidence* (ADR 0073): a `physics` claim measures the check's two controls anywhere;
  the `curb` claim records the energy its climb is given, as a flaw.

**Blueprint and builder.** Untouched: the check only reads.

**Result.**

The controls - a 5 cm block over a fixed slab, let go:

| Started | The slab's contact | Flagged |
| --- | --- | --- |
| 5 cm above | took the 40 mJ it fell, the block's own energy change to 1 %; gave back none | no |
| 1 cm above | took 8.0 mJ; gave back none | no |
| resting on it | gave back none | no |
| 0.5 mm inside | pushed it out with as much as lifting it 0.49 mm takes | no |
| 2, 3, 5, 10 mm inside | 1.99, 2.99, 4.99, 9.99 mm's worth | from 2 mm |
| a box 3 mm inside the box under it | 2.47 mJ, lifting the upper box the 3 mm it was set in (5 %) | yes |

The fields, each headline claim's run (docs/EVIDENCE.md) and the others - the most any touch gave
back beyond what it took, as a share of the 2 mm line:

| Run (the claim it holds) | Touches | The most any touch gave back beyond what it took, as a lift of the lighter body | Flagged |
| --- | --- | --- | --- |
| Sprint, kit cart (`sprint`) | 2,322 | 0.02 mm | no |
| Curb run, kit cart (`curb`) | 1,208 | 4.6 mm - a swivel caster's wheel at the 10 mm curb | yes |
| Ramps, kit cart | 572 | 0.05 mm | no |
| Push, kit cart | 1,608 | 0.06 mm | no |
| Doorway, kit cart (`doorway`) | 901 | 0.00 mm | no |
| Tilt table, arm cart (`tilt`) | 163 | 0.04 mm | no |
| Tilt table, cart alone (`tilt-cart`) | 13 | 0 | no |
| Pick and place, arm lab (`pick-place`) | 203 | 0.005 mm | no |
| Fetch (`fetch`) | 596 | 1.3 mm - the palm stop, holding the cube | no |
| Fetch, cube moved 2 s after the look (`fetch-felt`) | 590 | 1.7 mm | no |
| Fetch, cart shoved 6 N s at the table | 818 | 0 | no |
| Roller conveyor (`conveyor`) | 63 | 0.03 mm | no |
| Real's cell, two parts by hand (`cell`) | 84 | 2.6 mm - the Panda's fingers as they close on a part; 0.7 mm at 1 ms steps | yes |
| Real's cell, fed by the conveyor | 250 | 3.8 mm - a finger while it holds a part | yes |

What it found. **On the Curb run**, driven at the 10 mm curb, the kit cart pushes a swivel
caster's wheel - a cylinder - against the curb's edge, and from 3.0 to 7.7 s their contact gives
the cart 78 mJ more than it took: as much as lifting the 1.74 kg cart 4.6 mm, nearly half of what
lifting it over the 10 mm curb takes (171 mJ). It climbs over at 10.4 s. One setting changed at a
time:

| Changed | The caster's contact with the curb | 10 mm curb cleared at |
| --- | --- | --- |
| nothing | 78 mJ from nowhere, 4.6 mm's worth | 10.4 s |
| steps of 1 ms | 66 mJ, 3.9 mm's worth | 10.9 s |
| multiccd on (several points between cylinder and box) | clean | 11.4 s |
| elliptic friction cones | clean | not in 13 s |
| no noslip pass | clean | not in 13 s |

The energy comes from the single contact point MuJoCo finds between a cylinder and a box's edge
with multiccd off (ADR 0027), with the noslip pass on (ADR 0017); the cart climbs without it a
second later. The 18 mm curb of OPEN LW-026, given 25 s, is clean: cleared at 11.6 s on all four
wheels - and with multiccd on it stalls for good, as on the owner's Intel Mac. OPEN LW-047.

**In Real's cell** the Panda's fingers pass the line as they close on a part: 2.6 mm's worth of
lifting the part at 2 ms steps (about the same with no noslip pass), 0.7 mm at 1 ms - a contact that
comes on within one step, the step's doing more than the contact's. Fed by the conveyor, a finger
holding a part gives back 3.8 mm's worth between 17.8 and 23.8 s; not traced further.

**In Real's cell** the Panda's fingers pass the line as they close on a part: 2.6 mm's worth of
lifting the part at 2 ms steps (about the same with no noslip pass), 0.7 mm at 1 ms - a contact that
comes on within one step, the step's doing more than the contact's. Fed by the conveyor, a finger
holding a part gives back 3.8 mm's worth between 17.8 and 23.8 s; not traced further.

**In the Fetch** the jaws' contacts with the cube give back a little more than they took. As
designed, the palm stop's, while the jaws hold the cube against it: 0.21 mJ, as much as lifting the
16 g cube 1.3 mm (1.5 mm at 1 ms steps) - under the line. With no noslip pass it is gone, and the
cube slips out of the jaws, as ADR 0017 found; a box squeezed against a wall by a servo jaw alone
gives back nothing, with noslip or without, either integrator, either cone. Over the Fetch's 71 tuning set-ups and the 59 draws ADR 0049 held out, every goal is met in all 130; in 21 (16 %; 10 to 24 % at 95 %) a jaw's contact with the cube passes the line - in 15 as the jaws close on it, mostly the left pad (a contact that comes on with the pad already in the cube: a step's doing), in 6 while they hold it - by as much as 1.8 mJ, 11.5 mm's worth; the median set-up's most is 0.26 mm's worth.

**With elliptic friction cones** (OPEN LW-039) the jaws' pads give the cube 1.9 and 1.6 mJ they
never took - 12 and 10 mm's worth - while it is carried: a measured reason, beside the 16 tests
they fail, not to switch for the slope's creep alone.

The check costs 3.8 s of a 47 s Fetch run. Held by `tests/test_artifacts.py` (8: the bookkeeping,
the controls against the bodies' energy, two boxes, reading changes nothing, the curb), a window
test in `tests/test_whats_new.py`, and the evidence's `physics` claim. Suites: 1188 pass with a display, 1120 headless.

**Boundaries.** The line is judgment: a gain under it is not flagged, and the reports say the most
any touch came to. The jaws' contacts in the Fetch pass it in some set-ups; what they give is under
a millijoule, and whether it is the engine's or the reading's own error at a contact that comes and
goes from one step to the next is not separated here. A touch is a pair
of bodies touching without a break: one that parts and touches again starts afresh, so energy
made a little at a time across many short touches would be missed. Joint limits, welds and other
constraints are not watched, only contacts. It says that a contact made energy, not what the
energy did: the curb's 78 mJ is not shown to be what got the cart over (with multiccd on it gets
over anyway). Nothing is mended here: whether to turn multiccd back on - ADR 0027 turned it off for
the wheels' rolling loss - is the owner's call (OPEN LW-047).
