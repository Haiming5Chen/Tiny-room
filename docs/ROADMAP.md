# Roadmap

0. Architecture: vision, boundaries, source/license register, schema and lifecycle
   contracts; unit tests using a fake backend before mechanical implementation.
1. Mechanical construction: MjSpec adapter, room and primitives, Blueprint-built
   two-wheel robot, two torque motors, camera capture, inspection viewer and drive
   controls. Accept when JSON roundtrips, invalid graphs fail before compilation,
   reset is repeatable, gravity/contact work, motor inputs move/turn the robot,
   and camera yields RGB. GUI inspection remains a separate manual smoke check.
2. Ecosystem: select one external embodiment/asset; record exact upstream revision,
   license and transformations; wrap without leaking task or native assumptions.
3. Materials/states: measured parameters and explicitly supported observable state;
   no decorative state fields presented as simulated physics.
4. Coupling: one validated causal chain (e.g. wetness → friction), explicit solver
   ownership and exchange schedule; then thermal/fluid extensions with conservation
   and calibration tests.
5. Interactive builder: place/connect/configure/duplicate/save/load via Blueprint
   operations; compile while paused; run and reset without corrupting design.
6. AI/world-model research: same construction and observations; separable tasks,
   capability checks, causal prediction and redesign evaluation.

Do not advance a phase solely because an interface has been reserved for it.

## Current sequence adjustment

Mechanical milestone and control correction are complete. The next delivered slice
brings forward part of phase 5: an interactive workshop with Blueprint editing,
materials/motor configuration, save/load, and build/simulate/return. This follows
user feedback that driving the supplied robot did not yet express the intended
experience. See ADR 0002. Ecosystem imports and advanced physics remain deferred;
a full construction-game editor is still larger than this first workshop slice.


The workshop now includes a 22-module procedural component catalog, independent
3D previews, selectable mounting faces and visible surface textures. Poly Haven
wood assets are tracked in THIRD_PARTY.md and the asset manifest. This is a first
library, not completion of the external embodiment milestone. Precise face/frame
snapping, numeric geometry/pose editing and explicit joint setup are now delivered.
Next realism work should validate one accurately modeled assembly against measured
mass, motor and contact properties before expanding its claims.


The focused Robot Workbench and 14 engineering-style hardware modules are delivered,
including a composed mobile platform. Vendor CAD import and measured hardware
calibration remain the next realism milestone. Detailed primitive compounds do
not satisfy that milestone by their visual appearance alone.


Workbench assembly management now includes a collapsible hierarchy, component/detail
picking, subtree focus, duplication with independent joints/actuators, and direct
undo/redo/delete. Reusable user-authored module libraries and multi-robot controller
selection remain future extensions; vendor calibration remains a separate milestone.


Phase 3 has started with contact friction (ADR 0010): friction is now a sourced
property of a pair of surfaces rather than max() of two illustrative numbers, with a
cited table, confidence labels and a generated reference page. Rolling resistance
and gearmotor losses followed (ADR 0011): the kit gearmotor is a Pololu 37D from its
datasheet, with gearbox friction from its no-load current, and wheels carry b x N
from their measured load. Next in phase 3: elliptic friction cones, which would let
MuJoCo's own rolling friction replace the hinge policy and reach loose rolling bodies,
and a sourced rotor inertia. The per-contact hook that applies the pair table is also
where phase 4's first causal chain (surface wetness -> pair friction) enters.

