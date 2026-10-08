# How well must the camera be mounted? A tolerance for the Fetch table's camera

**Problem.** The Fetch program reads the table camera's pictures by where it believes the
camera stands, `fields.CAMERA_AT` looking at `CAMERA_AIM` (ADR 0032). A real stand is set up by
hand and gets bumped, and nothing said how far off it may be: every result since ADR 0032 had
the camera exactly where it was believed to be. FR-021, accepted by the owner on 8 October
2026: find the largest error at which Fetch still succeeds in at least 95 % of drawn set-ups,
and predict it first.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo places the camera where the
model says; a calibration error is the gap between that and what the program believes, which
is the program's. Hand-eye calibration is how a lab closes the gap (DRHeC, arXiv 2609.36779,
by its title); camera shifts are among LIBERO-MAX's events (`arxiv:2609.36518`). Wrapped:
MuJoCo's camera, moved through the adapter, and the camera of ADR 0032.

**Unique contribution.**
- *The camera off, the program none the wiser.* `MujocoBackend.move_camera` sets a camera off
  the pose it was built at - shifted along the world's axes, then turned about its own (pan
  about its up axis, tilt about its right axis, roll about its view). An `Eye` given a
  `believed` pose casts its rays from the camera as it stands and reads them as if it stood
  where believed; `sweep.run(camera_error=CameraError(...))` and `sweep --camera-error
  X,Y,Z[,PAN,TILT,ROLL]` (millimetres, degrees) do both for a run or a varied sweep, and the
  report says so. With no error nothing changes.
- *The closed form.* `perception.calibration.seen`: a point at p is read at
  c + R R'^T (p - c') - a camera shifted by d sees the cube -d away; turned a small angle, the
  cube swings about the camera by the angle times its distance. Here the camera is 0.88 m
  from the cube, looking 60 degrees down: a degree of pan moves the seen cube 15.3 mm
  sideways, a degree of tilt 13.1 mm along the table and 7.8 mm down, a degree of roll
  0.3 mm (the cube is 2 cm off the camera's axis).
- *The jaws' reach, measured by shifting the camera.* A shift is an aim error of its own size,
  so shifting the camera along each axis measures how far off the jaws may be aimed; the
  closed form then says which angle uses that up.

**Blueprint and builder.** Untouched; the error is a condition of the run, as friction is.

**Result.**

As designed, one error at a time
([report](../sweeps/2026-10-08-fetch-camera-tolerance.md)): the cube was seen where the closed
form put it, within 2.5 mm (the finder's own 1 to 2 mm along the table included). Shifting the
camera gave the jaws' margins - the aim error a fetch survives: 10.5 mm too far along the
table (at 14.8 mm the pads' tips hold the cube and drop it on the way), 25 mm to either side
(at 30 mm a jaw comes down on it), 10.3 mm too low (at 12.8 mm it is carried to the bin without
the goal's 5 cm of lift; at 20 mm the fingers strike the table), and at least 38 mm towards the
cart and 29 mm too high. With 15.3 mm a degree, pan uses up the sideways margin between 1.6
and 2.0 degrees: 1.75 held, 2 did not. With 13.1 mm a degree along the table, and the finder's
1.5 mm, tilt uses up the 10.5 to 13 mm between 0.7 and 0.9 degrees: 0.75 held, 1 did not.
Tilted the other way the cube is seen nearer and higher, which the jaws take: 3 degrees held.

Then 59 drawn set-ups each, at errors at or just inside the last that held as designed, with
what was predicted for them written down before they ran:

| Camera off by | aim error, as designed | predicted | drawn set-ups fetched |
| --- | --- | --- | --- |
| panned 1.5 degrees | 23 mm sideways | 59 of 59 | **59 of 59**, at least 95 % |
| tilted up 0.5 degrees | 8 mm along, 4 mm low | 59 of 59 | **59 of 59**, at least 95 % |
| 10 mm up | 10 mm low | at the edge | **59 of 59**, at least 95 % |
| 10 mm towards the cart | 10.5 mm along | at the edge | 58 of 59, at least 92 % (one dropped on the way) |
| tilted up 1 degree | 15 mm along, 8 mm low | most miss | 8 of 59 |

So, for this bench, one error at a time: within 1.5 degrees of pan, 0.5 degrees of upward tilt
(3 downward) and 10 mm upward of where the program believes the camera stands, and less than
10 mm towards the cart. Errors add as the closed form adds them - two combined errors were seen
within 2.4 mm of it - but an aim near two margins at once (10.8 mm along and 25.4 mm
sideways) missed, so a budget for several errors must leave room between them.

Held by `tests/test_camera_error.py` (4): the error's data; the closed form (minus the shift;
15.3 and 13.1 mm a degree); the camera moved in MuJoCo, read where believed, the sighting moved
as the closed form says within 1.5 mm, and nothing changed when believed where it stands; and
the onset as designed - panned 1.5 degrees, fetched; 2 degrees, not.

**Boundaries.** One camera, one field and one gripper: the numbers are this bench's. Errors
are tried one at a time; together they add as the closed form adds them, which the 59-draw
runs do not test. The program does not look for its own calibration error: a part seen where
it cannot be (below the table, inside it) is not caught. The jaws' margins are measured as
designed and with the drawn set-ups; a different arm or gripper needs its own.
