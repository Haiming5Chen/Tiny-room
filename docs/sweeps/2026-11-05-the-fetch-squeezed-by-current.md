# The Fetch squeezed by current, side by side — 2026-11-05

ADR 0070 (OPEN LW-041; FR-037). The Fetch field with the arm on its cart (`mobile_manipulator`), its
program solved once for the design on its mark as a sweep solves it, run as it is - its jaws closing
for 1 s and squeezing with what the ramp leaves - and with `tool_motion.squeezed(program, 7)`: every
close held to the jaws' full close, 1.4 s, its servos' current capped for 7 N at each pad's centre
(ADR 0066). Paired set-up by set-up (ADR 0036) on the 71 tuning set-ups (seed 1) and on 59 fresh draws
(seed 20261103, the repeats of `plan(ranges, 59, 20261103)` only), headless, MuJoCo 3.10.0. Each run's
handling (ADR 0040) and the grip's friction in use while carried (ADR 0061) are read on the cube.

| | Tuning set-ups (71 pairs) | Held-out draws (59 pairs) |
| --- | --- | --- |
| Every goal met: as is / at 7 N | 71 / 71 | 59 / 59 |
| Pairs that broke / mended (exact McNemar p) | 0 / 0 (1.0) | 0 / 0 (1.0) |
| The squeeze, steady, as is: median (range) | 3.6 N (3.2 to 5.0) | 3.8 N (3.2 to 5.1) |
| ... at 7 N | 10.0 N (5.2 to 12.2) | 7.7 N (5.4 to 12.2) |
| Its spread over the set-ups (sd): as is / 7 N | 0.40 / 2.29 N | 0.50 / 2.39 N |
| The grip's friction in use at most while carried: as is / 7 N | 96 % / 85 % | 95 % / 82 % |
| ... its median while carried | 41 % / 36 % | 44 % / 37 % |
| The bin's peak push: as is / 7 N | 0.52 / 0.52 N | 0.52 / 0.52 N |
| How far the cube fell when let go: as is / 7 N | 0.37 / 0.48 cm | 0.31 / 0.46 cm |
| The cube in the bin, 7 N later by | 0.73 s (0.47 to 1.02) | 0.76 s (0.51 to 0.87) |

The squeeze is the hardest push on the cube from one jaw, averaged over 50 ms (ADR 0040). Set to 7 N
at the pads' centres, it reached the cube as 5.2 to 12.2 N: the rotary jaws pull the cube towards the
palm as they close (OPEN LW-028), nearer their pivots than the pads' centres, and a cap on torque
pushes harder the shorter its lever - by as much as where each set-up leaves the cube. The ramp's
squeeze, set by when the ramp ends, varied less: six times less across the set-ups.

With every goal met either way, the 7 N squeeze could not show a gain. FR-037 asked for no goal lost, a
squeeze within 0.3 N of its setting across set-ups, and creep and the bin's push no worse: no goal was
lost and the bin's push was the same, but the squeeze was six times less even than the ramp's. Creep in
the hand was not read apart from the grip's friction in use, which was lower at 7 N. Not adopted (ADR
0070).
