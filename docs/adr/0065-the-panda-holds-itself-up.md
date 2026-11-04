# The Panda holds itself up, and its hand squeezes as the real one does

**Problem.** Measured in the factory cell (ADR 0056, OPEN LW-036), the Panda's tool stopped 3.3 to
4.5 mm short of every point it was sent to and 3.9 to 5.2 mm low, and its hand squeezed a 32 mm part
with 1.6 N; carried, the part moved 3.3 mm along the fingers, and the parts landed 2.2 to 6.0 mm out
along the table and 1.1 to 2.5 mm short across it. Menagerie's Panda is the arm's mechanics with a
position servo on each joint. The real arm's controller also holds it against gravity - Franka's
joint torques come on top of the torque that carries the arm's weight - so it reaches a commanded
pose instead of sagging under it; and Menagerie's hand is a 100 N/m spring on the fingers' tendon,
where the Franka Hand's datasheet gives 70 N of continuous squeeze, 140 N at most, its fingers moving
at 50 mm/s each. The Panda in every Real experiment - the Joint lab, teaching positions, the cell -
sagged, and what it held moved in its hand. Adopted on 2 November, when the owner left such calls
to the weekly reading's ranking, after its ranked items.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo does most of it. A body's `gravcomp`
applies an upward force of its weight at its centre of mass, as a controller's gravity term would;
an actuator's `forcerange` caps what it can push with; a geom's `solref` and `solimp` set how stiff
its contacts are, and its `solmix` how much of a contact's stiffness is its own (MuJoCo's
documentation, body/gravcomp and geom/solmix). They are set on the robot's own model as it is loaded
(`mjSpec`), not written beside it. How fast the hand moves is its controller's, and so the adapter's.

**Unique contribution.**
- *What a robot's own controller does* (`assets/robot_models.py`, `CONTROLLERS`): per registered
  robot, whether its controller holds it against gravity, and its hand's actuator, the squeeze on
  each finger, the fingers' bodies and their speed. The Panda: held, 70 N, 50 mm/s.
- *Applied as the robot is loaded* (`physics/mujoco_backend.py`, `held`): every link of the robot
  gets gravity compensation - on a fixed base only: on a cart MuJoCo's compensation would carry the
  cart's free joint too, which no arm's controller does; the hand's servo is made a hundred times as
  stiff on its tendon and limited to twice the squeeze, each finger taking half the tendon's force;
  the fingers' contacts get an imported gripper's stiffest settings (ADR 0047), weighted to be the
  contact's own. The first try left that weight equal: MuJoCo averaged each finger's contact with the
  part's softer default, and the 70 N squeeze still let the part slide 2 mm along the fingers as it
  was carried - every part landed 1.1 to 2.8 mm out along the table, all to one side.
- *At its hand's speed* (`MujocoBackend.step`): the hand's control follows its command no faster
  than moves each finger 50 mm/s, as the hand's own controller does; the stiffer servo had slammed
  the fingers shut at 2.9 m/s (Menagerie's at 0.26 m/s). Damping the fingers' joints for the same speed
  made them bounce on the part at up to 104 N: MuJoCo integrates a joint's damping after it has
  solved the contacts. The squeeze now builds over 0.27 s once the fingers touch.

**Blueprint and builder.** Untouched: the Panda is the same model in the same designs; how its
controller drives it is the robot's own data, in one table.

**Result** (`docs/sweeps/2026-10-26-factory-process-window.md`, the same 38 runs again, 228 parts):
- The tool now stops within 0.47 mm of every point of a cycle, where it stopped 5.7 to 6.7 mm off;
  the fingers close at 50 mm/s and each presses the part with 70.0 N all through the carry, sunk
  0.1 mm into its faces; the part is let go 0.5 mm from where the hand took it, at most 1 mm off on
  the way, where it was 3.3 mm off.
- Fed at the centre, six small blocks and six tall ones land 0.28 to 0.78 mm out along the table and
  within 0.32 mm across, worst 0.82 mm, where they landed 2.4 to 5.0 mm out and 1.4 to 2.3 mm short:
  Cpk along x 14.1 and 16.8, from 1.25 and 1.08. Fed ±2 mm and ±5 deg off, Cpk along x 12.0 (9.7 to
  14.3) for small blocks and 20.1 (16.2 to 23.9) for tall ones, from 1.27 and 1.04; fed ±5 mm and ±15
  deg off, 10.2 (8.2 to 12.1) and 16.4 (13.3 to 19.5), from 0.90 and 0.85. Every part lands within its
  room, as before, and within 1.05 mm of its slot; the tightest zone every part held is ±1 mm (±2 mm
  for small blocks fed ±5 mm off), from ±5 to ±10 mm; none is left turned more than 1.8 deg. A part
  takes 12.0 to 13.95 s, 12.4 s on average, as before.
- With the fingers' speed not limited, parts fed ±5 mm off spread three times as far along the table
  (0.58 mm, against 0.19, one standard deviation): fingers shut at 2.9 m/s knock the part.
- What's new's "The Panda holds itself up" runs the cell with tall blocks: under it, the worst part
  under a millimetre off.

Held by `tests/test_panda_held.py` (2): every link of the Panda held up on a fixed base and none on a
cart, the hand's force range and the fingers' contacts; and one cycle of the cell - the tool within
0.6 mm of each point, the fingers closing at 50 mm/s, each finger at 70 N through the carry, within
0.2 mm of the part's faces, the part still in the hand and landing within a millimetre of its slot.
`tests/test_robot_assets.py` holds the arm's joints as Menagerie gives them; `tests/test_process_window.py`
and `tests/test_straight_descent.py` hold the parts within a millimetre or so of their slots and the
tool within a millimetre of its vertical. Suites on MuJoCo 3.10.0: 1133 passed with a display, 1072 headless.

**Boundaries.** The compensation is ideal: the model's own masses, every step, where Franka's
controller uses its identified model; a held part's weight is not compensated. A Panda on a cart is
not held up and sags as before. The squeeze is a force limit on a stiff servo, reached 0.27 s after
the fingers touch: the real hand's force control is not modelled. Only the Panda is registered with
its controller. (An imported robot's gripper is not averaged: its jaws take priority, ADR 0047;
OPEN LW-040, filed here, was checked and closed.) The cell's spread is the simulation's: the real arm repeats to ±0.1 mm (ISO 9283).
