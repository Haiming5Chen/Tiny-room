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
