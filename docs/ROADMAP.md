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
results. Next: move the curb check off its geometric limit and measure stance from wheel
geometry, then upgrade MuJoCo and adopt its conveyor surfaces for the factory's feeder and
its PID and DC-motor actuators for the kit's servos and gearmotors; calibrate one real
servo with its system identification toolbox; run the fields with perturbations; and grasp
from the cell's camera instead of known positions.
