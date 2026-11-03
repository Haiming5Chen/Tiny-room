# Architecture

Python / future editor / future AI → Blueprint → World → PhysicsBackend → MuJoCo.
The core uses only the Python standard library. Native solver handles and indices
never appear in Blueprint or State. The optional MuJoCo adapter owns compilation,
contact mechanics, integration, rendering resources, and names-to-native-ID maps.

## Representation

- Entity: identified assembly instance with a Blueprint and world transform. No Robot base class.
- Component: identified declarative part (body, hinge, motor, camera). Relationships use stable IDs.
- Geometry: shape and dimensions in metres, independent of Material.
- Material: density (kg/m³), sliding friction coefficient, display RGBA. Future
  properties need explicit units and a solver/interaction consumer before activation.
- Blueprint: versioned JSON design containing parts, parents, attachment frames,
  material references, and controller descriptors. Immutable value objects allow
  editor commands to replace a design without mutating a running model.
- State: detached observation of body poses and world-frame velocities at simulation
  time. Not a Blueprint and not a complete solver checkpoint.
- Interaction: future rule protocol over shared state; no physical rules are
  scheduled in this milestone. Future coupling must declare reads, writes, units,
  ownership, ordering, and conservation tests before it enters World.step.
- Scene: environment entity collection; no task or robot assumptions.
- Embodiment: entity/control/sensor selection, not a physical subclass.
- Task: observation/evaluation protocol independent of scene creation.
- Controller: observation-to-named-actuator command protocol; serialized configuration
  is data, never executable code imported from a Blueprint.

## Coordinates and composition

SI units; right-handed Z-up; scalar-first quaternion (w,x,y,z). Body transforms
are relative to parent body; root is relative to entity transform. Geometry is
centred on its body. Box sizes are full lengths, cylinder is radius/full length,
sphere is radius. Cylinder local Z is its axle. Hinge axis is in child body frame.
Fixed children weld through the body tree; a hinge gives its child one rotational
DOF. Dynamic roots receive free joints. Disconnected roots are allowed. Attachment
points are named local frames used by builder snapping; explicit resolved
body transforms/joints remain authoritative. Cross-entity constraints and closed
kinematic loops are unsupported and must not be silently approximated.

## Lifecycle and ownership

World starts in BUILD. Set/replace scene only in BUILD. start compiles and transfers
mechanical authority to the backend. step advances a fixed timestep, takes named
torque commands, and returns a detached State. An omitted command means zero torque
for that step. reset restores the compiled initial state and returns to BUILD;
start recompiles the current design. The Blueprint never absorbs simulated poses.
close releases backend resources. UI uses this lifecycle rather than a second world.
Compilation rejects unsupported component types and unresolved references.

The backend exposes compile, step, snapshot, reset, close. Camera capture is an
optional adapter capability, so headless mechanics does not require a GL context.
The MuJoCo viewer sits in a separate presentation module and may access native
handles; core/controller/task code may not. Backend implementations must translate
body-local solver velocities to the documented world frame.

## Material limits

MuJoCo uses sliding/torsional/rolling contact friction and soft contact parameters.
The initial material sliding coefficient maps to geom friction[0]; small fixed
rolling/torsional coefficients are adapter defaults. This is not separate static
and dynamic friction, nor a restitution/stiffness calibration. Density drives
inferred mass/inertia. Illustrative material values are not measured datasets.
Camera is optical RGB rendering, not radiative heat transport.

At equal geom priority, MuJoCo combines friction using the larger pair coefficient,
so a low-friction part alone could not impose a low-friction contact against a
higher-friction floor: the 0.01 skid slid at the floor's 0.8. That adapter policy now
exists (ADR 0010). `Material.surface` names the real surface a material stands for,
and `materials/contact_pairs.py` holds sourced dry friction for 26 pairs of 8 surfaces.
The adapter runs `mj_step` stage by stage and, between `mj_collision` and
`mj_makeConstraint`, writes each contact's tangential coefficient from that table.
Contacts between unlisted surfaces keep MuJoCo's combination. With nothing sourced
the staged step is bit-identical to `mj_step` (tested). MuJoCo receives the kinetic
coefficient; static values are recorded but there is still no stick-slip. Menagerie
robot geoms keep their upstream friction.

Axles carry no viscous damping (ADR 0011). Their losses are MuJoCo dry friction
(`frictionloss`) with the stiffest constraint settings MuJoCo accepts, so they behave
as Coulomb friction: a gearmotor's friction derived from its datasheet no-load
current, and rolling resistance b x N (`materials/rolling.py`), recomputed every step
from the load the solver found at each tread. Only wheel-shaped geoms count - a
cylinder or sphere on the hinge axis, or a ring of tread blocks around it - and only
contacts whose normal points at the axle. A sourced motor profile hands its
speed-torque line's slope to the actuator's affine bias wherever the line limits the
command, so MuJoCo's implicitfast integrator follows the line at any inertia. Ideal
drive modules, swivels and user-made hinges keep the 0.01 N m s damping.

