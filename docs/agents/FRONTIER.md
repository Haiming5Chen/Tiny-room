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

### FR-005 · Tip-over margin while moving: the force-angle measure
- Status: proposed
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

### FR-007 · A powered roller conveyor for the factory's feeder
- Status: proposed
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

### FR-015 · Looking again when a grasp misses
- Status: proposed
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

### FR-016 · Planning the stop from where the camera sees the cube
- Status: proposed
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
