# How late is too late: when an alarm can still rescue a run, and what a false one costs

**Problem.** The program's checks fire at fixed moments of its reach - one more picture before the
jaws go down, a reach that has not settled 2 s after it should have, a grasp holding nothing, a
picture that is not new (ADR 0033, 0037, 0038) - and whether they fire in time was never measured.
With the Fetch cube moved 5 cm 2 s after the look, the program's own check began its recovery 3.2
s after the move, and looking again rescued every set-up (ADR 0051); how much later could it have
come? And what does an alarm cost that fires when nothing is wrong? A check is worth having only
if it fires while a recovery can still put things right, and only if a false alarm costs little:
whether a failure can be recovered depends on the state and the intervention together, and an
ideal detector tolerated a false-alarm rate of only 2 to 3 % ([RESCUE, arXiv
2610.13516](https://arxiv.org/abs/2610.13516); FR-022, the weekly reading of 19 October).

**Does an existing simulator solve it? Can we wrap it?** MuJoCo is deterministic: a run with an
alarm raised at a moment is the unalarmed run until then, step for step (ADR 0036). So branching a
run at a checkpoint is running it again with the alarm then - no snapshot of the program's own
state is needed, which FR-022 expected to be the main work. MuJoCo's own state (`mj_getState`)
would branch faster, but the program, its camera's noise and the field's disturbance live outside
it; replaying costs a branch its first 15 s, about a third of a run.

**Unique contribution.**
- *An alarm from outside* (`Runner.alarm`, programming/program.py): a detector outside the
  program says its reach is going wrong. At a stop where it looked, with a regrasp left and not
  already going back (`Runner.listening()`), the program recovers as its own recovery does,
  whatever recovery it was given: it opens its jaws by as much as they closed since the look,
  rises if it reached down, goes back and looks again.
- *A fifth recovery, `ignore`*: the checks fire and nothing comes of them - the program goes on as
  taught - so an alarm can be tried at every moment of what follows a check.
- *A sweep run's alarm* (`run(alarm=t)`, inventory/sweep.py): recorded with the block it came in,
  whether the program acted on it, when the program began each recovery (`Run.recovered`) and the
  spans in which it listened (`Run.listening`). Loaded set-ups now share one payload site through
  `shared_site`, as the sweeps always placed them.
- *Windows and false alarms* (`inventory/branch.py`, `python -m little_world.inventory.branch window
  | false-alarms`): a failing set-up run with its checks ignored, and again with an alarm every
  0.5 s of the time it listened - the alarms that rescue it, the earliest, the latest (the
  deadline) and the slack against its own check; and set-ups that needed no recovery, each run
  again with one alarm at a moment drawn evenly from the time it listened - whether it still meets
  every goal, and how much later.

**Blueprint and builder.** Untouched; programs keep their blocks.

**Result.** *When an alarm can still rescue a run.* The Fetch field's 9 set-ups (seed 1) with
the cube moved 5 cm sideways 2 s after the look, the program's checks ignored: going on as taught,
every one missed, and in 4 its jaws, closing where the cube had been, tipped the cube onto its
side. Each was run again with an alarm every 0.5 s of the 7.6 s the program listened - 15 alarms,
135 branches (`docs/sweeps/2026-10-23-fetch-alarm-windows.md`):

| The cube, left alone | Set-ups | Deadline: the last alarm that rescued | After its own check |
| --- | --- | --- | --- |
| standing | 5 | 22.5 s, just before the program leaves the table | +2.6 to +2.8 s |
| tipped onto its side by the program's own closing | 4 | 20.0 to 20.5 s | +0.3 to +0.9 s |

Its own check - the reach found blocked, 3.2 s after the move in every set-up - fired in time in
all 9, at least 0.28 s before the deadline (a deadline is known to the 0.5 s between alarms). Its
grasp check alone, 1.5 s later, would have come too late in 4 of 9: by then the closing had tipped
the cube, and looking again found it on its side, grasped it, and dropped it on the way to the
bin. The window opens before the move: an alarm 0.96 to 1.01 s before it rescued the set-up, the
look it began ending after the move; 1.11 to 1.16 s before, the look ended first and the reach
went where the cube had been. One alarm inside a window failed: at repeat 5's grasp check, opening
the jaws as they pinched the cube's edge tipped it over, where the run left alone kept it standing
- whether a run can be rescued depends on the state and the intervention together, as RESCUE
found. FR-022's prediction for a frozen camera, a deadline at the last descent, does not hold
here: with its pictures taken as new, none of 15 alarms rescued the run, since looking again sees
the same stale picture; only ADR 0038's check, which stops the program before it reaches,
protects it.

*What a false alarm costs.* The 71 set-ups of ADR 0048's sweep (seed 1), each run again with one
alarm at a moment drawn evenly from the time its program listened:

| While | Alarms | Still met every goal | Later by: median (least to most) |
| --- | --- | --- | --- |
| reaching | 36 | 36 | +4.0 s (+1.1 to +6.0) |
| closing | 13 | 13 | +6.8 s (+6.1 to +7.8) |
| holding | 22 | 21 | +7.5 s (+4.5 to +8.5) |
| all | 71 | **70** - 1 broken, at most 7 % (one-sided 95 %) | +5.9 s (+1.1 to +8.5) |

A false alarm costs time, about 6 s on a 37 s fetch. Raised while the cube is held, it opens the
jaws on it - the program's own recovery never comes once a grasp is checked - and drops it up to
6.6 cm onto the table: once of 22 the cube landed on its side, and a cube on its side is grasped
as if it stood and lost on the way to the bin - in 20 of the 24 runs where looking again found it
lying (OPEN LW-033, LW-034). Before the grasp is checked, the 49 false alarms broke none (at most
6 %) and cost 1 to 8 s: there the program's checks can afford to be eager, where RESCUE's ideal
detector tolerated a false-alarm rate of only 2 to 3 %; once the cube is held, an alarm should not
open the jaws. The program's own runs were ADR 0048's, bit for bit (9 disturbed, 71 undisturbed):
its alarm changes nothing until one is raised.

Held by `tests/test_branch.py` (10): an alarm is heard only at a stop where the program looked,
with a regrasp left, and one it cannot act on changes nothing; ignoring its checks the program goes
on as taught; an alarm makes it look again, whatever its recovery, and reach where the cube went,
the jaws opened as long as they had closed - or as far as they had closed when it comes as they
close; the alarms' moments, a window and a false alarm read from runs, a run's alarm round-tripped
through JSON, the command line; and one pair of Fetch runs: with no recovery the moved cube is
missed, with an alarm at 17 s it is fetched, and the two runs are one run, bit for bit, until the
alarm. Suites on MuJoCo 3.10.0: 1070 passed with a display, 1018 headless.

**Boundaries.** One field, one disturbance that a recovery can rescue and one that it cannot, on
the draws everything was tuned on (seed 1): a study, not a certification (ADR 0049). A deadline is
known to the 0.5 s between alarms, and the windows are scanned on 9 set-ups; the alarm is an ideal
detector - always right about when it fires, never late. The false alarms' moments are drawn from
the time the program listens, not from a detector's own errors; each set-up drew one. An alarm
acts only at a stop where the program looked, with its one regrasp left (ADR 0033), and the window
has no button for it. The checks' own false alarms were not counted: none fired in the undisturbed
runs here or in ADR 0051's.
