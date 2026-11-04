# The cell fed by the conveyor — 2026-11-04

ADR 0068 (FR-007). Production runs of the Panda's pick-and-place cell (ADR 0019) fed by the roller
conveyor: six parts each, into the Amber tray's six slots, headless, MuJoCo 3.10.0, 2 ms step. Two
pallets ride the line; each part is picked off its pallet at the stop, and the emptied pallet goes
back to the line's start with the next part on it (a person's move, not simulated). Each part's
arrival is read once its pallet has rested at the stop for 0.1 s - from the pallet's place there -
and its placement where it was left, from the centre of its slot (`FactoryCycle.left`).

Where the person puts each part on its pallet: at the nest's centre, or a uniform draw of ±1 mm along
the line, ±3 mm across it and ±3 deg (assumed; seeds 1 to 9), within the nest's 2 mm of room each
side - a part that does not fit between the bars is refused.

| Parts | Put on the pallet | Runs | Placed | Arrived at the stop: worst, median | Left: within their room, worst | Cpk x | Cycle |
| --- | --- | --- | --- | --- | --- | --- | --- |
| small blocks | at the centre | 1 | 6 of 6 | 2.0, 2.0 mm | 6 of 6, 0.97 mm | 7.5 | 12.1 to 13.9 s |
| small blocks | ±1 mm, ±3 mm, ±3 deg | 9 | 54 of 54 | 3.9, 2.6 mm | 54 of 54, 0.96 mm | 9.5 (7.7-11.3) | 12.1 to 13.9 s |
| tall blocks | at the centre | 1 | 6 of 6 | 2.0, 2.0 mm | 6 of 6, 0.75 mm | 13.9 | 12.1 to 13.9 s |
| tall blocks | ±1 mm, ±3 mm, ±3 deg | 3 | 18 of 18 | 3.7, 2.4 mm | 18 of 18, 0.74 mm | 17.0 | 12.1 to 13.9 s |

Every part was picked and placed: 84 of 84. Each arrived within 4 mm of its place at the stop -
along the line no further than its front bar (2.0 mm), across where it was put (within 1 mm). Every
part held the tightest zone tried, ±1 mm (95 % lower bound 94.6 % for the 54 drawn small blocks). The
first part of a run waits 0.25 s for its pallet to settle at the stop; every later pallet was
already there when the arm came back (waits 0.10 to 0.26 s, the 0.1 s settling included). A part
takes 12.1 to 13.9 s, as fed by hand (ADR 0056).

**Before the nests:** a part riding loose on its pallet slid forward at every stop, 3.4 mm - v^2/2ug
from 0.1 m/s with wood on HDPE (0.15) - and arrived 6.7 to 7.0 mm from its place after the queue and
the stop. **Before the friction rollers:** rollers held at speed slipped under the held pallets, which
shook on them, and a part crept along its pallet: 15 mm in 8 s on the first, 40 mm on the second.

**Frame time:** three-part runs, fed by hand and by the conveyor alternated twice, on the cloud's CPU:
a 2 ms step takes 0.39 ms fed by hand (25 contacts on average) and 0.86 ms fed by the conveyor (41) -
nine rollers on hinges with their drives, two pallets with their nests on them. The cell still runs
more than twice as fast as real time.
