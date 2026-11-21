# How far a design can go: where its success crosses one half along one factor

**Problem.** A field answers whether a design passed, and how often, at the field's own settings -
the Curb run's 10, 20 and 35 mm curbs, the tilt table's angle. It does not say how far the design can
go: which curb it still clears, and how surely. A study of driving agents read failure this way - one
measured factor a family, the rate of success along it and where it falls through one half, with an
interval from run-to-run variance ([arXiv 2611.06453](https://arxiv.org/abs/2611.06453); FR-042, third
in the weekly reading of 9 November).

**Does an existing simulator solve it? Can we wrap it?** No simulator reports a design's limits; the
runs are the project's own (`sweep.run`), and the statistics are a few lines of standard library.

**Unique contribution.**
- *A profile along one factor* (`inventory/boundary.py`, standard library): the factor stepped along
  a grid, every level run on the same draws of the other varied things (ADR 0024's box, one seed);
  each level's rate with its exact interval (ADR 0028); the rates fitted to fall with the factor by
  pool-adjacent-violators, weighted by runs; the level where the fit falls through one half, found
  linearly between the two levels it falls between; its 95 % interval from 2,000 resamples of each
  level's draws, with a seed of its own. Where the fit had to pool - a higher level doing better than
  a lower one - the report says so, and where it does not cross within the grid, it says that.
- *The runs*: `sweep.run` takes a variant of a field and a duration of its own (`field=`,
  `duration=`); `boundary.levels(factor, values, design, ...)` runs the grid, in parallel if asked;
  `python -m little_world.inventory.boundary curb 8 26 2 --samples 8 --seconds 25 --jobs 2` writes
  the report. The first factor is a curb's height (one curb, the Curb run's protocol); `--multiccd`
  runs a study with MuJoCo's multiccd on, the setting OPEN LW-047 asks about - off everywhere else.

**Blueprint and builder.** Untouched.

**Result.** The kit cart, driven at one curb for 25 s - as designed and 8 draws (seed 1) a height:

| Curb height, mm | 8 | 10 | 12 | 14 | 16 | 18 | 20 | 22 | 24 | 26 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cleared, of 9 - multiccd off (as everywhere) | 2 | 5 | 6 | 6 | 3 | 3 | 0 | 1 | 0 | 0 |
| Cleared, of 9 - multiccd on | 0 | 4 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

With multiccd off: 50 % at 14.3 mm, 95 % between 12.5 and 18.1 mm - but from 8 to 14 mm a higher curb
was cleared more often than a lower one, and the fit pooled them (522 of 2,000 resamples did not cross
within the grid). With multiccd on it stays below one half over the whole grid.

Two things this shows, neither mended here:
- **The cart's curb ability rests partly on the engine's energy from nowhere** (OPEN LW-047). Every
  clear from 14 mm up is with multiccd off, where a swivel caster's wheel pressed against a curb's edge
  is given energy it never took (ADR 0074: 78 mJ at 10 mm); with multiccd on, which gives that contact
  several points and no such energy, the cart clears 10 mm in 4 draws of 9, 12 mm in 1, and nothing
  higher. ADR 0041's "cleared 10, 14 and 18 mm given 25 s" was the design as designed, multiccd off.
- **A lower curb stalls the cart more than a higher one** (OPEN LW-052): 8 mm is cleared in 2 draws of
  9 with multiccd off and in none with it on, where 10 mm is cleared in 5 and 4. What holds it is the
  same caster's wheel against the curb's edge, for the whole 25 s. A rigid wheel pushed at its axle
  needs less push for a lower step, not more: this is the cylinder-against-edge contact again, at a
  height where it holds the wheel.

Held by `tests/test_boundary.py` (3: the fit, the crossing and the pooling; the interval from the
draws, narrowing with more of them; a curb the cart clears and one it cannot). Suites: 1198 pass with a display, 1130 headless.

**Boundaries.** One factor, one field: the tilt table's angle, a ramp's slope and the Fetch's reach
are not profiled yet, nor is a program's commitment apart from its competence - a cart driven at a
curb has no choice. Nine draws a level give wide intervals (a level of 0 of 9 is 0 to 34 %). A
crossing assumes success falls with the factor; where it does not, the report says so rather than
hiding it. Nothing in the Workshop shows a profile yet.
