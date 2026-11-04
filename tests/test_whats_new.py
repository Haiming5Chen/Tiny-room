"""Contracts for the Guide's What's new: recent work run in the window, as the sweeps ran it (ADR 0055).

The defect: what the sweeps measured - the cube moved after the program looked, a camera that
freezes, a shove, an alarm from outside - happened in another process and ended as counts in a
report; the owner saw nothing of it in the app. Each demonstration is a button that sets the
machine, field and program up, arms the disturbance the sweeps tried and runs it; the test for
each does what a user does and checks the machine does what the button says it will.
"""
import os
import textwrap
from types import SimpleNamespace

import pytest

from little_world.fields.disturbance import DEFAULTS, WEAK
from little_world.ui.live_disturbance import LiveDisturbance
from little_world.ui.program_workspace import ProgramWorkspace
from little_world.ui.whats_new import BY_ID, DEMOS


def test_each_demonstration_says_what_to_watch_and_arms_one_of_the_fetch_fields_disturbances():
    labels = {d.label for d in DEFAULTS['fetch'] + WEAK['fetch']}
    assert [d.id for d in DEMOS] == ['fed', 'conveyor', 'squeeze', 'panda', 'repeats', 'slip', 'tipping', 'hot_motor', 'factory',
                                     'look_again', 'frozen', 'shove', 'alarm'], "newest first"
    assert set(BY_ID) == {d.id for d in DEMOS}
    assert [d.where for d in DEMOS] == ['factory', 'conveyor', 'fetch', 'factory', 'fetch', 'fetch', 'tilt', 'fetch', 'factory'] + ['fetch'] * 4
    assert [d.heavier for d in DEMOS] == [1., 1., 1., 1., 1., 16.] + [1.] * 7
    assert [d.id for d in DEMOS if d.after] == ['repeats'], "the one that ends on its run's report"
    assert [d.product for d in DEMOS] == ['Small block'] * 3 + ['Tall block'] + ['Small block'] * 9
    assert [d.squeeze for d in DEMOS] == [0., 0., 7.] + [0.] * 10
    assert [d.feeder for d in DEMOS] == ['conveyor'] + ['hand'] * 12
    for demo in DEMOS:
        assert demo.title and demo.shows and demo.watch and demo.adr.startswith('ADR ')
        assert demo.disturbance == '' or demo.disturbance in labels, demo.disturbance
        assert len(textwrap.wrap(demo.shows, 40)) <= 8 and len(textwrap.wrap('Watch for: ' + demo.watch, 40)) <= 4, \
            "the Guide shows all of it"


class Bench(LiveDisturbance):
    """The window's parts a live disturbance reads: its field, machine, state and goals' clock."""

    def __init__(self, field='fetch'):
        self.field_id = field
        self.editor = SimpleNamespace(bodies=[SimpleNamespace(id='base', parent=None),
                                              SimpleNamespace(id='arm', parent='base')])
        self.backend = SimpleNamespace(moved=[], shift=lambda part, offset, turn=0.: self.backend.moved.append((part, offset)))
        self.goal_tracker = SimpleNamespace(start=None, met={})
        self.eye = None
        self.status = ''
        self.at(0.)
        self.init_live_disturbance()

    def at(self, time, speed=0.):
        self.state = SimpleNamespace(time=time, bodies={'machine/base': SimpleNamespace(linear_velocity=(speed, 0., 0.))})


def test_a_disturbance_is_armed_by_its_label_until_cleared_and_only_from_the_fields_own():
    bench = Bench()
    bench.arm_disturbance('cube moved 5 cm sideways, 2 s later')
    assert bench.live_disturbance.label == 'cube moved 5 cm sideways, 2 s later' and bench.live_kick is None
    with pytest.raises(ValueError, match='no disturbance called'):
        bench.arm_disturbance('cube thrown across the room')
    assert bench.live_disturbance.label == 'cube moved 5 cm sideways, 2 s later', "a wrong name leaves it armed"
    bench.arm_disturbance(None)
    assert bench.live_disturbance is None and bench.live_note == ''
    with pytest.raises(ValueError):
        Bench('doorway').arm_disturbance('shoved 6 N s at the table')


