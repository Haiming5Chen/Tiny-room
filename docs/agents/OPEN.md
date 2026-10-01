# Open

Unfinished work and problems found but not fixed, as the agents who found them reported
them. The owner decides what is taken up and in what order. Statuses: `open`, `done` (with
the commit), `dropped` (with the owner's reason). `tests/test_agent_docs.py` keeps the
table well formed.

| ID | Opened | By | What is open | Context | Status |
| --- | --- | --- | --- | --- | --- |
| LW-001 | 2026-09-27 | Claude (Cowork) | The caster curb check sits on its geometric limit: a 20 mm curb against a 40 mm caster wheel | stops on MuJoCo 3.3.7, climbs on 3.14 (docs/RADAR.md); 18 and 22 mm would be clear of the limit | open |
| LW-002 | 2026-09-27 | Claude (Cowork) | The measured stance margin comes from reported contact points | on 3.14 it reads 2.6 cm where 3.3.7 read 3.4 with the tilt unchanged (docs/RADAR.md) | open |
| LW-003 | 2026-09-27 | Claude (Cowork) | Part of the tilt-table difference on MuJoCo 3.14 is unexplained | 54.2 deg on 3.3.7, 52.4 on 3.14, 53.0 with multiccd off (docs/RADAR.md) | open |
| LW-004 | 2026-09-27 | Claude (Cowork) | MuJoCo is pinned to 3.3.7; the newest release is 3.14 | the headless suite passes 565 of 568 on 3.14; the three are LW-001 to LW-003 | open |
| LW-005 | 2026-09-27 | Claude (Cowork) | The factory's feeder is a teleport | MuJoCo 3.11 `geom/surfacevel` models a conveyor with a static geom (needs LW-004) | open |
| LW-006 | 2026-09-27 | Claude (Cowork) | MuJoCo's `pid` actuator is untried for the kit servos | it could replace the Torque slope of ADR 0014 (needs LW-004) | open |
| LW-007 | 2026-09-27 | Claude (Cowork) | MuJoCo's `dcmotor` is untried for the Pololu 37D | the datasheet model of ADR 0011 maps onto it (needs LW-004) | open |
| LW-008 | 2026-09-27 | Claude (Cowork) | The test fields run each scenario once, unperturbed | a sweep over friction, payload and start pose would report a spread (radar: LIBERO-plus) | open |
| LW-009 | 2026-09-27 | Claude (Cowork) | No servo has been calibrated against a real one | MuJoCo 3.5's system identification toolbox; needs hardware | open |
| LW-010 | 2026-09-27 | Claude (Cowork) | The factory cell grasps at known part positions | positions from the cell's camera are on the roadmap | open |
| LW-011 | 2026-09-27 | Claude (Cowork) | The radar's fetcher has not met the live feeds | its parsers are tested on documents shaped like the feeds; the first run was gathered by a browsing tool | open |
| LW-012 | 2026-09-27 | Claude (Cowork) | Radar phase two is undecided: a weekly schedule, semantic embeddings, a classifier from ratings | the owner's decision | open |
| LW-013 | 2026-09-27 | Claude (Cowork) | MuJoCo Menagerie has no radar topic | much attention and no topic in the first run, though the app's robots come from it | open |
| LW-014 | 2026-09-27 | Claude (Cowork) | Designs of the mobile platform family start 4.3 cm above the floor and drop when a run starts | seen in a tilt-table probe; the design's lowest point is at z = 0.043 | open |
