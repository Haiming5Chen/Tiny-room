# A grasp the program feels: the jaw servos' registers, not the simulator's contacts

**Problem.** Programs decide that they hold something - the Fetch program's grasp check, which
lets it carry on or makes it look again (ADR 0016, 0033) - and they read it from the simulator:
two jaw pads touching the same movable part (`Observations.grasped`). No real robot has that
reading. A sweep could show a program working that could not work on the bench, and nothing
said how much it leaned on knowing what a robot cannot know.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo gives the contacts and the
actuators' forces; what a servo reports is the servo maker's. A ROBOTIS X-series servo's
control table has Present Position (4096 pulses a turn), Present Velocity (0.229 rev/min a
count), Present Current (2.69 mA a count) and a Moving flag set above a Moving Threshold (10
counts by default); grippers are run in its current-based position control (ROBOTIS e-Manual,
XH430-W350, read 20 Oct 2026). A gripper that judges its grasp from its motor's current and
position, without a force or tactile sensor, is what [MIM-VLA](https://arxiv.org/abs/2610.08425)
builds on (the weekly reading of 19 Oct, FR-026).

**Unique contribution.**
- *The jaws read as servos* (`control/feel.py`): each kit jaw is read as an XH430-W350 at 12 V
  in current-based position control, its current limit at the 0.6 N m the kit gives a jaw - 85
  counts. Its torque becomes current by the datasheet's stall point, 3.4 N m at 1.3 A (2.6 N m
  an ampere), its angle, goal and speed become pulses and counts, each rounded as the register
  counts them.
- *Holding, felt* (`holding`): every jaw still (the Moving flag clear), stopped at least 2
  pulses short of where it was sent, and pushing towards it with at least 6 counts of current
  (16 mA) - what a kit jaw draws to move itself at full speed. A jaw just starting to move is
  still and behind its goal for some 15 ms at 3 or 4 counts; closed on nothing it reaches its
  goal and draws none.
- *Programs decide by it* (`programming/execution.held_now`): in sweeps, the benchmark and the
  app, a program whose gripper is a kit module takes as held what its grasp blocks name when
  the jaws feel a hold, and nothing otherwise; a registered model's own gripper keeps the
  contacts. The contacts stay the judge: each grasp check records what was felt and what was
  so (`Run.felt`), and sweep reports count them.

**Blueprint and builder.** Untouched: no new block, no new program data; a grasp block now
passes on what the jaws feel.

**Result.** Over the Fetch field's 71 set-ups (the design as designed, each range's ends and 59
drawn, seed 1), the program feeling its grasps: every goal met in 71 of 71, as with the contacts
(ADR 0042), and at each of the 71 grasp checks the jaws felt a hold where the contacts showed one -
none that was not there, none missed. The program passes its check a little later - the contacts
are there at the touch, the servos feel the hold once the jaws have stopped: the cube lifted 54 ms
later (median; 16 to 200 ms), in the bin 62 ms later (-54 to +222 ms); the handling within its
spread (squeeze over 50 ms 3.66 N, 3.22 to 5.00, against 3.96 N, 3.35 to 4.98; fall 0.35 cm
against 0.31; the bin's push 0.51 N in a step against 0.52). A jaw holding the cube draws 11 to
25 counts of current (28 carrying 0.5 kg); closing on air, at most 6 while it moves, and 3 or 4
for some 15 ms, still, as it starts. Disturbed - the 9 set-ups under each of the field's 7 disturbances - the program ended as it
did with the contacts (ADR 0042's sweep): every goal met in the same 54 runs, none where the
camera froze or went dark (the program stops before it grasps), the cube moved 2 s later looked
for again in all 9; its 54 grasp checks felt a hold where the contacts showed one, every time. No
check in these sweeps met empty jaws; the test that takes the cube from between the closing jaws
feels nothing held, and the program looks again and fetches it. The sweeps' reports: `docs/sweeps/2026-10-22-fetch-feel-71.md` and
`docs/sweeps/2026-10-22-fetch-feel-disturbed-9.md`.

Held by `tests/test_feel.py` (7): the registers' counts from the datasheet; holding needs both
jaws still, short and pushing; jaws closing on nothing feel nothing at any step; the Fetch
program feels the cube where the contacts say it is held, as designed and carrying 0.5 kg,
passing its check 52 ms later than the contacts would; with the cube taken from between the
jaws as they close, they feel nothing, the program looks again and fetches it; the report's
count, read back from JSON. Suites on MuJoCo 3.10.0: 1044 passed with a display, 992 headless.

**Boundaries.** The kit gripper is not a ROBOTIS gripper: reading its jaws as XH430s is an
assumption, stated, and the torque-to-current line through the stall point ignores the
no-load current the datasheet does not give and the friction a real servo's current carries.
The registers here are exact apart from their counting; a real servo's current is noisy, and
thresholds this close (6 counts against a hold's 10 to 12) would need checking on one. Feeling
says that the jaws hold something, not what. The arm's own servos are not read: a reach that
meets something still waits for its pose to time out (OPEN LW-029).
