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

## 2026-11-11 · Claude (Cowork) · easy to get from GitHub and use, and the project re-evaluated
Did: the owner's request of 10 Nov. ADR 0072 - a `little-world` command (the window with What's new,
`demo`, `build`, `doctor`), designs kept in the user's own folder, the README cut from 1,158 lines to
114 with its lists moved to docs/FEATURES.md and docs/MANUAL.md, docs/TROUBLESHOOTING.md. ADR 0073 -
`little-world evidence` (twelve headline claims measured again against their records), a quick test
tier (`pytest -m "not slow"`), two GitHub workflows, a link check, and docs/EVALUATION.md. What's new
in pages (ADR 0055 amended). On the Mac: `build/publish.sh`, which publishes in one step.
Measured: GitHub has the import of 24 Sep and nothing since - 89 commits never pushed (OPEN LW-044).
A clean clone installs in 26 s and opens its window. Evidence: 31 of 31 measurements hold where they
were recorded, in 3.5 min. Quick tier: 1,048 tests in 76 s; the whole headless suite is 37 min of
test time, 64 tests taking 35.9. On MuJoCo 4.0.0, on Linux, 20 of 1,087 tests fail; 4.0.0 does not
lift the pin - its engine wheel, `mujoco-core`, has none for Intel Macs (OPEN LW-046). With NumPy's
AVX-512 paths switched off on the same machine, 29 of the 31 measurements are the same to the last
digit and the Fetch delivers 4 ms earlier; every test passes there (OPEN LW-045). The bundle, cloned
afresh: the quick tier passes on Python 3.11 and 3.13. Suites: 1179 passed with a display, 1112
headless.
Corrected before publishing: the first draft of this work said 4.0.0 has an Intel Mac wheel again and
that the pin's reason was gone. It took a wrapper wheel for the engine's; the weekly reading of 9 Nov
had checked it and I had not read it first.
Unfinished: nothing is published - that needs the owner. The workflows have never run; Apple silicon
and Windows are untried (OPEN LW-045). The weekly reading of 9 Nov is in the frontier as FR-040 to
FR-044 (41 sources in the collection); none is started.
For the owner: (1) publish: `sh ~/Tiny-room/build/publish.sh`; (2) choose a licence - all rights are
reserved now, so people may read this and may not use it; (3) docs/EVALUATION.md lists where the
project went wrong, the first being that I reported "shipped" for seven weeks without checking that
anything had reached GitHub.

## 2026-11-06 · Claude (Cowork) · measured, not decided: a cube on its side, elliptic cones
Did: no code. OPEN LW-034 and LW-039 measured (docs only).
Measured: a cube lying with its 40 mm length across the Fetch's jaws (0 and 20 deg) is grasped by
its ends and lost on the drive to the bin; at 45 deg and more the jaws turn it along the fingers and
it is delivered. Gripping lower or squeezing by current does not keep it, and a stop beside its line
turns the jaws by at most 34 deg. With elliptic cones in every scene 16 of the 1087 headless tests
fail: a held cube slides 7.6 mm out of the grip in 10 s, the cell's hand no longer squares a part
fed turned 10 deg, the Fetch delivers 2 to 3 s later, a squeeze in newtons reads 7 % high.
Unfinished: LW-034 needs a wrist that turns, or a way to stand the cube up first.
For the owner: I would not switch to elliptic cones for the slope creep alone - they stop it, but
the grip and the cell get worse; say if you want them anyway.

## 2026-11-06 · Claude (Cowork) · OPEN LW-029: a reach that feels what it meets
Did: ADR 0071 - the runner reads the arm's joints as their servos report them, Present Position
against the goal it sends: late in a reach for the object (from three quarters of its travel), a
joint that falls 0.5 deg further behind its goal than it has been since has met something, and the
program rises and looks again at once. What's new: 'It feels the cube under its jaw'. LW-029 done.
Measured: the cube moved 5 cm 2 s after the look, 9 set-ups paired: the arm rose 0.21 s after a jaw
met the cube (2.44 s before), pressing it 2.35 N over 50 ms for 0.22 s (3.11 N for 2.45 s); every goal
met either way, the cube in the bin 2.4 s sooner; no reach felt in the other 63 disturbed runs, the 71
tuning set-ups or the 59 fresh draws (seed 20261106). Suites: 1159 passed with a display, 1093 headless.
Unfinished: a reach faster than a quarter of its travel's time behind its servo could be felt for
nothing - the Fetch's reach is 1.3 s against 60 ms; a jaw that meets the object only after the
reach's travel is not felt (the grasp check finds it).
For the owner: nothing to decide here.

## 2026-11-05 · Claude (Cowork) · OPEN LW-041: the Fetch keeps its ramp
Did: ADR 0070 - the Fetch as it is against closed fully at 7 N by current, paired on its 71 tuning
set-ups and 59 held-out draws (seed 20261103, now in the ledger); no code changed. FR-037 done; LW-041
done.
Measured: every goal met either way on all 130 pairs, none broken or mended (exact McNemar p = 1.0);
set to 7 N the squeeze reached the cube as 5.2 to 12.2 N - its spread six times the ramp's - and the
cube was in the bin 0.7 s later; the grip's friction in use at most fell from 95 to 82 %.
For the owner: not adopted - a squeeze set as a torque reaches the cube as more force the deeper the
jaws pull it in, so it varies more than the ramp's; the block stays for programs that want it.

