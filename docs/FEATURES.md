# What Little World does

Everything the window and its tools do, roughly in the order it was built, each with the decision record that explains it
and the numbers it was measured with. The [README](../README.md) is the short way in; the
[manual](MANUAL.md) says how each part of the window is used; [the evidence](EVIDENCE.md) says how to
measure the headline numbers again; [the evaluation](EVALUATION.md) says what does not hold.

- **Two workflows, one window.** *Real* runs complete robots - UR5e, Franka Panda and
  FR3, Kinova Gen3, from MuJoCo Menagerie with their original meshes, inertias and
  servos. *Anime* is the builder: 85 kit modules (chassis, gearmotors, wheels,
  casters, arms, grippers) and 26 lab assemblies, snapped together on named sockets.
- **Everything is data.** A design is a versioned JSON *Blueprint*. The core is
  standard-library Python and knows nothing about MuJoCo or the UI, so the same
  design can come from the mouse, from the in-app Python builder, or from a script.
- **Build -> simulate -> reset -> redesign**, with undo/redo, face-to-face precision
  connections, joint limits, sourced servo profiles, a block program editor, a live
  test panel (contact, tilt, joint error, torque) and side-by-side trials of saved
  versions. Simulating a vehicle is a **test drive**: a chase camera, live motor and
  slip telemetry, the path on the floor and a run report compared with the last run
  ([ADR 0012](adr/0012-test-drive.md)), in one of eleven **test fields** whose
  goals the physics decides: the workshop room, a sprint, a slalom, ramps, curbs, a
  crate to push, a pick-and-place table, a fetch-and-return, a doorway, a tilt table
  and a roller conveyor ([ADR 0013](adr/0013-test-fields.md)).
- **A pick-and-place cell** where the Panda plans with damped-least-squares IK and
  lifts by real finger contact - a missed grasp is a failure, not an animation. A
  production run places six parts one after another into slots, counting parts placed,
  failures and throughput ([ADR 0019](adr/0019-factory-production-run.md)).
- **Friction from the literature, not from max().** Contact friction is a property
  of a *pair* of surfaces: 26 pairs (rubber on concrete, PTFE on wood, aluminium on
  steel...) with cited kinetic and static coefficients, confidence labels and a
  generated [reference page](CONTACT_PAIRS.md), applied contact by contact
  inside the MuJoCo step ([ADR 0010](adr/0010-sourced-contact-pairs.md)).
- **Motors and wheels lose energy where real ones do.** The kit gearmotor is a Pololu
  37D 30:1 from its datasheet - speed-torque line, plus gearbox friction derived from
  its no-load current - and wheels carry rolling resistance from the load they bear
  ([ADR 0011](adr/0011-drivetrain-and-axle-losses.md)). A bare gearmotor
  runs at the rated 330 rpm; a test cart coasts down within 1 % of the closed form.
- **Arms that hold still on a moving base.** A servo's damping is integrated by the
  solver instead of applied a step late: the mobile manipulator used to chatter at its
  torque limits and creep 12 cm while "standing"
  ([ADR 0014](adr/0014-servo-damping-integrated-implicitly.md)). The build stage
  reads a machine as modules - base, drives, wheels, supports, arm, tool - and predicts
  how it stands before it runs: which parts carry it, its tilt and its stance margin,
  within 0.1 degrees and 1 mm of where the simulator settles
  ([ADR 0015](adr/0015-machine-structure-and-stance.md)).
- **Arms that do a task, judged by the physics.** Move the gripper in straight steps
  instead of joint by joint, teach poses into a program, check grasps, and generate a
  pick-and-place program solved for the arm you built: in the Pick and place field the
  arm lab puts the cube in the tray, and a missed grasp stops the program
  ([ADR 0016](adr/0016-arm-tasks-tool-moves-poses-grasp-checks.md)).
- **A mobile manipulator that fetches by itself.** Programs can drive the base to a
  point and heading; the Fetch program - solved for the machine you built - drives 1.6 m
  to a table, picks up a cube, backs away, drives to a bin and lets go, and the Fetch
  field's goals are all met at 34 s
  ([ADR 0018](adr/0018-fetch-drive-to-a-point.md)). Running it exposed that
  MuJoCo's soft friction let a held cube slide out of the jaws at 2 mm/s; two noslip
  iterations stop that without touching real sliding, which also corrected a curb result
  and freed a Menagerie arm grinding against its own base
  ([ADR 0017](adr/0017-friction-that-holds.md)).