def test_the_armed_disturbance_happens_on_its_trigger_once_a_run_and_the_window_says_when():
    bench = Bench()
    bench.arm_disturbance('cube moved 5 cm sideways, 2 s later')
    bench.tick_live_disturbance()
    assert bench.live_kick is None, "no run, no goals' clock: nothing to disturb"
    bench.goal_tracker.start = 1.
    for t in (2., 9., 11.):                         # driving, then at the table before it is still
        bench.at(t, speed=.3 if t < 11 else 0.)
        bench.tick_live_disturbance()
    assert bench.live_kick.root == 'machine/base' and not bench.backend.moved, "not before the cart reached the table"
    bench.goal_tracker.met['reached'] = 10.
    for t in (11.1, 11.31, 13.0, 13.40):            # still from 11.1 s: 0.2 s, then 2.1 s later
        bench.at(t)
        bench.tick_live_disturbance()
    assert not bench.backend.moved and bench.live_note == ''
    bench.at(13.43)
    bench.tick_live_disturbance()
    assert bench.backend.moved == [('objects/fetch_cube', (0., .05))]
    assert bench.live_note == 'cube moved 5 cm sideways, 2 s later - at 12.4 s'
    assert bench.status == 'Disturbed: cube moved 5 cm sideways, 2 s later. Watch what the machine does.'
    bench.at(20.)
    bench.tick_live_disturbance()
    assert len(bench.backend.moved) == 1, "once a run"
    bench.end_live_disturbance()
    assert bench.live_kick is None and bench.live_disturbance is not None, "armed for the next run, afresh"


def test_a_camera_fault_fails_the_programs_camera_once_it_has_one():
    bench = Bench()
    failed = []
    bench.eye = SimpleNamespace(fail=failed.append)
    bench.arm_disturbance('camera frozen as the cube is moved 5 cm')
    bench.goal_tracker.start, bench.goal_tracker.met['reached'] = 0., 5.
    for t in (5., 5.25, 5.36):
        bench.at(t)
        bench.tick_live_disturbance()
    assert failed == ['freeze'] and bench.backend.moved == [('objects/fetch_cube', (0., .05))]


def test_look_again_asks_a_listening_program_and_says_why_when_it_cannot():
    asked = []
    bench = SimpleNamespace(status='', runner=SimpleNamespace(alarm=lambda message: asked.append(message) or bool(asked[1:])))
    with pytest.raises(ValueError, match='only at a stop where it looked'):
        ProgramWorkspace.look_again(bench)
    ProgramWorkspace.look_again(bench)
    assert asked == ['You asked it to look again'] * 2
    assert bench.status.startswith('Looking again: it opens its jaws, rises')


def test_the_program_panel_says_what_the_program_sees_and_what_its_jaws_feel(monkeypatch):
    from little_world.control import feel
    from little_world.control.feel import Jaw
    bench = SimpleNamespace(runner=SimpleNamespace(seen=[], faults=[]), eye=None, tool_motion=None, backend=None,
                            joint_control=None)
    assert ProgramWorkspace.senses(bench) == ('Camera: this program does not look', 'Jaws: no servos to read')
    bench.eye, bench.tool_motion = object(), SimpleNamespace(jaws=('jaw_left', 'jaw_right'))
    registers = [Jaw(100, 100, 0, 0), Jaw(100, 100, 0, 0)]       # at their goals, still: on nothing
    monkeypatch.setattr(feel, 'read', lambda backend, control, actuators: tuple(registers))
    assert ProgramWorkspace.senses(bench) == ('Camera: it has not looked yet', 'Jaws: nothing between them')
    bench.runner.seen.append(('objects/fetch_cube', (1., 0., .7), (1., .048, .7)))
    registers[:] = [Jaw(90, 120, 0, 30), Jaw(91, 120, 0, 31)]   # stopped 30 pulses short, pushing
    assert ProgramWorkspace.senses(bench) == ('Camera: saw the fetch_cube 4.8 cm from the plan',
                                              'Jaws: holding - stopped on it, pushing (81 mA)')
    registers[0] = Jaw(90, 120, 40, 30)
    assert ProgramWorkspace.senses(bench)[1] == 'Jaws: moving'
    bench.runner.faults.append('stale')
    assert ProgramWorkspace.senses(bench)[0] == 'Camera: its picture is not new', "a frozen camera, not its last sighting"


# -- in the window: each demonstration started as a user starts it ---------------------------

WINDOW = pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1', reason='requires OpenGL')


def window(tmp_path):
    from little_world.construction.editor import starter_blueprint
    from little_world.ui.workshop import Workshop
    app = Workshop(tmp_path / 'design.json', starter_blueprint())
    app.factory_recipe_path = tmp_path / 'cell.json'
    return app


