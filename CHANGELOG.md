# Changes

What changed for someone who uses Little World, newest first. Every change has a decision record
in [docs/adr/](docs/adr/); what each feature is and how it was measured is in
[docs/FEATURES.md](docs/FEATURES.md).

## Unreleased

- The Inventory's new tab, *What it can do*: an example's measured limits - the kit cart's curb, the
  arm cart's held tilt table and its reach - and for any other design the commands that would measure
  it (ADR 0076).
- How far a design can go, the fourth factor: a ramp's slope. The two-wheel robot climbs to 5 deg;
  the kit cart climbs none, its drive wheels lifted by its casters. With 18 set-ups a level instead of
  9, a crossing's interval narrows as statistics say it should (ADR 0076).
- A grasp bench: five diagnostic objects at 36 poses each, through the arm lab's pick-and-place
  program, judged by the object. The cube and the kit's block standing are held everywhere; the block
  lying is lost whenever the jaws take it by its ends, the cylinder and the thin plate always. What's
  new's *By its ends, it falls* shows the lying block's case, and the Inventory's *Grasp bench* tab
  shows the arm lab's table and runs the bench on any design. With a depth camera finding each object
  instead of its known place, the arm lab drops what it dropped before: the camera finds every box.
  Its report says how close each grip came to slipping, and a robot from the library takes it too: the
  Panda holds the cylinder the kit's jaws cannot, and with its wrist turned to each box holds the
  factory cell's parts at every pose, as the cell does (ADR 0077).
- The pick-and-place template squeezes before it checks its grasp. On the grasp bench its check missed
  13 of 18 held cubes and blocks the jaws had turned square before it looked; now it feels every held
  part, and the arm lab's cube reaches the tray 0.02 s later (ADR 0078).
- A robot brought in from its own file has each servo moved once on import, and the report - and the
  Joint lab - say what it moved, or what the file gets wrong: a joint turned backwards, an actuator on
  another joint than its name says, a gripper that does not close. What's new's *A motor wired
  backwards* shows it (ADR 0079).
- `little-world evidence` measures fifteen claims: the grasp bench's lying block and the import probe's
  motor wired backwards are among them (ADR 0073).

## 0.4.0 - 21 November 2026

- The same start, checked: every sweep run keeps a fingerprint of its set-up, and the disturbed
  sweep's and the recovery report check that their pairs began alike before their statistics
  (ADR 0075).
- The run report keeps an estimated tip apart from one seen: the stance margin and the degrees from
  tipping are marked as estimates, and only a tilt past 60 deg says a machine tipped over (OPEN
  LW-048; ADR 0059 amended).
- Windows: the quick tier and the quick measurements pass there, as on macOS and Linux, and on
  GitHub a failed test is written where anyone can read it (OPEN LW-045).
- How far a design can go: one factor stepped along a grid - a curb's height first - and where a
  design's success falls through one half, with an interval (ADR 0076). The kit cart's profile shows
  how much of its curb climbing the engine's energy from nowhere gives it (OPEN LW-047). The second
  factor, a tilt table's angle, shows that the table's climb reads a machine late: held, the arm cart
  stands to 50 deg as designed, where the climb reads it going over at 54.6 - and `little-world
  evidence` records that as a flaw of its tilt claim (OPEN LW-053). What's new shows it: *Held, it
  goes over sooner*. The third, the Fetch's cube moved back, counts what the program tried apart from
  what it met: it reaches up to 6 cm and declines from 7, and no reach it tries fails.
- Windows again: every text file the app opens is read and written as UTF-8 - a build script with a
  comment in Chinese saves there now - and GitHub's workflows run on actions that use Node.js 24
  (OPEN LW-051). A window test that read the grip at its frames reads it every step (OPEN LW-054).

## 0.3.0 - 12 November 2026

- A physics check in every run: a contact that gives back more energy than it took is the engine
  making energy, and the drive panel, the run's report and every sweep report say so. On the Curb
  run it gives the kit cart 78 mJ at a curb's edge; What's new shows it (ADR 0074).
- `little-world evidence` measures thirteen headline claims: the physics check's controls are the
  thirteenth, and the Curb run's claim records the energy its climb is given, as a flaw.
- The frontier holds the weekly reading of 9 November (FR-040 to FR-044); the roadmap no longer
  says MuJoCo 4.0 has a wheel for Intel Macs.

## 0.2.0 - 11 November 2026

The first version since the import of 24 September, with seven weeks of work in it.

- `little-world`: one command for the window, its demonstrations (`demo`), the builder (`build`),
  an installation check (`doctor`) and the project's tools (ADR 0072).
- `little-world evidence`: a dozen headline measurements re-run on your machine against the
  recorded numbers; a quick test tier, `pytest -m "not slow"`; two GitHub workflows (ADR 0073).
- The README is the short way in; its lists are `docs/FEATURES.md` and `docs/MANUAL.md`.
  [docs/EVALUATION.md](docs/EVALUATION.md) says what holds, what does not and where the project
  went wrong.
- Since September (ADR 0010 to 0071): sourced contact friction and motors, test drives and
  eleven test fields, block programs that look with a depth camera, feel with their servos and
  look again, sweeps with disturbances and held-out draws, a factory cell fed by a conveyor and
  found by a camera, robots imported from URDF or MJCF, first-hour lessons, What's new.

## 0.1.0 - 24 September 2026

The first public import: the builder, the Blueprint format, the workshop room, Real and Anime
workspaces (ADR 0001 to 0009).
