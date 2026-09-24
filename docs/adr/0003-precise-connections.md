# Precise assembly and editable hinges

MuJoCo already solves hinge dynamics, damping, motor torque and angular limits.
Reuse its existing joint API; do not implement a second constraint solver. The
builder's contribution is resolving selected local attachment frames to portable
body transforms, with transactional edits and clear units.

Use six generated local surface frames for primitive bodies and existing named
Attachment frames for custom connection points. Mating aligns their origins and
opposes their outward Z normals. Resolve the result into the body parent/transform;
connections are not persistent constraints and do not automatically follow later
resizing. Reject hierarchy cycles. Subtrees travel with their selected root.

Expose exact local position, dimensions and rotation; a Connect inspector chooses
parent/source/target and gap. Hinge editing exposes child-local axis/pivot, damping
and optional limits, with fixed/hinge switching and optional ideal motor. Additive
Hinge fields default to the legacy origin/unlimited behavior in Blueprint v1.
Keep core and construction standard-library-only. Verify rotated frames, cycle
rejection, undo/save, native joint settings and actual limited motion, plus UI
input isolation so typing never starts simulation or drives the robot.