def click(app, label):
    b = next(b for b in app.active_workspace.buttons if b.label.startswith(label))
    assert b.enabled, label
    app.active_workspace.events.append(b.action)


def enabled(app, label):
    return next(b for b in app.active_workspace.buttons if b.label.startswith(label)).enabled


FETCHED = {'reached': 'met', 'lifted': 'met', 'delivered': 'met', 'upright': 'kept'}


def goals(app):
    return {g.id: g.status for g in app.goal_tracker.results()}


def said(app, monkeypatch, panel):
    """What the window's `panel` (one of its drawing methods) writes, frame after frame."""
    words = []
    draw = getattr(app, panel)

    def spy(ui, button, text, *rest):
        def written(w, *a, **k):
            words.append(w)
            return text(w, *a, **k)
        return draw(ui, button, written, *rest)
    monkeypatch.setattr(app, panel, spy)
    return words


@WINDOW
def test_one_click_from_the_top_bar_the_cube_moved_after_the_look_is_looked_for_again_and_fetched(tmp_path, monkeypatch):
    import glfw
    from little_world.ui.whats_new import TABLE_VIEW
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}
    order = []

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            click(app, "What's new")                 # the top bar's button
        elif n == 1:
            assert app.active_tab == 'Guide' and app.guide_view == 'New'
            click(app, 'Watch it look again')
        elif n == 2:
            assert app.field_id == 'fetch' and app.control_panel and app.panel_mode == 'program'
            assert app.live_disturbance.label == 'cube moved 5 cm sideways, 2 s later'
            assert app.runner.state == 'running' and app.status.startswith('Watch it look again: ')
            assert app.drive_view == 'free' and tuple(app.camera.lookat) == pytest.approx(TABLE_VIEW[0])
            assert not enabled(app, 'Look again'), "nothing to look at again before it has looked"
        elif n == 3:
            r = app.runner
            for event, happened in (('moved', bool(app.live_note)), ('looked again', r.regrasps > 0)):
                if happened and event not in order:
                    order.append(event)
            if r.state == 'running':
                assert app.state.time < 80, r.message
                return
            assert r.state == 'completed' and goals(app) == FETCHED, (r.message, goals(app))
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=600)
    assert step['n'] == 4 and order == ['moved', 'looked again'], order
    assert app.live_note.startswith('cube moved 5 cm sideways, 2 s later - at ')


@WINDOW
def test_a_frozen_camera_stops_the_program_and_look_again_pressed_while_it_reaches_is_obeyed(tmp_path, monkeypatch):
    import glfw
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_whats_new()
        elif n == 1:
            click(app, 'A camera that freezes')
        elif n == 2:
            r = app.runner
            if r.state == 'running':
                assert app.state.time < 40, r.message
                return
            assert r.state == 'failed' and r.message == "Looked for fetch_cube: the camera's picture is not new", r.message
            assert app.live_note.startswith('camera frozen as the cube is moved 5 cm - at ')
            assert app.senses()[0] == 'Camera: its picture is not new' and goals(app)['lifted'] == 'open'
            click(app, 'Tell it to look again yourself')
        elif n == 3:
            r = app.runner
            assert app.live_disturbance is None and r.state == 'running', r.message
            if not r.listening():
                assert app.state.time < 40 and not enabled(app, 'Look again'), r.message
                return
            click(app, 'Look again')
        elif n == 4:
            r = app.runner
            assert r.regrasps == 1 and r.message == 'You asked it to look again', r.message
            assert app.status.startswith('Looking again: ') and not enabled(app, 'Look again'), "once a run"
        elif n == 5:
            r = app.runner
            if r.state == 'running':
                assert app.state.time < 80, r.message
                return
            assert r.state == 'completed' and goals(app) == FETCHED, (r.message, goals(app))
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=600)
    assert step['n'] == 6


@WINDOW
def test_the_cart_shoved_off_its_stop_goes_back_to_it_and_fetches_the_cube(tmp_path, monkeypatch):
    import glfw
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}
    went_back = []

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_whats_new()
        elif n == 1:
            click(app, 'Shove the cart off its stop')
        elif n == 2:
            r = app.runner
            if r.retries and not went_back:
                went_back.append(r.message)
            if r.state == 'running':
                assert app.state.time < 80, r.message
                return
            assert r.state == 'completed' and goals(app) == FETCHED, (r.message, goals(app))
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=600)
    assert step['n'] == 3 and app.live_note.startswith('shoved 6 N s at the table - at ')
    assert len(went_back) == 1 and went_back[0].startswith('Pushed ') and went_back[0].endswith('off its stop: going back')


