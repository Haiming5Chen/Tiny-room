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


def test_where_a_program_decides_what_it_tried_is_counted_apart_from_what_it_met():
    """FR-042: commitment apart from competence. A draw is committed when the program closed its jaws
    on the part, met when every goal was; the report shows both, and names where it tried and failed."""
    from little_world.inventory.boundary import commitment, gap, markdown

    def tried_level(value, outcomes):
        return Level(value, tuple((f'draw {i}', met) for i, (met, _) in enumerate(outcomes)),
                     tuple((f'draw {i}', tried) for i, (_, tried) in enumerate(outcomes)))
    levels = [tried_level(0, [(True, True)] * 4), tried_level(4, [(True, True), (False, True), (True, True), (False, False)]),
              tried_level(8, [(False, False)] * 4)]
    tried = commitment(levels)
    assert [(lv.value, lv.met) for lv in tried] == [(0, 4), (4, 3), (8, 0)]
    assert gap(levels[1]) == ('draw 1',) and gap(levels[0]) == gap(levels[2]) == (), "tried and failed: draw 1 at 4"
    assert commitment([level(10, 1, 1)]) == (), "a machine with no choice has no commitment profile"
    p = profile('fetch', 'the cube moved back', 'cm', levels)
    t = profile('fetch', 'the cube moved back', 'cm', tried)
    report = markdown(p, 'arm cart', t)
    assert 'Tried (the program closed its jaws on it): 50 % at ' in report
    assert '| 4.0 | 2 of 4 | ' in report and ' 3 of 4 | draw 1 |' in report
    assert 'Tried' not in markdown(p, 'arm cart'), "without a commitment profile, as before"
    sharp = profile('fetch', 'the cube moved back', 'cm', [level(5, 9, 9), level(6, 9, 9), level(7, 0, 9)])
    assert sharp.step() == (6, 7) and sharp.line() == ('The cube moved back: every draw to 6.0 cm and none from 7.0 cm - one '
                                                       'half lies between them, finer than the grid not measured.')
    assert p.step() is None, "a crossing between levels some draws met is read as before"


def test_the_fetch_moved_back_moves_only_its_cube():
    from little_world.fields import FETCH, fetch_moved, find_field

    def cube(field):
        return next(b for b in field.build()[1].blueprint.components if b.id == 'fetch_cube').transform.position
    moved = fetch_moved(.05)
    assert moved.id == 'fetch-5' and find_field('fetch-5') is moved and moved.camera == FETCH.camera
    assert cube(moved)[0] == pytest.approx(cube(FETCH)[0] + .05) and cube(moved)[1:] == pytest.approx(cube(FETCH)[1:])
    assert [g.id for g in moved.goals] == [g.id for g in FETCH.goals]
    for back in (-.01, .40):
        with pytest.raises(ValueError):
            fetch_moved(back)


def test_the_fetch_reaches_for_a_cube_it_can_reach_and_declines_one_it_cannot():
    """The Fetch's program is solved for the cube where it is planned and finds it with its camera: 10 cm
    further back it says the cube is out of the arm's reach from its stop, and does not close its jaws."""
    pytest.importorskip('mujoco')
    from little_world.inventory.boundary import levels
    found = levels('reach', (0., 10.), 'mobile_manipulator', samples=0)
    assert [(lv.value, lv.met, lv.tried, lv.committed) for lv in found] == \
        [(0., 1, 1, (('as designed', True),)), (10., 0, 1, (('as designed', False),))]


def test_what_was_measured_is_kept_for_the_examples_as_designed_and_matches_their_reports():
    """The Inventory's 'What it can do' (ADR 0076): an example's measured limits are shown while the design
    is that example as designed, and every number shown is the one its report holds."""
    from pathlib import Path
    from little_world.inventory.boundary import RECORDED, recorded
    from little_world.robots.arm_lab import arm_lab_blueprint
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    root = Path(__file__).resolve().parents[1]
    assert recorded(mobile_manipulator_blueprint()) == ('mobile_manipulator', RECORDED['mobile_manipulator'])
    assert [f for f, _, _ in recorded(mobile_platform_blueprint())[1]] == ['curb']
    assert recorded(arm_lab_blueprint()) == (None, ()), "not measured: no record"
    shown = {factor: (words, (root / report).read_text(encoding='utf-8')) for found in RECORDED.values() for factor, words, report in found}
    words, report = shown['curb']
    assert '14.3 mm (12.5 to 18.1)' in words and '50 % at 14.3 mm, 95 % between 12.5 and 18.1 mm' in report
    words, report = shown['tilt']
    assert '53.5 deg (51.8 to 54.6)' in words and '50 % at 53.5 deg, 95 % between 51.8 and 54.6 deg' in report
    assert '54.6 to 58.7' in words and '| repeat 8 | 56 | 57 | 58.7 |' in report and '| as designed | 50 | 51 | 54.6 |' in report
    words, report = shown['reach']
    assert 'up to 6 cm; from 7 cm none' in words and 'every draw to 6.0 cm and none from 7.0 cm' in report
