# Frontier radar

New papers, open models, repositories and releases of the libraries this project stands
on, scored against its own decision records, roadmap and learning profile, and filed under
the decision each could change ([ADR 0021](adr/0021-frontier-radar.md)). Standard library
only; the store is one SQLite file outside the repository.

```
python -m little_world.radar fetch                 # the feeds, into ~/.little_world/radar.sqlite
python -m little_world.radar digest --days 7 --out digest.md --html digest.html
python -m little_world.radar rate <id> adopt|learn|watch|skip "why"
python -m little_world.radar ingest found.jsonl    # items gathered by hand or by an assistant
python -m little_world.radar topics                # what it looks for (docs/radar/profile.md)
python -m little_world.radar brief                 # its section of docs/agents/FRONTIER.md
```

The Markdown digest is short - verdicts and their reasons first, three items a topic. The
page (`--html`) holds everything: counts and verdicts at a glance, a filter by verdict, a
chart of the simulator's releases, and each item's summary and matched words on demand.

The loop it is for: a digest arrives; a person (or an assistant) judges the top of it;
an *adopt* becomes a trial on a branch, and a trial that holds becomes a decision record
that cites what it adopted. The radar reads; the test suite measures.

## The brief and the proposals (ADR 0026)

Between a verdict and a change sits a proposal. `docs/agents/FRONTIER.md` is the file both
agents read: numbered proposals (`FR-nnn`), each with where it comes from, how it would be
adapted to Little World, how we would know it worked and what it costs, and a status only
the owner moves to accepted or declined. `brief` rewrites the end of that file, between two
markers: the last two weeks' filed items, judged ones first, each with the proposals citing
it, and the items judged worth adopting or learning that no proposal cites yet.

Journals joined the feeds on 2 October: the tables of contents of Science Robotics, IEEE
Robotics and Automation Letters and IEEE Transactions on Robotics, an article keyed by its
DOI. From the cloud workspace those feeds refused automated requests (IEEE Xplore 418,
Science 403), so the weekly reading the owner chose - a scheduled session - searches them
with web search and writes its proposals outside the repository for the next agent session
to bring in; `fetch` on the owner's machine reads them directly if they answer it.

## First run - 27 September 2026

Gathered through a browsing tool (summaries condensed, not verbatim abstracts): the arXiv
cs.RO listing of 25 September (38 new submissions), Hugging Face's daily papers of the same
day (17) and its trending robotics models (20), GitHub's MuJoCo repositories active that
fortnight and robotics repositories created since 28 August (20), nine notable releases of
2026 found by a wider search, and MuJoCo's changelog from 3.4.0 to 3.14.0 - 198 entries in
twelve releases, 51 of them under "Breaking API changes". **302 items, 48 filed under a
topic** (29 topics: 21 decision records, the roadmap's next steps, four planned steps and
three learning goals).

What it filed, and the triage (23 verdicts):

| verdict | item | why, for this project |
| --- | --- | --- |
| adopt | MuJoCo 3.8.0: multiccd on by default (breaking) | see the trial below: it changes our curb and tilt-table results |
| adopt | MuJoCo 3.11.0: `geom/surfacevel` | the factory's feeder becomes a conveyor - a static geom with a moving surface, no joints |
| adopt | MuJoCo 3.12.0: `pid` actuator | the engine's own servo, correct under every integrator, could replace ADR 0014's Torque slope; the servo damping tests decide |
| adopt | MuJoCo 3.7.0: `dcmotor` actuator | ADR 0007's datasheet motor maps onto its resistance, back-EMF and friction terms |
| adopt | MuJoCo 3.5.0: system identification toolbox | the path to real hardware: record a real servo or cart, fit its friction, damping and gains |
| adopt | LIBERO-plus (arXiv 2510.13626) | perturbation sweeps for the test fields: friction, payload and start pose varied, the spread reported |
| learn | MolmoBot (Ai2, March 2026) | trained only in MuJoCo, zero-shot on a real Franka and a mobile manipulator: the reference for approaching reality |
| learn | Project Fetch phase two (Anthropic, June 2026) | an agent writes working robot code fast and fails at fine closed-loop control: blocks are the layer to give it |
| learn | CaP-X (arXiv 2603.22435) | coding agents do well only with good helper functions: study its benchmark before building one |
| learn | Extended friction models for servo actuators (arXiv 2410.08650) | servo friction identified on a pendulum bench: a cheap real experiment |
| learn | LeRobot 0.6; SmolVLA | the common dataset format and the smallest open VLA: the bridge to robot learning |
| learn | RoboCasa365; Drake 1.57 | benchmark design on the same engine; a second opinion on conveyors and contact integration |
| watch | MuJoCo 3.13.0: `discrete` integrator | experimental; could retire the Torque slope, but noslip is only approximated under it |
| watch | Newton; FoundationPose; MuJoCo itself | GPU only (we run on a Mac CPU); camera grasping later; the engine is read by changelog |
| skip | five repositories and papers | matched on buzzwords, or not our layer |