The builder's test step is now a test drive (ADR 0012): a chase view, live telemetry
with the motors' sourced limits, the path on the floor, the machine's own camera, and
a run report compared with the previous run. Seven test fields with goals judged
from the simulator state followed (ADR 0013). Checking whether an arm on a wheeled
base stands found that it could not stand still: servo damping applied a step late
made every kit arm chatter once disturbed, now integrated by the solver (ADR 0014).
Machines now read as modules with roles, and their stance is predicted before a run
and measured during it (ADR 0015). Arms now move their tool rather than single joints,
programs hold taught poses and grasp checks, and a pick-and-place program solved for the
built arm meets the Pick and place field's goals (ADR 0016). Programs drive a base to a
point, and the mobile manipulator fetches a cube from a table into a bin by itself in the
Fetch field (ADR 0018) - which exposed and fixed grasp creep (ADR 0017). The factory
cell runs production: part after part into slots, with throughput counted, and robots in
the joint lab move their hand in straight steps (ADR 0019). A doorway asks a machine to
turn where it matters, and a tilt table measures where it tips against the angle its design
predicts (ADR 0020). A frontier radar files new papers, models and MuJoCo's own changes
under the decisions they could change (ADR 0021, docs/RADAR.md); its first run found this
project eleven MuJoCo releases behind, and a trial of the newest moved three wheel-contact
results; the three are understood (ADR 0022) and the suite passes on the newest release.
The example machines now start on the floor instead of falling 4.3 cm as a run begins, which
was the source of one of those results, and the build stage warns about a design built in
the air (ADR 0023). A run can be repeated with variations - set down off its mark, loaded,
on other floors - and reports its spread and what moved it most (ADR 0024); the first
sweeps found a loaded cart rocking between its casters under its own arm, and program poses
now check where the tool got to and correct it (ADR 0025). What the field publishes now
reaches the project as numbered proposals the owner accepts or declines, with the radar's
brief beside them and journals among its sources (ADR 0026, docs/agents/FRONTIER.md).
MuJoCo 3.10.0 now runs on every machine - the newest release with wheels for the owner's
Intel Mac - with one contact per convex pair, so the engine adds no rolling loss of its own
to the sourced one (ADR 0027). A sweep says how sure it is: its rates come from the
set-ups drawn at random, with exact bounds (ADR 0028). The tilt test sets a machine square
against its rail before it tilts (ADR 0029). A run can be disturbed partway - the machine
shoved, a part moved - to see what it recovers from (ADR 0030), from the run report as well
as the command line; and a program pushed off its stop drives back to it and reaches again
(ADR 0031). The Fetch table has a depth camera, a RealSense D435 with its maker's numbers,
and the Fetch program looks for its cube before it reaches - plane removed, box fitted, no
learned model - and aims where it was seen (ADR 0032); it looks again before the jaws go
down, when a reach is stopped and when a grasp misses (ADR 0033). What the radar and the
weekly reading judge now stays in the repository, searchable by every agent (ADR 0034). The
Fetch program looks before it drives and stops where the cube is (ADR 0035). A disturbance
sweep pairs each set-up with itself undisturbed - the same run until the event, step for
step - and says how many successes the event broke and how sure that is (ADR 0036); the
first such sweep found two faults in looking again, both mended: a reach stopped on the cube
rises off it before going back, and a cube the jaws hide is not taken for gone (ADR 0037).
The table camera can fail - frozen or dark - and the program stops and names it instead of
grasping where a stale picture shows the cube (ADR 0038). How far that camera may stand off
where the program believes it is measured against a closed form: 1.5 degrees of pan, half a
degree of upward tilt, 10 mm (ADR 0039). Beside whether a part arrived, each run says how it
was handled - the pushes on it, its lean, its fall - and finds the Fetch program drops its cube
into the bin and sometimes presses it into the table first (ADR 0040). The presses came from the
cart teetering between its casters; it now stands on all four, steady under its arm and slow over
a curb (ADR 0041), and the cube is set down in the bin, not dropped (ADR 0042). A sweep can ask
whether each result survives a micrometre: Fetch's outcome does, its set-down forces only partly
(ADR 0043). A robot that does not exist yet can be brought in from its own URDF or MJCF file,
driven and programmed like the Menagerie arms (ADR 0044); any arm's tool now travels a straight
line when stepped, or driven by held keys (ADR 0045). The Guide opens on five lessons the app
checks itself (ADR 0046). A gripper in a robot's file is found at import, squeezes, and holds as
the grasp blocks need (ADR 0047). A program feels its grasp from its jaw servos' registers, not the
simulator's contacts (ADR 0048). Decisions are certified on draws they were not tuned on: the
Fetch program on 59 fresh set-ups (ADR 0049). A contact census shows the multiccd setting decides
none of the face-on-face contacts the results rest on, only the casters' (ADR 0050). Looking again
is tried against simpler recoveries and earns its keep where the cube moved after the look (ADR 0051).
An alarm from outside makes a program look again; replayed runs show how late it may come, and what a
false one costs (ADR 0052). Sweeps run with sourced latencies - the camera, the finder, the servo bus -
and find the program's margin in its grasp check (ADR 0053). A guided search for the failure did no
better than the sweeps' corners and draws, and the sweeps keep their plan (ADR 0054). Recent work can be
watched in the window: What's new runs four demonstrations of it, one press each, and the alarm of
ADR 0052 is a Look again button (ADR 0055). The factory cell is judged by where its parts land
against their slots' room and how long each takes: small blocks barely capable, tall ones failing,
the simulated Panda's sag and soft squeeze the causes, the fixes the owner's call (ADR 0056). The cell
lowers its parts straight down and lets go with a narrow hand, and tall blocks run (ADR 0057). A
motor can be run hot partway through a run; the kit cart's drive leaves so much margin that it
does not notice; What's new runs it (ADR 0058). The drive panel says how many degrees a machine has left before it tips,
its accelerations counted (ADR 0059). Once a program holds what it reached for, an alarm is not heard and
Look again greys out (ADR 0060). The drive panel says how much of a grip's friction is in use, and a cube made
heavier until it slides out measures how much weight a grasp carries (ADR 0061). Every sweep says where its runs failed (ADR 0063), and what it can show before it runs (ADR 0064). The Panda is held up against gravity
and its hand squeezes and moves as the real one does (ADR 0065). The kit's jaws squeeze by
current, a setting in newtons (ADR 0066). A roller conveyor field carries pallets to a stop (ADR 0067), and feeds the factory cell on
friction rollers (ADR 0068). The cell finds its parts with its overhead depth camera (ADR 0069). The Fetch keeps its closing
ramp: a squeeze by current, side by side on 130 set-ups, was not worth it (ADR 0070).
Next: what the owner picks from the frontier proposals - among them the DC-motor actuator for the kit's gearmotor, a roller conveyor for the factory's
feeder (moving surfaces and the PID actuator need a release past 3.10), one real servo
calibrated with the system identification toolbox, and the factory cell grasping from its
own camera.
