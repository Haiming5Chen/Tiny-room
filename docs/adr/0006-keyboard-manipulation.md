# Keyboard-controlled arms and gripping

Reuse MuJoCo hinges, torque actuators and rigid frictional contact. Add original
articulated arm/gripper catalog modules and a tabletop manipulation example. A
keyboard-position ControllerSpec maps two keys to one or more limited joints.
Holding a key integrates a bounded angle target; a torque-clamped PD controller
holds that target after release. The MuJoCo adapter adds model bias forces
(gravity and velocity effects) before the torque clamp to support the arm load. No body pose assignment, object parenting on
contact, invisible grasp welds or executable code in saved Blueprints.

Persist action label, keys, target speed and gains as optional ControllerSpec fields.
Old controllers retain their existing meaning. Keep runtime keyboard state and
native joint addresses outside Blueprint. The control law takes plain scalar joint
observations so headless scripts can use the same controller as the UI. Reject
reserved keys, unbounded joints and overlapping actuator ownership. Reset, focus
loss and pause clear held input. Editing a binding is a normal undoable edit.


Gripper variants reuse native primitive collision geometry. Configuration replaces
both contact pads and the palm material, and updates both existing jaw torque
limits in one immutable revision. A module-specific material prevents global
changes to wheel traction. Preserve MuJoCo's existing max-pair friction policy.
Arm size variants scale geometry, joint pivots and attachment frames consistently;
torque budgets are illustrative (compact arms retain capacity for a full-size tool).
The mobile manipulator attaches a compact arm to a fixed deck on the existing
dynamic chassis and retains both drive and joint controller descriptors. No new
solver or native constraint type is introduced.
