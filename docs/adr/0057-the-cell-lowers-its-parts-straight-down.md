# The cell lowers its parts straight down and lets go with a narrow hand

**Problem.** Judged by its process window (ADR 0056), the factory cell failed every production run
of tall blocks at its fifth part, every part left 19 to 82 mm off its slot (OPEN LW-037). Traced: the
cell moved its joints from one pose to the next, each joint at its own pace, so lowering a part into
the destination tray was an arc - halfway down, 80 mm over the drop, the tool was 7 to 15 mm off its
slot's vertical, most at the slots nearer the arm. A small part's bottom is then still above the
part beside it; a tall part's, 32.5 mm below the tool, met its neighbour's top edge, tipped 24 deg in
the hand and pushed the first part 73 mm along the tray. And the hand opened fully, 80 mm, to let a
part go: beside a tall part, a finger reached that part's top and pushed it 8 mm.

**Does an existing simulator solve it? Can we wrap it?** Industrial controllers move a tool along a
straight line on request - a linear move, as MoveIt's Cartesian path or a robot's own linear motion
command - and ADR 0045 does it for the kit's arms. Here the cell's own solver (ADR 0019) is reused:
the line is solved a centimetre at a time, each solution from the one before.

**Unique contribution.**
- *Straight up and down* (`factory/controller.py`): the four stages that move the tool vertically -
  lowering to grasp, lifting, lowering into the tray, retracting - carry joint solutions a centimetre
  apart along their line (`Stage.path`, `LINES`, `STEP`), and the stage moves through them
  (`FactoryCycle.along`); the transfer between trays and the approach, high over everything, still go
  joint by joint. The preview path shows the lines.
- *A narrow hand to let go* (`release_grip`): the hand opens 8 mm past the part on each side to
  release it and to retract, 48 mm for the kit's blocks, not the full 80 mm; it still opens fully over
  the input tray, where the part is alone.

**Blueprint and builder.** Untouched: the cell, the trays and the robot are as they were.

**Result** (`docs/sweeps/2026-10-26-factory-process-window.md`, the same 38 runs again):
- Lowered into the tray, the tool now keeps within 5 mm of its slot's vertical all the way down -
  the 4 mm the arm sags under its servos (OPEN LW-036) - where halfway down it had swung 7 to 15 mm.
- *Tall blocks*: every run finishes, and every one of the 114 parts lands within its room - 2.2 to
  6.0 mm out along the table, 1.1 to 2.4 mm short across, worst 6.3 mm; Cpk along x 1.08 fed at the
  centre, 1.04 (0.82 to 1.25) fed ±2 mm and ±5 deg off, 0.85 (0.67 to 1.04) at ±5 mm and ±15 deg.
  Before, no run finished and no part was within its room.
- *Small blocks*: 114 of 114 within their room, where 111 were; at the wider spread Cpk along x 0.90
  (0.71 to 1.09), from 0.57 (0.43 to 0.71); 1.27 (1.01 to 1.52) at the narrower, from 1.02. A part
  takes 12.0 to 13.9 s, 12.4 s on average (12.8 before): the lines are no longer than the arcs.
- With LW-036's two fixes previewed on top (gravity compensation, a 70 N squeeze), both products land
  1.5 to 2.5 mm out along the table and within 0.4 mm across.

Held by `tests/test_straight_descent.py` (3): the four vertical stages solved a centimetre at a time,
their line within 1 mm of the vertical through the point; the hand opening 48 mm to let go, fully
over the input tray; and a tall-block production run of six parts, every part within its room and the
tool within 5.5 mm of the vertical while lowered. Suites on MuJoCo 3.10.0: 1101 passed with a display, 1045 headless.

**Boundaries.** The lines are vertical moves only; the transfer still swings, high over the parts.
Nothing checks collisions along any path. The opening is sized on the part's width across the
fingers, from its known size (the cell's ideal observation). The arm still sags and the hand still
squeezes 1.6 N (LW-036, the owner's call); the parts still land 2 to 5 mm out along the table.
