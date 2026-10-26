# The factory cell judged by its process window: where each part lands, how long it takes

**Problem.** A production run (ADR 0019) counted the parts placed and checked that each was inside
its tray, 8 cm by 7 cm round the tray's centre. A factory asks more of a cell: that each part lands
inside its fixture's tolerance zone, and that none takes longer than the takt - the available
production time divided by the demand (Lean Enterprise Institute, Lean Lexicon). Neither was
measured, and nothing in the window said either (FR-029, from the weekly reading of 21 October:
LIBERO-Industry, arXiv 2610.16782). Measured now, the cell's small blocks land 1.4 to 4.4 mm out
along the table and 1.0 to 2.2 mm short across it, and its tall blocks fail the run.

**Does an existing simulator solve it? Can we wrap it?** The measures are the factory's own: Cpk =
min(USL - mean, mean - LSL) / 3 sigma, at least 1 wanted, with an approximate interval valid from
about 25 values (NIST/SEMATECH e-Handbook of Statistical Methods, 6.1.6), and a one-sided
Clopper-Pearson bound on a share. They are a few lines of the standard library; there is nothing to
wrap. The runs are the cell's own (ADR 0019).

**Unique contribution.**
- *Where each part was left* (`FactoryCycle.left`, `factory/controller.py`): once its placement is
  checked, each part is read from the centre of its slot - along the table's x and across it, in
  millimetres - turned from square to its tray, and with its cycle, from its plan's start to the
  check. A run keeps them (`run['placements']`); a single cycle its last (`placement`).
- *The room a part has* (`factory/process.py`, standard library): the destination tray's slots are
  45 mm apart along x and 70 mm across, the parts 32 mm square - so a part may stray 6.5 mm along x
  and 19 mm across before it touches the next slot's part, and turn 38.9 deg. The zone is derived
  from the cell, not assumed. `judge` counts the parts within it, the worst, the mean offset, Cpk per
  axis with its interval and the cycles longer than a takt; `tightest` finds the tightest zone held,
  with its Clopper-Pearson bound.
- *A feeder's spread* (`FactoryCycle.feeder`): where the feeder - not simulated - puts each part on
  the input tray, off its centre and turned; none by default, as before.
- *In the window*: under the cell, during a production run, a line says how many parts landed within
  their room, the worst against the room it had, and the slowest part. What's new runs it (ADR 0055):
  "Six parts, measured" takes the app to Real's cell, small blocks, and starts the run.

**Blueprint and builder.** Untouched: no change to the cell, the trays or the robot.

**Result** (`docs/sweeps/2026-10-26-factory-process-window.md`; 38 runs into the Amber tray, 214 parts):
- *Small blocks.* All six parts at the feeder's centre land within their room: 1.4 to 4.4 mm out
  along x, 1.0 to 2.2 mm short across, worst 4.8 mm; Cpk along x 1.05 - capable, barely - across 12.6.
  With the feeder off by ±2 mm and ±5 deg, 54 of 54 within their room, Cpk x 1.02 (0.80 to 1.23); by
  ±5 mm and ±15 deg, 51 of 54, Cpk x 0.57 (0.43 to 0.71), every miss along x. The hand squares a part
  fed turned up to 15 deg (none left turned more than 3.8 deg). The tightest zone every part held is
  ±5 mm (±10 mm at the wider spread). Each part takes 12.1 to 13.9 s: the cell holds a 14 s takt, and
  no shorter. The Franka Panda's own repeatability is ±0.1 mm (ISO 9283, its datasheet): the cell's
  spread is the simulation's, not the arm's.
- *Why.* The arm's tool stops 4 mm short of each point and 4 mm low: the Panda's position servos hold
  its weight with no gravity compensation, which the real arm's controller provides. The part is
  grasped 4.3 mm out from the tool's centre and creeps 3.3 mm further in the hand as it is carried:
  the hand squeezes 1.6 N (Menagerie's position servo, 100 N/m on its tendon), where the Franka Hand's
  datasheet gives 70 N continuous.
- *Tall blocks.* Every run failed, at its fifth part ("Placement failed: product is outside the
  selected tray"); every part left was outside its room, 19 to 82 mm off: the third part tipped 24 deg
  in the hand as it was lowered beside the first and pushed it 73 mm along the tray. Traced: the
  descent into the tray is an arc of the joints, not a line - halfway down the tool is 7 to 15 mm off
  its slot's vertical, most at the slots nearer the arm - so a tall part's bottom catches the top edge
  of the part beside it; and the hand opening fully (80 mm) to let go strikes the next tall part with
  a finger (pushed 8 mm).
- *Two fixes, previewed on copies and not adopted* - they change the Panda in every Real experiment,
  the owner's call (OPEN LW-036): gravity compensation alone takes the error across to under 0.5 mm;
  with a squeeze of 20 or 70 N as well, small blocks land 0.4 to 2.1 mm out, worst 2.1 mm; the squeeze
  without the compensation sends parts 32 to 44 mm off. With both, the tall blocks' runs finish, but
  two parts still land 17 to 22 mm off: the arc remains (OPEN LW-037).

Held by `tests/test_process_window.py` (5): the room from the slots' pitch and the part's width, and
the turn that reaches the next slot; Cpk and its interval as the e-Handbook gives them; the one-sided
Clopper-Pearson bound; a window's counts, worst, bias, takt and line; a production run that records
where each part was left and places a part the feeder put 3.6 mm off and turned 10 deg, squared. In
`tests/test_whats_new.py`, a window test: What's new's factory demonstration runs Real's cell and
its first two parts land within their room. Suites on MuJoCo 3.10.0: 1098 passed with a display, 1042 headless.

**Boundaries.** The feeder is still not simulated: its spreads are assumed draws, and the cell grasps
from the part's true position (ADR 0019's ideal observation). The zone is the slots' clearance - a
real fixture's tolerance is usually tighter, which the tightest-zone figure answers. Placements are
read once each part is checked, the parts after it left out. One cell, one tray, two products, nine
draws a spread. The takt is the slowest cycle seen, not a line's demand. The fixes are previews: no
claim that the remaining 2 mm creep is the real hand's; the arc and the full opening are traced, not fixed.
