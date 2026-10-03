# The tilt test sets the machine square against its rail

**Problem.** Swept over its variations (ADR 0024), the arm on a cart tipped over the tilt
table between 51.4 and 58.4 degrees, and the run that moved it most was the one set down
turned 3 degrees to the right: -3.1 degrees, and 2.8 degrees below its own prediction, the
furthest any variation strayed from one. Traced (ADR 0024, OPEN LW-017): turned right, the
machine ends with a single tread block against the trip rail and swings about it near 48
degrees, then goes over early. The owner was offered three answers - accept it, model the
turn in the prediction, or have the test square the machine - and chose the third on
3 October 2026.

**Does an existing simulator solve it? Can we wrap it?** This is a question of protocol,
not physics. A static tip test sets the machine square to the tilt axis against its stops
before it tilts; the simulator only has to be given the machine that way.

**Unique contribution.**
- *A field that squares.* `Field.squared`: the tilt table turns the machine in place about
  its base until it faces along the hinge line (`fields.squared`, `fields.heading`), then
  sets its trip rail against the wheels as before (ADR 0020). A design built turned, or a
  variation that turns it, is tested square; a design built straight is untouched.
- *Sweeps that do not vary what the test undoes.* `sweep.ranges_for(field)` leaves turning
  out of a squared field's plan: the tilt table's sweep has 18 runs instead of 20, the two
  turned ones gone. The random repeats still draw a turn of zero, so every other value they
  draw is the same as before. Turning stays in every other field's sweep.

**Blueprint and builder.** Designs are unchanged; the field turns its copy of the machine.

**Result.** On MuJoCo 3.10.0 (docs/sweeps/2026-10-03-tilt-mobile-manipulator-squared.md):
the 18 runs tip over between 54.0 degrees (as designed, and every placement, which the
fitted rail follows) and 58.5 (0.5 kg aboard, 5 cm to the left); against each run's own
prediction -1.8 to +0.7 degrees, where the turned run had been -2.8. Set down turned 3
degrees either way, the machine now tips at 53.98 and 54.00 degrees, where it does as
designed (53.99), and its prediction is the design's own, 55.75 about the rail's edge (the
prediction is made for the machine as the field stands it). Checked in
`tests/test_more_fields.py` (one new): a design turned 3 degrees and set 1 cm off its mark
reaches the table facing along the hinge line, moved but not turned - every body by the
same offset - with the rail set that much further over; the Fetch field leaves it as it
is; the tilt sweep's plan has 18 runs and none turned.

**Boundaries.** The tilt table no longer measures what a turned machine does against a
rail; that early tip is real for that placement and stays recorded in ADR 0024. The
machine is squared about its base's own vertical axis: a design whose first free body is not
its base would be squared about that body.
