# Going back to the stop: a program pushed off its stop drives back and reaches again

**Problem.** Shoved 6 N s once stopped at the table, the arm on a cart was moved 3.7 to
11.8 cm and fetched its cube in 3 of 9 set-ups (ADR 0030). Traced set-up by set-up, the
aimed poses of ADR 0025 had done what they were made for - solve the pose again for where
the machine now stood - but from there the arm worked at the edge of its reach: a finger on
the table, a lift stopping short of 5 cm, a cube dropped on the way, jaws closing on
nothing. Nothing in a program could take the machine back to where its poses were planned.
The owner chose to give it a way back (OPEN LW-019, 3 October 2026).

**Does an existing simulator solve it? Can we wrap it?** No simulator decides what a
program does when it is knocked off its mark; that is the program's behaviour. Mobile
manipulators commonly re-localise and re-approach their docking or pick pose rather than
reach from wherever they ended up; here the base's pose is ideal (the simulator's), so the
question is only when to go back and how.

**Unique contribution.**
- *When.* A runner remembers the stop its last drive-to block brought the machine to. An
  aimed pose that settles - or cannot settle - with the base more than 2 cm from that stop
  (`REAPPROACH`; a base stops within 1 cm of its mark, ADR 0025) sends the program back,
  at most once per run (`RETRIES`, a runner parameter like the corrections cap). Within 2
  cm, the corrections of ADR 0025 fix the arm as before.
- *How.* The way it came: the pose the machine drove in, if one came just before the
  drive-to, then the drive-to - which first backs the machine off 25 cm behind the stop
  along the stop's heading and then drives in straight (`RUN_UP`). Coming back from the
  side, a drive to a point accepts up to 3 cm across its line (ADR 0018); coming in
  straight, it stops where it did the first time.
- *Seen in reports.* A run records how often it went back (`Run.went_back`); the
  disturbance report has a column for it, and `--retries 0` runs without going back.

**Blueprint and builder.** Programs are unchanged data; going back is the runner's.

**Result.** Fetch, arm on a cart, the disturbance sweep of ADR 0030 again
(docs/sweeps/2026-10-03-fetch-mobile-manipulator-disturbed-going-back.md):

| Disturbance | aimed poses corrected (ADR 0030) | and going back | went back |
| --- | --- | --- | --- |
| none | 9 of 9 | 9 of 9 | none |
| shoved 4 N s at the table (1.7 cm) | 9 of 9, last goal +1.2 s | 8 of 9, +5.0 s | 5 |
| shoved 6 N s at the table (6.3 cm) | 3 of 9, +7.1 s | **8 of 9**, +10.1 s | 9 |
| cube moved 3 cm sideways | 7 of 9 | 7 of 9 | - |
| cube moved 5 cm sideways | none | none | - |

Going back costs 8 to 10 s. Undisturbed, no run went back. The one 6 N s set-up still lost,
and the one 4 N s set-up lost going back where corrections alone had held, had both had
the cube knocked by the jaws as the cart was shoved - moved 1 to 1.6 cm and tipped - and from
the stop the jaws took it but lost it as it rose or on the way to the bin. Whether the 2 cm
threshold or a
larger one serves better is not settled by nine set-ups: corrections alone fetched the cube
after pushes of up to 3.8 cm once, and failed after one of 3.7 cm.

Undisturbed, the 59 drawn set-ups of ADR 0028 run again: every goal in all 71 runs, with the
same times - no run went back (docs/sweeps/2026-10-03-fetch-mobile-manipulator-59-going-back.md).
Checked in `tests/test_going_back.py` (4): a machine pushed 5 cm off its stop
during its aimed pose goes back - the pose it drove in, a run-up 25 cm behind the stop along
its heading, then the stop - and completes; within 2 cm, or with no retry left, the pose
stands; a pose that cannot settle off its stop goes back instead of failing; and, in full
physics, the set-up whose lift stopped just short of 5 cm after an 8 cm shove now goes back
and meets every goal.

**Boundaries.** The base's pose is the simulator's own; a real machine would need to know
where it is. One retry: a machine shoved twice is not followed twice. A cube knocked over
during the shove is not found again - nothing looks at it (FR-011). The 2 cm threshold and
the 25 cm run-up are chosen, not measured.