- **How steep before it tips, predicted and then measured.** The build stage predicts the
  slope each side of a machine can take by rocking it, quasi-statically, on a tilted
  floor - a machine that rocks onto a caster has not tipped. On the tilt table, with a
  trip rail set against its wheels, the mobile manipulator goes over at 54 degrees where
  its design says 54.3 (55.8 about the rail's edge); without the rail it slides from 16,
  because only its drive wheels resist a side load. A doorway field checks turning through
  a 50 cm door without touching the frame
  ([ADR 0020](adr/0020-doorway-and-tilt-table.md)). The build stage also warns when a
  design starts in the air, since a run starts it where it was built: the examples used to
  fall 4.3 cm, and landing with the wheels driven left a caster swivelled 37 degrees by the
  second curb ([ADR 0023](adr/0023-machines-start-on-the-floor.md)).
- **Results with their spread.** From a run's report, "Repeat with variations" runs the
  field 20 more times in the background - the machine set down up to 2 cm and 3 degrees off
  its mark, carrying up to 0.5 kg, on surfaces anywhere in their published friction range -
  and shows the spread and what moved it most. The arm on a cart tips between 51.4 and 58.4
  degrees (54.5 as designed); a 3 degree turn on the table moves it most, and with a payload
  aboard the prediction holds within 0.3 degrees. Its Fetch program met every goal in all 20
  runs, and showed a loaded cart rocking between its casters under its own arm
  ([ADR 0024](adr/0024-runs-under-variation.md)) - so a program's arm poses now say
  what point they were aimed at, and where the tool got to is checked and corrected
  ([ADR 0025](adr/0025-poses-aimed-at-a-point.md)).
- **How sure a result is.** A sweep's rates come only from the set-ups drawn at random,
  with an exact 95 % bound: the arm on a cart fetched its cube in 8 of 8 drawn set-ups,
  which shows only that at least 69 % of such set-ups would; drawn 59 times, it fetched it
  in all 59 - it fails in under 5 % of them, with 95 % confidence
  ([ADR 0028](adr/0028-rates-from-runs-drawn-at-random.md)).
- **A tip test done as in a lab.** The tilt table sets a machine square against its rail
  before tilting: one set down turned 3 degrees now tips where it does straight, 54.0
  degrees, instead of 3 degrees early
  ([ADR 0029](adr/0029-tilt-test-squares-the-machine.md)).
- **Shoved mid-task.** A run can be disturbed partway - the machine shoved, a part moved -
  and each set-up compared with itself undisturbed. Shoved once it has stopped at the
  table, the arm on a cart still fetches its cube after a 4 N s shove (about 2 cm) in 9 of
  9 set-ups and after a 6 N s one (about 6 cm) in 3 of 9 - in none with its arm poses run as
  taught; a cube moved 5 cm is never found, since nothing looks for it
  ([ADR 0030](adr/0030-disturbances-during-a-run.md)). "Repeat with disturbances" in a
  run's report runs them in the background. Each set-up is run with and without the
  disturbance, and the two are the same run until it, step for step - so a sweep says how many
  successes the disturbance broke and how sure that is, from the set-ups whose outcome changed
  (an exact McNemar test): without looking again, a cube moved 5 cm after the look broke 8 of
  8 drawn set-ups (p = 0.008); with it, 1 of 59 (p = 1: no effect shown) - in that one the
  jaws came down on the moved cube and, rising off it, dragged it off the table
  ([ADR 0036](adr/0036-paired-runs.md)).
- **Back to its stop.** Pushed more than 2 cm off the stop its program drove it to, a
  machine now drives back - backing off and coming in straight, as it first did - and
  reaches again: shoved 6 N s at the table, the arm on a cart fetches its cube in 8 of 9
  set-ups instead of 3
  ([ADR 0031](adr/0031-going-back-to-the-stop.md)).
- **It looks before it grasps.** The Fetch table has a depth camera on a stand behind it - an
  Intel RealSense D435 with its maker's field of view and depth noise, its pictures cast as
  rays in MuJoCo - and the Fetch program looks for the cube once the cart has stopped: the
  table's plane is removed, what stands on it gathered and the cube's top face fitted, with
  no learned model and no GPU. It finds the cube within 2.4 mm wherever it is set down up to
  8 cm off its plan, and the arm reaches where it was seen: moved 5 cm as the cart stands at
  the table, the cube is fetched in 9 of 9 set-ups instead of none. One set down beyond the
  arm's reach from its stop is seen but not fetched
  ([ADR 0032](adr/0032-a-camera-at-the-table.md)). The program shows the camera's depth
  picture, the cube in green.
- **And looks again.** Just before the jaws go down, the camera takes one more picture; if
  the cube has moved, the jaws go back and the program looks again before touching it - as it
  does when a reach is stopped or the jaws close on nothing. The cube moved 5 cm after the look
  is now fetched in 9 of 9 set-ups instead of none
  ([ADR 0033](adr/0033-looking-again.md)). A reach stopped on the cube first rises off it
  the way it came, instead of dragging it off the table, and a cube whose top the open jaws
  hide is not taken for gone - the picture shows its surface where it was seen: moved 5 cm 2 s
  after the look, the cube is fetched in all 59 drawn set-ups (58 before), and undisturbed none
  looks again for nothing (2 did) ([ADR 0037](adr/0037-rise-first-and-read-the-place.md)).
- **And stops where the cube is.** The camera sees the table from anywhere, so the Fetch
  program looks before it drives and stops where the cube actually is - sideways as far as it
  moved, towards it only as far as the cart stays clear of the table. Set down 15 cm to either
  side or 6 cm further along the table, the cube is fetched (both were missed); 8 cm further
  along, out of the arm's reach from any stop clear of the table, the program stops at the
  table and says so instead of reaching for the wrong place
  ([ADR 0035](adr/0035-the-stop-follows-the-cube.md)).
- **A camera that fails, noticed.** The table camera can freeze on its last picture, or go
  dark, as a disturbance. Each picture carries its frame number and how much of it has depth,
  and a program that gets three in a row that are not new, or have no depth, stops at the look
  and says why - before it moves. Frozen as the cube is moved 5 cm, the program used to grasp
  twice where the stale picture showed the cube; now it stops at the look and says "the
  camera's picture is not new", in all 9 set-ups and in all 59 drawn ones, and every
  undisturbed run is as it was to the millisecond: no false alarm
  ([ADR 0038](adr/0038-a-camera-that-can-fail.md)).
- **How well the camera must be mounted.** The table camera can be set off where the program
  believes it - shifted, panned, tilted - to see how far a hand-set or bumped stand may be off.
  A closed form says how far off the cube is then seen (15 mm sideways per degree of pan at
  the camera's 0.88 m; 13 mm along and 8 mm down per degree of tilt), and shifting the camera
  measures how far off the jaws may be aimed: 10 mm too far or too low, 25 mm to either side,
  more the other ways. Over 59 drawn set-ups each, panned 1.5 degrees, tilted up 0.5 or
  raised 10 mm, every one was fetched (at least 95 %); 10 mm towards the cart, 58 of 59; tilted
  up a degree, 8 of 59 ([ADR 0039](adr/0039-how-well-the-camera-must-be-mounted.md)).
- **How gently, beside whether.** Every run now follows the part it carries: the hardest push
  on it from the machine, the table and the bin (in a step and over 50 ms), how far it leaned
  and how far it fell when let go. The arm on a cart squeezes the cube at about 4.8 N - thirty
  times its weight - and lets it fall about 6 cm into the bin; in 4 of 59 drawn set-ups that met
  every goal, it first pressed the cube into the table. With the cube moved and the program
  blind, a jaw comes down on the cube and presses it into the table at 5 N
  ([ADR 0040](adr/0040-how-gently-a-part-is-handled.md)).
- **A cart that stands on all four.** Those presses came from the cart: its casters stood
  6.5 mm off the floor, so it teetered on its drive wheels, and loaded behind its axle it tipped
  forward as the arm reached over the cube, the jaws coming down on it. Its casters now reach the
  floor its drive wheels stand on: it pitches under 0.2 degrees, and the table only ever carries
  the cube. The price is curbs - unable to pitch, it stalls at one until it has slewed onto a drive
  wheel, over an 18 mm curb at 11.6 s instead of 4.1
  ([ADR 0041](adr/0041-the-cart-stands-on-all-four.md)).
- **Set down, not dropped.** The Fetch program let the cube fall 6.8 cm into the bin: the kit
  arm cannot bring level jaws any lower there without hitting its own cart. Now the jaws close on
  the cube's upper half, squeeze a little harder once they feel it, and over the bin tilt down
  as far as lowers it most - 25 degrees for the kit cart. In all 71 set-ups of a sweep the cube
  falls 3 mm (median; 1.1 cm at most), lands at a quarter of the push it did, and comes to rest
  upright. Each run now also says how far a part leaned before it was held and at rest
  ([ADR 0042](adr/0042-set-down-not-dropped.md)).
- **Does a result survive a micrometre?** A sweep runs each drawn set-up once, so it cannot
  tell a result the design earns from one it happened on. `sweep --jitter 5` runs each again
  five times with the machine set down a micrometre off - the same set-up to any lab - and sets
  each measure's spread under that against its spread across set-ups. The tilt table tips within
  0.05 degrees of itself; Fetch's outcome never changed in 59 set-ups, its times, squeeze and
  lean are the design's, and the set-down is partly chance: the cube's fall into the bin spreads
  0.29 cm under a micrometre against 1.0 cm across set-ups
  ([ADR 0043](adr/0043-the-knife-edge-check.md)).
- **Bring your own robot.** A robot that does not exist yet can be tried: drop its URDF or
  MuJoCo file on the window, or choose *Robot: ... → Import a robot from its file* in the Joint
  lab. Little World copies it into your robot library, adds a position servo to every joint the
  file leaves without a motor - stiff enough to hold the robot within half a degree against its
  own weight, no stronger than the file's effort limit - and says in plain words what it found,
  what it added and what to check (a misspelt attribute, a joint too weak to hold the arm up, a
  mesh MuJoCo cannot read). The robot is then driven from the keyboard, programmed with blocks
  and placed like the Menagerie arms ([ADR 0044](adr/0044-robots-from-their-own-files.md)).
- **The tool travels its line.** In Tool mode a step now carries the tool along a straight line
  at 5 cm/s instead of letting each joint take its own path - a 10 cm step of the kit arm strayed
  up to 12.7 mm from its line, now 0.3 mm - and holding the arrow keys, or Page Up and Page Down,
  drives the tool continuously until it can reach no further. The same for every arm: kit,
  Menagerie or imported ([ADR 0045](adr/0045-the-tool-travels-its-line.md)).
- **The first hour, checked by the app.** The Guide now opens on five short lessons - drive the
  cart through the doorway, bring the gripper to the cube by moving the tool, program the arm to
  lift it, bring in a robot from its file, ask how sure a result is. "Start this lesson" sets up
  the machine and the field; the app watches the work and ticks a lesson off when it is done, in
  any order, saying in a line what is still missing ([ADR 0046](adr/0046-the-first-hour-checked-by-the-app.md)).
- **A gripper from its file.** A robot brought in from its file with a gripper at its end is now
  driven as a gripper: the import finds which joint closes it and which links are its jaws, it is
  driven by how closed it is, 0 to 100 %, and squeezes with its file's effort (12 N at each jaw
  if the file gives none). The grasp blocks and Tool mode's Open and Close work with it as with
  the Panda's: a box it holds, turned over by the elbow, stays within half a millimetre of where
  it was held ([ADR 0047](adr/0047-a-gripper-from-its-file.md)).
- **A grasp the program feels.** The Fetch program no longer asks the simulator whether it holds
  the cube: it reads its gripper's servos as a real one reports them - where each jaw stopped
  against where it was sent, how fast it moves and the current it draws, counted as an XH430's
  registers count - and takes the cube as held when both jaws have stopped short and push. Over
  71 set-ups it felt every hold the contacts showed and none that was not there; sweeps count how
  often feeling and contacts agree ([ADR 0048](adr/0048-a-grasp-the-program-feels.md)).
- **Certified on draws it was not tuned on.** Every sweep now says which seed drew its set-ups,
  and a ledger in the repository lists the seeds each decision was shaped on. A held-out sweep
  must draw with a seed the ledger has not seen - it is entered before the sweep runs - and is
  read beside its tuning sweep, every value outside the tuned range named. On 59 fresh set-ups
  the Fetch program met every goal in all 59, as on the draws it was tuned on; one knock on the
  table, stronger than any seen before, is reported as found ([ADR 0049](adr/0049-tuning-draws-and-held-out-draws.md)).
- **What one contact point carries.** A census counts, at the moments a Fetch run's results are
  decided, the contact points between each pair of parts - and how many MuJoCo would find with
  its multiple-contact search on, which ADR 0027 turned off. Every face on a face the results rest
  on - the jaw pads on the cube, the cube on the table and in the bin, the treads on the floor -
  is box on box and keeps its count either way; only the casters' wheels touch at one point
  instead of four or five. It also found that at the bin the cart stands on three: one caster
  lifts 0.2 mm ([ADR 0050](adr/0050-a-contact-census.md)).
- **What looking again earns.** The Fetch program's recovery - when its reach goes wrong, go back,
  look again, reach where the cube now is - is now tried against three simpler ones on the same
  set-ups: reach again where the cube had been, look again but reach as far off in a random
  direction, and stop. With the cube moved after the look, looking again fetched it in 9 of 9
  set-ups, each simpler one in none; elsewhere all four tie, and the report says why
  ([ADR 0051](adr/0051-what-looking-again-earns.md)).
- **How late is too late.** A detector outside a program can raise an alarm, and the program looks
  again as its own recovery does. Replaying a failing Fetch run with an alarm every half second
  shows when looking again can still rescue it: with the cube moved after the look, until the
  program leaves the table - or, where its own closing jaws tip the cube over, only until then; its
  own check came at least 0.28 s before that in every set-up. A false alarm costs about 6 s and
  broke 1 run of 71, one raised while the cube was held
  ([ADR 0052](adr/0052-how-late-is-too-late.md)).
- **Time passes while the program looks.** A sweep can run with the program's pictures, servo
  commands and readings late by sourced amounts - the camera's frame interval and the finder's
  measured time (139 ms), a Dynamixel bus at its defaults (7.6 ms out, 33 ms back) - and the Fetch
  program met every goal it met without. Late pictures alone change nothing, even half a second
  late, since it acts only on a cube that stands still; its limit is its grasp check's half second,
  which a command's trip to the jaws and the hold's trip back must fit in: 0.2 s each way held,
  0.3 s did not ([ADR 0053](adr/0053-time-passes-while-the-program-looks.md)).
- **Searching for the failure, measured.** A compass search over the variation box, following a
  run's margin towards failing, was tried against the sweeps' own draws: on the tilt table it found
  the worst corner the sweeps already run, and on the Fetch field - whose handling margins change by
  chance at the millimetre scale - it found a knife edge where a random draw had found a real corner.
  The sweeps keep their plan ([ADR 0054](adr/0054-searching-for-the-failure.md)).
- **Watch it work.** A *What's new* button in the top bar opens four demonstrations of recent
  work, one press each: the cube is moved 5 cm after the program looked, and the arm rises, looks
  again and fetches it from where it went; the camera freezes, and the program sees its pictures are
  old and stops; the cart is shoved at the table, drives back to its stop and carries on; and *Look
  again*, a new button in the Program panel, makes a running program look again when you press it.
  While a program runs, the panel says what its camera last saw and what its jaw servos feel
  ([ADR 0055](adr/0055-watch-it-work.md)).
- **The factory cell judged as a factory judges one.** Under a production run, a line now says how
  many parts landed within the room their slot gives them, the worst of them and the slowest part.
  Measured over 214 parts: small blocks land 1.4 to 4.4 mm off their slots, barely capable of the
  6.5 mm they have (Cpk 1.05), at 12 to 14 s a part; tall blocks fail the run. Why: the simulated Panda
  sags 4 mm with no gravity compensation, and its hand squeezes 1.6 N where the real one's datasheet
  gives 70 N - two fixes previewed for the owner to decide
  ([ADR 0056](adr/0056-the-factory-cell-judged-by-its-process-window.md)).
- **Tall parts, placed.** The factory cell now lowers each part straight down into its slot and opens
  its hand only 8 mm past the part to let go. Moved joint by joint, the descent had swung the tool up to
  15 mm off the vertical, and a tall part caught the one beside it: every production run of tall blocks
  failed. Now every one of 114 tall parts lands within its room, and small ones do too, at the wider
  feeder spread as well ([ADR 0057](adr/0057-the-cell-lowers-its-parts-straight-down.md)).
- **A motor run hot - and a cart that does not notice.** A run can now have one of its motors
  weakened partway, as physics says: a winding 50 K hot keeps 84 % of its stall torque (copper's
  0.393 %/K) at the same free speed. The kit cart drives exactly as before - on the sprint, the ramps,
  the push, the curbs and the Fetch - because its drive never asks a motor for more than its 0.5 N m
  operating cap; on the sprint a motor can drop to 30 % before anything changes. What's new - its
  demonstrations now newest first - runs it: the arm on its cart fetches the cube with its left motor
  hot, the drive panel marking the motor weakened ([ADR 0058](adr/0058-a-motor-run-hot.md)).
- **How near it is to tipping.** While a machine drives, the panel now says how many degrees it has
  left before it tips - its weight and its accelerations both, by Papadopoulos and Rey's force-angle
  measure - and the run report the fewest. On the tilt table the arm on its cart counts down about three
  quarters of a degree for each degree of table and runs out at 53.5, as it goes over; a hard stop from
  full speed takes 3 to 4 degrees from it. What's new shows it ([ADR 0059](adr/0059-how-near-it-is-to-tipping.md)).
- **Look again, not once it holds.** The Program panel's *Look again* greys out once the program has
  felt the cube in its jaws: pressed then, it opened the jaws in the air and dropped the cube, and the
  run took 7.4 s longer ([ADR 0060](adr/0060-once-it-holds-it-does-not-look-again.md)).
- **How close to slipping.** While the arm holds something, the drive panel says how much of its
  grip's friction is in use - 0 with nothing pulling it along the jaws, 100 % when it slides. The
  ordinary cube uses about 38 %; made 16 times as heavy it reaches 100 % on the lift and slides out,
  which What's new shows ([ADR 0061](adr/0061-how-close-to-slipping.md)).
- **Where runs fail.** After *Repeat with variations* or *Repeat with disturbances*, each line that
  missed says where: the first goal its runs missed ("missed: lifted 9") and what a program that gave
  up was doing ("gave up: looking 9"); every sweep report has the table. Two disturbances that both
  cost every run can fail in different places, and now it shows
  ([ADR 0063](adr/0063-where-runs-fail.md)).
- **What a sweep can show, before it runs.** Under *Repeat with variations* a line says what its
  draws can bound ("8 drawn: if all succeed, failures under 31 %"), and under *Repeat with
  disturbances* how many set-ups a disturbance must break before the paired test can be sure of it
  ("6 of the 8 drawn") ([ADR 0064](adr/0064-plan-the-draws.md)). What's new's *Where repeats
  fail* runs the Fetch once and stops on its report, both lines under its buttons.
- **The Panda holds itself up.** In Real mode the Panda is held against gravity, as its own
  controller holds the real arm, and its hand squeezes 70 N with its fingers moving 50 mm/s, as the
  Franka Hand's datasheet gives: the cell's tool stops within half a millimetre of every point, where
  it sagged 5 to 7 mm, and its parts land within about a millimetre of their slots, where they landed
  2 to 6 mm out. What's new's *The Panda holds itself up* runs it with tall blocks
  ([ADR 0065](adr/0065-the-panda-holds-itself-up.md)).
- **A squeeze set in newtons.** A Joint action block can say how hard the jaws squeeze, in newtons at
  each pad: the kit gripper's servos then cap their current at it, as a ROBOTIS servo in
  current-based position control does. Closed on a fixed box at 1 to 6 N they push within 2.5 % of
  the setting; where a part sits along the rotary jaws still sets how hard it is held. What's new's
  *A squeeze set in newtons* runs the Fetch at 7 N: the grip's friction in use peaks at 60 %, where
  the closing ramp's own squeeze peaks at 80 % ([ADR 0066](adr/0066-the-jaws-squeeze-by-current.md)).
  Side by side on 130 set-ups, the Fetch's own program keeps its ramp: squeezing by current met no
  goal more, squeezed less evenly and took 0.7 s longer ([ADR 0070](adr/0070-the-fetch-keeps-its-ramp.md)).
- **A roller conveyor.** A new test field: nine powered 50 mm steel rollers carry two 160 mm pallets,
  the kit's cube on each, at 0.1 m/s to a stop plate - the first comes to rest against it, the next
  queues behind - carried within 0.1 % of the rollers' speed. Parts this short ride on pallets, as
  on an assembly line; MuJoCo's cylinders let a box sink into them, so the rollers are capsules, a new
  shape. What's new's *A roller conveyor* runs it ([ADR 0067](adr/0067-a-roller-conveyor.md)).
- **The cell fed by a conveyor.** In Real's pick-and-place panel, *Conveyor: on* puts the roller
  conveyor on the cell's table in the input tray's place: pallets carry the parts to its stop, the
  Panda picks each off its pallet, and the empty pallet goes back to the line's start with the next
  part. Each pallet locates its part between two bars, so every part arrives within 4 mm of its place
  at the stop and lands within a millimetre of its slot. The rollers are friction rollers: under a
  held pallet they stand still, as a real accumulating line's do. What's new's *The cell fed by a
  conveyor* runs six parts ([ADR 0068](adr/0068-the-cell-fed-by-a-conveyor.md)).
- **The cell finds its parts.** *Locate: camera* in Real's pick-and-place panel: the cell's overhead
  camera, as a RealSense D435 with its depth noise, finds each part where it was put, instead of the
  simulation telling it; the arm first moves out of the camera's view. Its depth picture shows in the
  corner of the view, the part green. Every part it looked for it found and the cell placed, 216 of
  216, each seen within 1.5 mm of where it was. What's new's *The cell finds its parts* runs it
  ([ADR 0069](adr/0069-the-cell-finds-its-parts.md)).
- **A reach that feels what it meets.** Reaching down for the cube, the program reads the arm's
  servos as it reads the jaws': where each joint stands against where it was sent. A cube moved
  under a jaw since the last picture holds the arm back, and the program rises and looks again
  0.2 s after the jaw met it - it pressed the cube into the table for 2.4 s before, until the reach
  timed out - and fetches it 2.4 s sooner. Undisturbed, no reach is felt. The Program panel says how
  far the arm's joints stand from where they are sent, and when a reach felt something. What's new's
  *It feels the cube under its jaw* runs it ([ADR 0071](adr/0071-a-reach-that-feels-what-it-meets.md)).
- **One command, and a doctor.** `little-world` opens the window with What's new on the left;
  `little-world demo NAME` starts a demonstration, `little-world build` the builder, `--real` the
  complete robots. `little-world doctor` checks what an installation needs - Python, MuJoCo, the
  assets, a second of physics, an OpenGL window - and prints the line that mends whatever is
  missing. Designs are kept in your own Little World folder
  ([ADR 0072](adr/0072-from-a-clone-to-a-running-window.md)).
- **Evidence you can measure again.** `little-world evidence` runs thirteen of the project's
  headline measurements on your machine and prints each beside the number recorded for it -
  holds, or differs; two of them are flaws kept in the list. `pytest -m "not slow"` is a quick
  tier of about 1,000 tests in a minute; two GitHub workflows run it and the rest. What was found
  by looking at the whole project again is in [EVALUATION.md](EVALUATION.md)
  ([ADR 0073](adr/0073-evidence-anyone-can-measure-again.md)).
- **Energy from nowhere.** Every run now checks its contacts: a contact gives back the energy two
  bodies put into it as they press together, never more, and one that gives back more than lifting
  the lighter of them 2 mm would take is the engine making energy. The drive panel says so under
  *touching* while the run goes, and the run's report after Stop; every sweep report has a physics
  check. On the Curb run it catches the engine at it: a caster's wheel against the 10 mm curb's
  edge gives the kit cart 78 mJ it never took before the cart climbs over - What's new's *Energy
  from nowhere* shows it. Just past its line it also flags the Panda's fingers as they close on a
  part in Real's cell, and the Fetch's jaws on its cube in about one set-up in six - at most 1.8 mJ
  ([ADR 0074](adr/0074-energy-from-nowhere.md)).
- **A radar on the frontier, keyed on its own decisions.** New robotics papers, open
  models, repositories and MuJoCo's own changelog are scored against this project's
  decision records and roadmap and filed under the decision each could change, with the
  words that matched; a triage (adopt, learn, watch, skip) is kept. Its first run found the
  project eleven MuJoCo releases behind, and running the suite on the newest showed which
  three wheel-contact results would move and why
  ([ADR 0021](adr/0021-frontier-radar.md), [radar](RADAR.md)). It reads journals'
  tables of contents too, and its brief feeds a file of numbered proposals - where an
  idea would go in this app, how we would know it worked, what it costs - that the owner
  accepts or declines ([ADR 0026](adr/0026-frontier-brief-and-proposals.md),
  [frontier](agents/FRONTIER.md)). What it and the weekly reading judged stays in the
  repository - 81 papers, releases and engine changes so far, each with its verdict and why -
  and can be searched: `python -m little_world.radar search camera calibration`
  ([ADR 0034](adr/0034-the-radar-keeps-what-it-read.md)).
- **990 automated tests**, including OpenGL window tests that drive the interface
  through its real input callbacks. Every physical claim states its limits
  ([validation](VALIDATION.md)).
