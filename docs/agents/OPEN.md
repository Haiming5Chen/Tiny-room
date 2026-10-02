# Open

Unfinished work and problems found but not fixed, as the agents who found them reported
them. The owner decides what is taken up and in what order. Statuses: `open`, `done` (the
context says where), `dropped` (with the owner's reason). `tests/test_agent_docs.py` keeps the
table well formed.

| ID | Opened | By | What is open | Context | Status |
| --- | --- | --- | --- | --- | --- |
| LW-001 | 2026-09-27 | Claude (Cowork) | The caster curb check sits on its geometric limit: a 20 mm curb against a 40 mm caster wheel | checks moved to 18 against 24 mm (ADR 0022); the answer's dependence on the curb before it came from the platform's start in the air (ADR 0023) | done |
| LW-002 | 2026-09-27 | Claude (Cowork) | The measured stance margin comes from reported contact points | now from the touching geoms' shapes: 3.39 cm on 3.3.7, 3.40 on 3.14, predicted 3.37 (ADR 0022) | done |
| LW-003 | 2026-09-27 | Claude (Cowork) | Part of the tilt-table difference on MuJoCo 3.14 is unexplained | named release by release: box-box collider changes (tread blocks) and cylinder multicontact (caster) (ADR 0022) | done |
| LW-004 | 2026-09-27 | Claude (Cowork) | MuJoCo is pinned to 3.3.7; the newest release is 3.14 | the whole headless suite passes on 3.14 (577 since ADR 0023) | open |
| LW-005 | 2026-09-27 | Claude (Cowork) | The factory's feeder is a teleport | MuJoCo 3.11 `geom/surfacevel` models a conveyor with a static geom (needs LW-004) | open |
| LW-006 | 2026-09-27 | Claude (Cowork) | MuJoCo's `pid` actuator is untried for the kit servos | it could replace the Torque slope of ADR 0014 (needs LW-004) | open |
| LW-007 | 2026-09-27 | Claude (Cowork) | MuJoCo's `dcmotor` is untried for the Pololu 37D | the datasheet model of ADR 0011 maps onto it (needs LW-004) | open |
| LW-008 | 2026-09-27 | Claude (Cowork) | The test fields run each scenario once, unperturbed | runs under variation - start pose, payload, friction across its sources' ranges - from the run report or `python -m little_world.inventory.sweep` (ADR 0024) | done |
| LW-009 | 2026-09-27 | Claude (Cowork) | No servo has been calibrated against a real one | MuJoCo 3.5's system identification toolbox; needs hardware | open |
| LW-010 | 2026-09-27 | Claude (Cowork) | The factory cell grasps at known part positions | positions from the cell's camera are on the roadmap | open |
| LW-011 | 2026-09-27 | Claude (Cowork) | The radar's fetcher has not met the live feeds | its parsers are tested on documents shaped like the feeds; the first run was gathered by a browsing tool | open |
| LW-012 | 2026-09-27 | Claude (Cowork) | Radar phase two is undecided: a weekly schedule, semantic embeddings, a classifier from ratings | the owner's decision | open |
| LW-013 | 2026-09-27 | Claude (Cowork) | MuJoCo Menagerie has no radar topic | the profile files Menagerie and its arms (Panda, FR3, Gen3, UR5e) under ADR 0019, the robots' tool moves | done |
| LW-014 | 2026-09-27 | Claude (Cowork) | Designs of the mobile platform family start 4.3 cm above the floor and drop when a run starts | the examples start 2 mm clear and the build stage warns about a design built in the air (ADR 0023) | done |
| LW-015 | 2026-10-01 | Claude (Cowork) | The Curb run's 20 mm curb sits at the platform's caster radius | its result for the platform depends on the MuJoCo release: stops on 3.3.7, climbs on 3.14 (ADR 0023); the field keeps 10, 20 and 35 mm unless the owner decides otherwise | open |
| LW-016 | 2026-10-01 | Claude (Cowork) | A program's arm poses are solved for one stance; a cart that rocks between its casters moves the tool | poses aimed at a point are checked where the tool got to and solved again: loaded, the jaws meet the cube within 3.3 mm instead of 28 and it is lifted at 18.2 s instead of 23.7 (ADR 0025) | done |
| LW-017 | 2026-10-01 | Claude (Cowork) | The tip-angle prediction is furthest off for a machine turned on the tilt table | turned 3 deg: measured +0.4 and -3.1 deg against predicted +1.7 and -1.6. Traced: the machine turns as the table rises (straight: 1.7 deg by 40 deg of tilt); turned left it settles at that same heading, turned right at -0.5 deg with one tread block against the rail, then swings about it near 48 deg and goes over early (ADR 0024). Open for the owner: accept, ask the protocol to align the machine with the rail, or model the turn; the tread is a ring of blocks, a real tyre meets a rail along an arc | open |
