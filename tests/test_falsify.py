"""Search for the failure, not only sample it (FR-025): a falsifier over the sourced ranges.

Drawn set-ups certify a rate but do not say where failures live. The falsifier follows a run's
margin - for Fetch, how far inside what the tuning draws certified (ADR 0049) the cube's handling
stayed; for the tilt table, how far past its last hold the machine tipped - with a deterministic
compass search over the variation box. Here its parts on made-up runs and a made-up margin.
"""
import pytest

from little_world.fields.goals import Result
from little_world.fields.variation import Ranges, Variation
from little_world.inventory import falsify as f
from little_world.inventory.handling import Handled
from little_world.inventory.sweep import Run

MET = (Result('lifted', 'Cube lifted 5 cm', 'met', 19.), Result('delivered', 'Cube resting in the bin', 'met', 37.))


def fetched(table=.4, squeeze=3.6, rest=0., label='as designed', results=MET):
    handled = Handled('objects/fetch_cube', peak=(('machine', 4.), ('table', table), ('bin', .5)),
                      steady=(('machine', squeeze), ('table', .18), ('bin', .26)), tilt=26.5, dropped=.004,
                      before=0., rest=rest)
    return Run(Variation(label), results, program='completed', handled=(handled,))


def test_the_box_is_the_variation_ranges_own():
    limits = f.box(Ranges())
    assert [n for n, _, _ in limits] == list(f.NAMES)
    assert dict((n, (lo, hi)) for n, lo, hi in limits)['payload'] == (0., .5)
    v = Variation('x', x=.01, y=-.02, yaw=1.5, payload=.3, at=(0., .04), friction=-.5)
    assert f.variation(f.point(v), 'x') == v
    assert f.describe(f.point(v)) == 'x +1.0 cm, y -2.0 cm, turned +1.5 deg, 0.30 kg +4.0 cm across, friction -0.50'


def test_a_fetch_run_is_read_against_what_the_tuning_draws_certified():
    certified = f.envelope([fetched(table=.22, squeeze=3.2), fetched(table=.618, squeeze=5.)])
    assert certified['force from the table, in a step'] == (.22, .618)
    # At the report's precision 0.623 N is the certified 0.62 N, within; 0.77 N is outside (ADR 0049).
    assert f.fetch_margin(fetched(table=.623), certified)[0] > 0
    margin, why = f.fetch_margin(fetched(table=.77), certified)
    assert margin == pytest.approx((.625 - .77) / .398) and why == 'force from the table, in a step'
    assert f.fetch_margin(fetched(squeeze=3.1), certified) == (pytest.approx((3.1 - 3.195) / 1.8),
                                                                'force from the machine, over 50 ms, the least')
    assert f.fetch_margin(fetched(rest=90.), certified)[1] == 'leaning when it came to rest'
    missed = (Result('lifted', 'Cube lifted 5 cm', 'missed', None),)
    assert f.fetch_margin(fetched(results=missed), certified) == (-1., 'a goal missed')


def test_a_tilt_run_is_read_by_how_far_past_its_last_hold_it_tipped():
    assert f.tilt_margin(Run(Variation(), tipped=54.6)) == (pytest.approx(4.6), 'tipped')
    assert f.tilt_margin(Run(Variation(), tipped=None))[0] == -1.


def test_the_compass_search_follows_the_margin_and_stops_at_a_failure():
    limits = (('a', -1., 1.), ('b', 0., 1.))
    calls = []

    def measure(points):          # a failure past a + b > 1.2, the margin falling towards it
        calls.append(len(points))
        return [(1.2 - p[0] - p[1], 'made up') for p in points]
    tried = f.search(measure, (0., 0.), limits, budget=40)
    assert tried[0].at == (0., 0.) and tried[0].step == 0.
    assert f.first_failure(tried) == len(tried) and tried[-1].margin < 0
    assert max(calls) <= 2, 'two runs at a time'
    assert all(-1 <= t.at[0] <= 1 and 0 <= t.at[1] <= 1 for t in tried), 'inside the box'
    again = f.search(measure, (0., 0.), limits, budget=40)
    assert again == tried, 'deterministic'
    flat = f.search(lambda points: [(1., 'flat')] * len(points), (0., 0.), limits, budget=100)
    assert f.first_failure(flat) is None and min(t.step for t in flat[1:]) == pytest.approx(f.LEAST)
    assert len(f.search(measure, (0., 0.), limits, budget=3)) == 3
    unmoved = f.search(lambda points: [(1., 'flat')] * len(points), (0., 0.), limits, budget=100,
                       still=lambda at, i: i == 1)
    assert all(t.at[1] == 0. for t in unmoved), 'a coordinate that changes nothing is not tried'
    assert f.inert(f.point(Variation()), f.NAMES.index('at')) and not f.inert(f.point(Variation(payload=.1)), 4)


def test_draws_are_read_as_the_search_is_and_the_report_says_both():
    certified = f.envelope([fetched(table=.22), fetched(table=.618)])
    draws = [fetched(table=.5, label='repeat 1'), fetched(table=.77, label='repeat 2'), fetched(table=.4, label='repeat 3')]
    assert f.drawn_margins(draws, f.fetch_margin, certified) == (3, 2, pytest.approx((.625 - .77) / .398))
    tried = (f.Tried((0., 0., 0., 0., 0., 0.), .09, 'force from the machine, over 50 ms, the least', 0.),
             f.Tried((.01, 0., 0., 0., 0., 0.), -.2, 'force from the table, in a step', .5))
    page = f.markdown('fetch', tried, (59, 19, -.35))
    assert '| 2 | 0.5 | x +1.0 cm, y +0.0 cm, turned +0.0 deg, 0.00 kg +0.0 cm across, friction +0.00 | -0.20 **failure** |' in page
    assert 'The first failure: run 2.' in page
    assert 'Drawn at random instead: 59 draws, the first failure at draw 19; their lowest margin -0.35.' in page


def test_the_command_line_needs_a_tuning_sweep(tmp_path, capsys):
    with pytest.raises(SystemExit):
        f.main(['fetch'])
    assert '--tuning' in capsys.readouterr().err
    with pytest.raises(SystemExit):
        f.main(['fetch', '--tuning', str(tmp_path / 'none.json')])
    assert 'No such file' in capsys.readouterr().err
    with pytest.raises(SystemExit):
        f.main(['tilt', '--tuning', 'x.json', '--budget', '0'])
    assert '--budget is a number of runs' in capsys.readouterr().err