The adapter also runs MuJoCo's noslip pass (two iterations, ADR 0017): its soft
friction otherwise lets a contact creep below its friction limit - a held cube slid out
of the gripper at 2 mm/s - and excludes contacts between adjacent links of registered
robot models, which MuJoCo's parent filter skips when the parent is welded to the world.

Controllers use the same mechanism for their own damping (ADR 0014). A command may be
a `core.command.Torque`: a float that also carries its slope with respect to joint
speed. The position controller returns `Torque(command, -kd)` below its limit and the
plain limit at it; every kit motor has an affine bias that is zero unless a step gives
it a slope, so the force is the command at the speed it was computed for and follows
the speed implicitly within the step. Backends that cannot integrate implicitly treat
a Torque as the float it is.

The inspection UI uses GLFW input and MuJoCo's renderer directly. It deliberately
does not install the simulate application's shortcut handler: otherwise drive keys
also toggle rendering options. This reuses solver/rendering capabilities without
building a graphical construction editor. The UI's wheel-speed feedback generates
bounded named motor torques; it never assigns body poses or velocities. The core
and headless direct-torque API are unchanged.

## Test drive

Simulating a machine is a test drive (ADR 0012). `control/drive_telemetry.py` reads
MuJoCo state the physics has already computed - the machine's centre of mass, forward
speed, tilt, each drive motor's speed, torque, available torque and wheel slip, and
contacts with other bodies - as ideal sensors. `control/run_log.py` (standard library)
accumulates those samples into a run summary. The workshop's `TestDrive` mixin owns
the presentation only: a chase view on MuJoCo's free camera, kept in front of walls
with `mj_ray`; the Drive tab with live readings; the path drawn as decor lines; an
inset rendered from the machine's own camera; and after Stop a report compared with
the previous run. None of it is written to the Blueprint; an edit clears the report.

Where the test happens is a test field (ADR 0013, `little_world/fields/`): ordinary
Blueprint entities authored in the machine's start frame - so the design never moves -
plus goals judged from the core `State` alone (`fields/goals.py`, standard library):
lines crossed in order, zones reached or objects delivered at rest, staying upright,
leaving obstacles undisturbed. `Scene.backdrop` is an appearance hint ('sky') that the
MuJoCo adapter turns into a gradient skybox and a directional sun.

What the machine is made of is read from the Blueprint alone (ADR 0015,
`construction/structure.py`, standard library): modules are catalog parts as inserted,
with roles from the catalog, masses from geometry and density, and the keys bound to
their motors. The same module computes how the rigid design settles on a level floor -
which parts carry it, its tilt and its stance margin - and the drive telemetry measures
that margin from the simulator's supporting contacts during the run.

An arm's tool can be moved instead of its joints (ADR 0016, `control/tool_motion.py`,
MuJoCo-bound like the keyboard binding it drives): the tool module's point, the
keyboard-bound joints between it and the machine, and a Levenberg-Marquardt solve on a
scratch copy of the state whose result becomes joint targets for the same servos. A step
of the tool is solved along its straight line every 2 mm and handed out as the tool
travels it (`ToolMotion.glide`, `advance`, ADR 0045); held keys carry the tool's target
step by step (`ToolMotion.drive`); the window ticks the tool each physics step
(`KeyBindings.tick_tool`). Programs carry `pose` and `grasp` blocks as data (`programming/program.py`, version 2
when used); `programming/execution.py` hands a runner's output to a position controller
the same way in the window, in inventory trials and headless. A pose may carry the point
its tool was aimed at; a runner given the arm's aim (`ToolMotion.aim`) checks where the
tool got to once the pose settles and solves it again for where the machine now stands
(ADR 0025). A runner also remembers the stop its last drive-to reached: an aimed pose
settling more than 2 cm from it sends the program back - the pose it drove in, a run-up
behind the stop, the stop - once per run (ADR 0031).

A base with a left and a right drive wheel can be driven to a point (ADR 0018):
`control/navigation.py` turns the axle midpoint's pose into a forward speed and a turn
rate (standard library; `BasePose` reads the pose from MuJoCo as an ideal observation)
and those into wheel speeds for the same drive controller the keyboard uses. The runner
owns one controller per `goto` block, so its hysteresis lives with the block.

