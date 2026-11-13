# Milestone validation

Verified locally on 2026-09-11 with Python 3.13.11 and MuJoCo 3.3.7.
The exact installed runtime/test package versions are in requirements-lock.txt.

- Architecture documents and core interfaces were created before the adapter.
  The initial 14 core contract tests passed before mechanical behavior was added.
- Final suite with `LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest -q`:
  **21 passed**. Includes headless mechanics and actual OpenGL RGB capture,
  renderer reconstruction after reset/recompile, and changed image dimensions.
- Straight-drive smoke: 2 simulated seconds at 0.5 Nm on each wheel produced
  chassis position approximately (0.3281, -0.0021, 0.1193) metres. This demonstrates
  actuation/contact integration, not a real-world trajectory accuracy claim.
- Opposed torques turn the assembly. Tests verify finite poses, duplicate Blueprint
  instances with separate IDs, unordered component input, gravity/contact settling,
  command rejection, zeroing omitted commands, and exact initial-state reset.
- Actual camera PPM was produced and visually inspected. An inspection-camera
  rendering was also inspected and is saved at media/prototype.png.
- `.venv/bin/mjpython examples/two_wheel_robot.py --seconds 3` opened the native
  viewer and exited successfully. Interactive mouse movement, drive key presses,
  camera selection and reset/reopen remain manual acceptance checks; they were not
  exercised through UI automation in this run.

## Limits

The room uses a floor and four low walls so the assembly is easy to inspect. The
robot uses passive spherical skids rather than simulated caster assemblies.
MuJoCo's default equal-priority friction mixing takes the larger coefficient for
each pair, so a low coefficient on a skid does not override the floor coefficient.
Motor sizing in this prototype accommodates that contact model. No calibrated
static/dynamic friction split, restitution, thermal state, wetness, power budget,
or cross-physics interactions are claimed. Zero motor torque allows coasting.

Blueprint version 1 supports a tree of primitive bodies, one hinge per non-free
body, direct torque motors and cameras. It rejects unsupported kinds. Attachment
frames and controller descriptors serialize, but a snapping editor and controller
registry are not implemented. State is an observation, not a restart checkpoint.

The local Git repository is initialized; no remote or GitHub repository was created.

## Drive-window correction

The initial manual acceptance gap exposed a real input conflict: the passive viewer
also processed the application's WASD/P/R keys as native MuJoCo display shortcuts.
Installed MuJoCo 3.3.7's `mjRNDSTRING` and `mjVISSTRING` confirm W → wireframe,
D → static-body visibility, A → auto-connect, and P → contact-split visualization.
The original drive window is superseded by a small GLFW window using MuJoCo's
scene, camera, renderer and physics. It installs only Little World input handlers.

The updated full graphics suite passes **24 tests**. The new window regression
injects press/release callbacks for W/A/D/S and pause/reset into an actual GLFW
window, reads rendered pixels, and checks that frames remain nonblack, geometry
counts remain unchanged, and wireframe/segmentation modes stay disabled. Reset
returns World to BUILD with simulation time zero. This tests callback dispatch
and rendering, not physical keyboard delivery by the operating system.

Both `python examples/two_wheel_robot.py --seconds 3` and the legacy `mjpython`
launch path opened and exited successfully. Hold-to-drive, physical braking on
release, focus-loss input clearing, follow camera, an onboard-camera toggle,
view restoration and visible controls replace the old persistent torque commands.

## Interactive workshop slice

Added constructor/editor tests for immutable revisions, undo/redo, material edits,
turning a plain block into a motorized assembly, subtree/reference cleanup, empty
assemblies, failed-edit history preservation, BUILD-only preview, side ordering,
and motor-strength edits. Added an actual GLFW graphics test that clicks through
panel hit testing to resize, undo, start with a block, attach both wheels, save,
simulate with keyboard input, stop back into BUILD, and load the same Blueprint.
A window screenshot is visually inspected for panel layout and room composition.

The interaction test covers callback dispatch and rendering, not OS-level physical
mouse/key delivery. Workshop attachment positions are presets and designs may
intersect or tip; there is no editor collision-validation or general snapping yet.

Final workshop verification: `LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest -q`
completed with **32 passed**. The inspected final workshop capture is
`docs/media/workshop.png`.

## Workshop responsiveness correction

The first workshop's idle window profile recorded only 25 frames in a 4-second
sampling window (~6 FPS). Per-frame drawing averaged ~81 ms, dominated by repeated
`mjr_label` calls, with another ~76 ms average spent in buffer swapping. This was
application/rendering overhead, not a slow robot command.

Replaced individual text-button draws with a once-created Pillow font atlas and
two OpenGL batches. Retained graphics contexts, font textures and render-scene
buffers across primitive-model edits. World caches a prepared immutable scene, so
starting/stopping an unchanged design does not recompile. Static body observations
are cached only for bodies welded to the world; welded children of moving objects
continue to update. Idle build-mode drawing is capped at 15 FPS and wakes promptly
on input; active interaction targets 60 FPS.

The checked-in `scripts/benchmark_workshop.py` performs a 7-second run with camera
movement, three design edits, and simulated driving. One local post-fix run:

| Measurement | Result |
| --- | --- |
| Build/orbit including edits | 54.6 FPS; median frame 17.60 ms; p95 24.38 ms |
| Simulation/orbit | 56.8 FPS; median frame 17.50 ms; p95 19.83 ms |
| Median drawing work | 3.34 ms |
| Three design edits | 13.42 / 12.55 / 9.89 ms |
| Start prepared simulation | 1.25 ms |

These are local measurements, not hardware-independent guarantees. Startup and
initial graphics creation are separate from steady-state measurements. The old
profile and new scripted workload are not an identical benchmark, but the render
bottleneck and post-change responsiveness are directly measured.

Tests now also verify preview compilation reuse/invalidation, static-cache
invalidation and movement of welded children, retained GL resources across edits,
visible font pixels, button bounds, tabbed workflow, and save-key/drive separation.
The new UI capture is `docs/media/workshop.png`.

Final responsiveness/UI regression suite: **34 passed**, including graphics tests.


## Component catalog and textures

`LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest -q`: **86 passed**.
Coverage includes all 22 modules serialized, inserted twice with unique IDs,
compiled and stepped; a catalog drive pair with fore/aft sliding supports moves
its chassis under torque. An unsupported two-wheel block can drag its chassis;
support geometry is part of the assembly, not an implicit stabilization force.
Graphics checks cover distinct material pixels, selection preserving appearance,
catalog insertion and retention of the GPU context across edits. Legacy material
refresh preserves saved density/friction. The built wheel includes all three
texture data/manifest files. Capture: `docs/media/catalog.png`.

A local 7-second benchmark with the Add library and drive-wheel preview visible
measured 55.6 FPS while building/orbiting and 57.3 FPS while simulating/orbiting.
Median drawing work was 4.87 ms; build/simulation frame p95 were 18.08/19.95 ms.
Three edits took 28.59/32.73/20.91 ms; starting the prepared world took 1.51 ms.
These are local observations, not performance guarantees or proof of physical
calibration. Texture appearance does not add surface deformation or PBR lighting.


## Precise connections and hinge editing

