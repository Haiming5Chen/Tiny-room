# Backlog

One row per task. Claim a task by setting its status to `claimed` and the owner to your
name and the date; set `done` with the commit that finished it. Statuses: `open`,
`claimed`, `blocked` (say on what), `done`, `dropped` (say why). New tasks take the next
number. `tests/test_agent_docs.py` checks that this table stays well formed.

| ID | Status | Owner | Task | Done when | Source |
| --- | --- | --- | --- | --- | --- |
| LW-001 | open | | Move the caster curb check off its geometric limit: 18 and 22 mm instead of 20 | the platform clears 18 mm and stops at 22 mm on MuJoCo 3.3.7 and 3.14 | RADAR.md trial |
| LW-002 | open | | Measure the stance margin from wheel geometry rather than reported contact points | the manipulator's measured margin is within 3 mm of its prediction on 3.3.7 and 3.14 | RADAR.md trial |
| LW-003 | open | | Find the rest of the tilt-table difference on MuJoCo 3.14 (54.2 on 3.3.7, 53.0 with multiccd off) | the change responsible is named and a test holds the angle on both versions | RADAR.md trial |
| LW-004 | blocked | | Upgrade MuJoCo from 3.3.7 to 3.14 | pin, lock file and both suites updated; VALIDATION section with before and after (blocked on LW-001 to LW-003) | ADR 0021 |
| LW-005 | blocked | | A conveyor for the factory's feeder from `geom/surfacevel` instead of the teleport | parts ride a static belt geom to the input tray; production run unchanged or better (blocked on LW-004) | radar: MuJoCo 3.11 |
| LW-006 | blocked | | Try MuJoCo's `pid` actuator for the kit servos in place of the Torque slope | tests/test_servo_damping.py passes unchanged, or an ADR says why not (blocked on LW-004) | radar: MuJoCo 3.12 |
| LW-007 | blocked | | Model the Pololu 37D with MuJoCo's `dcmotor` | both datasheet endpoints met as in ADR 0011 (blocked on LW-004) | radar: MuJoCo 3.7 |
| LW-008 | open | | Perturbation sweeps for the test fields: friction, payload and start pose varied | a field reports the spread of a goal's time or angle over at least 20 perturbed runs | radar: LIBERO-plus |
| LW-009 | blocked | | Calibrate one real servo with MuJoCo's system identification toolbox | fitted friction, damping and gain for one servo, compared with its profile (blocked on hardware) | radar: MuJoCo 3.5 |
| LW-010 | open | | Grasp from the factory cell's camera instead of known part positions | a run of six parts placed with positions estimated from the cell camera | ROADMAP |
| LW-011 | open | | First live `python -m little_world.radar fetch` on the owner's machine; fix what the live feeds break | a digest built from fetched feeds, and parser tests for anything that differed | ADR 0021 |
| LW-012 | blocked | | Radar phase two: weekly schedule, semantic embeddings, a classifier from ratings | owner's decision (blocked on the owner) | ADR 0021 |
| LW-013 | open | | Add MuJoCo Menagerie as a radar topic: much attention and no topic in the first run | Menagerie releases are filed under a topic | radar first run |
| LW-014 | open | | Designs of the mobile platform family start 4.3 cm above the floor and drop at the start of a run | decide whether scenes set a design on the floor; a test for the start height | 2026-09-27 probe |