@WINDOW
def test_the_factory_demonstration_runs_reals_cell_and_says_where_each_part_landed(tmp_path, monkeypatch):
    import glfw
    from little_world.factory.controller import SLOTS
    from little_world.factory.process import judge, slot_room
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}
    cell = {}

    def in_the_cell():
        real = app.active_workspace
        cell['draw']()
        n = step['n']
        if n == 2:
            assert real.app_mode == 'Real' and real.experiment == 'Pick and place' and real.product == 'Small block'
            assert real.cycle.run is not None and real.cycle.state == 'running' and app.demo == 'factory'
        elif n == 3:
            placed = real.cycle.run['placements']
            if len(placed) < 2:
                assert real.state.time < 60 and real.cycle.state == 'running', real.cycle.message
                return
            zx, zy, turn = slot_room(SLOTS, 32.)
            w = judge(placed, (zx, zy), turn)
            assert w.inside == 2 and w.worst < zx and 11. < w.slowest < 15., w
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_whats_new()
        elif n == 1:
            button = next(b for b in app.active_workspace.buttons if b.label == 'Six parts, measured')
            button.action()                       # Real's cell draws from here on
            real = app.active_workspace
            cell['draw'] = real.draw
            monkeypatch.setattr(real, 'draw', in_the_cell)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=600)
    assert step['n'] == 4


@WINDOW
def test_the_tipping_demonstration_counts_down_the_degrees_left_as_the_table_tilts(tmp_path, monkeypatch):
    import glfw
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}
    seen = []

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_whats_new()
        elif n == 1:
            click(app, 'How near it is to tipping')
        elif n == 2:
            assert app.field_id == 'tilt' and not app.building and app.active_tab == 'Edit' and app.demo == 'tipping'
        elif n == 3:
            sample = app.drive_sample
            if sample is not None and sample.tip is not None:
                seen.append((app.state.time, sample.tip))
            if app.state.time < 8.:
                return
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    words = said(app, monkeypatch, 'draw_static_test_panel')
    app.run(seconds=600)
    assert step['n'] == 4 and seen
    assert seen[0][1] > 40. and seen[-1][1] < seen[0][1] - 3., (seen[0], seen[-1])
    counts = [float(w.split()[0]) for w in words if w.endswith(' deg from tipping')]
    assert counts and counts[0] > 40. and counts[-1] < counts[0] - 3., "the panel counts it down"


@WINDOW
def test_a_motor_run_hot_is_marked_in_the_drive_panel_and_the_cube_is_fetched_as_cool(tmp_path, monkeypatch):
    import glfw
    from little_world.fields.disturbance import hot
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}
    kept = []

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_whats_new()
        elif n == 1:
            click(app, 'A motor run hot')
        elif n == 2:
            assert app.field_id == 'fetch' and not app.building and app.active_tab == 'Edit' and app.demo == 'hot_motor'
            assert app.live_disturbance.label == 'left motor 50 K hot' and app.runner.state == 'running'
        elif n == 3:
            s = app.drive_sample
            if s is not None and s.motors:
                kept.append({m.name: m.kept for m in s.motors})
            r = app.runner
            if r.state == 'running':
                assert app.state.time < 80, r.message
                return
            assert r.state == 'completed' and goals(app) == FETCHED, (r.message, goals(app))
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    words = said(app, monkeypatch, 'draw_test_drive_panel')
    app.run(seconds=600)
    assert step['n'] == 4 and app.live_note.startswith('left motor 50 K hot - at 0.')
    assert 'Left motor weakened: 84 % of its torque' in words and not any(w.startswith('Right motor') for w in words)
    assert kept and kept[-1]['left'] == pytest.approx(hot()) and kept[-1]['right'] is None, kept[-1:]
    delivered = app.goal_tracker.met['delivered']
    assert abs(delivered - 37.5) < 1., "the cube in the bin when it is undisturbed, 37.5 s"


