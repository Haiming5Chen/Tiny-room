# The cell finds its parts — 2026-11-04

ADR 0069 (OPEN LW-010; FR-011 for the cell). Production runs of the Panda's pick-and-place cell, six
parts each into the Amber tray, headless, MuJoCo 3.10.0, 2 ms step. Each part was found either from
the simulator's state ("known", as before) or by the cell's overhead camera: a RealSense D435's
848 x 480 pixels and stereo noise ("camera"), or the same pixels without noise ("ideal"). Each part
was put by a person's uniform draw - by hand on the input tray, or on its pallet for the conveyor
(ADR 0068) - the same draws for both sensings, by seed. Each sighting is read against the part's
true pose (kept for the record only); each placement where the part was left, from its slot's centre.

| Feeder, parts | Put | Sensing | Runs | Placed | Seen off: in plan, worst (median) | in height | turn | Left: worst, Cpk x |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| by hand, small | ±2 mm, ±5 deg | camera | 9 | 54 of 54 | 1.5 (0.45) mm | 2.2 mm | 3.7 deg | 1.5 mm, 4.0 |
| by hand, small | ±2 mm, ±5 deg | known | 9 | 54 of 54 | - | - | - | 0.9 mm, 12.3 |
| by hand, small | ±2 mm, ±5 deg | ideal | 3 | 18 of 18 | 0.9 (0.68) mm | 1.4 mm | 2.6 deg | 1.6 mm, 3.3 |
| by hand, small | ±5 mm, ±15 deg | camera | 9 | 54 of 54 | 1.2 (0.35) mm | 2.2 mm | 3.1 deg | 1.6 mm, 4.4 |
| by hand, small | ±5 mm, ±15 deg | known | 9 | 54 of 54 | - | - | - | 1.1 mm, 10.2 |
| by hand, tall | ±2 mm, ±5 deg | camera | 3 | 18 of 18 | 1.2 (0.61) mm | 2.0 mm | 4.1 deg | 1.6 mm, 3.7 |
| conveyor, small | ±1, ±3 mm, ±3 deg | camera | 9 | 54 of 54 | 0.7 (0.46) mm | 0.2 mm | 2.2 deg | 0.8 mm, 9.0 |
| conveyor, small | ±1, ±3 mm, ±3 deg | known (ADR 0068) | 9 | 54 of 54 | - | - | - | 1.0 mm, 9.5 |
| conveyor, tall | ±1, ±3 mm, ±3 deg | camera | 3 | 18 of 18 | 0.7 (0.37) mm | 0.2 mm | 2.7 deg | 1.2 mm, 10.8 |
| conveyor, tall | ±1, ±3 mm, ±3 deg | known (ADR 0068) | 3 | 18 of 18 | - | - | - | 0.7 mm, 17.0 |

Every part the camera looked for, it found and the cell placed: 216 of 216, against 180 of 180 known.
Each was seen within 1.5 mm of where it was in plan, 2.2 mm in height and 4.1 deg in turn - FR-011
asked 5 mm and 5 deg - and every part was left within its room (6.5 mm along the table). Paired by
draw, a part found by the camera was left as far from its slot's centre as when it was known, within
1 mm either way (medians -0.05 and +0.01 mm by hand, -0.31 mm on the conveyor).

**Why the hand-fed parts are seen less well in height:** on the input tray the floor round the part is
a small part of the picture among the tray's walls, and the support plane is fitted to it; on a
pallet the plane is the pallet's whole top. **Why an ideal camera is no better:** at 0.75 m a pixel
spans 1.7 mm; the top face's edges fall between pixels, and the D435's noise dithers them - without
it, a part was seen 0.68 mm off in plan at the median, against 0.45 with it.

**The time it costs:** the first part of each run waits while the arm clears the camera's view - its
cycle 16.4 s against 13.9 known - and every later part is looked for with the arm already above the
destination tray: 12.0 to 12.3 s, as known (12.0 to 12.2). A sighting is about 0.15 s of the cloud's
CPU (some 22,000 rays), once a part.
