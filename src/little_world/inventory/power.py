"""Plan the draws before the run: the smallest effect worth seeing, and enough draws to see it (FR-039).

A comparison that could not have shown the effect it looked for says nothing when it finds none:
"underpowered - inconclusive", not "no difference" (a pre-registered study withdrew such a claim,
arXiv 2610.30478). The tests here are the ones the sweeps use: the exact McNemar test on paired
outcomes (ADR 0036) and a one-sided Clopper-Pearson bound on a rate (ADR 0028). Their power is
computed exactly, by summing over every outcome the draws could give. Standard library only.
"""
from math import comb, exp, log, log1p

ALPHA = .05     # two-sided, as the sweeps report their p
TARGET = .8     # the chance a plan wants of seeing the effect, if it is there


def mcnemar_p(b, c):
    """The exact two-sided McNemar p for `b` pairs that went one way and `c` the other:
    twice the binomial tail of the rarer side at one half, at most 1."""
    n = b + c
    if n == 0:
        return 1.
    k = min(b, c)
    return min(1., 2. * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def _binomial(n, p):
    """The probabilities of 0..n successes in n trials of chance p."""
    if p <= 0.:
        return [1.] + [0.] * n
    if p >= 1.:
        return [0.] * n + [1.]
    lp, lq = log(p), log1p(-p)
    return [exp(log(comb(n, k)) + k * lp + (n - k) * lq) for k in range(n + 1)]


def mcnemar_power(n, broke, mended=0., alpha=ALPHA):
    """The chance that `n` paired draws show a difference at `alpha` by the exact McNemar test,
    when each pair goes held-to-broken with chance `broke` and broken-to-held with `mended`."""
    if not (0. <= broke and 0. <= mended and broke + mended <= 1.):
        raise ValueError('pair chances are between 0 and 1, and add up to at most 1')
    flip = broke + mended
    if flip == 0.:
        return 0.
    share = broke / flip
    # the smallest one-sided count each number of discordant pairs needs to reach alpha
    power = 0.
    for d, pd in enumerate(_binomial(n, flip)):
        if pd < 1e-15 or d == 0:
            continue
        for b, pb in enumerate(_binomial(d, share)):
            if pb and mcnemar_p(b, d - b) <= alpha:
                power += pd * pb
    return power


def draws_for(broke, mended=0., target=TARGET, alpha=ALPHA, most=2000):
    """The fewest paired draws with at least `target` chance of showing the effect; None if
    more than `most` would be needed."""
    for n in range(1, most + 1):
        if mcnemar_power(n, broke, mended, alpha) >= target:
            return n
    return None


def bound_draws(rate, confidence=.95):
    """How many draws, every one a success, bound a failure rate below `rate` with one-sided
    `confidence` (Clopper-Pearson with no failures: (1 - rate)^n <= 1 - confidence)."""
    if not 0. < rate < 1.:
        raise ValueError('a rate is between 0 and 1')
    n = log(1. - confidence) / log1p(-rate)
    return int(n) + (0 if n == int(n) else 1)


def zero_bound(n, confidence=.95):
    """The one-sided upper bound on a failure rate when `n` draws all succeed."""
    return 1. - (1. - confidence) ** (1. / n)


def plan(broke, mended=0., draws=None, target=TARGET, alpha=ALPHA):
    """A comparison's plan in words: the effect looked for, the draws it needs, and - for the
    draws a sweep will make - the chance it has of showing it, or that it is underpowered."""
    need = draws_for(broke, mended, target, alpha)
    effect = f'pairs broken {100 * broke:.1f} %' + (f', mended {100 * mended:.1f} %' if mended else '')
    words = f'{effect}: {need} paired draws give {100 * target:.0f} % power at p {alpha:g}' if need else \
        f'{effect}: more than 2000 paired draws would be needed'
    if draws is not None:
        power = mcnemar_power(draws, broke, mended, alpha)
        words += f'; {draws} give {100 * power:.0f} %' + (' - underpowered: a null result would be inconclusive'
                                                          if power < .5 else '')
    return words


def to_show(pairs, alpha=ALPHA):
    """How many of `pairs` set-ups a disturbance must break - none mended - for the exact McNemar
    test to show it at `alpha`; None when so few pairs cannot show anything."""
    for broke in range(1, pairs + 1):
        if mcnemar_p(broke, 0) <= alpha:
            return broke
    return None
