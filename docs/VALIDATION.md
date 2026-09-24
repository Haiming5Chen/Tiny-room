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
