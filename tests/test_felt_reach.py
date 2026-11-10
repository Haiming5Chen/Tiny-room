"""A reach for the object that stops when the arm feels it meet something (ADR 0071, OPEN LW-029).

A program reaching down for a cube that was moved under a jaw since the last picture used to
press it into the table until the pose timed out, 2 s later. The runner now reads the arm's
joints as their servos report them, Present Position against the goal it sent: late in a reach
the goals slow towards their ends and a free joint catches up, so a joint that falls further
behind instead has met something. The stand-ins are tests/test_look_again.py's, the reach down
as slow as the Fetch's and the joints following their goals a servo's 60 ms behind; then the
Fetch run that pressed.
"""
from types import SimpleNamespace

import pytest

from little_world.programming.program import CATCHING, FELT_LAG, Block, Program, Runner
from test_look_again import ABOVE, CHECK, CLOSE, LIFT, LOOK, OPEN, READY, STOP

LAG = .06           # s: how far behind a moving goal the kit arm's servos keep a joint (the Fetch's
                    # shoulder lagged 1.0 degree at 17 degrees a second)
AT = Block('pose', value=10., duration=2., angles=(('arm', (20.,)),), point=(1.84, 0., .14))   # 1 s down
FETCH = Program((OPEN, READY, STOP, LOOK, ABOVE, AT, CLOSE, CHECK, LIFT))


def run(stop_at=None, runner=None, ticks=4000, dt=.01):
    """Tick a runner whose joints each step move dt/LAG of the way to their goals - a servo's lag -
    the base at its stop and the cube where it was planned. With `stop_at`, the first reach down
    stays where it has come that share of its way: a jaw has met the cube. Returns the runner and
    each message with when it was first said (s)."""
    runner = runner or Runner()
    angles, clock, said = {'arm': (0.,)}, {'t': 0.}, {}
    stuck = {'from': None, 'at': None}

    def see(target, planned):
        return SimpleNamespace(centre=(1.84, 0., .14))
    runner.start(FETCH)
    for _ in range(ticks):
        block = runner.program.blocks[runner.index]
        held = frozenset({'objects/cube'}) if block.kind == 'grasp' else frozenset()
        out = runner.tick(dt, angles, held=held, base=(1.6, 0., 0.), aim=lambda point, pose: None, see=see)
        clock['t'] += dt
        (now,) = angles['arm']
        if out['pose']:
            (goal,) = out['pose']['arm']
            reaching = block is AT and runner.state == 'running' and not runner.rising and not runner.regrasps
            if reaching and stop_at is not None:
                stuck['from'] = now if stuck['from'] is None else stuck['from']
                if stuck['at'] is None and now - stuck['from'] >= stop_at * (20. - stuck['from']):
                    stuck['at'] = now
            if reaching and stuck['at'] is not None:
                angles = {'arm': (stuck['at'],)}
            else:
                angles = {'arm': (now + (goal - now) * min(1., dt / LAG),)}
        said.setdefault(runner.message, round(clock['t'], 2))
        if runner.state != 'running':
            break
    return runner, said


def test_a_free_reach_whose_joints_lag_their_goals_is_not_felt():
    """A servo keeps its joint behind a moving goal - 0.9 degrees here at the reach's peak speed,
    more than FELT_LAG - and late in the reach catches up: nothing is felt."""
    runner, said = run()
    assert runner.state == 'completed' and runner.bumps == [] and runner.regrasps == 0, said
    assert not any('Felt' in m for m in said)


def test_a_reach_held_back_partway_down_is_felt_and_the_arm_rises_at_once():
    """The jaws meet the cube 70 % of the way down: well within the reach's own second the
    program has felt it, rises the way it came and looks again - where it waited the pose's 2 s."""
    runner, said = run(stop_at=.7)
    assert runner.state == 'completed' and runner.regrasps == 1, said
    assert 'Felt something reaching down: looking again' in said
    assert runner.bumps and runner.bumps[0][0] == FETCH.blocks.index(AT)
    assert CATCHING * 1. <= runner.bumps[0][1] < 1., runner.bumps      # felt before its 1 s of travel was over


def test_without_its_checks_the_program_waits_out_the_pose_as_before():
    """The felt reach is one of the runner's checks (ADR 0038): unchecked, the same reach waits
    out the pose's 2 s past its travel and is then found blocked - about 2 s later."""
    felt, said = run(stop_at=.7)
    waited, unchecked = run(stop_at=.7, runner=Runner(checks=False))
    assert 'Blocked reaching down: looking again' in unchecked and not waited.bumps, unchecked
    assert unchecked['Blocked reaching down: looking again'] - said['Felt something reaching down: looking again'] > 2.


def test_a_reach_that_cannot_look_again_any_more_still_waits_for_its_timeout():
    """With no regrasp left a felt reach changes nothing: the pose times out as it did."""
    runner, said = run(stop_at=.7, runner=Runner(regrasps=0))
    assert runner.state == 'failed' and runner.message == 'Timed out: pose did not settle' and not runner.bumps


def test_felt_lag_is_a_few_counts_of_a_servo_present_position():
    """0.5 degrees is six counts of an X-series servo's Present Position (0.088 degrees each):
    well above its quantization, half the 1.0 degree the free shoulder lags at the reach's peak."""
    assert 5 <= FELT_LAG / (360 / 4096) <= 7


def test_the_cube_moved_under_a_jaw_is_felt_at_once_and_not_pressed_for_two_seconds():
    """OPEN LW-029: the cube moved 5 cm sideways 2 s after the look, as the jaws come over it.
    A jaw came down on it at 17.2 s and pressed it into the table at 3.1 N until the reach timed
    out, 2.4 s later; the program then rose, looked again and fetched it. Now the reach is felt
    0.2 s after the jaw met the cube, and the cube is in the bin 2.4 s sooner."""
    pytest.importorskip('mujoco')
    from little_world.fields.disturbance import DEFAULTS
    from little_world.inventory.sweep import design, run as field_run
    late = next(d for d in DEFAULTS['fetch'] if d.label == 'cube moved 5 cm sideways, 2 s later')
    result = field_run('fetch', design('mobile_manipulator'), disturbance=late)
    assert result.regrasped == 1 and all(r.status in ('met', 'kept') for r in result.results), result.results
    assert result.recovered and result.recovered[0] < 17.5, result.recovered
    assert result.result('delivered').time < 41., result.result('delivered').time   # 43.2 s