A field can move and can be fitted to the machine (ADR 0020). `Field.actuate` maps a
`State` to torque commands for the field's own motors - the tilt table's hinge - which
the loop steps beside the machine's; `Field.fitted` hands `build` the machine's
Blueprint, so the table's trip rail is set against whatever the machine has lowest on its
right. Tip angles are the stance module's own rocking on a tilted floor
(`construction/structure.py`, `_rest` with gravity leaning off the floor's normal), found
by bisection per side. A field with a `reading` (State -> degrees, up to `gauge_top`) is a
static test: the test drive shows the reading on a gauge against the stance's prediction
for the field's `side`, and `ground` names the field bodies telemetry treats as floor.

A run can be repeated with variations (ADR 0024). `fields/variation.py` (standard library)
makes them data: the start pose and a payload are Blueprint edits - the payload a steel
block set down on the highest rigid part of the base under its site and fixed to it - and
friction is a table of pair coefficients, each sourced pair moved across the range its own
note cites (`materials/contact_pairs.SPREADS`), which the backend applies as a condition of
the run, never of the design (`MujocoBackend.vary_pair_friction`). `inventory/sweep.py` runs
a field over a plan - each variation alone at both ends of its range, then seeded random
repeats - with one of three protocols (hold still, drive straight ahead, or the field's
program template solved once for the design on its mark), in worker processes, and reports
each goal's spread; it is also a command (`python -m little_world.inventory.sweep`). The run
report starts it in another Python process (`ui/varied_runs.py`), so the window stays live.
A sweep's rates come from its random repeats only, with exact binomial bounds from
`inventory/confidence.py` (standard library, ADR 0028). A field can stand the machine square
before it starts (`Field.squared`, the tilt table, ADR 0029); its sweeps then leave turning
out (`sweep.ranges_for`). `fields/disturbance.py` (standard library, ADR 0030) describes what
happens partway through a run - a push on the machine's base, a loose part moved - and when;
the adapter applies it (`MujocoBackend.push`, `MujocoBackend.shift`), and `sweep.disturb`
runs the design and its drawn set-ups undisturbed and under each disturbance. The run report
starts those too (`ui/disturbed_runs.py`, sharing the process handling of `ui/varied_runs.py`).
Each drawn set-up is a pair - its two runs are one run until the event, which `sweep.run`'s
`trace` shows step by step and `Run.event` dates - and `sweep.summaries` counts what the event
broke and rescued, tested exactly by `confidence.mcnemar` (ADR 0036). Every sweep records the
seed its set-ups were drawn with; `inventory/holdout.py` (standard library, ADR 0049) keeps the
ledger of seeds decisions were tuned or judged on (`docs/sweeps/seeds.jsonl`), lets `sweep
--holdout` draw only with a seed the ledger has not seen for the field - entered before the run -
and reads a held-out sweep beside its tuning sweep. `MujocoBackend.contact_census` counts the
contact points between each pair of bodies at an instant, as the model is set and with multiccd
on, both on copies of the instant; `inventory/census.py` (ADR 0050) takes it at the moments a
Fetch run's results are decided, through a sweep run's `probe`, which is handed every step. The
runner's recovery is a choice (`Runner(recovery=)`: its own `look`, or the baselines `retreat`,
`guess` and `none`); `sweep --disturb --recovery` runs one, and `inventory/recovery.py` (ADR 0051)
reads it beside the program's own, pair by pair. An alarm from outside (`Runner.alarm`) makes a
program that looked recover as its own recovery does, while `Runner.listening()` says it would; the
recovery `ignore` lets the checks fire with nothing coming of them. A sweep run takes an alarm at a
time and records when the program recovered and the spans it listened; `inventory/branch.py` (ADR
0052) branches a failing run by running it again with an alarm every 0.5 s - deterministic, so
each branch is its parent until the alarm - for the window in which a recovery still rescues it,
and alarms one set-up after another that needed none, for what a false alarm costs.
`control/latency.py` (standard library) holds how late a program's pictures, servo commands and
readings are, from their sources - the camera's frame interval, the finder's time, a Dynamixel bus's
packets at its defaults - and `Lag`, which holds commands and readings back step by step; a sweep run
with a `latency` hands the program the camera of `perception.eye.Late`, which shows the world as it
was through `MujocoBackend.kept` and `as_it_was` (MuJoCo's ray casting on poses kept from then, on an
MjData of its own). `inventory/margin.py` (ADR 0053) reads sweeps at each latency against the sweep
without. `inventory/falsify.py` (ADR 0054) is a compass search over the variation box for a run's
margin - for Fetch against what the tuning draws certified, for the tilt table degrees past its last
hold; measured against the draws, it was not adopted, and only that study calls it.

