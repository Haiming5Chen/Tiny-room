# A reach that feels what it meets, side by side — 2026-11-06

ADR 0071 (OPEN LW-029). The Fetch field with the arm on its cart (`mobile_manipulator`), its
program solved once for the design on its mark as a sweep solves it, run as it was - a reach that
cannot settle waits out its pose's 2 s - and with the runner reading the arm's joints against
where it sends them, so that a reach that meets something is felt (`FELT_LAG` 0.5 deg, from
`CATCHING`, three quarters of the reach's travel). Paired set-up by set-up (ADR 0036): the 9
disturbed set-ups (the design and 8 draws, seed 1) undisturbed and under each of the field's 7
disturbances; the 71 tuning set-ups (seed 1); 59 fresh draws (seed 20261106, the repeats of
`plan(ranges, 59, 20261106)` only, entered in the ledger before they ran). Headless, MuJoCo 3.10.0.
The press is how long and how hard the machine pushed on the cube while it was not between both
jaws, before the cube was lifted: per 2 ms step, and the hardest over 50 ms (ADR 0040's window).

| The cube moved 5 cm sideways 2 s after the look (9 pairs) | As it was | Read |
| --- | --- | --- |
| A jaw met the cube at | 17.2 to 17.4 s | the same |
| The arm rose off it, after the jaw met it | 2.44 s (2.43 to 2.44) | 0.21 s (0.20 to 0.22) |
| ... saying | Blocked reaching down: looking again | Felt something reaching down: looking again |
| Pressed for | 2.45 s | 0.22 s |
| ... hardest over 50 ms | 3.11 N (2.88 to 3.16) | 2.35 N (2.23 to 2.38) |
| ... hardest in a step | 3.12 N | 6.10 N, the step its joints were sent where they stood |
| Every goal met | 9 of 9 | 9 of 9 |
| The cube lifted / in the bin | 26.4 / 43.5 s | 24.0 / 41.1 s |

| Everything else | Read |
| --- | --- |
| The other 6 disturbances and none, 9 set-ups each (63 runs) | no reach felt; every goal as it was - met in 45, and the 18 with the camera frozen or dark stop before they reach, as before |
| Tuning set-ups, seed 1 (71) | every goal met in 71 of 71 and no reach felt - each run the run as it was, the cube in the bin at the same millisecond as in ADR 0070's sweep |
| Fresh draws, seed 20261106 (59) | every goal met in 59 of 59 and no reach felt |

The check reads the joints and changes nothing until it fires, so a run in which no reach was felt
is the run as it was, step for step - as the cube moved 3 or 5 cm at once showed, every delivery
time the same to the millisecond. Medians, with the range over the set-ups in brackets.
