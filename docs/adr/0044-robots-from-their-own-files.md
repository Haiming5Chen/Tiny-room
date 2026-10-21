# Robots from their own files: the robot library

**Problem.** Little World drove four Menagerie arms, each registered by hand: a folder in the
repository, a metadata file written once, names hard-coded in the core's checks. A robot that
does not exist yet - one a student designs and exports from CAD as a URDF, a lab's own arm -
could not be tried, mounted, programmed or tested on a field. The owner asked for exactly that
on 21 October ("take in some data type of modeling, for testing robots or models that do not
exist ... they can program and build their robot as well"; FR-031). MuJoCo 3.10 reads a URDF
itself, but checked on this machine the robot comes in with no motors (`nu` 0), its root link
fused into the ground, its `package://` mesh paths not found and its visual shapes dropped; a
misspelt attribute (`efort`) is ignored without a word, leaving the joint with no effort limit.

**Does an existing simulator solve it? Can we wrap it?** Yes, mostly: MuJoCo's own URDF and MJCF
readers do the parsing, and its `MjSpec` the editing, compiling and writing. What a URDF lacks
for MuJoCo is known practice - PickNik's guide adds a position actuator per joint with a damping
ratio of 1 and gains by size, turns URDF effort limits into actuator force limits, keeps one
body per link and resolves meshes ([PickNik, Migrate to a MuJoCo configuration](https://docs.picknik.ai/how_to/configuration_tutorials/create_robot_sim_config/migrate_to_mujoco_config/);
MuJoCo's documentation on URDF extensions). No new dependency.

**Unique contribution.**
- *The importer* (`physics/importer.py`) reads a `.urdf` or MuJoCo `.xml`, says what it found
  and adds only what driving the robot needs. To a model with no actuators: a position servo on
  every hinge and slide, stiff enough to hold the robot within 0.5 degree (a slide within 0.5 mm)
  of where it is sent against its own weight at any pose - the weight weighed at the home pose
  and 64 random poses within the limits - never softer than settling its joint in 0.25 s, never
  stiffer than 100 rad/s at the joint's own inertia (stable at the 2 ms step), critically damped
  at that inertia; the file's effort limit is the servo's force limit. A URDF `<mimic>` becomes
  a joint equality, the follower without a servo of its own. The root link stays the robot's
  base; visual shapes are kept and collision shapes hidden behind them; links that already
  touch at the home pose are kept from colliding with each other, as neighbours are. A model
  with its own actuators keeps them and gets nothing added; they must be position servos on
  joints. A free joint at the base is removed: a robot is fixed where it is placed.
- *A report in plain words*: what the file is (links, joints, mass, height), what was added and
  why, and what to check - a misspelt or unknown URDF word, a joint with no effort limit, one
  too weak to hold the robot up ("can push at most 3 N m; holding the robot up takes up to
  5.51 N m at some poses: it will sag there"), a link with no mass (worked out from its shapes
  as if water) or no collision shape, a mesh MuJoCo cannot read (`.dae`: left out, named), one
  of more than 200,000 faces, collision meshes colliding as their convex hulls. A file that
  cannot be imported says why - a xacro file, a missing mesh (with the link and the path looked
  in), a floating, planar or ball joint, an actuator that is not a position servo - and leaves
  nothing behind.
- *The robot library* (`assets/robot_library.py`), outside the repository: one folder per robot
  with `model.xml` (the MuJoCo model, its meshes copied into `assets/`), `metadata.json`,
  `SOURCE.json` (the file's name and the SHA-256 of everything copied) and the description file
  as given. A design names a library robot as `user:<name>` - a name, never a path; an entry is
  never rewritten (importing again makes `name-2`), and a design whose robot was removed fails
  to load naming it. Tests each get an empty library.
- *Driven like the Menagerie arms*: a library robot is a registered robot to the backend, the
  keyboard, the block programs, the tool moves and the build report. Joints are named from the
  file ("Shoulder", "Elbow"), slides are driven and shown in millimetres. A robot file dropped
  on the window is imported and opened in the Joint lab; there, "Robot: ..." lists the library
  and "Import a robot from its file..." brings one in, and the left panel lists what its import
  said to check. `python -m little_world.physics.importer FILE` does it from the command line
  (`--check`, `--list`, `--remove`).

**Blueprint and builder.** A library robot is a `Body` with `robot_asset='user:<name>'` and its
`RobotServo` channels, as a Menagerie arm is; the core accepts the name's pattern only, and the
backend checks the channel against the robot's file.

**Result.** The two-link test arm (4.3 kg, no motors) imports with two servos (631 and
112 N m/rad, set by the arm's weight, not its inertia) and holds 60 and -40 degrees, held out
sideways, within 0.4 degree, within 1 degree after 0.18 s; imported with a 3 N m shoulder it
says it will sag, pushes no more than 3 N m and falls to its 115-degree limit. The parallel gripper's mimic finger follows its leader to 30 mm within 0.5 mm. The
UR5e imported from its own file keeps its six servos, adds nothing, and follows the shipped arm
joint for joint within 0.5 degree; the FR3 and Gen3 import the same way; the Panda's file is
refused by name (its gripper is driven through a tendon). RESULT

Links that overlap at the home pose are kept from colliding (without that, the test arm starts
pushed 4 degrees off); a jog sends the imported arm's tool where it is asked within 2 mm (on the
way it bows 10 mm off the straight line: each servo moves its own joint at its own pace, OPEN
LW-031).

Held by `tests/test_robot_library.py` (18, one a window test): the arm's servos and pose; the
effort limit; mimic and millimetres; the UR5e against itself; a block program on the imported
arm; a tool jog; overlapping links; the report's warnings; six files refused with their reasons
and nothing left behind; a missing mesh named; the library's names, no overwrite, a removed
robot named; library robots as parts and the command line; the Joint lab importing a robot from
its form and from a file dropped on the window, and running it. Suites on MuJoCo 3.10.0: 1020 passed with a display, 972 headless.

**Boundaries.** Arms and other robots fixed at their base: a floating base, a walking robot, a
ball or planar joint, height fields, skins and flexes are refused. At most 8 driven joints. The
servos added are ideal position servos - stiff and damped as stated, limited by the file's
effort, but with no speed limit (the URDF `velocity` is not used), no current, gearing or heat.
A gripper imported from a file is driven joint by joint, not yet by the grasp blocks (OPEN
LW-030); the tool point is a link named like a tool, else the last driven link. COLLADA meshes are left out, not
converted; collision meshes are convex hulls. Masses, inertias and limits are the file's: the
import says what it was given, not whether it is right.