@WINDOW
def test_a_cube_sixteen_times_as_heavy_slides_out_of_the_jaws_as_the_panel_counts_up(tmp_path, monkeypatch):
    import glfw
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}
    cube = {}

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_whats_new()
        elif n == 1:
            click(app, 'How close to slipping')
        elif n == 2:
            assert app.field_id == 'fetch' and app.active_tab == 'Edit' and app.demo == 'slip'
            body = app.backend.model.body('objects/fetch_cube').id
            cube['id'] = body
            assert app.backend.model.body_mass[body] == pytest.approx(16 * .01625), "16 times as heavy"
        elif n == 3:
            if app.state.time < 24.:
                assert app.runner.state == 'running', app.runner.message
                return
            cube['z'] = float(app.backend.data.xpos[cube['id']][2])
            cube['goals'] = goals(app)
            app.simulate()                              # back to build: the world is reset
            assert app.backend.model.body_mass[cube['id']] == pytest.approx(.01625), "as designed again"
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    words = said(app, monkeypatch, 'draw_test_drive_panel')
    app.run(seconds=600)
    assert step['n'] == 4 and cube['goals']['lifted'] != 'met' and cube['z'] < .15, "it slid out on the lift"
    uses = [int(w.split()[1]) for w in words if w.startswith('grip: ') and w.split()[1].isdigit()]
    assert uses and min(uses) < 90 and max(uses) >= 95, (min(uses), max(uses))


@WINDOW
def test_the_repeats_demonstration_stops_on_its_report_and_says_what_the_repeats_could_show(tmp_path, monkeypatch):
    """ADR 0063, 0064: the Fetch run once, stopped as its program ends; under each Repeat button what
    its draws can show - 8 drawn bound failures under 31 %, and a disturbance must break 6 of the 8
    to be shown - and Repeat with disturbances starts its 72 runs in the background."""
    import glfw
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}
    seen = {}

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_whats_new()
        elif n == 1:
            click(app, 'Where repeats fail')
        elif n == 2:
            assert app.field_id == 'fetch' and not app.building and app.demo == 'repeats', app.status
            assert app.runner.state == 'running' and app.status.startswith('Where repeats fail: ')
        elif n == 3:
            if not app.building:
                assert app.state.time < 80, app.runner.message
                return
            seen['runner'] = app.runner.state
            seen['goals'] = {g.id: g.status for g in app.run_report.goals}
            seen['status'] = app.status
        elif n == 4:
            click(app, 'Repeat with disturbances')
        elif n == 5:
            seen['total'] = app.disturbing['total'] if app.disturbing else None
            app.stop_disturbances()
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    words = said(app, monkeypatch, 'draw_run_report')
    app.run(seconds=600)
    assert step['n'] == 6 and seen['goals'] == FETCHED, seen
    assert seen['status'].startswith('Where repeats fail: under each Repeat button'), seen['status']
    assert '8 drawn: if all succeed, failures under 31 %' in words
    assert 'to be sure it breaks runs, it must break 6 of the 8 drawn' in words
    assert seen['total'] == 72 and app.disturbing is None, "started in the background, and stopped"
    assert not getattr(app, 'demo_report_due', False), "once"


@WINDOW
def test_the_panda_held_up_puts_tall_blocks_within_a_millimetre_of_their_slots(tmp_path, monkeypatch):
    """ADR 0065: Real's cell making tall blocks, the Panda held against gravity and squeezing 70 N."""
    import glfw
    from little_world.factory.controller import SLOTS
    from little_world.factory.process import judge, slot_room
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}
    cell = {}

    def in_the_cell():
        real = app.active_workspace
        cell['draw']()
        n = step['n']
        if n == 2:
            assert real.app_mode == 'Real' and real.experiment == 'Pick and place' and real.product == 'Tall block'
            assert real.cycle.run is not None and real.cycle.state == 'running' and app.demo == 'panda'
        elif n == 3:
            placed = real.cycle.run['placements']
            if len(placed) < 2:
                assert real.state.time < 60 and real.cycle.state == 'running', real.cycle.message
                return
            zx, zy, turn = slot_room(SLOTS, 32.)
            cell['window'] = judge(placed, (zx, zy), turn)
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_whats_new()
        elif n == 1:
            button = next(b for b in app.active_workspace.buttons if b.label == 'The Panda holds itself up')
            button.action()
            real = app.active_workspace
            cell['draw'] = real.draw
            monkeypatch.setattr(real, 'draw', in_the_cell)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=600)
    w = cell['window']
    assert step['n'] == 4 and w.inside == 2 and w.worst < 1., w


