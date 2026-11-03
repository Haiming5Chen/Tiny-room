# How close to slipping: the friction a grip uses, and a cube made heavier until it slides out

**Problem.** Results reported the forces on a handled part (ADR 0040), the squeeze (ADR 0042) and what
the jaws feel (ADR 0048), never how near a contact is to sliding. Whether a grasp held was known only
after the run: the cube arrived or it did not. FR-036 (first in the weekly reading of 2 November)
asked for each contact's friction use - how much of the friction its cone allows it uses - and
predicted that its inverse is a margin: "the grasp holds with 2.4 times margin" would mean a cube 2.4
times heavier starts to slip.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo computes every contact's force and
keeps it inside its friction cone; `mj_contactForce` gives it in the contact's frame and the contact
carries its coefficients. Nothing turns that into a share of the cone, follows it through a run or
shows it. The cones here are pyramidal (MuJoCo's default; ADR 0011 measured what elliptic ones would
change): the solver keeps each frictional force over its own coefficient - two along the surface and,
with `condim` 4, a torsional one - summed, at most the normal force.

**Unique contribution.**
- *Friction use* (`MujocoBackend.friction_use`): for each of a body's contacts its normal force and
  the friction it uses, measured as the cone is - summed for pyramidal cones, a length for elliptic
  ones - so that their ratio is 0 with no sideways load and 1 at the cone's edge, where the contact may
  slide. Reading it changes nothing in the run.
- *A grip's use* (`handling.grip_use`): for a part only the machine touches, the friction its contacts
  use over what they allow, together; `Runner.carrying` - past the grasp check that found the part
  held, before the jaws open again - and `Run.grip`, the carry's span with the most use, when, and the
  median.
- *A heavier part as a condition of a run* (`MujocoBackend.scale_mass`, `run(masses=...)`): mass and
  inertia scaled as if the material were denser, MuJoCo's constants recomputed with the state kept; a
  reset world's part is as designed again.
- *In the window*: under "holding" the drive panel says how much of the grip's friction is in use,
  warning from 80 %. What's new's "How close to slipping" fetches a cube 16 times as heavy: the line
  climbs as the arm lifts, reaches 100 % and the cube slides out of the jaws.

**Blueprint and builder.** Untouched: the measure reads a run; a heavier part is a condition of a run,
as a payload is (ADR 0024).

**Result.**
- *A block on a slope* (concrete under wood, mu 0.4, its friction angle 21.8 deg): resting at 5, 15
  and 21 deg it uses tan(theta) / mu of its friction within 0.02 (at 15 deg 0.6699 for 0.6699); at 23
  deg it is at the edge, 1, and slides. Inside its cone it still creeps 1.4 to 4.5 mm/s - MuJoCo's soft
  contacts with noslip on (OPEN LW-039).
- *The Fetch's grip, carrying the cube*: a little over a third of its friction in use (median 0.38),
  at most 0.80 while it drives to the bin. The jaws squeeze 3.1 N in all and the cube weighs 0.16 N:
  most of the friction in use is the rotary jaws' own pull along the cube (sliding 0.30) and twist
  about the pads (0.08), not the weight.
- *The cube made heavier, the same set-up*:

| cube | grip in use while carried, median (most) | squeeze | outcome |
| --- | --- | --- | --- |
| as designed, 16 g | 0.38 (0.80) | 3.1 N | in the bin, 36.9 s |
| 2 times, 33 g | 0.43 (1.0 lowering into the bin) | | in the bin |
| 4 times, 65 g | 0.44 (0.96) | 5.2 N | in the bin |
| 8 times, 130 g | 0.61 (1.0 on the lift) | 5.9 N | in the bin, having slid 17 mm in the jaws (6 mm as designed) |
| 16 times, 260 g | 0.77 (1.0) | | slid out on the lift, 0.9 s after it |
| 32 times, 520 g | 0.94 (1.0) | | slid out on the lift |

- *FR-036's prediction does not hold for this gripper*: its first-order margin, the inverse of the use
  as designed, says a cube 1.25 times heavier (from the most) or 2.6 times (from the median) would
  slip; it held to 8 times and was lost at 16. The jaws are position servos: a heavier cube presses
  them harder (3.1 to 5.9 N), and most of the friction in use does not grow with the weight. The use
  says how near the grip is to sliding now; how heavy a part it can carry is measured, as here.
- *In the window*: the cube 16 times as heavy slides out on the lift, the panel's line passing 95 %.

Held by `tests/test_friction_use.py` (4): the slope's closed form and its sliding; the cone the solver
keeps, a resting cube's weight carried by the table, a heavier cube's by its contacts, strangers and
impossible factors refused; a run following the grip while it carries, as designed, 8 and 16 times as
heavy; and reading the measure leaving a run unchanged. In `tests/test_whats_new.py`, a window test of
the demonstration. Suites on MuJoCo 3.10.0: 1122 passed with a display, 1063 headless.

**Boundaries.** The use is MuJoCo's own cone: pyramidal, its torsional coefficient (0.005 m) MuJoCo's
default rather than a sourced one, and its soft contacts creep inside it (LW-039). The grip is judged
in the air only - from the grasp check until the jaws open, while nothing else touches the part. The
mass study is one set-up, one cube; the drive wheels' traction margin FR-036 also asked for is not
reported yet.
