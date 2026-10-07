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

## 2026-10-07 · Claude (Cowork) · FR-016: the stop follows the cube
Did: the owner picked FR-016. ADR 0035: the Fetch program looks before it drives (the table
camera searching 25 cm round the plan) and its stop at the cube moves as the cube was seen
to have moved - sideways fully, towards the table at most 2.3 cm, the cart's front kept 1 cm
clear of the table's edge as measured from MuJoCo's geometry; the stop it backs off to moves as
that stop did. A `goto` may name the object it drives to (programs version 4); `aim` answers
False for a point out of reach, and a pose re-aimed there fails before the arm moves, saying
how far the cube was seen from its plan. The picture before the jaws go down is of where the
look saw the cube.
Measured: the cube set down before the run - ADR 0032's 14 placements all fetched (13
before); 6 and 7 cm further along, fetched (6 cm was missed); 15 cm to either side, and 6 cm
along with 15 cm to the side, fetched; 8 and 10 cm along refused at the table as out of the
arm's reach (it reaches 28 cm ahead of its axle at the cube's height). Undisturbed, drawn 59
times: 71 of 71, the cube in the bin after 35.9 s median (35.8 s). Disturbed on the same 9 set-ups:
every disturbance 9 of 9, the median changes within 0.6 s of before (a first version that
moved the backing-off stop with the cube's last sighting was 1.3 to 1.8 s slower after a cube
moved at the table, and was changed).
Unfinished: the stop moves without turning, so a cube out of reach from the front is not
approached from another side. One run of the 71 looked again though nothing had moved: the
single picture before the jaws go down missed the cube under them (OPEN LW-022).
For the owner: FR-017 to FR-021 wait for you.