Full display-enabled regression suite: **92 passed**. New checks cover local and
rotated named-frame snapping, descendant/cycle rejection, undo/redo, legacy Hinge
JSON defaults, precise geometry and pose, pivot/limit/damping configuration and
motor removal. A native dynamics test drives a bounded hinge and confirms its
angle settles near the configured 30-degree stop (within a 3-degree allowance for
MuJoCo's soft constraints). UI checks enter dimensions and joint values, verify
Enter applies without starting simulation, exercise motor pulses and cancellation,
and save/load the result while retaining graphics resources.

Local benchmark with Connect inspector and selected wheel: 55.7 FPS build/orbit,
57.5 FPS simulation/orbit; median draw 4.22 ms. Frame p95: 22.03/19.40 ms. Three
edits: 48.03/19.74/20.97 ms; prepared start: 1.11 ms. Captures inspected at
`docs/media/connections.png` and `docs/media/precision-form.png`. Visual inspection
caught/fixed a clipped tab, font layering over modal backgrounds, and an invisible
arrow primitive (replaced by a visible decorative axis line). These observations
are local UI/mechanics validation, not measured real-world robot calibration.


## Focused workbench and engineering-style hardware

Final full display-enabled suite: **127 passed** (9.33 s). This covers all 36
catalog modules inserted twice, JSON roundtrips and native stepping; preservation
of internal motors/materials/output frames; full compound-envelope placement;
independent caster axes; and a mobile chassis driven through its motor shafts.
UI checks open the workbench, search, insert gearmotor/servo modules, preserve the
mounting target, save, return to room simulation and restore the design.

The default CLI now opens the hardware mobile platform in the workbench; `--classic`
retains the earlier example. `docs/media/build-workspace.png` was visually checked.
Representative motor, servo, extrusion, bearing, hub and caster renders were also
inspected; ring segment widths were corrected to eliminate unintended flange gaps.

Detailed geometry initially caused high observation overhead and redundant renders.
Snapshots now batch-detach data and materialize public BodyState objects on access.
Velocity output is tested against mj_objectVelocity for every body in a rotating
hardware assembly; retained snapshots are tested after later integration. A separate
test confirms post-step body/geom/camera poses and velocities match full mj_forward.
The physics timestep and torque-control feedback cadence are unchanged.

Final reproducible local run: `scripts/benchmark_workshop.py --hardware`:

| Measurement | Result |
| --- | --- |
| Workbench build/orbit, including three edits | 50.3 FPS; median 17.28 ms; p95 17.89 ms |
| Hardware simulation/orbit | 50.7 FPS; median 17.48 ms; p95 22.57 ms |
| Median drawing work | 5.61 ms |
| Three structural edits | 102.82 / 102.75 / 98.25 ms |
| Start prepared simulation | 5.36 ms |

Edits still synchronously compile the detailed design, causing occasional ~100 ms
pauses; ordinary frames remain responsive. These results are local, not universal
performance or physical calibration claims. Workbench previews omit shadows because
there is no receiving floor; the room retains shadows at 1024px resolution.


## Assembly hierarchy and duplication

Full display-enabled suite: **132 passed** (10.15 s). New contracts cover copying
a motor and its attached wheel, independent native actuation, complete-robot
controller remapping, camera references, non-finite offset rejection, and exact
undo/delete restoration. UI checks cover the assembly browser, module picking,
duplicate form, focus, deletion, undo and saved-design roundtrip. The updated
workbench layout was inspected in `docs/media/assembly-browser.png`.

Module duplication retains physical geometry and can produce overlaps if the user
chooses a small offset; placement remains an explicit design operation. The UI
continues to use the first compatible differential controller in room simulation.

## Keyboard manipulation

The display-enabled suite passes 144 tests, including a native keyboard-panel
edit/save/start/pause/reset check. The contact integration test closes the jaws,
lifts the cube by more than 9 cm, holds it, then opens and verifies it falls to the
floor. No equality constraints are present. In the example run, the cube centre
rises from 20.7 cm to 32.8 cm before release. The same program runs through
`examples/programmed_pickup.py` without a window. Torque remains bounded and
positions are never assigned by the controller. The panel and full arm were
visually inspected in `docs/media/keyboard-arm-lab.png`.

This checks the prepared cube pickup, not arbitrary grasp planning or calibrated
robot dynamics. Target holding uses PD feedback and model bias compensation;
contacts, insufficient motor torque and joint limits can prevent the target pose.

## Gripper configuration and mobile arm

Display-enabled full suite: **157 passed**. The focused configuration suite also
passes all nine tests after the final UI adjustment. Checks cover transactional
configuration, isolated material edits, save/undo, all three pad shapes reaching
the native friction/torque parameters, all three arm sizes compiling, and driving
the cart while raising its shoulder. The cart remains upright during that bounded
motion test; arbitrary payload/trajectory stability is not asserted. The existing
contact pickup regression still passes. Gripper shape/material dialogs were tested
through native mouse callbacks, and the mobile assembly layout was visually
inspected in `docs/media/mobile-arm.png`.

## Sourced motor profiles

Full display-enabled suite: **163 passed** (14.98 s). Coverage includes frozen
source/profile JSON, legacy motor loading, undo, invalid operating caps, estimated
forward/braking envelopes, direct native command enforcement, model selection and
CSV export through the UI. An unloaded centered rotor with resolved timestep
converges to different endpoint speeds for the two profiles. This is a software
regression against our assumed envelope, not physical validation of either servo.
The study layout was visually inspected in `docs/media/motor-study.png`.

The envelope limits torque, not velocity. External loads can backdrive a motor
above its no-load speed. Very low inertia with a coarse timestep can also overshoot
because the envelope is evaluated once per step; timestep convergence remains
necessary for such assemblies. Braking, firmware and continuous-duty capability
are unvalidated. No source values have been labeled measured by this project.

## Program, guided building, sensors and hardware families

Full display-enabled suite: **179 passed** (15.26 s). The native workflow test
reorders program blocks, undoes, saves, executes a single block, then runs the full
pickup sequence and verifies lift/release. Other tests cover stale action references,
repeat and branch semantics, move completion, sensor timeout, real bilateral pad
contact, body-centre distance, guided transactional additions, and all family
assemblies compiling/roundtripping. The GUI flow test chooses a starter, adds a
contact condition through chained modal selectors, exports Test feedback and loads
a compact family. Existing workshop, catalog, motor-profile and mechanical tests
remain passing. Program, Test and Guide layouts were inspected under docs/media.

The sensor model is ideal; contact signals may lag poses by one native step.
Bilateral contact does not establish a secure grasp. Slip/contact-loss and tilt
alerts are diagnostic heuristics, not calibrated failure detectors. Family module
geometry matches our assembly frames but has no certified vendor fit or load rating.

## Inventory and comparisons

Full display-enabled suite: **184 passed** (17.93 s), followed by all five focused
inventory tests passing after the final result-persistence adjustment. Checks cover
UUID snapshots, immutable design/program roundtrip, draft/finished metadata edits,
invalid-file isolation, restart persistence, gravity/mass estimates against an
analytic 1 kg / 1 m case, exact component field differences, and identical-world
trial repeatability. A deliberately weaker shoulder produces greater simulated
tracking error. The GUI test saves a version, runs background comparison, edits
metadata, loads it and verifies recovery of the previous workspace. Inventory
Overview/Parts changes/Performance layouts were visually inspected under docs/media.

Trials use a five-second horizon and the same environment/protocol on both sides.
Parts analysis is a starting-pose estimate. Neither produces real-device validation,
an overall quality score, a payload rating or an electrical-energy prediction.

## Laboratory equipment collection — 2026-09-20

`LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest -q`: **398 passed**.
New contracts cover all 14 portable assemblies, insertion anchoring and undo,
Panda mounting, passive rollers, RGB camera presence, default joint bindings,
four-/six-wheel and mobile-Panda driving, and anchored rotary actuation.
After extending the UI assertions, the spatial-drag graphics test also passed
separately, checking All/Arms/Lab filtering, live roller search, mesh dragging,
exact placement, cancellation and undo. Native UI appearance was inspected at
1280 × 860; screenshot: `docs/media/lab-equipment.png`.
These are software behavior checks, not hardware calibration or payload validation.

## Second lab collection — 2026-09-20

Full native/graphics suite: **442 passed** with
`LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest -q`.
Additional coverage checks UR5e/Kinova/default tilt bindings, portable round trips,
loose-object behavior, three new mobile-base driving cases and powered tilt motion.
Rendered previews were regenerated and inspected for the tilting table, inspection
station and Kinova mobile manipulator. The inspection camera also produced a
nonuniform 160 × 120 RGB frame in an explicit native capture check.

## Click-to-jog robot controls — 2026-09-20

Full native/graphics suite: **447 passed**. All four sourced arms were exercised
with accumulated jog targets and actuator-range clamping; Panda gripper increments
were checked in closure percentages. Native UI checks verify click-to-start,
pause, restoration of the unchanged design, and visible gripper controls. After
pinning the gripper row and preserving its binding editor, the updated UI test
passed separately. The final panel was visually inspected; screenshot:
`docs/media/robot-controls.png`. These are bounded joint commands, not IK or
collision-aware motion planning.

## Factory starter cell — 2026-09-21

Full native/graphics suite: **455 passed** with
`LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest -q`.
Both block sizes completed physical grasp/lift/placement into both destination
bins. Planning left live qpos unchanged; the tests verified actual final product
position and lift. A deliberately displaced product produced a missed-grasp
failure, not a successful attachment. Native UI coverage exercised one-stage
pause, resume to completion, reset, product selection and unchanged robot design.
The factory window and sampled trajectory preview were visually inspected in
`docs/media/factory-cell.png`. This validates the fixed known-object cell only,
not general perception, collision avoidance or real hardware transfer.

## Direct factory authoring and guided explanations — 2026-09-21

Full native/graphics suite: **464 passed**. Recipe tests cover immutable edits,
JSON round trips, overlap/table/robot/camera obstruction explanations, and physical
cycles with a moved tray and an alternate source. A native UI test presses and
drags projected tray locations, rejects an invalid drop, clicks source/destination,
saves and reloads the recipe, undoes edits, and runs a guided physics stage before
returning to authoring. The final explanation card was moved below the active
robot view and visually checked in `docs/media/factory-guided.png`.
Placement validity and IK reachability are distinct; these checks are not general
collision avoidance or validation of every possible authored layout.

## One window, Real and Anime workspaces — 2026-09-21

Full native/graphics suite: **465 passed** with
`LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest -q`.
Native coverage counts GLFW window creation across repeated workspace switches,
checks preservation of unsaved builds, programs, cell layouts and paused simulation
state, and exercises all four sourced arms with joint programs. It also checks
reset stopping execution, the robot picker, and header layout at the minimum
window size. Real joint programming and Anime building were visually inspected
in `docs/media/real-workspace.png` and `docs/media/anime-workspace.png`.
Automatic pick and place remains specific to the Panda known-object cell; the
other sourced arms support joint experiments and programming, not general grasp
planning. Existing running apps need a restart to load the unified workflow.

## Sourced contact-pair friction — 2026-09-25

Run on Linux (Python 3.11, MuJoCo 3.3.7, Mesa under Xvfb for the window tests):
`LITTLE_WORLD_TEST_RENDER=1 xvfb-run .venv/bin/python -m pytest -q` - **478 passed**.
Before this change the same machine gave 463 passed and 2 failed; see the last
paragraph for those two.

The defect, measured before touching anything: the two-wheel robot's skids are
"skid" material (0.01) on a 0.8 floor, and MuJoCo's max() gave every skid contact
0.8. Driving at a steady 0.4 Nm per wheel, a skid carried 82 N and dragged with 65 N
of tangential force - a ratio of exactly 0.80.

| Two-wheel robot, room floor, 4 s | Before | After |
| --- | --- | --- |
| 0.2 Nm per wheel | 0.02 m | 1.15 m |
| 0.4 Nm per wheel | 0.78 m | 2.53 m |
| 1.0 Nm per wheel | 2.79 m (wall) | 2.76 m (wall) |

| Contact, as solved | Before | After (source) |
| --- | --- | --- |
| rubber wheel on concrete floor | 1.20 | 0.95 (Xu et al. 2025) |
| skid on concrete floor | 0.80 | 0.10 (PTFE, analogue of Chemours steel data) |
| wood block on wood floor | 0.65 | 0.36 (Villar-Garcia et al. 2022) |
| wooden cube on aluminium stand | 0.60 | 0.19 (CTU Code factor) |
| steel pivot cap on wood floor | 0.65 | 0.17 (Villar-Garcia et al. 2022) |

Checks added in `tests/test_contact_pairs.py`: every pair is bounded, cited, labelled
and at most low confidence when it is an analogue; lookup is symmetric and returns
nothing it has no source for; surfaces round-trip through Blueprint JSON and old JSON
loads; library materials saved before surfaces existed are recognised only when id,
density and friction are all unchanged; a gripper friction the user typed is never
replaced; a wooden block holds on a wooden plank 6 degrees below atan(0.36) and slides
6 degrees above it; an unsourced pair (copper on the floor) keeps MuJoCo's max(); the
inventory trial fingerprint changes when any table value changes; the reference page
is regenerated from the table. **With nothing sourced, 600 steps of the staged
`mj_step` are bit-identical to `mj_step`** (qpos and qvel compared exactly).

Cost, best of three on this machine: compile time unchanged (two-wheel 8.1 -> 7.9 ms,
mobile manipulator 116 -> 118 ms); `backend.step` two-wheel 81 -> 107 us, arm lab
133 -> 171 us, mobile platform 836 -> 943 us, mobile manipulator 1002 -> 1053 us.
About 16 us of that is the staged step and 9 us the table lookup; the remainder is
the physics changing (contacts that used to stick now slide).

The two tests that failed here before this change - `test_arm_grasps_lifts_holds_and_releases_by_contact`
and `test_program_workspace_pickup_save_step_and_drag` - asserted that a released cube
lands on the floor. Where it lands is a millimetre-scale coin toss: moving the cube's
start by 1 mm sends it back onto its stand or down beside it, and so does the
difference between the macOS and Linux builds of the same MuJoCo version. Both tests
now assert what release means - the cube comes back down and no pad touches it - which
holds whichever way it lands. (Run here on Linux only; the Mac has not re-run them.)

Not claimed: static friction or stick-slip, pressure-dependent rubber friction, wet
or dusty surfaces, torsional or rolling friction (unchanged defaults), or calibration
of any pair against this project's own measurements.

## Drivetrain and axle losses — 2026-09-25

Run on Linux (Python 3.11, MuJoCo 3.3.7, Mesa under Xvfb for the window tests):
`LITTLE_WORLD_TEST_RENDER=1 xvfb-run .venv/bin/python -m pytest -q` - **494 passed**.
See ADR 0011 for the model. The defect, measured at the ADR 0010 commit before
touching anything: every hinge's 0.01 N m s/rad damping was the only loss on a wheel.

| Kit gearmotor and mobile platform | ADR 0010 | Now | Reference |
| --- | --- | --- | --- |
| Bare 37 mm gearmotor, 0.5 Nm command | 477 rpm | 330 rpm | Pololu 37D 30:1, 12 V: 330 rpm |
| Platform drive wheels, 0.5 Nm per motor | 384 rpm | 321 rpm | below 330 under load |
| Platform speed at that command | 1.94 m/s | 1.74 m/s | |
| Caster wheel slip while cruising | 100 % | 64 % | casters carry 0.1 N at rest |
| Platform coast-down | 0.33 g | 0.15 g | 0.13 g from the modelled losses |

The platform stands on its two drive wheels; at rest its casters carry 0.08 N of its
17 N, so they are dragged more than rolled - a property of that example assembly,
not of the loss model. Its coast-down (1.44 m/s^2) is 15 % above the closed form for
gearbox friction plus rolling resistance (1.25 m/s^2). With smooth 50 mm cylinder
tyres and no swivel damping it is 4 % above (1.17 against 1.13). The difference is
the 24-block polygon tread and the swivel's unsourced damping, and it does not add up
linearly: either change alone gives 1.51 or 1.57 m/s^2. Chassis height ripple from
the polygon tread: 0.2 mm.

Checks in `tests/test_drivetrain.py` (16): the nine Pololu profiles match the
datasheet table; the net output meets both datasheet endpoints exactly; old profiles,
invalid currents and JSON round-trip; the rolling table is in metres and labelled;
kit axles lose their damping while ideal drives keep it; each wheel's dry friction is
exactly b x N from its own solved contact (to 1e-9) and reset restores the compiled
values; a swivel gets no rolling loss and its wheel does; the hardware tread wheel's
24-block ring carries 0.8-1.2 of the platform's weight as rolling load; a rubber pad
pressed by a hinged finger gets none; **a four-wheel cart's coast-down is within 1 %
of (M + sum I/r^2) a = b M g / r** (measured +0.2 %; +0.5 % with 20 mm wheels); a
gearmotor driving a 2.2e-4 kg m^2 disc reaches 330 rpm within 0.1 %, holds still under
80 % of its friction torque (under 1 mrad in a second) and coasts to rest in the
Coulomb time to 2 %; a bare output shaft (1.8e-8 kg m^2) runs within 0.1 % of 330 rpm
with no limit cycle - ADR 0007's once-per-step envelope sawtoothed it around 24,000
rad/s; the implicit slope appears only where the speed-torque line limits the command.

Dry-friction settings, a 37D driving that disc: MuJoCo's defaults crept 0.20 rad in a
second under 80 % of the friction torque, took 0.213 s to coast down against Coulomb's
0.145 s, and let the bare shaft run 3.7 % fast; the shipped settings give 0.000 rad,
0.145 s and 0.0 %. MuJoCo's own rolling friction (condim 6, same lever arm) on the
cart: 39 % and 23 % short of the closed form with the pyramidal cones used here, 1.0 %
and 1.3 % short with elliptic cones; the hinge policy: +0.2 % and +0.5 %.

The two-wheel robot now travels 0.36 m in 4 s at 0.2 Nm (1.15 m under ADR 0010) and
1.75 m at 0.4 Nm (2.53 m): it weighs 20.5 kg on two 85 mm rubber wheels, and rolling
resistance takes 0.12 Nm per wheel, 60 % of a 0.2 Nm command. `test_skids_skid_now`
therefore compares its sourced skids with a legacy max() skid at the same 0.3 Nm
(1.06 m against 0.02 m) instead of asserting a fixed distance, and
`test_real_profiles_produce_different_native_speed_limits` keeps to the two ROBOTIS
servos it was written for (the Pololu profiles have their own speed test).

Cost, best of three interleaved runs against the ADR 0010 commit: compile 0.5-1.5 ms
more; step two-wheel 86 -> 119 us, arm lab 124 -> 142 us, mobile platform 793 -> 849 us,
mobile manipulator 1046 -> 1102 us.

Not claimed: rubber's rolling resistance (an analogue), rotor inertia, speed- or
load-dependent friction, backlash, heating, current limits, tyre deformation, or
rolling resistance for loose bodies such as a ball on the floor.

## Test drive — 2026-09-25

Run on Linux (Python 3.11, MuJoCo 3.3.7, Mesa under Xvfb for the window tests):
`LITTLE_WORLD_TEST_RENDER=1 xvfb-run .venv/bin/python -m pytest -q` - **510 passed**
(headless: 479 passed, 31 skipped). See ADR 0012.

Measured on the mobile platform with a segmentation render of the 3D view: the box
around the machine covered 0.4 % of the view when simulating (0.1 % of its pixels were
the machine); in the chase view it covers 6.4 % (2.5 %). The chase view stays behind
the machine as it turns, and a ray against the room pulls it in front of walls.

Checks in `tests/test_test_drive.py` (16): path length is the path, not the
displacement, and ten seconds of sub-millimetre shimmer add under 5 mm; tilt, the
time-weighted shares at the motor limit and slipping, and what was touched; paused
frames add nothing and time cannot run backwards; a run is compared with the previous
one; angles wrap the short way, the chase view settles behind the machine without
swinging round, keeps the user's orbit relative to the heading and eases a jump; the
trail keeps a 3 m straight run as one segment and a quarter turn as a handful. On the
real platform in the room: forward speed within 10 % of the drive assist's 0.425 m/s,
each wheel's rpm within 15 % of speed / radius, no slip, the kit gearmotor's 330 rpm
no-load speed, torque never above what is available, and the drive assist named as
what sets the top speed (the motors alone could reach 1.73 m/s); a spin on the spot
turns 140 degrees while the centre of mass moves 3 mm (its chassis-rail origin moves
25 cm); driving into the pickup stand reports it by name, never the floor, with the
treads slipping and the motors at their limit more than a fifth of the time. Window
tests build, drive, stop, read the report and return to the Build stage, and show the
two-wheel robot's onboard camera only while driving and not when it is already the
main view.

Cost: the trail draws 30 m of driving with turns in 0.6 ms a frame (straight runs
merge into one segment); a per-frame telemetry sample, contact scan and log update
are well under a millisecond. The onboard inset renders the scene a second time, only
for machines with a camera.

Not claimed: sensor models (the readings are exact simulator state), force or damage
from contacts, or comparisons under controlled conditions - reports are per session
and the inventory's trials remain the way to compare saved versions.

## Test fields — 2026-09-25

See ADR 0013. Every field compiles with the mobile platform and the six-wheel rover
without overlapping them at the start, and the platform settles within 2 mm of its
height in the workshop room. Results of driving straight ahead with the drive assist
(5 rad/s targets, its default 0.425 m/s limit); the ramp columns aim each machine
head-on at one ramp:

| Machine | 5 m sprint | Curbs cleared | Ramps climbed | 4 kg crate past 3 m |
| --- | --- | --- | --- | --- |
| Mobile platform (2 x Pololu 37D, casters) | 11.8 s | 10, 20 mm (10 mm since ADR 0017) | 8 deg | no |
| Two-wheel robot (20.5 kg, skids) | 13.6 s | none | none | 14.0 s |
| Four-wheel rover | 12.4 s | 10, 20, 35 mm | 8, 14, 20 deg | 7.5 s |
| Six-wheel rover | 12.4 s | 10 mm | 8 deg | 7.0 s |
| Delivery cart (casters) | 12.5 s | none | none | 9.9 s |

The failures have physical reasons the tests hold: the platform's swivel casters (40 mm
wheels; ADR 0017 found they had crept up the 20 mm curb, as tall as their radius)
cannot climb a 35 mm curb; the two-wheel robot needs m g sin 8 deg = 28 N on the 8
degree ramp and its 1 Nm motors on 85 mm wheels give 23.5 N - with a plastic chassis
(9.1 kg, 12.4 N needed) the same robot climbs it; a 4 kg crate on concrete takes 15.7 N
to slide. The platform's sprint time is 5 m at the drive assist's 0.425 m/s to within
6 %, not its motors' 1.73 m/s. The rigid four-point platform stalls on the 14 degree
ramp with its drive wheels unloaded once a caster is on the slope - the same thing a
rigid chassis without suspension does.

Checks in `tests/test_fields.py` (14): lines crossed forward within their extent,
gates only in order with timed splits, "whole machine over" for curbs, delivery only
at rest, upright and undisturbed kept until broken (a moved bollard stays counted),
open versus missed; field data (titles, goals naming real bodies, unknown fields
refused, nothing overlapping the start), compilation with a sky and equal settling
height, and the four physical results above; a window test chooses a field through
the real button, drives it, refuses a field change while running and reads the goals
in the report. Full display-enabled suite: **524 passed**.

Not claimed: the props are test props, not standard courses; goals judge body
positions (a line is crossed when any body is past it within the gate), not contact
patches; fields are not randomised; inventory trials still run in the workshop room.

## Servo damping integrated implicitly — 2026-09-25

See ADR 0014. Found while checking whether the mobile manipulator stands: with its
drive holding zero and every arm target unchanged it could not stand still. Measured
over the last 1.5 s of 3 s on the sprint field's concrete, same gains and designs:

| Case | Explicit damping (before) | Implicit (after) |
| --- | --- | --- |
| Mobile manipulator standing, arm held | arm at its torque limits 70 % of steps, elbow 17 deg off, base rocking 5.4 deg, crept 12 cm | 0 %, 0.0 deg, 0.00 deg, no creep |
| Compact arm kit, 0.2 rad/s nudge on every joint | 75 % at limits, 21 deg off | 0 %, 0.0 deg |
| Standard arm (arm lab), same nudge | 21 %, 7.0 deg off | 0 %, 0.0 deg |
| Long-reach arm kit, same nudge | 0 %, 0.23 deg | 0 %, 0.23 deg |
| Arm lab keyboard pickup (G, R, hold) | cube lifted 12.1 cm | 14.4 cm |

