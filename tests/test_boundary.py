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


def test_a_table_stopped_at_its_top_is_met_once_the_machine_has_stood_there_its_hold():
    """The tilt table as a factor (ADR 0076): a table that stops at a level and holds there; the machine
    must still stand `hold` seconds after the table passed it, not merely as it passes."""
    from math import cos, radians, sin
    from little_world.components import Transform
    from little_world.core.state import BodyState, State
    from little_world.fields import FIELDS, TILT_MAX, tilt_seconds, tilt_table, tilt_target
    from little_world.fields.goals import GoalTracker, TiltHold
    from little_world.inventory.boundary import FACTORS, SECONDS

    def at(t, table, machine):
        def body(a):
            return BodyState(Transform((0., 0., 0.), (cos(radians(a) / 2), sin(radians(a) / 2), 0., 0.)), (0.,) * 3, (0.,) * 3)
        return State(t, {'field/table': body(table), 'machine/base': body(machine)})

    stood, fell = TiltHold('stood', 'Stood', 'field/table', 20., hold=3.), TiltHold('fell', 'Fell', 'field/table', 20., hold=3.)
    tracker, other = GoalTracker((stood,), 'machine/base'), GoalTracker((fell,), 'machine/base')
    for t, table, machine, toppled in ((0., 10., 10., 10.), (5., 20.4, 21., 21.), (7., 20.4, 21., 50.), (8., 20.4, 21., 50.)):
        tracker.update(at(t, table, machine))
        other.update(at(t, table, toppled))
    assert tracker.results()[0].status == 'met' and tracker.results()[0].time == 8., "stood 3 s since it passed 20 deg at 5 s"
    assert (other.results()[0].status, other.results()[0].detail) == ('missed', 'tipped over at 20 deg')

    assert tilt_target(100., 52.) == 52. and tilt_target(11., 52.) == pytest.approx(20.) and tilt_target(100.) == TILT_MAX
    field = tilt_table(52.)
    (goal,) = field.goals
    assert (goal.angle, goal.hold, goal.label) == (51.5, 3., 'Stood 3 s at 52 deg'), "its servo settles within half a degree"
    assert field.squared and field.fitted and field.side == FIELDS['tilt'].side, "squared and railed as the Tilt table is"
    from little_world.fields import find_field
    assert field.id == 'tilt-52' and find_field('tilt-52') is field, "the window finds it by its own id (What's new)"
    assert tilt_seconds(52.) == pytest.approx(1. + 26. + 3. + .5) == SECONDS['tilt'](52.)
    assert FACTORS['tilt'][:2] == ('tilt', 'deg') and FACTORS['tilt'][3] == 'table angle'
    for top in (0., 61.):
        with pytest.raises(ValueError):
            tilt_table(top)


def test_held_at_51_deg_the_arm_cart_goes_over_though_the_ramp_carries_it_past_54():
    """ADR 0076's tilt check: the 2 deg/s ramp reads the arm cart going over at 54.6 deg (ADR 0029), but held
    at 51 deg it goes over within the hold - creeping along the trip rail until it runs away - and held at
    47 deg it stands."""
    pytest.importorskip('mujoco')
    from little_world.inventory.boundary import levels
    found = levels('tilt', (47., 51.), 'mobile_manipulator', samples=0)
    assert [(lv.value, lv.met, lv.tried) for lv in found] == [(47., 1, 1), (51., 0, 1)]
