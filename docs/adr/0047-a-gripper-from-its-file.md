# A gripper from its file: found, driven by how closed it is, and holding

**Problem.** A robot imported from its file (ADR 0044) with a gripper at its end had the gripper
driven joint by joint: its finger a slide in millimetres, its mimic finger following. Nothing
said which way closes or which links are the jaws, so the grasp blocks never saw it hold - their
check reads both jaws touching the object - and Tool mode's Open and Close had nothing to drive
(OPEN LW-030). Its servo was sized as any joint's, for its 30 g finger: 16 N/m, so closed on a
3 cm box it pressed with 0.12 N at each jaw, and a 10.8 g box turned over by the elbow slid
7.3 mm during the turn and on at 4.4 mm/s after it - MuJoCo's soft friction creeps under so light
a squeeze, the two noslip iterations (ADR 0017) notwithstanding.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo reads the joints and their
`<mimic>` couplings, and holds an object between two jaws by its contacts' friction; it does not
say what a gripper is. Menagerie models drive their grippers through hand-written actuators and
tendons, the Panda's included. This work is on top of MuJoCo's own: which joint closes a gripper
is read from the file's names and checked on its geometry with `mj_geomDistance`; holding stays
MuJoCo's contact friction, as for the Panda and the kit gripper.

**Unique contribution.**
- *Found at import* (`physics/importer.py`): a limited joint named like a finger (finger,
  gripper, jaw, claw, pinch - the joint or its link) whose finger comes at least 3 mm closer to
  the other jaw at one end of its travel than at the other is a gripper; the other jaw is its
  mimic follower's link, or, with none, a fixed jaw - the link it hangs from or a link fixed to
  that one. The end where the jaws are nearest closes it. The report says so in a line - "its
  fingers 60 mm apart open, 0 mm closed: it is driven by how closed it is, 0 to 100 %, and
  presses what it closes on with up to 10 N at each jaw (its effort in the file, 20 N)".
- *Driven by how closed it is*, 0 to 100 %, as the Panda's gripper is: the keys, the jog buttons,
  Tool mode's Open and Close, the block programs and the run report send and read it so (`robot_models.grip`); its control
  is labelled 'Gripper close / open', and the tool point is between the jaws.
- *A servo that squeezes*: with the file's effort once the jaws are stopped a tenth of their
  travel short of where they are sent (6,667 N/m for this gripper), or, if the file gives no
  effort, with the kit gripper's 12 N at each jaw (ADR 0017) - a hinged finger's torque that force
  times its lever. Through a mimic the joint's force closes both fingers, so each jaw presses with
  half of it. So stiff a servo is stable at the 2 ms step only with the inertia of a geared drive
  behind the finger - a gripper's motor and screw - which is added as the joint's armature where
  the finger is lighter (0.64 kg here).
- *Contacts that do not give*: MuJoCo's contacts are soft in proportion to the mass behind them,
  and with the squeeze the jaws sank 6.8 mm into each side of the 10.8 g box; a mimic follower,
  at MuJoCo's default softness, gave 3.5 mm. The jaws' contacts and every mimic equality are made
  the stiffest MuJoCo takes at the 2 ms step (a time constant of twice the step, impedance 0.95 to
  0.99); the jaws decide their own contacts, with torsional friction.
- *Held, as the grasp blocks check it*: the backend names each imported gripper's jaws
  (`robot_jaws`), and `Observations.grasped()` - the grasp blocks, the run report's grip history,
  the inventory's trials and sweeps - counts both jaws on a movable object as held, as for the
  Panda and the kit gripper.

**Blueprint and builder.** Untouched: the gripper is metadata of the library robot (its channel,
open and closed positions, jaws); a design names the robot as before.

**Result.** The two-link test arm with a parallel gripper at its end: a block program closes the
jaws on a 3 cm, 10.8 g box (60 % in 1 s, as the pick-and-place programs close) and its grasp check
passes at 50.9 % closed; the elbow then turns the box over a right angle, where it hangs from the
jaws alone, and it stays within 1 mm of where it was held (0.44 mm). Sent fully closed, each jaw
presses with 10.0 N - the file's 20 N, shared - sinking 0.15 mm into the box; opened, the box falls
free. Tool mode's Open and Close drive the gripper. A claw - one hinged finger closing on a jaw
fixed to the palm, no effort in its file - is found the same way, squeezes with 12 N at its jaw
(0.48 N m for its 4 cm lever), and closing on nothing stops where its jaws meet, 77 % of its
travel. A double stage - the same two slides named as a stage's - is not a gripper and is driven
in millimetres, as ADR 0044 drove the gripper.

Held by `tests/test_robot_library.py` (20, one a window test): the gripper found, its program's
grasp, the box held turned over and the squeeze; the claw; the stage in millimetres. Suites on
MuJoCo 3.10.0: 1037 passed with a display, 985 headless.

**Boundaries.** A gripper is found by its names and its geometry: one whose joints and links are
named otherwise is driven joint by joint, as before; one gripper per robot, the first found. A
model with actuators of its own keeps them (ADR 0044), and its gripper is driven by them, joint by
joint. A gripper driven through a tendon or a linkage the file models - the Panda's own file, a
Robotiq's four-bar - is not imported (ADR 0044). The squeeze is the joint's effort limit as the file states
it, which may be the motor's rating or a guess; the file's velocity limit is not kept: sent at
once from open to closed, as Tool mode's Close sends it, the fingers reach 0.76 m/s before they
meet the box (the keys and the programs close at 60 % of the travel a second). The armature added is a drive's inertia chosen
for stability, not the robot's. Holding is MuJoCo's contact friction: no slip or payload rating is
claimed, and the held box rocks by a milliradian between its eight contacts.
