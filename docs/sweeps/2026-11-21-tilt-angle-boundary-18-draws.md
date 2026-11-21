# Tilt table, the table stopped at each angle and held 3 s, 18 draws a level: arm on a cart

Table angle: 50 % at 54.3 deg, 95 % between 53.5 and 55.2 deg.

| Table angle, deg | Met every goal | 95 % interval | Fitted |
| --- | --- | --- | --- |
| 45.0 | 18 of 18 | 81 to 100 % | 100 % |
| 46.0 | 18 of 18 | 81 to 100 % | 100 % |
| 47.0 | 18 of 18 | 81 to 100 % | 100 % |
| 48.0 | 18 of 18 | 81 to 100 % | 100 % |
| 49.0 | 18 of 18 | 81 to 100 % | 100 % |
| 50.0 | 18 of 18 | 81 to 100 % | 100 % |
| 51.0 | 16 of 18 | 65 to 99 % | 89 % |
| 52.0 | 15 of 18 | 59 to 96 % | 83 % |
| 53.0 | 13 of 18 | 47 to 90 % | 72 % |
| 54.0 | 10 of 18 | 31 to 78 % | 56 % |
| 55.0 | 7 of 18 | 17 to 64 % | 39 % |
| 56.0 | 2 of 18 | 1 to 35 % | 11 % |
| 57.0 | 0 of 18 | 0 to 19 % | 0 % |
| 58.0 | 0 of 18 | 0 to 19 % | 0 % |

Each level on the same 18 draws (seed 1); the interval from 2000 resamples of each level's draws (seed 1).

Run with `python -m little_world.inventory.boundary tilt 45 58 1 --design mobile_manipulator --samples 17 --jobs 2`
(252 runs, 53 minutes on two cores). The first nine draws - as designed and repeats 1 to 8, the draws of
[the 9-draw report](2026-11-21-tilt-angle-boundary.md) - read alone from these runs give 50 % at 53.5
deg, 95 % between 51.8 and 54.6, as that report does. With all 18: 50 % at 54.3, between 53.5 and 55.2 -
an interval 1.64 times narrower, where the square root of two gives 1.41 (FR-042's third check).
