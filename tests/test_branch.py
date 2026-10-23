"""How late is too late (FR-022): an alarm from outside, when it can still rescue a run, and what
a false one costs.

A check is worth having only if it fires while a recovery can still put things right (RESCUE,
arXiv 2610.13516). The runner takes an alarm from outside (`Runner.alarm`): at a stop where the
program looked, it recovers as its own recovery does - opens the jaws by as much as they closed
since the look, rises, goes back and looks again. A fifth recovery, 'ignore', lets the program's
checks fire with nothing coming of them, so that an alarm can be tried at every moment of what
follows. The stand-ins are tests/test_look_again.py's; one pair of Fetch runs checks that a branch
is its parent until the alarm, step for step, and that the alarm rescues it.
"""
from types import SimpleNamespace

import pytest

from little_world.programming.program import Runner
from test_look_again import CUBE, FETCH
from test_recovery import moved_once


def drive(runner, cube, holds, alarm=lambda runner: False, ticks=4000):
    """Tick a runner as tests/test_look_again.py does, asking `alarm(runner)` before each tick
    whether to raise one: (runner, aimed, actions, log, [(time, acted, reopen right after)])."""
    angles, aimed, actions, log, raised = {'arm': (0.,)}, [], [], [], []
    clock = {'t': 0.}

    def aim(point, pose):
        aimed.append(tuple(round(v, 3) for v in point))
        return (('arm', (100. + 1000 * point[1],)),)

    def see(target, planned):
        return SimpleNamespace(centre=cube(clock['t']))
    runner.start(FETCH)
    for _ in range(ticks):
        if not raised and alarm(runner):
            raised.append((round(clock['t'], 2), runner.alarm(), runner.reopen))
        held = frozenset({CUBE}) if runner.program.blocks[runner.index].kind == 'grasp' and holds(aimed) else frozenset()
        out = runner.tick(.01, angles, held=held, base=(1.6, 0., 0.), aim=aim, see=see)
        clock['t'] += .01
        if out['pose']:
            angles = dict(out['pose'])
        if out['action']:
            actions.append((round(clock['t'], 2), out['action']))
        if runner.message not in log:
            log.append(runner.message)
        if runner.state != 'running':
            break
    return runner, aimed, actions, log, raised


def at(kind, after=0.):
    """An alarm raised once the program is at its first block of `kind` after the look, `after`
    seconds into it."""
    return lambda runner: (runner.after_look is not None and runner.program.blocks[runner.index].kind == kind
                           and runner.elapsed + 1e-9 >= after)


def test_an_alarm_is_heard_only_at_a_stop_where_the_program_looked():
    runner = Runner()
    runner.start(FETCH)
    before = dict(vars(runner))
    assert not runner.listening() and runner.alarm() is False
    assert vars(runner) == before, 'an alarm it cannot act on changes nothing'
    cube = lambda t: (1.84, 0., .14)
    _, _, _, log, raised = drive(Runner(), cube, lambda aimed: True, at('pose'))
    assert raised[0][1] is True and 'An alarm: looking again' in log
    runner, _, _, log, raised = drive(Runner(regrasps=0), cube, lambda aimed: True, at('pose'))
    assert raised[0][1] is False and runner.state == 'completed', 'no regrasp left: not listening'


def test_ignoring_its_checks_the_program_goes_on_as_taught():
    runner, _, _, log, _ = drive(Runner(recovery='ignore'), *moved_once())
    assert runner.state == 'completed' and runner.regrasps == 0, log
    assert not any('looking again' in m or 'missed' in m for m in log), log
    assert [s for _, _, s in runner.seen] == [(1.84, 0., .14)], 'one look'


def test_an_alarm_makes_a_program_that_ignores_its_checks_look_again_and_reach_where_the_cube_went():
    runner, aimed, actions, log, raised = drive(Runner(recovery='ignore'), *moved_once(), at('grasp', .1))
    (when, acted, reopen), = raised
    assert acted and reopen == ('jaws', -1., pytest.approx(.8)), 'opened as long as the jaws had closed'
    opened = [t for t, a in actions if a == ('jaws', -1.) and t > when]
    assert opened and opened[-1] - opened[0] == pytest.approx(.8, abs=.02)
    assert runner.state == 'completed' and runner.regrasps == 1 and runner.recovery == 'ignore', log
    assert [s for _, _, s in runner.seen] == [(1.84, 0., .14), (1.84, .05, .14)]
    assert (1.84, .05, .14) in aimed


def test_an_alarm_as_the_jaws_close_opens_them_as_far_as_they_closed():
    _, _, _, _, raised = drive(Runner(recovery='ignore'), *moved_once(), at('action', .3))
    (_, acted, reopen), = raised
    assert acted and reopen[:2] == ('jaws', -1.) and reopen[2] == pytest.approx(.3, abs=.011)


# -- reading the branches ----------------------------------------------------------------------

def branch(label, alarm, ok, acted=True):
    from little_world.fields.goals import Result
    from little_world.fields.variation import Variation
    from little_world.inventory.sweep import Run
    results = (Result('lifted', 'Cube lifted 5 cm', 'met' if ok else 'missed', 20. if ok else None),
               Result('delivered', 'Cube resting in the bin', 'met' if ok else 'missed', 40. if ok else None))
    return Run(Variation(label), results, program='completed', event=16.46,
               alarm=((alarm, acted, 5),) if alarm is not None else (),
               recovered=(alarm,) if alarm is not None and acted else (), listening=((15.14, 22.74),))