@WINDOW
def test_a_squeeze_set_in_newtons_holds_the_cube_with_more_of_its_grip_to_spare(tmp_path, monkeypatch):
    """FR-037: the Fetch with its jaws squeezing 7 N by current - the close block says so - fetches
    the cube with the grip's friction in use at most about 60 %, where the ramp's squeeze reaches 80 %."""
    import glfw
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}
    seen = {}

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_whats_new()
        elif n == 1:
            click(app, 'A squeeze set in newtons')
        elif n == 2:
            closes = [b for b in app.program.blocks if b.kind == 'action' and b.value == 1]
            seen['closes'] = [(b.duration, b.secondary) for b in closes]
            assert app.field_id == 'fetch' and app.demo == 'squeeze' and app.runner.state == 'running', app.status
        elif n == 3:
            r = app.runner
            if r.state == 'running':
                assert app.state.time < 80, r.message
                if r.carrying():                    # in the air, between the grasp check and letting go
                    use = grip_use(app.backend, 'objects/fetch_cube')
                    if use is not None:
                        carried.append(use)
                return
            seen['goals'] = goals(app)
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    from little_world.inventory.handling import grip_use
    carried = []
    monkeypatch.setattr(app, 'draw', exercise)
    words = said(app, monkeypatch, 'draw_test_drive_panel')
    app.run(seconds=600)
    assert step['n'] == 4 and seen['goals'] == FETCHED, seen
    assert seen['closes'] == [(1.4, 7.), (pytest.approx(.02), 7.)], seen['closes']
    assert any(w.startswith('grip: ') for w in words), "the drive panel says how much of the grip is in use"
    assert carried and max(carried) <= .65, max(carried)


@WINDOW
def test_the_roller_conveyor_carries_its_pallets_to_the_stop_in_the_window(tmp_path, monkeypatch):
    """ADR 0067: the conveyor field from What's new - the arm on its cart beside it, the pallets
    carried to the stop and queued, their goals met by 2 s."""
    import glfw
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}
    seen = {}

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_whats_new()
        elif n == 1:
            click(app, 'A roller conveyor')
        elif n == 2:
            assert app.field_id == 'conveyor' and not app.building and app.demo == 'conveyor', app.status
        elif n == 3:
            if app.state.time < 2.5:
                return
            seen['goals'] = goals(app)
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=600)
    assert step['n'] == 4 and seen['goals'] == {'pallet_1': 'met', 'pallet_2': 'met', 'cube_1': 'met'}, seen


@WINDOW
def test_the_cell_fed_by_the_conveyor_picks_each_part_off_its_pallet(tmp_path, monkeypatch):
    """ADR 0068: Real's cell fed by the roller conveyor from What's new - each part picked off its
    pallet at the stop, the emptied pallet back at the line's start with the next part on it."""
    import glfw
    from little_world.factory.controller import SLOTS
    from little_world.factory.process import judge, slot_room
    app = window(tmp_path)
    draw = app.draw
    step = {'n': 0}
    cell = {}

    def in_the_cell():
        real = app.active_workspace
        cell['draw']()
        n = step['n']
        if n == 2:
            assert real.app_mode == 'Real' and real.feeder == 'conveyor' and real.cycle.line is not None
            assert real.cycle.run is not None and app.demo == 'fed', real.cycle.message
        elif n == 3:
            placed = real.cycle.run['placements']
            if len(placed) < 2:
                assert real.state.time < 60 and real.cycle.state in ('waiting', 'running'), real.cycle.message
                return
            zx, zy, turn = slot_room(SLOTS, 32.)
            cell['window'] = judge(placed, (zx, zy), turn)
            cell['arrivals'] = list(real.cycle.run['arrivals'])
            cell['carrier'] = dict(real.cycle.carrier)
            glfw.set_window_should_close(app.window, True)
        step['n'] += 1

    def exercise():
        draw()
        n = step['n']
        if n == 0:
            app.show_whats_new()
        elif n == 1:
            button = next(b for b in app.active_workspace.buttons if b.label == 'The cell fed by a conveyor')
            button.action()
            real = app.active_workspace
            cell['draw'] = real.draw
            monkeypatch.setattr(real, 'draw', in_the_cell)
        step['n'] += 1

    monkeypatch.setattr(app, 'draw', exercise)
    app.run(seconds=600)
    w = cell['window']
    assert step['n'] == 4 and w.inside == 2 and w.worst < 1.5, w
    assert len(cell['arrivals']) >= 2 and all((x * x + y * y) ** .5 < 2.5 for x, y, _ in cell['arrivals']), cell['arrivals']
    assert 'objects/product_3' in cell['carrier'], "the first pallet went back with the third part on it"