A field can have a camera of its own that programs look with (ADR 0032). `Field.camera`
names a Blueprint camera in the field and its sensor, whose numbers are in
`perception/sensors.py` (standard library). The adapter casts a camera's pixels as rays
(`MujocoBackend.cast`, MuJoCo's `mj_multiRay`: no GL context) and reports its pose
(`camera_pose`). `perception/eye.py` takes a picture of the region round where a part was
planned and adds the sensor's noise; `perception/boxes.py` (numpy) finds a known box in it -
support plane, clusters standing on it, top face laid back along its rays and fitted - and
never reads the simulator's pose of the part. A `look` block (program version 3) hands the
runner a `see` callback's sightings; once three in a row agree, the poses at that stop aimed
near the part aim where it was seen (`Runner.aimed`). Before a pose reaching for the part, the
runner takes one more picture; a part moved, a reach that cannot settle or a grasp that holds
nothing sends it back to the stop's approach to look again, once (`Runner.regrasp`, ADR 0033) -
from a reach that went down, first back up to the pose it reached from (`Runner.above`). A
picture that finds nothing asks the camera what it shows where the part was seen
(`Eye.place`, `boxes.place`: the depth the part's shape would give against the depth
measured - there, empty or hidden), and only empty looks again (ADR 0037). A disturbance can
fail the field's camera (`Eye.fail`: frozen on its last frame, or dark); each picture carries a
frame number, when it was taken and the share of it with depth, and the runner ends a look on
three in a row that are not new or are dark, naming the camera (`Runner.trouble`, ADR 0038).
`MujocoBackend.move_camera` sets a camera off the pose it was built at; an `Eye` given a
`believed` pose casts from the camera as it stands and reads the picture as if it stood
there, and `perception/calibration.py` says in closed form where a point is then seen
(`sweep --camera-error`, ADR 0039). `MujocoBackend.contact_forces` gives the forces on a body
by what touches it; `inventory/handling.py` follows the parts a field's goals carry through
each run - pushes by partner, lean, fall - into `Run.handled` and the reports (ADR 0040). `sweep.run` records each look with where the part really was, for the reports; the
program workspace draws the last picture through the canvas (`Canvas.pixels`). A `goto` may
name the object it drives to (program version 4): once a look has seen the object, the stop
moves as it did, along the stop's heading at most `secondary` metres (`Runner.follow`), and
a stop that followed is the one going back returns to; a look's `secondary` widens the
camera's search round its plan. `ToolMotion.aim` answers False for a point out of reach, and
a pose re-aimed there fails before it moves; `tool_motion._clear_ahead` measures how far a
machine at a stop could drive on before it meets a part fixed to the world (ADR 0035).

## Frontier radar

`little_world/radar/` (ADR 0021, standard library) is not part of the simulator: it reads
the project's documents, never its designs. `items.py` parses each feed into one `Item`
shape; `profile.py` makes topics of the decision records, the roadmap's next steps and
`docs/radar/profile.md`; `score.py` files items under topics by tf-idf cosine over stems
and word pairs, with the matched words as the reason; `store.py` keeps items and verdicts
in one SQLite file; `digest.py` writes the Markdown page; `fetch.py` holds the feeds and
the polite HTTP client; `brief.py` (ADR 0026) reads the proposals in
`docs/agents/FRONTIER.md` and writes the radar's section of that file between two markers,
leaving the rest to the agents. `collection.py` (ADR 0034) keeps what was filed or judged
in `docs/radar/collection.jsonl`, one sorted line an entry that merges line by line, and
moves it to and from a store; `search.py` searches it by the same tf-idf cosine mixed equally with a
latent-semantic one (ADR 0062; words alone when asked) - numpy, the radar's only module outside the standard library,
imported only by the `search` and `related` commands. See docs/RADAR.md.

## Interactive construction

`construction.AssemblyEditor` owns immutable Blueprint revisions, selection and
undo/redo. It imports no solver/UI packages and can be used programmatically.
`World.preview()` compiles the design for inspection while preserving BUILD mode;
`step()` remains forbidden there. The workshop applies edits only in BUILD,
recompiles the preview, and rolls back on invalid edits. Starting simulation uses
World.start and stopping uses World.reset, with no design mutation.

The panel and picking code live in `ui/workshop.py`; the furnished room lives in
`scenes/workshop.py`. Motor controllers are named Blueprint descriptors. The initial
workshop recognizes exactly a two-channel differential_torque descriptor and sends
bounded physical torques. It does not execute imported code from a saved design.

### Responsive presentation and prepared scenes

World remembers the last successfully prepared immutable Scene. Repeated preview,
start and stop reuse it; a changed design recompiles before use. MuJoCoBackend
caches immutable observations only for bodies whose weld ID is world (zero),
invalidating that cache on compilation/close. Dynamic assemblies remain fresh.

The workshop retains its MjrContext/MjvScene because the current adapter supports
primitive shapes and a fixed texture registry for kit models. Registered mesh assemblies
use model-specific context invalidation and separate preview contexts (see below).
`ui/canvas.py` rasterizes a font atlas once with Pillow and batches rectangles/text
through OpenGL. Graphics calls and edits stay on the window thread. UI activity
wakes a capped idle loop; physics uses the original fixed timestep independently
of the rendering target rate. No physics parameters were changed for responsiveness.

## Built-in asset registry

The component catalog produces namespaced, editable Blueprints, not opaque native
objects. Material adds optional texture ID and roughness appearance parameters.
The MuJoCo adapter registers five deterministic RGB textures in the same order for
every model, allowing the retained graphics context to be shared with cached catalog
previews. Selection uses decorative edge geometry instead of replacing surface color.
All texture files come from the packaged registry; Blueprint data cannot load
arbitrary paths or URLs. Physical contact geometry stays independent of appearance.
See CATALOG.md and the asset SOURCES.json for boundaries and provenance.


## Precise connections and hinges

The construction layer resolves source/target attachment frames into a child-local
pose and parent reference. Generated primitive frames provide six face/tangent
centres; explicit Attachment frames override names. Opposing local Z normals define
the mating rotation. No persistent relationship is inferred after a snap.

Hinge adds optional child-local `position` (metres) and `limits` (lower/upper degrees).
Defaults preserve legacy origin pivots and unrestricted rotation. The backend uses
MuJoCo's native pivot, damping and joint limits; no additional constraint solver.
The catalog arm now pivots at its mounting end. Fixed conversion removes dependent
motors/controllers atomically. UI forms isolate keyboard input and apply one undo
revision; construction APIs stay independent of graphics and solver packages.


## Detailed hardware observation and rendering

Detailed assemblies expose hundreds of editable subparts. Backend snapshots detach
all poses and velocities in batches; core `DeferredBodyStates` owns immutable Python
tuples and constructs a BodyState on access. No retained snapshot reads changing
native arrays. World-frame body-inertial velocities use the same subtree-COM
translation as MuJoCo's objectVelocity, with zero velocity for world-welded bodies.

After integration, the adapter refreshes kinematics, COM positions, cameras/lights
and COM velocities. It does not perform a redundant second collision/constraint
solve. The next native step performs its usual complete dynamics computation.
Pose/velocity/camera output is checked against a full forward refresh. Native force
and contact work arrays are solver internals, not part of the public State contract.

The focused workbench renders only the assembly and selected component, with no
hidden room render. It reuses the compiled world model and separates the room using
visual geom groups; the normal room view still includes both groups. Its floorless previews omit shadows. Room shadows use a 1024px
map. See ADR 0004 for ownership and the explicit hardware capability boundaries.


## Assembly management

The workbench's collapsible tree is a view of Body.parent; expansion, camera focus
and component/detail picking do not alter Blueprint data. Component picking uses
catalog root names/attachment markers and falls back to detailed body selection
for ungrouped older designs. The editor's shared subtree closure includes bodies,
hinges, cameras and dependent motors. Duplicate remaps every internal ID/reference,
keeps the copied root's original parent, applies a parent-frame offset, and copies
only fully contained controller descriptors. Duplicate and delete are atomic undo
revisions. No native solver types enter these construction operations.

## Interactive socket docking

MuJoCo continues to own collision, contact and motion. The builder adds a pure
Python docking policy over existing catalog parts and attachment frames; it does
not add a physics solver. Compatible slots, occupied slots and refusal reasons are
computed before committing. Drag previews only add presentation geometry; release
makes one immutable editor revision. Named tool/output frames use existing mating
math. These are simulator kit compatibility rules, not verified vendor mounting
specifications. Low-level precision connections remain available for custom parts.
Wheel insertion releases the selected assembly root and raises it if necessary to
clear the floor. Explicit base preparation can also ground or anchor an assembly.
These edits affect initial design poses only; runtime poses remain solver-owned.

The immersive build stage reuses the same MuJoCo scene and editor. Its floor/grid
are decorative render geometry only, excluded from physics and serialization.
Parts/details panels and camera presets change presentation state only. Socket
labels are contextual during dragging, or can be explicitly pinned with Sockets.

## Component replacement and removal

The existing immutable editor and MuJoCo backend remain responsible for design
transactions and physical behavior. Component lifecycle adds a construction policy,
not a new simulator. Optional Body.catalog_part records catalog provenance on module
roots while retaining old JSON defaults. Compatible replacements preserve IDs and
controller references; external children are retained on matching named sockets or
shifted with the changed structural face. Unsupported topology changes are refused.
Single-component removal refuses to orphan attached modules. An explicitly reviewed
branch removal deletes descendants and dependent controls as one undo revision.

## Mechanical kit usability

Manufacturer assembly guides motivate distinct complete assemblies and individual
components, discoverable rotating outputs, and multiple chassis mounting positions.
These remain original procedural kit models; vendor mounting fits are not claimed.
No new physics solver is needed: shaft loads weld to the motor's existing output
body, and multiple differential wheel pairs use existing MuJoCo hinges and motors.
Builder-side wheel spacing checks prevent overlapping adjacent wheels. Outward
wheel frames and their hinge axes are resolved together so both sides retain the
same forward-drive convention. The UI explains purpose, attachment and limitations.

## Assisted construction and Python authoring

Use existing MuJoCo joint/contact dynamics. Continuous side mounting is a builder
policy: named sockets remain presets, while a wheel's longitudinal coordinate can
be specified in metres with spacing validation. There is no hard-coded wheel count.
Defaults create editable keyboard actions for articulated modules. Drive assistance
maps side commands to all registered motors with per-wheel speed feedback, torque
caps and acceleration limits; it is not a vehicle stability or automotive ECU model.

The Python window uses the same AssemblyEditor/Blueprint APIs as direct manipulation.
A worker process runs user-authored Python, returns serialized Blueprint data, and
is terminated on timeout. This isolation keeps the UI responsive and makes failed
builds atomic; it is not a security sandbox for untrusted Python. Successful designs
are applied as one undoable editor revision. Scripts are saved separately from JSON
and are never executed merely by loading a design.

Drive descriptors retain legacy two-motor compatibility. Explicit `drive_sides`
allows an unmatched additional motor to join the same side command; pairing is
recomputed when more wheels arrive. `DriveSettings` is saved with the design.
The native adapter observes each wheel and the base's local velocity, converts
side intent to a linear target, ramps that target, compensates for wheel radius,
and clamps each feedback torque to its individual configured fraction. A simple
excess-wheel-speed limiter reduces accelerating torque; it is not a calibrated
slip estimator and has no battery/power-bus model. Benchmarks use the same adapter.

Default keyboard bindings are assigned only to newly inserted articulated modules,
so deleting or changing a binding is not undone by an unrelated subsequent edit.
Preferred semantic keys are used first; additional modules receive unused pairs.

## Ready-to-build catalog

The default catalog presents complete mechanical assemblies and useful structural
parts. Raw actuators, shaft loads and small hardware remain in Advanced for older
designs and expert authoring. Ready bases and arm/gripper kits compose the existing
Blueprints; new attachments use native hinges, motors and cameras. There is no new
solver or opaque asset format. Assembly insertion includes default controls in the
same undo transaction and all internal parts remain inspectable.

## Registered real robot assemblies

MuJoCo Menagerie already supplies meshes, inertias, joint limits, contact geometry,
actuators and gripper constraints. Preserve these via MuJoCo's MjSpec attachment;
do not rebuild them with primitive geometry or implement another solver. The builder's
contribution is mounting, saved assembly references and explicit keyboard actions.
Body.robot_asset identifies a bundled, version-pinned model; no arbitrary XML paths
or code are accepted from designs. Its box is a selection/bounds proxy only, not
physical geometry. RobotServo names a registered position actuator on that body.
Blueprint remains stdlib-only and serializable. Native joints and meshes stay in the
adapter. Model internals and size are fixed in this first asset integration; whole
assemblies can be mounted, moved, duplicated, deleted and saved.

Position servo commands use the upstream actuator's native target units, unlike
Motor torque commands. Omitted servo commands retain their target; reset restores
both home pose and targets. Existing torque behavior is unchanged. Keyboard/Program
controls increment position targets and preserve upstream force caps. Gripper keys
control the original tendon actuator and finger equality constraint.

Resource-bearing models require model-specific render contexts. Rebuild the main
context after mesh model changes, and give mesh previews their own context. Never
reuse primitive preview mesh indices against another model's GPU resources.

## Robots from their own files

`physics/importer.py` (MuJoCo-bound, ADR 0044) turns a URDF or MJCF file into a registered
robot. MuJoCo's own readers parse it and `MjSpec` edits, compiles and writes it; the importer
adds only what driving needs - position servos sized from the robot's weight and inertia, mimic
joints as equalities, one body per link, visual shapes kept and collision shapes hidden behind
them, links overlapping at the home pose excluded from colliding - and reports it in plain
words. `assets/robot_library.py` (standard library) keeps the results outside the repository,
one folder per robot that is never rewritten (`$LITTLE_WORLD_ROBOTS`, else the platform's
application-data folder), and names them `user:<name>`. Designs carry the name, never a path:
the core accepts the pattern, `robot_models` resolves it, and the backend attaches a library
model exactly as it attaches a Menagerie arm. A servo's unit - 'deg', 'mm', or a gripper's
'%' - goes from `robot_models.units` through the backend (`servo_units`) to the keyboard control
and the block programs. A gripper found at import (ADR 0047) is metadata of the robot - its
channel, its open and closed positions, its two jaws: `robot_models.grip` maps its closure to its
control, the backend names its jaws (`robot_jaws`) and `Observations` counts both of them on a
movable object as held. Tests each run with an empty library.

## Lessons the app checks

`lessons.py` (standard library, ADR 0046) holds the first hour as data: each lesson a goal,
steps, a set-up name and a check over `Facts` - what a workspace can say about the work: the
field and its goals, the tool's distance from the cube, the program and how its run ended, the
Joint lab's robot and how far its joints moved, the last repeats with variations. The window's
`LessonsPanel` (`ui/lessons_panel.py`) gathers the facts of the active workspace each frame and
finishes every lesson whose check passes; one `Progress` lives on the window's host, kept in a
JSON file beside the robot library (`$LITTLE_WORLD_PROGRESS` in tests). A lesson's set-up uses
only the actions a user has: loading a kit, choosing a field, simulating, opening a panel.

## Recent work in the window

`ui/whats_new.py` (ADR 0055) is the Guide's What's new: demonstrations as data - a title, what
happens, what to watch for, the Fetch field's disturbance to arm - and `start_demo`, which loads the
kit's mobile manipulator, chooses the Fetch field, solves the Fetch program, arms the disturbance,
runs the program and turns the view to the table, through the window's own actions.
`ui/live_disturbance.py` applies an armed disturbance during a run: the sweeps' `Disturbing`
(ADR 0030), ticked each physics step from `field_commands` with the window's goal clock, a camera
fault given to the program's own `Eye`; it is made afresh for each run. The Program panel's Look
again calls `Runner.alarm` (ADR 0052), enabled while `Runner.listening`, and `senses` puts the
runner's last sighting or camera fault and `control.feel.read`'s jaw registers into two lines.

## The grasp a program feels

`control/feel.py` (standard library, ADR 0048) reads a kit gripper's jaws as ROBOTIS XH430-W350
servos: from each jaw's torque, angle, goal and speed, the registers a real one reports - Present
Position, Present Velocity, Present Current and the Moving flag - rounded as they count.
`holding` says the jaws hold something when both are still, stopped short of their goal and
pushing towards it. `programming/execution.held_now` gives a program its grasp from that wherever
programs run - the window, the benchmark, sweeps; a registered model's own gripper servo is not
read this way and keeps the contacts (`Observations.grasped`). The contacts stay the judge: each
grasp check records what was felt and what was so (`Run.felt`), and sweep reports count them.

## Spatial drag preview and library styles

Real robots and Anime / kit are catalog views over one shared Blueprint format;
switching tabs never converts or replaces the current design. Both styles can be
combined in a build. Real models preserve their source mechanics and remain clearly
identified; Anime / kit contains the original stylized editable assemblies.

Dragging uses a temporary MuJoCo model containing the current assembly and a ghost
module, with its own mesh upload context. Compile once per drag; mouse movement only
updates the ghost's root pose and forward kinematics. This is presentation state,
never a running physics edit. Unproject the cursor onto the ground for free placement,
or use the same socket transform for preview and commit. Drop is one editor revision;
cancel frees temporary resources and leaves Blueprint unchanged.

## Laboratory and industrial equipment

Lab equipment composes existing Blueprint bodies, native hinges, motors and cameras.
No new solver or electrical/industrial automation model is introduced. Mobile bases
reuse radius-aware differential drive; stationary tables/pedestals are anchored by
default. Passive conveyors contain individual freely rotating rollers. The indexing
table uses a bounded rotary hinge. Generic engineering layouts are distinct from
sourced robot assets; neither appearance nor assembly status establishes payload or
manufacturer compatibility. Complete workcells compose the same separately available
platform/table and Panda module; insertion and default controls remain atomic.

The second equipment collection reuses those same interfaces: a bounded horizontal
hinge powers a tilting table; inspection and sourced-arm workcells compose existing
modules. No prismatic joints or lift mechanics are implied. Storage fixtures and
test objects are ordinary rigid bodies with explicit anchored/free placement.

## Click-to-jog operation

The operation panel shares the existing native joint controller. Button presses
increment held targets in degrees (or percentage gripper closure), using actuator
ranges and existing sourced servos. No teleportation, inverse kinematics or saved
Blueprint edits are introduced. The first click starts physics; manual actions
stop a running program and clear its key state. The gripper remains visible across
joint pages. Pause freezes the world; stopping simulation restores the saved design.

## First automated factory cell

MuJoCo already supplies rigid contact, native actuators, forward kinematics and
Jacobians. The factory prototype wraps these rather than adding another solver:
a Panda-specific damped least-squares IK adapter plans top-down waypoints using
scratch native data, then commands the existing force-limited servos. Workcell
geometry and products remain ordinary Entity/Blueprint data. The unique work is
connecting a product/destination recipe to observable, failure-aware task stages.
Known-object sensing reads simulator state and is explicitly not image detection.
Grasps use physical finger contact, never welds or object teleportation. A fixed
workcell demo launches separately so the builder's unsaved design is preserved.
It is not yet a general collision-avoiding planner, editable line, or conveyor system.

`factory/process.py` (standard library, ADR 0056) judges a cell as a factory does: a run's
`Placement`s - each part from its slot's centre, turned from square, and its cycle - against the
room the destination tray's slots give a part (`slot_room`), with Cpk per axis and its interval
(`capability`), the tightest zone held (`tightest`) and a takt. `FactoryCycle.left` reads each part
once its placement is checked; `FactoryCycle.feeder` puts each part on the input tray off its centre
for a study; the factory panel shows `process.line` under a production run. The cell's vertical
stages carry joint solutions a centimetre apart along their line (`Stage.path`, `FactoryCycle.along`,
ADR 0057) and the hand opens 8 mm past the part to let go (`release_grip`).

A motor can be weakened during a run (ADR 0058): `MotorProfile.weakened` (core) scales a motor's
own speed-torque line and keeps its friction; `MujocoBackend.weaken` swaps a motor's profile until
the world resets; `fields/disturbance.py`'s 'motor' kind does it on a disturbance's trigger.
`MujocoBackend.motor_line` gives the line a motor follows now and the one it was built with; the drive
telemetry reads a motor's speed and torque against the first and marks it weakened (`MotorSample.kept`).

How near a contact is to sliding (ADR 0061): `MujocoBackend.friction_use(body)` gives each of a body's
contacts' normal force and the friction it uses, as its cone measures it (pyramidal: each frictional
force over its coefficient, summed); `inventory/handling.grip_use` makes a grip's share of it, for a part
only the machine touches; `Runner.carrying` and `Run.grip` follow it while a program carries what it
holds. `MujocoBackend.scale_mass` makes a body heavier for a run (`run(masses=...)`), undone by a reset.