The spectral radius of the step-to-step damping map (1 - dt M^-1 Kd) predicts which
arms chatter: 44 compact kit, 25 mobile manipulator, 5.0 standard arm, 1.00 long reach;
the implicit map's is below 1 for all of them. MuJoCo was also checked to keep an
actuator's velocity derivative when a force range clamps the force (a pendulum with a
-1000 N m s/rad bias clamped at 0.01 N m fell 5 degrees in 0.5 s instead of 178), which
is why a saturated command carries no slope instead of relying on a force range.

Checks in `tests/test_servo_damping.py` (10): a Torque is a float whose slope survives
only a clamp that does not bind; positive or non-finite slopes are refused; the
controller reports -kd below its limit and nothing at it; the actuator delivers exactly
the command at the speed it was computed for and leaves no slope behind; a nudged arm
settles back; the mobile manipulator stands within 0.1 degrees and 2 mm; a saturated
servo carries no slope; a sourced motor's line takes precedence. Cost: arm lab step
164 -> 170 us, mobile manipulator 1215 -> 1156 us (it no longer chatters).

Not claimed: the controller's stiffness and gravity feed-forward are still sampled once
per step, and servo rotor inertia is still not modelled.

## Machine structure and stance — 2026-09-25

See ADR 0015. Module masses sum to MuJoCo's compiled subtree masses to 1e-9 and the
design-pose centre of mass matches MuJoCo's for the arm lab, the mobile platform and
the mobile manipulator. The stance computed from the design before a run against the
simulator after 1.5 s:

| Machine | Predicted rest | Simulated rest |
| --- | --- | --- |
| Mobile manipulator (arm at design pose) | wheels + front caster, 2.84 deg, margin 3.37 cm | 2.8 deg, 3.4 cm |
| Mobile platform | two tread patches, 0.0 deg, margin 0.33 cm ("rocks easily") | rocked onto its front caster, 2.6 deg, 0.7 cm |
| Arm lab | its pedestal, margin 4.9 cm, but anchored | anchored |

During a run the Drive tab's margin follows the arm: raising the manipulator's shoulder
27 degrees and driving took it from 3.4 to 2.1 cm. Checks in `tests/test_structure.py`
(12): hull and signed margin geometry; a cube stands flat and one leaning past its edge
tips over; a rocker settles onto the side its centre of mass is on, at the exact angle
and margin; module roles, parents, keys and full body coverage for the mobile
manipulator, the arm lab and the bare cart; masses and centre of mass against MuJoCo;
the predicted stance against the settled simulation; and a window test opens the
Assembly tab on Modules, reads the header lines, selects the arm module by clicking it
and switches to Parts. Two window tests that waited on the wall clock (1.5 s and 4 s of
driving) now wait on simulated progress: at full frame rate 1.5 s of window time had
become enough for the platform to reach the room's pickup stand. Full display-enabled
suite: **546 passed**.

Not claimed: the stance is static and rigid (no acceleration, joints locked at the
design pose, level rigid floor); roles come from the catalog.

## Arm tasks: tool moves, taught poses, grasp checks — 2026-09-25

See ADR 0016. In the Pick and place field the arm lab runs the template solved for it
(22 ms): the cube is lifted 5 cm at 1.9 s and rests in the tray at 5.7 s, 13 mm from
its centre, judged by the field's goals from body poses; the program completes at
6.5 s. Moving the cube away before the grasp stops the program at the grasp check
("Nothing held") and the field reports the placement missed.

Two field changes came from running it. The tray at (0.30, 0.30) was 0.42 m from the
arm's axis: a level tool 2 cm above its floor was 1.9 cm out of the standard arm's reach
and 0.8 cm even with the tool free to tilt, so no program could have placed the cube
level; it is now at (0.20, 0.30), 0.36 m out and clear of the six-wheel rover's
footprint. And the placement goal first counted the cube as resting in the tray at
5.0 s, while the closed jaws still held it 1 cm above the floor; the zone now ends 32 mm
up, so the goal is met at 5.7 s, after the jaws open.

Checks in `tests/test_arm_tasks.py` (18): pose blocks round-trip, mark their program
version 2 and leave version-1 files unchanged; malformed poses are refused; joints in a
pose move together (every joint the same fraction of the way at any time), arrive
together and fail when they never settle; a grasp check fails on nothing held and on
the wrong object; poses are validated against the design; the tool point is midway
between the pads and its joints are the arm's four; tool steps forward, sideways, down
and diagonal are solved to 0.1 mm with the tool's angle held and reached by the servos
within 4 mm in 1.5 s; a step out of reach changes nothing; a taught pose is the arm's
targets; the template meets both goals; a missed grasp fails it; and a window test uses
Tool mode, teaches a pose, builds the template with its button, runs it and reads the
goals. Full display-enabled suite: **564 passed**.

Not claimed: no path planning or collision avoidance (a straight step into the stand
hits the stand), no orientation about the tool's axis, kit arms only; the template plans
once from the state it is made in.

## Friction that holds — 2026-09-25

See ADR 0017. The arm lab held its 16 g cube still for 10 s with the jaws at their
0.6 N m limit: with MuJoCo's default soft friction the cube slid 18.5 mm out of the
grip, accelerating; with two noslip iterations, 0.14 mm. A box on a 20 degree plane with
friction 0.2 still slides at g (sin a - mu cos a) within 5 %. The ADR 0013 matrix re-run:

| Machine | 5 m sprint | Curbs cleared | Ramps climbed | 4 kg crate past 3 m |
| --- | --- | --- | --- | --- |
| Mobile platform | 11.8 s | 10 mm | 8 deg | no |
| Two-wheel robot | 13.5 s | none | none | 13.8 s |
| Four-wheel rover | 12.4 s | 10, 20, 35 mm | 8, 14, 20 deg | 7.5 s |
| Six-wheel rover | 12.4 s | 10 mm | 8 deg | 7.0 s |
| Delivery cart | 12.5 s | none | none | 9.7 s |

The one change is the platform's 20 mm curb: its casters' 40 mm wheels had crept up an
edge as tall as their radius, which a pushed free wheel cannot climb. The Kinova Gen3's
first joint, frozen by noslip, turned out to be grinding against a 12 mm overlap between
its shoulder and base (present in the Menagerie file) at its 105 N m limit; contacts
between adjacent links of registered robots are now excluded, and it turns with force
to spare. Cost per step: two-wheel robot 198 -> 251 us, arm lab 246 -> 308 us, mobile
platform 1096 -> 1211 us, mobile manipulator 1289 -> 1457 us.

Checks in `tests/test_grip_friction.py` (3): a held cube stays within 1 mm of the grip
for 10 s; sliding above the friction limit is unchanged; adjacent robot links do not
touch and the Kinova's first joint turns below its limit. `tests/test_fields.py` now
holds the curb result as the physics of a pushed wheel.

Not claimed: tangential creep is removed, not normal softness; no separate static
friction coefficient.

## Fetch: driving to a point — 2026-09-25

See ADR 0018. The mobile manipulator, running the Fetch program solved for it from where
it stands, reaches the table at 9.7 s, has the cube lifted at 16.2 s and resting in the
bin at 32.9 s, stays upright, and completes at 33.6 s. Before ADR 0017 the same program
lost the cube on the way back: it crept 2.1 cm out of the jaws in 9 s of driving.
Driving to points (1.5, 0), (0.5, 0.6, 90 deg), (0.8, -0.4, 180 deg), (0, 0, 0 deg) in
turn, the platform came to rest within 0.5 cm and 2 degrees of each, the mobile
manipulator within 2.1 cm and 2 degrees. Two defects in the first versions were found
by running it: the turn on the spot drifted the base out of tolerance and the controller
went back and forth between point and heading (fixed by hysteresis), and the arm as
designed pushed the cube 3.7 cm along the table on the way in (fixed by taking the pose
above it before driving).

Checks in `tests/test_fetch.py` (9): drive ahead, turn first when off the bearing, back
up to a goal close behind, turn round for one far behind; slow down near the goal but
not below 3 cm/s; turn to the heading without chasing the point again unless pushed
away; wheel speeds from forward speed and turn rate; goto blocks as version-2 data, and
the runner failing without a base and ending on arrival; the base pose is the axle
midpoint; a program drives the platform to (1, 0.5, 90 deg); the mobile manipulator
meets all four Fetch goals by itself; and a window test builds the Fetch program with
its button, runs it and sees the base drive off towards the table. Full display-enabled
suite: **576 passed**; headless 541 (35 need a display).

Not claimed: ideal positions (no odometry drift or localisation), no path planning or
obstacle avoidance, plans made once from the state they are made in.

## Factory production run — 2026-09-25

See ADR 0019. Running six small blocks from the input tray and the stock shelf into the
Blue tray: all six placed, in a 3 by 2 grid of slots, none failed, 12.3 s per part and
4.9 parts per minute of simulated time; six tall blocks the same. The first part of a
run takes 13.9 s from the robot's home pose, the rest about 12.3 s from the retract pose.

Checks in `tests/test_factory.py` (4 new): a stocked cell is portable data with a sky
backdrop and its parts come to rest on the shelf; a run of three into the Amber tray puts
each within 2 cm of its slot and on the tray's floor, counts 3 placed and 0 failed at
10-15 s a part, and refuses to start without the input tray's part or while running; a
part taken off the input tray stops the run with "Grasp failed", counted; and a window
test starts a run with its button, sees the first part counted and the second under way,
and resets. Tool moves on registered robots (`tests/test_arm_tasks.py`, 2 new): the
Panda's and UR5e's tool points move 5 cm down in one step and their servos follow within
1.2 cm. Full display-enabled suite: **582 passed**; headless 546 (36 need a display).

Not claimed: the feeder is a teleport; one product type per run; six slots per tray.

## Doorway and tilt table — 2026-09-27

