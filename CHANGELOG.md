# Changes

What changed for someone who uses Little World, newest first. Every change has a decision record
in [docs/adr/](docs/adr/); what each feature is and how it was measured is in
[docs/FEATURES.md](docs/FEATURES.md).

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
