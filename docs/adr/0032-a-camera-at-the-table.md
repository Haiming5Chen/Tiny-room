# A depth camera at the table: the program looks for its cube and aims where it was seen

**Problem.** Every pose of the Fetch program was solved for the cube where the field puts it.
Moved 5 cm sideways once the cart stood at the table, the cube was fetched in none of 9
set-ups, and moved 3 cm in 7 of 9 - by the jaws' own width (ADR 0030, 0031). Traced: the
jaws came down at the planned place, a finger landed on the moved cube, and closing pushed
it about without holding it. Nothing in a program could look. The owner accepted FR-011 on
3 October 2026: find the cube with a depth camera, classically - remove the table's plane,
fit the box - and aim the grasp there.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo casts rays against its own
geometry (`mj_multiRay`, rays from one point); a depth picture is the sensor's pixels cast
that way - wrapped, as `MujocoBackend.cast`. MuJoCo's renderer can give a depth buffer too,
but needs an OpenGL context: EGL is missing in the cloud workspace and the headless suite has
no display, while rays need none and give the same depth on every machine. Finding a known
box on a table without learning is textbook (a support plane by RANSAC, clusters above it, a
fitted box: Open3D's `segment_plane`, PCL); written here in numpy rather than adding Open3D.
Learned pose estimators such as FoundationPose need a GPU; the app runs on an Intel Mac's CPU.

**Unique contribution.**
- *The camera.* The Fetch table has a camera stand 10 cm beyond its far edge: an Intel
  RealSense D435 0.9 m up, looking down 60 degrees at the front of the table, held out on a
  bracket so that the post is not in its picture (`fields.CAMERA_AT`; `Field.camera` names
  the camera and its sensor). Its numbers are the maker's (`perception/sensors.py`, standard
  library): depth over 87 x 58 degrees, 848 x 480 pixels - Intel's best depth resolution for
  it - nothing nearer than 16.8 cm, and depth noise z^2 x 0.08 px / (f x 50 mm), the stereo
  error of Keselman et al. (2017) with their measured disparity error: 2.7 mm at the cube's
  0.87 m, 14 mm at 2 m, inside the maker's "under 2 % at 2 m".
- *A picture.* `perception/eye.py` casts only the pixels that can see 12 cm either way of
  where the part was planned (about 23,000 rays, 50 ms), adds the sensor's noise from a
  seed of the set-up's own, drops depths outside the sensor's range, and makes points.
  `MujocoBackend.camera_pose` gives the camera's pose: an exact calibration.
- *Finding the cube.* `perception/boxes.py`: the plane most points lie in is the support
  (RANSAC within three times the noise, then least squares); points standing more than
  8 mm above it are gathered into clusters (links under 1 cm); a cluster's top face is its
  points near its top, laid back along the rays that saw them onto the top's height - a
  stereo camera's error lies along its rays, so this takes it out of where they lie across
  the face - and measured as a rectangle (turned as the smallest round them, its sides
  between the 3rd and 97th percentiles). The cluster is the cube when the face and the
  height are the cube's own within 8 mm, standing or on its side. The cube's size is known,
  as a lab knows its parts; its place and turn are measured, never read from the simulator.