## 2026-11-04 · Claude (Cowork) · OPEN LW-010: the cell finds its parts with its camera
Did: ADR 0069 (`camera_eye`, `FactoryCycle(eye=)` with `locate`, `view_clear` and the arm clearing
the camera's view; "Locate: camera" and the depth picture in Real's panel; What's new's "The cell
finds its parts"). LW-010 done; FR-011 done for the cell too.
Measured: 216 of 216 parts found by the camera and placed, each seen within 1.5 mm in plan and 4.1
deg, left within 1.6 mm of its slot (1.1 known); a run's first part 2.4 s slower while the arm clears.
On the way: from its home pose the Panda hangs its wrist 5 cm under the cell's camera, which sees
nothing else - so the arm clears the view first.
Unfinished: the camera's pose is exact and its turn reading is not used; latency is not modelled.

## 2026-11-04 · Claude (Cowork) · FR-007: the cell fed by a conveyor
Did: ADR 0068 (friction rollers in `fields/conveyor.py`, a `Line` laid out anywhere; the cell's
conveyor feeder in `factory/scene.py` and `factory/controller.py`; "Conveyor: on" in Real's panel;
What's new's "The cell fed by a conveyor"). FR-007 done; OPEN LW-005 and LW-042 done.
Measured: small blocks 60 of 60 placed over ten runs fed by the conveyor, each arriving within 3.9
mm of its place at the stop and left within 1.0 mm of its slot, 12.1 to 13.9 s a part; tall blocks
24 of 24. Under a held pallet the friction rollers stand still and what it carries stays put.
On the way: a loose part slides 3.4 mm on its pallet at each stop (v^2/2ug, wood on HDPE), so the
pallets locate their parts between two bars; the hand caught the conveyor's side frame lowering into
the near row of a tray, so the frames stand lower.
Unfinished: the pallets' return and loading are a person's move, not simulated; the feeder is not
saved with a cell.

## 2026-11-03 · Claude (Cowork) · FR-007, in part: a roller conveyor
Did: ADR 0067 (`fields/conveyor.py` and the "Roller conveyor" field; the capsule shape in the core and
the backend; What's new's "A roller conveyor").
Measured: two 160 mm pallets carried at 0.0999 m/s on rollers held at 0.1 m/s, at rest at the stop and
queued to 0.1 mm. On the way: a box across cylinders sinks into them in MuJoCo 3.10 with multiccd off
(4 mm into 50 mm ones), across capsules it does not; rollers too light let a light pallet hop 13 mm.
Found after: a pallet held at the stop or in the queue shakes on the rollers slipping under it, and
the cube on it creeps forward - 6 mm on the first, 31 mm on the second, from 2 to 10 s (OPEN LW-042).
Unfinished: the cell's feeder (OPEN LW-005): the conveyor is a field, not yet the cell's. Closed OPEN LW-040,
filed with ADR 0065: an imported gripper's jaws already take priority (ADR 0047), so they are not averaged.
FR-037's frontier status reads "doing": c8285c2 wrote "in part", which the docs check does not know.
For the owner: the parts ride on pallets because rollers cannot carry parts this short bare - the call
FR-007's note left open, made by the weekly reading's ranking as you asked on 2 November.

## 2026-11-03 · Claude (Cowork) · FR-037, in part: the jaws squeeze by current
Did: ADR 0066 (`KeyboardPositionControl.limits`, `MujocoKeyboardControl.squeeze` and `pad_lever`; an
action block's squeeze in newtons, in the Program editor; `tool_motion.squeezed`; What's new's "A squeeze
set in newtons").
Measured: on a fixed box at the pads' centres, set 1 to 6 N, pushed within 2.5 %; the Fetch as designed
at 7 N, closed fully: every goal met 0.7 s later, the grip at most 60 % in use (80 % with the ramp's
squeeze).
Unfinished: OPEN LW-041 (the Fetch squeezing by current, side by side on the tuning set-ups and held-out
draws, before its program changes).
For the owner: nothing to decide here.

## 2026-11-03 · Claude (Cowork) · OPEN LW-036: the Panda holds itself up; What's new for ADR 0063, 0064
Did: ADR 0065 (`robot_models.CONTROLLERS`; the backend's `held` and the hand's speed: the Panda's links
held against gravity on a fixed base, its hand squeezing 70 N a finger at 50 mm/s, its fingers' contacts
their own stiffness). What's new's "The Panda holds itself up" (tall blocks in the cell) and "Where
repeats fail" (the Fetch run once and stopped on its report, the lines ADR 0063 and 0064 added under its
Repeat buttons).
Measured: the cell's tool within 0.47 mm of every point (5.7 to 6.7 mm before); 228 parts in 38
production runs within 1.05 mm of their slots (2.2 to 6.3 mm), Cpk along x 10 to 20 (0.85 to 1.27).
Found on the way: MuJoCo averages a contact's stiffness over its geoms - the 70 N squeeze alone still
let the part slide 2 mm along the fingers - and the stiffer hand shut its fingers at 2.9 m/s.
Unfinished: OPEN LW-040 (an imported gripper's contacts averaged the same way).
For the owner: nothing to decide here.

## 2026-11-03 · Claude (Cowork) · FR-039: plan the draws
Did: ADR 0064 (`inventory/power.py`; what a sweep can show, under its button in the window).
Measured: FR-039's numbers reproduced exactly; read again, ADR 0041's presses (21 % power, 116 draws
needed) and ADR 0042's gentle set-downs (8 %, 186) were underpowered; ADR 0036's and 0051's were shown.
Unfinished: the plan line in the seed ledger (`sweep --plan`).
For the owner: nothing to decide here.

## 2026-11-03 · Claude (Cowork) · FR-038: where runs fail
Did: ADR 0063 (`inventory/stages.py`, `Run.stopped`, `Group.where`; a table in every sweep report; two
lines under each line that missed in the variations and disturbances panels).
Measured: on the Fetch with its recovery off, three disturbances cost every set-up and fail in two
places: the moved cube's runs gave up at the reach, the camera faults' at the look.
Unfinished: nothing new.
For the owner: nothing to decide here.

## 2026-11-02 · Claude (Cowork) · OPEN LW-027: the collection's search mixes words and meaning
Did: ADR 0062 (the command line's `search` and `related` mix words and meaning equally by default);
the reading of 2 November's 55 sources into the collection (238 entries).
Measured: at 238 entries words alone answer 14 of the 20 questions with known answers (MRR 0.60),
BM25 14 to 15, the mix 16 (0.69).
Unfinished: nothing new.
For the owner: nothing to decide here.

## 2026-11-02 · Claude (Cowork) · FR-036: how close to slipping
Did: ADR 0061 (`MujocoBackend.friction_use`, `scale_mass`; `handling.grip_use`; `Runner.carrying`,
`Run.grip`, `run(masses=...)`; the drive panel's grip line; What's new's "How close to slipping"), and
the weekly reading of 2 November into the frontier (FR-036 to FR-039) and the collection.
Measured: the Fetch carries its cube using 38 % of its grip's friction; heavier, it held to 8 times and
slid out at 16 - the squeeze grows with the load, so the use is not a mass margin. A block on a slope
creeps inside its cone (OPEN LW-039).
Unfinished: the wheels' traction margin (FR-036's third check); LW-039.
For the owner: nothing to decide here.

## 2026-10-27 · Claude (Cowork) · OPEN LW-033: once it holds, an alarm is not heard
Did: ADR 0060 (`Runner.holding`, `Runner.felt`; `listening` false while the program holds what it
reached for; the window's Look again greys out then; What's new says so).
Measured: on the Fetch an alarm after the grasp check no longer drops the cube - the run is the
undisturbed one, the cube in the bin at 36.87 s (it was 44.24 s and 44.51 s).
Unfinished: LW-034 (a cube on its side) stays open.
For the owner: nothing to decide here.

## 2026-10-27 · Claude (Cowork) · ADR 0058 seen in the window: a motor run hot
Did: What's new's "A motor run hot" (the arm on its cart fetching with its left motor 50 K hot) and the
drive panel's mark on a weakened motor (`MujocoBackend.motor_line`, `MotorSample.kept`); What's new
newest first, its texts whole. ADR 0058 had said the window offered it; no button did.
Measured: in the window the cube is in the bin at 37.5 s with the motor hot, as without it.
Unfinished: nothing new; LW-036 still waits.
For the owner: nothing to decide here.

## 2026-10-27 · Claude (Cowork) · FR-005: how near it is to tipping
Did: ADR 0059 (`control/tipping.py`: the force-angle measure and its `Watch` on the solver's state; the
drive panel's line and the run report's least; What's new's "How near it is to tipping").
Measured: on the tilt table the arm cart's angle runs out at 53.5 deg, 0.7 before its static prediction
and 1.1 before the field reads it over; the cart alone keeps 11.9 deg at the table's 60; a hard stop from
full speed takes 3 to 4 deg from each kit cart and tips none.
Unfinished: OPEN LW-038 (the dynamic check needs a machine that tips on braking).
For the owner: nothing to decide here; LW-036 still waits.

## 2026-10-27 · Claude (Cowork) · FR-019: a motor run hot
Did: ADR 0058 (`MotorProfile.weakened`, `MujocoBackend.weaken`, the 'motor' disturbance kind with
`hot()` from copper's coefficient and `WEAK`, offered in the window's disturbances).
Measured: the kit cart with its left motor 50 K hot (84 % of its torque) runs every drive field and the
Fetch step for step as before; its drive never asks for more than the motors' 0.5 N m operating cap;
on the Sprint nothing changes down to 30 %. FR-019's predicted curve was not seen.
Unfinished: nothing new; LW-036 still waits on the owner; FR-007 (rollers too long for the cell's
parts, noted) waits on the owner.
For the owner: nothing to decide here.

## 2026-10-26 · Claude (Cowork) · LW-037: the cell lowers its parts straight down
Did: ADR 0057 (`factory/controller.py`: the four vertical stages carry joint solutions a centimetre
apart along their line, `Stage.path`, `FactoryCycle.along`; the hand opens 8 mm past the part to let
go, `release_grip`).
Measured: the same 38 runs as ADR 0056 - every run finishes, tall blocks too; 228 of 228 parts within
their room (tall: none before); lowered, the tool keeps within 5 mm of the vertical (it swung 7 to 15
mm); 12.4 s a part.
Unfinished: LW-036 (the Panda's sag and squeeze, the owner's call).
For the owner: nothing new to decide; LW-036 still waits.

## 2026-10-26 · Claude (Cowork) · FR-029: the factory cell judged by its process window
Did: ADR 0056 (`factory/process.py`: the room a part has in its slot, Cpk with its interval, the tightest
zone held, a takt; `FactoryCycle.left` and `run['placements']`, `FactoryCycle.feeder`; a line under the
factory's production run; What's new's "Six parts, measured").
Measured: 38 runs, 214 parts. Small blocks land 1.4 to 4.4 mm off their slots - within the 6.5 mm room,
Cpk 1.05 along the table - at 12.1 to 13.9 s a part (a 14 s takt held); with a feeder ±5 mm and ±15 deg
off, 51 of 54 within. Tall blocks fail every run at the fifth part. The causes: the simulated Panda sags
4 mm (no gravity compensation) and its hand squeezes 1.6 N (datasheet: 70 N), so the part creeps 3.3 mm
in it. Previews of both fixes: 0.4 to 2.1 mm; tall runs then finish, two parts still 17-22 mm off.
Unfinished: OPEN LW-036 (the two fixes), LW-037 (tall parts tip).
For the owner: LW-036 - adopt gravity compensation and the datasheet's squeeze for the Panda? It changes
the Panda in every Real experiment; with it, parts land within about 2 mm instead of 4.

## 2026-10-26 · Claude (Cowork) · Watch it work: recent work seen in the app
Did: committed FR-025 (394a705, ADR 0054). ADR 0055, the owner's request of 26 October: a What's new
button in the top bar opens four demonstrations (`ui/whats_new.py`), each one press - the cube moved
after the look, a camera that freezes, a shove at the table, Look again pressed by you; the sweeps'
disturbances happen in the window during a run (`ui/live_disturbance.py`); a Look again button in the
Program panel (`Runner.alarm`, ADR 0052); two lines there on what the running program's camera last
saw and what its jaw servos feel.
Measured: each demonstration, run in the window, does what its button says: the moved cube looked for
again and fetched (done at 45.8 s), the frozen camera stopping the program at 14.8 s, the shoved cart
going back and fetching (50.7 s), Look again pressed at 16.2 s and the cube fetched (42.4 s); every
fetch with all four goals met.
Unfinished: "Repeat with time passing" - the latency of ADR 0053 as a run-report button - not started.
For the owner: to see it, double-click "Publish to GitHub.command", reopen Little World Builder and
press What's new in the top bar.

## 2026-10-23 · Claude (Cowork) · FR-025: searching for the failure
Did: ADR 0054 (`inventory/falsify.py`: a run's margin - Fetch against what the tuning draws certified,
the tilt table past its last hold - and a compass search over the variation box;
`mobile_manipulator_blueprint(caster_gap)`), measured against drawn set-ups.
Measured: Fetch - the search found no excursion in 40 runs where fresh draws had one at draw 19 (a
real corner); on one measure it found a knife edge at run 27. The tilt table - the search found the
plan's own corner (friction at its high end, 53.35 deg), better than 30 draws (55.03). Not adopted: the
sweeps keep their plan. The rocking cart of before ADR 0041 no longer presses the cube (10 set-ups).
Unfinished: OPEN LW-035.
For the owner: LW-035 - ADR 0041 set the casters down to stop the presses and paid with curb climbing
(LW-026); with today's program the rocking cart pressed none of the 10 set-ups tried. Revisiting ADR
0041 (a full Fetch sweep and the curbs with the casters up) is your call.

## 2026-10-23 · Claude (Cowork) · FR-028: time passes while the program looks
Did: ADR 0053 (`control/latency.py`: the bus's times from Protocol 2.0 packets, `Latency`, `sourced`,
`Lag`; `MujocoBackend.kept`, `as_it_was`, `sight`; `perception.eye.Late`; `run`/`sweep`/`disturb`
`latency=`, `sweep --latency`; `inventory/margin.py`): sweeps run with the program's pictures, servo
commands and readings late by sourced amounts, and the margin read against the sweep without.
Measured: the sourced latency (139 / 7.6 / 33 ms) held every Fetch set-up - 27 of 27 disturbed, 71 of
71 undisturbed; pictures half a second late alone changed nothing; the margin is the grasp check's
0.5 s, which the bus round trip must fit in: 0.2 s each way held everywhere, 0.25 s broke 11 of 27,
0.3 s all; the sourced bus is six times under it.
Unfinished: the finder's time was measured on the cloud's CPU, not the owner's Mac; the window runs
without latency. FR-025 (a falsifier search) is next by the ranking.
For the owner: nothing to decide.

## 2026-10-23 · Claude (Cowork) · FR-022: how late is too late
Did: ADR 0052 (`Runner.alarm` and `listening`, the recovery `ignore`, a sweep run's `alarm`,
`Run.recovered` and `Run.listening`, `sweep.shared_site`, `inventory/branch.py`): an alarm from
outside makes a program that looked recover as its own recovery does; failing runs are branched by
replaying them with an alarm every 0.5 s, and set-ups that needed no recovery are alarmed once.
Measured: the cube moved 2 s after the look, its checks ignored - an alarm rescued the run until the
program left the table in 5 of 9 set-ups and only until its own closing tipped the cube over in the
other 4; the program's own check came at least 0.28 s before that deadline in all 9. A frozen camera
has no window. 71 false alarms: 70 still met every goal, a median 5.9 s later; the one broken was
raised while the cube was held. The own runs reproduced ADR 0048's bit for bit (80 runs).
Unfinished: OPEN LW-033 (an alarm while the object is held drops it) and LW-034 (a cube on its side
is grasped as if it stood and lost on the way); the window has no button for an alarm. FR-028
(latency) is next by the ranking.
For the owner: nothing to decide.

## 2026-10-23 · Claude (Cowork) · FR-023: what looking again earns
Did: ADR 0051 (`Runner(recovery=)`, `sweep --disturb --recovery`, `Disturbed.recovery`,
`inventory/recovery.py`): the program's recovery tried against three baselines on the same set-ups
and read pair by pair.
Measured: the cube moved after the look - looking again 9 of 9, reaching again where it was 0 of 9,
a random re-aim as far off 0 of 9, stopping 0 of 9 (p = 0.0039 each); ties under the other
disturbances, each for a reason the report gives.
Unfinished: FR-022 (false alarms and the latest moment a recovery still helps) is next by the
ranking.
For the owner: nothing to decide; ADR 0033's look stays, now with the evidence that it, and what it
sees, is what rescues.

## 2026-10-22 · Claude (Cowork) · FR-030: a contact census
Did: ADR 0050 (`MujocoBackend.contact_census`, `inventory/census.py`, a sweep run's `probe`):
the contact points of each pair of parts at the moments a Fetch run's results are decided, as
set and with multiccd on.
Measured: every face-on-face pair the results rest on is box on box - the same count with
multiccd on (1-6 points); only the casters' wheels touch at one point (4-5 with multiccd). No
sweep needed rerunning. Found beside it: at the bin one caster is 0.2 mm off the floor (OPEN
LW-032).
Unfinished: LW-032 (whether the cart standing on three at the bin matters).
For the owner: nothing to decide unless LW-032 should be worked on.

## 2026-10-22 · Claude (Cowork) · FR-027: tuning draws and held-out draws
Did: ADR 0049 (`inventory/holdout.py`, the sweep's `seed`, `--holdout` and `--ledger`,
`docs/sweeps/seeds.jsonl`): every sweep records its seed; decisions are certified on draws a
ledger shows they were not tuned on, the seed entered before the run.
Measured: the Fetch program on 59 fresh set-ups (seed 20261022): every goal in 59 of 59, as on
seed 1; ADR 0041's presses none, ADR 0042's fall and squeeze within their tuned ranges. Outside:
one knock on the table of 0.77 N in a step (0.62 N the most tuned; 0.18 N over 50 ms), reported,
nothing changed.
Unfinished: FR-030 (the contact census) is next.
For the owner: from now on a decision's held-out run is entered in the ledger before it runs - a
change made after seeing it needs a new seed.

## 2026-10-22 · Claude (Cowork) · FR-026: a grasp the program feels
Did: ADR 0048 (`control/feel.py`, `programming/execution.held_now`, the sweep's, benchmark's
and window's program loops, `Run.felt` and its line in sweep reports): programs take a grasp
from what the kit gripper's servos would report, not from the simulator's contacts, which stay
the judge.
Measured: Fetch, 71 set-ups: 71 of 71 every goal; 71 grasp checks, all felt as the contacts
showed; 54 ms later at the check. Disturbed (9 set-ups under each of 7 disturbances): the same outcomes as with the contacts, and 54 grasp checks all felt as the contacts showed; no sweep check met empty jaws, and the cube taken from between closing jaws is felt as not held.
Unfinished: LW-029 (a reach that meets a moved cube waits for its pose; the arm's servos are not
read). FR-027 (held-out draws) is coded and runs next, on draws none of this was tuned on.
For the owner: the kit gripper is read as a ROBOTIS XH430 - an assumption; a real servo would
check the 6-count threshold against its own noise.

## 2026-10-22 · Claude (Cowork) · LW-030: a gripper from its file
Did: ADR 0047 (`physics/importer.py`, `assets/robot_models.py`, the backend's `robot_jaws` and
`servo_grips`, the keyboard control's closure, `Observations`): an imported robot's gripper is
found at import and driven by how closed it is; its servo squeezes with the file's effort, and
its jaws' contacts and its mimic equality are as stiff as MuJoCo takes at the 2 ms step; the
grasp blocks, Tool mode and the run report see it hold.
Measured: before, 0.12 N at each jaw and a turned-over 10.8 g box creeping out at 4.4 mm/s;
after, 10.0 N at each jaw and the box within 0.44 mm of where it was held
(tests/test_robot_library.py, 20).
Unfinished: FR-026 (feel the grasp): its sweeps were lost to a restart of the workspace and
run again.
For the owner: a gripper is recognised by its joint and link names (finger, gripper, jaw, claw,
pinch); a gripper of your own named otherwise is still driven joint by joint.

## 2026-10-22 · Claude (Cowork) · FR-033: the first hour, checked by the app
Did: ADR 0046 (`lessons.py`, `ui/lessons_panel.py`, the Guide tab, a sample arm file
`assets/samples/sample_arm.urdf`): five lessons with a set-up and a check each; the window
finishes them as the work satisfies them, in any order, and keeps progress per user.
Measured: each lesson finished in the window by a user's actions (tests/test_lessons.py).
Unfinished: LW-030 (an imported gripper and the grasp blocks) still open; FR-026's sweeps (feel
the grasp) running.
For the owner: try the Guide's lessons on the Mac - whether the steps read clearly to you is the
check no test can make.

## 2026-10-21 · Claude (Cowork) · FR-032: the tool travels its line
Did: ADR 0045 (`control/tool_motion.py` glide, line, drive, Glide; `ui/key_bindings.py`
tool_key, tick_tool; the main loop ticks the tool): tool steps travel their straight line at 5
cm/s; in Tool mode held arrow and page keys drive the tool; works for kit, Menagerie and
imported arms.
Measured: kit arm 10 cm steps 0.2-0.3 mm off the line (7-13 mm before); the imported arm's
3.6 cm step 0.4 mm (10.2); UR5e 0.6-3.5 mm (its sag); held keys 14.7 cm in 3 s within 0.3 mm.
Unfinished: LW-031 done. LW-030 (imported grippers and the grasp blocks) open.
For the owner: next by the ranking FR-026 (feel the grasp; its code is written, it needs its
sweeps), then FR-033 (an interactive first hour, which can now teach tool moves).

## 2026-10-21 · Claude (Cowork) · FR-031: robots from their own files; the readings of 21 Oct merged
Did: merged the weekly reading and the focused reading of 21 Oct (67725f5): FR-027 to FR-035,
notes under 10 proposals, 43 collection items. On the owner's request of 21 Oct, ADR 0044:
`physics/importer.py` reads a URDF or MJCF file, adds a position servo to every joint the file
leaves without a motor (stiff enough to hold the robot within 0.5 degree against its own weight,
critically damped at the joint's inertia, limited by the file's effort), turns `<mimic>` into a
joint equality, keeps one body per link, resolves `package://` meshes and copies them, keeps
links overlapping at home from colliding, and reports in plain words what it found, added and
what to check; `assets/robot_library.py` keeps the robots outside the repository, named
`user:<name>` in designs. A file dropped on the window, or the Joint lab's "Import a robot from
its file...", brings one in; `python -m little_world.physics.importer` from the command line.
Servo units ('deg', 'mm', the Panda gripper's '%') now travel with each servo instead of the
channel-7 convention.
Measured: the test arm (4.3 kg, no motors) holds 60 and -40 degrees within 0.4 degree, within 1
degree after 0.18 s; with a 3 N m shoulder it is reported too weak and falls to its limit; a
mimic finger follows to 30 mm within 0.5 mm; the UR5e imported from its own file adds nothing
and follows the shipped arm within 0.5 degree, FR3 and Gen3 import the same way, the Panda's
file is refused by name (a tendon gripper); six broken files are refused with their reasons.
Unfinished: LW-030 (an imported gripper is driven joint by joint, not by the grasp blocks),
LW-031 (a tool jog ends where sent but bows 10 mm off the line). LW-026 to LW-029 as before.
For the owner: FR-034 (the robot_descriptions catalogue: network at import time and an optional
dependency) and FR-035 (the MCP server, which you said to delay) wait for you. Next by the
ranking: FR-032, moving the tool rather than the joints (it would close LW-031), then FR-026.

## 2026-10-21 · Claude (Cowork) · FR-024: the knife-edge check
Did: ADR 0043 (`inventory/jitter.py`, `sweep --jitter K`): each drawn set-up of a sweep runs K
more times with the machine set down a micrometre off under its own label, and the report sets
each measure's spread under that against its spread across set-ups, naming the set-ups where a
micrometre moves a measure past a tenth of that (knife edges) and those whose outcome changed.
Measured: the tilt table (8 set-ups) and Fetch (ADR 0042's 59, 354 runs): no outcome changed.
Fetch's time (0.10 s against 1.2 across set-ups), squeeze (0.06 N against 1.6) and lean (0.12
degrees against 1.4) are the design's; its set-down is partly chance - the cube's fall into the
bin spreads 0.29 cm under a micrometre against 1.0 across set-ups, the bin's push 0.07 N against
0.35, the table's 0.013 N against 0.064. So ADR 0042's fall of 0.1 to 1.1 cm is a range the
design gives; which value a set-up gets is chance.
Unfinished: nothing of FR-024. LW-026 to LW-029 as before.
For the owner: next, as you asked on 21 Oct, a robot library - robots that do not exist yet,
imported from their own URDF or MJCF files - after merging the two readings of 21 Oct.

## 2026-10-20 · Claude (Cowork) · LW-024: set down, not dropped; the weekly reading merged
Did: shipped ADR 0041 (a03c950, tiny-31). Merged the weekly reading of 19 Oct (358a5e9):
FR-022 to FR-026 proposed, its notes under 13 proposals, 53 items in the collection. On the
owner's choice of 13 Oct, ADR 0042 (`control/tool_motion.py`): the Fetch program's jaws close on
the cube's upper half, squeeze 0.6 degrees more once it is felt held (`SQUEEZE`), and over the
bin tilt as far as lowers it most - 25 degrees; `inventory/handling.py` reports how far a part
leaned before it was held and at rest, and measures a fall from each release.
Measured: over 71 Fetch set-ups every goal met; the cube fell 0.3 cm (0.1 to 1.1; 6.8 cm
before), the bin pushed back at 0.52 N in a step (2.14) and 0.26 N over 50 ms (0.57), squeeze
3.9 N (5.0), in the bin at 37.3 s (36.8). Without the squeeze, 3 of 71 were not set down: the
jaws' 1 s closing ramp ends just past the cube and held it at about 0.5 N a pad, and in one
set-up (low pad friction) it crept 10 mm down the pads as the cart drove and slipped out 3.9 cm
up - the jaws then pressed it at 1.65 N, and ADR 0040's fall measure had said it fell nothing;
two were pressed onto the floor while held (0.6 N). Shoved 6 N s at the table, the blind program
now fetches the cube upright (knocked over before). Under every disturbance the same set-ups
fetched as before, each set down; with the cube moved 5 cm 2 s after the look, the move now
lands after the last picture before the jaws go down, and a jaw presses the cube into the table
at 3.3 N for about 2 s until the reach times out (OPEN LW-029, new).
Unfinished: LW-028 (new: the rotary jaws pull the cube 11 mm towards the palm, so it is let go
3 to 6 mm up where 2.5 was planned); LW-029 (new, above); LW-027 (new: after the merge the collection's word search
puts a known answer in the top three for 16 of 20 questions, MRR 0.70 from 0.79); LW-026.
For the owner: as you said on 20 Oct, I go by the weekly reading: next FR-024, the knife-edge
check (it named this set-down's small forces as the likely ones to fail it), then FR-026,
feeling the grasp from the servo - ADR 0042 found the hold set by when the jaws' ramp ends.
FR-004, FR-005, FR-007, FR-008, FR-012 to FR-014, FR-019, FR-022, FR-023 and FR-025 wait.

## 2026-10-14 · Claude (Cowork) · LW-025: the cart stands on all four
Did: traced LW-025 and LW-024 (10 Oct), asked the owner (13 Oct), and on the owner's decision
set the kit cart's swivel casters to reach the floor its drive wheels stand on (ADR 0041,
`robots/mobile_platform.py`: from the parts' geometry; `mobile_platform_blueprint(caster_gap)`,
`ROCKING_GAP` for the cart as it was). The cloud workspace was lost between 10 and 13 Oct and
rebuilt from the public repository and the last bundle, with the owner's approval.
Measured: the five set-ups that pressed the cube all carried 0.44 to 0.5 kg behind the axle; the
cart teetered between its casters, tipping onto the front one as the arm reached over the cube,
and the open jaws' palm stop came down on it. On all four: pitch within 0.2 degrees (up to 4
before); over 59 drawn Fetch set-ups none pressed the cube (4 before), the table carrying 0.18 N,
the cube leaning 3.1 degrees (median; 8.8 at most, 101 before), every goal met in all 71; under
every disturbance the same set-ups fetched as before. The cost: the drive wheels carry 15 % less;
at a curb the cart stalls, motors at their limit, until it has slewed onto a drive wheel - it
clears 10 to 18 mm at 10.4 to 11.6 s instead of 3.8 to 4.1, and nothing in the curb checks' 7 s.
Tilt table 54.6 degrees (54.0), sprint 11.9 s (11.8), a shove carries it further (8 N s: 89 cm,
79 before).
Unfinished: LW-024 (the cube is let go 6.8 cm over the bin's floor; the owner chose to tilt the
jaws over the bin, next); LW-026 (new: stalling at curbs; a sprung caster or rocker not modelled).
The weekly brain run of 12 Oct failed (usage limit); the next is 19 Oct.
For the owner: a correction - on 13 Oct I said the cart on all four "climbs no curb, not even
10 mm": that came from the curb checks' 7 s window; given longer it clears the same curbs, slowly.
FR-004, FR-005, FR-007, FR-008, FR-012 to FR-014 and FR-019 wait for you.

## 2026-10-09 · Claude (Cowork) · FR-020: how gently a part is handled
Did: the owner picked FR-020. ADR 0040: `MujocoBackend.contact_forces(body)` gives the forces on
a body by what touches it, as the solver applied them; `inventory/handling.py` follows the parts
a field's goals carry through every run (`Run.handled`): for the machine, the table and the bin,
the hardest push on the part from any one of their bodies - so two jaws squeezing count as the
squeeze and do not cancel - in a step and averaged over 50 ms; its largest lean; how far it fell
when let go. The varied report adds a table, the disturbance report a row per disturbance;
`sweep.run(timestep=)` for the instrument check.
Measured: the resting cube's support equals its weight to 0.01 %. Halving the step moved forces
in a step by up to 12 %, over 50 ms by up to 4 %. Over 59 drawn Fetch set-ups, all goals met:
squeeze 4.8 N over 50 ms (3.7 to 6.7), let go 5.8 cm above the bin floor, landing at 1.9 N;
in 4 of 59 the cube was first pressed into the table (0.6 to 2.0 N), in 2 it leaned past 20
degrees, and carrying 0.5 kg it tipped onto its side. Cube moved 5 cm, blind: pressed into the
table at 5.1 N; looking: the table only carried it.
Unfinished: LW-024 (the cube is dropped into the bin, not set down) and LW-025 (some successes
press the cube into the table first), both found, not fixed. No gentleness verdict: no sourced
fragility or gripper rating.
For the owner: LW-024 and LW-025; FR-004, FR-005, FR-007, FR-008, FR-012 to FR-014 and FR-019
wait for you.

## 2026-10-08 · Claude (Cowork) · FR-021: how well the camera must be mounted
Did: the owner picked FR-021. ADR 0039: the adapter can set a camera off the pose it was built
at (`MujocoBackend.move_camera`), and an `Eye` given a believed pose reads its pictures as if
the camera stood there; `sweep --camera-error X,Y,Z[,PAN,TILT,ROLL]` (mm, degrees) runs a
varied sweep that way and the report says so. `perception/calibration.py` is the closed form:
where a point is read with the camera off by a shift and a turn.
Measured: closed form at the camera's 0.88 m - pan 15.3 mm a degree sideways, tilt 13.1 mm
along and 7.8 mm down, roll 0.3 mm; the sightings agreed within 2.5 mm. The jaws' margins,
from shifting the camera: 10.5 mm too far along, 25 mm sideways, 10.3 mm too low, at least
38 mm towards the cart and 29 mm too high. Onsets as designed where closed form and margins put
them: pan 1.75 held, 2 not; tilt up 0.75 held, 1 not. 59 drawn set-ups each: pan 1.5, tilt up
0.5, 10 mm up - 59 of 59 (at least 95 %); 10 mm towards the cart 58 of 59; tilt up 1, 8 of 59.
Unfinished: errors were certified one at a time; one combination near two margins missed, so a
joint budget needs its own runs. The program does not detect its own calibration error.
For the owner: FR-004, FR-005, FR-007, FR-008, FR-012 to FR-014, FR-019 and FR-020 wait for
you.

## 2026-10-08 · Claude (Cowork) · FR-018: a camera that can fail
Did: the owner picked FR-018. ADR 0038: a disturbance can fail the field's camera as it happens
- frozen on its last frame, or dark - alone or with a move, the camera failing first; Fetch
gains "camera frozen as the cube is moved 5 cm" and "camera dark at the table". Each picture
carries a frame number, when it was taken and the share of it with depth; the runner ends a
look on three pictures in a row that are not new or are dark, naming the camera, and before
the jaws go down treats such a picture as no evidence (it looks again, or stops).
`Runner(checks=False)` and `sweep --unchecked-camera` take pictures on trust, to measure the
difference. The disturbance report now quotes what the program said where set-ups missed, and
prints a p below 0.0001 as such.
Measured: frozen, on trust: 0 of 9, the jaws down twice at the stale place in every set-up;
checked: 0 of 9, all named at the look, nothing grasped. Dark: on trust "it would not keep
still" after 5 s; checked "has no depth" 0.3 s after it went dark. The other 54 runs of the
nine-set-up sweep, and the 60 undisturbed runs of the 59-draw sweep, met their last goal at
the same time as before: no false alarm.
Unfinished: the frame number decides, not the picture's time, so a frame frozen within one
picture interval of its first use is used once; a camera knocked off its mount is FR-021's.
For the owner: FR-004, FR-005, FR-007, FR-008, FR-012 to FR-014 and FR-019 to FR-021 wait for
you.

## 2026-10-08 · Claude (Cowork) · LW-022 and LW-023: looking again without dragging or doubting
Did: the owner picked LW-022 and LW-023, the two faults ADR 0036's paired runs showed. ADR
0037: a reach for the cube that is stopped, and a grasp that holds nothing, first rise back to
the pose the arm reached down from, the way they came, then go back to look again (the runner
keeps that pose when a reach for the object begins). A picture before the jaws go down that
finds nothing no longer means the cube has gone: the camera says what it shows where the cube
was seen (`Eye.place`, `boxes.place`) - each ray that would meet the cube followed to its
surface: there, empty or hidden - and only empty looks again.
Measured: ADR 0036's paired sweep again (59 drawn set-ups, the cube moved 5 cm 2 s after the
look): broken 0 of 59, at most 5 % (1 of 59); every goal met 60 of 60 (59 of 60); undisturbed,
none looked again for nothing (2 of 60); the median change from undisturbed +3.1 s, as before.
Set-up by set-up against the previous version, only the set-ups the faults touched ran
differently: the eleven whose reach was stopped on the moved cube (repeat 9 now fetched; the
other ten 0.35 to 0.6 s sooner in nine, 0.3 s later in one) and the two that had looked again
for nothing (4.1 s sooner). Every disturbance on the nine set-ups: 9 of 9, the same median
changes; the cube set down elsewhere: 17 of 19 looking, 6 blind, as before. Traced, repeat
35's picture: 148 of the 170 rays that would meet the cube ended on its surface; the finder
had needed the top face, which the palm hid.
Unfinished: hidden is taken for there, so a cube moved under the jaws' cover is found by the
grasp, not before; a reach pushed off its stop still goes straight back to it (ADR 0031). The
container restarted once during the measurements (the first paired sweep was lost at 94 of
120 runs and run again from the start).
For the owner: FR-004, FR-005, FR-007, FR-008, FR-012 to FR-014 and FR-018 to FR-021 wait for
you.

## 2026-10-07 · Claude (Cowork) · FR-017: paired runs
Did: the owner picked FR-017. ADR 0036: every drawn set-up of a disturbance sweep is a pair,
its undisturbed run and its disturbed run, one run until the event - `sweep.run` can record a
digest of every joint's position and speed at every step, and the tests show a pair equal bit
for bit up to the event and different from it on, on the Sprint and the Fetch fields. The
report gains "Broken by it": of the drawn set-ups that met every goal undisturbed, how many the
event broke, with the share of successes it breaks (95 %), how many failures it turned round,
and the exact McNemar p (`confidence.mcnemar`, standard library). `sweep --disturb --only
LABEL` runs one disturbance; the run report's panel says "broke k of n".
Measured: the cube moved 5 cm sideways 2 s after the look. Without looking again (ADR 0033
off): 8 of 8 drawn successes broken, at least 69 %, p = 0.0078 (FR-017 expected nine and
0.0039; the as-designed set-up is chosen, not drawn). With it, 59 drawn set-ups: 1 of 59
broken (0 to 9 %), p = 1, the cube in the bin 3.1 s later (median). The broken pair (repeat 9),
traced: the cube moved 26 ms after the picture before the jaws went down, a jaw came down on
it, the reach was stopped, and the arm, rising to its ready pose to look again, dragged the
cube over the table's edge.
Unfinished: LW-023 (new), that drag; LW-022 again, in 2 of the 60 undisturbed set-ups. The
proposal's `--paired` flag and cache of twins were not built: every disturbance sweep already
runs each set-up undisturbed, so every report pairs.
For the owner: LW-022 and LW-023 are faults in how the Fetch program looks again; FR-004,
FR-005, FR-007, FR-008, FR-012 to FR-014 and FR-018 to FR-021 wait for you.

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
