# The factory cell's process window — 2026-10-26

ADR 0056 (FR-029). Production runs of the Panda's pick-and-place cell (ADR 0019): six parts from the
input tray to the Amber tray's six slots, headless, MuJoCo 3.10.0, 2 ms step. Each part's placement
is read where it was left, from the centre of its slot, and its cycle from its plan's start to its
placement checked (`FactoryCycle.left`, `factory/process.py`).

The room a part has: the destination tray's slots are 45 mm apart along the table's x and 70 mm
across it, and both parts are 32 mm square, so a part may stray 6.5 mm along x and 19 mm across before
it touches the next slot's part; a centred part may turn 38.9 deg.

The feeder is not simulated (ADR 0019): it puts each part on the input tray's centre. To see how the
cell takes parts that come less exactly, each part was also put off the centre by a uniform draw,
±2 mm and ±5 deg, and ±5 mm and ±15 deg (assumed spreads, nine runs each, seeds 1 to 9).

## Small blocks

| Feeder | Parts | Within their room | Worst off | Mean off (x, y) | Cpk x | Cpk y | Cpk turn | Tightest zone held by every part |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| at the centre | 6 | 6 | 4.8 mm | +3.2, -1.7 mm | 1.05 | 12.6 | 168 | ±5 mm |
| ±2 mm, ±5 deg | 54 | 54 | 5.4 mm | +3.4, -1.7 mm | 1.02 (0.80-1.23) | 12.4 (10.1-14.8) | 58 (47-70) | ±5 mm (54 of 54; 95 % lower bound 94.6 %) |
| ±5 mm, ±15 deg | 54 | 51 | 8.9 mm | +3.9, -1.7 mm | 0.57 (0.43-0.71) | 12.4 (10.1-14.8) | 22 (18-27) | ±10 mm |

Cpk against the room, with the e-Handbook's 95 % interval from 25 parts on. Every part out of its room
was out along x. The hand squares a part fed turned up to 15 deg: none was left turned more than 3.8
deg. Each part took 12.1 to 13.9 s (mean 12.8 s): the cell holds a takt of 14 s, and no shorter.

**Why along x, and why short across:** traced stage by stage on the first part. The arm's tool
stops 4 mm short of every point it is sent to and 4 mm low - the Panda's position servos hold its
weight with no gravity compensation (no `gravcomp`; stiffness 4500, 3500 and 2000 N m/rad) - and
1.9 mm short across the table at the destination. The part is grasped 4.3 mm out from the tool's
centre, as far as the tool stopped short, and creeps 3.3 mm further out in the hand while it is
lifted, carried and lowered: the hand squeezes it with 1.6 N (Menagerie's hand: a position servo of
100 N/m on its tendon), where the Franka Hand's datasheet gives 70 N continuous. Out along x, the
creep and the short stop at the tray nearly cancel the grasp's offset; across, the short stop is the
error.

## Tall blocks

Every run failed - the first at its fifth part, "Placement failed: product is outside the selected
tray" - and every part left was outside its room, 19 to 82 mm off. Traced: while the second part was
released the first was pushed 8 mm across the tray; while the third was lowered into the slot behind
the first it tipped 24 deg in the hand, slid 11 mm in it, came down on the first part's edge and
pushed it 73 mm along the tray.

Why: the cell moves its joints from one pose to the next by interpolating each joint, so the descent
into the tray is an arc, not a line. Halfway down - 80 mm over the drop - the tool was 7.2, 7.4, 15.0,
14.7, 10.5 and 8.9 mm off the vertical through the six slots (small blocks; most along x, at the two
slots nearer the arm). A small part's bottom is then still above its neighbour; a tall part's, 32.5
mm below the tool, meets its neighbour's top edge. And the hand opens fully, 80 mm, to let a part go:
next to a tall part a finger reaches its top (a finger's mesh, 2.7 N), which pushed the first part 8
mm - 29 mm with the stiffer hand of the previews. Opening only to 48 mm let the first two land as
small ones do; the third and fourth still met the arc.

## The two fixes, previewed (not adopted)

The same runs on copies of the model: the arm's links gravity-compensated (`gravcomp` 1), as the
real Panda's controller compensates its weight; the hand squeezing with a force limit (20 N or the
datasheet's 70 N, its fingers' contacts as stiff as an imported gripper's jaws, ADR 0047).

| Small blocks, at the centre | x off (6 parts) | y off | Worst |
| --- | --- | --- | --- |
| as it is | +1.4 to +4.4 mm | -1.0 to -2.2 mm | 4.8 mm |
| gravity compensated | +1.5 to +3.7 mm | -0.4 to -0.1 mm | 3.7 mm |
| gravity compensated, 20 N | +0.4 to +2.1 mm | -0.5 to -0.1 mm | 2.1 mm |
| gravity compensated, 70 N | +0.4 to +2.1 mm | -0.5 to +0.3 mm | 2.1 mm |
| 70 N, not compensated | +26 to +35 mm | -27 to +18 mm, turned 8 to 22 deg | 44 mm |

With both, the tool stops within 0.2 mm of its points and the part still creeps 2 mm out in the hand
(more noslip iterations change nothing: 10 instead of 2, the same to 0.03 mm). The tall blocks' runs
then finish, but the third and fourth parts land 17 to 22 mm off: the fixes do not cure them.

Runs: 38 production runs of six parts (214 parts) and 9 previews; scripts in the session's scratchpad
(`fr029/`).
