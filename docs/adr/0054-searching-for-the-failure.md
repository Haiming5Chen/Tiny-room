# Searching for the failure: a falsifier measured against the draws, and not adopted

**Problem.** A sweep's drawn set-ups certify a rate - 59 draws without a failure bound it under 5 %
(ADR 0028, 0049) - but do not say where failures live. A search that follows a run's margin towards
zero might find them in fewer runs: a guided search found failures of navigation systems more often
than an unguided one, and they transferred to the real robot ([arXiv
2610.06862](https://arxiv.org/abs/2610.06862); FR-025, the weekly reading of 19 October). FR-025 set
its own gate: the search must find failures in fewer runs than random sampling to be kept.

**Does an existing simulator solve it? Can we wrap it?** No simulator searches a project's variation
box for its own results; the search is a stdlib loop around the sweep's run (ADR 0024), deterministic
as the runs are.

**Unique contribution.**
- *A run's margin*, 0 at the edge of failing (`inventory/falsify.py`): for Fetch, each measure of how
  the cube was handled (ADR 0040) that does harm as it grows - the table's and the bin's push, in a
  step and over 50 ms, its leans, its fall - and the squeeze either way, against the most (and least)
  the tuning draws had it at the report's precision (ADR 0049), as a share of the draws' spread; a goal
  missed is a failure outright. For the tilt table, the degrees past its last hold (50) it tipped.
- *A compass search* over the box - x, y, turn, payload, where it sits, friction - from the design as
  designed: each coordinate a step either way, two runs at a time, a move kept when it lowers the
  margin, the step halved when none does; a payload's place is not moved while there is none.
  `python -m little_world.inventory.falsify fetch|tilt --tuning SWEEP.json [--draws SWEEP.json]`.
- *The kit cart as it was* (`mobile_manipulator_blueprint(caster_gap)`, ADR 0041's `ROCKING_GAP`),
  for the known failure region FR-025 was to be judged on.

**Blueprint and builder.** Untouched; the cart's default is as it was.

**Result.** Measured on the Fetch field and the tilt table (`docs/sweeps/2026-10-23-falsifier-search.md`,
162 runs):

| | The search | Drawn at random | The plan's corners |
| --- | --- | --- | --- |
| Fetch, every measure | no failure in 40 runs; lowest +0.03 | first outside at draw 19 of 59 fresh draws: the table's push 0.77 N | - |
| Fetch, the table's push alone | first outside at run 27: 0.65 N | draw 19 | - |
| under a micrometre (ADR 0043) | 1 of 5 repeats outside: a knife edge | 5 of 5 outside (0.69 to 0.75 N): a corner | - |
| tilt table, the lowest tip | 53.35 deg, at run 15 of 30 | 55.03 deg in 30 draws | 53.32 deg: friction alone at its high end |

The search did not do better than the draws, and is not adopted: the sweeps keep their plan, the
corners and the draws (ADR 0024). Where the margin is smooth, as on the tilt table, its worst is a
corner the plan already runs, and the search found the same; where it is rugged, as the cube's
handling is at the millimetre scale - set down 1.0, 1.1 and 0.9 cm behind its mark, margins +0.03,
+0.22 and +0.04 - a search follows chance, and found a knife edge where a draw found a real corner
(0.49 kg carried). The known failure region was gone: with today's program the cart rocking between
its casters, as before ADR 0041, pressed the cube in none of the 10 set-ups it was tried on - as
designed and the 9 carrying 0.44 kg or more; the table carried the cube's weight - so the presses ADR 0041 removed by setting the casters down no
longer come with the rocking (OPEN LW-035, for the owner: ADR 0041 traded climbing a curb for them).
The search's module stays as this study's instrument; nothing else calls it.

Held by `tests/test_falsify.py` (6): the box and a point's variation; a Fetch run read against what the
tuning draws certified - at the report's precision, 0.623 N within 0.62 and 0.77 N outside, the squeeze
under its least, a cube left on its side, a goal missed; a tilt run's degrees past its hold; the compass
search on a made-up margin - inside the box, two runs at a time, deterministic, stopping at a failure,
halving to its least step, not moving what changes nothing; draws read as the search is, and the
report. Suites on MuJoCo 3.10.0: 1083 passed with a display, 1031 headless.

**Boundaries.** Two fields, one search, one start, one budget each: a single realisation of each
comparison, not a rate of finding. The searched runs all draw one camera noise ('searched'), each draw
its own. Other searches - Bayesian, or over one measure at a time from the worst draw - were not tried;
the Fetch margin is the envelope of the tuning draws, not a sourced limit on what the cube can bear.