- *A look block.* `Block('look', object, value=seconds watched, duration=timeout,
  point=where it was planned)`; a program with one is version 3, which older readers refuse
  (ADR 0016's rule). The runner takes a picture every 0.1 s through a `see` callback; the
  look ends, after watching for its `value`, once three pictures in a row agree within
  5 mm, and fails at its timeout saying why: "not found" or "it would not keep still". Then
  the poses at that stop aimed within 15 cm of where the object was planned aim where it was
  seen - solved for it before they move, when it was seen more than 5 mm away - and ADR
  0025's checks correct them there; the next drive forgets it.
- *The Fetch program looks* when its field has a camera. Its jaws come in short of the cube
  (`ready`: the fingers' reach past the tool point, the cube's half width and 1 cm), at the
  height they will hold over it, because held over it - as before - a finger hid 40 to 75 %
  of the top of a cube moved under it from the camera. Once stopped: look for a second, jaws
  over where the cube was seen, down, grasp. `sweep --blind` runs the program without looking;
  the tests of ADR 0025, 0030 and 0031 run it that way, as they were measured.
- *In the window.* "Look for" blocks, a form to add one, and the table camera's last depth
  picture in the corner of the view (near warm, far cool, the cube green) with how far from
  the plan it was seen (`Canvas.pixels`).
- *Found on the way.* A move could only shift a part; it can turn it too
  (`MujocoBackend.shift(..., turn)`, `Disturbance.turn`).

**Blueprint and builder.** Designs are untouched: the camera is the field's, a Blueprint
camera on the field's own stand. The sensor's model lives outside the core.

**Result.** How well it sees (`python -m little_world.perception`;
docs/sweeps/2026-10-04-fetch-camera-accuracy.md): the cube set down at 80 placements - up to
8 cm off its plan either way, turned up to 45 degrees - and looked at with the cart at its
start:

| Camera | Found | Position error, median / largest | Turn error, median / largest |
| --- | --- | --- | --- |
| without noise, 1 picture a placement | 80 of 80 | 1.2 / 1.9 mm | 0.3 / 2.4 deg |
| D435 noise, 20 pictures a placement | 1600 of 1600 | 1.3 / 2.4 mm | 0.6 / 6.0 deg (9 pictures over 5) |

FR-011 asked for 5 mm and 5 degrees. About 1 mm of the position error is a bias towards the
camera: points at the top of the cube's near side faces pass for top face.

Fetch, arm on a cart, MuJoCo 3.10.0: the disturbance sweep of ADR 0030 on its nine set-ups,
the program looking (docs/sweeps/2026-10-04-fetch-mobile-manipulator-disturbed-looking.md),
against the same program blind as ADR 0031 measured it on 3 October:

| Disturbance | blind (ADR 0031) | looking | camera saw it moved |
| --- | --- | --- | --- |
| none | 9 of 9 | 9 of 9 | 0.1 cm |
| shoved 4 N s at the table | 8 of 9 | 9 of 9, last goal +0.8 s | 0.1 cm |
| shoved 6 N s at the table | 8 of 9 | 9 of 9, +11.3 s | 0.1 cm |
| cube moved 3 cm sideways | 7 of 9 | 9 of 9 | 3.0 cm |
| cube moved 5 cm sideways | none | **9 of 9** | 5.0 cm |
| cube moved 5 cm sideways, 2 s later | - | none | 0.1 cm |

Every sighting was within 1.8 mm of where the cube really was. ADR 0030 moves the cube 0.3 s
after the cart has stopped, while the camera watches; moved 2 s later, as the jaws come over
it, the cube is missed in every set-up and the grasp check says nothing is held - one look is
one look. Shoved, the cart now fetches its cube in every set-up: the shove comes while the
camera looks, with the jaws short of the cube, so it no longer knocks the cube over - the
set-ups ADR 0031 lost had theirs knocked - and after going back the program looks again.
Looking costs 2.5 s undisturbed: the cube is in the bin at 35.8 s (median) instead of 33.3.

The cube set down elsewhere before the run, the design as designed, blind and looking
(docs/sweeps/2026-10-04-fetch-cube-set-down-elsewhere.md; `python -m little_world.perception
--fetch` runs them):

| Cube set down | blind | looking | seen off the plan | seen off where it was |
| --- | --- | --- | --- | --- |
| 3 cm to the cart's left or right | every goal | every goal | 3.0 cm | 1.8 mm or less |
| 5 cm left or right | missed | every goal | 5.0 cm | 1.0 mm or less |
| 8 cm left or right | missed | every goal | 8.0 cm | 1.4 mm or less |
| 3 cm further along the table | every goal | every goal | 3.1 cm | 0.9 mm |
| 6 cm further along | missed | **missed** | 6.0 cm | 0.4 mm |
| 2 cm nearer the cart | every goal | every goal | 1.8 cm | 1.9 mm |
| 3 cm further and 5 cm left or right | missed | every goal | 5.9 cm | 1.6 mm or less |
| where planned, turned 20 or 40 deg | every goal | every goal | 0.2 cm | 1.6 mm or less |
| 5 cm left, turned 30 deg | missed | every goal | 5.0 cm | 1.5 mm |

Blind: 6 of 14 placements; looking: 13 of 14. The one missed looking was seen within 0.4 mm
but lies beyond the arm's reach from the stop planned for the cube where it should be.

Undisturbed, the 59 drawn set-ups of ADR 0028 again, looking
(docs/sweeps/2026-10-04-fetch-mobile-manipulator-59-looking.md): every goal in all 71 runs,
59 of 59 drawn - it fails in under 5 % of such set-ups, with 95 % confidence, as blind - the
cube in the bin at 35.8 s (median; 33.3 blind) and every look within 2.0 mm of where it
really was.

Checked in `tests/test_perception.py` (7): the D435's numbers; a cube found within 1.5 mm and
1.5 degrees in pictures drawn by intersecting rays with boxes in numpy, upright or on its
side, turned, on a tilted table, and within 5 mm and 5 degrees with the camera's noise;
nothing found where there is nothing or something of another size. And in
`tests/test_look.py` (9): the runner's rules - a look waits for three pictures that
agree, sees a cube moved while it watches where it came to rest, fails saying why, re-aims
only the poses near the object, forgets at the next stop; programs with a look are version
3; reports say how far off the cube was seen; the Fetch table's camera finds its cube within
5 mm through MuJoCo's rays; in full physics, the cube moved 5 cm as the cart stands at the
table is fetched; and, with a display, the window shows the camera's picture.

**Boundaries.** One camera, fixed, its pose known exactly; its noise is the stereo error
alone - no holes on dark or shiny surfaces, no flying pixels at edges, no infrared pattern.
A cube moved after the look is missed (measured above): seeing it would take looking again,
when a grasp misses. The arm has four joints and cannot turn its jaws to the cube's turn:
the turn is measured, not used. The program still drives to the stop planned for the cube
where it was meant to be, so the arm reaches only as far as it can from there. The search
covers 12 cm either way of the plan. Ten pictures a second and the one-second watch are
chosen, not measured.
