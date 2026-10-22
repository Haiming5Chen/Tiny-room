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
