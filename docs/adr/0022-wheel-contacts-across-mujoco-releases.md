# Wheel contacts across MuJoCo releases: stance from shapes, curbs off the limit, the tilt gap named

**Problem.** Run unchanged on MuJoCo 3.14, the suite moved three results, all with a wheel in
contact (docs/RADAR.md, OPEN LW-001 to LW-003): the platform's caster climbed the 20 mm
curb it stops at on 3.3.7; the mobile manipulator's measured stance margin read 2.6 cm
instead of 3.4 with its tilt unchanged; and it tipped on the tilt table at 52.4 degrees
instead of 54.2. Each could be the machine or the engine. A check that measures the engine
is no check of the machine.

**Does an existing simulator solve it? Can we wrap it?** It is MuJoCo's contacts that differ;
the questions are which of our measurements depend on how the engine reports or makes
contacts, and which engine change moved each number. The changelog the radar reads names the
candidates; running each release decides.

**Unique contribution.**
- *Stance from shapes, not reported points.* The measured support polygon was the convex hull
  of the contact points MuJoCo reports. How many points it makes for a wheel, and where,
  changed between releases (17 on 3.3.7, 10 on 3.14 for the settled manipulator). It is now
  built from the touching geoms' own shapes: for each machine geom in a supporting contact,
  its points that reach furthest along the contact normal - a wheel's two rim points, a
  box's lowest corners, a sphere's lowest point (`control/drive_telemetry.py`,
  `lowest_points`). The same shapes the rigid prediction uses.
- *Curbs off the limit, and the engine's dependence on history shown.* The platform's
  casters were mapped against single curbs and against the same curbs after a 10 mm one, on
  both releases and with MuJoCo's multiple-contacts option (multiccd) on and off:

  | | alone: 18 / 20 / 22 / 24 mm | after a 10 mm curb: 18 / 20 / 22 / 24 mm |
  | --- | --- | --- |
  | 3.3.7 as used (one contact per convex pair) | climb / climb / stop / stop | stop / stop / climb / climb |
  | 3.3.7 with multiccd | climb / stop / stop / stop | climb / stop / stop / stop |
  | 3.14 as released (multiccd, cylinder multicontact) | climb / climb / climb / stop | climb / climb / climb / stop |
  | 3.14 without multiccd | climb / stop / stop / stop | climb / climb / stop / stop |

  (Corrected by ADR 0023: the platform started 4.3 cm in the air and landed with its wheels
  driven, which left a caster swivelled; started on its wheels, all four configurations
  answer the same alone and after a 10 mm curb. What follows was the reading at the time.)
  On 3.3.7 as used, the answer depends on the curb before it and is not monotonic in
  height: a caster that cannot climb 18 mm climbs 24. That is the engine. The Curb run's
  "20 mm, missed" for the platform (ADR 0017) is one such answer, not the geometric limit it
  was read as. Multiccd makes 3.3.7 consistent but adds 5 % to a rolling cart's coast-down
  deceleration against its closed form (the test holds 1 %), so it is not switched on here.
  The checks are now 18 mm (climbed) against 24 mm (not), alone, on any release; and a
  check that the answers do not depend on the curb before them, marked as expected to fail
  on releases before 3.8.
- *The tilt-table difference, named.* Each release from 3.4 to 3.14 was run on the same
  table, with multiccd as released and switched off:

  | release | 3.3.7 | 3.4 | 3.5 | 3.6 | 3.7 | 3.8 | 3.8.1 | 3.9 | 3.10 | 3.11 | 3.12 | 3.13 | 3.14 |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | as released | 54.20 | 53.64 | 53.62 | 53.62 | 53.79 | 54.21 | 54.24 | 54.24 | 54.21 | 54.11 | 53.39 | 52.42 | 52.42 |
  | multiccd off | 54.20 | 53.64 | 53.62 | 53.62 | 53.79 | 53.79 | 53.64 | 53.64 | 53.64 | 53.70 | 53.01 | 53.01 | 53.01 |

  The kit's tread wheels are rings of box blocks, so a wheel on the table and against the
  trip rail is a box-box contact; the caster's wheel is a cylinder. The steps match the
  changelog: 3.4 "fixed a bug in the box-box distance computation" (-0.6), 3.12 rewrote the
  box-box collider (-0.7), 3.8 turned multiccd on by default (+0.4) and 3.13 added
  multicontact for cylinders (-1.0); midpoint and gyroscopic integration of free bodies
  (3.7, 3.8.1, 3.11) move it by 0.2 or less. The check compares with the prediction at the
  rail within 4 degrees: the swivelling caster accounts for 1.6 on 3.3.7, and the releases
  themselves span 1.8.

**Blueprint and builder.** Nothing saved changes. The Curb run keeps its 10, 20 and 35 mm
curbs; `curb_run(heights)` builds it with others.

**Result.** The measured stance margin of the settled manipulator: 3.39 cm on 3.3.7, 3.40 cm
on 3.14, predicted 3.37. The suite on MuJoCo 3.14 passes in full (the curb-history check
included), so these three no longer stand in the way of an upgrade (OPEN LW-004, the
owner's decision). On 3.3.7 the curb-history check fails, as expected and recorded (it
passes since ADR 0023, with the machine started on its wheels).

**Boundaries.** Which release is right near a caster's radius is not settled here: that
needs a real caster and curb. The rigid prediction still knows nothing of a swivelling
caster or of the tread blocks' compliance. Support points come from boxes, cylinders,
spheres and capsules; any other shape still uses the points MuJoCo reports.