def test_alarms_are_raised_inside_the_time_the_program_listened():
    from little_world.inventory.branch import scan
    assert scan(((15.14, 17.2),)) == (15.5, 16., 16.5, 17.)
    assert scan(((15., 16.),)) == (15.5, 16.), 'not at the moment it begins to listen; up to when it stops'
    assert scan(((15.14, 15.4), (18.2, 19.)), every=.25) == (15.25, 18.25, 18.5, 18.75, 19.)


def test_a_window_is_read_from_its_branches():
    from little_world.inventory.branch import window, windows_markdown
    own = branch('as designed', None, True)
    own = type(own)(**{**vars(own), 'recovered': (19.67,)})
    oks = {15.5: False, 16.: True, 16.5: True, 17.: False, 17.5: True, 18.: True, 18.5: False}
    found = window(branch('as designed', None, False), [branch('as designed', t, ok) for t, ok in oks.items()], own)
    assert (found.earliest, found.deadline, found.holes) == (16., 18., (17.,))
    assert found.check == 19.67 and found.own and found.slack == pytest.approx(-1.67)
    page = windows_markdown([found], 'cube moved 5 cm sideways, 2 s later')
    assert '| as designed | 16.46 | 15.14-22.74 | 19.67 | 4 of 7 (not 17.0) | 16.0 | 18.0 | -1.7 s |' in page


def test_a_false_alarm_is_drawn_from_the_time_listened_and_read_by_what_the_program_was_doing():
    from little_world.inventory.branch import FalseAlarm, false_alarm, false_alarm_at, false_alarms_markdown, phase
    parent = branch('repeat 3', None, True)
    t = false_alarm_at(parent)
    assert 15.14 < t < 22.74 and t == false_alarm_at(parent), 'drawn from the set-up: the same each time'
    assert false_alarm_at(type(parent)(**{**vars(parent), 'listening': ()})) is None
    assert [phase(FETCH, i) for i in (4, 5, 6, 7, 8)] == ['reaching', 'reaching', 'closing', 'closing', 'holding']
    cost = false_alarm(parent, branch('repeat 3', t, True), FETCH)
    assert (cost.phase, cost.acted, cost.parent, cost.alarmed, cost.cost) == ('reaching', True, True, True, 0.)
    alarms = [FalseAlarm(f'repeat {k}', 17., True, 'reaching', True, True, 3. + k) for k in range(9)]
    alarms += [FalseAlarm('repeat 9', 21., True, 'holding', True, False, None),
               FalseAlarm('repeat 10', 15.2, False, 'reaching', True, True, 0.)]
    page = false_alarms_markdown(alarms)
    assert '| reaching | 9 | 9 | 0 of 9, at most 28 % | +7.0 s (+3.0 to +11.0) |' in page
    assert '| holding | 1 | 0 | 1 of 1, at most 100 % | - |' in page
    assert '| all | 10 | 9 | 1 of 10, at most 39 % | +7.0 s (+3.0 to +11.0) |' in page
    assert '1 alarm came when the program was not listening and changed nothing.' in page


def test_a_run_with_an_alarm_records_it_and_round_trips():
    from little_world.inventory.sweep import _run
    from dataclasses import asdict
    import json
    r = branch('as designed', 18., True)
    back = _run(json.loads(json.dumps(asdict(r))))
    assert (back.alarm, back.recovered, back.listening) == (((18., True, 5),), (18.,), ((15.14, 22.74),))


def test_the_command_line_names_what_it_reads(capsys):
    from little_world.inventory.branch import main
    with pytest.raises(SystemExit):
        main(['when'])
    assert "invalid choice: 'when'" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(['window', '--every', '0'])
    assert '--every is a time in seconds' in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(['window', '--disturbance', 'a gust of wind'])
    assert "no disturbance 'a gust of wind'; it has: 'shoved 4 N s at the table'" in capsys.readouterr().err


# -- one pair of Fetch runs ----------------------------------------------------------------------

def test_a_branch_is_its_parent_until_the_alarm_and_the_alarm_rescues_it():
    """The cube moved 5 cm, 2 s after the look: with no recovery the reach is blocked and the
    program stops. The same set-up with an alarm at 17 s - after the cube moved, before the
    program's own check (19.7 s) - looks again and fetches it; the two runs are one run, bit for
    bit, until the alarm."""
    pytest.importorskip('mujoco')
    from little_world.fields.disturbance import DEFAULTS
    from little_world.inventory.sweep import design, run, solve
    late = next(d for d in DEFAULTS['fetch'] if d.label == 'cube moved 5 cm sideways, 2 s later')
    bp = design('mobile_manipulator')
    program = solve('fetch', bp)
    plain, alarmed = [], []
    parent = run('fetch', bp, program=program, disturbance=late, recovery='none', trace=plain)
    rescued = run('fetch', bp, program=program, disturbance=late, recovery='none', alarm=17., trace=alarmed)
    assert parent.program == 'failed' and parent.result('lifted').status == 'missed' and not parent.recovered
    assert parent.listening and parent.listening[0][0] < 17. < parent.listening[0][1]
    (when, acted, _), = rescued.alarm
    assert acted and rescued.recovered == (when,) and when == pytest.approx(17., abs=.002)
    assert all(x.status in ('met', 'kept') for x in rescued.results), rescued.message
    k = next(k for k, (a, b) in enumerate(zip(plain, alarmed)) if a != b)
    assert plain[:k] == alarmed[:k] and alarmed[k][0] == pytest.approx(when + .002, abs=1e-6)
