Measured for ADR 0054 (searching for the failure) on 2026-10-23: `inventory/falsify.py`'s compass
search over the variation box (ADR 0024: x, y within 2 cm, turned within 3 degrees, 0 to 0.5 kg carried
up to 5 cm across its site, friction across every pair's spread), from the design as designed, against
drawn set-ups. 162 runs. Each searched run carries the label 'searched', so all draw the same camera
noise; a drawn set-up draws its own.

# Searching for the failure, against drawing at random

## Fetch: what the tuning draws certified

A run's margin: each measure of how the cube was handled (ADR 0040) that does harm as it grows - the
table's and the bin's push, in a step and over 50 ms, its leans, its fall - and the squeeze either
way, against the most (and least) any of the 59 tuning draws (seed 1) had it, at the report's
precision (ADR 0049), as a share of the draws' spread; below 0, outside what was certified.

| Looking | Runs | First outside the envelope | Lowest margin | Under a micrometre (5 repeats each) |
| --- | --- | --- | --- | --- |
| 59 fresh draws (seed 20261022, ADR 0049's held-out sweep) | 59 | draw 19: the table's push 0.77 N in a step (0.49 kg carried) | -0.35 | 0.69 to 0.75 N, 5 of 5 outside: a corner |
| the search, every measure | 40 | none | +0.03 (the squeeze, 3.3 N) at its second run, x -1 cm | +0.05 to +0.17: the squeeze 3.29 to 3.59 N |
| the search, the table's push in a step alone | 27 | run 27: 0.65 N (x -2 cm, y +1 cm, friction +0.25) | -0.07 | 0.48 to 0.64 N, 1 of 5 outside: a knife edge |

The margin is rugged at the millimetre scale: set down 1.0, 1.1 and 0.9 cm behind its mark, the
design's margins were +0.03, +0.22 and +0.04, and friction a quarter up or down from where the
search stood took the table's push from inside to outside and back. A compass search follows
neighbours; here the neighbours differ by chance - where on the cube's edge the jaws come to rest -
as much as by the set-up, so it found what chance gives: a margin that a micrometre moves by 0.13,
and an excursion that four of five micrometre repeats do not repeat. The drawn set-up that left the
envelope carried 0.49 kg, and stays outside under a micrometre - a real corner, which the search,
following the squeeze down and the table's push near the design, did not go to.

## The tilt table: how far past its last hold the machine tips

| Looking | Runs | The lowest tip | Where |
| --- | --- | --- | --- |
| the search | 30 | 53.35 deg (+3.35 past 50), first at run 15 | friction at its high end, set down 2 cm ahead and 1 cm right |
| 30 random draws (seed 1) | 30 | 55.03 deg | - |
| the plan's corners, each variation alone at either end (in every sweep) | 10 | 53.32 deg | friction at its high end |

Here the margin is smooth - each variation moves the tip steadily, friction most (1.3 degrees from
the middle of its spread to its high end) - and the search went straight to the worst: but it is a corner the sweep's plan already runs, friction alone at
its high end. A payload makes the machine stand steadier wherever it sits, so the search never carried one.

## The region FR-025 was to be judged on is gone

FR-025 proposed to judge the search on a known failure region: the cart rocking between its casters
before ADR 0041, which pressed the cube into the table in 4 of 59 drawn set-ups, all carrying 0.44 to
0.5 kg. With today's program, the rocking cart (`mobile_manipulator_blueprint(ROCKING_GAP)`), as
designed and on the 9 set-ups of the 71 carrying 0.44 kg or more - the plan's three 0.5 kg corners and
the six heaviest draws - pressed none: the table pushed the cube with its weight, 0.17 to 0.19 N over 50 ms, and every
goal was met. Since ADR 0040 the jaws close on the cube's upper half (ADR 0042), which would keep the
palm stop clear of its top as the cart tips - likely the reason, not traced (OPEN LW-035).
