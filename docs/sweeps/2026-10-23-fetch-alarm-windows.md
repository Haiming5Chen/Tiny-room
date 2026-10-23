Measured for ADR 0052 (how late is too late) on 2026-10-23: the Fetch field as of ADR 0051, on the
tuning draws (seed 1) - the 9 set-ups of its disturbed sweeps, and the 71 of ADR 0048's sweep - with
`inventory/branch.py`'s readers. 311 runs. The runs with the program's own recovery are ADR 0048's,
bit for bit: the 9 disturbed ones (`2026-10-22-fetch-feel-disturbed-9.md`) and the 71 undisturbed
ones (`2026-10-22-fetch-feel-71.md`) came out with the same goals met at the same times, the same
grasp checks and the same disturbance times - the alarm's code changes nothing until an alarm is raised.
Again: `python -m little_world.inventory.branch window --jobs 2` and `python -m
little_world.inventory.branch false-alarms --samples 59 --jobs 2`; the frozen camera's runs are
`sweep.run(..., recovery='ignore', checks=False, alarm=t)`.

# Fetch: how late is too late, and what a false alarm costs

## When an alarm can still rescue a run: cube moved 5 cm sideways, 2 s later

Each set-up run with the program's checks ignored - it goes on as taught - and missing a goal; then again with an alarm every 0.5 s of the time the program listened, from the end of its look at the stop to leaving it, the alarm making it look again as its own recovery does. Each such run is the unalarmed one until the alarm, step for step (ADR 0036). "Its own check" is when, with its own recovery, the program's check began it (ADR 0033, 0037); the deadline is the latest alarm that still rescued the set-up, and the slack how much later than its own check that is. World seconds.

| Set-up | Disturbed at | Listening | Its own check | Alarms that rescue | Earliest | Deadline | Slack |
| --- | --- | --- | --- | --- | --- | --- | --- |
| as designed | 16.46 | 15.14-22.74 | 19.67 | 15 of 15 | 15.5 | 22.5 | +2.8 s |
| repeat 1 | 16.61 | 15.29-22.90 | 19.82 | 10 of 15 | 16.0 | 20.5 | +0.7 s |
| repeat 2 | 16.47 | 15.15-22.70 | 19.65 | 10 of 15 | 15.5 | 20.0 | +0.3 s |
| repeat 3 | 16.61 | 15.29-22.93 | 19.81 | 14 of 15 | 16.0 | 22.5 | +2.7 s |
| repeat 4 | 16.48 | 15.16-22.78 | 19.67 | 15 of 15 | 15.5 | 22.5 | +2.8 s |
| repeat 5 | 16.63 | 15.30-22.90 | 19.83 | 13 of 15 (not 21.0) | 16.0 | 22.5 | +2.7 s |
| repeat 6 | 16.46 | 15.14-22.71 | 19.65 | 11 of 15 | 15.5 | 20.5 | +0.9 s |
| repeat 7 | 16.51 | 15.19-22.79 | 19.72 | 10 of 15 | 15.5 | 20.0 | +0.3 s |
| repeat 8 | 16.66 | 15.34-22.97 | 19.88 | 14 of 15 | 16.0 | 22.5 | +2.6 s |

What the windows show:

- **Where the window closes.** Going on as taught, the program closes its jaws where the cube had
  been; in 4 set-ups (repeats 1, 2, 6 and 7) that closing tipped the cube onto its side, and those
  are the 4 whose window closed early, at 20.0 to 20.5 s - 0.3 to 0.9 s into the closing. In the
  other 5 the cube leaned (6 to 36 degrees) and stood again, and an alarm rescued them until the
  last moment before the program left the table. Every late alarm that failed found the cube on
  its side - its centre 8 mm lower - grasped it, felt it held, lifted it, and lost it on the way to
  the bin: it fell to the floor (17 to 18 cm).
- **Its own check was in time.** The program's own check - the reach found blocked, 3.18 to 3.22 s
  after the move in every set-up - came at least 0.28 s before the deadline (a deadline is known
  to the 0.5 s between alarms). Its grasp check alone, about 1.5 s later, would have come after it
  in the 4 set-ups the closing tipped.
- **Where the window opens.** Before the move: an alarm at 15.5 s rescued the 5 set-ups moved 0.96
  to 1.01 s after it - the look it began ended after the move, and saw the cube where it went -
  and not the 4 moved 1.11 to 1.16 s after it, whose look ended first and saw it where it had been.
- **One hole.** Repeat 5's alarm at its grasp check (21.0 s): opening the jaws as they pinched the
  cube's edge tipped it over, where the run left alone kept it standing; alarms before and after
  rescued it. Whether a run can be rescued depends on the state and the intervention together.

## A frozen camera has no window

The camera frozen as the cube is moved 5 cm (ADR 0038's disturbance), as designed, with every
picture taken as new (`checks` off) and the checks ignored: the look saw the cube where the frozen
picture showed it, 5 cm from where it was, and the reach missed. None of 15 alarms (15.5 to 22.5 s)
rescued it: each looked again and saw the same stale picture. FR-022's prediction - a deadline at
the start of the last descent onto the cube - assumed a recovery that could see; only ADR 0038's
check, which stops the program before it reaches, protects this run.

## What a false alarm costs

Set-ups that needed no recovery, each run again with one alarm at a moment drawn evenly from the time its program listened (from the end of its look at the stop to leaving it): whether it still met every goal, and how much later it met its last than unalarmed - the same set-up, the same run until the alarm. An alarm recovers as the program's own recovery does, which never comes once a grasp is checked: while the object is held, it opens the jaws on it before looking again.

| While | Alarms | Still met every goal | Broke a success | Later by: median (least to most) |
| --- | --- | --- | --- | --- |
| reaching | 36 | 36 | 0 of 36, at most 8 % | +4.0 s (+1.1 to +6.0) |
| closing | 13 | 13 | 0 of 13, at most 21 % | +6.8 s (+6.1 to +7.8) |
| holding | 22 | 21 | 1 of 22, at most 20 % | +7.5 s (+4.5 to +8.5) |
| all | 71 | 70 | 1 of 71, at most 7 % | +5.9 s (+1.1 to +8.5) |

A false alarm costs time - about 6 s on a 37 s fetch - and broke one success. Raised while the
cube was held, an alarm opened the jaws on it and dropped it up to 6.6 cm onto the table; repeat
39's, raised as the cube was lifted, left it on its side, and the program grasped it lying and lost
it on the way to the bin. Four others it dropped lay on their side too and were delivered all the
same; in all, 20 of the 24 runs in which looking again found the cube on its side lost it on the
way (OPEN LW-033, LW-034). The 71 moments fell 36 while reaching, 13 while
the jaws closed and 22 while the cube was held - in proportion to how long each lasts. The bounds
are one-sided at 95 % over the set-ups (ADR 0028); each set-up drew one moment, from its name.
