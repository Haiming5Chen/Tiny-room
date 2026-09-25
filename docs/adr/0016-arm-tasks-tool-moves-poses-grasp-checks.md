# Arm tasks: tool moves, taught poses and grasp checks

**Problem.** A kit arm could only be moved one joint at a time - by a key, a jog button
or a program block per joint - so putting the gripper somewhere meant turning shoulder,
elbow and wrist in turn while the tool swept an arc. A program could not move several
joints together, and it had no way to notice that the jaws had closed on nothing: the
arm went on carrying air. The Pick and place field (ADR 0013) had goals no program met.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo supplies what the
solving needs - forward kinematics and the Jacobian of any point on a body (`mj_jac`) -
and the factory cell already solves the Panda's inverse kinematics with it. There is no
general inverse kinematics in MuJoCo itself, and the machines here are built by the user,
so the arm's chain, its tool and its joints have to be found from the design. The
motion itself stays with the physics: a solution only sets joint targets for the same
position servos (ADR 0014), so torque limits, contact and gravity decide what happens.

**Unique contribution.**
- *Tool moves* (`control/tool_motion.py`). The tool is the design's tool module (ADR
  0015); its point is midway between a gripper's pads, fixed in the tool's frame. The
  arm's joints are the keyboard-bound actuators whose joints lie between the machine and
  the tool. A move is solved on a scratch copy of the state by Levenberg-Marquardt damped
  least squares within the joint limits, from several starts (the current targets; the
  first joint turned to face the goal if it is vertical; each with the other joints bent,
  because a stretched-out arm is singular). By default the tool's pointing angle is held,
  so a gripper stays level while it moves. Steps are in the arm base's forward and left,
  laid flat, and true up; a step that cannot be reached within 2 mm changes nothing and
  says how far short it is.
- *Taught poses.* A program block `pose` holds joint angles for several actions and moves
  them together: each joint's target follows a smoothstep from where it started, so all
  arrive at once, at up to a set speed for the joint with furthest to go, and the block
  fails if they have not settled within a set time after that. **Teach pose** in the
  robot controls adds the arm's current targets as a step.
- *Grasp checks.* A block `grasp` waits until the gripper holds an object between both
  jaws (the existing ideal contact observation) and fails the program with "Nothing held"
  when it does not: a missed grasp stops instead of being carried on.
- *A pick-and-place program solved for the machine.* The template takes the object at
  the gripper and the field's tray and solves each waypoint for this arm: close, check,
  lift, over the tray, down, open, retract. It keeps the tool level where the arm can;
  lifting from a fully stretched reach also draws back towards the arm, and only then may
  the tool tilt.
- *Arm runs read as arm runs.* An anchored machine's Drive tab and run report drop speed,
  distance and slip, count goals instead, and do not flag touching things as a warning.

**Blueprint and builder.** Programs gain the two block kinds and a pose's angles; a
program that uses them is written as version 2, which a version-1 reader refuses rather
than misreads, and version-1 files are written exactly as before. Poses are validated
against the design's joint limits. The Pick and place field changed twice, both found by
running this: its tray moved from (0.30, 0.30) - 0.42 m from the arm's axis, where a
level tool 2 cm above the tray's floor is 1.9 cm beyond the standard arm's reach - to (0.20, 0.30),
0.36 m out and clear of the widest test machine; and "resting in the tray" now requires
the cube on the tray floor (centre at most 32 mm up), because a cube held still 1 cm
above it by closed jaws had counted as placed before they opened.

**Result.** In the Pick and place field the arm lab, running the template solved in
22 ms, lifts the cube 5 cm at 1.9 s and has it resting in the tray at 5.7 s, judged by
the field from body poses alone; the program completes at 6.5 s. With the cube moved away
before the grasp, the program stops at the grasp check and the field reports the
placement missed. A tool step is solved to 0.1 mm of the goal with the tool's angle held
to 0.06 degrees, and the servos put the tool within 4 mm of it in 1.5 s. The same run is
driven through the window by its real buttons in a display test.

**Boundaries.** Kit arms with a tool module only: a registered robot model (the Panda) has
its own solver in the factory cell. Positions only, plus the tool's pointing angle: no
orientation about the pointing axis, no path planning and no collision avoidance - a
straight step into the stand hits the stand. The template assumes the object is between
the jaws or reachable from above, and a place point in the field; it plans once, from
the state when it is made. Grasp detection is contact on both jaws, not a force or slip
estimate.
