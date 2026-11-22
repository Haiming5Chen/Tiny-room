# Grasp bench: arm_lab, found by the camera

Each object at 9 places x 4 turns on a bench 18.7 cm up; approach, close, lift 10 cm, carry 20 cm, hold 2 s; found by the bench's depth camera. Held: lifted and carried, and under 2 mm of slip in the jaws over the last 2 s.

At the 0, 30, 60, 90 deg turns the object's x axis lay 74, 44, 14, 16 deg from the line the jaws close along (0: along it; the median over the places).

| Object | 0 deg | 30 deg | 60 deg | 90 deg | Held | 95 % interval |
| --- | --- | --- | --- | --- | --- | --- |
| cube | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |
| block | 9 of 9 | 8 of 9 | 9 of 9 | 9 of 9 | 35 of 36 | 85 to 100 % |
| block lying | 8 of 9 | 7 of 9 | 9 of 9 | 0 of 9 | 24 of 36 | 49 to 81 % |
| cylinder | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 36 | 0 to 10 % |
| plate | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 36 | 0 to 10 % |

## Why the rest were not held

- block: not lifted (1)
- block lying: not lifted (10); slipped in the jaws (2)
- cylinder: not looked for: the camera finds boxes (ADR 0032) (36)
- plate: the arm cannot close its jaws on it without striking the bench (36)

Held runs slipped 0.01 to 1.86 mm in their last 2 s.

## What the grasp check felt

The program went on as taught whatever its grasp check felt; the check reads the jaws' servos (ADR 0048), not the object.

| Object | held, felt held | held, felt nothing | not held, felt held | not held, felt nothing |
| --- | --- | --- | --- | --- |
| cube | 36 | 0 | 0 | 0 |
| block | 35 | 0 | 1 | 0 |
| block lying | 24 | 0 | 12 | 0 |
| cylinder | 0 | 0 | 0 | 0 |
| plate | 0 | 0 | 0 | 0 |

It felt 95 of the 95 held runs held, and 13 of the 13 others.

## How it was run

`python -m little_world.inventory.graspbench --design arm_lab --jobs 2 --camera` (ADR 0077): a RealSense
D435's depth camera 45 cm beyond the bench and 78 cm over it; for each pose the program is solved for
the bench's middle at the object's turn, looks for the object there and reaches where the camera saw
it - up to 2.8 cm away - and carries it to the place 20 cm from the middle. The template takes hold as
ADR 0078 has it.

## Against the known pose

The same 180 poses known (docs/sweeps/2026-11-22-grasp-bench-squeeze-first.md):
- *What the camera missed*: nothing. It found every box at every pose; the cylinder it does not look
  for - its finder knows boxes (ADR 0032) - and the plate is out of the pads' reach either way.
- *What its error cost*: held at 94 box poses both ways, 3 only known and 1 only found (exact McNemar
  p = 0.63). The standing block 2 cm ahead and to the left, turn 30, was taken by its corners a few
  millimetres from where the known program took it, felt held, and left on the bench as the arm lifted;
  the three lying blocks that differ crept 1.83 to 2.14 mm in the hold, either side of the 2 mm line.
