# How near it is to tipping, its accelerations counted: the force-angle measure

**Problem.** The drive panel's stance margin (ADR 0015, 0022) says how far the centre of mass is
inside the support polygon, and its own note says what it misses: "it ignores acceleration, so hard
braking can tip a machine with margin left". Nothing in the window or the runs said how near a
machine came to tipping while it braked, climbed or swung its arm (FR-005, the weekly reading of 5
October).

**Does an existing simulator solve it? Can we wrap it?** The measure is Papadopoulos and Rey's
force-angle tipover stability measure (ICRA 1996; Vehicle System Dynamics 33, 2000), as Appala and
Ghosal restate it (IISc): for each edge of the support polygon, the angle between the net force on
the machine other than its supports' - its weight less its inertia - and the line from its centre of
mass to that edge, a moment turned into a couple; zero as it starts to tip over that edge. MuJoCo
supplies what it needs - the machine's mass, its centre of mass and that centre's velocity, its
angular momentum about it (`mj_subtreeVel`), its contacts - and nothing that computes it.

**Unique contribution.**
- *The measure* (`control/tipping.py`, numpy): `force_angles` for each edge of a support polygon,
  `measure` the least with its edge, `ordered` the polygon from a support's points. Its tests hold it
  to the closed forms: on the flat each edge has atan(reach / height); on a slope the downhill edge
  runs out at the static tip angle; braking takes atan(deceleration / g) from the front edge and gives
  it to the back; a moment about an edge takes from it.
- *On the solver* (`Watch`): each call, the machine's centre of mass and its acceleration and the
  rate of change of its angular momentum, both over the last 50 ms - a spinning wheel braked in one
  step is an impulse no machine tips on; its support, the points of its own geoms within 1 cm of what
  it stands on, so that a cart rocking onto a caster a few millimetres up is not taken for one tipping
  over; and what it stands on - a field's own ground where it has one (the tilt table, not its rail),
  else anything under it within 45 degrees of upright.
- *In the window*: under the stance margin, the drive panel says how many degrees the machine has left
  before it tips, warning under 10 - on the tilt table, under the table's angle; the run report the
  fewest it had. What's new runs it: the arm on its cart on the tilt table, the count running down
  until it tips. What's new now shows each demonstration's text whole: the factory's had lost its
  last line.

**Blueprint and builder.** Untouched: the measure reads a run, it changes nothing in a design.

**Result.**
- *Tilt table, the arm on its cart*: from 44 degrees left standing level, the angle fell steadily,
  three quarters of a degree for each degree of table - a static test - and ran out at 53.5 deg: 0.7 deg before the stance's
  static prediction (54.2 deg, without the rail; 55.6 with it) and 1.1 deg before the field read it
  over (54.6). An uphill wheel had first lifted 2 mm off the table at 53.0 deg, 0.22 s before the
  angle ran out: on a table tilting 2 degrees a second the soft contacts let it rise early.
- *Tilt table, the cart alone*: at the table's top, 60 deg, it had 11.9 deg left - it would run out at
  71.9 deg, its stance's prediction with the rail 72.0 - and it did not tip.
- *A hard stop from full speed* (0.42 m/s, decelerating at up to 1.8 m/s^2) took 3 to 4 degrees: the
  cart alone from 57 left while cruising to 54 (with 0.5 kg on its deck 55 to 50, with 1 kg 51 to 47),
  the arm on its cart from 44 to 40 (with 0.5 kg 41 to 37). None came near tipping.

Held by `tests/test_tipping.py` (8): the closed forms above; the support ordered and its inner
points dropped; on the tilt table the arm cart's angle running out before it goes over and falling
three quarters of a degree a degree, the cart alone keeping 10 to 14 degrees at 60; and a hard stop taking degrees from the
arm cart without tipping it. In `tests/test_whats_new.py`, a window test of the demonstration: the panel's count running down. Suites
on MuJoCo 3.10.0: 1114 passed with a display, 1057 headless.

**Boundaries.** The accelerations are taken over 50 ms, so an impulse shorter than that counts only
in part; the support's 1 cm catch is an assumption sized on the cart's caster gap (6.5 mm, ADR 0041).
The kit's machines never came near tipping in a hard stop; FR-005's check - that the angle runs out
within 20 ms of a wheel lifting 2 mm when braking tips a machine - needs a machine that tips, and was
not made. The support is taken flat; on a curb or a ramp's lip it is not.

**Amended 12 November 2026 (OPEN LW-048): an estimate is not a tip.** The run report printed the
force angle's fewest as "(it tipped)" whenever it reached zero, and the drive panel "(tipping)" for
either estimate below zero. On the Curb run the kit cart leaned 3.7 deg at most and kept its upright
goal while both fell far below zero: in a step at 9.28 s one drive wheel's treads on the curb were
all it stood on (stance margin -13.1 cm), and at 8.43 s two casters - one pressed against the curb's
edge, its normal 22 deg off vertical - tilted the estimated support plane 11 deg and left the rear
caster out of it (-146 deg). Both readings are now labelled as estimates ("estimated: ..." in the
report, "est." in the drive panel) and keep their warning colours, and the report says what was seen
beside them - "seen: tilted N deg at most, did not tip" - when they say it was past tipping and it
was not; only a tilt past 60 deg says it tipped over ("It tipped over.", as before).
`RunSummary.stability_lines()`; held by `tests/test_test_drive.py::test_the_report_keeps_a_tip_it_estimated_apart_from_one_it_saw`.
The estimates themselves are unchanged: the support is still one step's contacts (OPEN LW-049).
