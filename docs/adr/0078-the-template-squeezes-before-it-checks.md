# The template squeezes before it checks

**Problem.** The arm lab's pick-and-place template - the program the Program panel's *Pickup
template* writes, and what the arm lab's sweeps and the grasp bench run - closed its jaws for 1 s and
then checked the grasp from the jaws' servos (ADR 0048). The ramp's target ends 2 or 3 pulses past a
25 mm face: there a resting jaw pushes with 4 counts of current, under the 6 the feel needs, so the
check passed only while the jaws were still pressing the part. A cube 16 deg off square was felt from
4.98 to 5.24 s, the check beginning at 4.99 s. On the grasp bench (ADR 0077) the check missed 13 of 18
held cubes and blocks turned 44 deg to the jaws - closing on their corners, the jaws turned them square
before the check began - and a program that checks stops there, "Nothing held: the grasp missed", the
part in its jaws (OPEN LW-056).

**Does an existing simulator solve it? Can we wrap it?** Nothing is modelled anew: it is the order of
a program's blocks. The jaws, their servos and the feel are as ADR 0042 and 0048 have them.

**Unique contribution.** `tool_motion.take_hold(jaws, target)`: close for 1 s, keep closing `SQUEEZE`
more - the 0.6 deg with which the Fetch already holds its cube at about 1 N a pad once it is felt held
(ADR 0042) - then check. Resting, each jaw now stops 6 pulses short of its goal pushing with 10 counts.
The template and the grasp bench's program take hold so. The Fetch's own program keeps its order -
check, then squeeze: its cube stands square to its jaws in every set-up (the machine is turned 3 deg at
most), and moving its squeeze would move its recorded runs.

**Blueprint and builder.** Untouched. A program written by the template before this keeps its blocks.

**Result** (the grasp bench on the arm lab, the same 180 poses before and after, paired;
docs/sweeps/2026-11-22-grasp-bench-squeeze-first.md):
- The check felt 97 of the 97 held runs held, where it felt 85 of 98: none missed. Resting on the cube
  turned 30 deg, each jaw stops 6 pulses short of its goal pushing with 10 counts (4 before).
- Held at 97 poses both ways; one lying block, held before, crept 2.14 mm in the last 2 s (1.85 before)
  and is counted not held - none held only after (exact McNemar p = 1.0). By object: cube and standing
  block 36 of 36 both ways, the lying block 25 of 36 (26), cylinder and plate 0.
- Squeezed harder, held parts creep a little more in the hold: the cube 0.51 mm at the median in 2 s
  (0.29 before), the lying block 1.59 (1.41), the standing block 0.03 (0.02).
- The arm lab's pick-and-place as designed (the evidence's claim): the cube lifted at 1.922 s and
  resting in the tray at 5.744 s, each 0.02 s - the squeeze - later than its record; the records follow.
- Checked in `tests/test_graspbench.py` (the cube turned 30 deg is held and felt) and
  `tests/test_arm_tasks.py` (the template squeezes before it checks); `tests/test_evidence.py` and the
  records follow the arm lab's times. Suites on MuJoCo 3.10.0: 1221 passed with a display, 1150 headless.

**Boundaries.** The squeeze is still a duration of the jaws' ramp, sized on the kit cube and gripper
(ADR 0042); parts of other widths were not tried. The Fetch's program was not changed. Why the harder
squeeze lets held parts creep more is not traced.
