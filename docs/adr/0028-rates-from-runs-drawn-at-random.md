# Results with their uncertainty: rates from the runs drawn at random

**Problem.** A sweep (ADR 0024) reported "every goal in all 20 runs" for the arm on a cart
fetching its cube, and the reports read as if that were the machine's success rate. Twelve
of those runs were chosen, not drawn: the design as designed and each variation alone at
either end of its range. They check corners; they are not a sample of anything. Only the
eight random repeats are draws of the conditions a machine meets. Counted as one sample,
20 successes would claim a success rate of at least 86 % (one-sided, 95 % confidence); the
eight drawn runs support 69 %. The proposal that asked for this (FR-003) made the same
mistake in its own example.

**Does an existing simulator solve it? Can we wrap it?** The statistics are textbook:
Clopper and Pearson's exact binomial interval (1934), which SciPy computes from the beta
distribution. SciPy would be a dependency for one function. The bound is found here by
bisection on the binomial sum, in the standard library; checked once against SciPy's beta
quantiles, it agrees to 1e-14 for every count up to 60 runs.

**Unique contribution.**
- *Which runs are the sample.* MuJoCo is deterministic: run the same set-up twice and the
  result is the same. Every bit of uncertainty is in which set-ups were drawn, so the rate
  a sweep can estimate is "over set-ups drawn uniformly within the stated ranges", and only
  the drawn runs (`drawn`, the `repeat` variations) estimate it. The chosen runs stay in the
  report as corner checks.
- *Rates with a bound.* `inventory/confidence.py` gives one- and two-sided Clopper-Pearson
  bounds and the runs a claim needs (`runs_needed`: 59 drawn runs without a failure show
  failures below 5 % at 95 %; 299 for 1 %). `sweep.rates` counts every goal, and each goal,
  over the drawn runs. The report's goal table gains a column ("8 of 8, at least 69 %") and
  a "How sure" paragraph that says which runs were drawn, which were chosen, and what a
  stronger claim would take (`--samples 59`).
- *Readings are not successes.* A static test's tipping angle is a reading. With n drawn
  runs, another drawn the same way lands between the lowest and highest of them with
  probability (n - 1)/(n + 1) - 7 in 9 for eight - whatever the spread's shape (order
  statistics); the report and the panel say so instead of a rate.
- *In the window.* The variations panel puts two short lines under its headline: "8 of 8
  random set-ups met every goal, / so at least 69% would (95% confidence)".

**Blueprint and builder.** Untouched.

**Result.** The Fetch sweep on MuJoCo 3.10.0 (docs/sweeps/2026-10-03-fetch-mobile-manipulator.md):
every goal in all 20 runs; from the 8 drawn, at least 69 % of set-ups within the ranges
meet every goal. Run again with 59 drawn set-ups
(docs/sweeps/2026-10-03-fetch-mobile-manipulator-59.md): every goal in all 71 runs, so the
arm on a cart fails to fetch its cube in under 5 % of set-ups within the ranges, with 95 %
confidence - the first claim of that kind the project can make; the cube was in the bin
between 32.8 and 34.5 s. `tests/test_confidence.py` (9): the tabulated
Clopper-Pearson intervals (0/10, 1/10, 5/10, 19/20, 20/20) to 5e-5; n of n bounded below
by (1 - 0.95)^(1/n); 59 and 299 runs for 5 % and 1 %; impossible counts refused; a sweep of
twelve chosen runs, one failing, and eight drawn ones takes its rate from the eight; a sweep
with nothing drawn claims no rate; a static test reports its drawn span with 7/9.

**Boundaries.** The rate is over set-ups drawn uniformly within the ranges the sweep states,
and those ranges are assumptions until measured in a lab (FR-009, not now): the bound
inherits them. One seed draws the set-ups; another seed draws other ones. The bounds are
one-sided lower bounds on success; they say nothing about why a run fails.
