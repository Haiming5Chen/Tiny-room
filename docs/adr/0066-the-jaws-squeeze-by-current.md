# The jaws squeeze by current: a squeeze is a setting in newtons

**Problem.** The kit jaws are position servos, and how hard they squeeze was a by-product: the
position error times the gain when the closing ramp ends past the part (ADR 0042). A program had no
way to say how hard to hold. Measured on the Fetch as designed, its 1 s close leaves the jaws pressing
the cube with less than 6 N at each pad's centre and more than 4 (a cap at 6 or 8 N changes nothing in
the run, at 4 N a little); a close held longer presses with all the motor has, 0.6 N m. FR-037, from
the weekly reading of 2 November (fifth in its ranking), asked for the squeeze as a setting.

**Does an existing simulator solve it? Can we wrap it?** The servo does: a ROBOTIS X-series servo in
current-based position control (Operating Mode 5) runs its position loop with the current capped at
its Goal Current (address 102), at most its Current Limit (ROBOTIS e-Manual, XH430-W350); the torque a
current makes is taken from the datasheet's stall point, 3.4 N m at 1.3 A, as ADR 0048 reads it. The
kit's joint control is the project's own controller, so the cap is a setting there; MuJoCo's actuator
force range is the motor's, compiled once, and stays so.

**Unique contribution.**
- *Goal Current* (`control/keyboard.py`, `limits`; `control/mujoco_keyboard.py`, `squeeze`): a joint
  action's jaws push with at most so many newtons square to each pad at its centre - each jaw's torque
  capped at the force times its lever, the moment arm about its joint of a push through the pad's
  centre (`pad_lever`; 52.5 mm for the kit gripper). It holds until an action on those jaws sets
  another; 0 gives them their motors' full torque back.
- *In a program* (`programming/program.py`, `programming/execution.py`): an action block's
  `secondary` is its jaws' squeeze, 0 to 100 N; the Program editor's action form asks for it and the
  block says "squeeze 7 N". `tool_motion.squeezed` closes a program's jaws as a servo in current mode is
  closed: each close held until the jaws' target is fully closed (1.4 s), with the squeeze. Programs
  saved before keep their blocks and run as they did: a squeeze of 0 is the motors' full torque.
- *What the jaws feel* (ADR 0048): holding, Present Current reads its Goal Current, as the servo's.
- *In the window*: What's new's "A squeeze set in newtons" runs the Fetch with its jaws at 7 N.

**Blueprint and builder.** Untouched: the gripper, its motors and their limits are as designed; a
squeeze is the program's, not the design's.

**Result.**
- Closed on a fixed box at their pads' centres, the jaws set to 1, 2, 4 and 6 N push with 0.98, 1.95,
  3.97 and 5.99 N; Present Current within a count of its Goal Current (7, 15, 30, 45 counts).
- A squeeze is a torque: a box reaching along most of the pads is touched first at its outer edge,
  15 mm past their centres, and pushed with 52.5 / 67.5 of the setting (3.14 N for 4 N) - where a part
  sits along a rotary jaw sets how hard it is held.
- The Fetch as designed, closed fully at 7 N: every goal met, the cube in the bin at 37.6 s (36.9 s
  as it is); the grip's friction in use at most 60 % while it carries the cube (80 %), its median 36 %
  (38 %); the force from the machine on the cube 7.0 N (3.4 N, as ADR 0040 measures it), the bin's
  peak 0.58 N (0.74 N). At 2 N, on the program's own 1 s close, the grip reached its friction's edge
  for a moment and still delivered.
- The share of the grip's friction in use hardly moves with the squeeze: closed fully at 7, 8, 9 and
  10 N its median while carried is 36, 37, 37 and 32 %, its peak 60, 52, 61 and 51 %. Carried at 7 N,
  the pads' contacts are square to the pads (within 0.2 deg) and the cube is pressed against the palm
  stop as well (2.8 N), the pull towards the palm OPEN LW-028 found; why the share does not fall is
  not measured here. FR-037's default - the least squeeze that keeps the grip's use at half - is not
  reached by squeezing.
- Not adopted for the Fetch: its program, its sweeps and every result before keep the ramp's squeeze.
  The side-by-side FR-037 asks for - the 71 tuning set-ups, then 59 held-out draws (ADR 0049) - is not
  made (OPEN LW-041).

Held by `tests/test_grip_current.py` (6): an action block's squeeze reaching the controller and an
action without one giving the jaws their full torque back; the four squeezes on the fixed box, the
lever and the registers; the box reaching past the pads' centres pushed less, and no squeeze the full
0.6 N m. A window test in `tests/test_whats_new.py` runs the Fetch at 7 N. Suites on MuJoCo 3.10.0:
1140 passed with a display, 1078 headless.

**Boundaries.** The torque per amp is a line through the stall point, which the datasheet's curve
bends; the cap is exact, with no current noise, ripple or thermal derating. A squeeze is in newtons at
a pad's centre only. The kit jaws' Profile Velocity is their ramp, 30 deg/s, as before. The Fetch's own
program does not squeeze by current, and how its results would move if it did is not measured beyond
its one run as designed.
