"""Contracts for runs under variation (ADR 0024).

The defect: a test field ran its scenario once, exactly as designed - the machine on its
mark, carrying nothing, on surfaces at the one friction value each source gives. A lab
repeats a test, and no repeat is the same, so one run could not say how far its result
holds: whether the arm on a cart tips at 54 degrees, or anywhere from 52 to 57.
"""
import math
import re
import pytest

from little_world.construction.docking import poses
from little_world.construction.structure import centre_of_mass, standing
from little_world.fields.variation import (GAP, STEEL, Ranges, Variation, carrier, friction, loaded,
                                           moved, payload_site, plan, varied)
from little_world.materials import contact_pairs as cp
from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
from little_world.robots.mobile_platform import mobile_platform_blueprint


# -- the plan and each variation: data, no solver -------------------------------------------

def test_a_plan_runs_as_designed_then_one_change_at_a_time_then_seeded_repeats():
    p = plan()
    assert p[0] == Variation() and p[0].nominal and len(p) == 20
    alone = p[1:12]
    assert all(sum(1 for v in (a.x, a.y, a.yaw, a.payload, a.friction) if v) == 1 for a in alone)
    assert len({v.label for v in p}) == len(p)
    assert plan() == p and plan(seed=2) != p, 'seeded: the same plan every time it is made'
    r = Ranges()
    for v in p:
        assert abs(v.x) <= r.place and abs(v.y) <= r.place and abs(v.yaw) <= r.turn
        assert 0 <= v.payload <= r.payload and abs(v.friction) <= r.friction
    assert plan(Ranges(place=0, turn=0, payload=0, friction=0), samples=0) == (Variation(),)


def test_impossible_variations_are_refused():
    for bad in (dict(payload=-1.), dict(friction=1.5), dict(x=math.nan), dict(at=(0.,)), dict(yaw=math.inf)):
        with pytest.raises(ValueError):
            Variation(**bad)
    with pytest.raises(ValueError):
        Ranges(friction=2.)


def test_setting_a_machine_down_off_its_mark_moves_and_turns_all_of_it_about_the_mark():
    bp = mobile_platform_blueprint()
    assert moved(bp) is bp
    before, after = poses(bp), poses(moved(bp, .02, -.01, 90.))
    for name, place in before.items():
        x, y, z = place.position
        assert after[name].position == pytest.approx((-y + .02, x - .01, z), abs=1e-9), name


def test_a_payload_is_a_steel_block_set_down_on_what_carries_it():
    """Over the platform's centre of mass the middle cross member carries it: a 4 cm steel
    cube of 0.5 kg, 1 mm above it, fixed to it."""
    bp = mobile_platform_blueprint()
    site = payload_site(bp)
    body, top = carrier(bp, site, .5)
    assert body == 'cross_1'
    heavy = loaded(bp, .5, site)
    block = next(c for c in heavy.components if c.id == 'payload')
    side = block.geometry.size[0]
    assert side ** 3 * STEEL == pytest.approx(.5) and side == pytest.approx(.0399, abs=1e-4)
    assert block.parent == 'cross_1'
    assert poses(heavy)['payload'].position[2] == pytest.approx(top + GAP + side / 2)
    assert centre_of_mass(heavy)[0] == pytest.approx(centre_of_mass(bp)[0] + .5)
    assert loaded(bp, 0., site) is bp
    with pytest.raises(ValueError, match='already'):
        loaded(heavy, .5, site)
    with pytest.raises(ValueError, match='nothing on the machine'):
        loaded(bp, .5, (1., 1.))


def test_a_payload_goes_where_nothing_that_moves_reaches_over_it():
    """On the arm on a cart the upper arm leans over the centre of mass, so the block goes
    on the deck, behind the arm, in the middle."""
    bp = mobile_manipulator_blueprint()
    _, com = centre_of_mass(bp)
    with pytest.raises(ValueError, match='moving part'):
        carrier(bp, com[:2], .5)
    site = payload_site(bp)
    assert carrier(bp, site, .5)[0] == 'arm_deck' and site[0] < -.08 and abs(site[1]) < .01
    s = standing(varied(bp, Variation(payload=.5), site))
    assert s.tip('right') > standing(bp).tip('right'), 'weight low and behind the arm: steadier sideways'


