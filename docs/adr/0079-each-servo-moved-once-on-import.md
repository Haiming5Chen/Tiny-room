# Each servo moved once on import: what it moves, said in plain words

**Problem.** The robot library (ADR 0044) takes a file's own actuators as written, as long as each is
a position servo on a joint. A command can pass every check of shape and range and still mean
something else - a negative gear that turns a joint backwards, two actuators on each other's joints,
a gripper whose control is reversed (arXiv 2611.06653; FR-044, fifth in the weekly reading of 9
November). Measured before: a two-link arm written with its elbow's gear at -1, one with its two
actuators on each other's joints, and a claw whose servo's gear is -1 each imported without a word -
"nothing added", nothing to check - and the reversed elbow then turned -5 deg when told +5.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo runs what it is given; the check is a
few steps of it. Nothing is modelled anew.

**Unique contribution.** `importer.probe`, run at the end of every import (and on any model with its
metadata): in a copy of the model at the app's 2 ms step and implicit integrator, its contacts off,
each servo is sent 5 deg (a slide 5 mm) from home - within its joint's limits and its range, up if
there is room - held 1 s, and what moved is read. A joint that moves within 10 % of what it was sent
agrees; one that moves the other way is reversed; one that moves too little or too far is scaled or
still; an actuator whose name is another joint's than the one it drives is named. A gripper - the one
the importer found, or, for a file with its own actuators, the one its geometry shows - is told to
close, and its jaws must come together. Each servo's line goes into the import's report - "'shoulder'
sent +5 deg turned +5.0 deg, the tool 49 mm forward - as the file says" - a mismatch as a thing to
check, and every verdict into the robot's metadata (`probe`). The Joint lab says whether each servo
moved as its file says, above its checks. A servo on a tendon is not probed.

**Blueprint and builder.** Untouched: the probe reads a model and writes words.

**Result** (`tests/test_robot_library.py`, three new):
- The sample arm, the parallel gripper and the claw of the robot library's tests agree: each joint
  turned +5.0 deg when sent +5, each gripper brought its jaws together.
- The four Menagerie arms agree, every servo within 3 % of what it was sent (the Panda's hand, on a
  tendon, not probed) - FR-044's check (1).
- The three planted faults are each named, 3 of 3 - FR-044's check (2): the negative gear ("'elbow'
  sent +5 deg went -5.0 deg: the other way - its actuator 'elbow_motor' drives it backwards"), the
  swapped actuators ("Its actuator 'shoulder_motor' drives 'elbow', though its name says
  'shoulder'"), the reversed claw ("Told to close, 'claw_joint' did not bring its jaws together").
- The UR5e from its own file still moves as the shipped one within 0.5 deg - FR-044's check (3), its
  test unchanged.
- The probe adds 0.01 to 0.05 s to an import.
- Suites on MuJoCo 3.10.0: 1226 passed with a display, 1154 headless.
- *In What's new* (22 November): *A motor wired backwards* brings into Real's Joint lab a sample arm
  whose elbow motor has a negative gear (`assets/samples/arm_elbow_reversed.xml`, kept deliberately
  wrong) - imported once; pressed again, shown from the robot library - and the Joint lab says one
  servo is not as its file says, and which way it went. Checked in `tests/test_whats_new.py` (a window
  test). Suites: 1231 passed with a display, 1158 headless.

**Boundaries.** One servo at a time, from home only, with the contacts off: what a joint does under
load, or at another pose, is not probed. The name check reads names; a joint named nothing like its
actuator passes it. A reversed gripper resting at its open end reads as not closing, not as opening.
FR-044's one-click flip is not done: the report names the fault, and mending it is the file's.
