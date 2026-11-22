# Grasp bench: arm_lab, the template squeezing before it checks

Each object at 9 places x 4 turns on a bench 18.7 cm up; approach, close, lift 10 cm, carry 20 cm, hold 2 s; known pose. Held: lifted and carried, and under 2 mm of slip in the jaws over the last 2 s.

At the 0, 30, 60, 90 deg turns the object's x axis lay 74, 44, 14, 16 deg from the line the jaws close along (0: along it; the median over the places).

| Object | 0 deg | 30 deg | 60 deg | 90 deg | Held | 95 % interval |
| --- | --- | --- | --- | --- | --- | --- |
| cube | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |
| block | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |
| block lying | 8 of 9 | 8 of 9 | 9 of 9 | 0 of 9 | 25 of 36 | 52 to 84 % |
| cylinder | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 36 | 0 to 10 % |
| plate | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 36 | 0 to 10 % |

## Why the rest were not held

- block lying: not lifted (10); slipped in the jaws (1)
- cylinder: not lifted (36)
- plate: the arm cannot close its jaws on it without striking the bench (36)

Held runs slipped 0.01 to 1.88 mm in their last 2 s.

## How close to slipping

The most of its grip's friction in use while the object was in the air, held by the jaws alone (FR-036): 100 % is a grip at the edge of its friction cones, sliding.

| Object | held runs: median | most | not held, in the air |
| --- | --- | --- | --- |
| cube | 55 % | 92 % | - |
| block | 42 % | 72 % | - |
| block lying | 35 % | 41 % | 45 %, 100 %, 100 %, 100 %, 100 %, 100 %, 100 %, 100 %, 100 %, 100 % |

## What the grasp check felt

The program went on as taught whatever its grasp check felt; the check reads the jaws' servos (ADR 0048), not the object.

| Object | held, felt held | held, felt nothing | not held, felt held | not held, felt nothing |
| --- | --- | --- | --- | --- |
| cube | 36 | 0 | 0 | 0 |
| block | 36 | 0 | 0 | 0 |
| block lying | 25 | 0 | 11 | 0 |
| cylinder | 0 | 0 | 2 | 34 |
| plate | 0 | 0 | 0 | 0 |

It felt 97 of the 97 held runs held, and 13 of the 47 others.

## How it was run

As docs/sweeps/2026-11-22-grasp-bench-arm-lab.md, the same 180 poses, with the template taking hold as
ADR 0078 has it: close for 1 s, squeeze 0.6 deg more, then check (`tool_motion.take_hold`). Run again
on 690a8b6 with the grip's friction in use measured while each object was in the air (FR-036): the
same 180 runs to the last digit, and the section on how close each grip came to slipping.

## Against the first run

- *The check*: it felt 97 of the 97 held runs held, where it felt 85 of 98 - the 13 it missed, cubes and
  standing blocks turned 30 deg, are all felt now. Resting on the cube turned 30 deg each jaw stops 6
  pulses short of its goal pushing with 10 counts of current, over the 6 the feel needs (4 before).
- *Held*: at 97 poses both ways; one lying block (2 cm ahead and to the right, turn 0) held only before -
  it crept 2.14 mm in the last 2 s (1.85 before), over the 2 mm line; none held only after (exact McNemar
  p = 1.0).
- *Creep in the hold*, held runs, median and most: the cube 0.51 and 1.60 mm (0.29 and 0.85 before), the
  lying block 1.59 and 1.88 (1.41 and 1.85), the standing block 0.03 and 0.21 (0.02 and 0.20).