`inventory/stages.py` (ADR 0063, standard library) reads where a group of runs failed: how many met each
goal and every goal before it, the first goal each missed, and - from `Run.stopped`, the block a program
gave up at - what it was doing; a table for the sweep reports, two short lines for the panels.
`inventory/power.py` (ADR 0064, standard library) is the power of the sweeps' own tests, computed
exactly: the exact McNemar test's for paired runs, the draws a bound on a rate needs.

`control/tipping.py` (ADR 0059) is the force-angle measure: `force_angles`, `measure` and `ordered`
over a support polygon, numpy only, and `Watch`, which reads a machine's mass, centre of mass,
acceleration and rate of change of angular momentum (over 50 ms) and its support - its geoms within
1 cm of what it stands on - from the solver. `DriveTelemetry` keeps one; `DriveSample.tip` and
`RunSummary.min_tip` carry it to the drive panel and the run report.

## Guided factory authoring

Create's Ponder inspires contextual explanations and visible cause/effect, not a
Minecraft dependency or copied assets. The factory gains a portable cell recipe
(tray positions, source, destination, product), authored directly in the scene.
Placement validates table bounds, tray overlap and fixed obstructions separately
from IK reachability. Drag ghosts are presentation-only; release commits one
undoable recipe change and rebuilds ordinary Blueprint geometry. Recipes persist
separately from robot designs. Guided explanations pause the real task controller
at stage boundaries, so a failed grasp remains a failure rather than an animation
that implies successful physics. Existing MuJoCo IK/contact remains the executor.

