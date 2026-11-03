# Where runs fail: how far each sweep's runs got, and where a program gave up

**Problem.** A sweep reports how many set-ups met every goal, with its interval (ADR 0028), and,
paired, how many a disturbance broke and how many it mended (ADR 0036). It does not say where the
others failed: ADR 0051 and 0052 wrote by hand that the moved cube's runs failed at the grasp and the
frozen camera's at the look. Two disturbances can cost the same and fail in different places
(RoboCasa-Shift, arXiv 2610.27861: equal drops of 0.188, first-stage failures 19.0 % against 36.4 %).
FR-038 (second in the weekly reading of 2 November) asked for a stage profile in every sweep report.

**Does an existing simulator solve it? Can we wrap it?** Not a simulator's question. The field's
goals are its stages already, in the order a run meets them - the Fetch's: reached the table, lifted
the cube, set it in the bin - and the program runner knows at which block it gave up.

**Unique contribution.**
- *Where a program gave up* (`Run.stopped`): its block and the block's kind, when it failed.
- *A stage profile* (`inventory/stages.py`, standard library): for a group of runs, how many met each
  goal and every goal before it (`funnel`), the first goal each run missed (`missed_at`), what a
  program that gave up was doing - looking, driving, moving the arm, checking the grasp (`stopped`);
  a table in every sweep report and a disturbance report (`markdown`), two short lines for a panel
  (`lines`).
- *In the window*: after "Repeat with variations" or "Repeat with disturbances", under each line that
  missed, where: "missed: lifted 9", "gave up: looking 9".

**Blueprint and builder.** Untouched: a report reads its runs.

**Result.** On the Fetch's disturbance sweep - 9 set-ups under each of the field's seven
disturbances - with the program's recovery off (`--recovery none`, ADR 0051's baseline), so that
failures show, three disturbances cost the same, none of the 9 set-ups and all 8 drawn pairs broken,
and fail in two places:

| Disturbance, recovery off | Every goal | Reached the table | Cube lifted | In the bin | Gave up |
| --- | --- | --- | --- | --- | --- |
| none, shoved 4 or 6 N s, cube moved 3 or 5 cm before the look | 9 of 9 each | 9 | 9 | 9 | - |
| cube moved 5 cm, 2 s after the look | 0 of 9 | 9 | 0 | 0 | moving the arm, 9 |
| camera frozen as the cube is moved | 0 of 9 | 9 | 0 | 0 | looking, 9 |
| camera dark at the table | 0 of 9 | 9 | 0 | 0 | looking, 9 |

The moved cube's runs gave up at the reach - it pressed the cube into the table until the pose timed
out (LW-029) - and the camera faults' at the look: what ADR 0051 and 0052 wrote by hand, now in every
report and, after "Repeat with disturbances", in the window ("missed: lifted 9", "gave up: reaching
9"). With its own recovery the program fetches the moved cube in all 9 (ADR 0051).

Held by `tests/test_stages.py` (3): the funnel, the first goal missed and where programs gave up,
counted on runs made up for it; where a program stopped surviving the report file; and on the field,
the frozen camera's Fetch giving up at its look having reached the table. Suites on MuJoCo 3.10.0:
1125 passed with a display, 1066 headless (run with ADR 0064's four tests beside them: 1129 and 1070).

**Boundaries.** The stages are the field's goals and the program's block kinds: finer stages - the
reach split from the descent, the carry from the set-down - are not named. Runs stored before this
record have no `stopped`; their funnels still read.
