# What looking again earns: the program's recovery against its baselines

**Problem.** When its reach goes wrong at a stop where it looked - the cube moved after the look,
a grasp holding nothing, a reach blocked, the camera stuck - the Fetch program opens its jaws, goes
back, looks again and reaches where it now sees the cube (ADR 0033, 0037). That was measured
against no recovery at all. A recovery earns its complexity only if it beats the simplest thing
that also moves the robot back: over 3,888 paired episodes a scripted return to an earlier pose
matched a learned corrector ([arXiv 2610.06921](https://arxiv.org/abs/2610.06921)), and a study of
retrieval-triggered corrections could not tell its corrections from random ones of the same size
([arXiv 2610.24573](https://arxiv.org/abs/2610.24573); FR-023, the weekly readings of 19 and 21
October).

**Does an existing simulator solve it? Can we wrap it?** MuJoCo is deterministic: under two
recoveries a set-up's runs are one run until the reach first goes wrong, so each pair of runs
differs by the recovery alone - the paired design of ADR 0036, in which the study's placebo
effect is exactly zero. What is new is the baselines and reading them pair by pair.

**Unique contribution.**
- *Recoveries as a choice of the runner* (`Runner(recovery=)`, programming/program.py): its own,
  `look`; `retreat` - back up and reach again from just after the look, aimed where it saw the
  cube, with no new picture: the trigger-matched baseline, the same detectors firing at the same
  moments; `guess` - look again, but reach as far from the first sighting as the cube now is, in a
  random direction (drawn from the sighting, so a set-up always draws the same): the random
  control the second study lacked; `none` - stop.
- *Disturbed sweeps with a recovery* (`sweep --disturb --recovery`): recorded in the sweep's JSON
  and said in its report.
- *Read pair by pair* (`inventory/recovery.py`, `python -m little_world.inventory.recovery OWN.json
  BASELINES...`): per disturbance, each recovery's set-ups meeting every goal, the set-ups looking
  again rescued beyond the baseline and the other way, and the exact McNemar test on them.

**Blueprint and builder.** Untouched; programs keep their blocks and the runner its own recovery.

**Result.** The Fetch field's 9 set-ups (seed 1: the design and 8 drawn), undisturbed and under
four of its disturbances, with each recovery (`docs/sweeps/2026-10-23-fetch-recovery-baselines.md`):

| | Looking again | Retreat | Guess | None |
| --- | --- | --- | --- | --- |
| undisturbed | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 |
| cube moved 5 cm before the look | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 |
| cube moved 5 cm, 2 s after the look | **9 of 9** | 0 of 9 | 0 of 9 | 0 of 9 |
| shoved 6 N s at the table | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 |
| camera frozen as the cube is moved | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 9 |

Looking again earns its complexity where a recovery is needed at all - the cube moved after the
look: it rescued 9 set-ups each baseline lost and lost none they kept (exact McNemar p = 0.0039
against each). Reaching again where the cube had been rescued nothing beyond stopping. The random
re-aim looked again too, saw the cube 4.9 to 5.1 cm away, and reached as far off in another
direction: 2 aims out of the arm's reach, 5 grasps of nothing, 2 reaches blocked - what the look
found, not the look, does the rescuing. Elsewhere the four tie, and say why: a shove is undone by
going back to the stop (ADR 0031), a cube moved before the look is seen by it, and a frozen camera
stops the program before any reach (ADR 0038). No recovery fired in an undisturbed run. The look
arm is ADR 0048's disturbed sweep; one of its runs was repeated and came out the same.

FR-023's `timed` arm - the same retreat at a fixed time, with no detector - was not run: a
retreat at the very moment a detector fired rescued nothing, so one at a fixed time cannot.

Held by `tests/test_recovery.py` (8): the four recoveries and their rules on the runner, with the
stand-ins of `tests/test_look_again.py` - looking again reaches where the cube went, a retreat
reaches again where it was with no second look, a guess looks again and reaches as far off
elsewhere, no recovery ends the program; a disturbed sweep's recovery in its JSON and report; the
pairwise reading; the command line. Suites on MuJoCo 3.10.0: 1060 passed with a display, 1008 headless.

**Boundaries.** One field, four disturbances, 9 set-ups each, on the draws everything was tuned
on (seed 1): a study of what the recovery adds, not a certification (ADR 0049). None of the 8
drawn set-ups rescued by a baseline bounds how often it would rescue a late move to at most 31 %
(one-sided 95 %), not lower. The random control draws one direction per set-up. The false alarms of FR-022 - a recovery
fired where none was needed - are not measured here, beyond none in nine undisturbed runs.
