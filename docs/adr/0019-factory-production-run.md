# Factory cell: a production run, and the rough edges round it

**Problem.** The factory cell (Real mode) placed one part and stopped: another meant
Reset cell and start again, so nothing about it was a factory - no throughput, no count
of parts placed or failed, no second part to place next to the first. It stood on a table
in a black void. Its messages called the same tray a bin in one place and a tray in
another. And a registered robot in the joint lab could only be moved joint by joint.

**Does an existing simulator solve it? Can we wrap it?** The physics of every cycle is
already MuJoCo's - finger contact, lift, release, all checked from contact and pose
(docs/FACTORY.md). What was missing is the loop around it and the bookkeeping, which
belong to the cell's controller, and a place for the next parts to come from.

**Unique contribution.**
- *A production run.* `FactoryCycle.production(parts, destination)` runs the cell part
  after part: the part on the input tray first, then the parts waiting on a stock shelf
  beside the table (`factory_scene(stock=...)`), each fed onto the input tray once the one
  before has been placed and the hand has retracted. The feeder itself is not simulated -
  the next part is moved onto the tray, said so in the ADR and the scene - but everything
  from there is the same physics as a single cycle: plan, grasp by contact, verified lift,
  verified placement. A failure stops the run with its reason.
- *Slots.* Successive parts go to the next of six slots in the destination tray, two rows
  along the direction the fingers close, so an open hand lowering a part clears the parts
  already there.
- *Counters.* Parts placed, failed, seconds per part and parts per minute, live above the
  scene; the clock reads the run's time and the part in hand.
- *Round it.* A sky backdrop instead of a black void (ADR 0013's); "tray" everywhere; the
  drive-key hint only for machines that drive. And tool moves (ADR 0016) now drive the
  registered robots too: the Panda's tool point is between its fingertips (as its planner
  grasps), an arm-only model's is its flange, and their joints are their own position
  servos; the Panda's gripper servo is its jaws.

**Blueprint and builder.** The cell's recipe (tray positions, product, source and
destination) is unchanged and loads as before; the stock is part of the scene, not the
recipe. `factory_scene()` without stock is the scene every earlier test used.

**Result.** Six small blocks: all six placed in their slots in the Blue tray, none failed,
12.3 s per part, 4.9 parts per minute of simulated time; six tall blocks the same. In a
test run of three into the Amber tray each lands within 2 cm of its slot and rests on the
tray's floor, not on another part. A part taken off the input tray stops the run with
"Grasp failed", counted. Tool steps of 5 cm on all four registered robots are solved
exactly with the tool's angle held, and their servos follow within 0.3 to 1 cm.

**Boundaries.** The feeder is a teleport, not a mechanism. One product type per run; six
slots per tray. The planner is still the fixed top-down waypoint planner with known object
positions (no vision, no collision checking beyond what contact does), and a registered
robot's tool moves have no collision check against its own links.
