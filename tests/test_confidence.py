"""How sure a sweep's counts make us (ADR 0028): exact binomial bounds, and sweeps that
take their rates from the runs drawn at random only.

Reference values are Clopper and Pearson's exact interval as tables print it (they agree
with the beta distribution's quantiles to 1e-14 for every count up to 60 runs).
"""
import pytest

from little_world.fields.goals import Result
from little_world.fields.variation import Ranges, Variation
from little_world.inventory.confidence import interval, lower_bound, runs_needed, upper_bound
from little_world.inventory.sweep import Run, Sweep, assurance, drawn, markdown, rates


def test_the_bounds_are_the_tabulated_clopper_pearson_ones():
    for (k, n), (low, high) in {(0, 10): (0., .3085), (1, 10): (.0025, .4450), (5, 10): (.1871, .8129),
                                (20, 20): (.8316, 1.), (19, 20): (.7513, .9987)}.items():
        got = interval(k, n)
        assert got == pytest.approx((low, high), abs=5e-5), (k, n, got)
    # One-sided: n successes in n runs leave the rate at least (1 - 0.95) ** (1 / n).
    assert lower_bound(8, 8) == pytest.approx(.05 ** (1 / 8)) and round(lower_bound(8, 8), 3) == .688
    assert round(lower_bound(20, 20), 3) == .861
    assert upper_bound(0, 8) == pytest.approx(1 - .05 ** (1 / 8))
    assert lower_bound(0, 5) == 0. and upper_bound(5, 5) == 1.


def test_a_claim_of_rare_failure_needs_its_runs():
    assert runs_needed(.05) == 59 and runs_needed(.01) == 299
    assert lower_bound(59, 59) >= .95 > lower_bound(58, 58)


@pytest.mark.parametrize('bad', [(3, 2), (-1, 4), (1, 0), (1.5, 3)])
def test_impossible_counts_are_refused(bad):
    with pytest.raises(ValueError):
        lower_bound(*bad)
    with pytest.raises(ValueError):
        runs_needed(0.)


def sweep_of(runs):
    return Sweep('sprint', 'cart', 'drive', 20., None, Ranges(), tuple(runs))


def goals(finish='met'):
    return (Result('start', 'Start line', 'met', 1.9), Result('finish', '5 m finish', finish, 15. if finish == 'met' else None),
            Result('upright', 'Stayed upright', 'kept'))


def test_only_the_runs_drawn_at_random_give_a_rate():
    """Twelve chosen runs - one of them a corner that misses - and eight drawn at random that
    all succeed: the rate is 8 of 8, at least 69 %, and the corner is reported, not counted."""
    chosen = [Run(Variation(), goals())] + [Run(Variation(f'corner {i}', x=.02), goals()) for i in range(10)] + \
             [Run(Variation('carrying 0.5 kg', payload=.5), goals('missed'))]
    random = [Run(Variation(f'repeat {i + 1}', x=.001 * i), goals()) for i in range(8)]
    s = sweep_of(chosen + random)
    assert len(drawn(s)) == 8
    whole, start, finish, upright = rates(s)
    assert (whole.label, whole.met, whole.runs) == ('every goal', 8, 8) and round(whole.low, 3) == .688
    assert (finish.label, finish.met) == ('5 m finish', 8)
    assert assurance(s) == ('8 of 8 random set-ups met every goal,', 'so at least 69% would (95% confidence)')
    report = markdown(s)
    assert '| 5 m finish | 19 of 20 | 8 of 8, at least 69 % |' in report
    assert 'Every goal was met in 8 of them, so at least 69 %' in report and 'The other 12 runs were chosen' in report
    assert '`--samples 59`' in report


def test_a_sweep_with_nothing_drawn_claims_no_rate():
    s = sweep_of([Run(Variation(), goals()), Run(Variation('carrying 0.5 kg', payload=.5), goals())])
    assert rates(s) == [] and assurance(s) == ()
    assert 'no run was drawn at random, so no rate can be given' in markdown(s)


def test_a_static_test_says_how_likely_a_new_run_lands_in_the_drawn_span():
    """Tip angles are readings, not successes: with n drawn, a further run drawn the same
    way lands between their lowest and highest with probability (n - 1) / (n + 1)."""
    held = (Result('held_50', 'Held at 50 deg', 'met', 26.),)
    runs = [Run(Variation(), held, tipped=54.5, predicted=55.8)] + \
           [Run(Variation(f'repeat {i + 1}', x=.002 * i), held, tipped=53. + .5 * i, predicted=55.8) for i in range(8)]
    s = Sweep('tilt', 'arm on a cart', 'hold', 33., None, Ranges(), tuple(runs))
    assert assurance(s) == ('8 random set-ups tipped at 53.0-56.5 deg;', 'a new one lands in that span 7 times in 9')
    assert 'with probability 7/9' in markdown(s)
