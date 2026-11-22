# A grasp bench: five diagnostic objects on a grid of poses, judged by the object

**Problem.** Grasping was judged only inside whole tasks - the Fetch, the factory cell - so a
weakness showed where a task happened to meet it: a block lying across the jaws was lost on the way to
the bin (OPEN LW-034), and nothing asked which objects and poses a gripper holds. A benchmark of MuJoCo
grasps asked it directly, across robots and objects: one fixed approach, close and lift, five
diagnostic objects, a grid of poses, and a missing output counted as a failure ([arXiv
2611.07651](https://arxiv.org/abs/2611.07651); FR-043, fourth in the weekly reading of 9 November).

**Does an existing simulator solve it? Can we wrap it?** No simulator ships a bench for a user's own
gripper. The runs are the project's own (`sweep.run` through MuJoCo, the arm lab's pick-and-place
template solved for each pose); the intervals are ADR 0028's exact ones.

**Unique contribution.** `inventory/graspbench.py`:
- *Objects*, each a loose wooden part on a bench 18.7 cm up (the arm lab's pickup stand's height): a
  25 mm cube; the kit's 25 x 25 x 40 mm block standing, and lying on its side; a cylinder 25 mm across
  and 40 mm tall, standing; a 60 x 40 x 6 mm plate lying flat (`bench_field(name, pose)`).
- *Poses*: 3 x 3 places 2 cm apart round the bench's middle, each at 0, 30, 60 and 90 deg: 36.
- *Protocol*, the template's (`tool_motion.pick_and_place`): open; 6 cm over the object's top; down to
  its centre, or as little over it as keeps the jaws 5 mm over the bench (`JAWS_CLEAR`, as the Fetch
  sets a part down; the tool at its angle where the arm can, else at any - `lowest`); close for 1 s;
  the grasp check; lift 10 cm; carry 20 cm to the side; hold 2 s. Known pose: the program is solved
  for where the object is.
- *Judged by the object*: held is lifted 8 cm or more and carried 18 cm or more at the end, and
  under 2 mm of slip in the jaws over the last 2 s. A grasp the arm cannot reach or make counts as a
  failure, with its reason. The program goes on as taught whatever its grasp check feels (the
  runner's 'ignore', FR-022), so the outcome is the grip's; what the check felt from the jaws' servos
  (ADR 0048) is reported against it, in a table of four.
- *The jaws' angle*: where the object's x axis (the lying block's and the plate's length) lies from
  the line the jaws close along, 0 to 90 deg, as LW-034 measures it (`skew`). An arm without a wrist
  that turns closes its jaws across the line from its base, so a turn of the object is a turn
  against the jaws.
- `python -m little_world.inventory.graspbench --design arm_lab --jobs 2 --out FILE` writes the report
  and its outcomes as JSON.

**Blueprint and builder.** Untouched: the bench is a field of Blueprint parts, the arm the arm lab as
designed.

**Result** (the arm lab, 180 runs, 6 minutes on two cores; docs/sweeps/2026-11-22-grasp-bench-arm-lab.md):
- Held: the cube 36 of 36 (90 to 100 %), the standing block 36 of 36, the lying block 26 of 36 (55 to
  86 %), the cylinder 0 of 36, the plate 0 of 36. The arm lab turns at its base, shoulder, elbow and
  wrist - no wrist roll - and at the bench's middle its jaws close along a line 74.5 deg from x: the
  four turns lay the object's x axis 74, 44, 14 and 16 deg from it.
- The lying block, OPEN LW-034 on the bench: held 9 of 9 across the jaws (74 deg) and 9 of 9 at 14
  deg; lost 9 of 9 at 16 deg, by its ends - felt held, it turns 40 deg in the jaws as it is carried
  along its length, tips 9 deg and slides out during the hold, onto the floor. At 14 deg it turns 36
  deg on the carry, 30 deg off its length, and stays level. Held, it slips 0.6 to 1.9 mm in the last
  2 s (median 1.4); the cube 0.1 to 0.9, the standing block under 0.2.
- The grasp check felt 85 of the 98 held runs held. It missed 7 of the 9 cubes and 6 of the 9
  standing blocks turned 30 deg (44 deg to the jaws), every one held: closing on their corners, the
  jaws turn them square before the check begins, and at rest the 1 s close leaves each jaw 2 or 3
  pulses short of its goal, pushing with 4 counts of current - under the 6 the feel needs. At turn 0
  (16 deg off square) a cube is felt only while the jaws still turn and press it: from 4.98 to 5.24
  s, the check beginning at 4.99 s (traced; OPEN LW-056, mended in ADR 0078: the template squeezes
  before it checks). The 10 lying blocks lost after the check it felt held - they were.
- The cylinder is never lifted. With multiccd off (ADR 0027) each pad touches it at one point - one at
  its top rim, the other near its foot - and closing they push it 10 mm towards the arm, out of their
  grip; it stands on the bench on one contact, 1.7 mm deep. With multiccd on (a probe, not adopted)
  the pads take it by several points and lift it 9 cm, and it falls from them as the carry begins
  (OPEN LW-057).
- The plate is out of reach: the pads stand 35 mm tall about the tool point, and kept 5 mm over the
  bench they cannot close on a 6 mm plate - each of the 36 says so, and is not run.
- Checked in `tests/test_graspbench.py` (10: 8 quick, the plate's through MuJoCo among them; 2 slow
  - the lying block across the jaws and by its ends, the cube turned 30 deg held and unfelt). Suites
  on MuJoCo 3.10.0: 1220 passed with a display, 1150 headless.
- *In the window* (22 November): What's new's *By its ends, it falls* loads the arm lab on the bench
  (the window finds the field by its id, `fields.VARIANTS`) with the lying block at turn 90, solves the
  bench's program for it and runs it: felt held, lifted, turned more than 20 deg in the jaws on the
  carry, on the floor when the program completes (`tests/test_whats_new.py`, a window test). Suites:
  1221 passed with a display, 1150 headless.
- *In the Inventory* (22 November): a fifth tab, *Grasp bench*, shows the table the bench recorded for
  an example as designed (`RECORDED`, `recorded`: the arm lab's, its report and what to read in it),
  and runs the bench on the current design in another process - its button the varied runs' way of
  launching a sweep - the table filling from the runs' progress lines as they come in (`progress`,
  `counts`), then read back from the outcomes it wrote (`from_json`, `summary`). FR-043 asked for the
  button in the Joint lab; the kit's arm is built in the workshop, so it is in the Inventory beside *What
  it can do*. Checked in `tests/test_graspbench.py` (the record against its report, the lines, the
  outcomes read back) and `tests/test_inventory.py` (a window test, the command a stand-in). Suites:
  1223 passed with a display, 1151 headless.

**Boundaries.** One gripper, the kit's on the arm lab, and known pose only: FR-043's camera mode, the
other designs and the robot library's grippers, intervals clustered by pose, FR-036's friction in use
at the lift, and the Joint lab's button are not done. The carry runs one way, to the side; why the
lying block is held at 14 deg and lost at 16 is measured, not explained. The cylinder's result is
this engine's: a real cylinder in parallel jaws is held along a line of contact on each side.
