# Frontier

What the field publishes that could change this project, and what agents propose to do
with it. The owner decides: nothing here is a task until the owner accepts it.

How it works ([ADR 0026](../adr/0026-frontier-brief-and-proposals.md)):

1. **The radar reads.** `python -m little_world.radar fetch` reads preprints (arXiv cs.RO,
   Hugging Face's daily papers), journals' tables of contents (Science Robotics, IEEE
   Robotics and Automation Letters, IEEE Transactions on Robotics), open models and
   repositories, and every MuJoCo release newer than the pinned one, and files each item
   under the decision record or roadmap step it could change ([ADR 0021](../adr/0021-frontier-radar.md)).
2. **The brief.** `python -m little_world.radar brief` rewrites the section between the
   `radar` markers at the end of this file: what was filed in the last two weeks, judged
   items first, each with the proposals that cite it, then what was judged worth adopting
   or learning and has no proposal yet. Do not edit inside the markers.
3. **Proposals.** An agent that reads something worth acting on writes a proposal below:
   how it would be adapted to Little World, how we would know it worked, what it costs.
   A weekly scheduled session searches the same sources and writes its proposals outside
   the repository; the next agent session copies them here under new numbers.
4. **The owner decides.** Only the owner moves a proposal to `accepted` or `declined`.
   Agents work on accepted proposals only, mark one `doing` when they start and `done`
   with the decision record that settled it.

## Writing a proposal

- Take the next free number: `### FR-nnn · short title`, then six fields in this order:
  - **Status:** `proposed`, `accepted`, `doing`, `done` or `declined`, the word first; a
    date, a reason or a decision record may follow.
  - **From:** the items it rests on, linked; a radar id in backticks (`arxiv:2510.13626`)
    ties it to the brief.
  - **Idea:** what the source found or offers, in a sentence or two.
  - **In Little World:** where it would go: modules, fields, the decision records it changes.
  - **How we would know:** the measurement or test that would show it worked, with numbers.
  - **Cost and needs:** work, dependencies, hardware, MuJoCo version, the owner's time.
- One idea per proposal. Say what is assumed and what was not read (a title is not a paper).
- Do not rewrite another agent's proposal. To disagree or add evidence, append
  `- Note (who, date): ...` under it; the owner reads both.
- `tests/test_agent_docs.py` checks the numbers, the fields and the statuses;
  `python scripts/agent_status.py` lists what waits on the owner.

## Proposals

### FR-001 · Runs under variation
- Status: done (ADR 0024, 2026-10-01; OPEN LW-008)
- From: [LIBERO-plus](https://arxiv.org/abs/2510.13626) (`arxiv:2510.13626`, radar: adopt)
- Idea: policies that succeed in one nominal scene fail under small, systematic changes of
  start pose, objects and physics; a result should come with its spread, not one run.
- In Little World: a field run repeated with the machine set down off its mark and turned,
  a steel-block payload, and each surface pair's friction across its cited range; the
  sweep reports each goal's spread and what moved it most (`fields/variation.py`,
  `inventory/sweep.py`, "Repeat with variations" in the run report).
- How we would know: done. The tilt table spread 51.4 to 58.4 deg over 20 runs, and the
  sweeps found two problems no single run showed (LW-016, fixed by ADR 0025; LW-017).
- Cost and needs: spent: two decision records.
- Note (weekly run, 2026-10-19): random draws certify a rate; FR-025 adds a search for where the failures are, FR-024 a check that each drawn outcome is not a knife edge.

### FR-002 · MuJoCo 3.10.0 on every machine
- Status: done (ADR 0027, 2026-10-02; accepted by the owner the same day: one version everywhere, 3.10.0)
- From: [MuJoCo's changelog](https://mujoco.readthedocs.io/en/latest/changelog.html), 3.4
  to 3.14 filed entry by entry (ADR 0021); multiccd on by default from 3.8.0
  (`mujoco:3.8.0#6`, radar: adopt); OPEN LW-004
- Idea: the newest MuJoCo is 3.14.0, but its Python wheels for Intel Macs stop at 3.10.0,
  and the owner's Mac is an Intel one: 3.10.0 is the newest release every machine runs.
- In Little World: pin 3.10.0 in `pyproject.toml` and the lock file, and account for every
  result that moves (on 3.10 the coast-down deceleration moves 5 %, as multiccd on 3.3.7
  did). The DC-motor actuator (FR-004) and the system identification toolbox (FR-010)
  become available; the PID actuator and moving surfaces do not (FR-014).
- How we would know: both suites pass on 3.10.0, each moved number explained in the
  decision record; the owner's Mac installs 3.10.0 from a wheel. Done: multiccd's extra
  wheel contacts made a rolling loss of their own (+5.0 % at 0.8 m/s), so the adapter keeps
  one contact per convex pair; the tilt table moved 54.48 to 53.99 deg, Fetch delivered at
  33.0 s instead of 34.0 (ADR 0027).
- Cost and needs: one decision record; the owner reinstalls the Mac's environment after
  publishing.

### FR-003 · Success rates with their uncertainty
- Status: done (ADR 0028, 2026-10-03; accepted by the owner the same day)
- From: [RoboCasa365](https://arxiv.org/abs/2603.04356) (`arxiv:2603.04356`, radar: learn)
  and LIBERO-plus report success over many episodes; the exact binomial interval
  (Clopper and Pearson, 1934)
- Idea: "every goal in all 20 runs" sounds certain and is not: 20 of 20 is consistent with
  a machine that fails up to 14 % of the time (one-sided 95 % bound). Benchmarks give the
  rate, the number of episodes and the interval.
- In Little World: the sweep's headline, the variations panel and the reports in
  `docs/sweeps/` say "20 of 20, at least 86 % (95 % confidence)"; a claim like "fails in
  under 5 %" gets the runs it needs (59 without a failure).
- How we would know: the interval matches tabulated Clopper-Pearson bounds to three
  decimals in a unit test; every sweep headline carries one.
- Cost and needs: standard library only; more runs cost minutes of computing, not work.
- Note (Claude, 2026-10-03): done with one correction to the idea above - only a sweep's
  random repeats are a sample; its chosen runs (as designed, each variation at either end)
  check corners. Fetch: 8 of 8 drawn, at least 69 %, not 20 of 20 and 86 % (ADR 0028).

### FR-004 · The Pololu 37D as MuJoCo's own DC motor
- Status: proposed
- From: [MuJoCo 3.7.0: the `dcmotor` actuator](https://mujoco.readthedocs.io/en/latest/changelog.html)
  (`mujoco:3.7.0#1`, radar: adopt); OPEN LW-007
- Idea: the engine models a DC motor's electrical side, so torque falls with speed inside
  the solver rather than in a controller written beside it, and the command can be a
  voltage, as a motor driver sets it. In 3.10 (`MjsActuator.set_to_dcmotor`) it takes motor
  constants and winding resistance, and optionally inductance, cogging, an on-board
  controller, heating and LuGre friction.
- In Little World: ADR 0011 builds the 37D 30:1's torque-speed line (12 V, 5.5 A stall,
  0.2 A no-load, 330 rpm) in our own code. Map those numbers onto `dcmotor`: 2.18 ohm from
  12 V over 5.5 A; a torque constant of 0.26 N m/A at the output from stall and a back-EMF
  constant of 0.33 V s/rad from free run - their ratio, 0.77, is the gearbox efficiency
  the datasheet implies, or the extrapolation Pololu warns about. Give the rotor's inertia
  to the wheel joint as armature (rotor inertia times 30 squared), which ADR 0011 leaves
  out. Heating would answer Pololu's note that the motors stall early as they warm.
- How we would know: the drivetrain tests pass on the engine's motor (stall torque at rest,
  zero torque at 330 rpm, the coast-down within 1 %); the Sprint run's times move by less
  than 2 %, or the armature explains the difference; the current at stall reads 5.5 A.
- Cost and needs: FR-002 first; the rotor's inertia is not on Pololu's pages (an estimate
  with its source, or a measurement); `dcmotor` was reworked in 3.12, so the mapping is
  redone when the pin passes 3.11. One decision record.
- Note (weekly run, 2026-10-05): MuJoCo 3.12.0 redesigned the dcmotor's on-board controller ("input attribute selects subset of [pos, vel, ff, voltage]") with a breaking change to its input modes and gain semantics, and 3.14.0 changed `mj_readCtrl` for multi-input actuators (pid, dcmotor). A dcmotor mapping written on the pinned 3.10.0 will not carry over unchanged: keep it inside the MuJoCo adapter and test it against the ADR 0011 datasheet curve (no-load speed, stall torque, coast-down), so an upgrade fails a test instead of shifting results silently. The [actuator digital-twin paper](https://www.mdpi.com/2076-0825/15/8/451) found simplified models degrade outside the regime they were tuned in, while a model with the device's limits and controller holds — model current limits, not only the torque–speed line.
- Note (weekly run, 2026-10-19): MuJoCo 3.16.0 changed how shortcut actuators inherit parameters - only from a default of the same shortcut or `general`; motors in position-default classes are no longer position servos (issue #3561) - and fixed or affine actuators may now declare their input as pos, vel or pressure (no effect on simulation). When the pin lifts, a test that the compiled gains of every kit actuator equal its profile (Pololu 37D, XH430) should run before anything else, together with the dcmotor input change of 3.12 noted on 5 October.

### FR-005 · Tip-over margin while moving: the force-angle measure
- Status: done (ADR 0059, 2026-10-27: the force-angle measure on the solver's state, in the drive panel and the run report; on the tilt table the arm cart's angle runs out at 53.5 deg, 0.7 deg before its static prediction, as it goes over; a hard stop from full speed takes 3 to 4 deg from the kit carts and tips none; the 20 ms check against a lifting wheel needs a machine that tips on braking, OPEN LW-038; taken by the weekly reading's ranking)
- From: E. G. Papadopoulos and D. A. Rey, "A new measure of tipover stability margin for
  mobile manipulators", ICRA 1996; [Analytic solutions for wheeled mobile manipulator
  supporting forces](https://arxiv.org/abs/2202.10186) (title only, not yet read)
- Idea: a static margin - how far the centre of mass sits inside the support polygon - says
  nothing about braking hard or swinging a loaded arm. The force-angle measure uses the
  net force and moment at the centre of mass, inertial ones included, and its height, and
  gives for each edge of the polygon the angle left before the machine tips over it.
- In Little World: ADR 0015 and 0022 compute the stance margin statically from the geoms
  that touch the floor. Compute the force-angle measure every step over the same polygon
  from the solver's data (the subtree centre of mass and its acceleration), show its
  minimum in the telemetry, and add a "hard stop" field: full speed, then stop, with and
  without a payload high on the arm.
- How we would know: on the slowly rising tilt table it agrees with the static prediction
  (54.3 deg); over a sweep of hard stops, it crosses zero within 20 ms of a wheel first
  lifting 2 mm off the floor, in runs where the static margin stays positive.
- Cost and needs: no dependency; the centre of mass's acceleration needs MuJoCo's
  `mj_rnePostConstraint`; a field, a telemetry line and one decision record. In a real lab
  it is a live warning for a mobile arm.
- Note (weekly run, 2026-10-05): the [MNGR criterion](https://www.mdpi.com/2076-3417/16/16/8136) uses the normal ground reactions at the wheels with an inverse centre-of-mass-height factor (cheap, sensitive to top-heaviness). MuJoCo already gives the wheel normal forces, so a "lightest-loaded wheel" margin can be logged beside the force-angle measure at almost no cost; the tilt table (ADR 0020) is the ground truth for both — each must reach zero at the measured tip angle (53.99°).
- Note (weekly run, 2026-10-19): [emergency maneuvers of differential-drive robots, arXiv 2610.05607](https://arxiv.org/abs/2610.05607) (`arxiv:2610.05607`) is a template for the hard-stop field: block-randomised trials at three speeds (45, 55 and 65 cm/s), an independent pose truth beside the encoders, and the result stated as the reaction distance for 90 % success with its uncertainty rather than one stopping distance. In Little World the truth is the simulator's pose; logging the encoders' heading beside it shows the odometry error the paper measured (4.7-5.1 degrees for reverse spins). FR-025's lightest-loaded-wheel margin is the same quantity as the 5 October MNGR note.
- Note (weekly run, 2026-11-02): [On Shaky Ground (2610.36725)](https://arxiv.org/abs/2610.36725): on a light unactuated wheeled base only 54-70 % of a 100 N tool force was realized and the tool drifted up to 100 mm until base-ground resistance was raised. The kit cart stands on free swivel casters (ADR 0041), so an arm's push partly moves the cart: a hard-stop field could add an arm pushing on a wall - force realized against commanded, base drift, drive wheels held against free. Bears on LW-035 too.

### FR-006 · Disturbances during a run, and recovery
- Status: done (ADR 0030, 2026-10-03; accepted by the owner the same day)
- From: [RoboRecover: benchmarking robot policy recovery under execution deviations](https://arxiv.org/abs/2609.28952)
  (`arxiv:2609.28952`; the abstract could not be read on 2026-10-02)
- Idea: varying a run only at its start misses what a lab does to a robot: the cart is
  bumped, a wheel crosses a slippery patch, a part is moved after it was seen. Recovery is
  tested by causing the deviation in the middle of the task.
- In Little World: ADR 0024 varies conditions at the start. Add variations that happen at a
  moment: a push on the base, a floor patch of a slipperier pair, the cube moved after the
  arm set off. The sweep reports, per disturbance, the share of runs that still meet every
  goal and the time lost.
- How we would know: a shove that moves the stopped cart 1 cm before the arm reaches down:
  with ADR 0025's corrections the jaws still meet the cube within 5 mm, with corrections
  off they miss by about the shove. A cube moved after it was seen is missed either way
  until the cell sees it (FR-011); the sweep says so.
- Cost and needs: small: the variation module, the sweep, a decision record.
- Note (Claude, 2026-10-03): done for pushes and moved parts, not the slippery patch
  (LW-018). Measured, the guess above was too simple: shoved about 2 cm, the cart met every
  goal in 9 of 9 set-ups with corrections and 8 of 9 without; shoved about 6 cm, 3 of 9 and
  none. Past about 4 cm even the corrections fail (ADR 0030, LW-019).
- Note (weekly run, 2026-10-05): LIBERO-MAX's eight event kinds (target and receptacle moved, camera shift, sensor corruption, lighting, visual theme, distractor burst, obstacle inserted) are a checklist for ADR 0030. Little World has the first two; the camera ones are FR-018/FR-021; "obstacle inserted" (a box dropped into the GoTo path) is the next physically meaningful one.
- Note (weekly run, 2026-10-21): [LIBERO-Pro2.0](https://arxiv.org/abs/2610.24587) (`arxiv:2610.24587`) separates 22 static perturbations from 20 runtime interventions; runtime shifts cost 26.5 points on average (up to 32.5) over 17 policies. Little World already keeps the two apart (ADR 0024 static draws, ADR 0030 disturbances); the reports should keep saying which is which.

### FR-007 · A powered roller conveyor for the factory's feeder
- Status: doing (ADR 0067, 2026-11-03, in part: a roller conveyor field - 50 mm steel rollers as capsules, 160 mm
  pallets carried within 0.1 % of their speed to a stop and queued; the cell's feeder still moves its
  parts by hand; taken by the weekly reading's ranking of 2 November, as the owner asked)
- From: [MuJoCo 3.11.0: `geom/surfacevel`](https://mujoco.readthedocs.io/en/latest/changelog.html)
  (`mujoco:3.11.0#1`, radar: adopt); [Drake 1.57: virtual conveyor belts](https://drake.mit.edu/release_notes/v1.57.0.html)
  (`web:drake-1.57`, radar: learn); OPEN LW-005
- Idea: a belt is a surface that moves, and MuJoCo 3.11 models one as a static geom with a
  surface velocity - but 3.11 has no Intel-Mac wheels. A powered roller conveyor, a row of
  rollers turning at one speed, is a real lab component and works on any release.
- In Little World: the factory's feeder teleports parts today. A roller conveyor module:
  rollers on hinges, each held at one speed by a velocity servo, a stop plate at the cell;
  a part dropped at the far end arrives at the pick position.
- How we would know: a box on the rollers travels at their surface speed (angular speed
  times radius) within 3 % once settled; it stops against the plate without climbing it;
  over a variation sweep it arrives within 5 mm of the pick position and the cell picks it
  every time; the factory run's frame time with the conveyor full is measured and stated.
- Cost and needs: contacts between every roller and every part cost frame time; no new
  dependency. When the pin passes 3.11 a belt becomes a second module, not a replacement.
- Note (weekly run, 2026-10-19): nothing new - no conveyor paper in what was read; `geom/surfacevel` still needs 3.11.
- Note (weekly run, 2026-10-21): [LIBERO-Industry](https://huggingface.co/papers/2610.16782) (`arxiv:2610.16782`) grades conveyor work by three task kinds (loading onto, unloading from, transfer between moving surfaces) and by conveyor speed and interaction window. When the feeder becomes a conveyor, these are the factors to sweep; FR-029 supplies the metrics first. `geom/surfacevel` still needs 3.11.

- Note (Claude (Cowork), 2026-10-26): the cell's parts are too short for rollers. Interroll's planning guide ("Conveyor rollers: planning", read 26 Oct): "the roller pitch must be selected so that the conveying good is carried by three conveyor rollers at any given time"; the smallest rollers it names are 20 mm. The cell's parts are 32 mm square, so a roller line could carry them only on carriers (pallets) or not at all; a belt - MuJoCo 3.11's `geom/surfacevel`, past the 3.10 pin - or a shuttle on a slide would. Which, if any, is the owner's call.
- Note (weekly run, 2026-11-02): MuJoCo 3.17.0 (22 Oct) says nothing about macOS wheels; the pin stays. Upcoming: a `surfacevel[3]` field in each contact - a belt's speed seen per contact.

### FR-008 · Agents write block programs, graded by the fields
- Status: proposed
- From: [CaP-X](https://arxiv.org/abs/2603.22435) (`arxiv:2603.22435`, radar: learn);
  [Project Fetch, phase two](https://www.anthropic.com/research/project-fetch-phase-two)
  (`web:anthropic-project-fetch-2`, radar: learn); [Coding agents for generalized task and
  motion planning problems](https://arxiv.org/abs/2609.30233) (`arxiv:2609.30233`, title
  only, not yet read)
- Idea: language-model coding agents write working robot programs when they are given good
  helper functions, and fail at fine closed-loop control; the helpers matter more than
  the model.
- In Little World: block programs are such helpers - drive to a point, an aimed pose,
  grip, wait - over closed loops the app already runs (ADR 0018, 0025), and they save as
  JSON (`Program.to_json`). A command-line check takes a program file and a field, runs it
  under the variation sweep and prints each goal's success: an agent, or the owner, writes
  the program as text, and the fields grade it.
- How we would know: the Fetch template scores the same through the check as in the app;
  a program written by an agent given only the block vocabulary and the field's goals is
  graded on the same 20 variations as the template, side by side.
- Cost and needs: the check command and a decision record; no dependency. The app calls no
  model: the agent is whoever the owner asks.
- Note (weekly run, 2026-10-05): [LLMs for Model-Based Robot Design](https://arxiv.org/abs/2609.33423) — 0 of 30 direct LLM designs could be verified feasible; feasibility came from making the LLM write an explicit model (relations, compatibility constraints, objectives) and optimising that, and changing modelling assumptions substantially changed the feasible set. If agents are later allowed to choose kit parts, not only write block programs, make them state that model first and let the fields grade the result. This week also had six code-as-policy papers (in `docs/radar/collection.jsonl`) — FR-008's shape (programs graded by fields) is where the field is.
- Note (weekly run, 2026-10-19): four papers this fortnight agree on what makes agent-written programs work - structured failure feedback and validation in stages. [AeroEval](https://arxiv.org/abs/2610.09764) (`arxiv:2610.09764`): static checks, then execution checks, 55 % to 95 %, each stage alone 44 % and 56 %; [BT-Agent](https://arxiv.org/abs/2610.13862) (`arxiv:2610.13862`): predefined skills returning structured failures, a text-only tier at 10.9 times the throughput; [Fly-by-Code](https://arxiv.org/abs/2610.12549) (`arxiv:2610.12549`): diagnostic programs in simulation, false "done" claims 25 to 5, success 31.7 % to 75 %; [BiGym 2.0](https://arxiv.org/abs/2610.07594) (`arxiv:2610.07594`): coding agents beat demonstration-driven RL. Little World has the pieces: blocks are the skills, the run report's named failures are the structured feedback, and the `look` block is the view probe. A cheap static tier - does the program validate, are its poses reachable - before any MuJoCo run would match AeroEval's first stage.
- Note (weekly run, 2026-10-21): [HexaShell](https://huggingface.co/papers/2610.23479) (`arxiv:2610.23479`) is the strongest data point so far for agents writing robot programs: 39.7 % over RoboDojo's 42 tasks, but pushing 92.5 % against tight insertion 8.3 %, and the agent's failures were mostly seen and not fixable - contact was the limit. For Little World that argues for keeping contact-heavy steps inside blocks that already carry tested physics (grasp with its squeeze, set down, look again) and letting the agent compose them; and for grading agent-written programs the HexaShell way - build on some draws, freeze, test on fresh ones (FR-027). Titles only, same direction: SCOPE (certifying program edits, 2610.23128), CoEvolve (2610.23288), Compile Once, Run Cheap (frozen portable skills, 2610.25114), Self-Crystallizing Behavior Trees (2610.25455). Needs the owner's decision on API cost and keys.
- Note (focused reading, 2026-10-21): an MCP server (FR-035) is the natural harness for an agent writing block programs - it would use the same tools a person does.
- Note (weekly run, 2026-11-02): [Alpha (2610.30197)](https://arxiv.org/abs/2610.30197) is the grading FR-008 needs: the agent and a deterministic scripted oracle on identical seeds, faults injected by layer, paired McNemar - here the oracle is the shipped Fetch program and the faults ADR 0030, 0038 and 0053's disturbances, camera faults and latencies. Its whole 20-point gap came from the prompt-to-JSON interface (with valid output both tied, no discordant pairs): validate an agent's block program against the block schema, with plain-language errors, before it runs. [SO-101 Bench (2610.36420)](https://huggingface.co/papers/2610.36420): an LLM agent writing code with a learned grasp 83.2 % against about 61 % for the best learned policies. [FORCA (2610.31841)](https://arxiv.org/abs/2610.31841) reads force records between runs - the run report and the feel registers (ADR 0048) are that record; [RoboAuto (2610.36533)](https://arxiv.org/abs/2610.36533) designs its own experiments - the `look` block and the fields are those. Still needs the owner's decision on API cost and keys.

### FR-009 · Variation ranges from sources, the owner's lab first
- Status: proposed
- From: [MolmoBot](https://allenai.org/blog/molmobot-robot-manipulation) (`web:molmobot`,
  radar: learn); ADR 0024 (its placement and payload ranges are assumptions)
- Idea: MolmoBot was trained only in MuJoCo, on procedurally varied scenes, and works on
  real robots without real training data; the ranges it varied over are a published
  reference. The better reference is the lab where the machines will run.
- In Little World: each range in `fields/variation.py` (set down within 2 cm and 3 deg of
  its mark, a 0.5 kg payload) gets a source, as every friction pair has in
  `contact_pairs.SPREADS`: the owner's measurement where there is one (set the cart down
  by hand ten times and measure), a paper's otherwise. A test fails on a range without one.
- How we would know: that test, and the sweeps rerun with sourced ranges, their spreads
  reported beside the assumed ones.
- Cost and needs: a tape measure and a few minutes of the owner's time; reading MolmoBot's
  paper for its ranges, not only the blog.
- Note (the owner, 2026-10-03, relayed by Claude): not now - no lab work for the moment.
- Note (weekly run, 2026-10-05; the owner: not now - evidence only): [real-to-sim reconstruction effects](https://arxiv.org/abs/2610.00731) — authored metric geometry and physics parameters vs engine defaults: r = 0.90 vs 0.51 with real success, mean error 6.97 vs 17.54 points (10 task-policy pairs × 20 runs). Cite it in the ADR that takes FR-009: sourced numbers are what make a simulated rate predict the lab.
- Note (weekly run, 2026-10-19; the owner: not now - evidence only): [Same Action, Different Outcome](https://arxiv.org/abs/2610.10801) (`arxiv:2610.10801`) found real repeat-variability one to three orders of magnitude above the robot's repeatability, which calibrated simulators did not reproduce. When ranges are taken from the owner's lab, repeating one fixed set-up ten times on the real machine measures that spread directly - the one number a simulation cannot supply.
- Note (weekly run, 2026-10-21): (the owner: not now - evidence only, no action asked) [ContactBench 1.0](https://arxiv.org/abs/2610.24512) (`arxiv:2610.24512`) pairs objects printable on consumer 3D printers with simulation models whose resistance load can be tuned - a pattern for the owner's lab: a printed fixture and its twin, measured both ways.
- Note (weekly run, 2026-11-02): (the owner: not now - evidence only) [PhysLadder (2610.34527)](https://arxiv.org/abs/2610.34527) matched sim and real task by task (10 of 16 identical counts at three trials); [SO-101 Bench](https://huggingface.co/papers/2610.36420) kept the exact ranking of five policies from simulation to the real arm (Spearman 1.00) while overestimating success: when the lab comes, compare rankings of designs as well as rates. [Your Benchmark Is an Empirical Measure Over Difficulty (2610.29927)](https://huggingface.co/papers/2610.29927): a rate means something only with the distribution it was drawn from - ADR 0024's variation box - so a lab-sourced range changes what every rate means.

### FR-010 · A real servo on a pendulum bench, fitted
- Status: proposed
- From: [MuJoCo 3.5.0: system identification toolbox](https://mujoco.readthedocs.io/en/latest/changelog.html)
  (`mujoco:3.5.0#2`, radar: adopt); [Extended friction models for the physics simulation
  of servo actuators](https://arxiv.org/abs/2410.08650) (`arxiv:2410.08650`, radar: learn);
  [Trajectory-based actuator identification via differentiable simulation](https://arxiv.org/abs/2604.10351)
  (title only, not yet read); OPEN LW-009
- Idea: a servo's friction is not its datasheet's: it sticks, dips as it starts to slide
  and grows with load. The paper identifies these models by letting a pendulum swing on
  the servo; MuJoCo's toolbox fits a model's parameters to recorded motion.
- In Little World: a pendulum bench field - one XH430 servo, a link of known mass,
  released from several angles - and the same rig built for real. The real servo reports
  its own position over its bus (a U2D2 adapter); the toolbox fits damping, friction and
  armature, or, on 3.10, a `dcmotor` with its on-board controller and LuGre friction
  standing for the whole servo; the fitted numbers enter the servo's profile with
  "measured on the owner's bench" and the date as their source, beside the datasheet's.
- How we would know: fitted on two release angles, the model replays a third swing it was
  not fitted on with at most half the angle error (RMS over three seconds) of the
  datasheet model.
- Cost and needs: hardware: one XH430, a U2D2, a printed link (LW-009, the owner's call);
  FR-002 first; the toolbox installs as `mujoco[sysid]` (SciPy, Matplotlib, Plotly and
  more), kept out of the core. It is the whole sim-to-real loop on one joint, and a good
  first lesson in it.
- Note (the owner, 2026-10-03, relayed by Claude): not now - no hardware for the moment.
- Note (weekly run, 2026-10-05; the owner: not now - evidence only): TeAR's inputs are joint temperature, motor current and supply voltage. The XH430 reports all three (X-series control table), so the pendulum bench should log them with position; the fit can then say how friction and torque change as the servo warms, and gives FR-019 servo numbers. The [actuator digital-twin paper](https://www.mdpi.com/2076-0825/15/8/451) used the same bench shape (1-DoF pendulum, MuJoCo).
- Note (weekly run, 2026-10-19; the owner: not now - evidence only): BAM ([identified actuators](https://bam.readthedocs.io/en/latest/usage/actuators.html), the code of arXiv 2410.08650) has bench recording, fitting and MuJoCo-on-CPU guides and published parameters for Dynamixel MX-64, MX-106, XL-320 and XL-330 (not the XH430); its README reports that friction models M2-M6 cut simulation error by more than half against Coulomb-viscous on 2R arms. [IDTD](https://arxiv.org/abs/2610.10905) (`arxiv:2610.10905`) designs the bench trajectory so each segment exposes different parameters (39.6 % lower identification error). Menagerie lists a "Dynamixel 2R" model (README only, not opened). A hardware-free first step, if ever wanted: record the simulated XH430 on a simulated pendulum, fit it back with the same tool, and see which parameters a bench can separate.

### FR-011 · Grasping from the cell's camera, classical first
- Status: done (ADR 0032, 2026-10-04, for the Fetch table; accepted by the owner 2026-10-03.
  The factory cell still grasps at known positions: LW-010)
- From: [FoundationPose](https://huggingface.co/nvidia/foundationpose)
  (`hf-model:nvidia/foundationpose`, radar: watch); OPEN LW-010
- Idea: real cells find their parts with a camera. Learned pose estimators such as
  FoundationPose need a GPU; for known boxes on a known table depth alone is enough:
  remove the table's plane, cluster what is left, fit the box.
- In Little World: the factory cell's camera renders a depth image (MuJoCo renders depth);
  a perception module outside the core turns it into the part's position and yaw, and the
  pick pose comes from that instead of from the Blueprint.
- How we would know: over a sweep of part placements, position within 5 mm and yaw within
  5 deg of the truth, and the cell picks as often as with true positions; then again with
  a real depth camera's noise added, from its datasheet.
- Cost and needs: numpy only; rendering needs a display or an offscreen context (the
  window tests run under xvfb); the direction is the owner's choice (LW-010).
- Note (Claude, 2026-10-04): done at the Fetch table, where the measured failure was (the
  cube moved 5 cm: none of 9). A RealSense D435 on a stand beyond the table, with its maker's
  numbers; MuJoCo's rays instead of its renderer, so no display or GL context is needed and
  the suites stay headless. Over 80 placements the cube was found within 2.4 mm and 6 deg
  (median 1.3 mm, 0.6 deg; 9 of 1600 noisy pictures over 5 deg, the cube turned 45 deg). The
  Fetch program looks once stopped and aims there: the cube moved 5 cm, 9 of 9; set down up to
  8 cm off before the run, fetched where blind it was not - except 6 cm further along the
  table, out of the arm's reach from its stop (FR-016). Moved after the look, it is missed
  (FR-015). Yaw is measured, but the four-joint arm cannot use it.

### FR-012 · Runs exported as LeRobot datasets
- Status: proposed
- From: [LeRobot 0.6](https://huggingface.co/blog/lerobot-release-v060) (`web:lerobot-0.6`,
  radar: learn); [LeRobotDataset v3.0](https://huggingface.co/blog/lerobot-datasets-v3);
  [SmolVLA](https://huggingface.co/lerobot/smolvla_base) (`hf-model:lerobot/smolvla_base`,
  radar: learn)
- Idea: robot learning shares one dataset format - per-frame joint states and actions in
  Parquet, camera streams as video, metadata in JSON. Policies train on it and real robots
  record into it.
- In Little World: an exporter outside the core writes a run - joint positions and
  velocities, commands, the cell camera's frames - as a LeRobot dataset, so a variation
  sweep becomes a dataset of 20 episodes, and recordings of the owner's real machine in
  the same format can sit beside the simulated ones.
- How we would know: LeRobot's own loader reads an export back with the run's frames and
  joint values unchanged; replaying an exported Fetch episode's commands in Little World
  meets the same goals.
- Cost and needs: an optional dependency (pyarrow and a video encoder), never in the core.
  LeRobot itself needs PyTorch, whose Intel-Mac wheels stopped after 2.2, so the loader
  check may run on Linux. Training a policy is a separate decision.
- Note (weekly run, 2026-10-19): [Traceable World State](https://arxiv.org/abs/2610.12033) (`arxiv:2610.12033`): ordered, hash-chained records gave exact terminal-state replay in 103 of 103 episodes and caught 412 of 412 injected corruptions for 1.72 % more storage than plain JSONL. Exported runs could carry the commit, the MuJoCo version, a hash of the compiled model and the draw seed, with a hash chain over the run, so any number in an ADR can be re-derived and checked (stdlib `hashlib`). LeRobot is unchanged since v0.6.1 (3 August).
- Note (weekly run, 2026-10-21): LeRobot still v0.6.1.
- Note (focused reading, 2026-10-21): the robot library's imported models would make exported runs (LeRobot) about robots other than the kit's.
- Note (weekly run, 2026-11-02): [From 12 to 200 Demonstrations (2610.37170)](https://arxiv.org/abs/2610.37170) measured the noise of ten-episode blocks (the same checkpoint differed by 2 in 10) and sorted episodes into stages: an export should carry each episode's seed, set-up and stage reached. LeRobot still v0.6.1. Needs an optional dependency (pyarrow): not added (AGENTS.md), so it waits.

### FR-013 · A second engine's opinion on the static tests
- Status: proposed
- From: [Drake 1.57](https://drake.mit.edu/release_notes/v1.57.0.html) (`web:drake-1.57`,
  radar: learn)
- Idea: when a result moves between MuJoCo releases (the tilt table: 54.5 deg on 3.3.7,
  52.6 on 3.14, ADR 0023), a closed-form prediction says which is nearer - but only where
  one exists. An engine with a different contact model, Drake's compliant contact with an
  error-controlled integrator, is an independent check.
- In Little World: a script outside the app loads the tilt-table and stance scenes into
  Drake (it reads a subset of MJCF) and prints the tip angle and margin beside MuJoCo's and
  the prediction.
- How we would know: the three agree within 1 deg, or the difference is traced to a
  modelling choice and written down; either is a result.
- Cost and needs: pydrake (whether it installs on an Intel Mac is to be checked; Linux runs
  it) and scenes trimmed to what Drake parses; nothing in the app changes.
- Note (weekly run, 2026-10-19): Drake's [v1.27.0 notes](https://drake.mit.edu/release_notes/v1.27.0.html) say support for x86_64 ended in v1.22.0; v1.40.0 lists only a mac-arm64 tarball, and the v1.57.0 wheel list shows macOS arm64 (truncated). Drake will probably not install on the owner's Intel Mac: a second engine fits a check that runs on Linux (the cloud session) rather than in the app.
- Note (weekly run, 2026-10-21): Drake still at v1.57.0; nothing new.
- Note (weekly run, 2026-11-02): the same paper's first sim-to-sim gap was the harness (a missing floor, a wrong timestep), not the engines: before comparing Drake with MuJoCo on the static tests, compare the two harnesses on a box at rest and a free fall. Drake v1.58.0 needs macOS 26 and its visible Mac builds are arm64 only: Linux only here.

### FR-014 · Past the 3.10 pin: the engine's PID servo and moving surfaces
- Status: proposed (blocked: no MuJoCo wheels newer than 3.10.0 for Intel Macs)
- From: [MuJoCo 3.12.0: the `pid` actuator](https://mujoco.readthedocs.io/en/latest/changelog.html)
  (`mujoco:3.12.0#3`, radar: adopt); MuJoCo 3.11.0's `geom/surfacevel` (`mujoco:3.11.0#1`);
  OPEN LW-005, LW-006
- Idea: the engine's own PID servo, correct under every integrator, could replace ADR
  0014's Torque slope; a surface velocity makes a belt without moving parts.
- In Little World: nothing until the pin can pass 3.10: on Apple silicon or Linux, or with
  MuJoCo built from source for the owner's Mac.
- How we would know: ADR 0014's servo damping tests pass with `pid` in place of the slope;
  a belt carries a box at its surface speed within 3 %.
- Cost and needs: a newer Mac, a Linux machine, or a source build (CMake, the C library,
  then the Python bindings): the owner's call.
- Note (weekly run, 2026-10-05): no MuJoCo release since 3.14.0 (22 Sep 2026), so nothing changes for the 3.10.0 pin (decided on 2 Oct, after 3.14.0). For the day it lifts: 3.13.0 added "single-shot multicontact for collisions with cylinder geoms" — every wheel is a cylinder and ADR 0027 turned multiccd off because extra wheel contacts added a rolling loss, so re-run the coast-down first; the unreleased version adds the same for capsules and changes how `dampratio` is computed — check whether any Little World actuator uses `dampratio` (ADR 0014).
- Note (weekly run, 2026-10-19): two releases since the last reading, 3.15.0 (5 October) and 3.16.0 (14 October); macOS x86_64 wheels could not be checked (the PyPI file list was unreadable), so the 3.10.0 pin stands. For the day it lifts: 3.15.0 made `dampratio` breaking (operational-space inertia at `qpos0`; check whether any kit actuator uses it, ADR 0014); 3.16.0's contact sensor reports relative contact velocity, a direct slip measurement for wheels and jaws; upcoming, multicontact also for geoms with a positive margin. One item for now: 3.16.0 says that changing a geom's size, pose, margin or gap on a compiled model could miss contacts before (stale bounding volumes).
- Note (Claude, 2026-10-20): checked on 3.10.0 - nothing changes a geom's size, pose, margin or gap on a compiled model. Variations add the payload to the Blueprint and compile it anew, friction is written per contact (ADR 0010), a moved cube moves through its free joint, the camera's pose is not a geom's, and the Build tab's drag preview moves a whole body (`body_pos`), whose bounding volumes are in its own frame.
- Note (weekly run, 2026-10-21): no MuJoCo release since 3.16.0; the wheel question is still unanswerable from here (PyPI text cut before the file list; `/simple/` closed to the fetch tool). For the day the pin lifts, the Upcoming notes add: solver termination scaled by the inertia trace with `meaninertia` deprecated - anything that depends on how far the solver converges (noslip, ADR 0017; the hold of ADR 0042) is re-checked first; named-access fixes for actuators and per-dof fields - re-run the compiled-gains test proposed on 19 Oct. Strategic: [NEP 57](https://numpy.org/neps/nep-0057-numpy-platform-support.html) expects NumPy's macOS x86-64 support to end by 2027/28 - an end date for the Intel Mac independent of MuJoCo (also FR-002); moving development to Apple silicon or Linux is the owner's hardware decision and would lift the 3.10 pin.
- Note (weekly run, 2026-11-02): MuJoCo 3.17.0 (22 Oct): a batch simulation API (it might run sweeps in parallel on a CPU, to measure then), position actuators' `dampratio` resolved only at compile time (check ADR 0014 and 0016's actuators when the pin lifts); upcoming speculative contacts and per-contact `surfacevel`; nothing on macOS x86_64 wheels.

### FR-015 · Looking again when a grasp misses
- Status: done (ADR 0033, 2026-10-04; accepted by the owner the same day)
- From: ADR 0032's own measurement (the cube moved 5 cm 2 s after the look: none of 9, the
  grasp check holding nothing); [RoboRecover](https://arxiv.org/abs/2609.28952)
  (`arxiv:2609.28952`), recovery from deviations during execution; OPEN LW-020
- Idea: a grasp check that fails says the object is not where the jaws went. A pick cell
  that can see opens its jaws, looks again and tries once more before it gives up.
- In Little World: when a grasp check fails at a stop where the program looked, the runner
  opens the jaws, takes them back up to the pose before the descent, looks again and repeats
  the approach once - a cap like going back's (ADR 0031), a runner parameter, counted in
  `Run`.
- How we would know: "cube moved 5 cm sideways, 2 s later" goes from none of 9 to most of
  them; undisturbed and under the other disturbances nothing changes; the seconds it costs
  are reported.
- Cost and needs: small: the runner, which blocks a retry repeats, tests, a decision record.
- Note (Claude, 2026-10-04): built as proposed, it looked again in 1 of the 9 set-ups: in 8
  the jaws came down onto the moved cube and the reach could not settle before any grasp was
  checked, and in the ninth the cube had been knocked out of reach. So the program also takes
  one more picture just before the jaws go down, and looks again when a reach is stopped -
  once per run in all. Cube moved 5 cm 2 s later: 9 of 9, the jaws never touching it; nothing
  else changed (ADR 0033).

### FR-016 · Planning the stop from where the camera sees the cube
- Status: done (ADR 0035, 2026-10-07; accepted by the owner the same day)
- From: ADR 0032's own measurement (the cube 6 cm further along the table, seen within
  0.4 mm, out of the arm's reach from the stop planned for it); OPEN LW-021
- Idea: the table camera sees the cube from anywhere: look before driving, and stop where
  the arm can reach the cube where it is, as a mobile manipulator plans its base from what it
  perceives rather than from a map.
- In Little World: the Fetch program's first look comes before its drive to the table; the
  stop is placed from where the cube was seen (a goto aimed relative to the object, as poses
  are), and the look at the stop stays for the grasp.
- How we would know: the cube set down 6 and 10 cm further along the table, or 15 cm
  sideways, is fetched; the placements fetched now still are; the run is no slower when the
  cube is where planned.
- Cost and needs: small to medium: the runner (a goto re-aimed by a look), the template,
  tests, a decision record.
- Note (weekly run, 2026-10-05): two titles this week ([base placement via capability maps, 2609.33096](https://arxiv.org/abs/2609.33096); [UniWAM anchor-pose supervision, 2609.39388](https://arxiv.org/abs/2609.39388)) are about where the base should stop so the arm can reach. The classic, non-learned answer is an inverse reachability map (background: Vahrenkamp, Asfour, Dillmann, "Robot placement based on reachability inversion", ICRA 2013 — not read this week): precompute once per arm from the existing IK where the base may stand for a given tool pose, then pick the stop nearest the planned path. CPU and stdlib.
- Note (Claude, 2026-10-07): done as proposed, with one correction from measuring - the stop cannot follow a cube further along the table all the way: the cart's front stands 3.3 cm from the table's edge at the planned stop, so it follows 2.3 cm and the arm reaches the rest, up to 28 cm ahead of its axle. Fetched: 6 and 7 cm further along, 15 cm to either side, 6 cm along and 15 cm sideways together, and every placement of ADR 0032; 8 and 10 cm further along are refused at the table as out of reach, said before the arm moves. The inverse reachability map of the note above was not needed: the arm's poses hold when the stop moves with the cube.

### FR-017 · Paired runs: the same draw with and without the event
- Status: done (ADR 0036, 2026-10-07; accepted by the owner the same day)
- From: the weekly reading of 2026-10-05 (FR-W01): [LIBERO-MAX, arXiv 2609.36518](https://arxiv.org/abs/2609.36518) (`arxiv:2609.36518`) and its [project page](https://liberomax.github.io) (pairs share task, start, seed and the actions before the event; paired 95 % bootstrap intervals; 11.0–25.7-point drops).
- Idea: Give every disturbed run a twin — the same drawn variation, seed and program, without the event. MuJoCo is deterministic, so the two runs are identical up to the event and any difference in outcome is caused by the event alone. Report four cells (both succeed / the event broke it / the event rescued it / both fail) instead of two separate rates, and test the effect on the discordant pairs.
- In Little World: `inventory/sweep.py --disturb --paired` (the undisturbed twin cached by draw seed, so ADR 0024/0028 sweeps can reuse it); `inventory/confidence.py` gains an exact McNemar test (binomial on discordant pairs, `math.comb`, stdlib) beside Clopper-Pearson; "Repeat with disturbances" in the run report shows "broken by the event: k of n successes". Extends ADR 0028 and 0030.
- How we would know: (1) a test that twin trajectories are bitwise equal (qpos) up to the step before the event, on Fetch and Sprint; (2) a 0/9-vs-9/9 result like "cube moved 5 cm, 2 s later" before ADR 0033 becomes 9 discordant pairs, exact McNemar p = 0.0039 — a defensible claim from nine runs (re-run that case paired to see what ADR 0033 changed); (3) on the 59-draw Fetch sweep with the default disturbance, "k of 59 successes broken by the event" with its interval, consistent with today's unpaired rate.
- Cost and needs: about a day; stdlib only; twice the disturbed runs (twins cacheable); no MuJoCo change.
- Note (Claude, 2026-10-07): done, with three differences from the proposal. No `--paired` flag and no cache: a disturbance sweep already runs every set-up undisturbed beside its disturbed runs, so every report pairs them. Nine pairs before ADR 0033 became eight, and p = 0.0039 became 0.0078: the as-designed set-up is chosen, not drawn, and stays out of the count (ADR 0028). The step check uses a digest of every joint's position and speed, not positions alone. Measured with looking again, on the 59-draw Fetch sweep with the cube moved 5 cm 2 s after the look: 1 of 59 successes broken (0 to 9 %), p = 1, consistent with the rates alone (59 of 59 against 58 of 59); the one broken pair showed a new failure, the arm dragging a cube it had come down on off the table (OPEN LW-023).
- Note (weekly run, 2026-10-19): [arXiv 2610.06921](https://arxiv.org/abs/2610.06921) (`arxiv:2610.06921`) uses the same paired design - with and without correction, same seed - at 3,888 episodes; FR-023 extends ADR 0036 to compare recoveries with each other.

### FR-018 · A camera that can fail: frozen picture and blackout
- Status: done (ADR 0038, 2026-10-08; accepted by the owner the same day)
- From: the weekly reading of 2026-10-05 (FR-W02): LIBERO-MAX's observation events "camera shift" and "sensor corruption" ([project page](https://liberomax.github.io), `arxiv:2609.36518`); [Blackout vs. Freeze: Analyzing Physical Failure Modes of VLAs under Camera Faults, arXiv 2609.39145](https://arxiv.org/abs/2609.39145) (`arxiv:2609.39145`, title only).
- Idea: Add two camera faults to the disturbances — frozen (the camera keeps returning the picture from time t) and dark (no valid depth from t) — and make `look` notice them. Today `look` waits for 3 pictures agreeing within 5 mm; a frozen camera delivers exactly that, of a world that has since moved, so it would pass silently and the jaws would close on air. Real D435 frames carry a frame number and timestamp: require the counter to advance and a minimum valid-pixel fraction in the window, otherwise end the look with a named failure ("camera stale", "camera dark") and no motion.
- In Little World: `fields/disturbance.py` kinds `camera_freeze`, `camera_dark` (timed like the others); `perception/eye.py` stamps each picture (frame counter, sim time) and reports the valid fraction; the runner's `look` checks both; the run report shows the named failure. Extends ADR 0032/0033 and 0030.
- How we would know: Fetch, 9 set-ups, "cube moved 5 cm + camera frozen at the move": measure first without the check (expected: silent misses at the old place), then with it (target 9/9 end "camera stale", zero grasps at the stale place); blackout 9/9 named "camera dark"; the undisturbed 59-draw sweep still 59/59 with the same times (no false alarms); a unit test with a fake camera that repeats one frame.
- Cost and needs: 1–2 days; stdlib + the existing numpy perception; no new dependency.
- Note (Claude, 2026-10-05): with ADR 0033 the picture before the jaws go down comes from the same frozen camera and agrees, and the look after a missed grasp sees the old place again, so the expectation above holds: one wasted grasp, then a second at the stale place.
- Note (Claude, 2026-10-08): done, with the timing of "cube moved 5 cm sideways" (as the cart stops, during the look). On trust, as the 5 October note expected: the jaws went down twice at the stale place in all 9 set-ups, ending "Timed out: pose did not settle" (5) or "Nothing held" (4). Checked: all 9 named at the look, "the camera's picture is not new", nothing grasped; dark: all 9 "has no depth"; the 59-draw undisturbed runs as before to the millisecond. Two differences from the proposal: the kinds are a `camera` field ('freeze', 'dark') on any disturbance, so a fault can come with a move; and the frame number alone decides staleness (the picture's time is kept, not checked), so a frame frozen less than one picture interval before its first use is used once.
- Note (weekly run, 2026-10-19): [PIER](https://arxiv.org/abs/2610.12123) (`arxiv:2610.12123`) measured both error kinds of a gate with one re-observation: re-looking cut wrong refusals from 57 to 18 of 120 but raised wrong proceeds from 5 to 7 of 120, and stale or falsely reassuring inputs beat thresholds. The `look` (ADR 0033, 0037, 0038) could report both kinds - wrongly refusing and wrongly proceeding - under added depth noise, not only successes.
- Note (weekly run, 2026-11-02): [Black-box sensor diagnosis (2610.36852)](https://arxiv.org/abs/2610.36852) reports false triggers on fault-free runs (0 of 64) beside its repairs, and a surrogate that predicted as well and repaired nothing: prediction is not usefulness, ADR 0051's lesson.

### FR-019 · A weakened motor among the disturbances
- Status: done (ADR 0058, 2026-10-27: 'motor' disturbances - a motor's own line scaled, its friction kept; a winding 50 K hot keeps 84 % of its stall torque (copper 0.00393/K, NBS Circular 31); the kit cart notices nothing on any drive field or the Fetch, run for run the same: its drive asks no motor for more than its 0.5 N m cap; on the Sprint a motor can drop to 30 % before a change; the predicted curve was not seen; taken by the weekly reading's ranking)
- From: the weekly reading of 2026-10-05 (FR-W03): [TeAR, arXiv 2609.36182](https://arxiv.org/abs/2609.36182) (`arxiv:2609.36182`: heating, current saturation, voltage sag → "weaker, delayed, or noisier motion"); [rovers under wheel-to-wheel traction asymmetry, arXiv 2609.38715](https://arxiv.org/abs/2609.38715) (`arxiv:2609.38715`, title only).
- Idea: Disturb an actuator instead of the body: from time t one drive motor gives less torque and speed, sized from physics rather than picked. Copper's resistance rises 0.393 %/K (handbook value), so a winding 50 K hotter has 19.7 % more resistance and, at fixed voltage, 84 % of its stall torque; a supply sagging 10 % (assumed — to be sourced from a battery datasheet) cuts no-load speed 10 %. One weak wheel on a differential drive makes the machine curve — the textbook reason robots need heading feedback.
- In Little World: `fields/disturbance.py` kind `motor_weak` (motor, torque factor, speed factor, time); `MujocoBackend.weaken(...)` scales that actuator's gain and force range between steps; the Pololu 37D profile (ADR 0007/0011) supplies the factors with their sources; the run report names the motor and the factor. Extends ADR 0030.
- How we would know: Sprint with one motor at 84 % torque from the start — lateral drift at the finish vs the closed-form curvature from the two wheel speeds, agreement stated in %; Fetch with one base motor weak — added time and stop error, paired with FR-017; a test that factor 1.0 changes nothing bit-for-bit.
- Cost and needs: about a day; stdlib; independent of FR-004 (dcmotor would later let resistance itself be the parameter).
- Note (weekly run, 2026-10-19): nothing usable - the one actuator-degradation paper this fortnight ([arXiv 2610.10934](https://arxiv.org/abs/2610.10934), `arxiv:2610.10934`) gives no degradation model in its abstract.

### FR-020 · How gently: peak force and tilt of the handled part, beside success
- Status: done (ADR 0040, 2026-10-09; accepted by the owner the same day)
- From: the weekly reading of 2026-10-05 (FR-W04): [ManiPhysicsBench: Physics-Based Assessment of Object Preservation in VLA Manipulation, arXiv 2610.02802](https://arxiv.org/abs/2610.02802) (`arxiv:2610.02802`, title only); [Is Success All You Need?, arXiv 2610.01351](https://arxiv.org/abs/2610.01351) (`arxiv:2610.01351`, title only).
- Idea: A Fetch that succeeds after knocking the cube over or dropping it from height is not a lab-ready success — in a real lab the cube is a vial. Record for the handled part: peak contact force per partner (jaws, table, bin), the contact impulse at grasp and at release, its largest tilt, and its height when let go; report median and spread like times.
- In Little World: `MujocoBackend` sums `mj_contactForce` over contacts that involve the part's geoms each step (available in 3.10); `Run` gains `part_peak_force_N`, `part_impulse_Ns`, `part_max_tilt_deg`, `release_height_mm`; a "handled gently?" row in the run report with limits from each gripper's published force range (sourced per arm); sweeps show the distribution. A new ADR, citing ADR 0016's grasp checks.
- How we would know: (1) instrument check — a cube resting on the table reads m·g within 1 % as total normal force; (2) the known rough case (blind template with the cube moved, where the jaws used to knock it) shows tilt above 10° and a force spike, the looking template (ADR 0032) does not; (3) peak forces in MuJoCo's soft contacts depend on timestep and solref — run at two timesteps, and if peaks differ by more than 20 % report impulse only (the better-conditioned quantity). That last point is itself a lesson worth writing down.
- Cost and needs: 1–2 days; stdlib + the existing MuJoCo API.
- Note (Claude, 2026-10-09): done, with three changes from the proposal. Forces are the hardest push from any one body of each partner, not their sum: two jaws squeezing from either side cancel in a sum. The impulse at grasp and release became the force averaged over 50 ms (a sensor reading 20 times a second), which moved by at most 4 % when the step was halved, against 12 % for the force in a step - under the proposal's 20 %, so both are reported. No "handled gently?" verdict: the kit gripper's force rating is not published and no fragility is sourced. Measured: squeeze 4.8 N, a 6 cm drop into the bin, and 4 of 59 successes that pressed the cube into the table first (OPEN LW-024, LW-025); the blind rough case pressed it into the table at 5 N, which the table's push - not the machine's - tells apart.

### FR-021 · How well must the camera be mounted? A calibration tolerance for the Fetch table
- Status: done (ADR 0039, 2026-10-08; accepted by the owner the same day)
- From: the weekly reading of 2026-10-05 (FR-W05): LIBERO-MAX's "camera shift" event ([project page](https://liberomax.github.io), `arxiv:2609.36518`); [CoRe-VLA under camera shifts, arXiv 2609.37150](https://arxiv.org/abs/2609.37150) (`arxiv:2609.37150`, title only); [DRHeC hand-eye calibration, arXiv 2609.36779](https://arxiv.org/abs/2609.36779) (`arxiv:2609.36779`, title only).
- Idea: The program believes the camera is where `fields.CAMERA_AT` says; a real stand is set up by hand and gets bumped. Move the true camera away from the believed pose (yaw/pitch 0, 0.5, 1, 2°; position 0, 5, 10, 20 mm) while the program keeps the believed one, and find the largest error at which Fetch still succeeds at ≥ 95 % (Clopper-Pearson, ADR 0028). Predict it first: at range d a yaw error δ moves the seen cube by d·tan δ — 10.5 mm per degree at 0.6 m (assumed range; the real one is in `CAMERA_AT`) — against the jaws' capture margin. The result is a number for a real bench: "mount the D435 within X° and Y mm, or calibrate it".
- In Little World: `Field.camera` gets a true-pose offset separate from the believed pose (a variation source, ADR 0024); `sweep --camera-error`; a tolerance table in `docs/sweeps/`. Extends ADR 0032; shows how much ADR 0033's looking again already absorbs.
- How we would know: the table with intervals; failure onset within one sweep step of the closed-form prediction; zero offset reproduces 59/59.
- Cost and needs: about a day of work plus CPU time (8 offsets × 59 draws ≈ 470 Fetch runs — time it first); stdlib; no hardware.
- Note (Claude, 2026-10-05): the camera's range to the cube is about 0.87-0.90 m (`fields.CAMERA_AT` (2.30, 0, 0.90) aims at (1.85, 0, 0.12)), so a degree of yaw moves the seen cube about 15 mm there, not 10.5.
- Note (Claude, 2026-10-08): done. Pan 15.3 mm a degree (as the 5 October note said), tilt 13.1 mm along and 7.8 mm down, a shift minus itself; the jaws' margins came from shifting the camera (10.5 mm too far, 25 mm sideways, 10.3 mm too low; more the other ways), and with them the closed form put the onsets where they were measured: pan between 1.75 and 2 degrees, tilt up between 0.75 and 1. On 59 drawn set-ups: pan 1.5, tilt up 0.5 and 10 mm up held at least 95 %; 10 mm towards the cart, 58 of 59 (the edge); tilt up 1, 8 of 59. Not a variation drawn per set-up as proposed but a condition of the sweep (`--camera-error`), one error per sweep; about 370 Fetch runs.

### FR-022 · How late is too late: branch each failing run from its checkpoints
- Status: done (ADR 0052, 2026-10-23: `Runner.alarm` - an alarm from outside makes a program that looked recover as its own recovery does - and a recovery 'ignore'; branches by replaying the deterministic run with the alarm, no snapshot needed; the cube moved 2 s after the look: an alarm rescued until the program left the table in 5 of 9 set-ups and until its own closing tipped the cube over in 4, its own check at least 0.28 s before that deadline in all 9; a frozen camera has no window (prediction 3 does not hold); 71 false alarms: 70 still met every goal, about 6 s later, the one broken an alarm while the cube was held (OPEN LW-033, LW-034); taken by the weekly reading's ranking)
- From: the weekly reading of 2026-10-19 (FR-W01): [RESCUE: Is This Alarm Worth Acting On?, arXiv 2610.13516](https://arxiv.org/abs/2610.13516) (`arxiv:2610.13516`: simulator and policy state restored at checkpoints and branched with alternative actions, 128,340 branches; whether a failure is recoverable depends on state and intervention together; an idealised detector tolerated only a 2.0–3.3 % false-alarm rate).
- Idea: A detector is useful only if it fires while recovery is still possible. MuJoCo is deterministic and ADR 0036 relies on a run being identical up to an event, so save the full state (MjData and the program runner's own state) every 0.5 s of a disturbed run that fails, start the program's recovery from each checkpoint (look again, go back, rise and read the place) and find the latest checkpoint that still ends in success - the recovery deadline - against the moment the existing checks fire (ADR 0031, 0033, 0038). The other half: on undisturbed draws, trigger a recovery at a random time and measure what a false alarm costs.
- In Little World: a new `inventory/branch.py` (`checkpoints(run, every_s=0.5)`, `branch(run, at, recovery)`) on the paired-run machinery of `inventory/sweep.py` (ADR 0036); the runner needs a snapshot of its own state (assumed not yet available; the main work). Per disturbance kind: alarm time, deadline, slack, the share of failures recoverable at the alarm. A new ADR citing 0030, 0033, 0036, 0038.
- How we would know: (1) a branch with no recovery reproduces its parent run bit for bit (final qpos equal); (2) a table of deadline and slack for the disturbed set-ups that fail in the current sweeps; (3) a prediction to check: for a frozen camera the deadline is the start of the last descent onto the cube, within one checkpoint; (4) the false-alarm cost in seconds with its spread over 59 draws and the successes a false alarm breaks (target 0, with its Clopper-Pearson bound).
- Cost and needs: 2 days; stdlib; branches run from the checkpoint to the end only, scanned from late to early (assumes recoverability roughly monotone near the end - check by a full scan on two set-ups first). Time one branch first.
- Note (weekly run, 2026-10-21): two titles to read when arXiv lets us - [Coverage Shift in VLM Success Monitoring (2610.24801)](https://arxiv.org/abs/2610.24801) (monitors judged on the harder failures better policies leave) and [Interventional Evaluation of Memory (2610.23372)](https://arxiv.org/abs/2610.23372). And with FR-024: the upcoming MuJoCo Python bindings zero-fill unallocated arena arrays (previously uninitialized). On 3.10.0, a bit-for-bit comparison should therefore compare only qpos, qvel, act, time and arrays cut to their live size (`ncon`, `nefc`) - a one-line check of `inventory/jitter.py`'s comparison and of this proposal's "branch reproduces its parent".

### FR-023 · A plain retreat as the baseline for every recovery
- Status: done (ADR 0051, 2026-10-23: the runner's recovery as a choice - look, retreat, guess (the random re-aim of the 21 Oct note), none; the cube moved after the look: looking again 9 of 9, each baseline 0 of 9, p = 0.0039 each; ties elsewhere; `timed` not run, since the retreat at the detector's moment rescued nothing; taken by the weekly reading's ranking)
- From: the weekly reading of 2026-10-19 (FR-W02): [Does a Learned Corrector Beat a Simple Retreat?, arXiv 2610.06921](https://arxiv.org/abs/2610.06921) (`arxiv:2610.06921`: 3,888 paired episodes; a scripted return to an earlier joint configuration matched the learned pipeline; 43.2 % of failed episodes succeeded on a plain re-run).
- Idea: Little World's recoveries (ADR 0031 going back, ADR 0033 looking again, ADR 0037 rising first and reading the place) were measured against no recovery. A recovery earns its complexity only if it beats the simplest thing that also moves the robot back. Add two baselines on the same draws: retreat - rise to the last "above" pose and repeat the last blocks blind; timed - the same retreat at a fixed time, without any detector. In MuJoCo a same-seed re-run is identical, so the paper's placebo is exactly zero and all spread comes from the drawn set-ups - worth stating.
- In Little World: a `recovery=` switch on the Fetch template (`look` | `retreat` | `timed` | `none`); `sweep --disturb --recovery retreat`; ADR 0036's exact McNemar test between `look` and `retreat` on the discordant pairs; a report line "rescued by looking beyond a retreat: k of n".
- How we would know: 9 set-ups × each disturbance kind (cube moved 5 cm, moved 2 s later, 6 N s shove, camera frozen) × the four arms. Predicted: for a moved cube retreat fails and looking wins on most pairs; for a shove that leaves the cube where it was, retreat may tie looking - a tie is a finding. Rates with Clopper-Pearson bounds, discordant pairs with exact p.
- Cost and needs: about a day; stdlib; about 4 × 36 disturbed runs.
- Note (weekly run, 2026-10-21): [RTPC](https://arxiv.org/abs/2610.24573) (`arxiv:2610.24573`) names "the lack of a trigger-matched memory-free baseline" as a limitation and found its corrections indistinguishable from random directions of the same family. FR-023's `timed` retreat is exactly a trigger-matched baseline; add a second control for ADR 0033's look: when the look re-aims, compare with re-aiming at a random point at the same distance from the old aim. If the random re-aim does as well on the disturbed set-ups, the look is not what rescues them.
- Note (weekly run, 2026-11-02): [Backtrack (2610.32941)](https://arxiv.org/abs/2610.32941) retraces recent motion and retries and reports gains only against the unassisted policy; ADR 0051's baselines on the same set-ups - retreat, random re-aim, stop - are the stricter test: keep them as the house rule.

### FR-024 · The knife-edge check: does a result survive a micrometre?
- Status: done (ADR 0043, 2026-10-21: Fetch's outcome survives a micrometre in all 59 set-ups, its set-down forces and fall only partly - as the reading of 19 Oct expected; the owner, 20 Oct: "use the weekly brain we have on decisions")
- From: the weekly reading of 2026-10-19 (FR-W03): [Same Action, Different Outcome: Variability in Dynamic Cloth Manipulation, arXiv 2610.10801](https://arxiv.org/abs/2610.10801) (`arxiv:2610.10801`: real repeats vary one to three orders of magnitude above the robot's repeatability; four calibrated simulators reproduced neither the size nor the ordering).
- Idea: In MuJoCo one drawn set-up has exactly one outcome, so a sweep cannot tell a robust success from a lucky one: some outcomes sit on a knife edge, a contact that does or does not open. Re-run each drawn set-up K = 5 times with perturbations far below anything a lab controls (start pose ±1 µm and ±1e-5 rad, cube placement ±1 µm) and count outcome flips and the spread of the continuous measures (time, fall, squeeze, table press, tip angle). A result that flips under a micrometre is chance, not a property of the design, and is reported so.
- In Little World: `inventory/sweep.py --jitter K` with the sizes as named constants and their rationale (far below the sourced ranges of ADR 0024); a column "flips under jitter" and, per measure, the ratio of jitter spread to draw spread.
- How we would know: (1) `--jitter 0` reproduces the plain sweep bit for bit; (2) on the 59-draw Fetch: flipping set-ups, k of 59 with an interval (target 0), each one listed and examined; (3) per measure, jitter spread over draw spread below 0.1 counts as robust - the small forces (the table's 0.17–0.23 N after ADR 0041, the bin's landing in ADR 0042) are the likely ones to fail and would be reported as chaos-limited; (4) the tilt table's 54.61 degrees under jitter - a spread above 0.05 degrees (assumed threshold) is worth an entry in ADR 0029.
- Cost and needs: about a day; stdlib; 5 × 59 = 295 Fetch runs plus the tilt table (time it first).

### FR-025 · Search for the failure, not only sample: a falsifier over the sourced ranges
- Status: done - measured, not adopted (ADR 0054, 2026-10-23: a compass search from the design as designed against the draws; Fetch, a margin against what the tuning draws certified: no failure in 40 runs, where 59 fresh draws left the envelope at draw 19 (a real corner, 5 of 5 under a micrometre); on the table's push alone the search left it at run 27, a knife edge (1 of 5); the tilt table: the search found 53.35 deg, the plan's own corner, friction at its high end; the known failure region (the rocking cart's presses) is gone with today's program, OPEN LW-035; the sweeps keep their plan; taken by the weekly reading's ranking)
- From: the weekly reading of 2026-10-19 (FR-W04): [Generalizable Robustness Testing of DNN-Based Robotic Navigation Systems via XAI-Guided Search, arXiv 2610.06862](https://arxiv.org/abs/2610.06862) (`arxiv:2610.06862`: guided search median success 70.0 % vs 53.85 % unguided; simulated failures transferred to the real robot with precision 0.95 and recall 0.67).
- Idea: 59 random draws certify a rate (ADR 0028, 0039) but do not say where the failures live. Add a deterministic search over the same variation box (start x, y, yaw; payload and its place; friction; cube position) that drives a continuous margin towards zero: for Fetch the jaws' capture margin, for the tilt table the tip angle minus the required one, for the cart the lightest-loaded wheel's normal force (FR-005). A stdlib optimiser (coordinate search or Nelder-Mead with restarts) started from the worst of the 59 draws; output the worst set-up found inside the sourced box with its margin, or "no failure found in N runs".
- In Little World: a new `inventory/falsify.py`; `sweep --search N`; margin functions per field beside their goals (`fields/`); every failure found frozen as a regression test.
- How we would know: (1) on a known failure region - the rocking cart before ADR 0041, 4 of 59 table presses, all with 0.44–0.50 kg on the deck - runs to the first failure for search against random sampling (random expects about 15); search must do better to be kept; (2) on today's design, the best margin found and its set-up; (3) the worst case found re-run under FR-024's jitter, to tell a real corner from a knife edge.
- Cost and needs: 1–2 days; stdlib; 100–200 runs per field.
- Note (weekly run, 2026-11-02): [Your Benchmark Is an Empirical Measure Over Difficulty (2610.29927)](https://huggingface.co/papers/2610.29927)'s coverage gaps are what ADR 0054's search looked for; a sweep report could say what share of its draws fell near the corners the search found.

### FR-026 · A grasp the program can feel: the servo's present current and position
- Status: done (ADR 0048, 2026-10-22: the kit jaws read as XH430-W350 registers; programs take a grasp as held when both jaws are still, short and pushing; 71 of 71 Fetch grasp checks felt as the contacts showed; taken by the weekly readings' rankings - the owner, 20 Oct: "continue and use the weekly brain we have on decisions")
- From: the weekly reading of 2026-10-19 (FR-W05): [MIM-VLA: Learning Physical Interaction Representations from Gripper Motor Feedback, arXiv 2610.08425](https://arxiv.org/abs/2610.08425) (`arxiv:2610.08425`: gripper motor current, position and velocity alone; 75.0 % vs 48.8 %; no tactile or force sensor); [How Firm Should a Grasp Be?, arXiv 2610.11221](https://arxiv.org/abs/2610.11221) (`arxiv:2610.11221`: the least force that holds without damage).
- Idea: Whether the cube is held is judged today from the simulator's contacts, which a real robot does not have. A Dynamixel X-series servo such as the XH430 reports present position and present current. Give the program a `feel` reading, and a block, computed only from what the gripper's servo would report: the jaw stopped short of its empty-close angle and current above the no-load band means holding. The program's own decisions (a missed grasp, ADR 0033; letting go over the bin) use `feel`; the simulator's contacts stay the judge. Later, X-series current-based position mode could set the squeeze (ADR 0040, 0042) as a current limit.
- In Little World: `MujocoBackend` exposes the gripper actuator's force; the servo profile converts torque to current with the datasheet's torque-current relation and the register's resolution (to be sourced from the ROBOTIS e-Manual, ADR 0007 style - not read yet); a `feel()` in `control/` and a `feel` block; the run report shows "felt held" beside "held (truth)".
- How we would know: a confusion matrix of felt against truth at each decision point over the 59 drawn Fetch runs and the disturbed 9-set-up sweeps - target no "felt held" with empty jaws, every disagreement listed; the gap between the current band closing on air and squeezing; the Fetch results with `feel` driving the decisions equal to today's (paired, ADR 0036).
- Cost and needs: about a day; stdlib; one datasheet to source; no hardware.
- Note (weekly run, 2026-10-21): [Multimodal Interaction Estimation](https://arxiv.org/abs/2610.24235) (`arxiv:2610.24235`) tells an unknown payload from a human push from force history (91.89 %, above 90 % with one modality occluded). The `feel` reading could tell the same two apart from the jaw servo's current: a heavier part raises the holding current and keeps it, a push gives a transient. That would also name the disturbance kinds of ADR 0030 from the robot's side. [Touch Where It Matters](https://arxiv.org/abs/2610.24485) hands the gripper to a local touch controller (no numbers); [Blind Precise Assembly](https://arxiv.org/abs/2610.23849) (title only).
- Note (weekly run, 2026-11-02): [FEEL (2610.38351)](https://arxiv.org/abs/2610.38351) turns proprioception into newtons (0.251 N RMSE over 0-20 N; the virtual spring alone about 14 times the error). ADR 0048 reads current counts; a squeeze in newtons is FR-037's job.

### FR-027 · Tune on one set of draws, judge on another
- Status: done (ADR 0049, 2026-10-22: sweeps record their seed, a ledger of seeds, `sweep --holdout` refuses seen draws; the Fetch program, ADR 0041, 0042 and 0048, certified on seed 20261022's 59 set-ups - 59 of 59, one table knock outside the tuned range reported; taken by the weekly reading's ranking)
- From: the weekly reading of 2026-10-21 (FR-W01): [RTPC failure analysis, arXiv 2610.24573](https://arxiv.org/abs/2610.24573) (`arxiv:2610.24573`: an effect seen in the first cohort did not reproduce in an independent replication); [HexaShell, arXiv 2610.23479](https://huggingface.co/papers/2610.23479) (`arxiv:2610.23479`: tools built on ten layouts, frozen, then tested on ten new ones).
- Idea: Recent decisions were shaped while looking at the very set-ups that then certify them: ADR 0042's 0.02 s squeeze was added after repeat 44 crept out of the jaws, and ADR 0041 was judged on the 59 draws where the four presses had been found. A design tuned on its own test set looks better than it is; the RTPC paper is this week's example of an effect that vanished on a fresh cohort. Make it a rule: every design ADR names its **tuning draws** (seed A) and is certified once on a **held-out draw set** (seed B) written into the ADR before the run. Anything changed after seeing the held-out result needs a new seed C. Start by re-certifying ADR 0041 and ADR 0042 on fresh draws.
- In Little World: `inventory/sweep.py` gets `--holdout`, which refuses a seed already in a ledger `docs/sweeps/seeds.jsonl` (seed, ADR, role tuning|holdout, date, commit); the run report prints tuning and held-out results side by side - rates with Clopper-Pearson bounds (ADR 0028), continuous measures with median and range. Assumed: draws are already seeded and the seed is in each sweep's `result.json`; otherwise recording it is the first step. A short ADR "tuning draws and held-out draws", and a line in each later ADR.
- How we would know: (1) a test: `--holdout` with a seed from the ledger fails; (2) ADR 0042 on 71 fresh draws: 71/71 in the bin, 0 creeps or presses (upper bound about 5 %, two-sided 95 %), fall and squeeze inside the tuning ranges (0.1-1.1 cm; median squeeze 3.89 N); (3) ADR 0041 on 59 fresh draws: 0 table presses (upper bound about 6 %), table push within 0.17-0.23 N; (4) any held-out number outside its tuning range is reported in the ADR as found, not re-tuned silently - that line is the point of the exercise.
- Cost and needs: half a day of code; 130 Fetch runs, about 80 minutes of CPU at the 20 Oct pace (~37 s a run); stdlib; resumable as the other sweeps.

### FR-028 · Time passes while the program looks
- Status: done (ADR 0053, 2026-10-23: latencies from their sources - a picture 139 ms (the D435's 33 ms frame interval at 30 fps and the finder's 106 ms, measured on the cloud's CPU), a command 7.6 ms and a reading 33 ms (Protocol 2.0 packets for six servos at 57,600 bps and 500 us return delays); latency 0 the runs as before; at the sourced latency every Fetch set-up held (27 of 27 disturbed, 71 of 71); pictures half a second late alone changed nothing (prediction 2 holds); the margin is the grasp check's 0.5 s, which the bus round trip must fit in: 0.2 s each way held, 0.25 s broke 11 of 27, 0.3 s all - six times the sourced bus; taken by the weekly reading's ranking)
- From: the weekly reading of 2026-10-21 (FR-W02): [LIBERO-Dynamic, arXiv 2610.24579](https://arxiv.org/abs/2610.24579) (`arxiv:2610.24579`: the world advances during each policy's calibrated inference latency; faster object motion degraded every policy).
- Idea: In a lab, a depth frame is delivered some time after exposure, the finder needs time to compute, and a servo command reaches the motor after a bus round trip; meanwhile the cart rolls on, the arm keeps moving and a shoved cube keeps sliding. Assumed: today `look` returns the scene at the instant of the call and commands act in the same step (if a delay already exists, this reduces to step 3). Add a latency model with **sourced** parts - the D435's frame interval at the configured frame rate (ADR 0032's datasheet), the classical finder's measured wall time on the owner's Mac, and the XH430 bus round trip from the ROBOTIS e-Manual (baud rate, return delay time; not read this run) - and deliver each picture and command that much simulated time later. Then sweep extra latency to find the **latency margin**: the largest delay at which results hold, in the manner of ADR 0039's mounting tolerance. Different from FR-018 (a camera that freezes or goes dark): this is the normal delay of a working camera.
- In Little World: `perception/` (the `look` result held back by `t_cam + t_find` while the simulation keeps stepping), the runner's command path (`t_bus`), `sweep --latency 0,33,66,133,266` (ms); report columns per latency; an ADR citing 0032, 0033, 0038, 0039.
- How we would know: (1) latency 0 reproduces today's sweep bit for bit; (2) prediction: the still-cube Fetch is nearly insensitive (59/59 up to at least 133 ms), because nothing moves while it looks; (3) the moving cases decide - "cube moved 2 s later" (LW-029) and a shove during a look: success against latency with Clopper-Pearson bounds, the margin being the largest latency with no loss beyond the interval; (4) the sourced default latency placed on that curve; a margin under 3x the sourced latency (assumed threshold) is reported as fragile.
- Cost and needs: 1-1.5 days; stdlib; 5 latencies x the 9 disturbed set-ups per kind, plus one 59-draw sweep at the sourced latency; two datasheet numbers to source.
- Note (weekly run, 2026-11-02): [Delay Randomization (2610.32277)](https://arxiv.org/abs/2610.32277) measured a delay margin (20-30 ms for an unrandomized tracker) in a CPU MuJoCo harness and argues delay ranges should come from measured latency, as ADR 0053's did.

### FR-029 · The factory cell judged by its process window: takt and tolerance
- Status: done (ADR 0056, 2026-10-26: each part's placement against the room its slot gives it and its cycle; small blocks 1.4 to 4.4 mm off, Cpk along the table 1.05, a 14 s takt held; tall blocks fail the run; the Panda's sag and 1.6 N squeeze the causes, two fixes previewed for the owner, OPEN LW-036, LW-037; shown under the factory's production run and in What's new; taken by the weekly reading's ranking)
- From: the weekly reading of 2026-10-21 (FR-W03): [LIBERO-Industry, arXiv 2610.16782](https://huggingface.co/papers/2610.16782) (`arxiv:2610.16782`: industrial constraints as controlled conditions - conveyor speed, interaction-window duration, size of the acceptance region; success degraded as they were combined).
- Idea: The production run (ADR 0019) counts finished parts. A factory judges a cell by two numbers: cycle time against **takt** (the time the line allows per part) and placement inside a **tolerance zone** at the receiving fixture. Give the cell both - a `takt_s` and an acceptance region (x, y, yaw) on the output fixture - and report per part the placement error and cycle time, and per run the share inside the window and the process capability index per axis, Cpk = min(USL - mean, mean - LSL) / 3 sigma, with a bootstrap interval because n is small. Tolerances come from a source (a fixture or pallet tolerance) or are stated as assumptions. No new physics; when FR-007's conveyor exists, conveyor speed becomes LIBERO-Industry's third factor (how long a part stays within reach).
- In Little World: the factory cell's production run and its report (ADR 0019; module names assumed); the fixture's tolerance as data beside the cell; a takt/tolerance sweep in `inventory/sweep.py`; an ADR.
- How we would know: (1) today's production run re-reported with placement error (mm, deg) and cycle time with their spread; (2) a falsifiable prediction: the cell grasps at known positions (LW-010), so placement sigma should be well under a millimetre; Cpk >= 1.33 (the usual "capable" threshold) on every axis or the ADR names the axis that fails; (3) tolerance swept +-5, +-2, +-1, +-0.5 mm: the tightest zone with >= 99 % of parts inside (Clopper-Pearson); (4) takt swept to the shortest takt the cell holds with no part late.
- Cost and needs: about a day; stdlib (`statistics`, `random`); a tolerance to source.
- Note (weekly run, 2026-11-02): [Payload generalization (2610.29356)](https://arxiv.org/abs/2610.29356) carries a Panda's feedforward to new payloads without its dynamic model - the cell's 4 mm tool sag (OPEN LW-036); [Self-Driving Laboratories Auditable (2610.36761)](https://arxiv.org/abs/2610.36761) judges whole episodes by outcome, timing, reproducibility, safety violations and fault recovery - a checklist for the cell's report beside Cpk and takt.

### FR-030 · A contact census: where one contact point carries a result
- Status: done (ADR 0050, 2026-10-22: every face-on-face pair a result rests on is box on box with its own collider - the same points with multiccd on; only the casters' wheels run on one point (4-5 with multiccd); no sweep rerun; at the bin the cart stands on three, OPEN LW-032; taken by the weekly reading's ranking)
- From: the weekly reading of 2026-10-21 (FR-W04): [HexaShell, arXiv 2610.23479](https://huggingface.co/papers/2610.23479) (`arxiv:2610.23479`: "contact, not reasoning, is the limit"; pushing 92.5 %, tight insertion 8.3 %); [ContactBench 1.0, arXiv 2610.24512](https://arxiv.org/abs/2610.24512) (`arxiv:2610.24512`); [MuJoCo changelog, Upcoming](https://mujoco.readthedocs.io/en/latest/changelog.html) (multicontact keeps spreading to more geom pairs).
- Idea: ADR 0027 turned multiccd off everywhere because extra wheel contacts added a rolling loss - measured on the wheels. Other ADR numbers also rest on contact: the jaw pads on the cube (squeeze, creep, the ~11 mm pull towards the palm of LW-028), the cube on the table and in the bin (presses, landing force), the casters on the floor. Pairs handled by MuJoCo's general convex collider (mesh-box, cylinder-box and similar) get one contact point when multiccd is off, so a flat face can be held by a single point and its resistance to turning comes from that point alone; box-box and plane pairs have their own multi-point colliders (assumed: which kit pairs fall where is not known here). A census lists, for every pair that carries an ADR number, its collider family and the number of contact points per step at the decisive moments (grasp held, set down, cart at rest). Only where a flat-on-flat pair runs on one point is the affected sweep repeated once with multiccd on.
- In Little World: `MujocoBackend.contact_census(pairs)` reading `data.contact[:ncon]` and the geom types; a column in `inventory/handling.py`'s summary; an addendum to ADR 0027 or a short ADR.
- How we would know: (1) the census table: pair x collider x contact points (min, median) at held / set down / rest; (2) if the jaw-cube pair already has several points, the grasp numbers stand and the ADR says so - a valid negative result; (3) if it has one: 59 paired Fetch draws, multiccd off against on (ADR 0036's exact McNemar on success; differences in squeeze, creep and the palm pull) - if LW-028's ~11 mm moves by more than its spread over the draws, part of LW-028 is the contact model, not the jaws; (4) the sprint time (11.9 s) in the same on/off pair, so ADR 0027's wheel cost is restated next to whatever the grasp gains.
- Cost and needs: about 2 hours for the census; one 59-draw sweep (~40 min) only if step 3 is needed; stdlib.

### FR-031 · Bring your own robot: a robot library from URDF and MJCF files
- Status: accepted (the owner, 21 Oct: "we can maybe take in some data type of modeling, for testing not existed robot or model, and they can program and build thier robot as well. Therefore, we probably need a new system for that"); done (ADR 0044, 2026-10-21: URDF and MJCF files imported into a robot library outside the repository, servos added where a file has none, a plain-language report; OPEN LW-030 and LW-031)
- From: the focused reading of 2026-10-21 on control, robot files and MCP (FR-W01): [PickNik's migration guide](https://docs.picknik.ai/how_to/configuration_tutorials/create_robot_sim_config/migrate_to_mujoco_config/); [MuJoCo's URDF extensions](https://mujoco.readthedocs.io/en/latest/modeling.html); MuJoCo 3.10.0 checked on this machine.
- Idea: Today Little World runs four Menagerie arms, registered by hand with a metadata file each (ADR 0004/0016). Let anyone bring a robot that does not exist yet as a URDF or MJCF file (with its meshes): the app copies it into the user's robot library (outside the repository), compiles it with MuJoCo, adds what a description file lacks - a position servo on every unactuated joint (`dampratio` 1, `kp` set so the joint answers in a stated time from its own inertia, its `effort` limit as the force limit), the root link kept as a body, `package://` paths resolved, adjacent links excluded from touching - writes the processed model and its metadata, and registers it like a Menagerie arm. One screen says in plain words what was found and what was added ("6 joints, 4.2 kg, no motors in the file: a servo added to each; 2 links have no collision shape"). The model then behaves as a kit module: placed, mounted on a cart, driven from the keyboard, programmed with blocks, tested on fields.
- In Little World: a new `assets/robot_library.py` (where the library is, list, add, remove) and an importer beside the MuJoCo adapter (`physics/importer.py`: compile, add servos, check, write `model.xml` and `metadata.json`); `robot_models.MODELS` extended with the library's robots under `user:` ids (a saved design names an id, never a path); an "Import robot…" action and the report screen in Build; an ADR.
- How we would know: (1) a URDF with no actuators imports, gets one servo per joint, and holds a commanded pose within 1 degree in 2 s under gravity; (2) effort limits come through (a 12 N m joint saturates at 12); (3) a Menagerie arm re-imported from its own MJCF reproduces the registered arm's joint trajectory for a taught pose within 0.5 degree (the importer adds nothing to a model that already has actuators); (4) a broken file (missing mesh, partial inertia, a misspelt attribute) gives a named, plain-language reason, not a traceback; (5) the imported arm mounted on the kit cart runs a block program on the Pick and place field.
- Cost and needs: 2–3 days; MuJoCo's own URDF and MJCF parsers (no new dependency); test models made in the tests; a library folder per platform.

### FR-032 · Move the tool, not the joints: tool-space control for any arm
- Status: done (ADR 0045, 2026-10-21: tool steps travel their straight line, held arrow and page keys drive the tool, any arm; taken by the focused reading's ranking - the owner, 20 Oct: "use the weekly brain we have on decisions"; 21 Oct: "controlling and learning cost as low as possible")
- From: the focused reading of 2026-10-21 on control, robot files and MCP (FR-W02): [UW–Madison telemanipulation](https://robotics.wisc.edu/natural-and-intuitive-telemanipulation-interfaces/) (mapping to the tool, RelaxedIK); [arXiv 1802.04349](https://arxiv.org/pdf/1802.04349) (task-level 27.5 s against joint-by-joint 56.7 s, five novices).
- Idea: A kit arm or a Menagerie arm is driven joint by joint from the keyboard (two keys a joint); the tool can only be moved by a program (ADR 0016, 0025). Give every arm, imported ones included, a tool mode: arrow keys and two more move the tool along the field's axes at a set speed, the mouse drags it, and the arm follows by the same solver the programs use; a key records the pose as a waypoint (teach and repeat), another sends it home. The tool point is found from the model (a site named like a tool, else the last link) and can be moved in the Inspector.
- In Little World: `control/tool_motion.py` (already solves a point for kit arms and registered models) driven each frame from key state; the keyboard controller gains a tool mode; Build's Inspector shows the tool point; the run report counts waypoints; an ADR.
- How we would know: (1) for each kit and registered arm, holding a key moves the tool along that axis within 5 mm of a straight line over 10 cm, where the arm can reach; (2) at a singularity or the reach limit it stops and says why; (3) a taught sequence replays to within the aimed pose's 5 mm (ADR 0025); (4) a timed task for the owner - put the cube in the tray - by joints and by tool mode; time each (one person, not a study).
- Cost and needs: 1–2 days; stdlib; no new dependency.

### FR-033 · Learn it inside the app: an interactive first hour
- Status: done (ADR 0046, 2026-10-22: five lessons the app checks, in the Guide; taken by the focused reading's ranking - the owner, 21 Oct: "controlling and learning cost as low as possible")
- From: the focused reading of 2026-10-21 on control, robot files and MCP (FR-W03): [CoBlox study, ABB](https://new.abb.com/news/detail/26823/training-end-users-to-program-industrial-robots) (79 novices: an interactive tutorial against a video, 9 min 59 s against 13 min 38 s to create a pick-and-place program, correctness 12.1 against 9.4 of 15).
- Idea: Little World teaches with guided assembly steps and documents. Turn the first hour into tasks the app checks itself, each a few minutes: drive the cart through the doorway; move the arm's tool onto the cube (FR-032); make a block program that picks it up; import a robot (FR-031) and make it wave; run a sweep and read its spread. Each task names its goal, watches the field's goals, and says what went wrong in the words of the run report. Progress is kept per user, outside the repository.
- In Little World: a `ui/tutorial.py` driving existing workspaces through their public actions; tasks as data (field, design, goal, hint); an ADR.
- How we would know: each task can be completed by a script through the same actions a user has (a test per task); the owner's own time per task; whether the run report's words were enough to recover from a deliberate mistake in each task.
- Cost and needs: 2 days; stdlib; depends on FR-031 and FR-032 for two of its tasks.

### FR-034 · Open robots in one click: the robot_descriptions catalogue
- Status: proposed (the owner decides: it needs the network at import time and an optional dependency)
- From: the focused reading of 2026-10-21 on control, robot files and MCP (FR-W04): [robot_descriptions](https://pypi.org/project/robot_descriptions) (Apache-2.0, about 211 descriptions, v3.3.0 of 12 Oct 2026).
- Idea: Once FR-031 imports a file, offer a browsable list of open robots - arms, grippers, mobile bases, legged robots - fetched on demand, each with its licence shown before it is added to the library. Little World would test, program and compare robots no one in the lab owns yet.
- In Little World: an optional dependency for the catalogue only; the importer of FR-031 does the rest; the licence and source recorded in the library entry (THIRD_PARTY.md for anything committed).
- How we would know: five descriptions of different kinds import with no hand edits, or each gives its named reason; licences shown and recorded.
- Cost and needs: 1 day; network access at import time (the package clones repositories); an optional dependency - the owner decides.

### FR-035 · Little World as an MCP server (later)
- Status: proposed (the owner, 21 Oct: "we can delay the mcp thing")
- From: the focused reading of 2026-10-21 on control, robot files and MCP (FR-W05): [ROS MCP server](https://glama.ai/mcp/servers/@robotmcp/ros-mcp-server/blob/199d21908a936d17fc8f02a318cf7758ab619376/docs/architecture.md) (topics, services, actions as tools through rosbridge; no safety limits described).
- Idea: Let an assistant use Little World the way a person does, in simulation only: list designs and fields, build from the kit or the library, run a field or a sweep, read the run report, write a block program and grade it on a field (this is FR-008's harness). Read-only tools first; anything that writes - a saved design, a program - versioned and undoable; nothing reaches real hardware.
- In Little World: a small server beside the app (stdlib JSON-RPC over stdio, as MCP uses) calling the same functions as the command-line sweeps; an ADR.
- How we would know: an assistant connected to it runs the Fetch field and quotes the run report correctly; every tool has a test; no tool can change a saved design without leaving the old version.
- Cost and needs: 2 days; the MCP protocol by its specification (not read this time); the owner said to delay it.
- Note (weekly run, 2026-11-02): (the owner: later) [Matched Capabilities, Different Behaviors: MCP and CLI Interfaces (2610.34298)](https://huggingface.co/papers/2610.34298), title only - read it before designing the server.

### FR-036 · How close to slipping: friction use on the contacts a result rests on
- Status: done (ADR 0061, 2026-11-02: friction use on every contact, a grip's while it carries, in the drive panel and What's new; the Fetch carries its cube using 38 % of its grip's friction; made heavier it held to 8 times and slid out at 16, so the first-order margin - the inverse of the use - does not say how heavy a part a position-servo gripper can carry: its squeeze grows with the load; the wheels' traction margin not yet; taken first by the weekly reading's ranking, as the owner asked on 2 Nov)
- From: the weekly reading of 2026-11-02 (FR-W01): [Keeping Contact, arXiv 2610.36961](https://arxiv.org/abs/2610.36961) (`arxiv:2610.36961`, accepted for RA-L: the margin is a signed distance from the friction-cone edge; fixed and no-margin baselines did worse); [FEEL, arXiv 2610.38351](https://arxiv.org/abs/2610.38351) (`arxiv:2610.38351`: adapting to the estimated finger force raised damage-free picks from 7/10 to 10/10).
- Idea: results report forces (ADR 0040), the squeeze (ADR 0042) and what the jaws feel (ADR 0048), not how near a contact is to sliding. For a contact with normal force f_n, tangential force f_t and its friction coefficient mu (ADR 0010), the friction use u = |f_t| / (mu f_n) is 0 with no sideways load and 1 at the edge of the cone; its inverse is a margin anyone can read - "the grasp holds with 2.4 times margin": to first order at the same squeeze, a cube about 2.4 times heavier would start to slip. The same number for the drive wheels on the ramps and the Push field is a traction margin. Report the least over each phase with the mu used. MuJoCo's soft contacts let a little creep happen inside the cone (noslip is on, ADR 0017): read u beside the measured creep, not instead of it.
- In Little World: `MujocoBackend.friction_use` beside `contact_forces` (ADR 0040), from `mj_contactForce` and each contact's friction; the handling watch's least grip and traction margins per phase; a run-report line ("grip margin 2.4x"); the Program panel's senses add the jaws' friction use while a program runs (ADR 0055); a What's new demonstration where the cube gets heavier until it slips, the margin counting down to 1.
- How we would know: (1) a box on a plane tilted to theta reads u = tan(theta) / mu within 2 % while it holds, and slides once tan(theta) > mu; (2) the Fetch's least grip margin m over lift and carry on 9 set-ups (seed 1), then cubes of 0.7, 0.9, 1.1 and 1.3 m times the nominal mass on the same set-ups: no slip (under 2 mm in the jaws) predicted below 1 m, slip above, confirmed if at least 8 of 9 agree at each mass; (3) the drive wheels' u on the steepest ramp climbed against where the machine stalls or slides back; (4) the measure changes nothing it watches: sweeps reproduce bit for bit.
- Cost and needs: about a day; stdlib and calls already in the adapter; 36 Fetch runs. Works on 3.10.0.

### FR-037 · The jaws squeeze by current, as the XH430 does in its current-based position mode
- Status: doing (ADR 0066, 2026-11-03, in part: the jaws squeeze by current, a setting in newtons on an action block, the registers at Goal Current; the Fetch's own program is not changed - the side-by-side on the 71 tuning set-ups and the 59 held-out draws are not made, OPEN LW-041; taken fifth by the weekly reading's ranking, as the owner asked on 2 Nov)
- From: the weekly reading of 2026-11-02 (FR-W02): [ROBOTIS e-Manual, XH430-W350](https://emanual.robotis.com/docs/en/dxl/x/xh430-w350/) (`web:emanual.robotis.com/docs/en/dxl/x/xh430-w350`: Operating Mode 5, current-based position control; Goal Current at address 102 within the Current Limit, 2.69 mA a count; stall 3.4 N m at 1.3 A); [FEEL, arXiv 2610.38351](https://arxiv.org/abs/2610.38351) (finger force from proprioception, 0.251 N RMSE over 0-20 N).
- Idea: the kit jaws are position servos and their squeeze is a by-product: ADR 0042 found the hold is set by when the closing ramp ends. The real XH430's Operating Mode 5 runs the position loop with the current - the torque - capped by Goal Current, so a squeeze becomes a setting in newtons. Model it: keep the jaw position loop and clamp its force at k_t I_goal through the jaw lever, k_t from the e-Manual's stall point (3.4 N m / 1.3 A, about 2.6 N m/A; a stall approximation until a bench measurement, FR-010). The grasp block gets a squeeze in newtons, by default the least that keeps FR-036's grip margin at 2; the feel registers (ADR 0048) then read Present Current near Goal Current while holding, as the real servo would.
- In Little World: `control/feel.py` (Operating Mode and Goal Current registers); the jaw actuator's force range set during a run from Goal Current (check first that changing it on a compiled 3.10.0 model is safe); the Fetch's squeeze step replaced by a current setting; a squeeze in newtons in the Joint lab and the grasp block; measured side by side and adopted only after held-out draws (ADR 0049).
- How we would know: (1) jaws closed on a fixed box at 1, 2, 4 and 6 N read pad forces within 10 %; (2) the Fetch on the 71 tuning set-ups (seed 1) against ADR 0042: still 71 of 71, the squeeze within 0.3 N of its setting (ADR 0042: median 3.89 N, set by timing), creep and the bin's push no worse, LW-028's pull towards the palm reported again; (3) 59 fresh draws before adoption; (4) under ADR 0043's micrometre jitter the squeeze's spread falls, a cap not depending on when the ramp ends.
- Cost and needs: 1-1.5 days; stdlib; about 140 Fetch runs. Changes how the kit grasps: measured first, adopted on held-out draws.

### FR-038 · Where runs fail: a stage profile in every sweep report
- Status: done (ADR 0063, 2026-11-03: the goals as stages, the block a program gave up at; a table in every sweep report and two lines in the panels; three disturbances costing all 9 of the Fetch's set-ups, recovery off, fail in two places - the moved cube at the reach, the camera faults at the look; taken second by the weekly reading's ranking, as the owner asked on 2 Nov)
- From: the weekly reading of 2026-11-02 (FR-W03): [RoboCasa-Shift, arXiv 2610.27861](https://arxiv.org/abs/2610.27861) (`arxiv:2610.27861`: two conditions with the same rate drop, 0.188, failed at the first stage 19.0 % and 36.4 % of the time; a rate unchanged while 8 of 80 pairs flipped); [From 12 to 200 Demonstrations, arXiv 2610.37170](https://arxiv.org/abs/2610.37170) (`arxiv:2610.37170`: four stages showed failures moving from reaching to grasping to none as data grew).
- Idea: a sweep reports a rate with its interval (ADR 0028) and, paired, McNemar (ADR 0036). Two disturbances can cost the same rate and fail in different places, and a rate can stay put while pairs flip both ways. Add a stage profile: the program's blocks grouped into stages (for the Fetch: drive to the table, look, reach, grasp checked, lift and carry, set down) and per stage how many runs reached it and how many ended there; for paired sweeps the flips each way and the stage where the two runs first parted. Report flips even when the rate does not move.
- In Little World: the runner's block index kept per run (ADR 0052 records it with each alarm); a `stages` field in `inventory/sweep.py`; `inventory/stages.py` (profile, flips by stage, markdown); the run report draws a funnel; a What's new entry.
- How we would know: (1) the undisturbed Fetch, 71 set-ups: every run reaches the last stage; (2) on ADR 0051's disturbed set-ups the profile puts "cube moved 2 s later" failures at the reach and grasp and the frozen camera at the look, as ADR 0051 and 0052 wrote by hand; (3) the flip counts equal ADR 0036's and 0051's McNemar tables; (4) two disturbances with tied rates and different profiles searched for and reported either way.
- Cost and needs: half a day to a day; stdlib; about 45 Fetch runs if stored runs lack block indices.

### FR-039 · Plan the draws before the run: the smallest effect worth seeing, and enough draws to see it
- Status: done (ADR 0064, 2026-11-03: the exact power of the paired McNemar test and of a bound on a rate; what a sweep can show, under its button in the window; the records' comparisons read again - ADR 0041's presses and 0042's gentle set-downs underpowered, 0036's and 0051's shown; the plan not yet written into the seed ledger by the command line; taken third by the weekly reading's ranking, as the owner asked on 2 Nov)
- From: the weekly reading of 2026-11-02 (FR-W04): [Externalise the Memory, arXiv 2610.30478](https://arxiv.org/abs/2610.30478) (`arxiv:2610.30478`: a pre-registered test underpowered for its own minimum effect; the claim withdrawn, not refuted); [PhysLadder, arXiv 2610.34527](https://arxiv.org/abs/2610.34527) (three trials per task; six tasks differed by one success); the project's own ADR 0041.
- Idea: before a comparison sweep, write into the seed ledger (`docs/sweeps/seeds.jsonl`, ADR 0049) the prediction, the smallest effect worth seeing, the test (exact McNemar for paired outcomes, Clopper-Pearson for a bound) and the draws that give 80 % power; after the run, report "underpowered - inconclusive" where the draws could not have shown that effect, never "no difference". Exact two-sided McNemar with every discordant pair one way needs at least 6 pairs for p < 0.05 (4 give 0.125, 5 give 0.0625, 6 give 0.031). ADR 0041's presses went 4 to 0 with p = 0.125, the floor for 4 pairs: at a 4/59 press rate, 59 paired draws had about a 21 % chance to show it at 0.05, 120 about 83 %, 150 about 95 %. With no failures, 0/59 bounds a rate at 4.95 % (one-sided 95 %); under 2 % needs 149 draws, under 1 % 299.
- In Little World: `inventory/power.py` (stdlib: exact binomial and McNemar power by enumeration; draws for a target bound); `sweep --plan` writes the plan line into the ledger and warns when a comparison has under 50 % power unless marked a pilot; a report sentence ("this comparison could show a change from 6.8 % to 0 with 83 % chance"); the sweep dialog shows the draws needed before Run.
- How we would know: (1) hand values: 4 discordant pairs give p 0.125; power at 59 draws and a 0.068 rate 0.209 +- 0.005; 0/149 bounds under 2 %; (2) an audit of the comparisons in ADR 0036, 0041, 0042, 0049, 0051 and 0053, listing which were underpowered for what they reported - expected ADR 0041's presses, not ADR 0051's (9 pairs, p = 0.0039); (3) optional: ADR 0041's comparison re-run with about 120 planned paired draws on a fresh seed.
- Cost and needs: half a day; stdlib; the optional re-run about 240 runs.

## Radar brief

<!-- radar:begin -->

*Written by `python -m little_world.radar brief` on 2026-10-02; edits inside these markers are replaced at the next run.*

Since 2026-09-18: 302 items read, 51 filed under a decision or a step, 23 judged; MuJoCo pinned at 3.10.0.

**ADR 0007** · Sourced motor profiles and build reports
- **adopt** [MuJoCo 3.7.0: Added the dcmotor actuator for modeling DC motors.](https://mujoco.readthedocs.io/en/latest/changelog.html) · the Pololu 37D profile of ADR 0007 maps onto dcmotor's resistance, back-EMF and friction; after the upgrade · FR-004
- **learn** [Extended Friction Models for the Physics Simulation of Servo Actuators](https://arxiv.org/abs/2410.08650) · servo friction beyond Coulomb-viscous, identified on a pendulum bench: a cheap real experiment for the kit servo · FR-010
- [MuJoCo 3.12.0: The dcmotor on-board controller is redesigned: the input attribute selects any subset of \[pos, vel, ff, voltage\], where pos and vel are...](https://mujoco.readthedocs.io/en/latest/changelog.html) · matched torque, emf, selects

**Next: closer to the real machine** · Closer to the real machine
- **adopt** [MuJoCo 3.5.0: Added a new **System Identification** toolbox (Python), see README for details.](https://mujoco.readthedocs.io/en/latest/changelog.html) · the calibration path to real hardware: record a real servo or cart, fit friction, damping and gains · FR-010
- **learn** [MolmoBot: open manipulation policies trained only in MuJoCo simulation](https://allenai.org/blog/molmobot-robot-manipulation) · trained only in MuJoCo and transfers zero-shot: its procedural randomization is the reference for approaching reality · FR-009
- [Sim-to-Real Aware End-to-End Learning Environment for Micromobility](https://arxiv.org/abs/2609.28969) · matched real, sim, transfer
- and 2 more (`python -m little_world.radar digest --html page.html`)

**ADR 0024** · Runs under variation: a result with its spread
- **adopt** [LIBERO-plus: robustness of robot policies under systematic perturbations](https://arxiv.org/abs/2510.13626) · perturbation sweeps for the test fields: friction, payload and start pose varied, the spread of results reported · FR-001

**Next: conveyor and feeder** · Conveyor and feeder
- **adopt** [MuJoCo 3.11.0: Added geom/surfacevel: the velocity of a geom's surface as seen by contacts, given as a velocity field with a constant component and a...](https://mujoco.readthedocs.io/en/latest/changelog.html) · the factory feeder becomes a conveyor: a static geom with a surface velocity, no joints; after the MuJoCo upgrade · FR-007, FR-014
- **learn** [Drake 1.57: virtual conveyor belts and an error-controlled contact integrator](https://drake.mit.edu/release_notes/v1.57.0.html) · a second opinion on conveyors and on contact integration accuracy · FR-007, FR-013

**ADR 0014** · Servo damping the solver integrates
- **adopt** [MuJoCo 3.12.0: Added the pid actuator: a PID controller with real position and velocity setpoint inputs, optional integral action (ki, integrating the...](https://mujoco.readthedocs.io/en/latest/changelog.html) · the engine's own PID servo, correct under every integrator, could replace the Torque slope of ADR 0014; the servo damping tests decide · FR-014
- **watch** [MuJoCo 3.13.0: Added a new integrator discrete: the constraint solve and the implicit velocity update merge into one operation, performed in the...](https://mujoco.readthedocs.io/en/latest/changelog.html) · experimental; could make ADR 0014's Torque slope unnecessary, but noslip is only approximated under it
- [MuJoCo 3.12.0: The mode-flag semantics of dcmotor/input ("voltage", "position", "velocity", selecting the interpretation of a single control) are...](https://mujoco.readthedocs.io/en/latest/changelog.html) · matched position, controller, damping
- and 4 more (`python -m little_world.radar digest --html page.html`)

**ADR 0027** · MuJoCo 3.10.0 on every machine, with one contact per convex pair
- **adopt** [MuJoCo 3.8.0: The multiccd option (multiple contacts returned from the convex collision detection pipeline) is now enabled by default.](https://mujoco.readthedocs.io/en/latest/changelog.html) · breaking for us: with multiccd on, the platform's caster climbs the 20 mm curb (disabling it restores the stop) and the tilt table tips the manipulator at 52.4 deg instead of 54.2 (53.0 with it off) · FR-002

**Learn: language models that program robots** · Language models that program robots
- **learn** [Project Fetch, phase two: a language model programs a quadruped robot](https://www.anthropic.com/research/project-fetch-phase-two) · agents write working robot code fast and fail at fine closed-loop control: Little World's blocks are the layer to give an agent · FR-008
- **learn** [CaP-X: A Framework for Benchmarking and Improving Coding Agents for Robot Manipulation](https://arxiv.org/abs/2603.22435) · coding agents do well only with good helper functions: study its benchmark before building one on the block-program API · FR-008
- [Agent-Editing World Model: Rethinking World Modeling for LLM Agents](https://huggingface.co/papers/2609.28416) · matched language, agent, llm

**Learn: robot learning** · Robot learning
- **learn** [LeRobot 0.6: datasets, imitation learning and VLA policies with one evaluation command](https://huggingface.co/blog/lerobot-release-v060) · the common dataset format: exporting Little World runs as LeRobot datasets is the bridge to robot learning · FR-012
- **learn** [lerobot/smolvla_base](https://huggingface.co/lerobot/smolvla_base) · the smallest open VLA; runs on one consumer GPU · FR-012
- [lerobot/pi05_base](https://huggingface.co/lerobot/pi05_base) · matched learning robotics, language action, imitation learning
- and 11 more (`python -m little_world.radar digest --html page.html`)

**ADR 0013** · Test fields: scenarios with goals the simulator checks
- **learn** [RoboCasa365: a large simulation benchmark of everyday tasks](https://arxiv.org/abs/2603.04356) · benchmark design on the same engine, including mobile manipulation · FR-003
- [RoboRecover: Benchmarking Robot Policy Recovery under Execution Deviations](https://arxiv.org/abs/2609.28952) · matched benchmarking robot, scenarios, policy · FR-006

**Learn: physics simulation** · Physics simulation
- **watch** [Newton: an open GPU physics engine with MuJoCo Warp among its solvers](https://github.com/newton-physics/newton) · GPU only; Little World runs on a Mac CPU
- **watch** [google-deepmind/mujoco](https://github.com/google-deepmind/mujoco) · the engine itself: its changelog is read entry by entry

**Next: grasping from a camera** · Grasping from a camera
- **watch** [nvidia/foundationpose](https://huggingface.co/nvidia/foundationpose) · object pose from a camera: for when the factory grasps from its camera · FR-011

**Next: paths through clutter** · Paths through clutter
- [CAMP: Cooperative Arm-Hand Motion Planning in Constrained Spaces](https://arxiv.org/abs/2609.29021) · matched planning, motion, planners
- [Coding Agents for Generalized Task and Motion Planning Problems](https://huggingface.co/papers/2609.30233) · matched planning, motion · FR-008

**ADR 0022** · Wheel contacts across MuJoCo releases: stance from shapes, curbs off the limit, the tilt gap named
- [MuJoCo 3.5.0: MuJoCo Warp is now officially released.](https://mujoco.readthedocs.io/en/latest/changelog.html) · matched released, mujoco

**ADR 0010** · Sourced contact-pair friction
- [MuJoCo 3.11.0: Added geom/adhesion and pair/adhesion: an adhesive force associated with a contact, useful for modeling sticky materials.](https://mujoco.readthedocs.io/en/latest/changelog.html) · matched pair, contact, geom

**ADR 0017** · Friction that holds: no creep below the limit, no self-contact in robot models
- [MuJoCo 3.13.0: The Newton solver with elliptic cones now rebuilds the cone-augmented Hessian factor with a single refactorization instead of per-contact...](https://mujoco.readthedocs.io/en/latest/changelog.html) · matched cones, contact, sliding

<!-- radar:end -->
