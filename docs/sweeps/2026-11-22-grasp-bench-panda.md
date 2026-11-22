# Grasp bench: franka_panda

Each object at 9 places x 4 turns on a bench 18.7 cm up; approach, close, lift 10 cm, carry 20 cm, hold 2 s; known pose. Held: lifted and carried, and under 2 mm of slip in the jaws over the last 2 s.

At the 0, 30, 60, 90 deg turns the object's x axis lay 13, 43, 73, 77 deg from the line the jaws close along (0: along it; the median over the places).

| Object | 0 deg | 30 deg | 60 deg | 90 deg | Held | 95 % interval |
| --- | --- | --- | --- | --- | --- | --- |
| cube | 9 of 9 | 0 of 9 | 9 of 9 | 9 of 9 | 27 of 36 | 58 to 88 % |
| block | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |
| block lying | 0 of 9 | 8 of 9 | 9 of 9 | 9 of 9 | 26 of 36 | 55 to 86 % |
| cylinder | 8 of 9 | 7 of 9 | 7 of 9 | 8 of 9 | 30 of 36 | 67 to 94 % |
| plate | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 36 | 0 to 10 % |

## Why the rest were not held

- cube: slipped in the jaws (9)
- block lying: slipped in the jaws (7); not lifted (3)
- cylinder: not lifted (6)
- plate: the arm cannot close its jaws on it without striking the bench (36)

Held runs slipped 0.00 to 0.50 mm in their last 2 s.

## How close to slipping

The most of its grip's friction in use while the object was in the air, held by the jaws alone (FR-036): 100 % is a grip at the edge of its friction cones, sliding.

| Object | held runs: median | most | not held, in the air |
| --- | --- | --- | --- |
| cube | 11 % | 18 % | 62 %, 65 %, 65 %, 65 %, 75 %, 75 %, 75 %, 79 %, 79 % |
| block | 11 % | 42 % | - |
| block lying | 6 % | 72 % | 64 %, 65 %, 66 %, 67 %, 67 %, 67 %, 90 %, 100 %, 100 %, 100 % |
| cylinder | 28 % | 32 % | - |

## What the grasp check felt

The program went on as taught whatever its grasp check felt; the check reads its jaws' contacts with the object: a library robot's gripper servo is not read as the kit's are.

| Object | held, felt held | held, felt nothing | not held, felt held | not held, felt nothing |
| --- | --- | --- | --- | --- |
| cube | 27 | 0 | 9 | 0 |
| block | 36 | 0 | 0 | 0 |
| block lying | 26 | 0 | 10 | 0 |
| cylinder | 30 | 0 | 0 | 6 |
| plate | 0 | 0 | 0 | 0 |

It felt 119 of the 119 held runs held, and 19 of the 25 others.

## How it was run

`python -m little_world.inventory.graspbench --design franka_panda` (ADR 0077): the Panda from the
robot library standing on the floor beside the bench, held up and squeezing 70 N as its own controller
does (ADR 0065); the same objects, poses and protocol as the arm lab's, but that its gripper closes all
the way at its key's speed (100 % at 60 %/s) before the template's squeeze and check, and that the
bench reads its hand's clearance from its meshes' own vertices.

## Against the kit's gripper on the arm lab

The arm lab's table is docs/sweeps/2026-11-22-grasp-bench-squeeze-first.md.
- *It squeezes harder*: 70 N against the kit's 1 N or so, it uses a fifth of the friction - held cubes
  11 % at the median, the kit's 55 % - and creeps under 0.5 mm in the hold, the kit's up to 1.9.
- *It holds the cylinder*: 30 of 36, where the kit's jaws push it out (OPEN LW-057); its fingers'
  contacts are the stiffest MuJoCo takes (ADR 0065), and they close on it from above.
- *It drops a cube taken by its corners*: turned 30 deg, 43 deg from its jaws, 0 of 9 - its flat fingers
  slide off the corners, where the kit's rotary jaws turn the cube square and hold it.
- *Like the kit, it loses the lying block by its ends*: its jaws, which the bench's program does not
  turn, close 13 deg from the block's length at turn 0, and it slips out, 0 of 9; across them it is
  held. The arm lab's jaws close across the line from its base, the Panda's along it.
