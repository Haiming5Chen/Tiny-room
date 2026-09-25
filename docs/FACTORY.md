# Factory workcell: arrange, connect, understand

Use the **Real / Anime** switch at the top of the app. Both workflows share one
window. **Real** opens robot experiments; **Anime** keeps component construction.
Switching retains both workspaces and pauses the simulation you leave. The desktop
launcher opens Real by default. The nested Real/Anime catalog tabs are removed.

## Choose a robot and experiment

The top-right **Robot** picker offers Panda, FR3, Kinova Gen3 and UR5e as complete
registered robots. **Joint lab** provides manual operation and a **Program sequence**
editor, including a small joint-motion example. Programs are retained per robot
within the session and can be saved/loaded separately. Arm-only models are labeled;
**Pick and place** is enabled only for Panda, the validated grasping experiment.
There is no component assembly UI in Real. Custom construction remains in Anime.

## Arrange your cell

Select **Arrange**, then drag any of the three trays directly on the table.
A translucent 3D tray follows the cursor, snapping to a 1 cm placement grid.
Green means the tray fits the workspace; red comes with a specific explanation:
outside the table, overlapping another tray, too close to the robot base, or
intersecting a camera support. Release commits one undoable edit. Escape cancels.
Drag empty space to orbit the camera. Robot, table and camera remain fixed.

These checks concern placement. **Preview path** separately checks the Panda's
ability to reach the task's top-down waypoints. A valid tray placement does not
promise a feasible or collision-free robot motion.

## Connect the task

Select **Set task**. Click the tray to pick **from**, then a different tray to
place **into**. Labels show the selected roles in the scene. Any of the three trays
can be the source or destination. Choosing a source puts the initial product in
that tray as part of editing the design, before simulation starts.

Choose Small block or Tall block, then **Preview path → Run cycle**.
The robot computes its joint targets. The task checks bilateral finger contact,
actual product lift and final placement. Failure pauses with a reason.
**One stage** pauses after each stage; **Pause / Resume** controls execution.
**Reset cell** restores the product and robot to their initial poses.
Reset before editing a running or completed cell.

## Production run

**Run 6 parts** places the part on the input tray and then the five waiting on the
stock shelf beside the table, one after another, each into the next of six slots in the
destination tray. The feeder that brings each part from the shelf to the input tray is
not simulated: the run moves the next part onto the tray once the one before has been
placed and the hand has retracted. Every cycle is otherwise the full physics - grasp by
finger contact, verified lift, verified placement - and a failure stops the run with its
reason. Above the scene: parts placed and failed, seconds per part and parts per minute
of simulated time (about 12.3 s and 4.9 a minute for small blocks). **Reset cell** puts
every part back ([ADR 0019](adr/0019-factory-production-run.md)).

In the **Joint lab**, the robot controls' **Tool** mode moves the hand in straight steps
(the Panda's point is between its fingertips; an arm-only model's is its flange), and
**Teach pose** adds the arm's targets to the program ([ADR 0016](adr/0016-arm-tasks-tool-moves-poses-grasp-checks.md)).

## How picking works

**How picking works** resets the current cell and opens a contextual explanation.
**Next step** runs one real task stage and pauses. Explanations cover approach,
known-object sensing, finger contact, frictional lift, transfer, placement and
verification. **Replay** resets the demonstration. **Try it yourself** returns to
Arrange with the authored layout preserved. A failed task is shown as a failure.

This draws inspiration from Create's [Ponder](https://github.com/Creators-of-Create/Create/wiki/Internal---Ponder-UI)
approach to in-context documentation. No Create code or assets are included.

## Save and undo

**Undo** reverts the most recent committed tray, product or task edit.
**Save cell** writes the layout and task to
`~/Library/Application Support/Little World/factory-cell.json`, which loads next
launch. Runtime poses and a partly selected task are not saved. The recipe is
versioned portable JSON, separate from robot Blueprint files.

## Simulation scope

Panda retains its sourced Menagerie meshes, joint limits, inertias, coupled fingers
and force-limited servos. Native damped least-squares IK calculates top-down
waypoints; smooth joint targets are executed through those servos. The sampled
preview uses scratch state and never moves the live robot. Actual motion can
lag under finite force or contact. Products are free rigid bodies grasped through
MuJoCo friction/contact, never a weld or attachment trick.

**Known-object sensing** reads the product position from the simulator.
**Camera view** displays the simulated overhead RGB camera; image recognition is
not connected. Products are two predefined rigid block shapes. This remains a
Panda pick-and-place template, not an arbitrary line editor: no conveyors,
multi-robot scheduling, arbitrary shape recognition or general collision-avoiding
motion planner. Rearranged layouts can expose motion or grasp failures.
