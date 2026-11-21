# Tilt table, the table stopped at each angle and held 3 s: arm on a cart

Table angle: 50 % at 53.5 deg, 95 % between 51.8 and 54.6 deg.

| Table angle, deg | Met every goal | 95 % interval | Fitted |
| --- | --- | --- | --- |
| 45.0 | 9 of 9 | 66 to 100 % | 100 % |
| 46.0 | 9 of 9 | 66 to 100 % | 100 % |
| 47.0 | 9 of 9 | 66 to 100 % | 100 % |
| 48.0 | 9 of 9 | 66 to 100 % | 100 % |
| 49.0 | 9 of 9 | 66 to 100 % | 100 % |
| 50.0 | 9 of 9 | 66 to 100 % | 100 % |
| 51.0 | 7 of 9 | 40 to 97 % | 78 % |
| 52.0 | 6 of 9 | 30 to 93 % | 67 % |
| 53.0 | 5 of 9 | 21 to 86 % | 56 % |
| 54.0 | 4 of 9 | 14 to 79 % | 44 % |
| 55.0 | 2 of 9 | 3 to 60 % | 22 % |
| 56.0 | 1 of 9 | 0 to 48 % | 11 % |
| 57.0 | 0 of 9 | 0 to 34 % | 0 % |
| 58.0 | 0 of 9 | 0 to 34 % | 0 % |

Each level on the same 9 draws (seed 1); the interval from 2000 resamples of each level's draws (seed 1).

Run with `python -m little_world.inventory.boundary tilt 45 58 1 --design mobile_manipulator --jobs 2`
(126 runs, 27 minutes on two cores); each run lasts the table's climb at 2 deg/s, the hold and half a
second. Met: the machine still stood 3 s after the table passed half a degree under the level.

## Each draw, held and on the climb

The climb is the Tilt table's own protocol (2 deg/s to 60 deg) on the same draws; the prediction is
the design's, about the trip rail's edge (ADR 0029).

| Draw | Stood at, deg | Over at, held | Over on the climb | Predicted | Climb minus held (midway) |
| --- | --- | --- | --- | --- | --- |
| as designed | 50 | 51 | 54.6 | 55.6 | 4.1 |
| repeat 1 | 53 | 54 | 56.2 | 56.2 | 2.7 |
| repeat 2 | 50 | 51 | 55.1 | 55.7 | 4.6 |
| repeat 3 | 54 | 55 | 56.6 | 56.7 | 2.1 |
| repeat 4 | 55 | 56 | 57.9 | 57.3 | 2.4 |
| repeat 5 | 52 | 53 | 55.8 | 56.1 | 3.3 |
| repeat 6 | 54 | 55 | 57.2 | 56.4 | 2.7 |
| repeat 7 | 51 | 52 | 55.1 | 56.3 | 3.6 |
| repeat 8 | 56 | 57 | 58.7 | 57.7 | 2.2 |

Every draw stood held only to 2.1 to 4.6 deg below its climb's reading: the climb reads a machine late.
Pressed against the trip rail the cart creeps along it, and from about 50 deg (as designed) the creep
runs away and it goes over 1 to 3 s later (ADR 0076):

| Changed, as designed | Where it goes over |
| --- | --- |
| nothing: the table's climb at 2 deg/s | 54.6 deg |
| the climb at 0.5 deg/s | 51.4 deg |
| held at 49 deg for 10 s | stands, creeping 0.2 mm/s along the rail |
| held at 50 deg for 10 s | 3.3 s after the table stopped |
| held at 51 deg, steps of 1 ms | stands its 3 s, creeping 0.2 mm/s |
| held at 51 deg, 20 noslip iterations (2 as everywhere) | stands its 3 s, creeping 0.25 mm/s; held at 53, over |
| held, MuJoCo's elliptic friction cones (OPEN LW-039) | stands at 52 deg; over at 53 |
| held at 51 deg, the casters' swivels or the drive wheels stiffened | over, or running away as the hold ends |
