# Machine structure: modules, roles and stance

**Problem.** A mobile manipulator is 300-odd bodies. The Assembly tab showed them as a
tree of part names, so nothing said "a chassis, two drives with their wheels, two
casters, an arm and a gripper", which keys move which of them, or what each weighs.
Nothing said how the machine stands either, although that is what an arm on a light
cart changes: the first sign that a design was top-heavy or balanced on a line was a
tipped or rocking run. While a run was going the Drive tab showed the wheels and
nothing of the arm.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo computes masses,
centres of mass and contacts, and the run-time stance is read from its contacts. What
it cannot do is answer before the run, from the design, and it has no notion of a
catalog module or a role. Both are derived here from the Blueprint alone (standard
library), and checked against the compiled model.

**Unique contribution** (`construction/structure.py`, `control/drive_telemetry.py`).
- *Modules and roles.* A module is a catalog part as it was inserted: its root body and
  everything below it until the next module's root. Its role comes from the catalog
  variant (drive, wheel, support, arm, tool, sensor, mount...); a gearmotor bound to the
  drive controller is a drive, otherwise an actuator. Each module lists its bodies, its
  motors, the keys bound to them and its mass (density x volume, exactly as MuJoCo
  derives it; a registered robot model's mass is left as unknown, not guessed).
- *Stance before the run.* The machine is treated as rigid at its design pose and set
  on a level floor. It rests on its lowest points; while its centre of mass lies outside
  the polygon they make, it tips about the nearest point of that polygon's boundary,
  towards the centre of mass, until the next point meets the floor. The result is the
  tilt, which parts carry it, and the stance margin: the distance from the centre of
  mass to the nearest edge of the support polygon. Round parts are polygons (16-point
  rims) within 2 % of their radius; past 45 degrees the machine is reported as tipping
  over.
- *Stance during the run.* The same margin from the simulator's own supporting
  contacts (normals within 45 degrees of vertical) and the machine's subtree centre of
  mass, sampled with the drive telemetry; the run report keeps the lowest. A machine on
  one wheel or an edge has no polygon, and no margin is shown rather than a false one.
- *Where it shows.* The Assembly tab opens on **Modules** (role, title, mass, keys;
  clicking selects the module) with **Parts** for the full tree. The Build stage header
  states the composition and the stance ("Rests on 2 wheels and 1 support, tilted
  2.8 deg; centre of mass 3.4 cm inside"). The Drive tab adds the stance margin and an
  ARM section with each action's keys and joint angles, and lays sections out to fit.

**Blueprint and builder.** Read-only: nothing is saved and no design changes. A design
bolted to the world is "anchored" and gets no stance.

**Result.** Module masses add up to the compiled model's to 1e-9 for the arm lab, the
mobile platform and the mobile manipulator, and the design-pose centre of mass matches
MuJoCo's. The rigid stance predicts that the mobile manipulator rests on both wheels and
its front caster, 2.84 degrees nose-down with 3.37 cm of margin; after 1.5 s in the
simulator it rests there at 2.8 degrees with 3.4 cm (the caster is 6.5 mm above the
tread wheels' lowest point, so the four-point chassis is a rocker). The bare mobile
platform balances on its two tread patches with 3.3 mm to spare - its centre of mass is
0.7 mm ahead of the axle - and the drop at the start of a run is enough to rock it onto
a caster, which the header flags as "rocks easily".

**Boundaries.** The stance is static: it ignores acceleration, so braking hard or
swinging the arm quickly can tip a machine that has margin left, and it takes the design
pose, not the pose the arm will reach. Joints are locked for the analysis (a wheel that
rolls as the chassis pitches is treated as fixed) and the floor is level and rigid.
Roles come from the catalog; a part built from raw bodies in the editor is a "part".
