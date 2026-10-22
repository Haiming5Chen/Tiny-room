# The tool travels its line: straight tool moves and held keys

**Problem.** ADR 0016's tool step set the arm's joint targets where the step ends, and each
servo took its joint there at its own pace, so the tool bowed off the straight line on the way:
on 10 cm steps the kit arm strayed 7.7 mm (left), 6.9 mm (up) and 12.7 mm (down), 4.5 and 7.8 mm
stepping back 2 and 6 cm from its stretched design pose, the UR5e 2.3 to 4.3 mm, and an arm
imported from its own file (ADR 0044) 10.2 mm on a 3.6 cm step (OPEN LW-031). Near a part, a bow
of a centimetre is a knock. And the tool could only be clicked along; holding a key moved single
joints. Moving the tool rather than the joints is what lets a newcomer work an arm: five novices
picked and placed in 27.5 s with a task-level mapping against 56.7 s joint by joint
([arXiv 1802.04349](https://arxiv.org/pdf/1802.04349); the focused reading of 21 October, FR-032).

**Does an existing simulator solve it? Can we wrap it?** A straight tool move is ordinary robot
practice - an industrial controller's linear move and its jog in world or tool axes - done by
interpolating the tool along the line and solving the joints as it goes. MuJoCo supplies the
Jacobian (`mj_jac`), which ADR 0016's damped least squares already uses; nothing else is added.

**Unique contribution.**
- *A step glides* (`ToolMotion.glide`, `line`, `Glide`): the step's straight line is solved at
  points every 2 mm (`WAYPOINT`), each from the one before, so the arm keeps its way of bending
  all along; a point that cannot be reached so - leaving a stretched, singular arm - is solved
  from the joint angles that far between the start and the end's own solution. Nothing moves
  unless every point is within 2 mm of the line. `advance` then hands out the joint targets as
  the tool travels the line at 5 cm/s (`SPEED`), smoothly from rest to rest. The Tool panel's
  steps (1, 2, 5 cm) glide; its readout and Teach pose use where the move ends.
- *Held keys drive the tool* (`ToolMotion.drive`): in Tool mode, held arrow keys carry the tool's
  target forward, back, left and right along the arm's own axes, Page Up and Page Down up and
  down, at 5 cm/s, each step solved from the last; at the edge of its reach - or where it cannot
  keep the tool's angle - it stops, and the panel says why; released, it stays where it got to.
  In Tool mode the arrows move the tool, not the base; W, A, S and D still drive.
- Any arm: kit arms, Menagerie arms and imported robots alike.

**Blueprint and builder.** Untouched: a move is runtime targets; a taught pose is still a
program's joint angles.

**Result.**

| Tool moved by | jump to the end (ADR 0016) | along the line |
| --- | --- | --- |
| kit arm, 10 cm left / up / down | 7.7 / 6.9 / 12.7 mm off the line | **0.2 / 0.2 / 0.3 mm** |
| kit arm from its stretched pose, back 2 / 6 cm | 4.5 / 7.8 mm | 2.3 / 1.3 mm |
| UR5e, 10 cm forward / left / up / down | 2.4 / 3.6 / 4.3 / 2.3 mm | 0.6 / 3.5 / 1.8 / 1.5 mm |
| imported test arm, 3 cm forward and 2 cm down | 10.2 mm | **0.4 mm** |

A 10 cm step now takes 1.9 s to arrive within 2 mm (0.6 to 0.9 s before). What stays off the
line is the arm's own sag: the UR5e's servos end 1 to 4 mm low under its weight either way.
Held for 3 s, the kit arm's tool went 14.7 cm to the left, and 14.7 cm down, within 0.3 mm of
its line (the servos lag 3 mm behind the target); driven forward it stopped at the edge of its
reach and stayed. Three seconds of driving were solved and simulated in 0.9 s.

Held by `tests/test_tool_glide.py` (8, one a window test): a glide's angles from rest to rest;
the kit arm's line against its jump, at the tool speed; a line out of reach moves nothing; a
held key at 5 cm/s, straight, stopping at the edge of the reach and staying; the imported arm's
line against its jump; the keys in the window (Page Up raises the tool, released it stops, an
arrow moves the tool and not the base). `tests/test_arm_tasks.py`'s window test waits for the
glide before teaching. Suites on MuJoCo 3.10.0: 1028 passed with a display, 979 headless.

**Boundaries.** The line is where the tool is sent; the servos still lag and sag, and nothing
checks collisions along it (the solver never did). A line through a pose the arm cannot take is
refused, not bent around; from a stretched arm the first millimetres leave the line. One speed;
the tool cannot yet be dragged with the mouse. A program's pose blocks still move joint by joint
- smooth in the joints, not straight in space.
