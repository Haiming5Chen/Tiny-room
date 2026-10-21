"""The knife-edge check (ADR 0043, FR-024): each set-up drawn at random is run again with the
machine set down a micrometre off, and each measure's spread under that is set against its
spread across the set-ups."""
from math import degrees, inf

import pytest

from little_world.fields.goals import Result
from little_world.fields.variation import Ranges, Variation
from little_world.inventory import jitter
from little_world.inventory.handling import Handled
from little_world.inventory.sweep import Run, Sweep, from_json, markdown, to_json


def test_a_repeat_is_its_set_up_a_micrometre_off_under_its_own_label():
    v = Variation('repeat 7', x=.012, y=-.004, yaw=1.3, payload=.2, friction=.4)
    again = [jitter.jittered(v, k) for k in (1, 2, 3)]
    assert all(a.label == v.label and a.payload == v.payload and a.friction == v.friction for a in again)
    assert all(0 < abs(a.x - v.x) <= jitter.PLACE and abs(a.y - v.y) <= jitter.PLACE for a in again)
    assert all(abs(a.yaw - v.yaw) <= degrees(jitter.TURN) for a in again)
    assert len({(a.x, a.y, a.yaw) for a in again}) == 3 and jitter.jittered(v, 2) == again[1]


def made(label, met=True, time=36., bin_peak=.5):
    """A Fetch run as a sweep keeps it: the cube delivered (or not) and how it was handled."""
    results = (Result('delivered', 'Cube resting in the bin', 'met' if met else 'missed', time if met else None),)
    handled = (Handled('objects/fetch_cube', (('machine', 4.), ('bin', bin_peak)), (('machine', 3.5), ('bin', .26)),
                       26., .003),)
    return Run(Variation(label), results, handled=handled)


RUNS = [made('repeat 1', time=36.), made('repeat 2', time=37.), made('repeat 3', time=38.)]
REPEATS = [made('repeat 1', time=36.01), made('repeat 1', time=35.99, bin_peak=.9), made('repeat 2', time=37.),
           made('repeat 2', time=37.04), made('repeat 3', met=False), made('repeat 3', time=38.)]


def test_how_far_a_measure_spreads_under_a_micrometre_against_across_set_ups():
    """Three hundredths of a second among a set-up's runs (the median) against a second across
    set-ups is the design's. A landing that one set-up's repeats spread by 0.4 N, where the set-ups' own runs
    agreed, leaves the median at nothing but counts that set-up as a knife edge. A set-up whose
    repeats do not all meet every goal is named, and its missed run measures no time."""
    assert jitter.flips(RUNS, REPEATS) == ['repeat 3']
    by = {e.measure: e for e in jitter.edges(RUNS, REPEATS)}
    time = by['last goal met, s']
    assert time.within == pytest.approx(.03) and time.across == pytest.approx(1.) and time.robust
    assert (time.edges, time.sets, time.where) == (0, 2, 'repeat 2') and time.most == pytest.approx(.04)
    landing = by['bin in a step, N']
    assert landing.within == 0. and landing.most == pytest.approx(.4) and landing.where == 'repeat 1'
    assert (landing.edges, landing.sets) == (1, 3) and landing.robust
    lean = jitter.Edge('leaned at most, deg', 2., 3., 'repeat 2', 1.)
    assert lean.ratio == 2. and not lean.robust and jitter.Edge('x', 1., 1., '', 0.).ratio == inf
    assert jitter.groups(RUNS, REPEATS[:2]) == [('repeat 1', [RUNS[0], *REPEATS[:2]])]


def test_the_report_says_what_survived_a_micrometre_and_reads_back():
    result = Sweep('fetch', 'arm on a cart', 'program', 60., None, Ranges(), tuple(RUNS), None, tuple(REPEATS))
    text = markdown(result)
    assert '## Under a micrometre (ADR 0043)' in text and 'The outcome changed in 1 of 3: repeat 3.' in text
    assert "| last goal met, s | 0.03 | 0.04 (repeat 2) | 1 | 0.03 | 0 of 2 | the design's |" in text
    assert "| bin in a step, N | 0 | 0.4 (repeat 1) | 0 | 0.00 | 1 of 3 | the design's |" in text
    assert from_json(to_json(result)) == result
    assert '## Under a micrometre' not in markdown(Sweep('fetch', 'arm on a cart', 'program', 60., None,
                                                         Ranges(), tuple(RUNS)))


def test_a_repeat_moved_by_nothing_is_its_set_up_step_for_step(monkeypatch):
    """With nothing to move it by, a repeat is its set-up to the bit - every step's digest the
    same - so what a micrometre changes is the micrometre's doing."""
    pytest.importorskip('mujoco')
    from little_world.inventory.sweep import design, run
    bp = design('mobile_platform')
    setup = Variation('repeat 4', x=.011, y=-.007, yaw=-1.9)
    monkeypatch.setattr(jitter, 'PLACE', 0.)
    monkeypatch.setattr(jitter, 'TURN', 0.)
    own, again = [], []
    run('sprint', bp, setup, trace=own)
    run('sprint', bp, jitter.jittered(setup, 1), trace=again)
    assert own == again and len(own) > 1000
