# Disturbances during a run: a shove, a part moved

**Problem.** ADR 0024 varies the conditions a run starts in; once a run began, nothing
happened to it. A lab does things to a robot while it works: someone bumps the cart, a part
is moved after the robot planned for it. How hard a shove the arm on a cart takes and still
fetches its cube, and whether the aimed poses of ADR 0025 are what saves it, had never been
measured. The owner accepted FR-006 on 3 October 2026; its source is RoboRecover (arXiv
2609.28952), a benchmark of recovery from deviations during execution.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo applies external forces to
bodies (`xfrc_applied`) and lets a free body be moved; benchmarks of recovery, and the
push-recovery tests of legged robots, inject such events. Those are wrapped. What is this
project's: saying when it happens (after a goal is met, once the machine stands still),
judging by the field's own goals, and comparing every set-up with itself undisturbed.

**Unique contribution.**
- *What happens, and when.* `fields/disturbance.py` (standard library): a `Disturbance` is
  a push on the machine's base - an impulse in newton-seconds, spread over 0.1 s, at an
  angle to the machine's heading - or a loose field part moved by an offset. It is timed
  from a goal being met, optionally once the machine has stood still a while, plus a
  delay. `Disturbing` applies it and notes what it did, including how far the base went
  the way it was pushed, a second later.
- *The adapter.* `MujocoBackend.push` holds a force on a body's centre of mass until it is
  changed; `MujocoBackend.shift` moves a body on a free joint and leaves it at rest. A body
  fixed to the world cannot be shifted.
- *Each set-up against itself.* `sweep.disturb` runs the design as designed and the eight
  set-ups its sweep draws at random (ADR 0028), undisturbed and under each of the field's
  disturbances (`DEFAULTS`). Fetch: shoved 4 or 6 N s to its left once stopped at the
  table; the cube moved 3 or 5 cm sideways at that moment. Sprint: shoved 4 or 8 N s to its
  left a second after the start line. The report gives, per disturbance, the set-ups that
  met every goal, the rate over the drawn ones with its bound, the median change in when
  the last goal was met, and how far pushes moved the machine.
  `python -m little_world.inventory.sweep fetch --disturb`; `--corrections 0` runs a
  program's poses as taught (the runner's correction cap is now a parameter).
- *Found on the way, and fixed.* The grasp check counted the table as held. Shoved 6 N s,
  a corrected pose closed the jaws on the table's edge, both pads touched something - the
  table - and the program carried on as if it held the cube; only the field's goals said
  otherwise. A grasp now counts only a body that can move (`Observations.grasped`), so such
  a program stops with "Nothing held", as ADR 0016 meant it to.

**Blueprint and builder.** Untouched: a disturbance is a condition of a run.

**Result.** Fetch, arm on a cart, MuJoCo 3.10.0, nine set-ups each
(docs/sweeps/2026-10-03-fetch-mobile-manipulator-disturbed.md, and
-disturbed-as-taught.md with `--corrections 0`):

| Disturbance | aimed poses corrected (ADR 0025) | poses as taught | the base moved |
| --- | --- | --- | --- |
| none | 9 of 9 | 9 of 9 | - |
| shoved 4 N s at the table | 9 of 9, last goal +1.2 s | 8 of 9, last goal +1.0 s | 1.7 cm (0.9 to 3.8) |
| shoved 6 N s at the table | 3 of 9, last goal +7.1 s | none | 6.4 cm (3.7 to 11.8) |
| cube moved 3 cm sideways | 7 of 9 | 6 of 9 | - |
| cube moved 5 cm sideways | none | none | - |

Sprint, mobile platform, driven straight ahead at full speed with nothing to steer it
(docs/sweeps/2026-10-03-sprint-mobile-platform-disturbed.md): shoved 4 N s a second past
the start line, it ends up 12 cm to the side a second later (7.7 to 21.5 cm, the turn the
shove gives it included) and still finishes in every set-up, 0.1 s later; shoved 8 N s, 79
cm (46.6 to 121.4), and it finishes in 2 of 9.

What it shows: undisturbed, the poses work as taught in every set-up. The corrections carry
the cart through a 4 N s shove (about 2 cm) in every set-up, where poses as taught lose one,
and through a 6 N s shove (about 6 cm) in 3 of 9, where poses as taught lose all nine - past
about 4 cm the corrected pose put the jaws on the table's edge, and the program has no way
back to its stop (OPEN LW-019). A cube
moved after the cart arrived is still taken at 3 cm in 7 of 9 set-ups, by the jaws' own
width, and at 5 cm in none: nothing looks at the cube again (FR-011). Checks in
`tests/test_disturbance.py` (7): what a disturbance says and refuses; a push waits for its
goal and a still machine, pushes to the machine's left whichever way it faces, stops after
0.1 s and is measured along its own direction; a move happens once; the adapter pushes a
machine and moves a loose cube but not a fixed table; a fixed table between the jaws is not
held; the report compares each set-up with itself; and, in full physics, the design as
designed recovers from the 6 N s shove with corrections and misses the cube without them.

**Boundaries.** A push is a force on the base's centre of mass for 0.1 s, not a hand on its
side, always to its left; the impulses were chosen to span "recovers" to "does not", not
measured in a lab. A moved part moves instantly and at rest. There is no slippery floor
patch yet, and no button in the window (OPEN LW-018). Nine set-ups give wide bounds: the
rates say what was seen, not how often it happens in a lab.
