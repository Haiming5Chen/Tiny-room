# The cell fed by a conveyor, on friction rollers

**Problem.** The factory cell's feeder was not simulated: a production run moved each next part
onto the input tray (ADR 0019, OPEN LW-005). ADR 0067 built a roller conveyor as a test field and
left FR-007's cell undone. Run longer than its test, that conveyor showed two things. Its rollers
are held at speed, so they slip under a pallet the stop or the queue holds: the pallet shakes on
them, up and down at up to 4 cm/s, and what it carries creeps forward - the kit's cube 6 mm on the
first pallet and 31 mm on the second between 2 and 10 s (OPEN LW-042). And a part riding loose on a
pallet slides at every stop: from 0.1 m/s, a wooden part on HDPE (friction 0.15, ADR 0010) slides
v^2/2ug = 3.4 mm - measured 3.4 mm a stop, 6.8 mm after the queue and the stop, past the 5 mm
FR-007 asks a part to arrive within.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo carries the pallets by contact
friction (ADR 0067); what it cannot say is how a real line accumulates. Interroll's planning basics
for conveyor rollers do: friction rollers, whose drive turns the tube through a slip coupling. "When
materials are stopped, the rollers will also stop. The drive of the friction rollers continues to
turn in this case", and the force a drive passes "regulates itself relative to the weight of the
conveying good" - 4 to 6 % of the roller's load for a 50 mm roller with a friction element on one
side. A workpiece pallet locates its part in a fixture, so it does not slide.

**Unique contribution.**
- *Friction rollers* (`fields/conveyor.py`, standard library): each roller's drive passes at most
  5 % of the load a pallet and its part put on it - its share over a pallet's 55 mm of 160, a torque
  limit of 1.6 mN m - and its velocity servo turns it at 0.1 m/s within that. Under a held pallet the
  rollers stand still while their drives turn on: no shaking, no creep (LW-042 done).
- *A line laid out anywhere* (`Line`): where its first roller is, which way it carries along x, the
  height of its rollers' tops and the entity its parts are in. The field's line is ADR 0067's, part
  for part; its side frames now stand 10 mm under the rollers' tops.
- *The cell's feeder* (`factory/scene.py`, `factory_scene(feeder='conveyor')`, `conveyor_line`): the
  conveyor stands on the cell's table and carries towards the robot along -x, its stop holding a
  pallet centred on the source tray's place - the tray is not built. Where it would run off the
  table, cross a tray or a camera post, or reach within 20 cm of the robot along x, it says so. Two
  pallets ride it, each locating its part between two bars across the line, 2 mm of room each side
  of the 32 mm part: the fingers close across the line, between the bars. The run's other parts wait
  on the stock shelf.
- *The cell's run* (`factory/controller.py`, `FactoryCycle(line=)`): the rollers are driven every
  step, the cell running or not. A run waits for each part's pallet to rest at the stop for 0.1 s,
  plans the pick from where the part is - known-object sensing, as before - and lowers it into its
  slot from the pallet's height. Once the part is lifted, its pallet goes back to the line's start
  with the next waiting part on it, and the pallet behind rides up to the stop: the return and the
  loading are a person's, one move, not simulated. Where each part arrived at the stop is noted.
- *In the window*: Real's pick-and-place panel has "Conveyor: on / off" beside "From:"; a run's lines
  add where the parts arrived and the longest wait. What's new's "The cell fed by a conveyor" runs
  six parts.

Traced on the way: the hand lowering a part into the near row of the Amber tray caught the top edge
of the conveyor's side frame and set the part down 3 mm out along the table; the frames now stand
10 mm under the rollers' tops, and the arm touches nothing but its part.

**Blueprint and builder.** A cell's scene is built by `factory_scene` as before; fed by hand it is
unchanged. The feeder is the window's choice, not part of a saved cell (its recipe is still version
1). A pallet's bars are welded children of its body, a shape any Blueprint can have.

**Result** (`docs/sweeps/2026-11-04-cell-fed-by-the-conveyor.md`; 14 runs of six parts):
- *Fed by the conveyor, every part is picked:* 84 of 84 - small and tall blocks, put on their pallets
  at the nest's centre or by a draw of ±1 mm along the line, ±3 mm across and ±3 deg. Each arrived
  within 3.9 mm of its place at the stop: along the line no further than its front bar, 2.0 mm, and
  across where it was put. Each was left within 1.0 mm of its slot, Cpk along the table 9.5 (7.7 to
  11.3) for the 54 drawn small blocks; a part takes 12.1 to 13.9 s, as fed by hand (ADR 0056). Every
  pallet but a run's first was at the stop when the arm came back.
- *Friction rollers:* on the field, the rollers under the held pallets stand still and the others
  turn at 0.1 m/s; the cube on the first pallet stays put (it crept 0.7 mm a second, the second's
  3.8). The pallets are carried at 0.0999 m/s, as before, and come to rest at 1.72 and 1.92 s (1.56
  and 1.76): a drive passing a twentieth of the load brings a pallet up to speed more gently.
- *Frame time:* a 2 ms step of the cell takes 0.86 ms fed by the conveyor and 0.39 ms fed by hand
  (41 contacts against 25; three parts each, alternated, on the cloud's CPU): the conveyor more than
  doubles the cell's cost, which still runs more than twice as fast as real time.

Held by `tests/test_cell_conveyor.py` (3): a friction roller's drive and its limit; the conveyor in
the source's place, the trays and table it must keep off, the pallets, their nests and the parts on
them; a three-part run fed by the conveyor - each part placed within 1.5 mm, arrived no further than
its bar, its pallet there when the arm came back, the arm touching nothing but its parts, the
emptied pallets back on the line, and a part that does not fit its nest refused. The field's run in
`tests/test_conveyor.py` now holds that the rollers under its held pallets stand still and the cube
on the first stays put. A window test in `tests/test_whats_new.py` runs the fed cell from What's
new. Suites on MuJoCo 3.10.0: 1148 passed with a display, 1084 headless.

**Boundaries.** The return of an emptied pallet and the loading of the next part are a person's -
one move, not simulated - and the parts waiting are on the shelf, not on a line upstream. A friction
roller's limit is set once from a pallet and its part, not from the load on each roller each step;
5 % is the middle of Interroll's 4 to 6 %, which it calls non-binding. One stop, no zones, no
sensors but the state's; the line's speed is fixed. A nest is two bars along the line: a part is
free across it, and a person's spread was drawn within the bars, assumed. The feeder choice is not
saved with the cell.
