# One ramp straight ahead, 25 s: the two-wheel robot

Ramp slope: 50 % at 5.2 deg, 95 % between 5.1 and 5.2 deg - inside the step from 5.0 to 5.5 deg, whose straight line it assumes.

| Ramp slope, deg | Met every goal | 95 % interval | Fitted |
| --- | --- | --- | --- |
| 4.0 | 9 of 9 | 66 to 100 % | 100 % |
| 4.5 | 9 of 9 | 66 to 100 % | 100 % |
| 5.0 | 8 of 9 | 52 to 100 % | 89 % |
| 5.5 | 0 of 9 | 0 to 34 % | 0 % |
| 6.0 | 0 of 9 | 0 to 34 % | 0 % |
| 6.5 | 0 of 9 | 0 to 34 % | 0 % |
| 7.0 | 0 of 9 | 0 to 34 % | 0 % |

Each level on the same 9 draws (seed 1); the interval from 2000 resamples of each level's draws (seed 1).

Run with `python -m little_world.inventory.boundary ramp 4 7 0.5 --design two_wheel --seconds 25 --jobs 2`
(63 runs, under 3 minutes on two cores). Met: on the deck beyond the ramp's top, upright.

Its 20.5 kg against the 23.5 N its two motors give at stall (1 N m each on 85 mm wheels) bound it at
6.7 deg, where m g sin(slope) equals that drive; it stops 1.5 deg short, where the slope asks 18 N.
The draw that missed at 5 deg is repeat 3 (0.36 kg aboard, friction at the top of its range).

## The kit cart

The kit cart climbs no ramp, from 4 deg up (ADR 0041 found none of the Ramps field's 8, 14 and 20
deg). It stands on four rigid points: when its front caster starts up the slope the cart pivots on its
casters and lifts its drive wheels off the floor - at the stall only the two casters touch anything -
and with nothing driving it stands there. With multiccd on it climbs none either. A sprung caster or a
rocker would let it (OPEN LW-026).