## 2026-10-07 · Claude (Cowork) · the shared log, the brain, and Codex's line of work merged
Did: a766b5f a shared log for the agents (the owner's request); e8cac05 ADR 0034, the brain:
the research collection `docs/radar/collection.jsonl` (81 entries, 69 judged) with
`radar collect`, `recall`, `search`, `related` and `search --check`; the weekly reading of
5 October (re-fired by hand after the scheduled run failed) brought in as FR-017 to FR-021 and
notes on eight older proposals. Then, at the owner's decision (5 October, 19:40 UTC), Codex's
`main` (six commits: Panda teaching, reviewable cell changes, semantic testing with hidden
windows, the factory scene document and layout editing, its shared log) merged into this
branch, copied read-only from the Mac. Thirteen files overlapped and five conflicted; each
kept both sides: `scripts/agent_status.py` is Codex's log code unchanged with this branch's
status summary as the default; AGENTS.md keeps Codex's "Multi-agent coordination" section
word for word; VALIDATION.md keeps both sets of sections; LOG.md holds every event of both
sides in time order. `Publish to GitHub.command` on the Mac now keeps the agents' uncommitted
log lines across its branch switch (git refuses the switch otherwise; the old script is in
`build/`).
Measured: both suites on the merge: 940 passed with a display, 893 headless (700 and 661
before; Codex's line had 695 with hidden windows). Search: words alone answer 17 of 20 test
questions in the top three; a latent-semantic half, 15 to 19 depending on its settings, so
words rank by default.
Unfinished: Codex's reader keeps a byte position, so after a merge that changes the log
before that position it replays the whole log once, with a notice (it will, once, after this
merge). The weekly reading's entries reach the collection only when an agent merges them
(`collect --add`; the brain-context document now asks the weekly run for them in that
shape). `HANDOFF.md`, Codex's record, still says the brain's location is unknown - left as
Codex wrote it; the log says where it is. LW-012 (an embedding model) is still the owner's.
For the owner: run Publish to GitHub.command when you like - it now carries the log; after
it, the Mac's folder is on this branch, which holds Codex's work too. FR-016 to FR-021 wait
for you.

## 2026-10-04 · Claude (Cowork) · FR-015: looking again
Did: the owner accepted FR-015. ADR 0033: at a stop where the program looked, it looks again -
back to the pose it drove in, where the jaws hide nothing, then the look and the reach - when
one more picture just before the jaws go down finds the cube moved or hidden, when a reach
for the cube cannot settle, or when a grasp holds nothing (the jaws opened first); once per
run (`Runner(regrasps=)`, `--regrasps`, `Run.regrasped`, the report's "Looked again").
Measured: built only as proposed (after a missed grasp), it reached 1 of 9 set-ups of "cube
moved 5 cm 2 s later": the other 8 had failed with the jaws down on the moved cube, and the
one had its cube knocked out of reach. With the picture before the jaws go down: 9 of 9,
the jaws never touching the moved cube, 2.6 s later than undisturbed; under the other
disturbances and undisturbed, 9 of 9 each with the same median times and pushes as before.
Suites: 687 passed with a display, 648 headless.
Unfinished: a cube knocked or moved beyond the arm's reach from its stop is seen and not
fetched (LW-021, FR-016 proposed); a second move after the second look is missed (once per
run).
For the owner: FR-016 and the remaining proposals.

## 2026-10-04 · Claude (Cowork) · FR-011: a depth camera at the Fetch table
Did: the owner accepted FR-011 (grasping from a camera, classical first). ADR 0032: an Intel
RealSense D435 on a stand beyond the Fetch table with its maker's numbers; its pictures are
MuJoCo's rays (`MujocoBackend.cast`, no GL context, so the suites stay headless); a classical
finder for known boxes (`perception/`: support plane by RANSAC, clusters standing on it, the
top face laid back along its rays and fitted); a `look` block (programs version 3) whose
sighting re-aims the poses at its stop; the Fetch program looks once stopped, its jaws waiting
short of the cube so as not to hide it. `sweep --blind`, a camera column in the disturbance
report, `python -m little_world.perception` for the camera's accuracy, and the program
workspace shows the camera's depth picture. The tests of ADR 0025, 0030 and 0031 run the
program blind, as they were measured. ADR 0031's broken line fixed.
Measured: the cube at 80 placements (up to 8 cm off, turned up to 45 deg): found in every
picture, within 2.4 mm and 6 deg with the D435's noise (median 1.3 mm, 0.6 deg). Fetch, nine
set-ups, looking: the cube moved 5 cm as the cart stands at the table, 9 of 9 (none
blind); moved 3 cm, 9 of 9; shoved 4 and 6 N s, 9 of 9 each (going back alone lost one each:
the shove knocked the cube with the jaws, which now wait short of it); moved 5 cm 2 s later,
none. Set down elsewhere before the run: 13 of 14 placements fetched looking, 6 of 14 blind.
Looking costs 2.5 s; drawn 59 times undisturbed, it met every goal in all 59, as blind.
Suites: 682 passed with a display, 643 headless. Run blind the same day (a follow-up commit),
the disturbance sweep gave what ADR 0031 measured, set-up for set-up, and none of 9 for the
cube moved 2 s later: the camera stand changed nothing for a program that does not look.
Unfinished: LW-020 (a cube moved after the look is missed; FR-015 proposed), LW-021 (a cube
seen beyond the arm's reach from its planned stop; FR-016 proposed), LW-010 (the factory
cell). A look costs about 0.1 s of computing a picture: on a slow machine the window may
lag while it looks.
For the owner: FR-015 and FR-016, and the remaining proposals (FR-004, FR-005, FR-007,
FR-008, FR-012, FR-013).

## 2026-10-03 · Claude (Cowork) · going back to the stop (LW-019) and the disturbances button (LW-018)
Did: the owner chose these two next. ADR 0031: an aimed pose settling more than 2 cm from
the stop its program drove to sends the program back - the pose it drove in, a 25 cm run-up
behind the stop along its heading, the stop - once per run; runs record it and the
disturbance report counts it. The run report has "Repeat with disturbances" (ADR 0030,
another process, a line per disturbance). Tracing the shoved runs corrected ADR 0030 before
publishing: the grasp check had not passed on the table in those runs (the Fetch check names
the cube); the arm, aimed from where the cart was pushed to, worked at the edge of its reach.
Measured: shoved 6 N s at the table, the arm on a cart fetched its cube in 8 of 9 set-ups (3
of 9 before); shoved 4 N s, 8 of 9 (9 of 9 with corrections alone - the one lost had its cube
knocked over by the shove). Undisturbed, 59 of 59 drawn set-ups with the same times; nothing
went back. Suites: 666 with a display, 628 headless.
Unfinished: LW-018's slippery patch (the owner chose the button only). A cube knocked over
by the shove is not found again (FR-011 would see it).
For the owner: the remaining proposals (FR-004, FR-005, FR-007, FR-008, FR-011 to FR-013).

## 2026-10-03 · Claude (Cowork) · FR-003, LW-017 and FR-006, as the owner chose
Did: the owner accepted FR-003 and FR-006, chose to square machines on the tilt table
(LW-017) and said no lab work for now (FR-009, FR-010). ADR 0028: a sweep's rates come from
its random repeats only, with exact bounds; the report and the variations panel say how
sure they are. ADR 0029: the tilt test turns the machine square to its rail before it
tilts; its sweeps no longer turn it. ADR 0030: a run can be disturbed partway - the
machine shoved, a part moved - and `sweep --disturb` compares each set-up with itself
undisturbed; on the way, the grasp check stopped counting a fixed table as held.
Measured: Fetch met every goal in 8 of 8 drawn set-ups (at least 69 %), and in 59 of 59
when 59 were drawn: it fails in under 5 % of such set-ups, with 95 % confidence. Tilt,
squared: 54.0 to 58.5 deg, the turned machine now tips as designed (53.98 against 53.99).
Shoved at the table, the arm on a cart recovered from 4 N s (1.7 cm) in 9 of 9 set-ups and
from 6 N s (6.4 cm) in 3 of 9; with its poses run as taught, 8 of 9 and none. Suites: 660 with a display, 623 headless.
Unfinished: no button for disturbances and no slippery patch (LW-018); past about 4 cm the
corrected arm meets the table's edge and the program has no way back to its stop (LW-019).
For the owner: the next proposals to accept or decline (FR-004 to FR-008, FR-011 to
FR-013), and whether a program should drive back to its stop when its arm cannot reach
(LW-019).

## 2026-10-02 · Claude (Cowork) · MuJoCo 3.10.0 (FR-002)
Did: ADR 0027. MuJoCo pinned to 3.10.0, as the owner chose (the newest release with
wheels for an Intel Mac). Run as released it moved one check, the test cart's coast-down,
by 5 %: multiccd, on by default since 3.8, gives a cylinder wheel four contacts on the box
floor within 0.2 mm of each other, and the solver loads the leading ones more as it rolls -
a rolling loss of the engine's own on top of the sourced one, growing with speed. The
adapter turns multiccd off (one contact per convex pair, as on 3.3.7).
Measured: coast-down +0.18 % against the closed form on 3.3.7 and on 3.10.0 (+5.0 % with
multiccd). Tilt table 54.48 to 53.99 deg, the box-box fix of 3.4 that ADR 0022 named;
Fetch in the bin at 33.04 s (33.97); settled stance 3.36 cm (predicted 3.37); curbs and
sprint unchanged. Suites on 3.10.0: 643 with a display, 606 headless.
Unfinished: nothing from FR-002. The owner's Mac needs its environment reinstalled.
For the owner: after publishing, run `.venv/bin/python -m pip install -e '.[workshop,dev]'`
in Tiny-room (or the uv line in the README) so the Mac gets 3.10.0. FR-004 (the motor as
MuJoCo's dcmotor) and FR-010 (the servo bench) are now possible on the pin.

## 2026-10-02 · Claude (Cowork) · the frontier brief and proposals
Did: ADR 0026, asked for by the owner as the project's "brain". The radar reads journals'
tables of contents (Science Robotics, IEEE RA-L, IEEE T-RO) besides preprints and releases,
and `python -m little_world.radar brief` writes its findings into the new
`docs/agents/FRONTIER.md`. Fourteen proposals written there (FR-001 to FR-014): where each
idea would go in Little World, how we would know it worked, what it costs.
`scripts/agent_status.py` lists the ones waiting for the owner. As the owner chose, a weekly
scheduled session (Mondays) searches the same sources and writes new proposals outside the
repository; the next agent session brings them in.
Measured: first brief: 302 items read, 51 filed, 23 judged; every adopt and learn verdict is
cited by a proposal. Suites on MuJoCo 3.3.7: 642 with a display, 605 headless.
Unfinished: the journal feeds refused this workspace (IEEE Xplore 418, Science 403; LW-011).
The weekly run's first brief is due on 2026-10-05.
For the owner: twelve proposals wait for you (FR-003 to FR-014). If it helps: FR-003 and
FR-006 are cheap and make every result more defensible; FR-004 and FR-005 bring the motors
and the machines' tipping closer to the real ones; FR-009 and FR-010 need you in a lab;
FR-014 waits on hardware newer than an Intel Mac.

## 2026-10-02 · Claude (Cowork) · OPEN LW-013, LW-017 traced, the variations panel drawn
Did: the radar profile files MuJoCo Menagerie and the four registered arms under ADR 0019
(LW-013, done). LW-017 traced and written into ADR 0024 (no behaviour changed). The
variations panel draws every run as a tick against the run as designed and the prediction,
and keeps inside the window. Commits 6030ea3, 38672c3, 7140150.
Measured: suites 634 with a display, 597 headless; 3.14 headless 597.
Unfinished: LW-017 waits on the owner. The remaining open items need the owner (LW-004,
LW-009, LW-012, LW-015, LW-017), need LW-004 first (LW-005 to LW-007), cannot be done from
this workspace (LW-011: the fetcher has to meet the live feeds from the owner's machine), or
are a direction to choose (LW-010, grasping from the cell's camera).

## 2026-10-02 · Claude (Cowork) · OPEN LW-016: poses aimed at a point
Did: ADR 0025. A pose can carry the point its tool was aimed at; the runner, given the arm's
aim (`ToolMotion.aim`), checks where the tool got to once the pose settles and solves it
again for where the machine now stands, at most twice. The Fetch template aims its poses at
the stops; the app, the sweeps and the tests pass the aim. Tracing it also refined ADR 0024's
explanation (edited in place, unpublished): loaded, the jaws had met the cube 28 mm from
their aim before the lift lost another 12 mm to the rock.
Measured: as designed each aimed pose settled 10-12 mm off (the base stops within 1 cm of
its mark) and one correction brought it within 1-3 mm; in the bin at 34.0 s (32.5 before).
Loaded with 0.5 kg behind the arm: jaws within 3.3 mm of the cube, lifted at 18.2 s (23.7
before). Suites: 632 with a display, 595 headless; 3.14 headless 595.
Unfinished: the pick-and-place template's poses are not aimed (its arm stands on a
pedestal). LW-017 traced, not changed: a machine turns as the tilt table rises, and one set
down 3 deg right ends with a single tread block against the rail and swings about it (ADR
0024 has the numbers).
For the owner: LW-017 is a choice - accept it, have the tilt protocol align the machine with
the rail, or model the turn in the prediction.

## 2026-10-01 · Claude (Cowork) · OPEN LW-008: runs under variation
Did: ADR 0024. A field run can be repeated with variations: set down off its mark and
turned, carrying a steel block, friction across each surface pair's published range
(`fields/variation.py`, `contact_pairs.SPREADS`, `MujocoBackend.vary_pair_friction`). The
sweep (`inventory/sweep.py`, also `python -m little_world.inventory.sweep`) runs 20
variations in worker processes and reports each goal's spread and what moved it most. The
run report has "Repeat with variations", which runs it in another process
(`ui/varied_runs.py`).
Measured: tilt table, arm on a cart: 51.4 to 58.4 deg over 20 runs (54.5 as designed);
turned 3 deg on the table moves it most (-3.1) and is where the prediction is furthest off
(2.8 deg high); with 0.5 kg aboard the prediction holds within 0.3 deg. Fetch: every goal in
all 20 runs; loaded behind the arm, the cart rocks 5 deg between its casters as the arm
lifts and the lift falls 12 mm short until it rocks back. Suites: 626 with a display, 589
headless; 3.14 headless 589.
Unfinished: LW-016 (arm moves solved for one stance), LW-017 (a turned machine on the tilt
table), both found by the sweeps and not fixed.
For the owner: the placement and payload ranges (2 cm, 3 deg, 0.5 kg) are my assumptions;
say if your lab's are different and they are one line to change.

## 2026-10-01 · Claude (Cowork) · OPEN LW-014: machines start on the floor
Did: ADR 0023. The example machines are built resting 2 mm above the floor: the mobile
platform (and the arm on a cart) is set down after assembly, the two-wheel example and the
block are placed lower. The build stage warns when a design starts more than 5 mm up
(`structure.clearance`). The curb-history check is no longer marked as expected to fail.
Measured: the platform used to fall 44 mm as a run began, the two-wheel example 10.5 mm; now
they settle 2.5 to 2.9 mm. Started on its wheels, the platform's caster answers the same alone
and after a 10 mm curb in all four configurations; the fall had left a caster swivelled 37
degrees by the second curb. This corrects my earlier report and ADR 0022: the curb history
came from the start, not from MuJoCo 3.3.7's contacts. Stance margin 3.34 cm on 3.3.7, 3.35 on
3.14 (predicted 3.37); tilt table 54.5 deg on 3.3.7, 52.6 on 3.14. Suites: 613 with a display,
577 headless; 3.14 headless 577.
Unfinished: nothing from LW-014.
For the owner: designs you saved before keep their heights; the build stage now says if one
starts in the air, and "Free base + ground" sets it down. LW-015 (the Curb run's 20 mm curb)
now depends only on the MuJoCo release.

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