See ADR 0020. The mobile platform's three-stop doorway program completes with all four
goals: through the 50 cm door, parked in the bay, frame untouched (posts within 1 cm and
5 degrees), upright. A four-wheel skid-steer rover turns under 15 degrees in 3 s on concrete
where the platform turns over 90. Predicted tip angles: a box's equal its static stability
factor's to 0.02 degrees; a machine that rocks onto a caster tips past 55 degrees, not at
6. The mobile manipulator: 54.3 degrees to either side (55.8 about the trip rail's edge),
61.4 forward, 50.7 back; on the table it goes over at 54.2 degrees - one caster, loaded
and pushed sideways, swivels 86 degrees as the table rises. The platform (predicted 70.1)
holds to 60. With the rail at the table's edge instead of at its wheels, the manipulator
slid from 16 degrees and flipped over the rail at 30.

Checks in `tests/test_more_fields.py` (9): held and missed goals with the angle it went
over at, and the lean measured against the table; the table's schedule; tip angles of a
box and of a rocking machine; the trip rail set against the machine; the table follows
its schedule under a machine; the manipulator tips within 3 degrees of its rail-corrected
prediction while the platform holds; a skid-steer rover cannot turn on the spot; the
doorway program. `tests/test_fields.py`: fields keep clear of each body of the machine at
the start (a trip rail may sit under a chassis, not in a wheel). Full display-enabled
suite, with the radar's 13: **604 passed**; headless 568 (36 need a display).

Not claimed: side slopes only (ends predicted, not measured); a rigid prediction (casters,
tyres and joint compliance are worth about 2 degrees here); the doorway's stops are given.

## Frontier radar — 2026-09-27

See ADR 0021 and docs/RADAR.md. Parsers checked on invented documents in each feed's shape
and, for MuJoCo's changelog, on the real text from 3.4.0 to 3.14.0: every version's entry
count matches the changelog's own numbering (198 entries, 51 under Breaking API changes).
First run: 302 items, 48 filed under a topic, 23 judged. Trial of MuJoCo 3.14.0 (the
project stays on 3.3.7): the headless suite passes 565 of 568; the three that move all
involve a cylinder wheel in contact - the caster at a 20 mm curb climbs (stops with
multiccd off), the manipulator tips at 52.4 degrees instead of 54.2 (53.0 with multiccd
off), and its measured stance margin reads 2.6 cm instead of 3.4 with the tilt unchanged.

Checks in `tests/test_radar.py` (13), listed in ADR 0021.

Not claimed: the radar ranks and files; it does not read papers or decide. The fetcher has
not been run against the live feeds from the build machine; the first run's items were
gathered through a browsing tool.

## Static tests shown as static tests; radar page; agents' notes — 2026-09-29

See ADR 0020 (A static test looks like one) and ADR 0021 (Short, then complete). On the
tilt table the mobile manipulator still goes over at 54.2 degrees with the table on two
posts and a beam instead of one block; the report reads "Tipped over at 54 deg, predicted
54, 56 at the rail". The Doorway program template, run by the mobile platform: through
the door at 14.5 s, in the bay at 16.7 s, frame untouched, upright.

Checks: `tests/test_radar.py` (14) now also renders the page from a digest holding a title
with a script tag, a `javascript:` link and a note with markup, and finds all three escaped
and no link made; `tests/test_agent_docs.py` (4) keeps the agents' notes present, the
open items a well-formed table with unique numbers, known statuses and who found each,
the reports newest first, and the status script running. Unused imports found by a
linter were removed across the tree (54). Full display-enabled suite: **609 passed**;
headless 573 (36 need a display).

Not claimed: the page's fonts come from Google Fonts and fall back to the system's
offline; the agents' notes are written by agents, not generated.

## Wheel contacts across MuJoCo releases — 2026-10-01

See ADR 0022. The settled mobile manipulator's stance margin, now measured from the shapes
of the geoms that touch the floor: 3.39 cm on MuJoCo 3.3.7 and 3.40 cm on 3.14, predicted
3.37 (from reported contact points it read 3.4 and 2.6). The platform's caster against
curbs alone and after a 10 mm curb, on both releases with multiccd on and off (table in the
record): on 3.3.7 as used, the answer near the 20 mm radius depends on the curb before it
and is not monotonic in height. The tilt table across all twelve releases from 3.4 to
3.14: the steps from 54.2 to 52.4 degrees match the box-box collider changes (the tread
blocks are boxes) and cylinder multicontact (the caster), each named in the record.

Checks in `tests/test_fields.py`: the caster climbs 18 mm and not 24 mm, alone; whether a
curb is climbed does not depend on the curb before it (expected to fail before MuJoCo 3.8,
and recorded so). `tests/test_more_fields.py`: the manipulator tips within 4 degrees of its
rail-corrected prediction. On MuJoCo 3.3.7: **609 passed** with a display, 573 headless,
and 1 expected failure; on 3.14 the headless suite: **574 passed**.

Not claimed: which release is right near the caster's radius; that needs a real caster and
curb.

## Machines start on the floor — 2026-10-01

See ADR 0023. The mobile platform and the arm on a cart started with their wheels 4.35 cm
above the floor and fell 44 mm as each run began; the two-wheel example fell 10.5 mm and the
bare block started 8.5 cm up. Set down after assembly, the examples settle 2.5 to 2.9 mm as a
run starts. With the platform started on its wheels, the caster gives the same answers alone
and after a 10 mm curb on MuJoCo 3.3.7 and 3.14, with multiccd on and off: 18 mm climbed
everywhere, 20 and 22 mm only on 3.14 as released, 24 mm nowhere. The fall had left a caster
swivelled 6 degrees at the lone curb and 37 degrees at the curb after the 10 mm one. The
manipulator's stance margin: 3.34 cm on 3.3.7 and 3.35 on 3.14, predicted 3.37. On the tilt
table: 54.5 degrees on 3.3.7 and 52.6 on 3.14, predicted 54.3 (55.8 at the rail); the loaded
caster still swivels 86 degrees before it goes.

Checks: `tests/test_structure.py` - the four examples start within 5 mm of the floor, the
platform lifted 4 cm reads 4 cm higher, an arm bolted to its pedestal has nothing standing
free; the platform and the manipulator settle less than 3 mm as a run starts.
`tests/test_fields.py` - whether a curb is climbed does not depend on the curb before it, no
longer marked as expected to fail. On MuJoCo 3.3.7: **613 passed** with a display, 577
headless; on 3.14 the headless suite: 577 passed.

Not claimed: a run does not set a design down; one built in the air still falls, and the
build stage says so. Designs saved before this change keep their heights.

## Runs under variation — 2026-10-01

See ADR 0024. Twenty runs per sweep: as designed; set down 2 cm ahead, behind, left and
right; turned 3 degrees each way; carrying 0.5 kg at its site and 5 cm either side; friction
at the low and high end of every sourced pair; eight seeded random repeats. Tilt table, the
arm on a cart: over between 51.4 and 58.4 degrees (54.5 as designed); set down off its mark,
no change (the rail is set against its wheels); friction -0.5 to +0.2; turned 3 degrees +0.4
and -3.1 against a predicted +1.7 and -1.6 - traced to the machine turning as the table
rises (set down straight it settles 1.7 degrees off; set down 3 degrees right it settles at
-0.5 with one tread block against the rail and swings about it near 48 degrees); carrying
0.5 kg +1.8 to +4.0, each within 0.3 degrees of its prediction. Fetch, the program solved once for the design on its mark: every
goal met in all 20 runs, the cube in the bin at 31.9 to 33.6 s; with 0.5 kg on the deck
behind the arm the cart rides on its rear caster, the jaws meet the cube 28 mm from their
aim, and the cart rocks 5 degrees forward as the arm lifts, leaving the cube 12 mm short of
the 5 cm line until it rocks back (lifted at 23.7 s instead of 16.2).

Checks in `tests/test_variation.py` (14): the plan (as designed, each change alone, seeded
repeats, inside its ranges); refusals; moving and turning a design about its mark; the
payload as a steel block on its carrier, its default site clear of moving parts; every
friction spread holding the value used, each cited end the value used or a number its note
quotes; the backend's friction condition and its reset; the simulator weighing the payload;
a sweep, its report and its JSON; the headline, the quantity drawn as ticks and what moved it most; the tilt table
following the prediction with a payload aboard; stopping a sweep stopping its worker
processes; and, with a display, the run report starting a sweep in another process and
copying its report. On MuJoCo 3.3.7: **626 passed** with a display, 589 headless; on 3.14
the headless suite: 589 passed.

Not claimed: the placement and payload ranges are assumptions, stated; eight random repeats
are a sample, not a distribution; the field, the motors' unit-to-unit spread and sensing
are not varied.

## Poses aimed at a point — 2026-10-02

See ADR 0025. The Fetch program's poses taken at its stops carry the point their tool was
aimed at; the runner checks where the tool got to and solves the pose again when it is more
than 5 mm off. As designed, each settled 10 to 12 mm off its point (the base stopped 1.0 cm
short of its mark at the table, 0.9 cm off at the bin) and one correction brought the tool
within 1 to 3 mm; the cube is in the bin at 34.0 s (32.5 before). With 0.5 kg behind the
arm: the jaws meet the cube within 3.3 mm (28 before), the lift leaves it 11.5 mm over the
5 cm line, lifted at 18.2 s (23.7 before). Over ADR 0024's 20 variations: every goal in
every run, lifted at 16.4 to 18.2 s (15.9 to 23.7 before), in the bin at 33.3 to 35.5 s
(the reports are in `docs/sweeps/`).

Checks in `tests/test_aimed_poses.py` (6): an aimed pose as data and its validation; the
runner checking, correcting and stopping after two corrections; a correction that cannot
settle not failing the program; a pose without a point, or a runner without an aim,
unchanged; the arm aiming a pose from where its machine stands; the loaded cart lifting the
cube clear. On MuJoCo 3.3.7: **632 passed** with a display, 595 headless; on 3.14 the
headless suite: 595 passed.

Not claimed: sensing is ideal (the simulator's own tool and base poses); a pose is checked
once it settles, not tracked while it moves.

## Radar: the robot models the app imports — 2026-10-02

OPEN LW-013. The radar profile adds MuJoCo Menagerie and the four registered arms (Panda,
FR3, Gen3, UR5e) to ADR 0019, whose tool moves they use. Checked in `tests/test_radar.py`
(15): the Menagerie repository and a model update both file under ADR 0019 with "menagerie"
among the words that matched. Suites: **633 passed** with a display, 596 headless; on 3.14
the headless suite: 596 passed. With the variations panel's ticks (one more check): **634
passed** with a display, 597 headless; 3.14 headless 597.

## Frontier brief and proposals — 2026-10-02

ADR 0026. The radar reads three journals' tables of contents (Science Robotics, IEEE
Robotics and Automation Letters, IEEE Transactions on Robotics) and writes a brief into
`docs/agents/FRONTIER.md`, where agents write numbered proposals for the owner to accept or
decline; `scripts/agent_status.py` lists those waiting. First brief: 302 items read, 51
filed, 23 judged; 14 proposals, every adopt and learn verdict cited by one. Checks:
`tests/test_radar.py` (21, six new) - both journal feed shapes (DOIs from elements and from
addresses without their query, markup dropped, an item without a link skipped), the
journals among the sources, proposals read with their status, citations by whole id and by
a link no other item shares, the brief's order, inert feed text and waiting list, writing
only between the markers, the command line end to end; `tests/test_agent_docs.py` (6, two
new) - every proposal has its six fields in order and a known status, a done one names its
decision record, and the status script lists the proposals that wait on the owner. On
MuJoCo 3.3.7: **642 passed** with a display, 605 headless.

Not claimed: the journal feeds were not reached from this workspace (IEEE Xplore answered
418, Science 403); the brief reads no papers; a proposal is an agent's reading of its
sources and says so where only a title was seen.

## MuJoCo 3.10.0, one contact per convex pair — 2026-10-02

ADR 0027 (FR-002, the owner's choice: 3.10.0 is the newest MuJoCo with wheels for an Intel
Mac). Run as released, 3.10.0 moved one check: the test cart's coast-down slowed 5.0 %
faster than its closed form, because multiccd (on by default since 3.8) gave each
cylinder wheel four contacts on the box floor and the solver loaded the leading ones more:
a rolling loss of the engine's own (+1.4 %, +5.0 %, +6.3 % at 0.4, 0.8 and 1.6 m/s). The
adapter turns multiccd off; the coast-down then equals 3.3.7's at all three speeds.
Nominal runs against 3.3.7: tilt table 54.48 to 53.99 deg (predicted 55.75 about the rail);
settled stance 2.89 deg and 3.36 cm (predicted 2.84 and 3.37); Fetch at the table 9.58 s,
lifted 16.37 s, in the bin 33.04 s (9.65, 16.68, 33.97); curbs and sprint unchanged. Checked
in `tests/test_drivetrain.py` (one new): each wheel of the cart meets the floor at one
contact and the flag is set. On MuJoCo 3.10.0: **643 passed** with a display (484 s; 507 s
on 3.3.7), 606 headless (411 s; 442 s on 3.3.7).

Not claimed: the suites ran on Linux with Python 3.11, not on the owner's Mac; one contact
per convex pair is this project's choice for its sourced rolling loss, not a finding that
MuJoCo's multiple contacts are wrong in general.

## How sure: rates from the runs drawn at random — 2026-10-03

ADR 0028 (FR-003, accepted by the owner). A sweep's rates come from its random repeats only;
its chosen runs - as designed, each variation alone at either end - are reported as corner
checks. Exact one-sided 95 % bounds (Clopper-Pearson, standard library; equal to SciPy's
beta quantiles within 1e-14 for every count up to 60 runs). Fetch on MuJoCo 3.10.0: every
goal in all 20 runs; 8 of 8 drawn, so at least 69 % of set-ups within the ranges would meet
every goal; failures below 5 % would take 59 drawn runs without one - and run with 59 drawn
set-ups, Fetch met every goal in all 59: it fails in under 5 % of them, with 95 %
confidence. A static test reports
its drawn span instead: tip angles 54.4 to 58.0 deg over 8 drawn runs, where another lands
7 times in 9. Checked in `tests/test_confidence.py` (9). Suites: 615 headless when committed; with a
display, run with ADR 0030 below.

Not claimed: the rate is over set-ups drawn uniformly within ranges that are assumptions
(FR-009); one seed draws them.

## The tilt test squares the machine — 2026-10-03

ADR 0029 (OPEN LW-017; the owner chose to align the machine with the rail). The tilt
table turns the machine in place to face along its hinge line before setting the rail;
its sweeps no longer turn the machine (18 runs). Arm on a cart, MuJoCo 3.10.0: tips over
between 54.0 and 58.5 deg, -1.8 to +0.7 deg from each run's prediction (the turned run had
been 2.8 deg off); set down turned 3 deg either way, it tips at 53.98 and 54.00 deg (as
designed 53.99). Checked in `tests/test_more_fields.py` (one new). Suites: 616 headless when committed; with a
display, run with ADR 0030 below.

Not claimed: what a turned machine does against a rail is no longer measured by this field
(ADR 0024 keeps it).

## Disturbances during a run — 2026-10-03

ADR 0030 (FR-006, accepted by the owner). A push on the machine's base or a loose part
moved, timed from a goal being met and the machine standing still; `sweep --disturb` runs
the design and the 8 set-ups its sweep draws, undisturbed and under each disturbance. Fetch,
arm on a cart: shoved 4 N s at the table (1.7 cm median), every goal in 9 of 9 set-ups (8 of
9 with poses as taught); 6 N s (6.4 cm), 3 of 9 (none as taught); the cube moved 3 cm, 7 of 9
(6 of 9); 5 cm, none. Sprint, mobile platform: shoved 4 N s, 9 of 9; 8 N s, 2 of 9. Found and
fixed on the way: the grasp check counted a table fixed to the world as held. Checked in
`tests/test_disturbance.py` (7). Suites on MuJoCo 3.10.0: **660 passed** with a display, 623 headless.

Not claimed: a push is a force on the base's centre of mass for 0.1 s, always to its left,
sized to span recovery rather than measured; nine set-ups give wide bounds; no slippery
patch (LW-018).

## Going back to the stop — 2026-10-03

ADR 0031 (OPEN LW-019; the owner chose going back). An aimed pose that settles, or cannot
settle, more than 2 cm from the stop its program drove to sends the program back - the pose
it drove in, a 25 cm run-up behind the stop along its heading, the stop - once per run.
Fetch, arm on a cart, nine set-ups: shoved 6 N s at the table (6.3 cm), every goal in 8 of 9
(3 of 9 with corrections alone); shoved 4 N s (1.7 cm), 8 of 9 (9 of 9); undisturbed, 9 of 9
and nothing went back; drawn 59 times undisturbed, every goal in all 59 with the same times
as before. The set-ups lost had their cube knocked over by the shove.
Checked in `tests/test_going_back.py` (4). Suites: 627 headless when committed; with a
display, run with the next section.

Not claimed: the base's pose is the simulator's; one retry per run; the 2 cm threshold and
the 25 cm run-up are chosen, and nine set-ups do not settle the threshold.

## Disturbances from the run report — 2026-10-03

OPEN LW-018, the owner's choice of a button: "Repeat with disturbances" in a run's report
runs `sweep --disturb` in another process, as variations run, and lists each disturbance with
the set-ups that met every goal and how much later; its report copies as Markdown. A
disturbance sweep reads back from its JSON. Checked in `tests/test_disturbance.py` (two
new: the read-back, and the window test that drives the button). Suites on MuJoCo 3.10.0:
**666 passed** with a display, 628 headless.

Not claimed: the slippery floor patch is not built (LW-018 stays open for it).


## A camera at the table — 2026-10-04

ADR 0032 (FR-011, accepted by the owner). The Fetch table has a depth camera on a stand beyond
it - an Intel RealSense D435: depth over 87 x 58 deg at 848 x 480, nothing nearer than
16.8 cm, depth noise z^2 x 0.08 px / (f x 50 mm), from Intel's documents and Keselman et al.
(2017) - whose pictures are MuJoCo's rays from it, with no GL context. A program's `look`
block finds a known box in them classically - support plane, clusters, the top face laid
back along its rays - and the poses at that stop aim where it was seen. Measured: the cube at
80 placements, up to 8 cm off its plan and turned up to 45 deg, found in every picture: within
1.9 mm and 2.4 deg without noise, 2.4 mm and 6.0 deg with the D435's (median 1.3 mm and
0.6 deg; 9 of 1600 pictures over 5 deg). Fetch, arm on a cart, nine set-ups, looking: the
cube moved 5 cm as the cart stands at the table, 9 of 9 (none blind, run the same day as ADR
0031 measured it); 3 cm, 9 of 9 (7 of 9); shoved 4 and 6 N s, 9 of 9 each (8 of 9 each); moved
5 cm 2 s later, none (none);
undisturbed 9 of 9, the cube in the bin 2.5 s later than blind. Set down elsewhere before the
run: 13 of 14 placements fetched looking, 6 of 14 blind. Drawn 59 times undisturbed, looking:
every goal in all 59 (at least 95 %), 2.5 s later than blind. Every sighting within 2.0 mm of
where the cube really was. Checked in `tests/test_perception.py` (7) and `tests/test_look.py`
(9, one with a display). Suites on MuJoCo 3.10.0: 682 passed with a display, 643 headless.

Not claimed: the camera's pose is known exactly; its noise is the stereo error alone - no
holes, flying pixels or projected pattern; one look per stop, so a part moved after it is
missed; the four-joint arm does not use the cube's turn; the program still stops where the
cube was planned; the one-second watch and ten pictures a second are chosen.

## Looking again — 2026-10-04

ADR 0033 (FR-015, accepted by the owner). At a stop where the program looked, it looks again -
back to the pose it drove in, the look, the reach - when one more picture just before the jaws
go down finds the object more than 1 cm from where the look saw it or hidden, when a reach for
it cannot settle, or when a grasp holds nothing (the jaws opened first); once per run.
Measured: as first built, after a missed grasp only, it reached 1 of 9 set-ups of the cube
moved 5 cm 2 s after the cart stopped. With the picture before the jaws go down: 9 of 9
(none before), the jaws never touching the moved cube, 2.6 s later than undisturbed. Under
the other disturbances and undisturbed, 9 of 9 each with the same median times and pushes as
ADR 0032. Checked in `tests/test_look_again.py` (5). Suites on MuJoCo 3.10.0: **687 passed**
with a display, 648 headless.

Not claimed: once per run; the check before the jaws go down is a single picture; a cube
moved while the jaws are already going down may be knocked, and one beyond the arm's reach
from its stop is not fetched (FR-016); the 2 cm and 1 cm thresholds are chosen.

## The radar keeps what it read — 2026-10-05

ADR 0034. What the radar files or an agent judges is kept in `docs/radar/collection.jsonl`:
81 entries to start (the 30 named in the first run's digests, 18 of them judged; the 51 the
first weekly reading judged), 69 judged - 7 adopt, 18 learn, 35 watch, 9 skip - and 43 read
by title only. Checked: a line round-trips; two sightings of one paper merge into one entry
(the longer summary, sources and topics joined, the earliest sighting, the newest verdict);
a malformed line is refused by its number; no journal abstract is kept and a long summary is
cut; `collect` keeps filed and judged items and files hand-gathered ones; `recall` restores
verdicts into a fresh store, once. Search by words over the collection: on 20 questions
written down before the first search, an answer in the top three for 17 (mean reciprocal rank
0.794); with a latent-semantic cosine mixed in half and half, 18 (0.823) at this commit and
between 15 and 19 as its settings and the project's writing changed, so words rank by
default. A latent space with as many directions as its text has subjects finds an entry
that shares no word with the question. Checked in `tests/test_radar_collection.py` (11).
Suites on MuJoCo 3.10.0: **700 passed** with a display, 661 headless.

