# The cell finds its parts with its camera

**Problem.** The factory cell read where each part was from the simulator - known-object sensing
(ADR 0019, OPEN LW-010) - while its overhead camera was only a view. FR-011, accepted on 3 October,
asked for the cell's camera to find its parts; ADR 0032 did it for the Fetch table and left the
cell. Now parts come to the cell off their places: put by hand off the tray's centre (ADR 0056), or
up to 4 mm from their place at the conveyor's stop (ADR 0068). And measured on the way: from its
home pose the Panda hangs its wrist 5 cm under the camera - from there the camera sees only the arm.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo casts the camera's rays
(`mj_multiRay`, the adapter's `cast`); ADR 0032 built the rest - a RealSense D435's pixels and stereo
noise, and a box finder that takes away the surface the part stands on, gathers what stands on it and
fits the part's known size. The cell wraps both; nothing new is modelled.

**Unique contribution.**
- *The cell's camera* (`factory/controller.py`, `camera_eye`): the overhead camera as a D435 - 848 x
  480 pixels over 87 x 58 deg, its depth error growing with the square of the distance, 1.8 mm at the
  part's 0.7 m - cast from where the scene's camera hangs, knowing the sizes of the cell's parts as a
  lab knows what it picks.
- *Finding the part* (`FactoryCycle(eye=)`, `locate`): the part is looked for round the source's place
  - on the tray's floor, or on the pallet's top at the stop - and the pick is planned from where the
  camera saw it. The part's pose is never read for the pick; each sighting keeps it beside, for the
  record. A part the camera does not see is not reached for ("The camera does not see the part at
  the source.").
- *Out of the camera's view first* (`view_clear`, the 'clearing' state): rays from the camera to the
  corners of the part's top face; when the arm meets one first, the plan is provisional, and the arm
  first moves to above the destination tray - where the plan takes it anyway - then the camera looks,
  the cell plans again and goes. A run's later parts are looked for with the arm already there.
- *In the window*: "Locate: camera / known" in Real's pick-and-place panel; the task sequence's first
  step reads "Locate product with camera"; the camera's last depth picture in the corner of the view,
  the part's pixels green, with how far from its place it was seen. What's new's "The cell finds its
  parts" runs the conveyor-fed cell with it.

**Blueprint and builder.** Untouched: the camera is the scene's own; finding by camera is the
window's choice, not part of a saved cell.

**Result** (`docs/sweeps/2026-11-04-the-cell-finds-its-parts.md`; 45 runs of six parts, paired by draw with
the parts found from the state):
- *Every part the camera looked for, it found and the cell placed*: 216 of 216 - small and tall blocks,
  by hand on the tray (put off its centre by ±2 mm and ±5 deg, or ±5 mm and ±15 deg) and on the
  conveyor's pallets - as the state found 180 of 180. Each was seen within 1.5 mm of where it was in
  plan, 2.2 mm in height and 4.1 deg in turn; FR-011 asked 5 mm and 5 deg. Every part was left within
  its room, at worst 1.6 mm from its slot's centre (1.1 mm when known); paired by draw, within 1 mm of
  where the known part was left, either way. Cpk along the table 4.0 to 4.4 by hand (10 to 12 known),
  9.0 on the conveyor (9.5).
- *Where its error comes from*: the pixels, not the noise - at 0.75 m a pixel spans 1.7 mm, and an
  ideal depth camera saw the parts no closer (0.68 mm off at the median, 0.45 with the D435's noise
  dithering the edges). On a tray the floor round the part is small among its walls and the height
  is read to 2.2 mm; on a pallet's whole top, to 0.2 mm.
- *What it costs*: a run's first part waits while the arm clears the view - 16.4 s against 13.9 -
  and its later parts are looked for with the arm already out of the way, 12.0 to 12.3 s as known. A
  sighting is about 0.15 s of the cloud's CPU, once a part.

Held by `tests/test_cell_camera.py` (3): on the tray and on a pallet at the stop, the home pose hiding
the part and the arm clearing the view before the camera sees it within 1 mm in plan; a run found by
the camera, its parts put off centre and turned, each seen within 2 mm and 2 deg and placed within
1.5 mm of its slot; and an empty source not reached for. A window test in `tests/test_whats_new.py`
runs What's new's demonstration. Suites on MuJoCo 3.10.0: 1152 passed with a display, 1087 headless.

**Boundaries.** One camera whose pose is exact - no calibration error (ADR 0039's tolerance is the
Fetch table's) - and the D435's stereo error alone: no holes, flying pixels or projected pattern. It
looks once a part, while nothing moves, so no latency is modelled. The turn it sees is not used: the
hand grasps square to the table and squares the part (ADR 0057). The grasp is still felt by contact
and the placement still checked from the state. The clear pose is above the destination tray; a tray
moved where the arm there still hides the source makes the cell say so and stop.
