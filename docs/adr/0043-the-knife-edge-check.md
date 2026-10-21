# The knife-edge check: does a result survive a micrometre?

**Problem.** A sweep draws set-ups at random (ADR 0024, 0028) and MuJoCo runs each exactly once:
one set-up, one outcome. So a sweep cannot tell a result the design earns from one it happened
on - a contact that does or does not open, a part that creeps one way or the other. ADR 0042's
first sweep met one: in 1 of 71 set-ups the cube crept out of the jaws, and nothing said whether
the next set-up drawn beside it would have done the same. Real repeats of one set-up vary - one
to three orders of magnitude above a robot's repeatability for cloth, which four calibrated
simulators did not reproduce ([Same Action, Different Outcome, arXiv 2610.10801](https://arxiv.org/abs/2610.10801),
from the weekly reading of 19 October, FR-024).

**Does an existing simulator solve it? Can we wrap it?** MuJoCo is deterministic, which is what
ADR 0036 relies on; the check uses that. Perturbing a deterministic simulation to probe its
sensitivity is the ordinary tool (finite differences, ensembles); what is ours is where it is
applied - the placement a sweep already varies - and how the result is reported beside the
draws.

**Unique contribution.**
- *Repeats a micrometre off* (`inventory/jitter.py`): each drawn set-up is run `REPEATS` (5)
  times more, the machine set down within `PLACE` (1 micrometre) of its place along X and Y and
  turned within `TURN` (1e-5 rad, 0.00057 degrees) - four orders of magnitude under the 2 cm and
  3 degrees the sweep draws from. A repeat keeps its set-up's label, so a program that looks
  draws the same camera noise: only the placement moves. Moved by nothing, a repeat is its
  set-up step for step.
- *Each measure against itself* (`edges`, `flips`): for every measure a run reports - whether
  every goal was met, the last goal's time, where it tipped, and ADR 0040/0042's squeeze, the
  table's and the bin's push, the fall, the lean - the spread among a set-up's own run and its
  repeats (the median over set-ups, and the most, with where), against the spread of the
  set-ups' own runs. Under a tenth of it (`ROBUST`) a measure is the design's; above, partly
  chance. Each set-up that spreads further than that under a micrometre is counted: a knife
  edge for that measure. Set-ups whose outcome changed are named.
- `sweep --jitter K` runs the repeats and adds the section to the report.

**Blueprint and builder.** Untouched; a repeat is an ordinary variation.

**Result.** The tilt table (8 drawn set-ups, 48 runs): the outcome never changed, and where
the cart tipped spread 0.05 degrees at most under a micrometre against 3.7 across set-ups - the
design's. Fetch (the 59 drawn set-ups of ADR 0042's sweep, 354 runs): the outcome changed in
none; the time its last goal was met spread 0.10 s (the median over set-ups; 0.48 at most)
against 1.2 s across set-ups, the squeeze 0.06 N against 1.6 and the lean 0.12 degrees against
1.4 - the design's, though 25, 14 and 26 set-ups passed a tenth of it. The set-down is partly
chance: under a micrometre the cube's fall into the bin spread 0.29 cm (0.90 at most) against
1.0 across set-ups, the bin's push 0.07 N in a step against 0.35 and 0.02 N over 50 ms against
0.06, the table's 0.013 N against 0.064 - a fifth to a third of the spread between set-ups, in
46 to 58 of the 59. What ADR 0042 reports of these is their range over set-ups (the cube falls
0.1 to 1.1 cm); which of those a set-up gets is the micrometre's, not the set-up's
(`docs/sweeps/2026-10-21-fetch-knife-edge-59.md`, `2026-10-20-tilt-knife-edge.md`).

Held by `tests/test_jitter.py` (4): a repeat is its set-up a micrometre off under its own label;
spreads, knife edges and changed outcomes from made-up runs; the report's section, and a sweep
with repeats read back from JSON; moved by nothing, a repeat is its set-up step for step.
Suites on MuJoCo 3.10.0: 1002 passed with a display, 955 headless.

**Boundaries.** Only the machine's placement is jittered: the cube's own place, the payload and
friction are not, and the camera's noise is held. A micrometre is not the variability of a real
repeat - it asks only whether the simulated result is stable where it stands; a lab's own
repeats (FR-009) are what would measure that. Five repeats find a knife edge often crossed, not
a rare one.