Not claimed: the collection is what agents read, not what was published, and a verdict is an
agent's reading; the first run's other 272 items are not recovered; latent semantic analysis
is not an embedding model, and no embedding model was tried; MuJoCo changes taken from the
digests carry hand-written ids.


## Panda visual position teaching — 2026-10-01

Added portable named-position round-trip/validation tests, scratch-preview checks
that preserve live qpos/ctrl, unreachable-target rejection, physical servo arrival,
and native UI coverage for drag, save/recall, robot restrictions and minimum-size
layout. The interface was visually checked in `docs/media/panda-teaching.png`.

The full native suite produced **466 passed, 2 failed**: an existing builder test
exceeded its 10-second deadline and a synthetic spatial-drag test received desktop
cursor/focus events. The builder test passed on isolated rerun. The drag test now
isolates its scripted input from real cursor/focus callbacks; it and all three new
teaching tests passed together (**4 passed**). Thus every test passed across these
runs, but there was no single all-green full-suite run after the test isolation fix.
Teaching verifies a downward Panda endpoint within 12 mm, not collision-free paths,
other robot models, arbitrary tool orientation or multi-action task sequences.

## Shared cell change proposals — 2026-10-02

Default suite: **443 passed, 31 skipped** (`.venv/bin/python -m pytest -q`).
Explicit native checks: **9 passed**, covering cell proposal contracts/review,
physical factory execution, direct tray/task authoring, guided operation, and Panda
teaching. The shared-window/robot-switch test also passed in the earlier focused
run (**7 passed** including proposal tests). Contract checks cover strict wire
fields/units, exact before/after values, atomic multi-tray swaps, invalid batches,
stale manual edits/undo revisions, no-op requests and preservation on rebuild
failure. Export refuses to overwrite files; import prepares review without applying.
The final review was visually inspected in `docs/media/cell-change-review.png`.
This validates the existing fixed cell's structured edit boundary, not an AI
provider, language understanding, arbitrary factories or motion planning.

## Semantic agent testing and hidden native windows — 2026-10-03

Final full native suite: **674 passed in 154.37 seconds**, using
`LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest -q`.
All native windows were hidden. Tests use synthetic cursor coordinates and no
presentation synchronization; regular application launches retain visible windows
and normal synchronization. This removes desktop typing/focus interference and
avoids moving the user's pointer.

Added 195 adversarial cases, including 1,200 seeded valid transactions and 80
invalid batches, plus semantic scenario and harness-failure checks. Extreme integer
coordinates exposed an uncaught OverflowError; they now produce a controlled
validation rejection. Three agent-authored scenarios use real UI callbacks and
form character handling to exercise review/apply/undo/redo, stale/ambiguous/invalid
requests, physical placement with independently bounded product coordinates, and
Panda teaching save/recall. A deliberately wrong expectation correctly fails and
halts the remaining actions. Snapshots explicitly verify window_visible=false.

Earlier visible-window testing passed 673 tests but received real keyboard input
in a search test. Initial hidden-window testing exposed OS-cursor assumptions and
presentation timing in existing tests. The final synthetic-cursor fixture and
hidden no-vsync execution resolved those test-environment issues; all 674 tests
passed together after these changes. See AGENT_TESTING.md for replay commands,
JSON traces and the distinction between semantic tests, visual QA and future
language-model evaluation. No AI provider or natural-language parser was tested.

## Shared factory scene document — 2026-10-04

Default regression suite: **657 passed, 35 skipped in 44.50 seconds**. Focused
document suite: **18 passed**, including native compilation and a subprocess
example that imports a saved custom machine, creates two instances, exports JSON
and refuses to overwrite an existing file. No window was opened. Contract tests
cover stable references, shared-asset impact, linked deletion, revision conflicts,
undo/redo, portable proposal round trips, strict fields/units/poses, canonical order
and detached diff reports. Simulation steps leave authored document data unchanged.

The standalone example compiled a 67-body scene. This verifies the portable
document and existing native backend composition, not station UI integration,
collision clearance, reach, production flow execution or natural-language generation.


## Interactive factory layout — 2026-10-04

Added a same-window layout integration test and a fourth semantic replay (26
actions). Coverage includes actual MuJoCo geometry picking, render-only drag
preview, one-edit release, stale drag/deletion rejection, exact poses, independent
builder copies, asset-ID collisions, linked deletion, undo/redo, save round trips,
failed compilation rollback and preservation across Real/Anime switching. The test
asserts that only one native window is created and that controls do not overlap at
1040 × 740. A hidden screenshot was inspected for readability and selection cues.

The first complete run had 694 passes and one existing workshop test timeout: only
37 of its required 47 frames completed within ten seconds. Its timeout was extended
to 60 seconds; it still closes immediately after all scripted interactions and
retains its original behavior assertions. No visible app windows were opened.

Final full regression: `LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest -q`
— **695 passed in 112.44 seconds**. These checks verify layout editing and existing
robot workflows, not process execution, reach/clearance checks or AI comprehension.

## Two lines of work merged — 2026-10-07

Codex's line (the Mac's `main`: Panda teaching, reviewable cell changes, semantic testing with
hidden windows, the factory scene document and layout editing, its shared event log) merged
into `contact-pair-friction`, which holds everything above from 2026-09-24 on. The shared log
keeps Codex's reader and writer (`tests/test_agent_status.py`, 10) with the status summary as
the default (`tests/test_agent_docs.py`, 8). Suites on MuJoCo 3.10.0 after the merge: **940
passed** with a display, 893 headless. Not claimed: the two lines' features were tested side
by side in one suite, not together in one scenario.

## The stop follows the cube — 2026-10-07

ADR 0035 (FR-016, accepted by the owner). The Fetch program looks before it drives - the
table camera searching 25 cm round the plan - and its stop at the cube, and the stop it backs
off to, move as the cube was seen to have moved: sideways fully, towards the table at most
2.3 cm, so the cart's front stays 1 cm clear of the table's edge (measured from MuJoCo's
geometry: 3.3 cm at the planned stop). Measured, the cube set down before the run: ADR 0032's
14 placements, all 14 fetched (13 before); 6 and 7 cm further along the table, fetched (6 cm
was missed); 15 cm to either side and 6 cm along with 15 cm to the side, fetched; 8 and 10 cm
along, refused at the table with "out of the arm's reach from this stop", said before the arm
moves - the arm reaches 28 cm ahead of its axle at the cube's height. Blind, 6 of the 19.
Undisturbed, drawn 59 times: every goal in all 71 runs, the cube in the bin after 35.9 s
median (35.8 s before); one run looked again though nothing had moved (OPEN LW-022).
Disturbed on the same 9 set-ups: every disturbance 9 of 9, the median changes within 0.6 s
of ADR 0033's. Checked in `tests/test_stop_follows.py` (13), with `test_look.py`,
`test_look_again.py` and `test_aimed_poses.py` updated. Suites on MuJoCo 3.10.0: **953 passed** with a display, 906 headless.

Not claimed: the stop moves without turning; a cube out of reach from every stop clear of the
table is refused, not approached from another side; the clearance counts parts fixed to the
world, from box corners, with the cart as it stood when the program was solved; the 25 cm
search and the 1 cm margin are chosen.

## Radar: one phrase, one piece of evidence — 2026-10-07

ADR 0021 files an item only on two separate pieces of evidence, a word pair standing for its
words, so that "language models" alone puts no protein paper under robot programming. The
pair stood for its words only while it weighed more than they did, and the weights move
whenever a document joins the texts: found while writing ADR 0036 - with it among the
decision records, "language" outweighed "language model" and the test's protein paper was
filed under "Learn: language models that program robots" on "language" and "models". Now a
word inside a shared pair never counts apart from it, whatever the weights, and a match shows
the pair ("contact creep", "mujoco menagerie") where it showed one of its words. Search
scores are unchanged (`search --check`: 17 of 20 in the top three, words alone). Checked in
`tests/test_radar.py` (one new test; two now expect the pair).

## Paired runs — 2026-10-07

ADR 0036 (FR-017, accepted by the owner). A set-up's undisturbed and disturbed runs are one
run until the event, checked bit for bit - a digest of every joint's position and speed at
every step - on the Sprint field (shoved 4 N s) and the Fetch field (the cube moved 2 s after
the look): equal up to the event, different from it on. Each drawn set-up is then counted as
a pair. Without looking again (ADR 0033 off), the cube moved 5 cm after the look broke 8 of
8 drawn set-ups that succeeded undisturbed - at least 69 % of successes, exact McNemar p =
0.0078 - where the two rates alone said 8 of 8 against 0 of 8. With it, on 59 drawn set-ups:
1 of 59 broken (0 to 9 % of successes), none rescued, p = 1 - no effect shown; the cube in
the bin 3.1 s later (median). The broken one, traced: the cube moved 26 ms after the picture
before the jaws went down, a jaw came down on it, and the arm, rising off it to look again,
dragged it over the table's edge (OPEN LW-023). Undisturbed, 59 of 59; two of the 60 looked
again though nothing had moved (LW-022). Checked in `tests/test_paired_runs.py` (6): the exact
test's values, the pairing with the as-designed set-up left out, a disturbance that breaks
nothing, a rescue, and the two runs of a pair equal step for step until the event on the
Sprint and Fetch fields; `tests/test_disturbance.py`'s report row has the new column.
Suites on MuJoCo 3.10.0: **960 passed** with a display, 913 headless.

Not claimed: pairs are exact on one machine and MuJoCo build; the test is about outcomes, not
times; the as-designed set-up is chosen and stays out of the count.


## Rise first, read the place — 2026-10-08

ADR 0037 (OPEN LW-022 and LW-023, the owner's pick). A reach for the cube that is stopped, and a
grasp that holds nothing, first rise back to the pose the arm reached down from, then go back
to look again; a picture before the jaws go down that finds nothing asks what the picture shows
where the cube was seen - its surface, something nearer over it, or the table beyond it - and
only an empty place looks again. On ADR 0036's paired sweep again (59 drawn set-ups and the
design as designed, the cube moved 5 cm sideways 2 s after the look): broken 0 of 59, at most 5
% (1 of 59 before); every goal met in 60 of 60 (59); the cube in the bin 3.1 s later than
undisturbed, median, as before. Set-up by set-up against the previous version: eleven moved
set-ups had their reach stopped on the cube, which moved just after the picture before the
jaws went down - repeat 9 is now fetched instead of dragged over the table's edge, the other
ten finish 0.35 to 0.6 s sooner in nine and 0.3 s later in one; the other 49 met their last goal
at the same time. Undisturbed, none looked again for nothing (2 before; repeats 35 and 43 now
4.1 s sooner) and the other 58 met their last goal at the same time. In repeat 35's picture, 148
of the 170 rays that would meet the cube ended on its surface and 22 on the jaws in front of it;
with the cube moved 5 cm, 159 passed where it had been. Every disturbance on the nine set-ups
of ADR 0030: 9 of 9 each, the median changes as ADR 0035's. The cube set down before the run:
17 of 19 fetched looking and 6 blind, as before, within 0.1 s. Checked in
`tests/test_rise_and_place.py` (10). Suites on MuJoCo 3.10.0: **970 passed** with a display,
923 headless.

Not claimed: the place is read for a part standing as its size says, square to the field; hidden
is taken for there, so a part moved under the jaws' cover is found by the grasp, not before;
rising retraces the reach in the joints, not in space; a reach pushed off its stop still goes
straight back to it.

## A camera that can fail — 2026-10-08

ADR 0038 (FR-018, accepted by the owner). A disturbance can freeze the field's camera on its
last frame or make it dark; each picture carries a frame number, when it was taken and the share
of it with depth, and three pictures in a row that are not new, or are dark, end a look with the
camera named and nothing moved. Fetch, the nine set-ups of ADR 0030: frozen as the cube is moved
5 cm, taken on trust (`--unchecked-camera`), 0 of 9 - in every set-up the jaws went down twice
where the frozen picture showed the cube, ending "Timed out: pose did not settle" (5) or
"Nothing held: the grasp missed" (4); checked, 0 of 9, every one "Looked for fetch_cube: the
camera's picture is not new", nothing grasped. Dark at the table: on trust "it would not keep
still" after 5 s; checked, "the camera's picture has no depth", 0.3 s after it went dark. The
other six rows (none and five disturbances): all 54 runs met their last goal at the same time as
before. Frozen, on 59 drawn set-ups: all 59 stopped at the look, named; the 60 undisturbed runs
at the same time as before to the millisecond - no false alarm. A p too small for four places
now reads "p < 0.0001". Checked in `tests/test_camera_faults.py` (10) and
`tests/test_paired_runs.py` (one more). Suites on MuJoCo 3.10.0: **981 passed** with a
display, 934 headless.

Not claimed: a picture's number and its depth are checked, not what it shows - a stream that
numbers a stuck picture afresh, or a camera knocked off its mount, passes; a frame frozen within
one picture interval of its first use is used once; dark means less than half of the picture
with depth.

## How well the camera must be mounted — 2026-10-08

ADR 0039 (FR-021, accepted by the owner). The table camera is set off its believed pose in
MuJoCo (`MujocoBackend.move_camera`) while the program reads its pictures as if it stood where
believed (`Eye(believed=...)`, `sweep --camera-error`). Closed form (`perception.calibration`):
a shift d makes the cube seen -d away; a degree of pan 15.3 mm sideways, of tilt 13.1 mm along
the table and 7.8 mm down, of roll 0.3 mm. As designed, 67 single errors: the cube seen within
2.5 mm of the closed form; the jaws' margins from shifting the camera - 10.5 mm too far along
(14.8 drops the cube on the way), 25 mm sideways (30 fails), 10.3 mm too low (12.8 fails), at
least 38 mm towards the cart and 29 mm too high; pan held at 1.75 degrees and failed at 2, tilt
up held at 0.75 and failed at 1 - where the closed form and the margins put them; tilt down held
at 3. On 59 drawn set-ups each (predictions written before): panned 1.5 degrees, tilted up 0.5,
raised 10 mm - 59 of 59, at least 95 %; 10 mm towards the cart, 58 of 59; tilted up 1 degree, 8
of 59. Two combined errors were seen within 2.4 mm of the closed form; one near two margins at
once missed. Checked in `tests/test_camera_error.py` (4). Suites on MuJoCo 3.10.0: **985 passed** with a
display, 938 headless.

Not claimed: one camera, one field and one gripper; errors certified one at a time; the program
does not notice its own calibration error.

## How gently — 2026-10-09

ADR 0040 (FR-020, accepted by the owner). Each run now follows the parts the field's goals
carry: for the machine, the table and the bin, the hardest push on the part from any one of
their bodies (so a squeeze counts), in a step and over 50 ms; its largest lean; how far it fell
when let go (`MujocoBackend.contact_forces`, `inventory/handling.py`, `Run.handled`). The
instrument: the resting cube's support adds up to its weight to 0.01 %. Halving the step moved
forces in a step by up to 12 % and over 50 ms by up to 4 %; the lean and the fall moved more.
Over 59 drawn Fetch set-ups, every goal met: squeezed at 4.8 N over 50 ms (3.7 to 6.7), let go
5.8 cm above the bin's floor (3.1 to 7.0), landing at 1.9 N in a step and leaning 9 degrees
(medians); in 4 of the 59 the cube was pressed into the table (0.6 to 2.0 N over 50 ms) and in 2
it leaned past 20 degrees (OPEN LW-024, LW-025). The cube moved 5 cm at the table: blind, pressed
into the table at 5.1 N (32 times its weight); looking, the table only ever carried it.
Checked in `tests/test_handling.py` (5). Suites on MuJoCo 3.10.0: **990 passed** with a display,
943 headless.

Not claimed: what the part can bear (no fragility sourced; the kit gripper's rating is not
published); forces are MuJoCo's soft contacts.

## The cart on all four — 2026-10-14