Much attention, no topic: MuJoCo Menagerie (4,125 stars) - the source of this project's
registered robots, which no topic names yet - MuJoCo MPC, MyoSuite, and two openly
promotional lists. The first is a gap in the profile; the last two are noise. (Closed on
2026-10-02: the profile files Menagerie and its arms under ADR 0019, OPEN LW-013.)

Missed: short changelog entries carry too few words to match - "Added single-shot
multicontact for collisions with cylinder geoms" names no topic, yet it is about every
wheel here. That is what the trial is for.

## Trial: MuJoCo 3.3.7 -> 3.14.0

The adopted changes all need a newer MuJoCo, so the first action was to run the whole
headless suite, unchanged, on MuJoCo 3.14.0 in a separate environment:

| | 3.3.7 (pinned) | 3.14.0 | 3.14.0, multiccd off |
| --- | --- | --- | --- |
| headless suite | 568 passed | 565 passed, 3 failed | 2 of the 3 pass |
| caster against a 20 mm curb (as tall as its radius) | stops | climbs | stops |
| manipulator on the tilt table (predicted 54.3, 55.8 at the rail) | tips at 54.2 deg | 52.4 deg | 53.0 deg |
| manipulator's settled stance margin (predicted 3.4 cm) | 3.4 cm | 2.6 cm, tilt unchanged | 2.6 cm |

Run side by side, the suite took 279 s on 3.14.0 and 340 s on 3.3.7.

All three involve a cylinder wheel in contact, and the breaking change the radar filed
first explains part of it: multiccd, on by default since 3.8.0, returns several contacts
per convex collision. Turned off, the caster stops at the curb again and a third of the
tilt-table difference goes; the rest, and the margin, come from elsewhere in how wheel
contacts are made and reported (3.13.0 added multicontact for cylinders; the radar missed
that entry, above). Neither curb answer is plainly the real one - a real caster at a curb
as tall as its radius sits on the limit - so that check belongs at 18 and 22 mm, not at 20.
The margin moved with the tilt unchanged: the reported contact points moved, not the
machine. Decision for now: stay on 3.3.7; next, move the curb check off the limit, measure
stance from the wheel geometry rather than from reported contact points, find the rest of
the tilt difference, then upgrade and adopt the actuators and the conveyor.

Settled on 2026-10-01 (ADR 0022): the margin is now measured from wheel shapes and agrees on
both releases; the curb answers on 3.3.7 turned out to depend on the curb before them (on
3.14 they do not) - traced later to the platform starting 4.3 cm in the air (ADR 0023); and
the tilt difference is the box-box collider changes (the tread blocks are boxes) and
multicontact for the caster's cylinder. The headless suite passes in full on 3.14.

Upgraded on 2026-10-02 to 3.10.0, the newest release with wheels for the owner's Intel
Mac (ADR 0027). Run as released it moved one more result: multiccd's extra contacts gave a
rolling cylinder wheel a loss of the engine's own, 5 % of the sourced one at 0.8 m/s. The
adapter turns multiccd off; the radar now reads MuJoCo's changes after 3.10.0.

## Topics

`docs/radar/profile.md` lists the extra words per decision, the planned steps and the
learning goals. Add a `## ADR nnnn` section when a record's own words differ from the
field's; add a `Next:` topic when the roadmap gains a step.
