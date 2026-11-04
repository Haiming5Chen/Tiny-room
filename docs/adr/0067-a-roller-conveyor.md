# A roller conveyor carries pallets to a stop

**Problem.** Nothing in Little World moved parts along: the factory's feeder is not simulated - a
production run moves the next part onto the input tray (ADR 0019) - and no field had a conveyor
(FR-007, OPEN LW-005). A belt is a surface that moves, which MuJoCo models from 3.11 on
(`geom/surfacevel`), past the pin (ADR 0027). Powered rollers work on 3.10. But what a roller line
carries must rest on three rollers at any time, and the smallest rollers named are 20 mm across
(Interroll, "Conveyor rollers: planning"): the kit's 25 mm cube and the cell's 32 mm blocks are too
short to ride rollers bare (noted under FR-007, 26 October). The owner left the call to the weekly
reading's ranking (2 November); taken here as an assembly line takes it: the parts ride on pallets.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo turns the rollers - hinges, each
held at one speed - and carries what rests on them by its contact friction. Two of its limits on
3.10 shaped the conveyor, both measured:
- A box laid across cylinders sinks into them: 3.10 has no box-on-cylinder collider of its own and,
  with multiccd off (ADR 0027), its general one gives a single point; a 160 mm pallet sank 4 mm into
  50 mm cylinders, and 10 mm into 20 mm ones, carried at 0.067 m/s, not 0.1. Across capsules -
  MuJoCo's own box-on-capsule collider - it rests on their tops (within 0.1 mm). Little World's
  shapes gain the capsule: a cylinder's radius and straight length, with round ends.
- Rollers as light as a 20 mm aluminium one let a light pallet hop over them (13 mm), carried at
  0.07 m/s with a spread of 0.09 m/s; with eight times that inertia it is carried at the rollers'
  speed, steadily. A 50 mm steel tube 1.5 mm thick has more, and half of it as a solid of its mass.

**Unique contribution.**
- *The capsule* (`core/component.py`, the backend, `construction/docking.py` and `structure.py`):
  a shape of radius and straight length, compiled as MuJoCo's capsule.
- *The conveyor* (`fields/conveyor.py`, standard library): nine 50 mm rollers 55 mm apart, each a
  capsule as heavy as its steel tube (0.185 kg), on a hinge, held at 0.1 m/s at its surface by its
  own velocity servo, whose damping the solver integrates (ADR 0014); a bed under them, out of
  their reach (ADR 0020); side frames beside their ends; side guides and a stop plate 2 mm clear of
  their tops; 160 mm HDPE pallets
  (0.37 kg), each carrying the kit's cube, on HDPE-on-steel friction (ADR 0010).
- *The field* (`fields/__init__.py`, "Roller conveyor"): two pallets set at the conveyor's start
  beside the machine's; its goals, each pallet at rest where the stop and the pallet ahead hold it -
  within 5 mm along, 10 mm across, flat on the rollers - and the first one's cube still on it.
- *In the window*: Test's field list has it; What's new's "A roller conveyor" runs it with the arm on
  its cart beside it.

**Blueprint and builder.** A capsule is a new shape for any Blueprint; the builder's catalog has no
part made of one, and the conveyor is a field's, not a design's. Designs saved before are unchanged.

**Result** (`tests/test_conveyor.py`): the rollers' surfaces held at 0.0992 to 0.1000 m/s under the
pallets' load; both pallets carried at 0.0999 m/s once on their way (within 0.1 %); the first at rest
against the stop 1.56 s after the start, at its place to 0.1 mm, the second queued behind it at 1.76
s, neither rising more than 0.5 mm; the first pallet's cube slid 5 mm forward on it as it stopped, and
stayed on it. With the arm on its cart beside it, a 2 ms step takes 0.5 to 1.0 ms more than on the
Sprint (38 contacts against 16), on the cloud's CPU, under another load.

Held by `tests/test_conveyor.py` (3): three rollers under a pallet and the capsule's shape and
bounds; a box across cylinders sinking and across capsules resting, in MuJoCo itself; and the field
run - speed within 3 %, rest within 1 mm, no climbing, the goals met in order. A window test in
`tests/test_whats_new.py` runs it from What's new. Suites on MuJoCo 3.10.0: 1144 passed with a display, 1081 headless.

**Boundaries.** The factory's feeder still moves its parts by hand (FR-007's cell is not done):
nothing yet picks from the conveyor, releases a pallet past the stop or returns it. Each roller is
its own ideal velocity servo - no shared drive, belt or motor curve; the rollers' ends are rounded,
inside the guides; the speed is fixed. Pallets do not accumulate pressure beyond their friction on
the rollers, measured nowhere against a real line. Held at the stop or in the queue, a pallet shakes
on the rollers slipping under it - up and down at up to 4 cm/s - and what it carries creeps forward:
from 2 to 10 s, the first pallet's cube 6 mm, the second's 31 mm (OPEN LW-042); the test holds the
first 4 s.