## One window, two workflows

Real and Anime are application workspaces, not catalog appearance filters. A single
GLFW window/event loop hosts two lazily created workspace controllers, each with
its own Blueprint/recipe, native world, camera, program and graphics resources.
Switching pauses the outgoing simulation, clears transient input and retains its
unsaved data and runtime state. Callbacks route to the active workspace; shutdown
releases both worlds before destroying the one window. No subprocess is launched.
Real exposes experiments and programming for registered arms; Anime exposes kit
construction. Panda pick-and-place is separate from the general joint/program lab.

## Visual position teaching

MuJoCo already provides forward kinematics and Jacobians; reuse the existing Panda
scratch-data IK adapter and native position servos. The new contribution is direct
3D target authoring, named portable positions, and explicit preview/move feedback.
TeachingBook is immutable stdlib-only JSON, separate from Blueprint and runtime.
The first version fixes the hand orientation downward and checks joint reachability;
it does not plan collision-free paths. Preview never changes live physics. Motion
uses bounded interpolated servo targets and reports failure if the hand does not
arrive. No new solver, dependency, or geometry format is introduced.

## Reviewable factory edits

Existing scene systems (OpenUSD, Isaac Sim) and planning scenes (MoveIt) motivate
shared data, explicit diffs and separate validation levels; see AI_AUTHORING.md.
Wrap the existing immutable CellRecipe and Blueprint scene builder, not a new
solver. A stdlib-only request describes allowed cell operations against a precise
base recipe and edit revision. Preview constructs a fully validated candidate;
apply checks freshness and uses the same undoable transaction as direct edits.
This is the communication boundary for future AI/code authorship; natural language
and arbitrary factory generation are not connected yet. No solver handles or
executable request content enter the portable document.