ADR 0041 (LW-025; the owner's decision of 13 October). The kit cart's swivel casters are set
from the parts' geometry to reach the floor its drive wheels stand on, 6.5 mm lower than before:
it stands on all four instead of teetering on its drive wheels between them. Predicted and
settled: the mobile manipulator rests on all four, level, its centre of mass 9.0 cm inside
(was the front caster, 2.84 degrees, 3.37 cm); the bare cart 9.4 cm (was 0.33 cm, "rocks
easily"). Through a Fetch run it pitches within 0.2 degrees (was -4.0 to +3.0); the drive wheels
carry 15 % less. The five set-ups that pressed the cube into the table, the program unchanged:
the table carries only the cube's weight, the cube leans at most 6 degrees (was up to 101).
Over 59 drawn Fetch set-ups and the twelve chosen, every goal met in all 71 and none pressed the cube
into the table (0 of 59, at most 6 %; 4 of 59 before), the table pushing back at 0.18 N over 50 ms
(0.17 to 0.23), the cube leaning 3.1 degrees (1.2 to 8.8); let go 6.8 cm over the bin's floor
(5.8 before). Every cart field as designed: sprint 11.9 s (11.8); the curbs it clears are the
same, but it stalls at one until it has slewed onto a drive wheel - an 18 mm curb at 11.6 s
(4.1); doorway 14.4 s (14.2); the tilt table tips it at 54.6 degrees (54.0); Fetch in the bin
at 36.2 s, as before. Shoved 6 N s at the table, the shove now comes as the jaws reach down:
blind, a jaw knocks the cube over; looking, the program goes back and fetches it upright.
The tilt table, varied: 53.3 to 59.4 degrees (54.0 to 58.5), within -2.3 to +1.0 of each
prediction. Shoved in the sprint lane: 4 N s 9 of 9, 8 N s 3 of 9 (2), pushed further (89 cm
against 79). Fetch under every disturbance: the same set-ups fetched, the cube leaning at most 9
degrees (17). Checked in `tests/test_structure.py`, `tests/test_fields.py` (a new test: on all
four, 18 mm in 11.6 s against 4.1 rocking), `tests/test_disturbance.py`, `tests/test_camera_faults.py`
and `tests/test_rise_and_place.py`. Suites on MuJoCo 3.10.0: 991 passed with a display, 944 headless.

Not claimed: uneven floors (four rigid points on one leave a wheel or a caster in the air), a
sprung caster or a rocker; the cube is still let go over the bin (OPEN LW-024).

## Set down, not dropped — 2026-10-20

ADR 0042 (LW-024; the owner's choice of 13 October). The Fetch program's jaws close on the
cube's upper half (18.3 mm higher, their lower edge at its middle), squeeze 0.6 degrees more
once it is felt held, and over the bin tilt down by whatever angle lowers it most - 25 degrees
for the kit cart, its lowest corner planned 2.5 mm over the floor, the jaws 10.8 mm. Over 59
drawn set-ups and the twelve chosen, every goal met in all 71: the cube fell 0.3 cm when let go
(0.1 to 1.1; 6.8 cm before), the bin pushed back at 0.52 N in a step (2.14) and 0.26 N over 50
ms (0.57), the squeeze 3.9 N over 50 ms (5.0), the table 0.18 N as before; it leaned 0.0 degrees
before it was held and at rest; in the bin at 37.3 s (36.8). Without the squeeze, 3 of 71 were
not set down so: one crept out of the jaws and fell 3.9 cm, two were pressed onto the floor
while held. A fall is now the most a part fell after the machine let go, before it touched it
again (ADR 0040's measure missed a fall the jaws then pressed). Under every disturbance the same
set-ups fetched as on the cart's sweep, each cube set down; with the cube moved 5 cm 2 s after
the look, a jaw now comes down on it and presses it into the table at 3.3 N over 50 ms for about
2 s before the reach is stopped (OPEN LW-029). Checked in `tests/test_set_down.py` (5),
`tests/test_handling.py` (7) and `tests/test_disturbance.py`. Suites on MuJoCo 3.10.0: 998
passed with a display, 951 headless.

Not claimed: touch - the height comes from the plan, so a floor not where the field says is met
harder or missed; the cube is let go 3 to 6 mm higher than planned (OPEN LW-028); what is set
down must bear a 25 degree tilt; the squeeze is sized on the kit cube.

## Under a micrometre — 2026-10-21

ADR 0043 (FR-024, the weekly reading of 19 October; the owner's rule of 20 October). Each drawn
set-up of a sweep is run five times more with the machine set down within 1 micrometre of its
place and turned within 1e-5 rad, under its own label (the same camera noise). The tilt table, 8
set-ups: no outcome changed; it tipped within 0.05 degrees of itself against 3.7 degrees across
set-ups. Fetch, ADR 0042's 59 set-ups (354 runs): no outcome changed; the last goal's time (0.10
s against 1.2), the squeeze (0.06 N against 1.6) and the lean (0.12 degrees against 1.4) spread
under a tenth of their spread across set-ups - the design's; the fall into the bin (0.29 cm
against 1.0), the bin's push (0.07 N in a step against 0.35, 0.02 over 50 ms against 0.06) and
the table's (0.013 N against 0.064) spread a fifth to a third of it, in 46 to 58 of the 59 - partly
chance. Moved by nothing, a repeat is its set-up step for step. Checked in `tests/test_jitter.py`
(4). Suites on MuJoCo 3.10.0: 1002 passed with a display, 955 headless.

Not claimed: only the machine's placement is jittered (the cube's own place, the payload and
friction are not); a micrometre is not a real repeat's variability (FR-009 would measure that);
five repeats find a knife edge often crossed, not a rare one.

## Robots from their own files — 2026-10-21

ADR 0044 (FR-031; the owner, 21 October). A URDF or MJCF file is imported into a robot library
outside the repository and driven like a Menagerie arm. Checked with robots made in the tests:
the two-link arm (4.3 kg, no motors, its forearm a mesh in a ROS package) gets a servo on each
joint - 631 and 112 N m/rad, set by holding its weight within 0.5 degree - and holds 60 and -40
degrees held out sideways within 0.4 degree, within 1 degree after 0.18 s; with a 3 N m shoulder
it is reported too weak, pushes no more than 3 N m and falls to its limit; a parallel gripper's
mimic finger follows its leader to 30 mm within 0.5 mm, driven in millimetres; links overlapping
at home are kept from colliding (without that the arm is pushed 4 degrees off); a two-pose block
program completes; the tool goes where a jog sends it within 2 mm. The UR5e imported from its own
file adds nothing and follows the shipped arm within 0.5 degree. Six broken files are refused by
name and leave nothing behind; a misspelt `efort`, a link without mass and a COLLADA mesh are
reported. The Joint lab imports from its file or from a file dropped on the window. Checked in
`tests/test_robot_library.py` (18, one a window test). Suites on MuJoCo 3.10.0: 1020 passed with a display, 972 headless.

Not claimed: robots that float or walk, ball and planar joints; more than 8 driven joints;
speed limits, current, gearing or heat in the servos added; grippers from files driven by the
grasp blocks (OPEN LW-030); a straight-line tool path (the tool bows some 10 mm on a 3.6 cm
jog, OPEN LW-031); that a file's masses and limits are right.

## The tool travels its line — 2026-10-21

ADR 0045 (FR-032; the owner's request of 21 October for control that costs little to learn).
A tool step is solved every 2 mm along its straight line and handed out at 5 cm/s; held arrow
and page keys carry the tool at that speed. Kit arm, 10 cm steps left, up and down: 7.7, 6.9
and 12.7 mm off the line before, 0.2, 0.2 and 0.3 after; from its stretched pose, back 2 and 6
cm: 4.5 and 7.8 mm before, 2.3 and 1.3 after; UR5e: 2.3 to 4.3 mm before, 0.6 to 3.5 after (its
own sag under its weight remains); the imported test arm's 3.6 cm step: 10.2 mm before, 0.4
after. A 10 cm step arrives within 2 mm after 1.9 s (0.6 to 0.9 before). Held for 3 s, the tool
went 14.7 cm within 0.3 mm of its line; driven out of reach it stops and stays. Checked in
`tests/test_tool_glide.py` (8, one a window test) and `tests/test_arm_tasks.py`'s window test.
Suites on MuJoCo 3.10.0: 1028 passed with a display, 979 headless.

Not claimed: the servos' lag and sag; collisions along the line; lines through poses the arm
cannot take (refused, not bent around); dragging the tool with the mouse; a program's pose
blocks, which still move joint by joint.

## The first hour, checked by the app — 2026-10-22

ADR 0046 (FR-033; the owner's request of 21 October for learning that costs little). Five
lessons as data, each checked from what the window can see. Each was finished in the window
through a user's actions: the tool lesson by holding arrow and page keys towards the cube as a
user watching it would (the arm first drawn back along a line that never passes the cube); the
program lesson by the Pick and place template and Run, the cube lifted; the import lesson by the
prefilled form with the sample arm (three joints, a servo added to each, nothing to check) and
the joint motion example; the drive lesson by a two-stop drive-to program through the door into
the bay, the frame untouched; the sweep lesson by the sprint, Stop and Repeat with variations.
Each check says what is missing before it passes; progress survives a restart and a spoilt file
starts afresh. Checked in `tests/test_lessons.py` (7, three of them window tests). Suites on
MuJoCo 3.10.0: 1035 passed with a display, 983 headless.

Not claimed: that the lessons shorten anyone's first hour (no study here); that a check sees
understanding rather than the simulator's state.

## A gripper from its file — 2026-10-22

ADR 0047 (OPEN LW-030). The two-link test arm with a parallel gripper at its end - two 30 g
fingers sliding across the palm, the second mimicking the first, 20 N of effort: the finger joint
is found as the gripper, closing where the fingers meet, its jaws the two finger links. Before,
its servo was sized as any joint's (16 N/m) and pressed a 3 cm box with 0.12 N at each jaw; a
10.8 g box turned over by the elbow slid 7.3 mm and on at 4.4 mm/s. Squeezing with its 20 N at
MuJoCo's default contact softness, the jaws sank 6.8 mm into each side of the box and the mimic
finger gave 3.5 mm. Now a block program closes the jaws on the box (60 % in 1 s) and its grasp
check passes at 50.9 % closed; turned over a right angle, the box hangs from the jaws alone and
stays within 1 mm of where it was held (0.44 mm); fully closed, each jaw presses with 10.0 N,
sinking 0.15 mm; opened, the box falls free. Tool mode drives the gripper, its tool point between
the jaws. A claw closing on a fixed jaw, no effort in its file, squeezes with 12 N at its jaw and,
closing on nothing, stops where its jaws meet (77 % of its travel). The same two slides named as
a stage's are driven in millimetres. Checked in `tests/test_robot_library.py` (20, one a window
test). Suites on MuJoCo 3.10.0: 1037 passed with a display, 985 headless.

Not claimed: grippers named otherwise, or driven through a tendon or a linkage; the file's
velocity limit (sent at once from open to closed, the fingers reach 0.76 m/s); a slip or payload
rating; that a file's effort is the gripper's real force.

## A grasp the program feels — 2026-10-22

ADR 0048 (FR-026, the weekly reading of 19 October). The kit gripper's jaws read as XH430-W350
servos at 12 V: the kit jaw's 0.6 N m is 85 counts of 2.69 mA at the datasheet's stall point
(3.4 N m at 1.3 A); a degree is 11 pulses; the Moving Threshold's 10 counts are 0.24 rad/s.
Holding: both jaws still, at least 2 pulses short of their goal, pushing with at least 6 counts.
Fetch, 71 set-ups (seed 1), the program feeling its grasps: 71 of 71 met every goal, as with the
contacts; 71 grasp checks, the jaws felt a hold at every one and the contacts showed one at every
one; the checks passed 54 ms later (median), the cube in the bin 62 ms later; squeeze 3.66 N
over 50 ms (3.96 with the contacts), fall 0.35 cm (0.31). A held jaw draws 11 to 25 counts (28
carrying 0.5 kg); closing on air, at most 6, moving. Disturbed (9 set-ups under each of 7 disturbances): the same outcomes as with the contacts, and 54 grasp checks all felt as the contacts showed; no sweep check met empty jaws, and the cube taken from between closing jaws is felt as not held. Checked in `tests/test_feel.py`
(7). Suites on MuJoCo 3.10.0: 1044 passed with a display, 992 headless.

Not claimed: that the kit gripper is a ROBOTIS one (an assumption, stated); a real servo's
current noise and friction (the registers here are exact but for their counting); what is held,
only that something is; the arm's own servos (a reach that meets something still waits for its
pose, OPEN LW-029).

## Tuning draws and held-out draws — 2026-10-22

ADR 0049 (FR-027, the weekly reading of 21 October). Sweeps record their seed; the ledger
`docs/sweeps/seeds.jsonl` lists seed 1 for every field as the tuning draws of ADR 0024 to ADR
0048, and seed 20261022 as the Fetch field's held-out draws, entered before they ran. The Fetch
program as of ADR 0048 on those 59 fresh set-ups, beside its 59 on seed 1: every goal met in 59 of
59 (94-100 %, two-sided 95 %) both; no presses on the table (0.17-0.23 N over 50 ms, as tuned);
the fall into the bin 0.2-0.9 cm (0.1-1.1 tuned); the squeeze 3.71 N (3.66 tuned); every grasp
felt as the contacts showed. Outside the tuning range: the table's push in one step 0.77 N on one
draw (0.62 N tuned; 0.18 N over 50 ms), the bin's least push in a step 0.44 N (0.45) and the
cube's least lean 26.0 degrees (26.2). Checked in `tests/test_holdout.py` (5). Suites on MuJoCo
3.10.0: 1049 passed with a display, 997 headless.

Not claimed: that sweeps outside the ledger used seed 1 (October's did); a failure rate below
about 5 % (59 fresh draws without one); held-out checks of the chosen set-ups, which every sweep
shares.

## A contact census — 2026-10-22

ADR 0050 (FR-030, the weekly reading of 21 October). The Fetch field run once as designed, its
contacts counted every 20 ms, as the model is set (multiccd off) and on a copy of the instant
with multiccd on, at the cart standing at its start and at the table, the cube held, carried and
resting in the bin. Box on box, the same count either way: the cube on the table 4 points (1-2 as
it is lifted), the jaw pads on it 1-4 each (the left 1-2: the rotary jaws meet it at an edge), the
palm stop 1-2, the cube in the bin 3-4, each tread on the floor 2-6. The casters' wheels on the
floor - a cylinder on a box - 1 point as set, 4-5 with multiccd. Beside it, the casters' loads:
one 2.2-8.2 N through the run, the other 0.4-2.5 N standing and nothing at the bin, 0.2 mm above
the floor. On the bench, a box resting on its face keeps its 4 points with multiccd, a lying
cylinder goes from 1 to several. Checked in `tests/test_census.py` (3). Suites on MuJoCo 3.10.0:
1052 passed with a display, 1000 headless.

Not claimed: drawn set-ups (one run, as designed); where the points are or what each carries;
any result with multiccd on (none was rerun: FR-030 reruns only a face on a face held by one
point, and there is none).

## What looking again earns — 2026-10-23

ADR 0051 (FR-023, the weekly readings of 19 and 21 October). The Fetch field's 9 set-ups (seed 1),
undisturbed and under four disturbances, with the program's own recovery and with three
baselines run on the same set-ups (`sweep --disturb --recovery`). The cube moved 5 cm, 2 s after
the look: looking again 9 of 9; reaching again where it had been 0 of 9; looking again but reaching
as far off in a random direction 0 of 9 (2 aims out of reach, 5 grasps of nothing, 2 reaches
blocked); stopping 0 of 9 - 9 discordant pairs against each, exact McNemar p = 0.0039. Undisturbed,
the cube moved before the look and the cart shoved 6 N s: 9 of 9 for all four; the camera frozen:
0 of 9 for all four. No recovery fired undisturbed. One run of the own arm repeated came out the
same. Checked in `tests/test_recovery.py` (8). Suites on MuJoCo 3.10.0: 1060 passed with a display, 1008 headless.

Not claimed: a certification (the draws are the tuning draws, ADR 0049); a baseline's rescue rate
below 31 % for a late move (8 drawn set-ups); FR-023's `timed` arm (not run: a retreat at the
detector's own moment rescued nothing); the cost of false alarms (FR-022).

## How late is too late — 2026-10-23

ADR 0052 (FR-022, the weekly reading of 19 October). An alarm from outside (`Runner.alarm`) makes a
program that looked recover as its own recovery does; with the recovery `ignore` its checks fire
and the program goes on as taught. The Fetch field's 9 set-ups (seed 1) with the cube moved 5 cm
2 s after the look, the checks ignored, each run again with an alarm every 0.5 s of the time the
program listened (135 branches): in 5 set-ups an alarm rescued the run until the program left the
table (deadline 22.5 s, 2.6 to 2.8 s after its own check); in 4 the program's own closing tipped the
cube onto its side and the window closed at 20.0 to 20.5 s (0.28 to 0.85 s after its own check).
The window opened before the move - an alarm 1.01 s before it rescued, 1.11 s before it did not -
and had one hole, an alarm whose opening of the jaws tipped the cube itself. The camera frozen with
its pictures taken as new: none of 15 alarms rescued it. The 71 set-ups of ADR 0048's sweep, each
with one false alarm drawn from the time its program listened: 70 still met every goal, a median
5.9 s later (1.1 to 8.5); the one broken was raised while the cube was held, dropped it on its
side, and a cube on its side was lost on the way to the bin in 20 of 24 runs. The program's own
runs reproduced ADR 0048's bit for bit (9 disturbed, 71 undisturbed). Checked in
`tests/test_branch.py` (10), including a pair of Fetch runs identical until the alarm. Suites on
MuJoCo 3.10.0: 1070 passed with a display, 1018 headless.

Not claimed: a certification (the tuning draws, ADR 0049); deadlines finer than the 0.5 s between
alarms; a real detector's errors (the alarm is always on time, and the false alarms' moments are
drawn evenly); an alarm the user can raise from the window; anything for fields other than Fetch.

## Time passes while the program looks — 2026-10-23

ADR 0053 (FR-028, the weekly reading of 21 October). Latencies from their sources
(`control/latency.py`): a picture 139 ms - the D435's 33 ms frame interval at 30 fps and the finder's
106 ms, measured; a command 7.6 ms and a reading 33 ms - Protocol 2.0 packets for the kit's six servos
at the X series' default 57,600 bps and 500 us return delays. The Fetch field's 9 set-ups (seed 1),
undisturbed, shoved 6 N s and with the cube moved 2 s after the look: at the sourced latency 27 of 27
met every goal (+0.0 to +0.1 s); at 0.2 s on every path 27 of 27 (about 4 s later undisturbed); at
0.25 s 16 of 27; at 0.3 s none - every failure the jaws holding the cube and the grasp check over
before the hold had crossed the bus. One path at a time, 0.5 s late: pictures 9 of 9 unchanged
(within 10 ms), commands 7 of 9, readings 7 of 9. The 71 set-ups of ADR 0048's sweep at the sourced
latency: 71 of 71, a median 0.03 s later. Checked in `tests/test_latency.py` (7). Suites on MuJoCo
3.10.0: 1077 passed with a display, 1025 headless.

Not claimed: the camera's pipeline beyond its frame interval, a USB adapter's latency timer, retries
or lost packets; the finder's time on the owner's Mac (it was measured on the cloud's CPU); latency
in the interactive window; a certification (the tuning draws, ADR 0049).

## Searching for the failure — 2026-10-23

ADR 0054 (FR-025, the weekly reading of 19 October). A compass search over the variation box from the
design as designed (`inventory/falsify.py`), against drawn set-ups. Fetch, a run's margin against what
the 59 tuning draws certified (ADR 0049): the search found no excursion in 40 runs (lowest +0.03),
where 59 fresh draws had one at draw 19 (the table's push 0.77 N in a step, 0.49 kg carried; 5 of 5
micrometre repeats outside); the search on that measure alone found one at run 27 (0.65 N; 1 of 5
repeats outside). The tilt table: the search's lowest tip 53.35 deg at run 15 of 30, 30 random draws
55.03 deg, the plan's corner friction at its high end 53.32 deg. The cart rocking between its casters
(before ADR 0041), as designed and on the 9 set-ups carrying 0.44 kg or more: no press, every goal met.
162 runs. Checked in `tests/test_falsify.py` (6). Suites on MuJoCo 3.10.0: 1083 passed with a display, 1031 headless.

Not claimed: a rate of finding (one realisation of each comparison); searches other than the compass
search; a sourced limit on what the cube can bear (the margin is the tuning draws' envelope); why the
rocking cart no longer presses (not traced).

## Watch it work — 2026-10-26

ADR 0055 (the owner's request of 26 October). Each of What's new's four demonstrations, started by its
button in a hidden window under Xvfb, does what the button says, on the run's clock: the cube moved 5
cm at 16.5 s, the program blocked reaching down at 19.9 s, looked again and lifted the cube at 27.1 s,
done at 45.8 s with all four goals met; the camera frozen at 14.5 s, the program stopped at 14.8 s with
"the camera's picture is not new" and the cube not lifted; shoved at 14.5 s, going back at 16.3 s, done
at 50.7 s, all goals met; Look again pressable from 15.2 s, pressed at 16.2 s, done at 42.4 s, all goals
met. Checked in `tests/test_whats_new.py` (9, three of them window tests). Suites on MuJoCo 3.10.0: 1092 passed with a display, 1037 headless.

Not claimed: anything the sweeps do not measure - the window shows their disturbances, the counts stay
theirs; the same times in every run (the goals are checked once a frame, so a disturbance after a goal
can come up to a frame's simulated time later); a reading of a robot model's own gripper servo.

## The factory cell's process window — 2026-10-26

ADR 0056 (FR-029, the weekly reading of 21 October). 38 production runs of the Panda's cell, six parts
each, headless; each part read from its slot's centre once its placement was checked, against the room
its slot gives it (6.5 mm along the table, 19 mm across, 38.9 deg turned). Small blocks: at the feeder's
centre 6 of 6 within their room, 1.4 to 4.4 mm out along x and 1.0 to 2.2 mm short across, Cpk along x
1.05; fed ±2 mm and ±5 deg off, 54 of 54, Cpk x 1.02 (95 %: 0.80 to 1.23); ±5 mm and ±15 deg, 51 of 54,
Cpk x 0.57 (0.43 to 0.71); none left turned more than 3.8 deg; cycles 12.1 to 13.9 s. Tall blocks: every
run failed at its fifth part, every part outside its room. Traced: the tool stops 4 mm short and low
(no gravity compensation), the hand squeezes 1.6 N, the part creeps 3.3 mm in it. Previewed on copies:
gravity compensation and a 20 or 70 N squeeze, 0.4 to 2.1 mm. Checked in `tests/test_process_window.py`
(5) and a window test in `tests/test_whats_new.py`. Suites on MuJoCo 3.10.0: 1098 passed with a display, 1042 headless.

Not claimed: a simulated feeder (its spreads are assumed draws); a real fixture's tolerance (the zone is
the slots' clearance); that the fixes are right - they are previews, the owner's call (OPEN LW-036); why
tall parts tip (OPEN LW-037).

## The cell lowers its parts straight down — 2026-10-26

ADR 0057 (OPEN LW-037). The factory cell's vertical stages solved a centimetre at a time along their
line, the hand opened 8 mm past the part to let it go. The 38 production runs of ADR 0056 again: every
run finished, small and tall alike; 228 of 228 parts within their room (225 before, the tall ones
none); worst 6.3 mm; Cpk along the table 1.25 and 1.08 at the feeder's centre, 0.90 and 0.85 with the
feeder ±5 mm and ±15 deg off (small, tall); lowered, the tool within 5.0 mm of the vertical (it had
swung 7 to 15 mm); 12.4 s a part on average. Checked in `tests/test_straight_descent.py` (3). Suites
on MuJoCo 3.10.0: 1101 passed with a display, 1045 headless.

Not claimed: straight transfers (only the vertical moves are lines); collision checking along any
path; that the 2 to 6 mm out along the table is the real arm's (OPEN LW-036).

## A motor run hot — 2026-10-27

ADR 0058 (FR-019). A 'motor' disturbance scales a motor's own speed-torque line from its trigger on,
its friction kept; copper's 0.00393 per C at 20 C (NBS Circular 31) gives a winding 50 K hot 84 % of
its stall torque at the same free speed. The kit cart with its left motor 50 K hot from the start: the
Sprint, the ramps, the push and the curb run step for step the same as undisturbed (their traces
equal), and the Fetch too, also with the motor at 25 %. The drive never asks a motor for more than its
0.5 N m operating cap, at most 48 % of the line at the speed it turns, on the flat 23 to 34 %. On the
Sprint the left motor kept 84 down to 30 % with nothing changed; at 25 % the drift to the right was
17 mm less (338 mm as designed). Checked in `tests/test_weak_motor.py` (4). Suites on MuJoCo 3.10.0:
1105 passed with a display, 1049 headless.

Not claimed: the winding's temperature (50 K is assumed); the magnets' weakening with heat; a machine
built nearer its motors' limits; the curve FR-019 predicted, which was not seen.

## How near it is to tipping — 2026-10-27

ADR 0059 (FR-005). The force-angle measure (Papadopoulos and Rey) against its closed forms: atan(reach /
height) per edge on the flat; the downhill edge running out at the static tip angle on a slope; braking
taking atan(a / g) from the front edge. On the solver: the arm on its cart on the tilt table, 44 deg left
standing level, falling three quarters of a degree for each degree of table, running out at 53.5 deg - its stance's static prediction 54.2
(55.6 with the rail), the field reading it over at 54.6, an uphill wheel 2 mm up at 53.0; the cart alone
11.9 deg left at the table's 60 deg (it would run out at 71.9; predicted with the rail 72.0). Hard stops
from 0.42 m/s: the least angle 54 deg (cart), 47 (cart, 1 kg on the deck), 40 (arm cart), 37 (arm cart,
0.5 kg), each 3 to 4 deg below its cruise. Checked in `tests/test_tipping.py` (8) and a window test in `tests/test_whats_new.py`. Suites on
MuJoCo 3.10.0: 1114 passed with a display, 1057 headless.

Not claimed: the 20 ms check against a lifting wheel when braking tips a machine (none tips, OPEN
LW-038); supports that are not flat; impulses shorter than the 50 ms the accelerations are taken over.

## A motor run hot, seen in the window — 2026-10-27

ADR 0058, its window part. What's new's "A motor run hot": the arm on its cart on the Fetch field, its
left motor 50 K hot from 0.6 s into the run, as the program started; the drive panel marks it weakened,
84 % of its torque, the right motor not; the cube in the bin at 37.5 s, as in the window undisturbed.
Checked in `tests/test_weak_motor.py` (5: the panel's reading of a weakened line, the reset world's
motor as built) and a window test in `tests/test_whats_new.py`. Suites on MuJoCo 3.10.0: 1116 passed with a display, 1058 headless.

Not claimed: what the panel's share means for heat - it is the share of the motor's own stall torque,
whatever weakened it.

## Once it holds, an alarm is not heard — 2026-10-27

ADR 0060 (OPEN LW-033). The Fetch as designed listens from 15.14 s to its grasp check at 19.11 s (it
listened to 20.62 s). An alarm 0.3 s and 1.5 s after the check is not heard, and the run is its
undisturbed run step for step, the cube in the bin at 36.87 s; before, the jaws opened on the cube in
the air and it was fetched again, in the bin at 44.24 s and 44.51 s. Checked in `tests/test_branch.py`
(one more). Suites on MuJoCo 3.10.0: 1117 passed with a display, 1059 headless.

Not claimed: ADR 0052's false-alarm study run again; a cube slipping from the hand after the check
looked for again on an alarm.

## How close to slipping — 2026-11-02

ADR 0061 (FR-036). Friction use - the friction a contact uses over what its cone allows - against its
closed form: a wooden block on a concrete slope (mu 0.4) uses tan(theta) / mu within 0.02 at 5, 15 and
21 deg and is at the edge, 1, and sliding at 23 deg. Reading it leaves a Sprint unchanged step for
step. The Fetch's grip while it carries the cube: median 0.38, at most 0.80; made 2, 4, 8, 16 and 32
times as heavy: 0.43, 0.44, 0.61 (in the bin, having slid 17 mm in the jaws), 0.77 and 0.94 (both
slid out on the lift). The squeeze grows with the load (3.1 N as designed, 5.2 N at 4 times, 5.9 N at
8), so the first-order margin from the use (1.25 to 2.6 times) did not say how heavy a cube it carries
(8 times). In the window the cube 16 times as heavy slides out as the panel passes 95 %. Checked in
`tests/test_friction_use.py` (4) and a window test in `tests/test_whats_new.py`. Suites on MuJoCo
3.10.0: 1122 passed with a display, 1063 headless.

Not claimed: a sourced torsional friction coefficient (MuJoCo's 0.005 m default); still contacts
inside their cones (a block on a slope creeps, OPEN LW-039); more than one set-up for the mass study;
the wheels' traction margin.

## The collection's search mixes words and meaning — 2026-11-02

ADR 0062 (OPEN LW-027). The 20 questions with known answers (docs/radar/queries.jsonl), an answer in
the top three: at 183 entries words alone 15 (mean reciprocal rank 0.69), words and meaning equally 17
(0.76); with the reading of 2 November, 238 entries, words alone 14 (0.60), Okapi BM25 14 to 15, the
mix 16 (0.69). The command line now mixes by default. Checked in `tests/test_radar_collection.py`.
Suites on MuJoCo 3.10.0: 1122 passed with a display, 1063 headless.

Not claimed: more than 20 questions; that the mix keeps its answers as the collection grows.

## Where runs fail — 2026-11-03

ADR 0063 (FR-038). The stage profile - how many runs met each goal and every goal before it, the first
goal each missed, what a program that gave up was doing - on runs made up for it, and on the field:
the Fetch's disturbance sweep with its recovery off, where three disturbances each cost all 9 set-ups
and fail in two places - the cube moved 2 s after the look at the reach (the program gave up moving the
arm, 9), the camera frozen and the camera dark at the look (9 each). Checked in `tests/test_stages.py` (3). Suites on MuJoCo 3.10.0: 1125 passed with a display, 1066 headless (run with ADR 0064's four tests beside them: 1129 and 1070).

Not claimed: stages finer than the field's goals and the program's block kinds.

## Plan the draws — 2026-11-03

ADR 0064 (FR-039). The exact McNemar test needs 6 pairs all one way for p < 0.05 (4: 0.125, 5: 0.0625,
6: 0.031); at a 4 in 59 rate 59 paired draws have a 21 % chance to show it, 116 give 80 %, 120 83 %,
150 95 %; 59 draws that all succeed bound a failure rate at 4.95 %, under 2 % takes 149, under 1 % 299;
the power summed over outcomes agrees with 4000 random draws within 2.5 points. Checked in
`tests/test_power.py` (4). Suites on MuJoCo 3.10.0: 1129 passed with a display, 1070 headless.

Not claimed: a plan written into the seed ledger by the command line; the smallest effect worth seeing,
which is chosen, not computed.

## What's new: where repeats fail — 2026-11-03

ADR 0063 and 0064 in the app. What's new's *Where repeats fail* runs the Fetch once, as designed, and
stops the run as its program ends - its report on the left, as Stop shows it, with both lines under its
Repeat buttons: "8 drawn: if all succeed, failures under 31 %" and "to be sure it breaks runs, it must
break 6 of the 8 drawn"; Repeat with disturbances then starts its 72 runs in the background. Checked by a
window test in `tests/test_whats_new.py`. Suites on MuJoCo 3.10.0: 1130 passed with a display,
1070 headless.

Not claimed: anything measured by the demonstration itself; the sweep it starts is the panel's own.

## The Panda held up — 2026-11-03

ADR 0065 (OPEN LW-036). The Panda's links held against gravity on a fixed base, not on a cart; its
hand's servo limited to 70 N a finger, its fingers moving at 50 mm/s, their contacts weighted to the
fingers' stiffness. In the cell the tool stops within 0.47 mm of every point (5.7 to 6.7 mm before),
each finger presses 70.0 N through the carry, and 228 parts in 38 production runs land within 1.05 mm
of their slots (2.2 to 6.3 mm before): Cpk along x 10 to 20, from 0.85 to 1.27. Checked in
`tests/test_panda_held.py` (2), with `tests/test_robot_assets.py`, `tests/test_process_window.py`,
`tests/test_straight_descent.py` and a window test in `tests/test_whats_new.py`. Suites on MuJoCo
3.10.0: 1133 passed with a display, 1072 headless.

Not claimed: the real arm's identified dynamics, its hand's force control, a payload compensated; a
Panda on a cart held up.

## The jaws squeeze by current — 2026-11-03

ADR 0066 (FR-037, in part). The kit gripper's jaws closed on a fixed box at their pads' centres, set
to 1, 2, 4 and 6 N, push with 0.98, 1.95, 3.97 and 5.99 N, Present Current within a count of its Goal
Current; a box reaching past the pads' centres is pushed with 52.5 / 67.5 of the setting; with no
squeeze the motors' full 0.6 N m. The Fetch as designed, closed fully at 7 N: every goal met, the
grip's friction in use at most 60 % (80 % as it is). Checked in `tests/test_grip_current.py` (6) and a
window test in `tests/test_whats_new.py`. Suites on MuJoCo 3.10.0: 1140 passed with a display, 1078 headless.

Not claimed: the Fetch's program squeezing by current, or its sweeps with it (OPEN LW-041); a squeeze
in newtons anywhere but at a pad's centre; the servo's current noise or the datasheet's bent curve.

## A roller conveyor — 2026-11-03

ADR 0067 (FR-007, in part). In MuJoCo itself, a 160 mm box laid across 50 mm cylinders sinks into them
with multiccd off, and across capsules rests on their tops. The conveyor field: the rollers held at
0.1 m/s under load; two pallets carried within 0.1 % of it, at rest against the stop and queued behind
the first, to 0.1 mm, rising under 0.5 mm, the first pallet's cube still on it. Checked in
`tests/test_conveyor.py` (3) and a window test in `tests/test_whats_new.py`. Suites on MuJoCo 3.10.0:
1144 passed with a display, 1081 headless.

Not claimed: the factory's feeder (it still moves its parts by hand); a shared drive, a motor curve or
a speed other than 0.1 m/s; accumulation pressure measured against a real line; a held pallet's load
staying put - it creeps forward on a pallet the rollers slip under (OPEN LW-042).

## The cell fed by a conveyor — 2026-11-04

ADR 0068 (FR-007). Friction rollers: each drive passes at most 5 % of its share of a pallet's load
(Interroll's 4 to 6 %); under the field's held pallets the rollers stand still and the cube on the
first stays put (it crept 0.7 mm/s, its follower 3.8 mm/s, OPEN LW-042). The cell fed by the
conveyor (`docs/sweeps/2026-11-04-cell-fed-by-the-conveyor.md`): small blocks 60 of 60 placed over
ten runs, each arriving within 3.9 mm of its place at the stop and left within 1.0 mm of its slot;
tall blocks 24 of 24, within 3.7 and 0.75 mm. Frame time: a 2 ms step 0.86 ms fed by the conveyor, 0.39
ms fed by hand. Checked in `tests/test_cell_conveyor.py` (3), the field's run
in `tests/test_conveyor.py` and a window test in `tests/test_whats_new.py`. Suites on MuJoCo 3.10.0:
1148 passed with a display, 1084 headless.

Not claimed: the pallets' return and loading (a person's, not simulated); a friction roller's drive
following the load on it step by step; zones, sensors, or a speed other than 0.1 m/s; a person's
spread on the pallet beyond the assumed draws; the feeder saved with a cell.

## The cell finds its parts — 2026-11-04

ADR 0069 (OPEN LW-010; FR-011 for the cell). The cell's overhead camera as a RealSense D435, its
depth noise included, finds each part round the source's place (`docs/sweeps/2026-11-04-the-cell-finds-its-parts.md`):
216 of 216 parts found and placed, small and tall, by hand and on the conveyor, each seen within 1.5 mm
in plan, 2.2 mm in height and 4.1 deg, left within 1.6 mm of its slot - as the state's 180 of 180. Checked in `tests/test_cell_camera.py` (3) and a window test in `tests/test_whats_new.py`.
Suites on MuJoCo 3.10.0: 1152 passed with a display, 1087 headless.

Not claimed: a camera's calibration error, holes or flying pixels; latency; the turn it sees used for
the grasp; a part found anywhere but round the source's place.

## The Fetch squeezed by current, side by side — 2026-11-05

ADR 0070 (OPEN LW-041; FR-037). The Fetch as it is against closed fully at 7 N by current, paired set-up
by set-up (`docs/sweeps/2026-11-05-the-fetch-squeezed-by-current.md`): on 71 tuning set-ups and 59 held-out draws
every goal met either way, no pair broken or mended; the squeeze at 7 N 5.2 to 12.2 N, its spread six
times the ramp's; the cube in the bin 0.7 s later. Not adopted:
the program keeps its ramp. No code changed; the suites are 5f41dd9's.

Not claimed: a squeeze other than 7 N, or one set for where the cube sits; a measured force at a pad.

## A reach that feels what it meets — 2026-11-06

ADR 0071 (OPEN LW-029). The Fetch as it was against its arm read as servos - a joint that falls 0.5 deg
further behind its goal late in a reach has met something - paired set-up by set-up
(`docs/sweeps/2026-11-06-a-reach-that-feels.md`): with the cube moved 5 cm 2 s after the look, the arm
rose 0.21 s after a jaw met the cube, not 2.44 s, pressed it 2.35 N over 50 ms for 0.22 s, not 3.11 N
for 2.45 s, and delivered 2.4 s sooner, every goal met 9 of 9 either way; under the other disturbances
and undisturbed - 63 disturbed runs, 71 tuning set-ups and 59 fresh draws - no reach was felt.
Checked in `tests/test_felt_reach.py` (6) and a window test in `tests/test_whats_new.py`.
Suites on MuJoCo 3.10.0: 1159 passed with a display, 1093 headless.

Not claimed: a reach faster than its servo's lag allows for (under a quarter of the travel's time);
a jaw meeting the object after the reach's travel; what was met; joints read in pulses.

## What's new in pages — 2026-11-06

ADR 0055, amended: at the window's own 1200 by 780, What's new shows its demonstrations eight to a
page with "< Newer" and "Older >" under them, and what the picked one shows above the Guide's own
button; a tall window shows them all on one page. Checked in `tests/test_whats_new.py` by drawing every
page with every demonstration picked. Suites on MuJoCo 3.10.0: 1179 passed with a display, 1112 headless.

Not claimed: a window narrower than the panel's 288 pixels; text sizes other than the panel's own.

## From a clone to a running window — 2026-11-11

ADR 0072 (the owner's request of 10 Nov). From a clean clone into a new environment, the README's
three commands: `pip install '.[workshop]'` 26 s, then `little-world` opens the window with What's
new on the left; `little-world doctor` finds the installation ready - nine checks, a note instead of
a failure where there is no display - and a window command that cannot import says what failed and to
run the doctor. The README is 114 lines; its feature list and manual are `docs/FEATURES.md` and
`docs/MANUAL.md`, moved whole. Checked in `tests/test_cli.py` (10, one a window test).
Suites on MuJoCo 3.10.0: 1179 passed with a display, 1112 headless.

Not claimed: anything published - GitHub has the import of 24 Sep until the owner pushes; macOS,
Apple silicon or Windows run with this command; an installer; a licence to use it.

## Evidence anyone can measure again — 2026-11-11

ADR 0073 (the owner's request of 10 Nov). `little-world evidence` measures 31 quantities for twelve
headline claims and prints each beside its record: all 31 hold on the machine they were recorded on,
in 3.5 min (`--quick`: 10 in 33 s); a run repeated is the same to the last bit, and the 71 Fetch
set-ups of ADR 0070 and ADR 0071, a week apart, agree to the millisecond. The quick tier
(`pytest -m "not slow"`) is 1,048 tests in 76 s; the 64 slow ones, 35.9 of the suite's 37.2 min,
are listed in `tests/slow.txt`. Every relative link in 158 Markdown pages leads to a file. Measured
for `docs/EVALUATION.md`: on MuJoCo 4.0.0, 20 of 1,087 headless tests fail (13 in the robot importer);
with elliptic friction cones, 16; with NumPy's AVX-512 paths switched off on the same machine, 29
of the 31 quantities are the same to the last digit, the Fetch's delivery moves 4 ms, and the quick
tier and the 64 slow tests pass. Checked in `tests/test_evidence.py` (9).
Suites on MuJoCo 3.10.0: 1179 passed with a display, 1112 headless.

Not claimed: a record from any machine but one; tolerances that are more than judgment; workflows
that have run - they were written without GitHub's runners; the other claims, which the tests hold.

## Energy from nowhere — 2026-11-12

ADR 0074 (FR-040, first in the weekly reading of 9 November). Every run checks that no contact gave
back more energy than it took: the work each pair of touching bodies' contacts did on them, added up
from the moment they touched, may not come to more than lifting the lighter body 2 mm takes.
Checked against the bodies' own energy: a block dropped 5 cm onto a slab gives the slab the 40 mJ it
fell, to 1 %, and is given none back; started 0.5 to 10 mm inside it is pushed out with as much as
lifting it that far takes (0.49 to 9.99 mm's worth), flagged from 2 mm; a box set 3 mm into another,
2.47 mJ, lifting it 3 mm (5 %). Reading it changes nothing, to the last bit. Over the headline
claims' runs and the other fields, three touches pass the line. On the Curb run a swivel caster's
wheel against the 10 mm curb's edge gives the kit cart 78 mJ from nowhere, 4.6 mm's worth, before
it climbs over at 10.4 s; at 1 ms steps 66 mJ, with multiccd on none (cleared at 11.4 s), with
elliptic cones or no noslip none and no climb in 13 s (OPEN LW-047). In Real's cell the Panda's
fingers pass it as they close on a part (2.6 mm's worth at 2 ms steps, 0.7 at 1 ms) and, fed by the
conveyor, as one holds a part (3.8). Over the Fetch's 71 tuning set-ups and the 59 draws ADR 0049 held out, every goal is met in all 130; in 21 (16 %; 10 to 24 % at 95 %) a jaw's contact with the cube passes the line - in 15 as the jaws close on it, mostly the left pad (a contact that comes on with the pad already in the cube: a step's doing), in 6 while they hold it - by as much as 1.8 mJ, 11.5 mm's worth; the median set-up's most is 0.26 mm's worth. With elliptic cones the
jaws' pads give the carried cube 1.9 and 1.6 mJ from nowhere (OPEN LW-039). In the window the drive
panel and the run's report say what the check found; What's new runs the Curb run (*Energy from
nowhere*). Checked in `tests/test_artifacts.py` (8), a window test in `tests/test_whats_new.py`, the
evidence's `physics` claim.
Suites on MuJoCo 3.10.0: 1188 passed with a display, 1120 headless.

Not claimed: that the line is more than judgment; that a gain made a little at a time across many
short touches would be caught; joint limits and other constraints; what the energy did - the
cart climbs the 10 mm curb without it, with multiccd on, a second later.

## An estimated tip apart from one seen — 2026-11-12

OPEN LW-048, ADR 0059 amended. The run report said "(it tipped)" when the force angle's estimate
reached zero. Reproduced on 4c0ea8f with the Curb run driven as a sweep drives it and the test
drive's telemetry read every step: the kit cart leaned 3.7 deg at most and kept its upright goal,
while the stance margin fell to -13.1 cm and the force angle to -145.8 deg - one step's support was
one drive wheel's treads, another's two casters with one against the curb's edge. In a hidden window
(What's new's *Energy from nowhere*) the report read "closest to tipping: -142 deg left (it tipped)";
it now reads "estimated: fewest -125 deg from tipping" and "seen: tilted 3 deg at most, did not
tip" (the window reads once a frame, so its fewest moves from run to run), and the drive panel marks
both readings "est.". Checked in `tests/test_test_drive.py` (one more test).
Suites on MuJoCo 3.10.0: 1189 passed with a display, 1121 headless.

Not claimed: that the estimates are right at a curb - they are as they were (OPEN LW-049).

## What fails on Windows on any machine — 2026-11-12

OPEN LW-045. The quick workflow's first run failed its quick tier on Windows, and which tests only a
signed-in reader of the job's log could see. Three causes found without a Windows machine: the shared
log's helper imported `fcntl`, which Windows has not (every test that loads it failed); a test patched
`os.killpg` and named `SIGKILL`, POSIX's both; and 46 places opened a text file without naming its
encoding, which on Windows is the code page - the log's middle dots read back as other characters.
The helper locks with `msvcrt` where there is no `fcntl` (a test runs it so), the test expects
`kill()` off POSIX, and every one of the 46 names UTF-8: the quick tier passes with Python's
`EncodingWarning` as an error (`python -X warn_default_encoding -m pytest -m "not slow" -W
error::EncodingWarning`). On GitHub's runners each failed test is now also an `::error` annotation,
which the run's page shows to anyone (`tests/conftest.py`; checked in `tests/test_evidence.py`).
Suites on MuJoCo 3.10.0: 1191 passed with a display, 1123 headless.

Not claimed: that the quick tier passes on Windows - its next run on GitHub says.

## Windows' last failure, named by GitHub — 2026-11-13

OPEN LW-045. With the causes of 12 November mended (d175694), GitHub's quick run passed on Linux and
Apple silicon and wrote the one test still failing on Windows as an annotation anyone can read:
`tests/test_agent_status.py::test_truncation_resets_with_notice_and_partial_lines_wait` printed
`- replacement` with two newlines. A log written on Windows ends its lines in CR LF; the shared
log's helper printed them so, and the console's own translation doubled each. It now ends every
event it prints in a plain newline; `tests/test_agent_status.py` writes a log with CR LF lines and
reads what the helper prints as bytes (it failed before, here on Linux too). The quick tier passes
with Python's `EncodingWarning` as an error (1,058).
Suites on MuJoCo 3.10.0: 1192 passed with a display, 1124 headless.

Not claimed: that Windows passes - its next run says.

## The same start, checked — 2026-11-13

ADR 0075 (FR-041). Every sweep run keeps a fingerprint of its set-up as the program takes over - the
engine, the model with every change made to it, the joints before the first step and then, the
program, the draw - exact and rounded, and the disturbed sweep's and the recovery report check their
pairs before their statistics. The paired studies' starts, rebuilt and checked: ADR 0036 and 0051's
63 pairs (9 set-ups, 7 disturbances) and ADR 0070's 130 (the program under test) began alike, exact;
ADR 0052's slip reproduced - the payload where its own mass puts it - is flagged in 59 of 71 set-ups,
every loaded one below the heaviest payload. On the same machine with NumPy's AVX-512 paths off the
9 set-ups start the same to the bit. A fingerprint takes 15 to 23 ms. Checked in `tests/test_identity.py` (3).
Suites on MuJoCo 3.10.0: 1195 passed with a display, 1127 headless.

Not claimed: that runs which began alike ran alike; the window's test drives; the owner's Mac (OPEN LW-050).
