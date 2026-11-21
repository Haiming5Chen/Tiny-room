# Fetch, its cube moved back along the table: arm on a cart

The cube moved back: every draw to 6.0 cm and none from 7.0 cm - one half lies between them, finer than the grid not measured.

Tried (the program closed its jaws on it): every draw to 6.0 cm and none from 7.0 cm - one half lies between them, finer than the grid not measured.

| The cube moved back, cm | Met every goal | 95 % interval | Fitted | Tried | Tried and failed |
| --- | --- | --- | --- | --- | --- |
| 0.0 | 9 of 9 | 66 to 100 % | 100 % | 9 of 9 | - |
| 1.0 | 9 of 9 | 66 to 100 % | 100 % | 9 of 9 | - |
| 2.0 | 9 of 9 | 66 to 100 % | 100 % | 9 of 9 | - |
| 3.0 | 9 of 9 | 66 to 100 % | 100 % | 9 of 9 | - |
| 4.0 | 9 of 9 | 66 to 100 % | 100 % | 9 of 9 | - |
| 5.0 | 9 of 9 | 66 to 100 % | 100 % | 9 of 9 | - |
| 6.0 | 9 of 9 | 66 to 100 % | 100 % | 9 of 9 | - |
| 7.0 | 0 of 9 | 0 to 34 % | 0 % | 0 of 9 | - |
| 8.0 | 0 of 9 | 0 to 34 % | 0 % | 0 of 9 | - |

Each level on the same 9 draws (seed 1); the interval from 2000 resamples of each level's draws (seed 1).

Run with `python -m little_world.inventory.boundary reach 0 8 1 --design mobile_manipulator --jobs 2` (81 runs,
30 minutes on two cores). The program is solved once, for the cube where it is planned, and finds it
with the table camera. Tried: it closed its jaws on the cube (a grasp check). Met: every goal - reached
the table, lifted the cube 5 cm, set it in the bin, stayed upright.

From 7 cm every draw stopped before moving the arm: "Seen 7 cm from where it was planned: out of the
arm's reach from this stop" (ADR 0035). No draw tried and failed.