## Semantic agent testing

Reuse the existing UI commands, immutable recipes, MuJoCo runtime and pytest; do
not implement a shadow editor or second physics system. A test-only semantic driver
exposes labeled controls, form fields, recipe revisions, proposal state and physical
observations as JSON. Agents supply allowlisted data actions, never eval or code.
Scenario execution creates an isolated temporary cell and a test window, records
per-step state and failures, and closes it. It does not attach to a user's unsaved
app or use personal saved designs. This interface tests behavior without pixel
recognition; visual appearance still requires separate visual review. No AI model
or language comprehension is implied by replaying agent-authored scenarios.

## Shared factory scene document

OpenUSD/Isaac Sim already address scene composition; reuse their architectural
principle (stable objects and shared assets), not another physics solver. Extend
our existing stdlib Blueprint/Entity/Scene representation with a portable authoring
document. Embed machine Blueprints once per asset, reference them from named
stations, and store world transforms explicitly. Process links are authored intent
only and do not imply implemented conveyors, grasp planning or production physics.
A revision-aware document editor previews diffs and atomically applies/undoes edits.
Compiled runtime is still an ordinary Scene consumed by the existing backend.
This first layer is a Python/data API; the fixed-cell UI is not silently migrated.

## Interactive station layouts

Reuse the shared FactoryDocument/FactoryEditor and existing MuJoCo rendering in a
third cached controller within the same GLFW window. The Real workspace exposes
Robot lab and Factory layout views; Anime remains the machine builder. Layout
editing compiles candidate scenes before committing editor/history state. Dragging
translates render geometry only; release creates one authored transaction. Saved
Blueprints and the current Anime design are copied into document assets explicitly.
This view authors layouts; process links are visual intent and do not run a line.