def test_friction_varies_each_pair_across_the_range_its_source_gives():
    for key, pair in cp.PAIRS.items():
        low, high, cited = cp.spread(*key)
        assert 0 < low <= pair.kinetic <= high < 2, key
        if cited:     # each end is the value used or a number the pair's own note quotes
            quoted = {float(n) for n in re.findall(r'\d+\.\d+', pair.note)} | {pair.kinetic}
            assert any(abs(low - q) < 1e-9 for q in quoted) and any(abs(high - q) < 1e-9 for q in quoted), key
        else:
            assert high / low == pytest.approx(2.)
    assert cp.varied(0.) == {k: p.kinetic for k, p in cp.PAIRS.items()}
    tread = ('concrete', 'rubber')
    assert (cp.varied(-1.)[tread], cp.varied(.5)[tread], cp.varied(1.)[tread]) == pytest.approx((.60, 1.01, 1.07))
    assert friction(Variation()) is None and friction(Variation(friction=-1.)) == cp.varied(-1.)
    with pytest.raises(ValueError):
        cp.varied(1.5)


# -- in the simulator ----------------------------------------------------------------------

mujoco = pytest.importorskip('mujoco')
from little_world import Entity, World  # noqa: E402
from little_world.fields import field_scene  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402


def test_a_run_can_use_other_pair_frictions_and_return_to_the_sources():
    backend = MujocoBackend()
    with World(backend, field_scene('sprint', Entity('machine', mobile_platform_blueprint()))) as world:
        world.start()
        tread = cp.lookup('rubber', 'concrete')

        def coefficients():
            for _ in range(50):     # it starts 2 mm up: let it land
                world.step({})
            return {round(mu, 4) for _, _, mu, pair in backend.contact_report() if pair is tread}
        assert coefficients() == {.95}
        backend.vary_pair_friction(cp.varied(-1.))
        assert coefficients() == {.6}
        backend.vary_pair_friction(None)
        assert coefficients() == {.95}
        for bad in ({('rubber', 'cork'): .5}, {('rubber', 'concrete'): 0.}, {('rubber', 'concrete'): math.nan}):
            with pytest.raises(ValueError):
                backend.vary_pair_friction(bad)


def test_the_simulator_weighs_the_payload_and_starts_the_machine_where_it_was_set_down():
    bp = mobile_manipulator_blueprint()
    heavy = varied(bp, Variation(x=.02, y=-.01, yaw=3., payload=.5))
    backend = MujocoBackend()
    with World(backend, field_scene('sprint', Entity('machine', heavy))) as world:
        world.start()
        m, d = backend.model, backend.data
        root = m.body('machine/root').id
        assert float(m.body_subtreemass[root]) == pytest.approx(centre_of_mass(bp)[0] + .5, rel=1e-9)
        assert float(m.body('machine/payload').mass[0]) == pytest.approx(.5, rel=1e-9)
        assert tuple(d.xpos[root]) == pytest.approx(poses(heavy)['root'].position, abs=1e-9)


def test_a_sweep_reports_every_goal_over_its_runs_and_what_each_variation_changed():
    from little_world.inventory.sweep import from_json, markdown, spread, sweep, to_json
    variations = (Variation(), Variation('friction at its low end', friction=-1.),
                  Variation('carried off the machine', payload=.5, at=(1., 1.)))
    s = sweep('sprint', mobile_platform_blueprint(), variations, 'mobile_platform')
    assert [r.variation for r in s.runs] == list(variations)
    assert from_json(to_json(s)) == s, 'what the app reads back from a sweep run apart'
    assert 'nothing on the machine' in s.runs[-1].error and not s.runs[-1].results
    rows = {label: (good, total) for label, good, total, _, _ in spread(s)}
    assert rows['5 m finish'] == (2, 2) and rows['Stayed upright'] == (2, 2)
    text = markdown(s)
    assert '| 5 m finish | 2 of 2 |' in text and 'not run: nothing on the machine' in text


def test_the_tilt_table_follows_the_prediction_with_a_payload_aboard():
    """The arm on a cart with 0.5 kg on its deck behind the arm: its centre of mass is lower
    and further from the table's low edge, and it tips 2.9 degrees later - 57.4 against a
    prediction of 57.6 about the rail, closer than as designed (54.5 against 55.8), where
    the loaded front caster swivels out from under it first."""
    from little_world.inventory.sweep import run
    bp = mobile_manipulator_blueprint()
    plain, heavy = run('tilt', bp), run('tilt', bp, Variation(payload=.5), site=payload_site(bp))
    assert heavy.tipped - plain.tipped > 2.
    assert abs(heavy.tipped - heavy.predicted) < 1. and heavy.predicted > plain.predicted


# -- reading a sweep, and the run report that starts one ----------------------------------

def made_up_sweep():
    """A sprint sweep's shape without running it: as designed, slower on a slippery floor,
    and the 5 m finish missed with a payload aboard."""
    from little_world.fields.goals import Result
    from little_world.inventory.sweep import Run, Sweep

    def results(finish, status='met'):
        return (Result('start', 'Start line', 'met', 1.9), Result('finish', '5 m finish', status, finish),
                Result('upright', 'Stayed upright', 'kept'))
    return Sweep('sprint', 'cart', 'drive', 20., None, Ranges(), (
        Run(Variation(), results(15.), seconds=5.),
        Run(Variation('friction at its low end', friction=-1.), results(15.6), seconds=5.),
        Run(Variation('carrying 0.5 kg', payload=.5), results(None, 'missed'), seconds=5.),
        Run(Variation('repeat 1', x=.01), results(15.1), seconds=5.),
        Run(Variation('carried off the machine', payload=.5, at=(1., 1.)), error='nothing on the machine')))


