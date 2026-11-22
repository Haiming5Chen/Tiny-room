# Grasp bench: franka_panda, its jaws turned

Each object at 9 places x 4 turns on a bench 18.7 cm up; approach, close, lift 10 cm, carry 20 cm, hold 2 s; known pose; the jaws turned square to each box by the arm's wrist. Held: lifted and carried, and under 2 mm of slip in the jaws over the last 2 s.

At the 0, 30, 60, 90 deg turns the object's x axis lay 0, 0, 90, 90 deg from the line the jaws close along (0: along it; the median over the places).

| Object | 0 deg | 30 deg | 60 deg | 90 deg | Held | 95 % interval |
| --- | --- | --- | --- | --- | --- | --- |
| cube | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |
| block | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |
| block lying | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |
| cylinder | 8 of 9 | 7 of 9 | 7 of 9 | 8 of 9 | 30 of 36 | 67 to 94 % |
| plate | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 36 | 0 to 10 % |
| small block | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |
| tall block | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |

## Why the rest were not held

- cylinder: not lifted (6)
- plate: the arm cannot close its jaws on it without striking the bench (36)

Held runs slipped 0.00 to 0.25 mm in their last 2 s.

## How close to slipping

The most of its grip's friction in use while the object was in the air, held by the jaws alone (FR-036): 100 % is a grip at the edge of its friction cones, sliding.

| Object | held runs: median | most | not held, in the air |
| --- | --- | --- | --- |
| cube | 6 % | 12 % | - |
| block | 6 % | 8 % | - |
| block lying | 6 % | 8 % | - |
| cylinder | 28 % | 32 % | - |
| small block | 9 % | 12 % | - |
| tall block | 10 % | 13 % | - |

## What the grasp check felt

The program went on as taught whatever its grasp check felt; the check reads its jaws' contacts with the object: a library robot's gripper servo is not read as the kit's are.

| Object | held, felt held | held, felt nothing | not held, felt held | not held, felt nothing |
| --- | --- | --- | --- | --- |
| cube | 36 | 0 | 0 | 0 |
| block | 36 | 0 | 0 | 0 |
| block lying | 36 | 0 | 0 | 0 |
| cylinder | 30 | 0 | 0 | 6 |
| plate | 0 | 0 | 0 | 0 |
| small block | 36 | 0 | 0 | 0 |
| tall block | 36 | 0 | 0 | 0 |

It felt 210 of the 210 held runs held, and 0 of the 6 others.

## The cell's parts with the jaws as the arm came

The same two parts without `--turned`: the jaws close 13, 43, 73 and 77 deg from a part's x axis at the
four turns, as for the five objects in docs/sweeps/2026-11-22-grasp-bench-panda.md.

| Object | 0 deg | 30 deg | 60 deg | 90 deg | Held | 95 % interval |
| --- | --- | --- | --- | --- | --- | --- |
| small block | 9 of 9 | 2 of 9 | 9 of 9 | 9 of 9 | 29 of 36 | 64 to 92 % |
| tall block | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |

The small block turned 30 deg - 43 deg from the jaws - slipped out at 7 of the 9 places, with 41 to 56 %
of its friction in use in the air; the tall block, taken at its middle 32.5 mm up (the small one at its
middle, 20 mm up), was held at every pose - measured, not explained.

## Paired with the runs as the arm came

The same 36 poses each way (ADR 0036's exact test on the pairs that differ):

| Object | held both ways | only turned | only as it came | p |
| --- | --- | --- | --- | --- |
| cube | 27 | 9 | 0 | 0.004 |
| block | 36 | 0 | 0 | 1 |
| block lying | 26 | 10 | 0 | 0.002 |
| small block | 29 | 7 | 0 | 0.016 |
| tall block | 36 | 0 | 0 | 1 |

A round object is not turned: the cylinder's 36 runs are the same both ways to the last digit, and the
plate's (out of reach) too.

## How it was run

`python -m little_world.inventory.graspbench --design franka_panda --objects cube block 'block lying'
cylinder plate 'small block' 'tall block' --turned` (ADR 0077): the Panda as in
docs/sweeps/2026-11-22-grasp-bench-panda.md, and at every pose its seventh joint - the one that turns
its hand about where it points, its axis through the tool point - turns the jaws to close across a long
box, or onto the nearer face of a square one, as the factory cell holds its hand square to its parts.
The cell's two parts (`factory.scene.PRODUCTS`) stand on the bench in the bench's wood (650 kg/m3 - the
cell's is 600).

## FR-043's check (3)

The factory cell placed 228 of 228 parts within room (ADR 0057, 0065): its hand held every part it took.
On the bench the Panda, its jaws turned as the cell turns them, holds both of the cell's parts at all 36
poses, 72 of 72: the bench agrees with the cell. As the arm comes, it drops the small block turned
30 deg at 7 of 9 places - a turn the cell's tray never gives it.
