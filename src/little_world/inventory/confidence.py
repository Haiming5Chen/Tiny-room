"""How sure a count of successes makes us: exact binomial bounds (ADR 0028).

A sweep's random repeats are draws of the conditions a machine meets - where it is set
down, what it carries, which floor (ADR 0024). The simulator is deterministic, so every
bit of uncertainty is in which conditions were drawn, and the share of drawn runs that
succeed estimates how often the machine succeeds under those conditions. Eight successes in
eight draws do not make that rate 100 %: they make it at least 69 %, with 95 % confidence.

The bounds are Clopper and Pearson's (1934, Biometrika 26, 404-413): exact, never claiming
more than the count allows. Each is found by bisection on the binomial distribution, summed
in logarithms so that any number of runs works. Standard library only.
"""
from math import ceil, exp, lgamma, log, log1p

CONFIDENCE = .95


def _term(n, i, p):
    """P(X = i) for X ~ Binomial(n, p), 0 < p < 1."""
    return exp(lgamma(n + 1) - lgamma(i + 1) - lgamma(n - i + 1) + i * log(p) + (n - i) * log1p(-p))


def _at_least(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    if k <= 0 or p >= 1.:
        return 1.
    if p <= 0.:
        return 0.
    return min(1., sum(_term(n, i, p) for i in range(k, n + 1)))


def _check(k, n, confidence):
    if not (isinstance(k, int) and isinstance(n, int)) or n < 1 or not 0 <= k <= n:
        raise ValueError(f'need 0 <= successes <= runs and at least one run, not {k} of {n}')
    if not 0. < confidence < 1.:
        raise ValueError(f'confidence is between 0 and 1, not {confidence}')


def _solve(rising, target):
    """The p in [0, 1] where the rising function `rising` crosses `target`, by bisection."""
    lo, hi = 0., 1.
    for _ in range(200):
        mid = (lo + hi) / 2
        if rising(mid) < target:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-14:
            break
    return (lo + hi) / 2


def lower_bound(k, n, confidence=CONFIDENCE):
    """The success rate is at least this, with the given one-sided confidence, after `k`
    successes in `n` independent runs. k = n gives (1 - confidence) ** (1 / n)."""
    _check(k, n, confidence)
    if k == 0:
        return 0.
    if k == n:
        return (1. - confidence) ** (1. / n)
    return _solve(lambda p: _at_least(k, n, p), 1. - confidence)


def upper_bound(k, n, confidence=CONFIDENCE):
    """The success rate is at most this, with the given one-sided confidence."""
    _check(k, n, confidence)
    return 1. - lower_bound(n - k, n, confidence)


def interval(k, n, confidence=CONFIDENCE):
    """The two-sided Clopper-Pearson interval: each side at (1 + confidence) / 2."""
    one_side = (1. + confidence) / 2
    return lower_bound(k, n, one_side), upper_bound(k, n, one_side)


def runs_needed(failing, confidence=CONFIDENCE):
    """How many runs, every one a success, it takes to say the failure rate is below
    `failing` with this confidence: 59 for 5 % at 95 %, 299 for 1 %."""
    if not 0. < failing < 1. or not 0. < confidence < 1.:
        raise ValueError('a failure rate and a confidence are between 0 and 1')
    n = max(1, ceil(log(1. - confidence) / log(1. - failing) - 1e-9))
    while (1. - confidence) ** (1. / n) < 1. - failing:      # guard the rounding
        n += 1
    return n