def test_a_sweep_reads_as_one_line_and_names_what_moved_it_most():
    from little_world.inventory.sweep import headline, moved_most
    s = made_up_sweep()
    assert headline(s) == ('Every goal met in 3 of 4 runs', 'warn')
    assert moved_most(s) == [('carrying 0.5 kg', '5 m finish: missed'),
                             ('friction at its low end', '5 m finish +0.6 s')], 'a lost goal first; repeats are not singled out'


def test_a_sweep_draws_as_ticks_of_the_quantity_that_spread():
    from dataclasses import replace
    from little_world.inventory.sweep import strip
    s = made_up_sweep()
    line = strip(s)
    assert line.label == '5 m finish' and sorted(line.values) == [15., 15.1, 15.6] and line.nominal == 15.
    assert line.unit == 's' and line.predicted is None
    tilted = replace(s, runs=tuple(replace(r, tipped=54.5 + i, predicted=55.8) for i, r in enumerate(s.runs)))
    line = strip(tilted)
    assert line.label == 'tipped over at' and line.values == (54.5, 55.5, 56.5, 57.5) and line.nominal == 54.5
    assert line.predicted == 55.8


@pytest.mark.skipif(__import__('os').name != 'posix', reason='process groups are POSIX')
def test_stopping_the_repeats_stops_their_worker_processes_with_them(monkeypatch):
    """The sweep runs its variations in worker processes of its own; stopping it from the
    report kills its whole process group, not just the parent."""
    import signal
    from little_world.ui import varied_runs
    killed = []
    monkeypatch.setattr(varied_runs.os, 'killpg', lambda group, sig: killed.append((group, sig)))

    class Running:
        pid = 4242

        def poll(self):
            return None
    holder = varied_runs.VariedRuns()
    holder.init_varied_runs()
    holder.varied = dict(process=Running())
    holder.stop_variations()
    assert killed == [(4242, signal.SIGKILL)] and holder.varied is None


@pytest.mark.skipif(__import__('os').environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')
def test_a_run_report_repeats_the_run_with_variations_in_another_process(monkeypatch, tmp_path):
    import sys
    import time
    import glfw
    from little_world.inventory.sweep import Sweep, to_json
    from little_world.ui.workshop import Workshop
    app = Workshop(tmp_path / 'cart.json', mobile_platform_blueprint())
    made = to_json(made_up_sweep())

    def command(field, design, out, name):
        assert field == 'sprint' and name == 'cart' and design.read_text() == app.editor.blueprint.to_json()
        return [sys.executable, '-c', 'import pathlib, sys\n'
                "for i in (1, 2): print(f'  {i}/3 run {i}: 5 s', flush=True)\n"
                f'pathlib.Path({str(out)!r}).write_text({made!r})\n'
                "print('  3/3 run 3: 5 s', flush=True)"]
    monkeypatch.setattr(app, 'vary_command', command)
    draw = app.draw
    step = {'n': 0, 't': 0.}

    def click(label):
        b = next(b for b in app.buttons if b.label.startswith(label))
        assert b.enabled, label
        app.events.append(b.action)

    def exercise():
        draw()
        n, now = step['n'], time.monotonic()
        if n == 0:
            app.set_field('sprint')
            click('SIMULATE')
        elif n == 1:
            app.key(app.window, glfw.KEY_W, 0, glfw.PRESS, 0)
            step['t'] = now
        elif n == 2:
            if app.state.time < .5:
                return
            app.key(app.window, glfw.KEY_W, 0, glfw.RELEASE, 0)
            click('STOP / RETURN TO BUILD')
        elif n == 3:
            assert app.run_report is not None
            click('Repeat with variations (20 runs)')
        elif n == 4:
            assert app.varied is not None and app.varied['field'] == 'sprint'
            if app.varied['result'] is None and not app.varied['error']:
                assert now - step['t'] < 30., 'the repeats should have finished'
                return
            assert not app.varied['error'] and isinstance(app.varied['result'], Sweep)
            assert app.varied['done'] == app.varied['total'] == 3
            assert 'every goal met in 3 of 4 runs' in app.status
        elif n == 5:
            click('Copy the full report')
        elif n == 6:
            assert glfw.get_clipboard_string(None).decode().startswith('# Sprint lane, varied: cart')
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=60)
    assert step['n'] == 7
