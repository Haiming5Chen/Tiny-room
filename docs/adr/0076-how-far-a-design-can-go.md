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
- *The tilt table's angle* (21 November), the second: `fields.tilt_table(top)` is the Tilt table
  stopped at `top` and held there - the same table, rail and squaring - and a machine meets it if it
  still stands 3 s (`HELD`) after the table passed half a degree under its top (`TiltHold.hold`; the
  Tilt table's own goals keep a hold of none). Each level's run lasts the climb, the hold and half a
  second (`tilt_seconds`): `python -m little_world.inventory.boundary tilt 45 58 1 --design
  mobile_manipulator --jobs 2`.

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

**The tilt table (21 November): the method's first check fails, and the profile says why.** FR-042's
first test of the method was that a profile along the tilt table's angle agrees, within its interval,
with where the same draws go over on the table's own climb and with what their designs predict (ADR
0029, 0059). The arm on its cart, the table stopped at each angle and held 3 s, as designed and the
same 8 draws (seed 1):

| Table angle, deg | 45 to 50 | 51 | 52 | 53 | 54 | 55 | 56 | 57 | 58 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Stood its 3 s, of 9 | 9 | 7 | 6 | 5 | 4 | 2 | 1 | 0 | 0 |

50 % at 53.5 deg, 95 % between 51.8 and 54.6, nothing pooled. On the table's 2 deg/s climb the same
draws went over between 54.6 and 58.7 deg (median 56.2) and their designs predict 55.6 to 57.7 (median
56.3): both outside the interval. Draw by draw the order is kept, and every draw stood held only to
2.1 to 4.6 deg below where its climb read it going over:

| Draw | Stood at, deg | Over at, held | Over on the climb | Predicted | Climb minus held (midway) |
| --- | --- | --- | --- | --- | --- |
| as designed | 50 | 51 | 54.6 | 55.6 | 4.1 |
| repeat 1 | 53 | 54 | 56.2 | 56.2 | 2.7 |
| repeat 2 | 50 | 51 | 55.1 | 55.7 | 4.6 |
| repeat 3 | 54 | 55 | 56.6 | 56.7 | 2.1 |
| repeat 4 | 55 | 56 | 57.9 | 57.3 | 2.4 |
| repeat 5 | 52 | 53 | 55.8 | 56.1 | 3.3 |
| repeat 6 | 54 | 55 | 57.2 | 56.4 | 2.7 |
| repeat 7 | 51 | 52 | 55.1 | 56.3 | 3.6 |
| repeat 8 | 56 | 57 | 58.7 | 57.7 | 2.2 |

The climb reads a machine late. The cart does not go over at one angle: pressed against the trip rail,
it creeps along it - 0.2 mm/s at 49 deg, as designed - and from about 50 deg the creep runs away and it
is over 1 to 3 s later, by which time a table climbing 2 deg a second has climbed 2 to 4 deg more. One
thing changed at a time:

| Changed, as designed | Where it goes over |
| --- | --- |
| nothing: the table's climb at 2 deg/s | 54.6 deg |
| the climb at 0.5 deg/s | 51.4 deg |
| held at 49 deg for 10 s | stands, creeping 0.2 mm/s along the rail |
| held at 50 deg for 10 s | 3.3 s after the table stopped |
| held at 51 deg, steps of 1 ms | stands its 3 s, creeping 0.2 mm/s |
| held at 51 deg, 20 noslip iterations (2 as everywhere) | stands its 3 s, creeping 0.25 mm/s; held at 53, over |
| held, MuJoCo's elliptic friction cones (OPEN LW-039) | stands at 52 deg; over at 53 |
| held at 51 deg, the casters' swivels or the drive wheels stiffened | over, or running away as the hold ends |

Part of the gap is the pyramidal cones' creep (OPEN LW-039): with friction held better, the runaway
starts one to two degrees higher. Part is not: with elliptic cones the cart still cannot be held at
53 deg, 2 deg below its climb's reading and 2.6 below the rigid prediction (55.6; ADR 0059 puts the give
of casters, tyres and joints at about 2 deg). The evidence's `tilt` claim (54.6 deg, a degree before
the prediction) records the climb's reading; it now carries this as a known flaw, with a third number,
standing held at 51 deg: no (OPEN LW-053). Report: docs/sweeps/2026-11-21-tilt-angle-boundary.md.
What's new's *Held, it goes over sooner* stops the table at 51 deg with the arm cart on it: a field
made for the run is kept by its own id (`fields.VARIANTS`, `find_field`; `tilt-51`), so the window
shows it, its goal ("Stood 3 s at 51 deg") and, after Stop, the run's report - over at 51.1 deg.

Held by `tests/test_boundary.py` (5: the fit, the crossing and the pooling; the interval from the
draws, narrowing with more of them; a curb the cart clears and one it cannot; a held table met only
once the machine has stood its hold; held at 51 deg the arm cart goes over, at 47 it stands) and a
window test in `tests/test_whats_new.py` (the table stops at 51, the cart goes over there). Suites:
1200 pass with a display, 1132 headless.

**Boundaries.** Two factors: a ramp's slope and the Fetch's reach are not profiled yet, nor is a
program's commitment apart from its competence - a cart driven at a curb, or stood on a table, has no
choice. The tilt table's hold is 3 s by judgment, and at 49 deg the cart still creeps: no hold is long
enough to say it would stand for good. FR-042's check that the interval narrows by about the square
root of two from 9 to 18 draws a level is not run. Nine draws a level give wide intervals (a level of 0 of 9 is 0 to 34 %). A
crossing assumes success falls with the factor; where it does not, the report says so rather than
hiding it. Nothing in the Workshop shows a profile yet.
