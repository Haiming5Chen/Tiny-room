# Fetch: driving to a point, and a task for an arm on wheels

**Problem.** An arm on a wheeled base had no task that used both. A program could drive
only by timed wheel speeds, so it could not bring the base to a table, and no test field
asked a machine to fetch anything - drive somewhere, pick something up, bring it back
and put it down - which is what a mobile manipulator is for.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo moves the machine; the
steering is a controller, and a textbook one: a differential base driven to a point by
turning towards it and driving, then turned to a heading. Navigation stacks (Nav2 and
the like) plan through maps with localisation; here the pose is an ideal observation,
as every program sensor is, and the fields are open, so a point-to-point controller is
enough and anything more would imply a capability that is not there.

**Unique contribution.**
- *Drive to a point* (`control/navigation.py`, standard library). The base's pose is its
  drive axle's midpoint and the direction square to its wheel line - what a differential
  drive steers, whatever the chassis's own frame. Far off the bearing it turns on the
  spot; otherwise it drives at up to 0.22 m/s, slowing with the distance left but never
  below 3 cm/s (slower, friction stalls it), and backs up to a goal less than 0.5 m
  behind rather than turning round, which also keeps an arm held out in front from
  sweeping into what it was just reaching. Once within tolerance it turns to the
  heading, at no less than 0.3 rad/s, and only chases the point again if it drifts four
  tolerances away: without that hysteresis a turn on the spot's small drift started the
  approach again and it oscillated. Wheel speeds follow from the wheel radius and track,
  read from the model (`BasePose`).
- *A `goto` program block*: a point (x, y) or (x, y, heading), a tolerance (default 1 cm)
  and a timeout. It is data like the rest (version 2); the runner drives the base with the
  controller above and the block ends when the base arrives, or fails at the timeout.
- *The Fetch field*: a 12 cm plywood table 1.8 m ahead with a 25 mm wooden cube on it, and
  a bin on the floor left of the start. Goals: reached the table, cube lifted 5 cm, cube
  resting in the bin (on its floor), stayed upright.
- *A Fetch program solved for the machine*: open the jaws and take the pose above the
  cube before driving (driving in with the arm as designed pushed the cube 3.7 cm along
  the table); drive so the tool is over the cube; lower, close, check the grasp, lift;
  back away; drive to the bin; lower and let go; retract. Each arm waypoint is solved for
  the machine standing where the program will have driven it, planned from the machine
  as it stands (settled 2.8 degrees onto its front caster, ADR 0015), and checked for the
  arm hitting its own machine: reaching down to a bin on the floor, the compact arm's
  forearm lands on the chassis's front cross member first, so the release rises in 2 cm
  steps until it does not. The release point is 5.5 cm short of the bin's centre so the
  chassis stays off the bin's near wall.

**Blueprint and builder.** The goto block is program data; the field is ordinary
Blueprint entities. The Program editor gains Drive to (defaulting to where the base is)
and a field-task button that builds the Pick and place or the Fetch program.

**Result.** The mobile manipulator fetches the cube by itself: it reaches the table at
9.7 s, has the cube lifted at 16.2 s and resting in the bin at 32.9 s, stays upright,
and the program completes at 33.6 s - judged by the field from body poses. Driving to
points, the platform comes to rest within 0.5 cm and 2 degrees of them, the heavier
mobile manipulator within 2 cm and 2 degrees. The fetch exposed the grasp creep fixed in ADR 0017: before it, the
cube slid out of the jaws on the way back.

**Boundaries.** Positions are ideal: no odometry drift, no localisation, no obstacle
avoidance or path planning - a goto drives straight at its point. The program plans once
from the state it is made in; if the object is moved, the arm reaches where it was. Kit
arms with a tool module on a base with a left and a right drive wheel.
