"""Contracts for capability boundaries (FR-042, ADR 0076): where a design's success falls through one
half along one factor, from the same draws at every level, with an interval."""
import pytest

from little_world.inventory.boundary import Level, crossing, monotone, profile


def level(value, met, tried):
    return Level(value, tuple((f'draw {i}', i < met) for i in range(tried)))


def test_rates_are_fitted_to_fall_and_the_crossing_is_found_between_the_levels_it_falls_between():
    levels = [level(8, 9, 9), level(12, 6, 9), level(14, 7, 9), level(16, 3, 9), level(18, 0, 9)]
    fitted = monotone(levels)
    assert fitted == pytest.approx((1., 13 / 18, 13 / 18, 1 / 3, 0.)), "12 and 14 mm pooled: the higher did better"
    assert crossing([8, 12, 14, 16, 18], fitted) == pytest.approx(14 + 2 * (13 / 18 - .5) / (13 / 18 - 1 / 3))
    assert crossing([8, 12], (1., .9)) is None and crossing([8, 12], (.4, .1)) is None, "not within the grid"
    p = profile('curbs', 'curb height', 'mm', levels)
    assert p.pooled() == ((12, 14),) and 'From 12.0 to 14.0 mm a higher level did better than a lower one: pooled.' in p.line()


def test_the_interval_comes_from_the_draws_and_narrows_with_more_of_them():
    few = profile('curbs', 'curb height', 'mm', [level(v, m, 9) for v, m in ((14, 9), (16, 7), (18, 4), (20, 2), (22, 0))])
    more = profile('curbs', 'curb height', 'mm', [level(v, 2 * m, 18) for v, m in ((14, 9), (16, 7), (18, 4), (20, 2), (22, 0))])
    assert few.at == pytest.approx(more.at) and few.low < few.at < few.high
    assert profile('curbs', 'curb height', 'mm', few.levels, seed=1) == few, "the bootstrap's seed is recorded and repeats"
    assert (more.high - more.low) < (few.high - few.low), "more draws a level, a narrower interval"
    assert few.line().startswith('Curb height: 50 % at 17.')


def test_a_curb_a_kit_cart_clears_and_one_it_cannot():
    pytest.importorskip('mujoco')
    from little_world.inventory.boundary import levels
    found = levels('curb', (10., 30.), 'mobile_platform', samples=0, duration=25.)
    assert [(lv.value, lv.met, lv.tried) for lv in found] == [(10., 1, 1), (30., 0, 1)]
