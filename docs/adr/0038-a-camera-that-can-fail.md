# A camera that can fail: frozen or dark, and the program that notices

**Problem.** The Fetch program takes the table camera's word for where the cube is (ADR 0032
to 0037). A camera whose stream stops keeps sending its last frame, and three copies of one
frame agree perfectly - exactly what a look waits for (three pictures within 5 mm). Measured
with a new disturbance, the camera frozen as the cube is moved 5 cm at the table, every
picture taken on trust as before: 0 of 9 set-ups met their goals. In every one the jaws went
down where the frozen picture showed the cube, looked again (ADR 0033) to the same picture and
went down at the same stale place again; the program stopped on "Timed out: pose did not
settle" (5) or "Nothing held: the grasp missed" (4), saying nothing of the camera. A camera
gone dark at the table (no depth): 0 of 9, "Looked for fetch_cube: it would not keep still",
after the look's full five seconds
([report](../sweeps/2026-10-08-fetch-camera-faults-on-trust.md)). FR-018, accepted by the
owner on 8 October 2026.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo shows the world as it is; a
stalled or blind stream is the sensor's, and catching it is the program's. A RealSense frame
carries a frame number and a timestamp (librealsense), the means a program has to tell a new
frame from an old one. The weekly reading of 5 October named both faults (LIBERO-MAX's
sensor corruption; *Blackout vs. Freeze*, arXiv 2609.39145, by its title). Wrapped: the
camera of ADR 0032.

**Unique contribution.**
- *Faults as disturbances.* A disturbance can fail the field's camera as it happens, `camera`
  'freeze' or 'dark': alone (kind `camera`) or with a move, the camera failing first, so that
  its last picture is of the world before the move. Fetch gains "camera frozen as the cube is
  moved 5 cm" and "camera dark at the table", timed as "cube moved 5 cm sideways" is.
- *Pictures that say what they are.* Each picture carries a frame number, when it was taken
  and how much of it has depth (`Picture.frame`, `stamp`, `valid`). Frozen, the camera sends
  its last frame - taken as it froze, of the region it was last asked about - again and
  again, number and all; dark, its frames are new and have no depth (`Eye.fail`).
- *The program judges.* A picture whose number has not moved on from the last one the program
  used is not new; one with depth in less than half of it is dark (`Runner.trouble`). Three
  such in a row end a look: the program fails, naming the camera - "Looked for fetch_cube:
  the camera's picture is not new", "... has no depth" - and moves nothing. Before the jaws go
  down, such a picture is no evidence of where the cube is: the program looks again, which
  names the fault if it lasts, or stops with no second look left. `Runner(checks=False)` and
  `sweep --disturb --unchecked-camera` take every picture on trust, as before, to measure what
  the checks change. The disturbance report quotes what the program said in the set-ups that
  missed.

**Blueprint and builder.** Untouched; programs are the same data.

**Result.**

The nine set-ups of ADR 0030 under every Fetch disturbance, each picture checked
([report](../sweeps/2026-10-08-fetch-mobile-manipulator-disturbed-camera-faults.md)):

| Disturbance | on trust (as before) | checked |
| --- | --- | --- |
| camera frozen as the cube is moved 5 cm | 0 of 9: down twice at the stale place, "Timed out: pose did not settle" (5), "Nothing held: the grasp missed" (4) | 0 of 9: "Looked for fetch_cube: the camera's picture is not new", nothing grasped, no second look |
| camera dark at the table | 0 of 9: "Looked for fetch_cube: it would not keep still", after 5 s | 0 of 9: "Looked for fetch_cube: the camera's picture has no depth" |
| none and the five disturbances of ADR 0030-0037 | 9 of 9 each | the same: all 54 runs met their last goal at the same time as before |

The paired sweep of ADR 0036 with the camera frozen as the cube is moved, 59 drawn set-ups
([report](../sweeps/2026-10-08-fetch-frozen-paired-59.md)): broken 59 of 59 - the program
cannot fetch what its camera cannot see - every one stopped at the look with the camera named
and nothing grasped; the 60 undisturbed runs met their last goal at the same time as before to
the millisecond, the checks raising no false alarm. Traced in two set-ups, the camera is named
0.3 s after it goes dark (three pictures) and 0.4 s after it freezes (its last frame is new
once, then three that are not).

Held by `tests/test_camera_faults.py` (10): the disturbances (alone and with a move, the camera
failing first; no camera to fail, said); the camera frozen, sending one frame whatever moves,
and dark, sending new frames without depth, and working again; a look at a stuck camera names
it and moves nothing - on trust, the same three pictures make a steady look; a dark one named;
stuck before the reach, it looks again and names the camera, or stops; a stand-in camera
without frame numbers never doubted; the report quoting why; and, in full physics, the design
as designed frozen (checked: named at the look; on trust: two misses) and dark (named).

**Boundaries.** A picture's number and depth are checked, not what it shows: a stream that
keeps numbering a stuck picture, or a camera knocked off its mount (FR-021), passes. A frame
frozen within one picture interval of its first use is used once, so with a later timing the
jaws can go down once at the stale place before looking again names the fault. Dark means
depth in less than half of the picture; a lens partly covered passes. The faults are the
stream's, sudden and lasting: no model of a sensor failing slowly.
