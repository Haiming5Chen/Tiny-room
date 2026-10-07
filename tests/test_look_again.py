"""A missed grasp at a stop where the program looked: open, look again, reach again (ADR 0033,
FR-015).

ADR 0032's program looks once, when it stops at the table; the cube moved after that look
was missed in every set-up, the grasp check holding nothing. These are the runner's rules for
trying again, with joints that go where they are sent, a base at its stop and a camera the
test stands in for; then the run that no set-up had passed.
"""
from types import SimpleNamespace

import pytest

from little_world.programming.program import Block, Program, Runner

CUBE = 'objects/cube'
OPEN = Block('action', 'jaws', -1, .5)
READY = Block('pose', value=40., duration=2., angles=(('arm', (5.,)),))
STOP = Block('goto', value=.01, duration=60., point=(1.6, 0., 0.))
LOOK = Block('look', CUBE, value=.3, duration=5., point=(1.84, 0., .14))
ABOVE = Block('pose', value=40., duration=2., angles=(('arm', (10.,)),), point=(1.84, 0., .20))
AT = Block('pose', value=40., duration=2., angles=(('arm', (20.,)),), point=(1.84, 0., .14))
CLOSE = Block('action', 'jaws', 1, .8)
CHECK = Block('grasp', CUBE, duration=.5)
LIFT = Block('pose', value=40., duration=2., angles=(('arm', (10.,)),), point=(1.84, 0., .20))
FETCH = Program((OPEN, READY, STOP, LOOK, ABOVE, AT, CLOSE, CHECK, LIFT))


def run(program, cube, holds, runner=None, ticks=4000, blocked=lambda runner: False):
    """Tick a runner: the base stands at the stop; `cube(t)` is where the camera sees the cube;
    `holds(aimed)` whether the jaws hold it, given the points the poses were aimed at;
    `blocked(runner)` whether the arm cannot move now."""
    runner = runner or Runner()
    angles, aimed, actions, log = {'arm': (0.,)}, [], [], []
    clock = {'t': 0.}

    def aim(point, pose):
        aimed.append(tuple(round(v, 3) for v in point))
        return (('arm', (100. + 1000 * point[1],)),)

    def see(target, planned):
        return SimpleNamespace(centre=cube(clock['t']))
    runner.start(program)
    for _ in range(ticks):
        held = frozenset({CUBE}) if runner.program.blocks[runner.index].kind == 'grasp' and holds(aimed) else frozenset()
        out = runner.tick(.01, angles, held=held, base=(1.6, 0., 0.), aim=aim, see=see)
        clock['t'] += .01
        if out['pose'] and not blocked(runner):
            angles = dict(out['pose'])
        if out['action']:
            actions.append((round(clock['t'], 2), out['action']))
        if runner.message not in log:
            log.append(runner.message)
        if runner.state != 'running':
            break
    return runner, aimed, actions, log


def test_a_missed_grasp_opens_the_jaws_looks_again_and_reaches_where_the_cube_now_is():
    moved = {'at': None}

    def cube(t):                        # the cube is moved 5 cm once the jaws are on their way down
        return (1.84, .05, .14) if moved['at'] is not None else (1.84, 0., .14)

    def holds(aimed):
        if moved['at'] is None and (1.84, 0., .14) in aimed:
            moved['at'] = len(aimed)    # moved after the first look, as the jaws went down
        return (1.84, .05, .14) in aimed
    runner, aimed, actions, log = run(FETCH, cube, holds)
    assert runner.state == 'completed' and runner.regrasps == 1, log
    assert 'Nothing held: looking again' in log
    # The jaws were opened again - the closing action, backwards, as long - before going back.
    reopened = [t for t, a in actions if a == ('jaws', -1)]
    assert len(reopened) >= 2 and reopened[-1] - reopened[len(reopened) // 2] > .3
    # Looked twice; the second look saw it where it was moved to, and the jaws went there.
    assert [s for _, _, s in runner.seen] == [(1.84, 0., .14), (1.84, .05, .14)]
    assert (1.84, .05, .20) in aimed and (1.84, .05, .14) in aimed


def test_moved_after_the_look_it_is_seen_before_the_jaws_reach_down():
    """One more picture as the jaws are about to go down: the cube is no longer where the look
    saw it (a finger over it hides it), so the jaws go back and look again before touching it."""
    def cube(t):
        return (1.84, 0., .14) if t < 1.5 else (1.84, .05, .14)    # moved once the jaws set off
    runner, aimed, actions, log = run(FETCH, cube, lambda aimed: (1.84, .05, .14) in aimed)
    assert runner.state == 'completed' and runner.regrasps == 1
    assert 'Moved since the look: looking again' in log
    assert (1.84, 0., .14) not in aimed                  # never reached down where it had been
    assert [a for _, a in actions].count(('jaws', 1)) == round(CLOSE.duration / .01)   # closed once, on the cube
    assert [s for _, _, s in runner.seen] == [(1.84, 0., .14), (1.84, .05, .14)]


def test_a_reach_down_that_is_blocked_looks_again():
    """The jaws came down on the cube moved under a finger and could not settle."""
    def blocked(runner):
        return runner.program.blocks[runner.index] is AT                 # every time it reaches down
    runner, aimed, actions, log = run(FETCH, lambda t: (1.84, 0., .14), lambda aimed: True, blocked=blocked)
    assert 'Blocked reaching down: looking again' in log and runner.regrasps == 1
    assert runner.state == 'failed' and runner.message == 'Timed out: pose did not settle'   # blocked again: no second try


def test_once_only_and_only_where_it_looked():
    never = (lambda aimed: False)
    runner, _, _, log = run(FETCH, lambda t: (1.84, 0., .14), never)
    assert runner.state == 'failed' and runner.message == 'Nothing held: the grasp missed' and runner.regrasps == 1
    runner, _, _, _ = run(FETCH, lambda t: (1.84, 0., .14), never, Runner(regrasps=0))
    assert runner.state == 'failed' and runner.regrasps == 0
    blind = Program(tuple(b for b in FETCH.blocks if b.kind != 'look'))
    runner, _, _, _ = run(blind, lambda t: (1.84, 0., .14), never)
    assert runner.state == 'failed' and runner.regrasps == 0          # nothing looked: nothing to look again
    with pytest.raises(ValueError):
        Runner(regrasps=-1)


def test_the_cube_moved_after_the_look_is_fetched_by_looking_again():
    """ADR 0032's limit: the cube moved 5 cm 2 s after the cart stopped, as the jaws come over
    it, was missed in all nine set-ups."""
    pytest.importorskip('mujoco')
    from little_world.fields.disturbance import DEFAULTS
    from little_world.inventory.sweep import design, run as field_run
    late = next(d for d in DEFAULTS['fetch'] if d.label == 'cube moved 5 cm sideways, 2 s later')
    result = field_run('fetch', design('mobile_manipulator'), disturbance=late)
    assert result.regrasped == 1 and all(r.status in ('met', 'kept') for r in result.results), (result.results, result.program)
    # Three looks: before the drive (ADR 0035), at the stop, and again once it had moved.
    assert len(result.seen) == 3 and abs(result.seen[-1][2][1] - result.seen[-1][3][1]) < .005
