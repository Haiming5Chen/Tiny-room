# Work log

Newest first. One entry per working session, written before the agent stops. Template:

```
## YYYY-MM-DD · agent · what the session was for
Done: what changed, with commits and decision records.
Measured: the numbers that matter.
Open: what is unfinished, uncommitted or doubtful; backlog IDs.
Next: what the next agent should do first.
```

## 2026-09-29 · Claude (Cowork) · handoff kit, static-test view, radar page
Done: agent handoff kit (`AGENTS.md` as the guide, `CLAUDE.md`, `docs/agents/`,
`scripts/agent_status.py`, `tests/test_agent_docs.py`). The tilt table now has its own
view while it runs and in the report: the table angle on a gauge with the design's
predicted tipping angle, the goals as chips, no drive telemetry; the table counts as ground.
A Doorway program template (three stops). The radar's digest is shorter (verdicts and
reasons first) and has a page (`digest --html`) with a verdict filter and a chart of
MuJoCo's releases. Unused imports removed across the tree (a linter found 54).
Measured: manipulator tips at 54.2 deg on the redrawn table stand (unchanged); doorway
program: through at 14.5 s, parked at 16.7 s, frame untouched. Suites: 609 with a display,
573 headless.
Open: LW-001 to LW-003 before any MuJoCo upgrade.
Next: LW-001 and LW-002 are small and unblock the upgrade.

## 2026-09-27 · Claude (Cowork) · doorway, tilt table, frontier radar
Done: ADR 0020 (doorway and tilt table, tip angles by rocking on a tilted floor), ADR 0021
(frontier radar: feeds, profile from the decision records, tf-idf filing, SQLite store,
digest, triage). First radar run: 302 items, 48 filed, 23 judged.
Measured: mobile manipulator tips at 54.2 deg, predicted 54.3 (55.8 at the rail); without
a rail at its wheels it slides from 16 deg. MuJoCo 3.14 trial: 565 of 568 headless tests
pass; the three that move all involve a cylinder wheel in contact (docs/RADAR.md).
Open: the fetcher has not met the live feeds (LW-011).
Next: the trial's three differences (LW-001 to LW-003).

## 2026-09-25 · Claude (Cowork) · physics from sources, test drive, fields, arm tasks
Done: ADR 0010 to 0019 - contact-pair friction from cited sources, drivetrain losses from
the Pololu datasheet, the test drive with telemetry and run reports, test fields with goals,
servo damping integrated by the solver, machine structure and stance, arm tool moves and
taught poses, friction that holds (noslip), driving to a point and the Fetch task, and the
factory's production run.
Measured: see each record's Result and docs/VALIDATION.md.

## Before 2026-09-25 · Codex · the application
The one-window app (Real and Anime workspaces), the Blueprint core, the MuJoCo adapter,
the kit catalogue, Menagerie robots, socket docking, the program editor, the inventory with
A/B trials and the first factory cell: decision records 0001 to 0009, imported as the
repository's first commit.
