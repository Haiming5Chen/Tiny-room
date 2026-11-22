# Grasp bench: arm_lab

Each object at 9 places x 4 turns on a bench 18.7 cm up; approach, close, lift 10 cm, carry 20 cm, hold 2 s; known pose. Held: lifted and carried, and under 2 mm of slip in the jaws over the last 2 s.

At the 0, 30, 60, 90 deg turns the object's x axis lay 74, 44, 14, 16 deg from the line the jaws close along (0: along it; the median over the places).

| Object | 0 deg | 30 deg | 60 deg | 90 deg | Held | 95 % interval |
| --- | --- | --- | --- | --- | --- | --- |
| cube | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |
| block | 9 of 9 | 9 of 9 | 9 of 9 | 9 of 9 | 36 of 36 | 90 to 100 % |
| block lying | 9 of 9 | 8 of 9 | 9 of 9 | 0 of 9 | 26 of 36 | 55 to 86 % |
| cylinder | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 36 | 0 to 10 % |
| plate | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 9 | 0 of 36 | 0 to 10 % |

## Why the rest were not held

- block lying: not lifted (10)
- cylinder: not lifted (36)
- plate: the arm cannot close its jaws on it without striking the bench (36)

Held runs slipped 0.00 to 1.85 mm in their last 2 s.

## What the grasp check felt

The program went on as taught whatever its grasp check felt; the check reads the jaws' servos (ADR 0048), not the object.

| Object | held, felt held | held, felt nothing | not held, felt held | not held, felt nothing |
| --- | --- | --- | --- | --- |
| cube | 29 | 7 | 0 | 0 |
| block | 30 | 6 | 0 | 0 |
| block lying | 26 | 0 | 10 | 0 |
| cylinder | 0 | 0 | 0 | 36 |
| plate | 0 | 0 | 0 | 0 |

It felt 85 of the 98 held runs held, and 10 of the 46 others.

## How it was run

`python -m little_world.inventory.graspbench --design arm_lab --jobs 2 --out FILE` on 9d1d3c2 and the
bench (FR-043, ADR 0077), MuJoCo 3.10.0 with multiccd off, 180 runs in 6 minutes on two cores. The
program is the arm lab's pick-and-place template solved for each pose; it goes on as taught whatever
its grasp check feels.

## What the runs show

- *The arm lab's jaws do not turn.* Its joints are its base, shoulder, elbow and wrist - no wrist
  roll - so its jaws close across the line from its base: at the bench's middle along a line 74.5 deg
  from x, at the grid's places 70 to 78. The turns are turns against the jaws.
- *The lying block by its ends* (16 deg, turn 90): felt held, it turns 40 deg in the jaws as it is
  carried - along its length - tips 9 deg in the hold and slides out of the jaws onto the floor, 1.8
  s into it; 9 of 9. At 14 deg on the other side (turn 60) it turns 36 deg on the carry, 30 deg off
  its length, stays level and is held, 9 of 9. Across the jaws (74 deg) it is held 9 of 9. This is
  OPEN LW-034's loss, at one of its two angles. Held, it creeps 0.6 to 1.9 mm in the jaws in the last
  2 s.
- *The grasp check feels the jaws arrive, not the hold* (OPEN LW-056). The 1 s close's target ends
  2 or 3 pulses past a 25 mm face; a jaw resting there pushes with 4 counts of current, under the 6
  the feel needs (ADR 0048). A cube or block turned 30 deg meets the jaws by its corners, is turned
  square before the check begins at 5.0 s, and is not felt - 13 of 18, every one held.
- *The cylinder* (OPEN LW-057): with multiccd off each pad touches it at one point, one at its top
  rim and the other near its foot, and closing they push it 10 mm towards the arm, out of the grip.
  With multiccd on the pads hold it by several points and lift it 9 cm; it falls from them as the
  carry begins.
- *The plate*: the pads are 35 mm tall about the tool point; kept 5 mm over the bench they meet a
  6 mm plate nowhere, and the bench does not try.
