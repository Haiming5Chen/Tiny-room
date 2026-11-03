"""Contracts for planning the draws before a run (FR-039).

A comparison that could not have shown its effect says nothing when it finds none. The sweeps'
own tests - the exact McNemar test on paired runs (ADR 0036), a one-sided bound on a rate (ADR
0028) - and their power, computed by summing over every outcome the draws could give.
"""
import random

import pytest

from little_world.inventory.power import bound_draws, draws_for, mcnemar_p, mcnemar_power, plan, to_show, zero_bound


def test_the_exact_mcnemar_test_needs_six_pairs_all_one_way():
    assert [mcnemar_p(k, 0) for k in (4, 5, 6)] == [.125, .0625, .03125]
    assert mcnemar_p(0, 0) == 1. and mcnemar_p(3, 3) == 1. and mcnemar_p(0, 4) == .125
    assert mcnemar_p(9, 0) == pytest.approx(.0039, abs=1e-4), "ADR 0051's nine pairs"
    assert [to_show(n) for n in (5, 6, 9, 59)] == [None, 6, 6, 6]


def test_adr_0041s_presses_had_a_fifth_of_a_chance_to_show_and_twice_the_draws_would_do():
    rate = 4 / 59
    assert mcnemar_power(59, rate) == pytest.approx(.209, abs=.005)
    assert mcnemar_power(120, rate) == pytest.approx(.83, abs=.01)
    assert mcnemar_power(150, rate) == pytest.approx(.945, abs=.01)
    assert draws_for(rate) == 116
    assert 'underpowered' in plan(rate, draws=59) and 'underpowered' not in plan(rate, draws=120)
    with pytest.raises(ValueError):
        mcnemar_power(10, .7, .5)


def test_a_rate_bounded_by_draws_that_all_succeed():
    assert zero_bound(59) == pytest.approx(.0495, abs=1e-4)
    assert bound_draws(.02) == 149 and bound_draws(.01) == 299
    assert zero_bound(bound_draws(.02)) < .02 <= zero_bound(bound_draws(.02) - 1)
    with pytest.raises(ValueError):
        bound_draws(0.)


def test_the_power_summed_over_outcomes_is_what_random_draws_find():
    rng = random.Random(1)
    n, broke, mended, trials = 30, .15, .03, 4000
    shown = 0
    for _ in range(trials):
        b = c = 0
        for _ in range(n):
            u = rng.random()
            if u < broke:
                b += 1
            elif u < broke + mended:
                c += 1
        shown += mcnemar_p(b, c) <= .05
    assert shown / trials == pytest.approx(mcnemar_power(n, broke, mended), abs=.025)
