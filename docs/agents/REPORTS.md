# Reports

Each agent's report of a working session, newest first, written before it stops. Facts for
the owner: what was done, what was measured, what is unfinished. Template:

```
## YYYY-MM-DD · agent · what the session was for
Did: what changed, with commits and decision records.
Measured: the numbers that matter.
Unfinished: what is not done, not committed or doubtful (OPEN item numbers).
For the owner: decisions or questions only the owner can settle.
```

## 2026-10-01 · Claude (Cowork) · OPEN LW-001 to LW-003: wheel contacts across MuJoCo releases
Did: ADR 0022. The stance margin is measured from the shapes of the geoms that touch the
floor, not from the contact points MuJoCo reports (LW-002). The caster curb checks moved off
the caster's radius: 18 mm against 24 mm, plus a check that the answer does not depend on
the curb before it, recorded as expected to fail before MuJoCo 3.8 (LW-001). The tilt-table
difference named by running all twelve releases from 3.4 to 3.14 (LW-003). `curb_run(heights)`
builds the Curb run with other heights.
Measured: margin 3.39 cm on 3.3.7 and 3.40 on 3.14, predicted 3.37. On 3.3.7 a 10 mm curb
first turns the caster's answers upside down (stops at 18 mm, climbs 24); 3.14, and 3.3.7
with multiccd, answer consistently. Tilt: the box-box collider changes (the tread blocks
are boxes) account for -1.3 deg, multicontact for the caster's cylinder -1.0, the multiccd
default +0.4. On 3.3.7: 609 passed with a display, 573 headless, 1 expected failure; on
3.14 the headless suite: 574 passed.
Unfinished: nothing from these three.
For the owner: the whole headless suite now passes on MuJoCo 3.14, so the upgrade (LW-004)
is yours to decide. The Curb run's 20 mm curb sits on the caster's radius (LW-015).
Switching multiccd on in 3.3.7 would make the curb answers consistent but adds 5 % to the
coast-down test's deceleration, so it stays off.

## 2026-10-01 · Claude (Cowork) · agent notes reworked
Did: the agent notes now say that the owner decides and agents report: `AGENTS.md`
rewritten; the work log became `REPORTS.md` (no instructions for other agents); the
backlog became `OPEN.md`, a list of what is unfinished and who found it, with no claims or
owners.
Measured: both suites pass (see STATE.md).
Unfinished: nothing from this session.

## 2026-09-29 · Claude (Cowork) · static-test view, radar page, agent notes
Did: the tilt table has its own view while it runs and in the report: the table angle on
a gauge with the design's predicted tipping angle, the goals as chips, no drive
telemetry; the table counts as ground. A Doorway program template (three stops). The
radar's digest is shorter (verdicts and reasons first) and has a page (`digest --html`)
with a verdict filter and a chart of MuJoCo's releases. Agent notes and
`scripts/agent_status.py`. Unused imports removed across the tree (a linter found 54).
Commits d7c5854, d6bf688, 291ad4d, 30012c6.
Measured: the manipulator tips at 54.2 deg on the redrawn table stand (unchanged); the
doorway program: through at 14.5 s, parked at 16.7 s, frame untouched. Suites: 609 with a
display, 573 headless.
Unfinished: OPEN LW-001 to LW-003 stand between the project and a MuJoCo upgrade.

## 2026-09-27 · Claude (Cowork) · doorway, tilt table, frontier radar
Did: ADR 0020 (doorway and tilt table, tip angles by rocking on a tilted floor), ADR 0021
(frontier radar: feeds, profile from the decision records, tf-idf filing, SQLite store,
digest, triage). First radar run: 302 items, 48 filed, 23 judged. Commits 159d6fc, 85e5c4a.
Measured: the mobile manipulator tips at 54.2 deg, predicted 54.3 (55.8 at the rail);
without a rail at its wheels it slides from 16 deg. MuJoCo 3.14 trial: 565 of 568 headless
tests pass; the three that move all involve a cylinder wheel in contact (docs/RADAR.md).
Unfinished: OPEN LW-001 to LW-014.
For the owner: whether and when to upgrade MuJoCo (LW-004); radar phase two (LW-012).

## 2026-09-25 · Claude (Cowork) · physics from sources, test drive, fields, arm tasks
Did: ADR 0010 to 0019 - contact-pair friction from cited sources, drivetrain losses from
the Pololu datasheet, the test drive with telemetry and run reports, test fields with goals,
servo damping integrated by the solver, machine structure and stance, arm tool moves and
taught poses, friction that holds (noslip), driving to a point and the Fetch task, and the
factory's production run.
Measured: see each record's Result and docs/VALIDATION.md.

## Before 2026-09-25 · Codex · the application
Did: the one-window app (Real and Anime workspaces), the Blueprint core, the MuJoCo
adapter, the kit catalogue, Menagerie robots, socket docking, the program editor, the
inventory with A/B trials and the first factory cell: decision records 0001 to 0009,
imported as the repository's first commit.
