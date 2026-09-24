# Mechanical kit research and adaptations

Reviewed 2026-09-16. These are design references; no third-party code, meshes or
vendor dimensions were imported in this pass.

| Reference | Useful idea | Little World adaptation |
| --- | --- | --- |
| [Webots Slot](https://github.com/cyberbotics/webots/blob/master/docs/reference/slot.md) | Explicit compatible connection points | Expose the motor's moving output at module level; shaft loads use that output instead of a generic body face. |
| [Gazebo robot construction](https://gazebosim.org/docs/all/building_robot/) | Links and joints define the mechanism; joint axes need explicit frames | Keep the motor casing fixed and attach loads to the moving shaft. Mirror wheel poses and axle signs together. |
| [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie/blob/main/README.md) | Document model origin, quality and physical limitations separately from appearance | Each part guide distinguishes simulated behavior from approximate or unsupported behavior. Procedural kit parts are not calibrated vendor models. |
| [Pololu Romi guide](https://www.pololu.com/docs/0J68/all) | Two driven wheels plus caster support; motors and wheels are separate components | Explain ready-made drive assemblies versus passive wheels and separate motors. |
| [ServoCity Nomad](https://www.servocity.com/nomad/) | Four independently driven wheels and several mounting locations | Front/rear wheel positions per chassis side; repeated left/right drive pairs. |
| [ServoCity ServoBlock](https://www.servocity.com/compact-servoblock-27mm-width-for-axon-mini-servo-hub-shaft/) | Servo, supporting bearing and output hub have distinct roles | Explain housing, moving output, hub and bearing separately instead of displaying unexplained hardware. |

## Implemented scope

- Center and front/rear side sockets with wheel spacing checks.
- Outward-facing wheel details and consistent forward-drive joint axes.
- Multiple differential wheel pairs in interactive control and benchmark runs.
- Motor output discovery without selecting a tiny internal shaft.
- Ten new driven components: two sizes each of crank, roller, flywheel, spool and
  rotating plate. These use the attached motor's joint, not another hidden motor.
- Existing hubs/couplers carry rotation through a second output socket.
- Catalog labels distinguish assembly, component and hardware; Part guide explains
  purpose, compatible connection, a practical example and model limitations.

## Next model-quality work

Visual detail is not evidence of accuracy. Imported complete robots should retain
source licenses, measured inertias, joint limits, actuators and a separate scene,
as Menagerie does. A future mesh importer must also separate visual meshes from
collision geometry and invalidate renderer resources correctly. This pass does
not add a mesh importer, electrical simulation, cable dynamics, gear meshing or
closed kinematic loops. Spools therefore rotate but cannot wind a physical cable.
