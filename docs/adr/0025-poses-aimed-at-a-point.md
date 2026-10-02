# Poses aimed at a point: where the tool got to, checked

**Problem.** A program's arm poses are joint angles, solved when the program is planned for
the machine as it then stood. A machine whose base moves under its arm puts its tool
somewhere else. Repeating Fetch with variations (ADR 0024) found it: with 0.5 kg on its
deck behind the arm the cart rides on its rear caster, 5 degrees off the stance the program
was solved for, so the jaws met the cube 28 mm from where they were aimed, and as the arm
lifted the cart rocked onto its front caster; the cube ended 12 mm short of the field's 5 cm
line until the cart rocked back on the way to the bin - lifted at 23.7 s instead of 16.2
(OPEN LW-016). Even as designed the base stops anywhere within 1 cm of its mark, and every
pose taken at a stop settled 10 to 12 mm from its point.

**Does an existing simulator solve it? Can we wrap it?** Robot software executes a goal in
the task space from the robot's current state: MoveIt plans from the current robot state,
task-space controllers servo the tool, visual servoing closes the loop on the tool's
observed error. There is nothing to wrap: the solver is the project's own (ADR 0016). What
the program lacked was the point a pose was for.

**Unique contribution.**
- *A pose can say what it was aimed at:* the point in the field its tool was solved for
  (program data, version 2, optional; a taught pose has none and runs as before).
- *The runner checks and corrects.* Given an aim, it moves the joints to the pose's angles as
  before, then asks where the tool got to: within 5 mm, the pose is done; otherwise the pose
  is solved again for the machine as it now stands - its base rocked or stopped off its mark
  - holding the tool pointed as the pose points it, and the joints move there; at most twice
  (`programming/program.py`, `ToolMotion.aim`). A correction that cannot settle keeps what the
  joints reached; a point out of reach leaves the pose as it was.
- *The measurement is ideal* - the simulator's tool position and base pose. A real machine
  needs its base's attitude and position (an IMU, odometry or localisation) or a camera on its
  tool to do the same; the program data would not change.
- The Fetch template aims every pose taken at a stop (at, lift, over, down, retract); the
  pose taken at the start, before the drive, is not aimed. The app's runs, the sweeps and the
  tests hand the runner the arm's aim. The program editor marks an aimed pose.

**Blueprint and builder.** Programs saved before run as they did: their poses carry no point.
The pick-and-place template's arm stands on a pedestal and its poses are not aimed.

**Result.** As designed, each aimed pose settled about 1 cm off its point - the base stopped
1.0 cm short of its mark at the table and 0.9 cm off at the bin - and one correction brought
the tool within 1 to 3 mm; six corrections put the cube in the bin at 34.0 s instead of
32.5. Loaded with 0.5 kg behind the arm, the jaws meet the cube within 3.3 mm instead of
28 and the lift leaves it 11.5 mm over the 5 cm line: lifted at 18.2 s instead of 23.7, in
the bin at 35.5 s. The same 20 variations as ADR 0024: every goal met in every run, lifted
at 16.4 to 18.2 s (15.9 to 23.7 before), in the bin at 33.3 to 35.5 s (31.9 to 33.6);
`docs/sweeps/` has both. Checks in `tests/test_aimed_poses.py` (6): an aimed pose as data; the
runner asking, correcting, and stopping after two; a correction that cannot settle not failing
the program; a pose without a point or a runner without an aim unchanged; the arm aiming a
pose from where its machine stands; the loaded cart lifting the cube clear.

**Boundaries.** Sensing is ideal. A pose is checked after it settles, not tracked while it
moves, so the tool can still be off while the arm travels; two corrections at most; poses
taken while the base drives are not corrected. Aiming does not make the cart stop rocking:
a machine that rocks between its casters as its arm moves is still worth redesigning.
