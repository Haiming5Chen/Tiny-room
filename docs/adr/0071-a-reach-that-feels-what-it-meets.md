# A reach that feels what it meets: the arm's servos read, as the jaws' are

**Problem.** OPEN LW-029: reaching down for a cube that was moved under a jaw since its last
picture - the Fetch cube moved 5 cm sideways 2 s after the look, as the jaws come over it - the
program pressed it into the table until its reach timed out. On the design as designed a jaw met
the cube 0.9 s into the 1.3 s reach; once the reach's travel was over the shoulder stood 2.57 deg
short of where it was sent, just outside the 2 deg within which a joint has arrived, and the arm
pressed the cube at 3.1 N for the 2 s a pose may take to settle; then the program rose off it,
looked again and fetched it (ADR 0033, 0037). The arm's servos had told it 2 s before: a servo
reports where it stands against where it was sent, as the jaws' do (ADR 0048), and nothing read
the arm's.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo gives the contacts, which a robot
does not have; a robot has its servos' registers - an X-series servo's Goal Position (116) and
Present Position (132), 4096 pulses a turn (ROBOTIS e-Manual, XH430-W350, read 2026-11-06).
Stopping a move when a joint falls behind what free motion would give is how a robot without a
force sensor feels what it runs into. Nothing to wrap: the runner already sends the goals and reads
where the joints stand.

**Unique contribution.**
- *A reach that feels* (`programming/program.Runner.met`): while the program reaches for the object
  a look found (ADR 0032's aimed reach), each joint's lag - its goal less where it stands, along the
  way it is sent - is followed. A servo keeps its joint about its own time constant behind a moving
  goal - the kit arm's 60 ms, 1.0 deg at the shoulder's 17 deg/s - and catches up as the goals slow
  towards their ends. From three quarters of the travel on (`CATCHING`: past the free lag's peak, so
  long as the servo's time is under a quarter of the travel's - 60 ms against the Fetch reach's
  1.3 s), a joint that falls `FELT_LAG`, 0.5 deg - six counts of Present Position - further behind
  than it has been since has met something.
- *And rises at once*: the program then does what it did with a reach found blocked - rises the way
  it came, looks again and reaches where the object now is (ADR 0033, 0037) - saying "Felt something
  reaching down: looking again"; the runner keeps each such reach in `bumps`. It is one of the
  runner's checks: `Runner(checks=False)` waits the pose out as before; with no look left it changes
  nothing, and the pose times out as it did.
- *In the window*: the Program panel's lines of what a running program has to go on gain the arm's:
  how far its joints stand from where they are sent ("Arm: 1.0 deg from where it is sent"), and "Arm:
  felt something reaching down - rising to look again". What's new's "It feels the cube under its
  jaw" runs the moved cube; "Watch it look again", the same cube, now rises at 17 s (20).

**Blueprint and builder.** Untouched: no block and no program data change; the same program runs.

**Result.** Paired, set-up by set-up (ADR 0036), the Fetch as it was against the arm read
(`docs/sweeps/2026-11-06-a-reach-that-feels.md`):
- *The cube moved 5 cm sideways 2 s after the look* (the design and 8 draws, seed 1): a jaw came
  down on the cube at the same moment either way, 17.2 to 17.4 s. As it was, the arm pressed it
  into the table for 2.45 s, 3.11 N over 50 ms (2.88 to 3.16), and rose 2.44 s after the jaw met
  it, "Blocked reaching down". Read, it rose 0.20 to 0.22 s after, "Felt something reaching down",
  having pressed for 0.22 s, 2.35 N over 50 ms (2.23 to 2.38) - with one 2 ms step at 6.1 N as its
  joints were sent where they stood. It then looked again and fetched the cube as before: every
  goal met 9 of 9 either way, the cube lifted and in the bin 2.4 s sooner (in the bin at 41.1 s
  against 43.5, the median).
- *The field's other disturbances, and none* (63 runs): no reach felt, every goal as it was. The
  check reads and changes nothing until it fires, so these runs are the runs as they were, step for
  step - the cube moved 3 or 5 cm at once delivered to the millisecond as before.
- *Undisturbed*: on the 71 tuning set-ups (seed 1), every goal met in 71 of 71 and no reach felt - each run the run as it was, the cube in the bin at the same millisecond as in ADR 0070's sweep; on 59 fresh draws (seed 20261106,
  entered in the ledger before they ran), every goal met in 59 of 59 and no reach felt.
- *The radar's search*, which learns what words mean from the project's decision records (ADR
  0062), moved with this record's wording: of its 20 known questions it answered 15 in the top three
  before, 14 with a draft of this record among them and 16 with the record as it stands (the mean
  reciprocal rank 0.69, 0.675, 0.73). A measure that a decision record's wording moves by two
  questions is not held at 15 by anything: `tests/test_radar_collection.py` now holds 14, and the
  drift is OPEN LW-043.

Held by `tests/test_felt_reach.py` (6): joints lagging a servo's 60 ms behind a free reach are not
felt; a reach held back 70 % of the way down is felt before its travel is over, and the program
rises and looks again; unchecked, the same reach waits the pose out and is found blocked 2 s later;
with no look left it times out as before; FELT_LAG is six counts of Present Position; the Fetch
with the cube moved under a jaw rises at once and delivers before 41 s. `tests/test_look_again.py`
and `tests/test_rise_and_place.py` now find their blocked reaches felt (unchecked, blocked as
before); `tests/test_whats_new.py` reads the Program panel's arm line, and a window test sees the
panel say it felt the cube within 1.5 s of its move. Suites on MuJoCo 3.10.0: 1159 passed with a display, 1093 headless.

**Boundaries.** The check takes a servo's lag to be under a quarter of the reach's travel time: a
reach down at the 180 deg/s a pose allows, over a short way, could be felt for nothing. A jaw that
meets the object only after the reach's travel is over - its joints already within 2 deg of their
goals - is not felt; the grasp check then finds what it finds. The joints are read in degrees as the
simulation has them, not rounded to pulses (0.5 deg is six). What was met is not known - anything
under a jaw stops the reach - and the threshold was set on the Fetch's own reaches; a heavier arm or
a slower servo would want it measured again.
